# UniHR Backup Restore Drill

Last Updated: 2026-03-23

## Goal

Validate that production backups are:

- created successfully;
- structurally valid;
- restorable into an isolated environment;
- usable enough to recover core application tables.

## Tools Already in Repo

- `scripts/backup.sh` — create compressed PostgreSQL backup
- `scripts/restore.sh` — destructive restore into target database
- `scripts/verify_backup.sh` — non-destructive sandbox restore verification

## Drill Frequency

- Backup creation: daily
- Sandbox restore verification: weekly
- Full documented restore drill: at least monthly and before major releases

## Preconditions

- Docker is available on the operator machine or target host
- Current production backup exists, or `scripts/backup.sh` can be run
- Operator has access to PostgreSQL credentials and deployment host

## Standard Drill Procedure

### 1. Generate or select backup

Use an existing backup file or create a fresh one:

```bash
./scripts/backup.sh
```

### 2. Run non-destructive verification

Restore into an isolated sandbox container and verify core tables:

```bash
./scripts/verify_backup.sh
```

To validate a specific file:

```bash
./scripts/verify_backup.sh backups/unihr_YYYYMMDD_HHMMSS.sql.gz
```

### 3. Record results

Capture the following in the operations log or ticket:

- backup file name and timestamp;
- backup file size;
- sandbox restore success/failure;
- public-schema table count;
- core table verification results for `users`, `tenants`, `documents`, `conversations`;
- operator name and review timestamp.

## Full Restore Drill

Use only in a disposable environment or approved maintenance window.

```bash
./scripts/restore.sh backups/unihr_YYYYMMDD_HHMMSS.sql.gz
```

Expected result:

- database is dropped and recreated;
- application services restart successfully;
- table count is non-zero and expected schema exists.

## Acceptance Criteria

The drill passes only if all of the following are true:

- backup archive passes `gzip -t` integrity check;
- sandbox PostgreSQL starts successfully;
- SQL restore completes without fatal corruption;
- core tables are present after restore;
- no unexplained schema loss is observed.

## Failure Handling

If the drill fails:

1. preserve the failing backup file;
2. collect script output and restore errors;
3. classify the failure as backup creation, archive integrity, restore compatibility, or schema/data issue;
4. open an incident or ops task before the next production deploy;
5. do not mark the backup policy as healthy until a new drill passes.

## Recommended Scheduling

```cron
# Daily production backup at 02:00
0 2 * * * cd /srv/aihr && ./scripts/backup.sh >> /var/log/unihr-backup.log 2>&1

# Weekly sandbox restore verification on Sunday at 03:00
0 3 * * 0 cd /srv/aihr && ./scripts/verify_backup.sh >> /var/log/unihr-backup-verify.log 2>&1
```

## Evidence Retention

Retain drill evidence for at least 90 days:

- command output;
- operator/reviewer name;
- date/time;
- backup filename;
- pass/fail outcome;
- remediation ticket if failed.