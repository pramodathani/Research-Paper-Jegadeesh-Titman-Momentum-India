"""Average return by calendar month, as in the paper's Tables IV and V."""

import math

import numpy as np
import pandas as pd
import statsmodels.api as statsmodels_api
from data_and_analytics.backtesting.return_statistics import (
    ReturnStatistics,
)


class CalendarMonthTable:
    """Splits a monthly series by calendar month."""

    def __init__(self) -> None:
        """Creates the statistics helper.

        Returns:
            None.
        """
        self.statistics = ReturnStatistics()

    def table(self, returns: pd.Series) -> pd.DataFrame:
        """Gives each calendar month's mean, t-statistic and share positive.

        Args:
            returns (pd.Series): Monthly returns indexed by month period.

        Returns:
            pd.DataFrame: Twelve rows indexed 1 to 12, with columns mean,
                t_statistic, positive_share and count.
        """
        present = returns.dropna()
        rows = {}
        for month in range(1, 13):
            subset = present[present.index.month == month]
            mean, t_value = self.statistics.mean_and_t(subset)
            positive = float((subset > 0).mean()) if len(subset) else math.nan
            rows[month] = {
                'mean': mean,
                't_statistic': t_value,
                'positive_share': positive,
                'count': len(subset),
            }
        return pd.DataFrame(rows).T

    def equal_means_test(
        self,
        returns: pd.Series,
        months: list[int] | None = None,
    ) -> tuple[float, float]:
        """Tests that the mean return is the same in the chosen months.

        Args:
            returns (pd.Series): Monthly returns indexed by month period.
            months (list[int] | None): Calendar months to include, or None
                for all twelve.

        Returns:
            tuple[float, float]: The F-statistic and its p-value, NaN when
                there are too few observations.
        """
        present = returns.dropna()
        if months is not None:
            present = present[present.index.month.isin(months)]
        calendar = present.index.month
        used = sorted(set(calendar))
        if len(used) < 2 or len(present) <= len(used):
            return math.nan, math.nan
        dummies = pd.get_dummies(calendar).astype(float).to_numpy()
        fitted = statsmodels_api.OLS(present.to_numpy(), dummies).fit()
        restriction = np.zeros((len(used) - 1, len(used)))
        for row in range(len(used) - 1):
            restriction[row, row] = 1.0
            restriction[row, row + 1] = -1.0
        test = fitted.f_test(restriction)
        return float(test.fvalue), float(test.pvalue)
