# Implementation Tasks: Client Import/Export Engine

## Phase 1: Contract Alignment [√]

- [x] T1: Fix import route path — update frontend `app.js:347` from `/clients/import` to `/clients/import/preview`
- [x] T2: Fix confirm endpoint — change `validation_id` from query param to body `{ validation_id, rows }` in `clients.py` + `import_service.py`
- [x] T3: Fix response keys — rename `imported` → `imported_count`, `skipped` → `duplicates_skipped` in `import_service.py` + route handler
- [x] T4: Fix deprecated API — change `row.dict()` → `row.model_dump()` and `async_session` → `AsyncSessionLocal` in `import_service.py`

## Phase 2: Import Parsing Engine [⊕]

- [x] T5: Build i18n header alias map — define `HEADER_ALIASES` dict for `en`, `fr`, `ar` that maps spreadsheet column names to model field names
- [x] T6: Implement CSV parser — read file with `csv.DictReader`, BOM support, map headers via alias map, yield dicts
- [x] T7: Implement XLSX parser — read file with `openpyxl`, iterate rows, map headers via alias map, yield dicts
- [ ] T8: Implement row validator — check required fields, date formats, gender; return `{ row_index, field, message }` errors
- [ ] T9: Implement intra-batch duplicate detection — within parsed rows, detect duplicate `passport_number` entries
- [ ] T10: Wire `parse_and_validate` — call parser → validator → duplicate check → store valid rows in Redis → return preview

## Phase 3: Import Confirmation & Transaction [∞]

- [ ] T11: Rewrite `commit_import` — single transaction, read rows from body, check DB for existing passports, INSERT new, rollback on failure, return correct response keys
- [ ] T12: Add cross-batch duplicate check — query non-archived clients by passport_number set, skip existing

## Phase 4: Export Hardening [^]

- [ ] T13: Fix export temp file cleanup — add `os.remove(filepath)` after serving download in `exports.py`, update Redis status to `downloaded`

## Phase 5: Test Fixtures & Test Cases [√]

- [ ] T14: Create test fixtures — `valid_en.xlsx` (add), `partial_errors.csv`, `duplicates.csv`, `empty.csv`
- [ ] T15: Unit test — CSV parser with valid and malformed files
- [ ] T16: Unit test — XLSX parser with valid and malformed files
- [ ] T17: Unit test — row validator: missing fields, bad dates, bad gender
- [ ] T18: Unit test — duplicate detection: same passport in batch AND same passport in DB
- [ ] T19: Integration test — full import flow: upload preview → confirm → verify inserted rows
- [ ] T20: Integration test — full export flow: request → poll status → download → verify file content
