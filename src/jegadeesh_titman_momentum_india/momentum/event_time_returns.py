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

    def spread_matrix(
        self,
        deciles: pd.DataFrame,
        monthly_returns: pd.DataFrame,
        horizon: int,
    ) -> np.ndarray:
        """Follows each month's winners and losers and gives the spread.

        Args:
            deciles (pd.DataFrame): Deciles chosen at the end of each month.
            monthly_returns (pd.DataFrame): Monthly returns with the same
                months and shares.
            horizon (int): How many months to follow.

        Returns:
            np.ndarray: Winners minus losers, one row per month after
                formation and one column per formation month, NaN if unknown.
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
        return spread

    def betas(
        self,
        deciles: pd.DataFrame,
        monthly_returns: pd.DataFrame,
        market_excess: pd.Series,
        horizon: int = 36,
    ) -> pd.DataFrame:
        """Estimates the spread's market beta in each month after formation.

        For each lag, the spread of the cohorts formed in every month is
        regressed on the market's excess return in the month it is earned.

        Args:
            deciles (pd.DataFrame): Deciles chosen at the end of each month.
            monthly_returns (pd.DataFrame): Monthly returns.
            market_excess (pd.Series): The market's excess return by month.
            horizon (int): How many months to follow.

        Returns:
            pd.DataFrame: One row per month after formation with the beta and
                its t-statistic.
        """
        spread = self.spread_matrix(deciles, monthly_returns, horizon)
        market = market_excess.reindex(deciles.index).to_numpy(dtype=float)
        rows = []
        for lag in range(1, horizon + 1):
            y = spread[lag - 1]
            x = np.full(len(y), np.nan)
            x[: len(y) - lag] = market[lag:]
            valid = ~np.isnan(y) & ~np.isnan(x)
            if valid.sum() < 12 or x[valid].std() == 0:
                rows.append({'month_after': lag, 'beta': np.nan, 't': np.nan})
                continue
            design = np.column_stack([np.ones(valid.sum()), x[valid]])
            coefficients, *_ = np.linalg.lstsq(design, y[valid], rcond=None)
            residuals = y[valid] - design @ coefficients
            variance = residuals @ residuals / (valid.sum() - 2)
            error = np.sqrt(variance * np.linalg.inv(design.T @ design)[1, 1])
            rows.append(
                {
                    'month_after': lag,
                    'beta': float(coefficients[1]),
                    't': float(coefficients[1] / error),
                }
            )
        return pd.DataFrame(rows).set_index('month_after')

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
        spread = self.spread_matrix(deciles, monthly_returns, horizon)
        count = spread.shape[1]
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
