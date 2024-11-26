from datetime import datetime

import pytest

from pyefa.data_classes import SystemInfo
from pyefa.exceptions import EfaParameterError, EfaParseError
from pyefa.requests import Request, StopFinderRequest, SystemInfoRequest


class MockRequest(Request):
    def parse(self, data: str):
        pass


@pytest.fixture
def mock_request() -> MockRequest:
    return MockRequest("my_name", "my_macro")


class TestRequest:
    def test_request_init(self, mock_request):
        assert mock_request._name == "my_name"
        assert mock_request._macro == "my_macro"
        assert not mock_request._parameters
        assert mock_request._schema

    def test_request_to_str_default_params(self, mock_request):
        assert (
            str(mock_request) == "my_name?commonMacro=my_macro&outputFormat=rapidJSON"
        )

    def test_request_unknown_parameters(self, mock_request):
        mock_request._parameters = {
            "outputFormat": "rapidJSON",
            "opt1": "value1",
            "opt2": "value2",
            "opt3": "value3",
        }

        with pytest.raises(EfaParameterError):
            str(mock_request)

    @pytest.mark.parametrize(
        "params, expected",
        [
            ({}, ""),
            ({"opt1": "value"}, "&opt1=value"),
            ({"opt1": "value1", "opt2": "value2"}, "&opt1=value1&opt2=value2"),
        ],
    )
    def test_request_params_str(self, mock_request, params, expected):
        mock_request._parameters = params
        assert mock_request._params_str() == expected

    @pytest.mark.parametrize(
        "param, value", [(None, None), (None, "value"), ("param", None), ("", "")]
    )
    def test_request_add_param_empty(self, mock_request: MockRequest, param, value):
        before = mock_request._parameters.copy()

        mock_request.add_param(param, value)

        after = mock_request._parameters

        assert before == after

    def test_request_add_param_success(self, mock_request: MockRequest):
        before = mock_request._parameters.copy()

        mock_request.add_param("opt1", "value1")

        after = mock_request._parameters

        assert before != after

    @pytest.mark.parametrize("value", [None, ""])
    def test_request_add_param_datetime_empty(self, mock_request: MockRequest, value):
        before = mock_request._parameters.copy()

        mock_request.add_param_datetime(value)

        after = mock_request._parameters

        assert before == after

    @pytest.mark.parametrize("date", [123, {"key": "value"}, "202422-16:34"])
    def test_request_add_param_datetime_exception(
        self, mock_request: MockRequest, date
    ):
        with pytest.raises(ValueError):
            mock_request.add_param_datetime(date)

    def test_request_add_param_datetime_datetime(self, mock_request: MockRequest):
        datetime = "20201212 10:41"

        assert mock_request._parameters.get("itdDate", None) is None
        assert mock_request._parameters.get("itdTime", None) is None

        mock_request.add_param_datetime(datetime)

        assert mock_request._parameters.get("itdDate", None) == "20201212"
        assert mock_request._parameters.get("itdTime", None) == "1041"

    def test_request_add_param_datetime_date(self, mock_request: MockRequest):
        date = "20201212"

        assert mock_request._parameters.get("itdDate", None) is None
        assert mock_request._parameters.get("itdTime", None) is None

        mock_request.add_param_datetime(date)

        assert mock_request._parameters.get("itdTime", None) is None
        assert mock_request._parameters.get("itdDate", None) == "20201212"

    def test_request_add_param_datetime_time(self, mock_request: MockRequest):
        time = "16:34"

        assert mock_request._parameters.get("itdDate", None) is None
        assert mock_request._parameters.get("itdTime", None) is None

        mock_request.add_param_datetime(time)

        assert mock_request._parameters.get("itdDate", None) is None
        assert mock_request._parameters.get("itdTime", None) == "1634"


class TestSystemInfoRequest:
    def test_init_name_and_macro(self):
        req = SystemInfoRequest()

        assert req._name == "XML_SYSTEMINFO_REQUEST"
        assert req._macro == "system"

    def test_parse_success(self):
        req = SystemInfoRequest()

        data = {
            "version": "1.2.3",
            "ptKernel": {"dataFormat": "EFA10_04_00"},
            "validity": {"from": "2024-11-01", "to": "2025-01-01"},
        }

        info = req.parse(data)

        assert isinstance(info, SystemInfo)
        assert info.version == "1.2.3"
        assert info.data_format == "EFA10_04_00"
        assert info.valid_from == datetime(2024, 11, 1).date()
        assert info.valid_to == datetime(2025, 1, 1).date()

    @pytest.mark.parametrize("data", [None, {}, {"dummy": "value"}])
    def test_parse_failed(self, data):
        req = SystemInfoRequest()

        with pytest.raises(EfaParseError):
            req.parse(data)

    @pytest.mark.parametrize(
        "param, value", [("param", "value"), ("name_sf", "my_name")]
    )
    def test_add_invalid_params(self, param, value):
        req = SystemInfoRequest()

        req.add_param(param, value)

        with pytest.raises(EfaParameterError):
            str(req)


class TestStopFinderRequest:
    def test_init_name_and_macro(self):
        req = StopFinderRequest("my_type", "my_name")

        assert req._name == "XML_STOPFINDER_REQUEST"
        assert req._macro == "stopfinder"

    def test_init_params(self):
        req = StopFinderRequest("my_type", "my_name")

        assert req._parameters.get("type_sf") == "my_type"
        assert req._parameters.get("name_sf") == "my_name"

    @pytest.mark.parametrize(
        "isGlobalId, expected_id", [(True, "global_id"), (False, "stop_id_1")]
    )
    def test_parse_success(self, isGlobalId, expected_id):
        req = StopFinderRequest("my_type", "my_name")

        data = {
            "locations": [
                {
                    "id": "global_id",
                    "isGlobalId": isGlobalId,
                    "name": "my location name",
                    "properties": {"stopId": "stop_id_1"},
                    "disassembledName": "disassembled name",
                    "coord": None,
                    "type": "stop",
                    "productClasses": [1, 2, 3],
                    "matchQuality": 0,
                }
            ]
        }

        info = req.parse(data)

        assert len(info) == 1
        assert info[0].id == expected_id

    def test_parse_empty_locations(self):
        req = StopFinderRequest("my_type", "my_name")

        data = {}

        stops = req.parse(data)

        assert len(stops) == 0

    @pytest.mark.parametrize(
        "data", [{"locations": None}, {"locations": "value"}, {"locations": 123}]
    )
    def test_parse_failed(self, data):
        req = StopFinderRequest("my_type", "my_name")

        with pytest.raises(EfaParseError):
            req.parse(data)

    @pytest.mark.parametrize(
        "param, value", [("param", "value"), ("name_sf", "my_name")]
    )
    def test_add_invalid_params(self, param, value):
        req = StopFinderRequest("my_type", "my_name")

        req.add_param(param, value)

        with pytest.raises(EfaParameterError):
            str(req)

    @pytest.mark.parametrize("value", ["any", "coord"])
    def test_valid_param_type_sf(self, value):
        req = StopFinderRequest("my_type", "my_name")

        req.add_param("type_sf", value)

        req._validate_params()

    @pytest.mark.parametrize("value", ["dummy", "STOP"])
    def test_invalid_param_type_sf(self, value):
        req = StopFinderRequest("my_type", "my_name")

        req.add_param("type_sf", value)

        with pytest.raises(EfaParameterError):
            req._validate_params()
