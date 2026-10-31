"""The paper's Section III: where the relative strength profits come from."""

from typing import Any

import numpy as np
import pandas as pd
import statsmodels.api as statsmodels_api
from data_and_analytics.backtesting.return_statistics import (
    ReturnStatistics,
)


class ProfitSources:
    """Computes the weighted relative strength strategy and its decomposition.

    Attributes:
        monthly_returns: Monthly returns, months by shares.
        universe: Bools, months by shares, True where a share is eligible at
            the end of the month.
        past_returns: Return over the ranking window ending each month.
        horizon: The holding period of the strategy in months.
    """

    def __init__(
        self,
        monthly_returns: pd.DataFrame,
        universe: pd.DataFrame,
        past_returns: pd.DataFrame,
        horizon: int = 6,
    ) -> None:
        """Keeps the tables.

        Args:
            monthly_returns (pd.DataFrame): Monthly returns.
            universe (pd.DataFrame): Eligibility at each month-end.
            past_returns (pd.DataFrame): Ranking-window returns.
            horizon (int): Holding months, 6 in the paper.

        Returns:
            None.
        """
        self.monthly_returns = monthly_returns
        self.universe = universe
        self.past_returns = past_returns
        self.horizon = horizon
        self.statistics = ReturnStatistics()

    def compounded(self, ending: bool) -> pd.DataFrame:
        """Compounds each share's returns over horizon months.

        A share with no return in any month of the window gets NaN; missing
        months inside the window count as zero.

        Args:
            ending (bool): True for the window ending at each row, False for
                the window that starts the month after each row.

        Returns:
            pd.DataFrame: Compounded returns, months by shares.
        """
        logs = np.log1p(self.monthly_returns.astype(float))
        sums = logs.fillna(0.0).rolling(self.horizon).sum()
        counts = logs.notna().astype(float).rolling(self.horizon).sum()
        result = np.expm1(sums).where(counts > 0)
        if ending:
            return result
        return result.shift(-self.horizon)

    def wrss_profits(self, minimum_shares: int = 30) -> pd.Series:
        """Gives the weighted relative strength strategy's profit each month.

        Weights are each eligible share's past return less the eligible
        average, scaled so the positive weights add up to one, so the profit
        is per rupee long. The profit is the weighted holding return.

        Args:
            minimum_shares (int): The fewest eligible shares for a month.

        Returns:
            pd.Series: Profit by formation month, NaN where unknown.
        """
        holding = self.compounded(ending=False).fillna(0.0).to_numpy()
        past = self.past_returns.to_numpy(dtype=float)
        eligible = self.universe.to_numpy(dtype=bool) & ~np.isnan(past)
        known = self.compounded(ending=False).notna().any(axis=1).to_numpy()
        profits = np.full(len(past), np.nan)
        for row in range(len(past)):
            mask = eligible[row]
            if mask.sum() < minimum_shares or not known[row]:
                continue
            centred = past[row, mask] - past[row, mask].mean()
            positive = centred[centred > 0].sum()
            if positive <= 0:
                continue
            profits[row] = float(
                (centred / positive * holding[row, mask]).sum()
            )
        return pd.Series(profits, index=self.past_returns.index)

    def decile_profits(self, deciles: pd.DataFrame) -> pd.Series:
        """Gives the winners-minus-losers holding return of each cohort.

        Args:
            deciles (pd.DataFrame): Deciles chosen at each month-end.

        Returns:
            pd.Series: The cohort's return over the next horizon months.
        """
        holding = self.compounded(ending=False)
        known = holding.notna().any(axis=1)
        filled = holding.fillna(0.0)
        winners = filled.where(deciles == 10).mean(axis=1)
        losers = filled.where(deciles == 1).mean(axis=1)
        has_both = (deciles == 10).any(axis=1) & (deciles == 1).any(axis=1)
        return (winners - losers).where(known & has_both)

    def summarize(self, series: pd.Series) -> dict[str, float]:
        """Scores a profit series with plain and Newey-West t-statistics.

        Args:
            series (pd.Series): Profits by formation month.

        Returns:
            dict[str, float]: months, mean, plain t and Newey-West t with
                horizon lags.
        """
        present = series.dropna()
        mean, plain = self.statistics.mean_and_t(present)
        _, robust = self.statistics.newey_west_mean_and_t(present, self.horizon)
        return {
            'months': len(present),
            'mean': mean,
            't_plain': plain,
            't_newey_west': robust,
        }

    def decomposition(self) -> dict[str, float]:
        """Splits the weighted strategy's profit into the paper's three terms.

        Uses non-overlapping horizon-month periods, averaged over every
        starting month. The profit is the average cross-sectional covariance
        of consecutive period returns (expression 2). The factor term is the
        cross-sectional variance of market-model betas times the serial
        covariance of the equally weighted index (expression 3), the
        idiosyncratic term is the average serial covariance of market-model
        residuals, and the dispersion term is what remains.

        Returns:
            dict[str, float]: total, dispersion, factor, idiosyncratic,
                index_serial_covariance, beta_variance and periods.
        """
        period_returns = self.compounded(ending=True)
        values = period_returns.to_numpy(dtype=float)
        eligible = self.universe.to_numpy(dtype=bool)
        totals = []
        serial = []
        residual_terms = []
        beta_variances = []
        for offset in range(self.horizon):
            rows = list(
                range(offset + self.horizon - 1, len(values), self.horizon)
            )
            if len(rows) < 6:
                continue
            panel = values[rows]
            mask = np.vstack(
                [np.ones(panel.shape[1], dtype=bool)]
                + [eligible[rows[k - 1]] for k in range(1, len(rows))]
            )
            panel = np.where(mask, panel, np.nan)
            index = np.nanmean(panel, axis=1)
            for k in range(1, len(rows)):
                both = ~np.isnan(panel[k]) & ~np.isnan(panel[k - 1])
                if both.sum() < 30:
                    continue
                now = panel[k, both] - panel[k, both].mean()
                before = panel[k - 1, both] - panel[k - 1, both].mean()
                totals.append(float((now * before).mean()))
            valid_index = ~np.isnan(index)
            if valid_index.sum() > 3:
                head = index[1:][valid_index[1:] & valid_index[:-1]]
                tail = index[:-1][valid_index[1:] & valid_index[:-1]]
                serial.append(float(np.cov(head, tail)[0, 1]))
            residuals, betas = self._residuals(panel, index)
            residual_terms.append(residuals)
            beta_variances.append(betas)
        total = float(np.mean(totals))
        index_covariance = float(np.mean(serial))
        beta_variance = float(np.mean(beta_variances))
        factor = beta_variance * index_covariance
        idiosyncratic = float(np.mean(residual_terms))
        return {
            'total': total,
            'dispersion': total - factor - idiosyncratic,
            'factor': factor,
            'idiosyncratic': idiosyncratic,
            'index_serial_covariance': index_covariance,
            'beta_variance': beta_variance,
            'periods': len(totals),
        }

    def _residuals(
        self,
        panel: np.ndarray,
        index: np.ndarray,
    ) -> tuple[float, float]:
        """Estimates the average residual serial covariance and beta variance.

        Args:
            panel (np.ndarray): Period returns, periods by shares.
            index (np.ndarray): The equally weighted index return per period.

        Returns:
            tuple[float, float]: The average over shares of the serial
                covariance of market-model residuals, and the variance of the
                shares' betas.
        """
        covariances = []
        betas = []
        for column in range(panel.shape[1]):
            series = panel[:, column]
            valid = ~np.isnan(series) & ~np.isnan(index)
            if valid.sum() < 10:
                continue
            x = index[valid]
            y = series[valid]
            if x.std() == 0:
                continue
            beta = np.cov(x, y)[0, 1] / x.var(ddof=1)
            alpha = y.mean() - beta * x.mean()
            fitted = np.full(len(series), np.nan)
            fitted[valid] = y - alpha - beta * x
            pairs = ~np.isnan(fitted[1:]) & ~np.isnan(fitted[:-1])
            if pairs.sum() < 5:
                continue
            covariances.append(
                float((fitted[1:][pairs] * fitted[:-1][pairs]).mean())
            )
            betas.append(beta)
        return float(np.mean(covariances)), float(np.var(betas, ddof=1))

    def lead_lag(
        self,
        profits: pd.Series,
        market_monthly: pd.Series,
    ) -> list[dict[str, Any]]:
        """Regresses profits on the squared lagged market return.

        The regression is the paper's r(p,t,6) = a + theta * r(m,t-6)^2 + u,
        with the market return demeaned and measured over the ranking window,
        estimated on the whole sample and on its two halves with Newey-West
        errors with horizon lags.

        Args:
            profits (pd.Series): Profit by formation month.
            market_monthly (pd.Series): The value-weighted market's monthly
                total return by month period.

        Returns:
            list[dict[str, Any]]: One row for the whole sample and each half,
                with theta, its t-statistic and the months used.
        """
        logs = np.log1p(market_monthly.astype(float))
        window = np.expm1(logs.rolling(self.horizon).sum())
        window = window.reindex(profits.index)
        joined = pd.concat(
            [profits.rename('profit'), window.rename('market')], axis=1
        ).dropna()
        joined['squared'] = (joined['market'] - joined['market'].mean()) ** 2
        half = len(joined) // 2
        parts = {
            'whole sample': joined,
            'first half': joined.iloc[:half],
            'second half': joined.iloc[half:],
        }
        rows = []
        for name, part in parts.items():
            explanatory = statsmodels_api.add_constant(
                part['squared'].to_numpy()
            )
            fitted = statsmodels_api.OLS(
                part['profit'].to_numpy(), explanatory
            ).fit(cov_type='HAC', cov_kwds={'maxlags': self.horizon})
            rows.append(
                {
                    'sample': name,
                    'months': len(part),
                    'theta': float(fitted.params[1]),
                    't': float(fitted.tvalues[1]),
                }
            )
        return rows
