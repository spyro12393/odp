# os_data_platform — Requirements (Phase 1)

## 1. Purpose

A config-driven sourcing platform that lets data engineers declare ingestion
jobs in YAML and have them executed, scheduled, retried, and monitored without
writing per-job orchestration code. Phase 1 focuses on **data landing only** —
raw bytes/records arrive in object storage; transforms happen downstream.

## 2. Users

- **Primary (Phase 1):** internal data engineers, comfortable with YAML and Git.
  Configs are added/edited via pull request.
- **Secondary (future phase):** less technical users via a web UI that writes to
  the same config source of truth.

## 3. In-scope source types

| Type            | Source                          | Destination     | Format         |
| --------------- | ------------------------------- | --------------- | -------------- |
| `api_to_lake`   | HTTP/REST APIs                  | GCS or MinIO    | Parquet        |
| `ftp_to_lake`   | FTP/SFTP files (PDF, XML, JPG…) | GCS or MinIO    | Raw passthrough |
| `crawler`       | Web pages (HTML, XML)           | GCS or MinIO    | Raw passthrough |

`api_to_lake` is the dominant workload; the other two must work but are lower
volume.

## 4. Functional requirements

### 4.1 Config-driven jobs
- Each ingestion job is defined by exactly one YAML file under `configs/`.
- Configs are validated at CI time (schema check) and again at DAG parse time.
- Secrets are **referenced**, never inlined. The reference is an **Airflow
  Connection ID** (e.g. `auth.connection: shopify_prod`); the platform never
  sees the secret value at config-parse time — it resolves at task runtime via
  `BaseHook.get_connection(...)`.
- Non-secret common configurables (e.g. shared base URLs, environment names)
  may be sourced from **Airflow Variables** and referenced from configs.

### 4.2 Scheduling
- Cron expression with explicit timezone.
- Backfill supported via standard Airflow CLI.
- Catchup behavior configurable per job (default: off).

### 4.3 Dynamic templating
- Jinja templating available in API URLs, params, bodies, and destination paths.
- Built-in Airflow macros (`{{ ds }}`, `{{ macros.ds_add(...) }}`, etc.).
- Project-specific macros registered centrally (e.g. `todate()`, `kst_now()`).

### 4.4 Destinations
- Two supported sinks in Phase 1: **GCS** and **MinIO** (S3-compatible).
- Selection is **per-job in the config** (`destination.type: gcs|minio`).
- Both sinks accessed via a single internal `Sink` interface so configs do not
  leak SDK details.

### 4.5 Execution
- All ingestion work runs in **`KubernetesPodOperator`** tasks on the existing
  K8s cluster, not in the Airflow worker process.
- One container image per source type (`ingest-api`, `ingest-ftp`,
  `ingest-crawler`), each calling into a shared internal Python library.
- Images are published to a **self-hosted Harbor/Nexus registry**.
- Per-task CPU/memory limits and timeout are configurable.

### 4.6 Reliability
- Per-task retries with exponential backoff, configurable.
- On-failure notification (Slack at minimum).
- Idempotent writes: a re-run for the same logical window does not corrupt or
  duplicate prior output (strategy: partition-overwrite on `dt=` prefix).

### 4.7 State / incremental ingestion
- Watermark state stored in a **dedicated Postgres database** owned by the
  platform. Not in Airflow `Variable`/`XCom`, and not co-located in the
  Airflow metadata DB.
- Each job has a single named watermark; advancement is atomic with successful
  write.

### 4.8 Observability
- Per-run metrics: rows in, bytes out, duration, retry count.
- Logs accessible via the Airflow UI (stdout/stderr from pods).
- Lineage / OpenLineage integration is **deferred** to a later phase.

### 4.9 Parquet schema management (`api_to_lake`)
- Schema is **explicit per config** — each `api_to_lake` YAML declares the
  output parquet schema (field names, types, nullability).
- Drift fails the run loudly rather than silently coercing.
- Schema may be declared inline or by `schema_ref:` to a shared schema file.

## 5. Non-functional requirements

- **Throughput:** target sizing is unknown in Phase 1 → use medium-tier safe
  defaults (chunked/streamed parquet writes, ~2Gi pod memory baseline). Revisit
  per source as real volumes are observed.
- **Isolation:** one bad job (hang, OOM, IP ban) must not impact other jobs.
- **Onboarding cost:** adding a new API source = one YAML file + PR; no Python
  changes for the common case.
- **Local dev:** a developer can validate a config and dry-run a single task
  locally without touching the cluster.

## 6. Architecture summary

```
Git repo (monorepo)
├── configs/                YAML job definitions (one file = one DAG)
│   ├── api/
│   ├── ftp/
│   └── crawler/
├── dags/
│   └── dag_factory.py      reads configs/, emits DAGs at parse time
├── operators/              thin Airflow wrappers around the lib
├── lib/                    os_data_platform Python package (fetch, sinks, state)
├── containers/             Dockerfiles per source type
└── macros/                 project Jinja macros (todate, kst_now, …)
```

Execution path:
```
YAML config → dag_factory → DAG → KubernetesPodOperator
                                  → container (lib code)
                                  → GCS / MinIO
                                  → watermark update (Postgres)
```

## 7. Tech stack

- **Orchestrator:** existing Airflow service
- **Execution:** existing Kubernetes cluster, `KubernetesPodOperator`
- **Language:** Python 3.11
- **Toolchain:** `uv` (env/deps), `ruff` (lint+format), `pytest` (tests)
- **Config validation:** Pydantic v2
- **Sinks:** GCS, MinIO (S3-compatible)
- **Parquet:** PyArrow, explicit schema per config
- **State store:** dedicated Postgres (separate from Airflow metadata DB)
- **Secrets:** Airflow Connections (referenced by connection ID) + Airflow
  Variables for non-secret common configurables
- **Container registry:** self-hosted Harbor/Nexus

## 8. Non-goals (Phase 1)

- Transforms beyond what's needed to land parquet (no dbt-style modeling).
- Web UI for config authoring.
- Streaming / event-driven ingestion (cron-scheduled batch only).
- Data quality assertions / Great Expectations integration.
- OpenLineage / column-level lineage.
- Multi-tenant quotas and per-team isolation.
- Auto-scaling of the Airflow scheduler/workers themselves.

## 9. Decisions & remaining open questions

### Resolved
1. **Secrets backend** → Airflow Connections (by ID) + Airflow Variables for
   non-secret configurables. No external vault in Phase 1.
2. **State store location** → new dedicated Postgres instance.
3. **MinIO vs GCS routing** → per-job in the config.
4. **Container registry** → self-hosted Harbor/Nexus.
5. **Volume sizing** → unknown; use medium-tier safe defaults and revisit per
   source.
6. **Parquet schema policy** → explicit schema required in each config.
7. **Python toolchain** → uv + ruff + pytest, Python 3.11.
8. **DAG factory scale strategy** → default to one generated `.py` per DAG (CI
   step), to keep scheduler parse time bounded as configs grow.

### Still open
- **Crawler egress identity** — direct from pod or via shared proxy/NAT?
  Decision deferred to M6 when the crawler is built.
