from abc import abstractmethod
from datetime import datetime
from pprint import pprint
from voluptuous import (
    Any,
    Match,
    Optional,
    Schema,
    Required,
    Range,
)

from .helpers import is_date, is_datetime, is_time, parse_datetime
from .data_classes import Departure, Stop, StopType, SystemInfo, TransportType

import logging

LOGGER = logging.getLogger(__name__)


class Request:
    def __init__(self, name, macro) -> None:
        self._name = name
        self._macro = macro
        self._parameters = {"outputFormat": "rapidJSON"}
        self._schema: Schema = Schema(
            {
                Required("outputFormat", default="rapidJSON"): Any("rapidJSON"),
                Optional("itdDate"): Match(r"\d{8}"),
                Optional("itdTime"): Match(r"\d{4}"),
            }
        )

    @abstractmethod
    def parse(self, data: str):
        raise NotImplementedError("Abstract method not implemented")

    @abstractmethod
    def add_param(self, param: str, value: str):
        if not param or not value:
            return

        LOGGER.debug(f'Add parameter "{param}" with value "{value}"')

        self._parameters.update({param: value})

        LOGGER.debug("Updated parameters dict:")
        LOGGER.debug(self._parameters)

    def add_datetime(self, date: str):
        if is_datetime(date):
            self.add_param("itdDate", date.split(" ")[0])
            self.add_param("itdTime", date.split(" ")[1].replace(":", ""))
        elif is_date(date):
            self.add_param("itdDate", date)
        elif is_time(date):
            self.add_param("itdTime", date.replace(":", ""))
        else:
            raise ValueError("Date(time) provided in invalid format")

    def __str__(self) -> str:
        # validata/update parameters with schema
        self._parameters = self._schema(self._parameters)

        return f"{self._name}?{self._macro}" + self._params_str()

    def _params_str(self):
        if not self._parameters:
            return ""

        return "&" + "&".join([f"{k}={str(v)}" for k, v in self._parameters.items()])


class SystemInfoRequest(Request):
    def __init__(self) -> None:
        super().__init__("XML_SYSTEMINFO_REQUEST", "system")

    def parse(self, data: dict) -> SystemInfo:
        version = data.get("version", None)
        data_format = data.get("ptKernel").get("dataFormat")
        valid_from = data.get("validity").get("from")
        valid_to = data.get("validity").get("to")

        valid_from = datetime.strptime(valid_from, "%Y-%m-%d").date()
        valid_to = datetime.strptime(valid_to, "%Y-%m-%d").date()

        return SystemInfo(version, data_format, valid_from, valid_to)


class StopFinderRequest(Request):
    def __init__(self, req_type: str, name: str) -> None:
        super().__init__("XML_STOPFINDER_REQUEST", "stopfinder")

        self._schema = self._schema.extend(
            {
                Required("type_sf", default="any"): Any("any", "coord"),
                Optional("name_sf"): str,
                Optional("anyMaxSizeHitList", default=30): int,
                Optional("anySigWhenPerfectNoOtherMatches"): Any("0", "1", 0, 1),
                Optional("anyResSort_sf"): str,
                Optional("doNotSearchForStops_sf", default=0): Any("0", "1", 0, 1),
                Optional("anyObjFilter_origin", default=0): Range(
                    min=0, max=64 + 32 + 16 + 8 + 4 + 2 + 1
                ),
            }
        )

        self.add_param("type_sf", req_type)
        self.add_param("name_sf", name)

    def parse(self, data: dict) -> list[Stop]:
        locations = data.get("locations", [])

        LOGGER.info(f"{len(locations)} stop(s) found")

        stops = []

        for location in locations:
            id = location.get("id", "")

            if not location.get("isGlobalId", False):
                if location.get("properties"):
                    id = location.get("properties").get("stopId")

            stop = {
                "id": id,
                "name": location.get("name", ""),
                "disassembled_name": location.get("disassembledName", ""),
                "coord": location.get("coord", []),
                "stop_type": StopType(location.get("type", "")),
                "transports": [
                    TransportType(x) for x in location.get("productClasses", [])
                ],
                "match_quality": location.get("matchQuality", 0),
            }

            stops.append(stop)

        stops = sorted(stops, key=lambda x: x["match_quality"], reverse=True)

        return [
            Stop(
                x["id"],
                x["name"],
                x["disassembled_name"],
                x["coord"],
                x["stop_type"],
                x["transports"],
            )
            for x in stops
        ]


class TripRequest(Request):
    def __init__(self) -> None:
        super().__init__("XML_TRIP_REQUEST2", "trip")

        self._schema = self._schema.extend(
            {
                Required("type_origin", default="any"): Any("any", "coord"),
                Required("name_origin"): str,
                Required("type_destination", default="any"): Any("any", "coord"),
                Required("name_destination"): str,
                Optional("type_via", default="any"): Any("any", "coord"),
                Optional("name_via"): str,
                Optional("useUT"): Any("0", "1", 0, 1),
                Optional("useRealtime"): Any("0", "1", 0, 1),
            }
        )

    def parse(self, data: dict):
        pass


class DeparturesRequest(Request):
    def __init__(self, stop: str) -> None:
        super().__init__("XML_DM_REQUEST", "dm")

        self._schema = self._schema.extend(
            {
                Required("name_dm", msg="Required parameter name_dm not provided"): str,
                Required("type_dm", default="stop"): Any("any", "stop"),
                Required("mode", default="direct"): Any("any", "direct"),
                Optional("useAllStops"): Any("0", "1", 0, 1),
                Optional("useRealtime", default=1): Any("0", "1", 0, 1),
                Optional("lsShowTrainsExplicit"): Any("0", "1", 0, 1),
                Optional("useProxFootSearch"): Any("0", "1", 0, 1),
                Optional("deleteAssigendStops_dm"): Any("0", "1", 0, 1),
                Optional("doNotSearchForStops_dm"): Any("0", "1", 0, 1),
                Optional("limit"): int,
            }
        )

        self.add_param("name_dm", stop)

    def parse(self, data: dict):
        stops = data.get("stopEvents", [])

        LOGGER.debug(f"{len(stops)} departure(s) found")

        departures = []

        for stop in stops:
            planned_time = stop.get("departureTimePlanned")
            planned_time = parse_datetime(planned_time)

            infos = stop.get("infos", [])
            transportation = stop.get("transportation", {})

            if transportation:
                line_name = transportation.get("number")
                route = transportation.get("description")

                origin_dict = {
                    "id": transportation.get("origin").get("id"),
                    "name": transportation.get("origin").get("name"),
                    "type": StopType(transportation.get("origin").get("type")),
                }
                destination_dict = {
                    "id": transportation.get("destination").get("id"),
                    "name": transportation.get("destination").get("name"),
                    "type": StopType(transportation.get("destination").get("type")),
                }

                origin = Stop(
                    origin_dict["id"], origin_dict["name"], origin_dict["type"]
                )
                destination = Stop(
                    destination_dict["id"],
                    destination_dict["name"],
                    destination_dict["type"],
                )

                product = TransportType(transportation.get("product").get("class"))

                departures.append(
                    Departure(
                        line_name,
                        route,
                        origin,
                        destination,
                        product,
                        planned_time,
                        None,
                    )
                )
        return departures
