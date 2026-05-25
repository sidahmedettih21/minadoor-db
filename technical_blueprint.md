# Technical Blueprint: Client Import/Export Engine

[VERIFICATION]
- Input: Codebase audit (models, routers, services, frontend JS, locales, tests, fixtures)
- Logic: Three-stage import pipeline (parse→validate→confirm), async export with Redis job tracking
- Gaps Identified: 4 frontend/backend contract mismatches, 1 placeholder service, 1 deprecated API usage, 0 test coverage
- Edge Cases: Interleaved duplicate passport in same batch, WeasyPrint system dependency, unbounded export temp file growth
- Ground Truth: `import_service.parse_and_validate` returns hardcoded zeros — entire pipeline must be rebuilt
- Confidence: 100%

## 1. API Contract Fixes (Align Frontend ↔ Backend)

| # | Layer | Current State | Required Fix |
|---|-------|--------------|--------------|
| 1 | Route | Frontend calls `POST /clients/import` | Rename to `POST /clients/import/preview` OR add alias route |
| 2 | Confirm body | Backend expects `validation_id` as query param | Accept `{ validation_id, rows }` in POST body |
| 3 | Response keys | Backend returns `{ imported, skipped }` | Rename to `{ imported_count, duplicates_skipped }` |
| 4 | Confirm import | Uses deprecated `row.dict()` | Change to `row.model_dump()` |
| 5 | DB session | Uses wrong `async_session` (should be `AsyncSessionLocal`) | Fix import in `commit_import` |

### Final API Contract (Correct)

```
POST /api/v1/clients/import/preview
  Body: multipart/form-data { file: .xlsx | .csv }
  → { validation_id, total_rows, valid_rows, errors: [{row, field, message}], preview_data: [...] }

POST /api/v1/clients/import/confirm
  Body: { validation_id, rows: [ClientCreate, ...] }
  → { imported_count, duplicates_skipped }

POST /api/v1/clients/export
  Body: { format, search?, travel_type?, status?, gender?, travel_date_from?, travel_date_to?, header_lang }
  → { job_id }

GET /api/v1/exports/{job_id}/status
  → { job_id, status, error?, download_url? }

GET /api/v1/exports/{job_id}/download
  → FileResponse (xlsx|csv|pdf)
```

## 2. Import Pipeline Architecture

```text
[Upload File] → [parse_and_validate()] → [Redis cache: TTL 30min]
                                          ↓
                                    {validation_id, errors, preview_data}
                                          ↓
[User reviews in UI] → [confirm_import()] → [Read cached rows from Redis]
                                          ↓
                              [transaction: INSERT rows, skip duplicates by passport_number]
                                          ↓
                                    {imported_count, duplicates_skipped}
```

### Step 1: `parse_and_validate` (rewrite from placeholder)
- Detect file type by extension + magic bytes (existing `validate_import_file` intact)
- **XLSX**: openpyxl → read header row → map columns by i18n aliases → iterate rows → validate each row against `ClientCreate` schema
- **CSV**: `csv.DictReader` with BOM support → same mapping + validation
- Validation rules per row:
  - Required fields: surname, given_name, father_name, passport_number, nationality, travel_date
  - Passport uniqueness: check against existing DB (non-archived) AND against other rows in same batch
  - Date format: accept both `YYYY-MM-DD` and `DD/MM/YYYY` and `MM/DD/YYYY` with locale hint
  - Gender: must be M or F (case-insensitive)
- Store valid rows + row-level errors in Redis key `import:{validation_id}` with TTL 30min
- Return: `{ validation_id, total_rows, valid_rows, errors: [{row, field, message}], preview_data: [...] }`

### Step 2: `confirm_import` (fix existing)
- Accept `{ validation_id, rows }` in body (BREAKING CHANGE from current `validation_id` query param)
- Fetch cached rows from Redis (or use `rows` from body if provided — allows client-side editing)
- Single transaction:
  - `SELECT passport_number FROM clients WHERE passport_number IN (...)` → build existing set
  - For each row: if passport not in existing set AND not already inserted in this batch → INSERT
  - Rollback entire transaction on any failure
