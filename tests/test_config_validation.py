from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from os_data_platform.config import load_config


def _write(tmp_path: Path, data: dict) -> Path:
    p = tmp_path / "cfg.yaml"
    p.write_text(yaml.safe_dump(data))
    return p


def _minimal_api_config() -> dict:
    return {
        "type": "api_to_lake",
        "id": "x",
        "source": {"url": "https://example.com"},
        "destination": {"type": "gcs", "bucket": "b", "path": "p/"},
        "parquet": {"fields": [{"name": "id", "type": "long"}]},
        "schedule": {"cron": "* * * * *", "start_date": "2026-01-01"},
    }


def test_minimal_api_config_loads(tmp_path: Path) -> None:
    cfg = load_config(_write(tmp_path, _minimal_api_config()))
    assert cfg.type == "api_to_lake"
    assert cfg.runtime.cpu == "500m"  # default applied


def test_unknown_field_rejected(tmp_path: Path) -> None:
    bad = _minimal_api_config()
    bad["source"]["typo_field"] = "oops"
    with pytest.raises(ValidationError):
        load_config(_write(tmp_path, bad))


def test_unknown_source_type_rejected(tmp_path: Path) -> None:
    bad = {"type": "snowflake_to_lake", "id": "x"}
    with pytest.raises(ValidationError):
        load_config(_write(tmp_path, bad))


def test_invalid_destination_type_rejected(tmp_path: Path) -> None:
    bad = _minimal_api_config()
    bad["destination"]["type"] = "azure"
    with pytest.raises(ValidationError):
        load_config(_write(tmp_path, bad))


def test_missing_required_field_rejected(tmp_path: Path) -> None:
    bad = _minimal_api_config()
    del bad["source"]
    with pytest.raises(ValidationError):
        load_config(_write(tmp_path, bad))


def test_empty_parquet_fields_rejected(tmp_path: Path) -> None:
    bad = _minimal_api_config()
    bad["parquet"]["fields"] = []
    with pytest.raises(ValidationError):
        load_config(_write(tmp_path, bad))


def test_invalid_parquet_field_type_rejected(tmp_path: Path) -> None:
    bad = _minimal_api_config()
    bad["parquet"]["fields"] = [{"name": "id", "type": "varchar"}]
    with pytest.raises(ValidationError):
        load_config(_write(tmp_path, bad))


def test_unknown_pagination_type_rejected(tmp_path: Path) -> None:
    bad = _minimal_api_config()
    bad["source"]["pagination"] = {"type": "magic"}
    with pytest.raises(ValidationError):
        load_config(_write(tmp_path, bad))


def test_cursor_pagination_requires_fields(tmp_path: Path) -> None:
    bad = _minimal_api_config()
    bad["source"]["pagination"] = {"type": "cursor"}  # missing cursor_param, cursor_response_path
    with pytest.raises(ValidationError):
        load_config(_write(tmp_path, bad))


def test_negative_retries_rejected(tmp_path: Path) -> None:
    bad = _minimal_api_config()
    bad["runtime"] = {"retries": -1}
    with pytest.raises(ValidationError):
        load_config(_write(tmp_path, bad))
