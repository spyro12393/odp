# os_data_platform

A config-driven data ingestion platform built on top of Airflow + Kubernetes.
Data engineers declare ingestion jobs as YAML files; the platform handles
scheduling, execution, retries, state, and landing the result in object storage.

**Status:** Phase 1 — data landing only. See [PHASE.md](PHASE.md) for milestone
progress and [REQUIREMENTS.md](REQUIREMENTS.md) for the full spec.

## What it does

Three source types are supported in Phase 1:

| Type            | Source                          | Destination     | Output         |
| --------------- | ------------------------------- | --------------- | -------------- |
| `api_to_lake`   | HTTP/REST APIs                  | GCS or MinIO    | Parquet        |
| `ftp_to_lake`   | FTP/SFTP files (PDF, XML, JPG…) | GCS or MinIO    | Raw passthrough |
| `crawler`       | Web pages (HTML, XML)           | GCS or MinIO    | Raw passthrough |

Each job is one YAML file. The platform reads the file, generates an Airflow
DAG from it, and runs the actual work inside a Kubernetes pod.

## Repo layout

```
configs/                YAML job definitions (one file = one DAG)
├── api/                  api_to_lake configs
├── ftp/                  ftp_to_lake configs
└── crawler/              crawler configs
dags/                   Airflow DAGs (populated by the DAG factory)
operators/              Thin Airflow wrappers around the lib
lib/os_data_platform/   Python package: config models, sinks, state, CLI
containers/             Dockerfiles per source type
macros/                 Project-specific Jinja macros (todate, etc.)
tests/                  Pytest suite
pyproject.toml          Project metadata, deps, lint/test config
requirements.txt        Runtime deps (mirrors pyproject.toml)
requirements-dev.txt    Dev/test deps
```

## Quickstart

### Install

Python 3.11 required. Two options — pick whichever your team uses.

**With `uv` (preferred):**
```bash
uv sync
```

**With plain `pip`:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
pip install -e .
```

### Validate a config

```bash
os-data-platform validate configs/api/example_shopify_orders.yaml
os-data-platform validate configs/                # validate every YAML under a dir
```

Output on success:
```
OK   configs/api/example_shopify_orders.yaml  (type=api_to_lake, id=shopify_orders)
All 1 config(s) valid.
```

On failure, you get per-field errors and a non-zero exit code:
```
FAIL configs/api/broken.yaml
       api_to_lake.source.url: Field required
       api_to_lake.parquet: Field required
```

This same command is what CI will run to gate PRs.

### Run tests

```bash
pytest
```

## Writing a config

Each job has the same top-level shape: `type`, `id`, `source`, `destination`,
`schedule`, `runtime`. The `source` block varies by `type`; everything else
is shared.

Minimal example (full version in [configs/api/example_shopify_orders.yaml](configs/api/example_shopify_orders.yaml)):

```yaml
type: api_to_lake
id: shopify_orders
owner: team-commerce

source:
  url: https://api.shopify.com/admin/orders.json
  auth:
    connection: shopify_prod        # Airflow Connection ID
  params:
    updated_at_min: "{{ macros.ds_add(ds, -1) }}T00:00:00Z"
    updated_at_max: "{{ ds }}T00:00:00Z"
  pagination:
    type: cursor
    cursor_param: page_info
    cursor_response_path: $.links.next
  records_path: $.orders[*]

destination:
  type: gcs                         # or 'minio'
  bucket: raw-lake-prod
  path: "shopify/orders/dt={{ ds }}/"

parquet:
  fields:
    - { name: id,         type: long,      nullable: false }
    - { name: email,      type: string }
    - { name: total,      type: double }
    - { name: created_at, type: timestamp, nullable: false }

schedule:
  cron: "0 2 * * *"
  timezone: Asia/Taipei
  start_date: "2026-01-01"

runtime:
  cpu: "500m"
  memory: "1Gi"
  retries: 3
  timeout_minutes: 30
```

### Key conventions

- **Secrets are referenced, never inlined.** `auth.connection: <id>` points at
  an Airflow Connection that holds the credentials. The platform never sees
  the secret value at parse time.
- **Jinja templating** is allowed in API URLs, params, bodies, FTP remote
  paths, crawler URLs, and destination paths. Standard Airflow macros
  (`{{ ds }}`, `{{ macros.ds_add(...) }}`) and project-specific ones
  (`{{ macros.todate(...) }}`) are available. Templates are rendered by
  Airflow at task runtime, not at config-load time.
- **Parquet schemas are explicit.** Every `api_to_lake` config must declare
  its `parquet.fields`. Drift fails the run loudly.
- **Unknown fields are rejected.** Typos like `scheudle:` are caught by the
  validator, not at 3am in production.
- **Per-job destination routing.** Each YAML picks its own sink (`gcs` or
  `minio`). Different jobs in the same repo can land in different places.

## Where things are headed

Phase 1 (in progress) lands the three source types end-to-end. Phase 2 adds
a web UI for less-technical authors. Phase 3 adds lineage, data quality, and
multi-tenant features. See [PHASE.md](PHASE.md) for the milestone breakdown.

## See also

- [REQUIREMENTS.md](REQUIREMENTS.md) — full functional and non-functional spec
- [PHASE.md](PHASE.md) — build phases, current focus, status checkboxes
