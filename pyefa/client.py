from enum import StrEnum

import json
import aiohttp

from .data_classes import Stop
from .requests import DeparturesRequest, Request, StopFinderRequest, SystemInfoRequest
from .exceptions import EfaConnectionError
import logging


LOGGER = logging.getLogger(__name__)


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
        if not url:
            raise ValueError("No URL provided")

        self._base_url = url if url.endswith("/") else f"{url}/"

    async def system_info(self):
        """ """
        request = SystemInfoRequest()

        url = self._build_url(request)

        response = await self._run_query(url)

        return request.parse(response)

    async def find_stop(self, name: str, type="any"):
        request = StopFinderRequest(type, name)

        url = self._build_url(request)

        response = await self._run_query(url)

        return request.parse(response)

    async def trip(self):
        pass

    async def departures(
        self,
        stop: Stop | str,
        limit=40,
        date: str | None = None,
    ):
        if isinstance(stop, Stop):
            stop = stop.id

        request = DeparturesRequest(stop)

        request.add_param("limit", limit)

        if date:
            request.add_datetime(date)

        url = self._build_url(request)

        response = await self._run_query(url)

        return request.parse(response)

    async def _run_query(self, query: str) -> dict:
        LOGGER.debug(f"Run query {query}")

        async with self._client_session.get(query) as response:
            if response.status == 200:
                return json.loads(await response.text())
            else:
                raise EfaConnectionError(
                    f"Failed to query EFA endpoint. Returned {response.status}"
                )

    def _build_url(self, request: Request):
        return self._base_url + str(request)
