from typing import Annotated, Any, Literal

from pydantic import Field

from .common import (
    ConnectionRef,
    Destination,
    ParquetOptions,
    Runtime,
    Schedule,
    StrictModel,
)


class NoPagination(StrictModel):
    type: Literal["none"]


class OffsetPagination(StrictModel):
    type: Literal["offset"]
    offset_param: str
    limit_param: str
    page_size: int = Field(gt=0)


class CursorPagination(StrictModel):
    type: Literal["cursor"]
    cursor_param: str  # request param that carries the cursor
    cursor_response_path: str  # JSONPath to next cursor in the response


Pagination = Annotated[
    NoPagination | OffsetPagination | CursorPagination,
    Field(discriminator="type"),
]


class ApiSource(StrictModel):
    url: str
    method: Literal["GET", "POST"] = "GET"
    headers: dict[str, str] = Field(default_factory=dict)
    params: dict[str, Any] = Field(default_factory=dict)
    body: dict[str, Any] | None = None
    auth: ConnectionRef | None = None
    pagination: Pagination = Field(default=NoPagination(type="none"))
    records_path: str = "$"  # JSONPath to the array of records in the response
    rate_limit_rps: float | None = Field(default=None, gt=0)


class ApiToLakeConfig(StrictModel):
    type: Literal["api_to_lake"]
    id: str
    owner: str | None = None
    source: ApiSource
    destination: Destination
    parquet: ParquetOptions
    schedule: Schedule
    runtime: Runtime = Field(default_factory=Runtime)
