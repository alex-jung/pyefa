import pytest
from pyefa.exceptions import EfaParameterError
from pyefa.requests import Request


class MockRequest(Request):
    def parse(self, data: str):
        pass


def test_base_request_init():
    req = MockRequest("my_name", "my_macro")
    assert req._name == "my_name"
    assert req._macro == "my_macro"
    assert not req._parameters
    assert req._schema


def test_base_request_to_str_default_params():
    req = MockRequest("my_name", "my_macro")

    assert str(req) == "my_name?commonMacro=my_macro&outputFormat=rapidJSON"


def test_base_request_unknown_parameters():
    req = MockRequest("my_name", "my_macro")

    req._parameters = {
        "outputFormat": "rapidJSON",
        "opt1": "value1",
        "opt2": "value2",
        "opt3": "value3",
    }

    with pytest.raises(EfaParameterError):
        str(req)


@pytest.mark.parametrize(
    "params, expected",
    [
        ({}, ""),
        ({"opt1": "value"}, "&opt1=value"),
        ({"opt1": "value1", "opt2": "value2"}, "&opt1=value1&opt2=value2"),
    ],
)
def test_base_request_params_str(params, expected):
    req = MockRequest("my_name", "my_macro")

    req._parameters = params
    assert req._params_str() == expected
