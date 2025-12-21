# Data API Samples

## Purpose

- Store real API responses for offline development, parser tests, and contract checks.
- Avoid unnecessary upstream traffic while keeping examples faithful to production.

## Layout

- Provider folders (for example, `cninfo/`).
- One pretty-printed JSON file per endpoint, named after the upstream path (e.g., `getBalanceSheets.json`).
- Filenames map 1:1 to the reference configs under [configs/api](../../configs/api) (snake_case in configs, camelCase here for the raw endpoint name).

## Workflow to add or refresh

1. Call the real endpoint (prefer the adaptor so params/headers match production).
2. Save the full JSON response to `data/api/<provider>/<endpoint>.json`.
3. Strip secrets or identifying values if they appear; keep structure intact.
4. Preserve top-level `path` and `code` fields so schema checks remain meaningful.
5. If payloads are huge, you may truncate repetitive arrays, but leave at least one full record for every shape the adaptor parses.

## Notes

- Treat these files as canonical examples; update them alongside the configs in `configs/api` when upstream contracts change.
- Do not hand-edit structures—regenerate from real calls to avoid drift.
