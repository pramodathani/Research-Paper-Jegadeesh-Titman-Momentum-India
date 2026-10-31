"""Runs one decile as a portfolio of overlapping cohorts."""

import pandas as pd
from data_and_analytics.backtesting.backtest import Backtest
from data_and_analytics.backtesting.backtest_result import BacktestResult
from data_and_analytics.backtesting.costs.cost_model import CostModel
from data_and_analytics.backtesting.overlapping_cohorts import (
    OverlappingCohorts,
)


class CohortPortfolio:
    """Holds a decile for K months in K overlapping cohorts.

    Attributes:
        monthly_returns: Holding returns, one row per month, one column per
            share.
        cost_model: The trading cost model, or None for no costs.
    """

    def __init__(
        self,
        monthly_returns: pd.DataFrame,
        cost_model: CostModel | None,
    ) -> None:
        """Keeps the returns and costs.

        Args:
            monthly_returns (pd.DataFrame): Monthly returns.
            cost_model (CostModel | None): The costs.

        Returns:
            None.
        """
        self.monthly_returns = monthly_returns
        self.cost_model = cost_model

    def run(
        self,
        deciles: pd.DataFrame,
        decile_number: int,
        holding_months: int,
    ) -> BacktestResult:
        """Backtests one decile.

        Args:
            deciles (pd.DataFrame): Decile numbers chosen at the end of each
                month, with the same months and shares as the returns.
            decile_number (int): The decile to hold, 1 to 10.
            holding_months (int): K, how many months each cohort is held.

        Returns:
            BacktestResult: The legs' returns before and after costs.
        """
        members = deciles == decile_number
        formed = deciles.notna().any(axis=1)
        cohorts = OverlappingCohorts(members, holding_months, formed)
        weights = cohorts.weights(self.monthly_returns)
        return Backtest(
            self.monthly_returns,
            weights,
            self.cost_model,
        ).run()
