from typing import Literal

from pydantic import Field

from .common import Destination, Runtime, Schedule, StrictModel


class CrawlerSource(StrictModel):
    urls: list[str] = Field(min_length=1)  # Jinja templating resolved at runtime
    method: Literal["GET"] = "GET"
    headers: dict[str, str] = Field(default_factory=dict)
    user_agent: str | None = None
    follow_links: bool = False
    max_depth: int = Field(default=1, ge=1)
    rate_limit_rps: float | None = Field(default=None, gt=0)


class CrawlerConfig(StrictModel):
    type: Literal["crawler"]
    id: str
    owner: str | None = None
    source: CrawlerSource
    destination: Destination
    schedule: Schedule
    runtime: Runtime = Field(default_factory=Runtime)
