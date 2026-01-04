# Rules Directory

This directory contains **rule definitions** used by the fundamental scoring engine.

All rules are expressed in **YAML** and act as a **domain-specific language (DSL)** describing:

- What data fields are required
- How metrics are derived from raw data
- How scores are calculated from metrics

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
├── ppt-sample-min.yaml
└── README.md
```

### `ppt-sample-min.yaml`

A **minimal executable ruleset sample**.

It is intentionally simplified and exists to:

- Validate rule parsing
- Validate metric computation
- Validate scoring execution
- Serve as a baseline for further rule development

This file is suitable for:

- Unit testing
- Engine bring-up
- Reference implementation

## Rule Structure Overview

Each ruleset YAML typically contains the following top-level sections:

- `ruleset`
  Metadata, scope, and execution settings

- `dimensions`
  High-level scoring categories and weights

- `fields`
  Mapping between logical fields and raw data sources

- `derived_metrics`
  Calculated metrics based on raw fields

- `scoring`
  Rules that convert metrics into points

The scoring engine is expected to interpret these sections sequentially.

## Execution Model

A typical execution flow for a ruleset in this directory is:

1. Load the YAML file
2. Validate schema and references
3. Resolve required raw data fields
4. Compute derived metrics
5. Aggregate metric values over time
6. Apply scoring rules
7. Combine dimension scores
8. Output a final score

## Design Principles

Rules in this directory follow these principles:

- **Configuration over code**
- **Explicit dependencies**
- **No hidden assumptions**
- **Separation of data, logic, and execution**

This allows new rules to be added or modified without changing the scoring engine.

## Extending the Rules

New rulesets can be added to this directory by:

- Copying an existing YAML file
- Modifying metrics, thresholds, or weights
- Bumping the `version` field

Multiple rulesets may coexist and be selected at runtime by `ruleset.id`.

## Notes

- These rules define *how* scoring is performed, not *how data is collected*.
- Data acquisition and normalization are handled outside this directory.
- No investment recommendations are implied by any ruleset.
