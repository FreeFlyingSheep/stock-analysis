"""Scoring rules adaptors."""

import re
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np
import yaml
from pydantic import ValidationError

from stock_analysis.schemas.rule import RuleSet

if TYPE_CHECKING:
    import os
    from collections.abc import Callable

    from stock_analysis.schemas.rule import RuleDimension, RuleFilter, RuleMetric


class RuleError(Exception):
    """Error raised during rule loading or evaluation operations."""


def _load_rules(rule_file_path: Path) -> RuleSet:
    """Load and parse scoring rules from a YAML configuration file.

    Args:
        rule_file_path: Path to the YAML rule configuration file.

    Returns:
        Parsed RuleSet object with dimensions, metrics, and filters.

    Raises:
        RuleError: If file is invalid, missing, or rule set is malformed.
    """
    raw: dict[str, Any] | None = yaml.safe_load(rule_file_path.read_text())
    if raw is None or "ruleset" not in raw:
        msg: str = f"Invalid rule file: {rule_file_path}"
        raise RuleError(msg)

    try:
        ruleset: RuleSet = RuleSet.model_validate(raw["ruleset"])
    except ValidationError as e:
        msg = f"Error validating rule file {rule_file_path}: {e}"
        raise RuleError(msg) from e

    for m in ruleset.metrics:
        if not any(d.id == m.dimension for d in ruleset.dimensions):
            msg = (
                f"Metric '{m.id}' references undefined dimension "
                f"'{m.dimension}' in rule file {rule_file_path}"
            )
            raise RuleError(msg)

    for f in ruleset.filters:
        if not any(m.id == f.metric for m in ruleset.metrics):
            msg = (
                f"Filter '{f.id}' references undefined metric "
                f"'{f.metric}' in rule file {rule_file_path}"
            )
            raise RuleError(msg)

    return ruleset


def _get_dict_value(data: Any, key: str) -> Any:  # noqa: ANN401
    """Get a value from a dictionary by key.

    Args:
        data: Dictionary to retrieve value from.
        key: Key to look up in the dictionary.

    Returns:
        The value associated with the key.

    Raises:
        RuleError: If data is not a dict or key is not found.
    """
    if not isinstance(data, dict):
        msg: str = f"Expected dict when accessing '{key}'"
        raise RuleError(msg)
    value: Any | None = data.get(key)
    if value is None:
        msg = f"Key '{key}' not found in data"
        raise RuleError(msg)
    return value


def _get_array_value(data: Any, key: str) -> Any:  # noqa: ANN401
    """Get a value from a list by index specified in key notation.

    Key format: 'list_name[index]' where index can be negative.

    Args:
        data: List to retrieve value from.
        key: Key with list access notation.

    Returns:
        The value at the specified index.

    Raises:
        RuleError: If format invalid, data not a list, or index out of range.
    """
    pos: int = key.find("[")
    if pos == -1:
        msg: str = f"Invalid list access syntax in '{key}'"
        raise RuleError(msg)
    value: Any = _get_dict_value(data, key[:pos])
    if not isinstance(value, list):
        msg = f"Expected list when accessing '{key}'"
        raise RuleError(msg)
    index: int = int(key[pos + 1 : -1])
    if index >= len(value) or index < -len(value):
        msg = f"Index '{index}' out of range when accessing '{key}'"
        raise RuleError(msg)
    return value[index]


def _get_dict_value_by_index(data: Any, key: str, index: str) -> Any:  # noqa: ANN401
    """Get a value from a dictionary of lists by index value.

    Finds a list element where the 'index' field matches the provided index.

    Args:
        data: Dictionary containing list values.
        key: Dictionary key (with '[]' suffix indicating list).
        index: Index string value to match in list elements.

    Returns:
        The matching list element.

    Raises:
        RuleError: If key invalid, not a list, or index not found.
    """
    if not isinstance(data, dict):
        msg: str = f"Expected dict when accessing '{key}'"
        raise RuleError(msg)
    value: Any = data.get(key[:-2])
    if not isinstance(value, list):
        msg = f"Expected list at '{key[:-2]}'"
        raise RuleError(msg)
    for v in value:
        if value.index is None:
            msg = f"No index provided for list at '{key[:-2]}'"
            raise RuleError(msg)
        i: Any = v["index"]
        if not isinstance(i, str):
            msg = f"Expected string index for list at '{key[:-2]}'"
            raise RuleError(msg)
        if i == index:
            return v
    msg = f"Index '{index}' not found in list at '{key[:-2]}'"
    raise RuleError(msg)


