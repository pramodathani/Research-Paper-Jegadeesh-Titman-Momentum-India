"""Tests of betas, the delisting stress and the F&O universe."""

import numpy as np
import pandas as pd
import pytest

from jegadeesh_titman_momentum_india.momentum.delisting_stress import (
    DelistingStress,
)
from jegadeesh_titman_momentum_india.momentum.fno_universe import FnoUniverse
from jegadeesh_titman_momentum_india.momentum.scholes_williams_beta import (
    ScholesWilliamsBeta,
)


class TestScholesWilliamsBeta:
    """Tests of ScholesWilliamsBeta."""

    def test_recovers_known_beta(self) -> None:
        """A share equal to 1.5 times an independent market has beta 1.5.

        Returns:
            None.
        """
        rng = np.random.default_rng(1)
        market = pd.Series(rng.normal(0, 0.01, 300))
        stocks = pd.DataFrame(
            {
                'A': 1.5 * market,
                'B': 0.5 * market,
            }
        )
        betas = ScholesWilliamsBeta().betas(stocks, market)
        assert betas['A'] == pytest.approx(1.5, abs=0.15)
        assert betas['B'] == pytest.approx(0.5, abs=0.15)

    def test_too_little_data_gives_nan(self) -> None:
        """A share with few days has no beta.

        Returns:
            None.
        """
        rng = np.random.default_rng(2)
        market = pd.Series(rng.normal(0, 0.01, 300))
        sparse = 1.0 * market
        sparse.iloc[:250] = np.nan
        betas = ScholesWilliamsBeta().betas(pd.DataFrame({'A': sparse}), market)
        assert np.isnan(betas['A'])


class TestDelistingStress:
    """Tests of DelistingStress."""

    def test_terminal_return_after_last_return(self) -> None:
        """A share that stops gets the stress return the next month.

        Returns:
            None.
        """
        months = pd.period_range('2010-01', periods=6, freq='M')
        returns = pd.DataFrame(
            {
                'LIVE': [0.01] * 6,
                'GONE': [0.01, 0.02, 0.03, np.nan, np.nan, np.nan],
            },
            index=months,
        )
        stressed = DelistingStress().apply(returns, -1.0)
        assert stressed['GONE'].iloc[3] == -1.0
        assert np.isnan(stressed['GONE'].iloc[4])
        assert stressed['LIVE'].equals(returns['LIVE'])

    def test_share_still_trading_at_the_end_is_left_alone(self) -> None:
        """A share trading in the final months gets no stress return.

        Returns:
            None.
        """
        months = pd.period_range('2010-01', periods=4, freq='M')
        returns = pd.DataFrame({'A': [0.01, 0.02, 0.03, 0.04]}, index=months)
        stressed = DelistingStress().apply(returns, -1.0)
        assert stressed.equals(returns)


class TestFnoUniverse:
    """Tests of FnoUniverse."""

    def test_marks_recent_futures(self) -> None:
        """A share with a future in the last 5 days is marked.

        Returns:
            None.
        """
        futures = pd.DataFrame(
            {
                'date': ['2010-01-27', '2010-01-05'],
                'symbol': ['AAA', 'BBB'],
            }
        )
        table = FnoUniverse().build(
            futures,
            pd.DatetimeIndex(['2010-01-29']),
            pd.Index(['AAA', 'BBB', 'CCC']),
        )
        assert list(table.columns[table.iloc[0]]) == ['AAA']
