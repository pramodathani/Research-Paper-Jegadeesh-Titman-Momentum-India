"""Tests of universes, deciles and cohort portfolios on tiny tables."""

import numpy as np
import pandas as pd
import pytest

from jegadeesh_titman_momentum_india.momentum.cohort_portfolio import (
    CohortPortfolio,
)
from jegadeesh_titman_momentum_india.momentum.decile_ranker import (
    DecileRanker,
)
from jegadeesh_titman_momentum_india.momentum.futures_portfolios import (
    FuturesPortfolios,
)
from jegadeesh_titman_momentum_india.momentum.grouped_decile_runs import (
    GroupedDecileRuns,
)
from jegadeesh_titman_momentum_india.momentum.long_short_result import (
    LongShortResult,
)
from jegadeesh_titman_momentum_india.momentum.price_matrices import (
    PriceMatrices,
)
from jegadeesh_titman_momentum_india.momentum.study_runner import (
    StudyRunner,
)
from jegadeesh_titman_momentum_india.momentum.universe_builder import (
    UniverseBuilder,
)


class TestDecileRanker:
    """Tests of DecileRanker."""

    def test_twenty_shares_two_per_decile(self) -> None:
        """Twenty shares ranked by return give two in each decile.

        Returns:
            None.
        """
        columns = [f'S{number:02d}' for number in range(20)]
        past = pd.DataFrame(
            [np.arange(20) / 100.0],
            index=pd.PeriodIndex(['2010-01'], freq='M'),
            columns=columns,
        )
        eligible = pd.DataFrame(True, index=past.index, columns=columns)
        deciles = DecileRanker().rank(past, eligible)
        assert deciles['S00'].iloc[0] == 1
        assert deciles['S19'].iloc[0] == 10
        assert (deciles.iloc[0].value_counts() == 2).all()

    def test_ineligible_and_missing_are_left_out(self) -> None:
        """Shares without a return or eligibility get no decile.

        Returns:
            None.
        """
        columns = [f'S{number:02d}' for number in range(12)]
        values = np.arange(12) / 100.0
        values[3] = np.nan
        past = pd.DataFrame(
            [values],
            index=pd.PeriodIndex(['2010-01'], freq='M'),
            columns=columns,
        )
        eligible = pd.DataFrame(True, index=past.index, columns=columns)
        eligible['S05'] = False
        deciles = DecileRanker().rank(past, eligible)
        assert pd.isna(deciles['S03'].iloc[0])
        assert pd.isna(deciles['S05'].iloc[0])
        assert deciles.iloc[0].notna().sum() == 10

    def test_too_few_shares_gives_nothing(self) -> None:
        """Fewer than ten shares cannot form deciles.

        Returns:
            None.
        """
        columns = ['A', 'B', 'C']
        past = pd.DataFrame(
            [[0.1, 0.2, 0.3]],
            index=pd.PeriodIndex(['2010-01'], freq='M'),
            columns=columns,
        )
        eligible = pd.DataFrame(True, index=past.index, columns=columns)
        deciles = DecileRanker().rank(past, eligible)
        assert deciles.isna().all().all()


class TestUniverseBuilder:
    """Tests of UniverseBuilder."""

    def test_top_by_traded_value_with_price_floor(self) -> None:
        """U2 drops cheap shares and keeps the most traded ones.

        Returns:
            None.
        """
        dates = pd.bdate_range('2010-01-04', periods=10)
        rows = []
        specs = {
            'BIG': (100.0, 9000.0),
            'MID': (100.0, 5000.0),
            'LOW': (100.0, 100.0),
            'PENNY': (4.0, 99999.0),
        }
        for symbol, (price, value) in specs.items():
            for date in dates:
                rows.append((date, symbol, price, value, 0.0))
        daily = pd.DataFrame(
            rows,
            columns=['date', 'symbol', 'close', 'traded_value', 'ret'],
        )
        matrices = PriceMatrices(daily)
        builder = UniverseBuilder(matrices, top_count=2, liquidity_days=5)
        u1, u2 = builder.build(pd.DatetimeIndex([dates[-1]]))
        assert u1.iloc[0].sum() == 4
        assert list(u2.columns[u2.iloc[0]]) == ['BIG', 'MID']

    def test_share_not_traded_recently_is_outside_u1(self) -> None:
        """A share with no close in the last 5 days is not in U1.

        Returns:
            None.
        """
        dates = pd.bdate_range('2010-01-04', periods=12)
        rows = [(d, 'LIVE', 50.0, 1000.0, 0.0) for d in dates]
        rows += [(d, 'GONE', 50.0, 1000.0, 0.0) for d in dates[:4]]
        daily = pd.DataFrame(
            rows,
            columns=['date', 'symbol', 'close', 'traded_value', 'ret'],
        )
        matrices = PriceMatrices(daily)
        u1, _ = UniverseBuilder(matrices).build(pd.DatetimeIndex([dates[-1]]))
        assert list(u1.columns[u1.iloc[0]]) == ['LIVE']


