from pathlib import Path
from typing import Annotated

import yaml
from pydantic import Field, TypeAdapter

from .api import ApiToLakeConfig
from .crawler import CrawlerConfig
from .ftp import FtpToLakeConfig

JobConfig = Annotated[
    ApiToLakeConfig | FtpToLakeConfig | CrawlerConfig,
    Field(discriminator="type"),
]

_adapter: TypeAdapter[JobConfig] = TypeAdapter(JobConfig)


def load_config(path: Path) -> JobConfig:
    """Load and validate one YAML job config."""
    with path.open() as f:
        data = yaml.safe_load(f)
    return _adapter.validate_python(data)