- Return: `{ imported_count, duplicates_skipped }`

```text
[^] Security: Input validation on every field. STRIDE: Spoofing (passport integrity), Tampering (readonly fields), Repudiation (audit log).
```

## 3. Export Pipeline

### Current State (working, with gaps)
- Background job via `BackgroundTasks`
- Supports: `.xlsx` (openpyxl), `.csv`, `.pdf` (WeasyPrint)
- i18n column headers from `HEADERS_I18N`
- Polling via Redis job status: `pending` → `completed` | `failed`

### Required Fixes

| # | Issue | Fix |
|---|-------|-----|
| 1 | Temp files never cleaned up | Add periodic cleanup task or TTL-based sweep on `/download` |
| 2 | Large exports block the event loop | Offload to Celery or thread pool; alternatively yield streaming response |
| 3 | No progress tracking | Add `progress` field to Redis job object (e.g., `{ total: 5000, done: 1200 }`) |
| 4 | PDF generation may crash if system libs missing | Add `pango`, `cairo`, `pango`, `gdk-pixbuf` to `Dockerfile` — document as build requirement |

### Cleanup Strategy
- Option A (simple): On `/download`, after serving file, `os.remove(filepath)` + update Redis to `{ status: "downloaded" }`
- Option B (robust): Background sweep every 10min via `BackgroundTasks` or cron that deletes files with `mtime > 1h`

## 4. Data Model Check

```python
class Client(Base):
    __tablename__ = "clients"
    # All existing fields correct. No schema changes needed.
    # Only gap: `payment_method` is a free string — should be an enum for import validation.
```

### Suggested import validation column map (i18n-aware):

Header alias map (extensible):
```
"en": { "surname": "surname", "given name": "given_name", "father name": "father_name",
        "mother name": "mother_name", "passport number": "passport_number",
        "passport no": "passport_number", "nationality": "nationality",
        "date of birth": "date_of_birth", "dob": "date_of_birth",
        "passport issue": "passport_issue_date", "passport expiry": "passport_expiry",
        "gender": "gender", "travel type": "travel_type_id", "travel date": "travel_date",
        "payment method": "payment_method", "payment": "payment_method",
        "notes": "notes" }
```

→ Same map needed for `fr` and `ar` aliases. This replaces the rigid column-order assumption.

## 5. Testing Strategy

| Layer | Tool | What to Test |
|-------|------|-------------|
| Unit | pytest | `parse_and_validate` with valid `.csv`, valid `.xlsx`, malformed files |
| Unit | pytest | Row-level validation: missing required fields, bad date format, invalid gender |
| Unit | pytest | Duplicate detection: intra-batch (two rows same passport) and cross-batch (passport already in DB) |
| Integration | httpx + test DB | `POST /import/preview` → verify response shape |
| Integration | httpx + test DB | `POST /import/confirm` → verify rows inserted, duplicates skipped |
| Integration | httpx + test DB | `POST /export` + `GET /exports/{id}/status` + `GET /exports/{id}/download` → verify file exists |
| Security | pytest | Attempt to import with invalid JWT (returns 401) |
| Security | pytest | Attempt to export without auth (returns 401) |
| Fixtures | CSV/XLSX | Provide `valid_en.csv`, `valid_en.xlsx`, `partial_errors.csv`, `duplicates.csv` |

### Test file fixtures to create:
- `backend/tests/fixtures/valid_en.csv` (exists — 1 row, good)
- `backend/tests/fixtures/valid_en.xlsx` (add — same data as CSV)
- `backend/tests/fixtures/partial_errors.csv` (3 rows: 2 valid, 1 missing surname, 1 bad gender)
- `backend/tests/fixtures/duplicates.csv` (2 rows with same passport number)
- `backend/tests/fixtures/empty.csv`
