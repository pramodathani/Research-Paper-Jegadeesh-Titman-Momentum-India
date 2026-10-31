"""Tradeable long-short versions that short through index or stock futures."""

import pandas as pd
from data_and_analytics.backtesting.costs.delivery_costs import (
    DeliveryCosts,
)
from data_and_analytics.backtesting.costs.futures_costs import FuturesCosts

from jegadeesh_titman_momentum_india.momentum.cohort_portfolio import (
    CohortPortfolio,
)
from jegadeesh_titman_momentum_india.momentum.long_short_result import (
    LongShortResult,
)
from jegadeesh_titman_momentum_india.momentum.study_runner import StudyRunner


class FuturesPortfolios:
    """Portfolio C (winners hedged with index futures) and D (F&O long-short).

    Attributes:
        runner: The study runner with its tables.
        impact_cost: Market impact per side for the top-500 and F&O shares.
    """

    def __init__(self, runner: StudyRunner, impact_cost: float = 0.001) -> None:
        """Keeps the runner.

        Args:
            runner (StudyRunner): The study runner.
            impact_cost (float): Impact per side.

        Returns:
            None.
        """
        self.runner = runner
        self.impact_cost = impact_cost

    def fno_long_short(
        self,
        futures_members: pd.DataFrame,
        formation_months: int,
        holding_months: int,
        skip: bool = False,
    ) -> LongShortResult:
        """Buys winners in cash and sells losers through stock futures.

        Only shares that had a stock future near the formation date take part
        in the ranking. The short leg earns the losers' stock return and pays
        futures costs; the basis and the cost of carry are not modelled.

        Args:
            futures_members (pd.DataFrame): Bools, months by shares, True where
                a stock future existed.
            formation_months (int): J.
            holding_months (int): K.
            skip (bool): Whether to skip the last trading week.

        Returns:
            LongShortResult: The two legs.
        """
        eligible = futures_members & self.runner.universes['U1']
        deciles = self.runner.deciles('U1', formation_months, skip, eligible)
        returns = self.runner.monthly_returns
        buy = CohortPortfolio(
            returns,
            DeliveryCosts(impact_cost=self.impact_cost),
        ).run(deciles, 10, holding_months)
        sell = CohortPortfolio(
            returns,
            FuturesCosts(impact_cost=self.impact_cost),
        ).run(deciles, 1, holding_months)
        return LongShortResult(buy, sell)

    def hedged_long_only(
        self,
        market_total_return: pd.Series,
        risk_free: pd.Series,
        formation_months: int,
        holding_months: int,
        skip: bool = False,
    ) -> pd.DataFrame:
        """Holds the top-500 winners and sells index futures against them.

        The hedge is the full value of the portfolio, rolled every month. It
        earns minus the index's total return plus the risk-free rate, as a
        fully financed short future does, and pays futures costs on a monthly
        round trip.

        Args:
            market_total_return (pd.Series): The index's monthly total return.
            risk_free (pd.Series): The monthly risk-free rate.
            formation_months (int): J.
            holding_months (int): K.
            skip (bool): Whether to skip the last trading week.

        Returns:
            pd.DataFrame: Columns gross and net, indexed by month period, for
                the months where the index return is known.
        """
        deciles = self.runner.deciles('U2', formation_months, skip)
        long_leg = CohortPortfolio(
            self.runner.monthly_returns,
            DeliveryCosts(impact_cost=self.impact_cost),
        ).run(deciles, 10, holding_months)
        futures = FuturesCosts(impact_cost=self.impact_cost)
        roll_cost = futures.buy_rate() + futures.sell_rate()
        hedge = -market_total_return.reindex(
            long_leg.gross_returns.index
        ) + risk_free.reindex(long_leg.gross_returns.index)
        gross = long_leg.gross_returns + hedge
        net = long_leg.net_returns + hedge - roll_cost
        return pd.DataFrame({'gross': gross, 'net': net}).dropna()
