"""Schemas for scoring rules."""

from typing import Any

from stock_analysis.schemas.base import BaseSchema


class RuleDimension(BaseSchema):
    """Scoring rule dimension configuration schema.

    Attributes:
        id: Unique dimension identifier.
        name: Human-readable dimension name.
        weight: Weight of dimension in overall score calculation.
        enabled: Whether dimension is active in scoring.
    """

    id: str
    name: str
    weight: float
    enabled: bool


class RuleFilter(BaseSchema):
    """Scoring rule filter configuration schema.

    Attributes:
        id: Unique filter identifier.
        name: Human-readable filter name.
        metric: ID of the associated metric.
        filter: Filter type/operator (e.g., 'threshold').
        description: Detailed filter description.
        params: Optional configuration parameters for the filter.
        enabled: Whether filter is active in scoring.
    """

    id: str
    name: str
    metric: str
    filter: str
    description: str
    params: dict[str, Any] | None
    enabled: bool


class RuleMetric(BaseSchema):
    """Scoring rule metric configuration schema.

    Attributes:
        id: Unique metric identifier.
        name: Human-readable metric name.
        dimension: ID of the associated dimension.
        metric: Metric computation identifier.
        description: Detailed metric description.
        params: Optional configuration parameters for computing the metric.
        max_score: Maximum score achievable for this metric.
        weight: Weight of metric in dimension score calculation.
        enabled: Whether metric is active in scoring.
    """

    id: str
    name: str
    dimension: str
    metric: str
    description: str
    params: dict[str, Any] | None
    max_score: float
    weight: float
    enabled: bool


class RuleSet(BaseSchema):
    """Complete scoring rule configuration set schema.

    Represents a complete set of dimensions, metrics, and filters for
    computing stock analysis scores.

    Attributes:
        id: Unique rule set identifier.
        version: Version string of the rule set.
        name: Human-readable rule set name.
        total_score_scale: Maximum score scale (e.g., 100.0).
        dimensions: List of scoring dimensions.
        metrics: List of scoring metrics.
        filters: List of filtering rules.
    """

    id: str
    version: str
    name: str
    total_score_scale: float
    dimensions: list[RuleDimension]
    metrics: list[RuleMetric]
    filters: list[RuleFilter]