def _get_value(data: dict[str, Any], source: str, index: str | None = None) -> Any:  # noqa: ANN401
    """Get a nested value from a dictionary using dot notation.

    Supports nested access via dots and array/list indexing.
    Example: 'main_indicators.records[0].year[].F067N' with optional index.

    Args:
        data: Root dictionary to retrieve value from.
        source: Dot-notated path to the value.
        index: Optional index for accessing array elements.

    Returns:
        The value at the specified nested path.

    Raises:
        RuleError: If path is invalid or key not found.
    """
    keys: list[str] = source.split(".")
    value: Any = data
    for key in keys:
        if index is not None and key.endswith("[]"):
            value = _get_dict_value_by_index(value, key, index)
        elif key.endswith("]"):
            value = _get_array_value(value, key)
        else:
            value = _get_dict_value(value, key)
    return value


class RuleAdaptor:
    """Adaptor for applying and evaluating stock scoring rules.

    Loads scoring rules from YAML configuration and provides methods
    to compute metrics and scores for stocks.

    Attributes:
        _rule_file_path: Path to the YAML rule file.
        _data: Stock data being evaluated.
        _ruleset: Loaded RuleSet configuration.
        _dimensions: Mapping of dimension IDs to RuleDimension objects.
        _metrics: Mapping of metric IDs to RuleMetric objects.
        _filters: Mapping of filter IDs to RuleFilter objects.
        _scores: Cache of computed metric scores.
        _current_year: Current year for time-relative calculations.
    """

    _rule_file_path: Path
    _data: dict[str, Any]
    _ruleset: RuleSet
    _dimensions: dict[str, RuleDimension]
    _metrics: dict[str, RuleMetric]
    _filters: dict[str, RuleFilter]
    _scores: dict[str, float]
    _current_year: int

    def __init__(self, rule_file_path: str | os.PathLike[str]) -> None:
        """Initialize the RuleAdaptor with a rule configuration file.

        Args:
            rule_file_path: Path to the YAML file with rule definitions.
        """
        self._rule_file_path = Path(rule_file_path)
        self._data = {}
        self._ruleset: RuleSet = _load_rules(self._rule_file_path)
        self._dimensions = {d.id: d for d in self._ruleset.dimensions}
        self._metrics = {m.id: m for m in self._ruleset.metrics}
        self._filters = {f.id: f for f in self._ruleset.filters}
        self._scores = {}
        self._current_year = datetime.now().astimezone().year

    def _roe_weighted_average(self) -> float:
        """Calculate weighted average ROE (Return on Equity).

        Computes median ROE across 5 years of data.

        Returns:
            Weighted average ROE value.
        """
        results: list[float] = []
        for i in range(5):
            roe: float = _get_value(
                self._data, f"main_indicators.records[0].year[{i}].F067N"
            )
            results.append(roe)
        return float(np.median(results))

    def _gross_margin(self) -> float:
        """Calculate gross margin for a stock.

        Computes median gross margin across 5 years of historical data.

        Returns:
            Gross margin percentage value.
        """
        results: list[float] = []
        for i in range(5):
            gross_margin: float = _get_value(
                self._data, f"main_indicators.records[0].year[{i}].F078N"
            )
            results.append(gross_margin)
        return float(np.median(results))

    def _net_profit_growth(self) -> float:
        """Calculate net profit growth rate.

        Computes median net profit growth across 5 years of data.

        Returns:
            Net profit growth percentage value.
        """
        results: list[float] = []
        for i in range(5):
            net_profit_growth: float = _get_value(
                self._data, f"main_indicators.records[0].year[{i}].F053N"
            )
            results.append(net_profit_growth)
        return float(np.median(results))

    def _ocf_to_net_income_ratio(self) -> float:
        """Calculate the operating cash flow to net income ratio.

        Computes median ratio across 5 years of historical data.

        Returns:
            OCF to net income ratio value.
        """
        results: list[float] = []
        for i in range(5):
            year: str = str(self._current_year - i - 2)
            cash_flow: float = _get_value(
                self._data,
                f"cash_flow_statement.records[0].year[].{year}",
                index="经营活动产生的现金流量净额",
            )
            income: float = _get_value(
                self._data,
                f"income_statement.records[0].year[].{year}",
                index="归属母公司净利润",
            )
            ocf: float = cash_flow / income if income != 0.0 else 0.0
            results.append(ocf)
        return float(np.median(results))

    def _debt_to_asset(self) -> float:
        """Calculate debt to asset ratio for a stock.

        Returns:
            The debt to asset ratio.
        """
        results: list[float] = []
        for i in range(5):
            debt_ratio: float = _get_value(
                self._data, f"main_indicators.records[0].year[{i}].F041N"
            )
            results.append(debt_ratio)
        return float(np.median(results))

    def _pe_ttm_percentile(self) -> float:
        """Calculate PE TTM percentile for a stock.

        Returns:
            The PE TTM percentile.
        """
        results: list[float] = []
        price: float = _get_value(self._data, "history.records[-1].Close")
        for i in range(5):
            year: str = str(self._current_year - i - 2)
            income: float = _get_value(
                self._data,
                f"income_statement.records[0].year[].{year}",
                index="归属母公司净利润",
            )
            shares: float = _get_value(
                self._data,
                f"balance_sheets.records[0].year[].{year}",
                index="实收资本（或股本）",  # noqa: RUF001
            )
            eps: float = income / shares if shares != 0.0 else 0.0
            pe: float = price / eps if eps != 0.0 else 0.0
            results.append(pe)
        return float(np.median(results))

    def _dividend_yield_ttm(self) -> float:
        """Calculate dividend yield TTM for a stock.

        Returns:
            The dividend yield TTM.
        """
        price: float = _get_value(self._data, "history.records[-1].Close")
        dps: float = 0.0
        for i in range(5):
            date: datetime = datetime.strptime(
                _get_value(self._data, f"company_his_dividend.records[{i}].F020D"),
                "%Y-%m-%d",
            ).astimezone()
            if date.year >= self._current_year - 5:
                match: re.Match | None = re.search(
                    r"10派(.*)元",
                    _get_value(self._data, f"company_his_dividend.records[{i}].F007V"),
                )
                if match is None:
                    continue
                dps += float(match.group(1)) / 10.0
        return dps / price

    def _manual_score_industry(self) -> float:
        """Retrieve manual industry score for a stock.

        Returns:
            The manual industry score.
        """
        return 0.0

    def _manual_score_moat(self) -> float:
        """Retrieve manual moat score for a stock.

        Returns:
            The manual moat score.
        """
        return 0.0

    def _manual_score_pricing(self) -> float:
        """Retrieve manual pricing score for a stock.

        Returns:
            The manual pricing score.
        """
        return 0.0

    def _manual_score_sentiment(self) -> float:
        """Retrieve manual sentiment score for a stock.

        Returns:
            The manual sentiment score.
        """
        return 0.0

    def _manual_score_understanding(self) -> float:
        """Retrieve manual understanding score for a stock.

        Returns:
            The manual understanding score.
        """
        return 0.0

    def _manual_score_psychology(self) -> float:
        """Retrieve manual psychology score for a stock.

        Returns:
            The manual psychology score.
        """
        return 0.0

    def _score_metric(self, metric: RuleMetric) -> float:
        """Score a stock for a specific metric.

        Args:
            metric: The metric to score.

        Returns:
            The score for the metric.
        """
        if metric.id in self._scores:
            return self._scores[metric.id]

        metrics: dict[str, Callable[[], float]] = {
            "roe_weighted_average": self._roe_weighted_average,
            "gross_margin": self._gross_margin,
            "net_profit_growth": self._net_profit_growth,
            "ocf_to_net_income_ratio": self._ocf_to_net_income_ratio,
            "debt_to_asset": self._debt_to_asset,
            "pe_ttm_percentile": self._pe_ttm_percentile,
            "dividend_yield_ttm": self._dividend_yield_ttm,
            "manual_score_industry": self._manual_score_industry,
            "manual_score_moat": self._manual_score_moat,
            "manual_score_pricing": self._manual_score_pricing,
            "manual_score_sentiment": self._manual_score_sentiment,
            "manual_score_understanding": self._manual_score_understanding,
            "manual_score_psychology": self._manual_score_psychology,
        }
        if metric.metric in metrics:
            score: float = metrics[metric.metric]()
            self._scores[metric.id] = score
            return score

        msg: str = f"Unknown metric ID '{metric.id}' for scoring."
        raise RuleError(msg)

    def _threshold(self, metric_filter: RuleFilter) -> float:
        """Retrieve threshold value for a filter.

        Args:
            metric_filter: The filter to apply.

        Returns:
            The threshold value.
        """
        if metric_filter.params is None or "threshold" not in metric_filter.params:
            msg: str = f"Filter '{metric_filter.id}' missing 'threshold' parameter."
            raise RuleError(msg)

        return metric_filter.params["threshold"]

    def _metric_value(self, metric_filter: RuleFilter) -> float:
        """Retrieve metric value for a filter.

        Args:
            metric_filter: The filter to apply.

        Returns:
            The metric value.
        """
        metric_value: float | None = self._scores.get(metric_filter.metric)
        if metric_value is None:
            msg: str = (
                f"Metric value for '{metric_filter.metric}' not found "
                f"when applying filter '{metric_filter.id}'."
            )
            raise RuleError(msg)

        return metric_value

    def _less_than_threshold(self, metric_filter: RuleFilter) -> bool:
        """Apply a 'less than threshold' filter to a stock.

        Args:
            metric_filter: The filter to apply.

        Returns:
            True if the stock passes the filter, False otherwise.
        """
        return self._metric_value(metric_filter) < self._threshold(metric_filter)

    def _greater_than_threshold(self, metric_filter: RuleFilter) -> bool:
        """Apply a 'greater than threshold' filter to a stock.

        Args:
            metric_filter: The filter to apply.

        Returns:
            True if the stock passes the filter, False otherwise.
        """
        return self._metric_value(metric_filter) > self._threshold(metric_filter)

    def _filter_metric(self, metric_filter: RuleFilter) -> bool:
        """Apply a filter to a stock for a specific metric.

        Args:
            metric_filter: The filter to apply.

        Returns:
            True if the stock passes the filter, False otherwise.
        """
        filters: dict[str, Callable[[RuleFilter], bool]] = {
            "less_than_threshold": self._less_than_threshold,
            "greater_than_threshold": self._greater_than_threshold,
        }
        if metric_filter.filter in filters:
            return filters[metric_filter.filter](metric_filter)

        msg: str = f"Unknown filter type '{metric_filter.filter}' for filtering."
        raise RuleError(msg)

    def set_data(self, data: dict[str, Any]) -> None:
        """Set the data for scoring.

        Args:
            data: The data dictionary for scoring.
        """
        self._data = data
        self._scores = {}

    def score(self) -> float:
        """Score a stock based on the loaded rules.

        Returns:
            The total score for the stock.
        """
        if not self._data:
            msg: str = "No data loaded for scoring."
            raise RuleError(msg)

        total_score: float = 0.0
        max_score: float = 0.0
        for m in self._metrics.values():
            if m.enabled and self._dimensions[m.dimension].enabled:
                score: float = self._score_metric(m)
                total_score += score
                max_score += m.max_score
        return (
            total_score / max_score * self._ruleset.total_score_scale
            if max_score > 0
            else 0.0
        )

    def metrics(self) -> dict[str, float]:
        """Get computed scores for all metrics.

        Returns:
            A dictionary of metric IDs to their computed scores.
        """
        if not self._scores:
            self.score()
        return self._scores

    def apply_filter(self) -> bool:
        """Apply filters to a stock.

        Returns:
            True if the stock passes all filters, False otherwise.
        """
        if not self._scores:
            self.score()

        for f in self._filters.values():
            if f.enabled and not self._filter_metric(f):
                return False

        return True
