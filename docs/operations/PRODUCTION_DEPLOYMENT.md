# Production Deployment Runbook

`docker-compose.production.yml` is the production-shaped deployment contract.
It starts PostgreSQL and Redis first, runs the one-shot `migrate` service, and
only then starts the API and RQ worker services.

## Required variables

Set these in the deployment secret store or an uncommitted environment file:

```text
POSTGRES_PASSWORD=...
AITEST_API_KEY=...
AITEST_WORKER_AUTH_SECRET=...
TEST_PROJECT_PATH=/absolute/path/to/project
```

Optional provider variables are passed to the worker, including
`MIMO_API_KEY`, `MIMO_BASE_URL`, and `MIMO_MODEL`.

## Start and verify

```bash
docker compose -f docker-compose.production.yml up -d --build
docker compose -f docker-compose.production.yml ps
curl -f http://127.0.0.1:8000/ready
docker compose -f docker-compose.production.yml logs --no-log-prefix migrate
```

The migration service is idempotent. It creates the SQLAlchemy ORM tables,
applies the tracked PostgreSQL SQL migrations, and records checksums in
`aitest_schema_migrations`. A changed migration file fails closed instead of
silently running schema drift.

## RQ recovery

The API runs a non-blocking stale-job recovery loop when Redis/RQ is selected.
Tune `AITEST_RQ_RECOVERY_INTERVAL` and `AITEST_RQ_STALE_AFTER` for the expected
long-task duration. The AgentLoop worker writes a JSON checkpoint to Redis after
each completed Skill (`aitest:agentloop:checkpoint:<job_id>`, seven-day TTL).
When a stale job is requeued, it is marked `mode=resume`; the worker restores
the last checkpoint and starts at the first unfinished Skill. If the process is
killed inside a Skill, that one Skill is retried from its entry point because
provider-token streaming is not checkpointed. Jobs without a checkpoint are
explicitly recorded as `entrypoint_restart_no_checkpoint` in RQ job metadata.

The local Linux staging probe validates this contract with the production
`_run_agent_task` entry point, a worker SIGKILL, Redis stale recovery, and two
concurrent workers:

```bash
RQ_REAL_AGENTLOOP=1 python scripts/rq_linux_recovery_probe.py
```
