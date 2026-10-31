"""Splits shares into ten groups by past return."""

import numpy as np
import pandas as pd


class DecileRanker:
    """Ranks eligible shares on past return and cuts them into deciles."""

    def rank(
        self,
        past_returns: pd.DataFrame,
        eligible: pd.DataFrame,
    ) -> pd.DataFrame:
        """Gives every eligible share a decile from 1 (losers) to 10.

        A share needs both a past return and eligibility. Ties are split by
        column order so that each decile holds as equal a count as possible.

        Args:
            past_returns (pd.DataFrame): Past J-month returns, one row per
                formation date.
            eligible (pd.DataFrame): Bools with the same shape.

        Returns:
            pd.DataFrame: Deciles 1 to 10 as floats, NaN for shares left out.
        """
        values = past_returns.to_numpy(dtype=float)
        allowed = eligible.to_numpy(dtype=bool) & ~np.isnan(values)
        deciles = np.full(values.shape, np.nan)
        for row in range(values.shape[0]):
            positions = np.flatnonzero(allowed[row])
            count = len(positions)
            if count < 10:
                continue
            order = np.argsort(values[row, positions], kind='stable')
            ranks = np.empty(count)
            ranks[order] = np.arange(count)
            deciles[row, positions] = np.floor(ranks * 10 / count) + 1
        return pd.DataFrame(
            deciles,
            index=past_returns.index,
            columns=past_returns.columns,
        )
