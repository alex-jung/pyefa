import logging

from voluptuous import Any, Optional, Required

from .req import Request

_LOGGER = logging.getLogger(__name__)


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
        raise NotImplementedError
