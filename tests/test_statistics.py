"""Tests of the summary, calendar month and event-time tables."""

import numpy as np
import pandas as pd
import pytest

from jegadeesh_titman_momentum_india.momentum.calendar_month_table import (
    CalendarMonthTable,
)
from jegadeesh_titman_momentum_india.momentum.event_time_returns import (
    EventTimeReturns,
)
from jegadeesh_titman_momentum_india.momentum.strategy_summary import (
    StrategySummary,
)


def make_series(values: list[float], start: str = '2010-01') -> pd.Series:
    """Builds a monthly series.

    Args:
        values (list[float]): The returns.
        start (str): The first month.

    Returns:
        pd.Series: Returns indexed by month period.
    """
    index = pd.period_range(start, periods=len(values), freq='M')
    return pd.Series(values, index=index)


class TestStrategySummary:
    """Tests of StrategySummary."""

    def test_mean_and_drawdown(self) -> None:
        """A gain then a 50% loss gives the right mean and drawdown.

        Returns:
            None.
        """
        series = make_series([0.10, -0.50, 0.10, 0.10])
        summary = StrategySummary().summarize(series)
        assert summary['mean'] == pytest.approx(-0.05)
        assert summary['periods'] == 4
        assert summary['maximum_drawdown'] == pytest.approx(-0.5)

    def test_alpha_against_market(self) -> None:
        """A series equal to 1% plus half the market has alpha 1%.

        Returns:
            None.
        """
        market = make_series([0.02, -0.01, 0.03, 0.00, -0.02, 0.01])
        series = 0.01 + 0.5 * market
        summary = StrategySummary().summarize(series, market)
        assert summary['alpha'] == pytest.approx(0.01)
        assert summary['beta'] == pytest.approx(0.5)

    def test_long_only_alpha_subtracts_risk_free(self) -> None:
        """With the risk-free rate removed the intercept drops by it.

        Returns:
            None.
        """
        market = make_series([0.02, -0.01, 0.03, 0.00, -0.02, 0.01])
        risk_free = make_series([0.005] * 6)
        series = 0.01 + 0.5 * market + risk_free
        summary = StrategySummary().summarize(
            series, market, risk_free, subtract_risk_free=True
        )
        assert summary['alpha'] == pytest.approx(0.01)

    def test_empty_series(self) -> None:
        """An empty series gives zero periods and NaN statistics.

        Returns:
            None.
        """
        summary = StrategySummary().summarize(
            pd.Series(dtype=float, index=pd.PeriodIndex([], freq='M'))
        )
        assert summary['periods'] == 0
        assert np.isnan(summary['mean'])


class TestCalendarMonthTable:
    """Tests of CalendarMonthTable."""

    def test_january_mean_and_positive_share(self) -> None:
        """Three Januaries with two gains give the right mean and share.

        Returns:
            None.
        """
        values = []
        for year_value in (-0.10, 0.04, 0.03):
            values.extend([year_value] + [0.01] * 11)
        table = CalendarMonthTable().table(make_series(values))
        assert table.loc[1, 'mean'] == pytest.approx((-0.10 + 0.04 + 0.03) / 3)
        assert table.loc[1, 'positive_share'] == pytest.approx(2 / 3)
        assert table.loc[2, 'mean'] == pytest.approx(0.01)

    def test_equal_means_test_detects_a_difference(self) -> None:
        """Very different Januaries give a small p-value.

        Returns:
            None.
        """
        rng = np.random.default_rng(0)
        values = []
        for _ in range(10):
            values.extend([-0.07] + list(rng.normal(0.01, 0.005, 11)))
        statistic, p_value = CalendarMonthTable().equal_means_test(
            make_series(values)
        )
        assert statistic > 10
        assert p_value < 0.001


class TestEventTimeReturns:
    """Tests of EventTimeReturns."""

    def test_constant_spread_accumulates(self) -> None:
        """Winners +2% and losers -1% give 3% a month and 9% after 3.

        Returns:
            None.
        """
        months = pd.period_range('2010-01', periods=12, freq='M')
        names = [f'S{number:02d}' for number in range(20)]
        returns = pd.DataFrame(0.0, index=months, columns=names)
        returns['S19'] = 0.02
        returns['S00'] = -0.01
        deciles = pd.DataFrame(5.0, index=months, columns=names)
        deciles['S19'] = 10.0
        deciles['S00'] = 1.0
        table = EventTimeReturns().winners_minus_losers(
            deciles, returns, horizon=3
        )
        assert table.loc[1, 'monthly'] == pytest.approx(0.03)
        assert table.loc[3, 'cumulative'] == pytest.approx(0.09)
