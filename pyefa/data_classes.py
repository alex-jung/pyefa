from dataclasses import dataclass, field
from datetime import date, datetime
from enum import IntEnum, StrEnum


@dataclass
class SystemInfo:
    version: str
    data_format: str
    valid_from: date
    valid_to: date


class StopType(StrEnum):
    STOP = "stop"
    POI = "poi"
    ADDRESS = "address"
    STREET = "street"
    LOCALITY = "locality"


class TransportType(IntEnum):
    SUBWAY = 2
    TRAM = 4
    BUS = 5
    RE = 6


class StopFilter(IntEnum):
    NO_FILTER = 0
    LOCATIONS = 1
    STOPS = 2
    STREETS = 4
    ADDRESSES = 8
    INTERSACTIONS = 16
    POIS = 32
    POST_CODES = 64


@dataclass
class Stop:
    id: str
    name: str
    type: StopType
    disassembled_name: str = field(repr=False, default="")
    coord: list[int] = field(default_factory=list)
    transports: list[TransportType] = field(default_factory=list)


@dataclass
class Departure:
    line_name: str
    route: str
    origin: Stop
    destination: Stop
    transport: TransportType
    planned_time: datetime
    actual_time: datetime | None
