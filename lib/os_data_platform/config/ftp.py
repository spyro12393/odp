from typing import Literal

from pydantic import Field

from .common import ConnectionRef, Destination, Runtime, Schedule, StrictModel


class FtpSource(StrictModel):
    auth: ConnectionRef  # Airflow FTP/SFTP Connection ID
    protocol: Literal["ftp", "sftp"] = "sftp"
    remote_path: str  # path or glob; Jinja templating resolved at runtime
    delete_after_download: bool = False


class FtpToLakeConfig(StrictModel):
    type: Literal["ftp_to_lake"]
    id: str
    owner: str | None = None
    source: FtpSource
    destination: Destination
    schedule: Schedule
    runtime: Runtime = Field(default_factory=Runtime)
