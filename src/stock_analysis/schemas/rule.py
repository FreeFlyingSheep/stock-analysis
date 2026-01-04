"""Schemas for scoring rules."""

from typing import Any

from stock_analysis.schemas.base import BaseSchema


class RuleDimension(BaseSchema):
    """Scoring rule dimension schema.

    Attributes:
        id: Dimension ID.
        name: Dimension name.
        weight: Weight of the dimension in overall score calculation.
        enabled: Whether the dimension is enabled.
    """

    id: str
    name: str
    weight: float
    enabled: bool


class RuleFilter(BaseSchema):
    """Scoring rule filter schema.

    Attributes:
        id: Filter ID.
        name: Filter name.
        metric: Associated metric.
        filter: Filter type (e.g., "threshold").
        description: Description of the filter.
        params: Parameters for the filter.
        enabled: Whether the filter is enabled.
    """

    id: str
    name: str
    metric: str
    filter: str
    description: str
    params: dict[str, Any] | None
    enabled: bool


class RuleMetric(BaseSchema):
    """Scoring rule metric schema.

    Attributes:
        id: Metric ID.
        name: Metric name.
        dimension: Associated dimension.
        metric: Metric identifier.
        description: Description of the metric.
        params: Parameters for the metric.
        max_score: Maximum score achievable for the metric.
        weight: Weight of the metric in dimension score calculation.
        enabled: Whether the metric is enabled.
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
    """Scoring rule set schema.

    Attributes:
        id: Rule set ID.
        version: Rule set version.
        name: Rule set name.
        total_score_scale: The scale of the total score (e.g., 100.0).
        dimensions: List of rule dimensions.
        metrics: List of rule metrics.
        filters: List of rule filters.
    """

    id: str
    version: str
    name: str
    total_score_scale: float
    dimensions: list[RuleDimension]
    metrics: list[RuleMetric]
    filters: list[RuleFilter]
