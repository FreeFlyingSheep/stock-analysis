# Rules Directory

This directory contains **rule definitions** used by the fundamental scoring engine.

All rules are expressed in **YAML** and act as a **domain-specific language (DSL)** describing:

- What metrics to compute
- How to score metrics
- How to apply filters
- How dimensions combine into overall scores

The engine is designed to **execute rules, not hard-code logic**.

## Purpose

The `rules/` directory is responsible for:

- Defining **scoring logic** in a declarative way
- Enabling **rule iteration without code changes**
- Serving as the single source of truth for evaluation criteria

Rules in this directory are intended to be:

- Machine-readable
- Deterministic
- Explainable
- Version-controlled

## Contents

```text
rules/
├── scoring_rules.yaml              # Primary scoring rule set
├── scoring_rules_sample.yaml       # Simplified example rule set
└── README.md
```

### `scoring_rules.yaml`

The **primary production rule set** based on the "赢家宝典" (Winners Bible) investment framework.

Structure:

- **Dimensions**: Objective Fundamentals (50%) + Subjective Analysis (50%)
- **Metrics**: Specific financial indicators computed from CNInfo/Yahoo Finance data
- **Filters**: Rules for excluding stocks that fail certain criteria

### `scoring_rules_sample.yaml`

A **simplified example rule set** suitable for:

- Testing the rule engine
- Reference implementation
- Development and experimentation

## YAML Structure

Each ruleset YAML contains the following top-level sections under `ruleset`:

```yaml
ruleset:
  id: <rule_id>
  version: "x.y.z"
  name: "<human_readable_name>"
  total_score_scale: 100

  dimensions:
    - id: <dimension_id>
      name: "<dimension_name>"
      weight: <0-100>
      enabled: true|false

  metrics:
    - id: <metric_id>
      name: "<metric_name>"
      dimension: <dimension_id>
      metric: <metric_type>
      description: "<description>"
      params: { ... }
      max_score: <float>
      weight: <0-100>
      enabled: true|false

  filters:
    - id: <filter_id>
      name: "<filter_name>"
      metric: <metric_id>
      filter: <filter_type>
      description: "<description>"
      params: { ... }
      enabled: true|false
```

### Fields Reference

- **dimension**: Groups related metrics; each has a weight contributing to total score
- **metric**: Computed from raw data (CNInfo balance sheets, income statements, Yahoo Finance historical data)
  - `metric` field specifies computation type (e.g., `roe_weighted_average`, `gross_margin`)
  - `params` contains metric-specific configuration
  - `max_score` defines highest achievable score
  - `weight` determines metric's contribution to dimension score
- **filter**: Screening rules to exclude stocks
  - `filter` field specifies filter type (e.g., `threshold`)
  - `params` contains filter-specific thresholds/conditions
  - Stocks failing enabled filters are marked as excluded

## Execution Model

The scoring engine executes rules in this order:

1. Load the YAML rule set
2. Validate schema and references
3. Retrieve required raw data from database (stocks, API responses)
4. Compute metrics for each stock
5. Apply filters to determine stock eligibility
6. Assign scores to metrics
7. Aggregate metric scores by dimension
8. Calculate final overall score (0-100)
9. Store results in analysis table

## Design Principles

Rules in this directory follow these principles:

- **Configuration over code**: All logic in YAML, no hardcoded thresholds
- **Explicit dependencies**: Metrics declare which data fields they need
- **No hidden assumptions**: Clear weights, scales, and computation methods
- **Separation of data, logic, and execution**: YAML defines logic; engine executes it

This allows new rules to be added or modified without changing the scoring engine code.

## Adding New Rules

To add a new rule set:

1. Create `scoring_rules_<name>.yaml` in this directory
2. Define `ruleset` with unique `id`, `version`, `name`, and `total_score_scale`
3. Add scoring `dimensions` with descriptive names and weights
4. Define `metrics` with:
   - Unique `id` and human-readable `name`
   - Reference to target `dimension`
   - `metric` type matching available metric implementations
   - `max_score` and `weight` for scoring calculation
   - `params` with metric-specific configuration
5. Add `filters` for stock exclusion rules if needed
6. Update `settings.py` `RULE_FILE_PATH` to point to new rule file

## Available Metric Types

Common metric types supported by the rule engine:

- `roe_weighted_average`: Return on Equity (多年加权平均)
- `gross_margin`: Gross profit margin
- `net_margin`: Net profit margin
- `profit_growth`: Year-over-year profit growth
- `ocf_ratio`: Operating cash flow to net income ratio
- `debt_ratio`: Total debt to total assets

## Versioning Rules

When updating rules:

1. Increment `version` field in ruleset
2. Document changes in comments
3. Test thoroughly with historical stock data
4. Consider backward compatibility if scores are stored
5. Add new versions alongside old ones if needed for comparison

- Copying an existing YAML file
- Modifying metrics, thresholds, or weights
- Bumping the `version` field

Multiple rulesets may coexist and be selected at runtime by `ruleset.id`.

## Notes

- These rules define _how_ scoring is performed, not _how data is collected_.
- Data acquisition and normalization are handled outside this directory.
- No investment recommendations are implied by any ruleset.