class TestCohortPortfolio:
    """Tests of CohortPortfolio and LongShortResult."""

    @staticmethod
    def _setup() -> tuple[pd.DataFrame, pd.DataFrame]:
        """Makes 4 months, 2 shares: W always +10%, L always -5%.

        Returns:
            tuple[pd.DataFrame, pd.DataFrame]: Returns and decile tables.
        """
        months = pd.period_range('2010-01', periods=4, freq='M')
        returns = pd.DataFrame(
            {
                'W': [0.10] * 4,
                'L': [-0.05] * 4,
            },
            index=months,
        )
        deciles = pd.DataFrame(
            {
                'W': [10.0] * 4,
                'L': [1.0] * 4,
            },
            index=months,
        )
        return returns, deciles

    def test_holding_one_month_earns_winner_return_from_month_two(
        self,
    ) -> None:
        """With K = 1 the winners earn 10% from the second month on.

        Returns:
            None.
        """
        returns, deciles = self._setup()
        result = CohortPortfolio(returns, None).run(deciles, 10, 1)
        assert pd.isna(result.gross_returns.iloc[0])
        assert result.gross_returns.iloc[1] == pytest.approx(0.10)

    def test_overlapping_cohorts_wait_for_a_full_set(self) -> None:
        """With K = 3 the first held month is the fourth.

        Returns:
            None.
        """
        returns, deciles = self._setup()
        result = CohortPortfolio(returns, None).run(deciles, 10, 3)
        assert result.gross_returns.iloc[:3].isna().all()
        assert result.gross_returns.iloc[3] == pytest.approx(0.10)

    def test_long_short_is_buy_minus_sell(self) -> None:
        """The zero-cost portfolio earns 10% minus -5%.

        Returns:
            None.
        """
        returns, deciles = self._setup()
        portfolio = CohortPortfolio(returns, None)
        long_short = LongShortResult(
            portfolio.run(deciles, 10, 1),
            portfolio.run(deciles, 1, 1),
        )
        assert long_short.gross().iloc[1] == pytest.approx(0.15)
        assert long_short.net().iloc[1] == pytest.approx(0.15)


class TestGroupedDecileRuns:
    """Tests of the tercile cut in GroupedDecileRuns."""

    def test_terciles_split_nine_shares_three_each(self) -> None:
        """Nine shares give three groups of three, lowest value in group 1.

        Returns:
            None.
        """
        columns = [f'S{number}' for number in range(9)]
        values = pd.DataFrame(
            [np.arange(9, dtype=float)],
            index=pd.PeriodIndex(['2010-01'], freq='M'),
            columns=columns,
        )
        eligible = pd.DataFrame(True, index=values.index, columns=columns)
        groups = GroupedDecileRuns(object()).terciles(values, eligible)
        assert list(groups.iloc[0]) == [1, 1, 1, 2, 2, 2, 3, 3, 3]


class TestFuturesPortfolios:
    """Tests of the hedged long-only portfolio."""

    def test_hedge_subtracts_market_and_adds_risk_free(self) -> None:
        """A 10% winner in a 4% market with 1% risk-free earns 7% gross.

        Returns:
            None.
        """
        dates = pd.bdate_range('2010-01-01', periods=300)
        rows = []
        for symbol in [f'S{number:02d}' for number in range(20)]:
            drift = 0.0001 * int(symbol[1:])
            for date in dates:
                rows.append((date, symbol, 100.0, 1.0e7, drift))
        daily = pd.DataFrame(
            rows,
            columns=['date', 'symbol', 'close', 'traded_value', 'ret'],
        )
        runner = StudyRunner(daily)
        months = runner.months
        market = pd.Series(0.04, index=months)
        risk_free = pd.Series(0.01, index=months)
        portfolios = FuturesPortfolios(runner)
        result = portfolios.hedged_long_only(market, risk_free, 3, 3)
        winners_only = CohortPortfolio(runner.monthly_returns, None).run(
            runner.deciles('U2', 3, False), 10, 3
        )
        expected = winners_only.gross_returns.loc[result.index] - 0.03
        assert result['gross'].to_numpy() == pytest.approx(expected.to_numpy())
        assert (result['net'] < result['gross']).all()
