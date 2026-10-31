"""Joint tests across the ten decile portfolios, as in the paper's Table III."""

import numpy as np
import pandas as pd
from scipy import stats


class JointTests:
    """F-tests that the ten portfolios earn the same, or all have zero alpha."""

    def equal_means(self, returns: pd.DataFrame) -> tuple[float, float]:
        """Tests that every portfolio has the same mean return.

        Uses Hotelling's T-squared on the differences between neighbouring
        portfolios, which has an F distribution under normal returns.

        Args:
            returns (pd.DataFrame): Monthly returns, one column per portfolio.

        Returns:
            tuple[float, float]: The F-statistic and its p-value.
        """
        data = returns.dropna().to_numpy()
        count, size = data.shape
        differences = data[:, 1:] - data[:, :-1]
        dimension = size - 1
        mean = differences.mean(axis=0)
        covariance = np.cov(differences, rowvar=False)
        t_squared = count * mean @ np.linalg.solve(covariance, mean)
        scale = (count - dimension) / (dimension * (count - 1))
        f_value = float(scale * t_squared)
        p_value = float(stats.f.sf(f_value, dimension, count - dimension))
        return f_value, p_value

    def zero_alphas(
        self,
        excess_returns: pd.DataFrame,
        market_excess: pd.Series,
    ) -> tuple[float, float]:
        """Tests that every portfolio's market-model alpha is zero.

        This is the Gibbons, Ross and Shanken test.

        Args:
            excess_returns (pd.DataFrame): Portfolio returns less the
                risk-free rate, one column per portfolio.
            market_excess (pd.Series): The market's excess return.

        Returns:
            tuple[float, float]: The F-statistic and its p-value.
        """
        joined = pd.concat(
            [excess_returns, market_excess.rename('_market')], axis=1
        ).dropna()
        factor = joined['_market'].to_numpy()
        assets = joined.drop(columns='_market').to_numpy()
        count, size = assets.shape
        design = np.column_stack([np.ones(count), factor])
        coefficients, *_ = np.linalg.lstsq(design, assets, rcond=None)
        residuals = assets - design @ coefficients
        covariance = residuals.T @ residuals / count
        alphas = coefficients[0]
        sharpe_squared = factor.mean() ** 2 / factor.var()
        statistic = (
            (count - size - 1)
            / size
            * (alphas @ np.linalg.solve(covariance, alphas))
            / (1.0 + sharpe_squared)
        )
        p_value = float(stats.f.sf(statistic, size, count - size - 1))
        return float(statistic), p_value
