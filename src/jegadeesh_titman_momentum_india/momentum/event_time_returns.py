"""Returns of the winners-minus-losers portfolio month by month after formation."""

import numpy as np
import pandas as pd
from data_and_analytics.backtesting.return_statistics import (
    ReturnStatistics,
)


class EventTimeReturns:
    """The paper's Table VII: average return k months after formation."""

    def __init__(self) -> None:
        """Creates the statistics helper.

        Returns:
            None.
        """
        self.statistics = ReturnStatistics()

    def winners_minus_losers(
        self,
        deciles: pd.DataFrame,
        monthly_returns: pd.DataFrame,
        horizon: int = 36,
    ) -> pd.DataFrame:
        """Follows each formation month's winners and losers for horizon months.

        Args:
            deciles (pd.DataFrame): Deciles chosen at the end of each month.
            monthly_returns (pd.DataFrame): Monthly returns with the same
                months and shares.
            horizon (int): How many months to follow.

        Returns:
            pd.DataFrame: One row per month after formation, with columns
                monthly, monthly_t, cumulative and cumulative_t; the
                cumulative t-statistics use Newey-West errors.
        """
        winners = (deciles == 10).to_numpy()
        losers = (deciles == 1).to_numpy()
        values = monthly_returns.to_numpy(dtype=float)
        formed = deciles.notna().any(axis=1).to_numpy()
        count = len(deciles)
        spread = np.full((horizon, count), np.nan)
        for lag in range(1, horizon + 1):
            for start in range(count - lag):
                if not formed[start]:
                    continue
                later = values[start + lag]
                win = later[winners[start]]
                lose = later[losers[start]]
                win = win[~np.isnan(win)]
                lose = lose[~np.isnan(lose)]
                if len(win) > 0 and len(lose) > 0:
                    spread[lag - 1, start] = win.mean() - lose.mean()
        rows = []
        running = np.zeros(count)
        for lag in range(1, horizon + 1):
            series = pd.Series(spread[lag - 1])
            mean, t_value = self.statistics.mean_and_t(series)
            running = running + np.nan_to_num(spread[lag - 1])
            present = np.isfinite(spread[lag - 1])
            cumulative = pd.Series(np.where(present, running, np.nan))
            cum_mean, cum_t = self.statistics.newey_west_mean_and_t(cumulative)
            rows.append(
                {
                    'month_after': lag,
                    'monthly': mean,
                    'monthly_t': t_value,
                    'cumulative': cum_mean,
                    'cumulative_t': cum_t,
                }
            )
        return pd.DataFrame(rows).set_index('month_after')
