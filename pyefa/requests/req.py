import logging
from abc import abstractmethod

from voluptuous import Any, Match, MultipleInvalid, Optional, Required, Schema

from pyefa.helpers import is_date, is_datetime, is_time

from ..exceptions import EfaParameterError

_LOGGER = logging.getLogger(__name__)


class Request:
    def __init__(self, name: str, macro: str) -> None:
        self._name: str = name
        self._macro: str = macro
        self._parameters: dict[str, str] = {}
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

    def add_param(self, param: str, value: str):
        if not param or not value:
            return

        _LOGGER.debug(f'Add parameter "{param}" with value "{value}"')

        self._parameters.update({param: value})

        _LOGGER.debug("Updated parameters dict:")
        _LOGGER.debug(self._parameters)

    def add_param_datetime(self, date: str):
        if not date:
            return

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
        """Validate parameters schema and return parameters as string\n
        for URL parametrization

        Returns:
            str: parameters as string ready to use in URL
        """

        self._validate_params()

        return f"{self._name}?commonMacro={self._macro}" + self._params_str()

    def _validate_params(self):
        """Validate parameters stored for request. This step will extend parameters with default values
        as well.

        Raises:
            EfaParameterError: Validation of some parameter(s) failed
        """
        try:
            self._parameters = self._schema(self._parameters)
        except MultipleInvalid as exc:
            _LOGGER.error("Parameters validation failed", exc_info=exc)
            raise EfaParameterError from exc

    def _params_str(self) -> str:
        """Return parameters concatenated with &

        Returns:
            str: parameters as string
        """
        if not self._parameters:
            return ""

        return "&" + "&".join([f"{k}={str(v)}" for k, v in self._parameters.items()])
