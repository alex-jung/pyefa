from enum import StrEnum

import json
import aiohttp
import logging

from .data_classes import Stop, SystemInfo
from .requests import DeparturesRequest, Request, StopFinderRequest, SystemInfoRequest
from .exceptions import EfaConnectionError


_LOGGER = logging.getLogger(__name__)


class Requests(StrEnum):

    SERVING_LINES = "XML_SERVINGLINES_REQUEST?commonMacro=servingLines"
    LINE_STOP = "XML_LINESTOP_REQUEST?commonMacro=linestop"
    COORD = "XML_COORD_REQUEST?commonMacro=coord"
    GEO_OBJ = "XML_GEOOBJECT_REQUEST?commonMacro=geoobj"
    TRIP_STOP_TIMES = "XML_TRIPSTOPTIMES_REQUEST?commonMacro=tripstoptimes"
    STOP_SEQ_COORD = "XML_STOPSEQCOORD_REQUEST?commonMacro=stopseqcoord"
    ADD_INFO = "XML_ADDINFO_REQUEST?commonMacro=addinfo"
    STOP_LIST = "XML_STOP_LIST_REQUEST?commonMacro=stoplist"
    LINE_LIST = "XML_LINELIST_REQUEST?commonMacro=linelist"


class EfaClient:
    async def __aenter__(self):
        self._client_session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, *args, **kwargs):
        await self._client_session.__aexit__(*args, **kwargs)

    def __init__(self, url: str):
        """Create a new instance of client.

        Args:
            url (str): url string to EFA endpoint

        Raises:
            ValueError: No url provided
        """
        if not url:
            raise ValueError("No EFA endpoint url provided")

        self._base_url = url if url.endswith("/") else f"{url}/"

    async def system_info(self) -> SystemInfo:
        """Get system info used by EFA endpoint.

        Returns:
            SystemInfo: info object
        """
        _LOGGER.info("Request system info")

        request = SystemInfoRequest()
        response = await self._run_query(self._build_url(request))

        return request.parse(response)

    async def stops(self, name: str, type="any") -> list[Stop]:
        """Find stop(s) by provided `name`

        Args:
            name (str): Name of station to search for (case insensitive)
            type (str, optional): ['any', 'coord']. Defaults to "any".

        Returns:
            list[Stop]: List of found station(s) provided by endpoint
        """
        _LOGGER.info(f"Request searching for stop with name {name}")
        _LOGGER.debug(f"type: {type}")

        request = StopFinderRequest(type, name)
        response = await self._run_query(self._build_url(request))

        return request.parse(response)

    async def trip(self):
        pass

    async def departures(
        self,
        stop: Stop | str,
        limit=40,
        date: str | None = None,
    ):
        _LOGGER.info(f"Request departures for stop {stop}")
        _LOGGER.debug(f"limit: {limit}")
        _LOGGER.debug(f"date: {date}")

        if isinstance(stop, Stop):
            stop = stop.id

        request = DeparturesRequest(stop)

        # add parameters
        request.add_param("limit", limit)
        request.add_param_datetime(date)

        response = await self._run_query(self._build_url(request))

        return request.parse(response)

    async def _run_query(self, query: str) -> dict:
        _LOGGER.info(f"Run query {query}")

        async with self._client_session.get(query) as response:
            _LOGGER.debug(f"Response status: {response.status}")

            if response.status == 200:
                return json.loads(await response.text())
            else:
                raise EfaConnectionError(
                    f"Failed to query EFA endpoint. Returned {response.status}"
                )

    def _build_url(self, request: Request):
        return self._base_url + str(request)
