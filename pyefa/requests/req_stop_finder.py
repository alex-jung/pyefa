import logging

from voluptuous import Any, Optional, Range, Required

from pyefa.data_classes import Stop, StopFilter, StopType, TransportType
from pyefa.exceptions import EfaParseError

from .req import Request

_LOGGER = logging.getLogger(__name__)


class StopFinderRequest(Request):
    def __init__(self, req_type: str, name: str) -> None:
        super().__init__("XML_STOPFINDER_REQUEST", "stopfinder")

        self._schema = self._schema.extend(
            {
                Required("type_sf", default="any"): Any("any", "coord"),
                Required("name_sf"): str,
                Optional("anyMaxSizeHitList", default=30): int,
                Optional("anySigWhenPerfectNoOtherMatches"): Any("0", "1", 0, 1),
                Optional("anyResSort_sf"): str,
                Optional("anyObjFilter_sf"): int,
                Optional("doNotSearchForStops_sf"): Any("0", "1", 0, 1),
                Optional("anyObjFilter_origin"): Range(
                    min=0, max=sum([x.value for x in StopFilter])
                ),
            }
        )

        self.add_param("type_sf", req_type)
        self.add_param("name_sf", name)

    def parse(self, data: dict) -> list[Stop]:
        locations = data.get("locations", [])

        if not isinstance(locations, list):
            raise EfaParseError(
                f"Failed to parse locations. Expected a list, got {type(locations)}"
            )

        _LOGGER.info(f"{len(locations)} stop(s) found")

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
