"""The study's date range, which moves forward as new data arrive."""

import datetime
import sys
from pathlib import Path

import pandas as pd


class StudyPeriod:
    """Decides the first and last holding month of the study.

    The first month is fixed by the plan. The last month is the latest month
    whose last trading day is in the data, so a monthly refresh extends the
    study without editing any date.

    Attributes:
        START: The first holding month, as YYYY-MM.
    """

    START = '2005-01'
    GRID = 'data/derived/grid.parquet'
    FALLBACK_END = '2026-10'

    @staticmethod
    def last_complete_month(last_date: datetime.date) -> pd.Period:
        """Gives the latest month that is complete on a given last data date.

        A month counts as complete only when no weekday remains after the
        date. When the month's last weekday was an exchange holiday, the
        month is treated as unfinished; pass --through-month to the build
        script to include it.

        Args:
            last_date (datetime.date): The last date with prices.

        Returns:
            pd.Period: The month, or the month before when the data stop
                part-way through it.
        """
        month = pd.Period(last_date, freq='M')
        remaining = pd.bdate_range(
            pd.Timestamp(last_date) + pd.Timedelta(days=1),
            month.end_time.normalize(),
        )
        if len(remaining) == 0:
            return month
        return month - 1

    @staticmethod
    def cut(
        daily: pd.DataFrame,
        through_month: str | None = None,
    ) -> pd.DataFrame:
        """Drops days after the last complete month.

        Args:
            daily (pd.DataFrame): Daily returns with a date column.
            through_month (str | None): The last month to keep, as YYYY-MM,
                or None to work it out from the data.

        Returns:
            pd.DataFrame: The rows up to the end of that month.
        """
        dates = pd.to_datetime(daily['date'])
        if through_month is None:
            last = StudyPeriod.last_complete_month(dates.max().date())
        else:
            last = pd.Period(through_month, freq='M')
        return daily[dates <= last.end_time.normalize()]

    @classmethod
    def end(cls, grid_path: str | None = None) -> str:
        """Gives the study's last holding month from the saved grid.

        Args:
            grid_path (str | None): The grid file, or None for the default.

        Returns:
            str: The month as YYYY-MM, or the last published one when the
                grid is not there.
        """
        path = Path(grid_path or cls.GRID)
        if not path.exists():
            print(
                f'warning: {path} not found; using {cls.FALLBACK_END}',
                file=sys.stderr,
            )
            return cls.FALLBACK_END
        months = pd.read_parquet(path, columns=['month'])['month']
        return str(pd.Period(months.max(), freq='M'))
