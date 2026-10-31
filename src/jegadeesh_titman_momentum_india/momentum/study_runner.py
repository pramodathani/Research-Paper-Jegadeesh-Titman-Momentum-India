"""Runs the paper's grid of strategies on the Indian data."""

from pathlib import Path
from typing import ClassVar

import pandas as pd
from data_and_analytics.backtesting.costs.delivery_costs import (
    DeliveryCosts,
)

from jegadeesh_titman_momentum_india.momentum.cohort_portfolio import (
    CohortPortfolio,
)
from jegadeesh_titman_momentum_india.momentum.decile_ranker import (
    DecileRanker,
)
from jegadeesh_titman_momentum_india.momentum.long_short_result import (
    LongShortResult,
)
from jegadeesh_titman_momentum_india.momentum.monthly_returns import (
    MonthlyReturns,
)
from jegadeesh_titman_momentum_india.momentum.price_matrices import (
    PriceMatrices,
)
from jegadeesh_titman_momentum_india.momentum.universe_builder import (
    UniverseBuilder,
)


class StudyRunner:
    """Ranks shares, forms cohorts and backtests every J, K and skip.

    Attributes:
        matrices: The wide price tables.
        monthly_returns: Holding returns by month and share.
        formation_dates: The last trading day of each month.
        universes: The bool tables for each universe name.
        liquidity: Median daily traded value before each formation date.
        impact_costs: Market impact per side for each universe name.
        skip_days: Trading days of the gap in the skip variant.
        brokerage: Brokerage per side as a fraction of value.
    """

    UNIVERSE_IMPACT: ClassVar[dict[str, float]] = {
        'U1': 0.003,
        'U2': 0.001,
    }

    def __init__(
        self,
        daily_returns: pd.DataFrame,
        skip_days: int = 5,
        brokerage: float = 0.0,
        delay_days: int = 0,
    ) -> None:
        """Builds the tables the strategies need.

        Args:
            daily_returns (pd.DataFrame): Long table with date, symbol, close,
                traded_value and ret.
            skip_days (int): Trading days skipped in the skip variant.
            brokerage (float): Brokerage per side, as a fraction.
            delay_days (int): Trading days by which every purchase and sale is
                delayed after the formation close.

        Returns:
            None.
        """
        self.matrices = PriceMatrices(daily_returns)
        self.skip_days = skip_days
        self.brokerage = brokerage
        self.monthly_returns = MonthlyReturns().build(
            self.matrices.returns,
            delay_days,
        )
        self.formation_dates = self.matrices.month_end_dates()
        self.months = pd.PeriodIndex(self.formation_dates, freq='M')
        builder = UniverseBuilder(self.matrices)
        u1, u2 = builder.build(self.formation_dates)
        self.liquidity = builder.liquidity(self.formation_dates)
        self.liquidity.index = self.months
        u1.index = self.months
        u2.index = self.months
        self.universes = {
            'U1': u1,
            'U2': u2,
        }
        self.monthly_returns = self.monthly_returns.reindex(
            index=self.months,
            columns=self.matrices.returns.columns,
        )

    def deciles(
        self,
        universe: str,
        formation_months: int,
        skip: bool,
        eligible: pd.DataFrame | None = None,
    ) -> pd.DataFrame:
        """Ranks shares on their past return and gives each a decile.

        With skip, the ranking window ends skip_days trading days before the
        formation date and starts the same number of days before the date
        formation_months earlier, so that the week before trading is not used.

        Args:
            universe (str): U1 or U2.
            formation_months (int): J, the length of the ranking window.
            skip (bool): Whether to leave out the last trading week.
            eligible (pd.DataFrame | None): Bools to use in place of the
                universe's, or None for the universe's own.

        Returns:
            pd.DataFrame: Deciles 1 to 10, one row per month.
        """
        ends = self.formation_dates[formation_months:]
        starts = self.formation_dates[: len(ends)]
        if skip:
            ends = self.matrices.shifted_dates(ends, self.skip_days)
            starts = self.matrices.shifted_dates(starts, self.skip_days)
        window = self.matrices.window_returns(starts, ends)
        window.index = self.months[formation_months:]
        window = window.reindex(self.months)
        if eligible is None:
            eligible = self.universes[universe]
        return DecileRanker().rank(window, eligible)

    def cost_model(self, universe: str) -> DeliveryCosts:
        """Gives the delivery cost model for a universe.

        Args:
            universe (str): U1 or U2.

        Returns:
            DeliveryCosts: Indian delivery costs with the universe's impact.
        """
        return DeliveryCosts(
            impact_cost=self.UNIVERSE_IMPACT[universe],
            brokerage=self.brokerage,
        )

    def grid(
        self,
        formation_choices: tuple[int, ...] = (3, 6, 9, 12),
        holding_choices: tuple[int, ...] = (3, 6, 9, 12),
        universes: tuple[str, ...] = ('U1', 'U2'),
    ) -> pd.DataFrame:
        """Runs every combination and gathers the monthly return series.

        Args:
            formation_choices (tuple[int, ...]): The values of J.
            holding_choices (tuple[int, ...]): The values of K.
            universes (tuple[str, ...]): The universes to run.

        Returns:
            pd.DataFrame: Long table with columns universe, skip,
                formation_months, holding_months, leg, month, gross, net,
                turnover and holding_count; legs are buy, sell and long_short.
        """
        frames = []
        for universe in universes:
            portfolio = CohortPortfolio(
                self.monthly_returns,
                self.cost_model(universe),
            )
            for skip in (False, True):
                for formation in formation_choices:
                    deciles = self.deciles(universe, formation, skip)
                    for holding in holding_choices:
                        buy = portfolio.run(deciles, 10, holding)
                        sell = portfolio.run(deciles, 1, holding)
                        long_short = LongShortResult(buy, sell)
                        legs = {
                            'buy': (
                                buy.gross_returns,
                                buy.net_returns,
                                buy.turnover(),
                                buy.holding_counts,
                            ),
                            'sell': (
                                sell.gross_returns,
                                sell.net_returns,
                                sell.turnover(),
                                sell.holding_counts,
                            ),
                            'long_short': (
                                long_short.gross(),
                                long_short.net(),
                                long_short.turnover(),
                                buy.holding_counts + sell.holding_counts,
                            ),
                        }
                        for leg, series in legs.items():
                            frame = pd.DataFrame(
                                {
                                    'gross': series[0],
                                    'net': series[1],
                                    'turnover': series[2],
                                    'holding_count': series[3],
                                }
                            )
                            frame['month'] = frame.index.to_timestamp()
                            frame['universe'] = universe
                            frame['skip'] = skip
                            frame['formation_months'] = formation
                            frame['holding_months'] = holding
                            frame['leg'] = leg
                            frames.append(frame.reset_index(drop=True))
        return pd.concat(frames, ignore_index=True)

    def save_grid(self, path: Path, **kwargs: object) -> pd.DataFrame:
        """Runs the grid and saves it.

        Args:
            path (Path): Where to write the parquet file.
            **kwargs (object): Passed to grid.

        Returns:
            pd.DataFrame: The grid.
        """
        result = self.grid(**kwargs)
        path.parent.mkdir(parents=True, exist_ok=True)
        result.to_parquet(path)
        return result
