"""Three-day returns around quarterly results, as in the paper's Table IX."""

import json
from pathlib import Path

import numpy as np
import pandas as pd


class AnnouncementReturns:
    """Finds each results announcement's trading day and its 3-day return.

    Day 0 is the announcement day if the filing reached NSE before the
    15:30 close, otherwise the next trading day. The return covers days -2
    to 0, as in the paper (p. 87).

    Attributes:
        close_time: The time after which a filing counts for the next day.
    """

    def __init__(self, close_time: str = '15:30') -> None:
        """Sets the market close.

        Args:
            close_time (str): The close as HH:MM.

        Returns:
            None.
        """
        self.close_time = pd.Timedelta(f'{close_time}:00')

    def read_filings(self, folder: Path) -> pd.DataFrame:
        """Reads the saved filings and keeps the first per share and quarter.

        Args:
            folder (Path): The folder with results_YYYYQn.json files.

        Returns:
            pd.DataFrame: Columns symbol, broadcast and quarter_end.
        """
        rows = []
        for path in sorted(folder.glob('results_*.json')):
            for row in json.loads(path.read_text()):
                rows.append(
                    (
                        row.get('symbol'),
                        row.get('broadCastDate') or row.get('filingDate'),
                        row.get('toDate'),
                    )
                )
        table = pd.DataFrame(
            rows, columns=['symbol', 'broadcast', 'quarter_end']
        )
        table['broadcast'] = pd.to_datetime(
            table['broadcast'], format='mixed', dayfirst=True, errors='coerce'
        )
        table['quarter_end'] = pd.to_datetime(
            table['quarter_end'], format='%d-%b-%Y', errors='coerce'
        )
        table = table.dropna()
        table = table.sort_values('broadcast')
        return table.drop_duplicates(['symbol', 'quarter_end'], keep='first')

    def returns(
        self,
        filings: pd.DataFrame,
        daily_returns: pd.DataFrame,
    ) -> pd.DataFrame:
        """Gives each filing's day 0 and its 3-day return.

        Args:
            filings (pd.DataFrame): Columns symbol and broadcast.
            daily_returns (pd.DataFrame): Wide daily returns, one row per
                trading day, one column per share.

        Returns:
            pd.DataFrame: Columns symbol, day_zero, month and ret3, for filings
                of shares in the table with at least two of the three days.
        """
        calendar = daily_returns.index
        columns = {name: i for i, name in enumerate(daily_returns.columns)}
        values = daily_returns.to_numpy(dtype=float)
        table = filings[filings['symbol'].isin(columns)].copy()
        broadcast = table['broadcast']
        after_close = (broadcast - broadcast.dt.normalize()) >= self.close_time
        day = broadcast.dt.normalize()
        positions = calendar.searchsorted(day, side='left')
        positions = np.where(
            after_close
            & (positions < len(calendar))
            & (calendar[np.minimum(positions, len(calendar) - 1)] == day),
            positions + 1,
            positions,
        )
        valid = (positions >= 2) & (positions < len(calendar))
        table = table[valid].copy()
        positions = positions[valid]
        if table.empty:
            return pd.DataFrame(columns=['symbol', 'day_zero', 'month', 'ret3'])
        column_index = table['symbol'].map(columns).to_numpy()
        window = np.stack(
            [values[positions - lag, column_index] for lag in (2, 1, 0)],
            axis=1,
        )
        present = ~np.isnan(window)
        growth = np.prod(np.where(present, 1.0 + window, 1.0), axis=1)
        table['day_zero'] = calendar[positions]
        table['month'] = table['day_zero'].dt.to_period('M')
        table['ret3'] = np.where(present.sum(axis=1) >= 2, growth - 1.0, np.nan)
        return table.dropna(subset=['ret3'])[
            ['symbol', 'day_zero', 'month', 'ret3']
        ]

    def monthly_matrix(
        self,
        announcements: pd.DataFrame,
        months: pd.PeriodIndex,
        columns: pd.Index,
    ) -> pd.DataFrame:
        """Puts announcement returns in a months by shares table.

        Args:
            announcements (pd.DataFrame): Output of returns.
            months (pd.PeriodIndex): The months wanted.
            columns (pd.Index): The shares wanted.

        Returns:
            pd.DataFrame: Average 3-day return of each share's announcements
                in each month, NaN where it made none.
        """
        table = announcements.pivot_table(
            index='month', columns='symbol', values='ret3', aggfunc='mean'
        )
        return table.reindex(index=months, columns=columns)
