"""Scores a monthly return series the way every result table does."""

import math
from typing import Any

import pandas as pd
from data_and_analytics.backtesting.performance_report import (
    PerformanceReport,
)
from data_and_analytics.backtesting.return_statistics import (
    ReturnStatistics,
)


class StrategySummary:
    """Mean, t-statistics, drawdown and market-model alpha of a series."""

    def __init__(self) -> None:
        """Creates the statistics helper.

        Returns:
            None.
        """
        self.statistics = ReturnStatistics()

    def summarize(
        self,
        returns: pd.Series,
        market_excess: pd.Series | None = None,
        risk_free: pd.Series | None = None,
        subtract_risk_free: bool = False,
    ) -> dict[str, Any]:
        """Scores a series.

        Alpha is the intercept from regressing the series, less the risk-free
        rate if subtract_risk_free is set, on the market's excess return.

        Args:
            returns (pd.Series): Monthly returns indexed by month period.
            market_excess (pd.Series | None): The market's return less the
                risk-free rate, or None to skip the regression.
            risk_free (pd.Series | None): The monthly risk-free rate.
            subtract_risk_free (bool): True for a long-only portfolio, False
                for a zero-cost one.

        Returns:
            dict[str, Any]: periods, mean, t_statistic, newey_west_t,
                compound_annual, maximum_drawdown, worst_period,
                positive_periods and, with a market, alpha, alpha_t, beta and
                beta_t; all NaN-filled for an empty series.
        """
        present = returns.dropna()
        if present.empty:
            return {
                'periods': 0,
                'mean': math.nan,
                't_statistic': math.nan,
                'newey_west_t': math.nan,
                'compound_annual': math.nan,
                'maximum_drawdown': math.nan,
                'worst_period': math.nan,
                'positive_periods': math.nan,
            }
        report = PerformanceReport(present)
        full = report.summary()
        keep = (
            'periods',
            'mean',
            't_statistic',
            'newey_west_t',
            'compound_annual',
            'maximum_drawdown',
            'worst_period',
            'positive_periods',
        )
        summary = {name: full[name] for name in keep}
        if market_excess is not None:
            target = present
            if subtract_risk_free and risk_free is not None:
                target = present - risk_free.reindex(present.index)
            model = self.statistics.market_model(target, market_excess)
            summary.update(
                {
                    'alpha': model['alpha'],
                    'alpha_t': model['alpha_t'],
                    'beta': model['beta'],
                    'beta_t': model['beta_t'],
                }
            )
        return summary
