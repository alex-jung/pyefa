import logging

from voluptuous import Any, Optional, Required

from pyefa.data_classes import Departure, Stop, StopType, TransportType
from pyefa.helpers import parse_datetime

from .req import Request

_LOGGER = logging.getLogger(__name__)


class DeparturesRequest(Request):
    def __init__(self, stop: str) -> None:
        super().__init__("XML_DM_REQUEST", "dm")

        self._schema = self._schema.extend(
            {
                Required("name_dm"): str,
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

        _LOGGER.debug(f"{len(stops)} departure(s) found")

        departures = []

        for stop in stops:
            planned_time = stop.get("departureTimePlanned", None)
            estimated_time = stop.get("departureTimeEstimated", None)

            if planned_time:
                planned_time = parse_datetime(planned_time)

            if estimated_time:
                estimated_time = parse_datetime(estimated_time)

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
                        estimated_time,
                        infos,
                    )
                )
        return departures
