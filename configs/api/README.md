# API Reference Configs

## Purpose

- Define upstream API contracts for each provider.
- Serve adaptors (see [src/stock_analysis/adaptors/cninfo.py](../../src/stock_analysis/adaptors/cninfo.py)) and developers as the single source of truth for calls and parsing logic.

## Layout

- Provider-specific folders (currently `cninfo/`).
- One YAML per endpoint, named with snake_case (e.g., `get_balance_sheets.yaml`).
- Each YAML pairs with a real response example under [data/api](../../data/api) using the matching endpoint name.

## YAML structure (CNInfo)

- `api`: identifiers and how to call the endpoint.
  - `id`, `name`: stable, human-readable identifiers.
  - `request`: `method`, `url`, and `params` (types, required flags, and any fixed values).
- `response`: contract for the returned payload.
  - Static fields (for example, `path.value`, `code.value`) capture invariants we expect.
  - `data` and children describe shapes (`object`, `array`, `string`, `number`) and dynamic markers (for example, `dynamic: true`, `label: <YYYY>` for yearly columns).
  - Use these definitions to guide parsing and detect upstream changes.
- `params` (when present): wrapper object structure expected by the API.

## Adding or updating an endpoint

1. Copy a nearby YAML as a template.
2. Set `api.id`, `api.name`, `request.method`, and `request.url` to match the upstream endpoint.
3. Document every request param with type, required flag, and fixed `value` when applicable.
4. Mirror the response shape using existing conventions; keep static `value` entries for known invariants.
5. Capture a fresh real response into `data/api/<provider>/<endpoint>.json` and confirm it matches the schema.

## Notes

- Keep configs and sample data in sync whenever upstream contracts change.
- Prefer concise structure descriptions; use patterns (like `items` with `dynamic` labels) instead of repeating every leaf.
