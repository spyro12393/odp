from pathlib import Path

import pytest

from os_data_platform.config import load_config

CONFIGS_DIR = Path(__file__).parent.parent / "configs"
EXAMPLE_CONFIGS = sorted(CONFIGS_DIR.rglob("*.yaml"))


@pytest.mark.parametrize(
    "path",
    EXAMPLE_CONFIGS,
    ids=lambda p: str(p.relative_to(CONFIGS_DIR)),
)
def test_example_config_loads(path: Path) -> None:
    cfg = load_config(path)
    assert cfg.id
    assert cfg.type
    assert cfg.destination.type in {"gcs", "minio"}


def test_at_least_one_example_per_source_type() -> None:
    types = {load_config(p).type for p in EXAMPLE_CONFIGS}
    assert types == {"api_to_lake", "ftp_to_lake", "crawler"}
