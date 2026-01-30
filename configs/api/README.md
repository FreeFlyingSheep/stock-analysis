# API Reference Configs

[English](README.md) | [中文](README.zh-CN.md)

## Purpose

- Define upstream API contracts for each provider.
- Serve adapters as the single source of truth for calls and parsing logic.

## Layout

- Provider folders:
  - `cninfo/` for CNInfo REST endpoints
  - `yahoo/` for Yahoo Finance schema definitions
- One YAML per endpoint, named with `snake_case` (for example, `get_balance_sheets.yaml`).
- Each YAML pairs with a real response example under `data/api` using the endpoint id.

## Naming conventions

- The canonical endpoint id is `api.id` inside the YAML.
- Sample data files use the id for filenames.

Example:

- Config: `configs/api/cninfo/get_balance_sheets.yaml`
- Endpoint id: `balance_sheets`
- Sample data: `data/api/cninfo/balance_sheets.json`

## YAML structure (CNInfo)

- `api`: identifiers and how to call the endpoint.
  - `id`, `name`: stable, human-readable identifiers.
  - `request`: `method`, `url`, and `params` (types, required flags, and any fixed values).
- `response`: contract for the returned payload.
  - Static fields (for example, `path.value`, `code.value`) capture invariants we expect.
  - `data` and children describe shapes (`object`, `array`, `string`, `number`) and dynamic markers (for example, `dynamic: true`, `label: <YYYY>` for yearly columns).
  - Use these definitions to guide parsing and detect upstream changes.
- `params` (when present): wrapper object structure expected by the API.

## YAML structure (Yahoo)

- Yahoo specs focus on response schema only; request details are handled by `yfinance` in the adapter.

## Adding or updating an endpoint

1. Copy a nearby YAML as a template.
2. Set `api.id`, `api.name`, `request.method`, and `request.url` to match the upstream endpoint (CNInfo only).
3. Document every request param with type, required flag, and fixed value when applicable.
4. Mirror the response shape using existing conventions; keep static value entries for known invariants.
5. Capture a fresh real response into `data/api/<provider>/<id>.json` and confirm it matches the schema.

## Related files

- CNInfo adapter: `src/stock_analysis/adapters/cninfo.py`
- Yahoo adapter: `src/stock_analysis/adapters/yahoo.py`
- Sample data: `data/api/README.md`

## Notes

- Keep configs and sample data in sync whenever upstream contracts change.
- Prefer concise structure descriptions; use patterns (like `items` with `dynamic` labels) instead of repeating every leaf.
