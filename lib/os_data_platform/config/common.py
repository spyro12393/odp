from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ConnectionRef(StrictModel):
    connection: str  # Airflow Connection ID; resolved at task runtime


class Schedule(StrictModel):
    cron: str
    timezone: str = "UTC"
    start_date: date
    catchup: bool = False


class Runtime(StrictModel):
    pod_image: str | None = None  # default selected by source type if unset
    cpu: str = "500m"
    memory: str = "2Gi"
    retries: int = Field(default=3, ge=0)
    retry_backoff_seconds: int = Field(default=60, ge=0)
    timeout_minutes: int = Field(default=30, ge=1)
    on_failure_slack: str | None = None


class Destination(StrictModel):
    type: Literal["gcs", "minio"]
    bucket: str
    path: str  # Jinja templating resolved at runtime


class ParquetField(StrictModel):
    name: str
    type: Literal[
        "string", "int", "long", "float", "double", "bool", "timestamp", "date"
    ]
    nullable: bool = True


class ParquetOptions(StrictModel):
    fields: list[ParquetField] = Field(min_length=1)
    compression: Literal["snappy", "gzip", "zstd"] = "snappy"
