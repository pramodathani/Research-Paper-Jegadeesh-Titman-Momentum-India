"""Tests of the profit-source analysis and the joint tests."""

import numpy as np
import pandas as pd
import pytest

from jegadeesh_titman_momentum_india.momentum.joint_tests import JointTests
from jegadeesh_titman_momentum_india.momentum.profit_sources import (
    ProfitSources,
)


def make_tables(
    returns: np.ndarray,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Builds the monthly returns, universe and 6-month past returns.

    Args:
        returns (np.ndarray): Monthly returns, months by shares.

    Returns:
        tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]: The monthly returns,
            an all-True universe and the returns of the six months ending in
            each month.
    """
    months = pd.period_range('2000-01', periods=returns.shape[0], freq='M')
    columns = [f'S{number:03d}' for number in range(returns.shape[1])]
    monthly = pd.DataFrame(returns, index=months, columns=columns)
    universe = pd.DataFrame(True, index=months, columns=columns)
    past = np.expm1(np.log1p(monthly).rolling(6).sum())
    return monthly, universe, past


class TestProfitSources:
    """Tests of ProfitSources."""

    def test_compounded_windows(self) -> None:
        """Backward and forward windows compound the right months.

        Returns:
            None.
        """
        returns = np.full((10, 2), 0.01)
        returns[3, 0] = np.nan
        monthly, universe, past = make_tables(returns)
        sources = ProfitSources(monthly, universe, past)
        ending = sources.compounded(ending=True)
        assert ending.iloc[5, 1] == pytest.approx(1.01**6 - 1)
        assert ending.iloc[5, 0] == pytest.approx(1.01**5 - 1)
        forward = sources.compounded(ending=False)
        assert forward.iloc[0, 1] == pytest.approx(1.01**6 - 1)
        assert pd.isna(forward.iloc[5, 1])

    def test_wrss_with_constant_returns_matches_formula(self) -> None:
        """With constant monthly returns the profit follows from the weights.

        Returns:
            None.
        """
        monthly_rates = np.linspace(-0.01, 0.03, 60)
        returns = np.tile(monthly_rates, (24, 1))
        monthly, universe, past = make_tables(returns)
        sources = ProfitSources(monthly, universe, past)
        profits = sources.wrss_profits()
        six = (1 + monthly_rates) ** 6 - 1
        centred = six - six.mean()
        expected = (centred * six).sum() / centred[centred > 0].sum()
        assert profits.iloc[10] == pytest.approx(expected)
        assert pd.isna(profits.iloc[-1])

    def test_decomposition_finds_dispersion_in_expected_returns(self) -> None:
        """Persistent differences in mean returns show up as dispersion.

        Returns:
            None.
        """
        rng = np.random.default_rng(5)
        rates = rng.normal(0.01, 0.01, 400)
        returns = rates + rng.normal(0.0, 0.05, (240, 400))
        monthly, universe, past = make_tables(returns)
        sources = ProfitSources(monthly, universe, past)
        result = sources.decomposition()
        expected_variance = np.var((1 + rates) ** 6 - 1)
        assert result['dispersion'] == pytest.approx(
            expected_variance, rel=0.35
        )
        assert abs(result['factor']) < 0.2 * expected_variance
        assert abs(result['idiosyncratic']) < 0.2 * expected_variance

    def test_one_extreme_share_dominates_the_decomposition(self) -> None:
        """A share with a huge run-up inflates the beta variance; dropping it fixes that.

        Returns:
            None.
        """
        rng = np.random.default_rng(11)
        returns = rng.normal(0.01, 0.05, (240, 200))
        returns[100:106, 0] = 1.5
        monthly, universe, past = make_tables(returns)
        distorted = ProfitSources(monthly, universe, past).decomposition()
        kept = [column for column in monthly.columns if column != 'S000']
        clean = ProfitSources(
            monthly[kept], universe[kept], past[kept]
        ).decomposition()
        assert distorted['beta_variance'] > 20 * clean['beta_variance']

    def test_first_period_respects_eligibility(self) -> None:
        """A share that is never eligible does not enter the first period.

        Returns:
            None.
        """
        rng = np.random.default_rng(12)
        returns = rng.normal(0.01, 0.05, (240, 100))
        monthly, universe, past = make_tables(returns)
        universe['S000'] = False
        with_flag = ProfitSources(monthly, universe, past).decomposition()
        kept = monthly.columns[1:]
        without = ProfitSources(
            monthly[kept], universe[kept], past[kept]
        ).decomposition()
        assert with_flag['total'] == pytest.approx(without['total'], rel=1e-9)

    def test_lead_lag_recovers_a_known_slope(self) -> None:
        """A profit built from the squared market return gives its slope back.

        Returns:
            None.
        """
        rng = np.random.default_rng(8)
        months = pd.period_range('1990-01', periods=300, freq='M')
        market = pd.Series(rng.normal(0.01, 0.04, 300), index=months)
        monthly = pd.DataFrame(0.0, index=months, columns=['A'])
        sources = ProfitSources(monthly, monthly.astype(bool), monthly)
        window = np.expm1(np.log1p(market).rolling(6).sum())
        squared = (window - window.mean()) ** 2
        profit = 0.02 - 2.0 * squared + rng.normal(0, 0.002, 300)
        rows = sources.lead_lag(profit, market)
        assert rows[0]['theta'] == pytest.approx(-2.0, abs=0.3)
        assert rows[0]['t'] < -3


class TestJointTests:
    """Tests of JointTests."""

    def test_equal_means_rejects_different_means(self) -> None:
        """Rising means are rejected and equal means are not.

        Returns:
            None.
        """
        rng = np.random.default_rng(1)
        equal = pd.DataFrame(rng.normal(0.01, 0.05, (300, 10)))
        rising = equal + np.linspace(0, 0.03, 10)
        _, p_equal = JointTests().equal_means(equal)
        _, p_rising = JointTests().equal_means(rising)
        assert p_equal > 0.01
        assert p_rising < 0.001

    def test_zero_alphas_rejects_nonzero_alpha(self) -> None:
        """Assets with no alpha pass the test and assets with alpha fail.

        Returns:
            None.
        """
        rng = np.random.default_rng(2)
        market = pd.Series(rng.normal(0.01, 0.04, 400))
        noise = rng.normal(0, 0.02, (400, 5))
        clean = pd.DataFrame(1.2 * market.to_numpy()[:, None] + noise)
        shifted = clean + 0.01
        _, p_clean = JointTests().zero_alphas(clean, market)
        _, p_shifted = JointTests().zero_alphas(shifted, market)
        assert p_clean > 0.01
        assert p_shifted < 0.001
