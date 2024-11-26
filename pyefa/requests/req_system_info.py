import logging

from pyefa.data_classes import SystemInfo
from pyefa.exceptions import EfaParseError
from pyefa.helpers import parse_date

from .req import Request

_LOGGER = logging.getLogger(__name__)


class SystemInfoRequest(Request):
    def __init__(self) -> None:
        super().__init__("XML_SYSTEMINFO_REQUEST", "system")

    def parse(self, data: dict) -> SystemInfo:
        _LOGGER.info("Parsing system info response")

        try:
            version = data.get("version", None)
            data_format = data.get("ptKernel").get("dataFormat")
            valid_from = data.get("validity").get("from")
            valid_to = data.get("validity").get("to")

            valid_from = parse_date(valid_from)
            valid_to = parse_date(valid_to)
        except AttributeError as exc:
            _LOGGER.error("Parsing of system info data failed", exc_info=exc)
            raise EfaParseError(str(exc)) from exc

        return SystemInfo(version, data_format, valid_from, valid_to)
