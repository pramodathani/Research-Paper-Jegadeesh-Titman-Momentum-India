"""Which shares had stock futures at each formation date."""

import numpy as np
import pandas as pd


class FnoUniverse:
    """Builds a bool table of shares with a stock future."""

    def build(
        self,
        futures: pd.DataFrame,
        formation_dates: pd.DatetimeIndex,
        columns: pd.Index,
        recent_days: int = 5,
    ) -> pd.DataFrame:
        """Marks shares that had a futures row near each formation date.

        Args:
            futures (pd.DataFrame): Columns date and symbol, one row per share
                per day with a stock future.
            formation_dates (pd.DatetimeIndex): The dates to mark.
            columns (pd.Index): The shares to include.
            recent_days (int): Calendar-day look-back; a future seen in this
                many calendar days counts.

        Returns:
            pd.DataFrame: Bools, one row per formation date.
        """
        frame = futures[['date', 'symbol']].copy()
        frame['date'] = pd.to_datetime(frame['date'])
        formation = np.asarray(formation_dates, dtype='datetime64[ns]')
        earliest = formation - np.timedelta64(recent_days, 'D')
        flags = np.zeros((len(formation), len(columns)), dtype=bool)
        column_position = {name: i for i, name in enumerate(columns)}
        for symbol, group in frame.groupby('symbol'):
            if symbol not in column_position:
                continue
            dates = np.sort(group['date'].to_numpy(dtype='datetime64[ns]'))
            last_index = np.searchsorted(dates, formation, side='right') - 1
            found = last_index >= 0
            latest = dates[np.where(found, last_index, 0)]
            hit = found & (latest > earliest)
            flags[:, column_position[symbol]] = hit
        return pd.DataFrame(flags, index=formation_dates, columns=columns)
