# Build Phases & Status

Tracks build progress toward the goals defined in [REQUIREMENTS.md](REQUIREMENTS.md).
Update the checkboxes as work lands; keep the "Current focus" pointer accurate.

**Status legend:** `[ ]` not started · `[~]` in progress · `[x]` done · `[!]` blocked

**Current focus:** Phase 1 / M1 — Config Schema (M0 scaffolding done, CI workflow file deferred to when CI host is chosen)

---

## Phase 1 — Data Landing (in progress)

Goal: meet the acceptance criteria in [REQUIREMENTS.md §10](REQUIREMENTS.md#10-acceptance-criteria-for-phase-1).
One real, scheduled pipeline working end-to-end for each of `api_to_lake`,
`ftp_to_lake`, and `crawler`, defined entirely in YAML.

### M0 — Decisions & Scaffolding
- [x] Draft REQUIREMENTS.md
- [x] Draft PHASE.md (this document)
- [x] Resolve open questions in [REQUIREMENTS.md §9](REQUIREMENTS.md#9-decisions--remaining-open-questions) (crawler egress deferred to M6)
- [x] Initialize git repo
- [x] Monorepo skeleton: `configs/`, `dags/`, `operators/`, `lib/`, `containers/`, `macros/`
- [x] Python project setup (`pyproject.toml`, lint, format, test runner)
- [ ] CI skeleton (lint + test on PR) — deferred, blocked on CI host choice (GitHub Actions / GitLab CI / Jenkins / ?)

### M1 — Config Schema
- [ ] Pydantic models for shared blocks (`schedule`, `runtime`, `destination`, `auth`)
- [ ] Pydantic models per source type (`api_to_lake`, `ftp_to_lake`, `crawler`)
- [ ] YAML loader + validator CLI (`os-data-platform validate <path>`)
- [ ] CI hook that validates every file under `configs/`
- [ ] Example reference configs for all three source types

### M2 — Platform Library Core
- [ ] `Sink` interface
- [ ] GCS sink implementation
- [ ] MinIO sink implementation
- [ ] Watermark store: Postgres schema + Python client
- [ ] Structured logging + basic run-metrics emission
- [ ] Local-run harness (`os-data-platform run <config>`)

### M3 — DAG Factory
- [ ] `dag_factory.py` reads `configs/`, emits one DAG per file
- [ ] `KubernetesPodOperator` wrapper: config → pod spec (image, resources, env)
- [ ] Custom Jinja macros registered (`todate`, project tz helpers)
- [ ] Documented backfill workflow (CLI command + when to use)
- [ ] DAG-parse-time validation (fail loud on bad config)

### M4 — Source: `api_to_lake` (end-to-end)
- [ ] Container image `ingest-api`
- [ ] HTTP fetcher: auth, pagination, rate limiting, retry on transient errors
- [ ] Records → parquet writer (PyArrow), partition-overwrite semantics
- [ ] **Real pipeline** against one production API, landing to GCS and MinIO
- [ ] Watermark advancement verified across two consecutive runs
- [ ] Working `todate()`-style dynamic parameter in the config

### M5 — Source: `ftp_to_lake` (end-to-end)
- [ ] Container image `ingest-ftp`
- [ ] FTP/SFTP fetcher with streaming (no full buffering in memory)
- [ ] **Real pipeline** pulling binary files (PDF/XML/photo) to GCS and MinIO

### M6 — Source: `crawler` (end-to-end)
- [ ] Pick crawler runtime (Scrapy vs Playwright vs plain `httpx`)
- [ ] Container image `ingest-crawler`
- [ ] **Real pipeline** fetching HTML pages to GCS and MinIO
- [ ] Per-job timeout and resource limits enforced

### M7 — Production Hardening
- [ ] Secrets backend wired up (per decision in §9)
- [ ] Slack failure notification on task failure
- [ ] On-call runbook: backfill, common failures, debugging a stuck pod
- [ ] Load/soak test against the largest expected source
- [ ] Documented onboarding flow for a new data engineer adding a config

### Phase 1 Exit
- [ ] All [REQUIREMENTS.md §10](REQUIREMENTS.md#10-acceptance-criteria-for-phase-1) criteria met
- [ ] Retrospective: what to keep, what to redesign before Phase 2

---

## Phase 2 — Web UI (future)

Goal: less-technical users can author and edit ingestion configs through a UI
that writes to the same Git source of truth (via PRs, not a separate DB).

High-level scope (to be expanded when Phase 1 nears exit):
- Config editor with schema-driven form generation
- Job catalog / search
- Per-job run history view (links into Airflow UI for deep dives)
- Authentication and basic RBAC

---

## Phase 3 — Observability & Multi-tenancy (future)

- OpenLineage / column-level lineage integration
- Data quality assertions (Great Expectations or equivalent)
- Per-team quotas, isolated credentials, audit logging
- Cost attribution per source/team
