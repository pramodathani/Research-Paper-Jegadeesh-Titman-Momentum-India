"""Deciles within size and beta groups, as in the paper's Table III."""

import numpy as np
import pandas as pd

from jegadeesh_titman_momentum_india.momentum.cohort_portfolio import (
    CohortPortfolio,
)
from jegadeesh_titman_momentum_india.momentum.decile_ranker import (
    DecileRanker,
)
from jegadeesh_titman_momentum_india.momentum.scholes_williams_beta import (
    ScholesWilliamsBeta,
)


class GroupedDecileRuns:
    """Ranks shares inside terciles of size or beta and returns all deciles.

    Attributes:
        runner: The study runner with its tables.
        beta_window: Trading days of daily returns used for each beta.
    """

    def __init__(self, runner: object, beta_window: int = 252) -> None:
        """Keeps the runner.

        Args:
            runner (object): A StudyRunner.
            beta_window (int): Trading days in the beta window.

        Returns:
            None.
        """
        self.runner = runner
        self.beta_window = beta_window
        self.last_deciles = None

    def terciles(
        self,
        values: pd.DataFrame,
        eligible: pd.DataFrame,
    ) -> pd.DataFrame:
        """Cuts the eligible shares at each date into three equal groups.

        Args:
            values (pd.DataFrame): A measure, one row per month.
            eligible (pd.DataFrame): Bools with the same shape.

        Returns:
            pd.DataFrame: Group 1 (lowest values) to 3, NaN if left out.
        """
        measure = values.where(eligible & values.notna())
        ranks = measure.rank(axis=1, method='first')
        counts = measure.notna().sum(axis=1)
        groups = np.ceil(ranks.div(counts, axis=0) * 3.0)
        return groups.clip(lower=1.0, upper=3.0).where(measure.notna())

    def size_groups(self) -> pd.DataFrame:
        """Cuts the all-shares universe into terciles of traded value.

        Returns:
            pd.DataFrame: Group 1 (smallest) to 3 (largest).
        """
        liquidity = self.runner.liquidity
        return self.terciles(liquidity, self.runner.universes['U1'])

    def beta_groups(self) -> pd.DataFrame:
        """Cuts the all-shares universe into terciles of Scholes-Williams beta.

        The market is the equally weighted average of all shares' daily
        returns, and each beta uses the daily returns of the 252 trading days
        up to the formation date.

        Returns:
            pd.DataFrame: Group 1 (lowest beta) to 3 (highest).
        """
        matrices = self.runner.matrices
        market = matrices.returns.mean(axis=1)
        calendar = matrices.returns.index
        estimator = ScholesWilliamsBeta()
        betas = pd.DataFrame(
            np.nan,
            index=self.runner.months,
            columns=matrices.returns.columns,
        )
        for month, date in zip(self.runner.months, self.runner.formation_dates):
            position = calendar.get_loc(date)
            start = position - self.beta_window + 1
            if start < 0:
                continue
            window = matrices.returns.iloc[start : position + 1]
            betas.loc[month] = estimator.betas(
                window, market.iloc[start : position + 1]
            ).to_numpy()
        return self.terciles(betas, self.runner.universes['U1'])

    def decile_returns(
        self,
        group_labels: pd.DataFrame | None,
        group: int | None,
        formation_months: int = 6,
        holding_months: int = 6,
        universe: str = 'U1',
        skip: bool = False,
    ) -> pd.DataFrame:
        """Runs all ten deciles for one group.

        Args:
            group_labels (pd.DataFrame | None): Group numbers, or None for
                the whole all-shares universe.
            group (int | None): The group to run, or None for everyone.
            formation_months (int): J.
            holding_months (int): K.
            universe (str): The universe to rank, U1 or U2.
            skip (bool): Whether to leave out the last trading week.

        Returns:
            pd.DataFrame: Gross monthly returns, one column per decile 1 to
                10, then the winners-minus-losers column named 10-1.
        """
        runner = self.runner
        eligible = runner.universes[universe]
        if group_labels is not None:
            eligible = eligible & (group_labels == group)
        window = runner.past_returns(formation_months, skip)
        deciles = DecileRanker().rank(window, eligible)
        self.last_deciles = deciles
        portfolio = CohortPortfolio(runner.monthly_returns, None)
        columns = {}
        for decile in range(1, 11):
            result = portfolio.run(deciles, decile, holding_months)
            columns[decile] = result.gross_returns
        table = pd.DataFrame(columns)
        table['10-1'] = table[10] - table[1]
        return table
