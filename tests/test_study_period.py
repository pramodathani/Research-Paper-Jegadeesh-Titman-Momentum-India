"""Tests of the study's moving end date."""

import datetime

import pandas as pd

from jegadeesh_titman_momentum_india.momentum.study_period import StudyPeriod


class TestStudyPeriod:
    """Tests of StudyPeriod."""

    def test_month_end_data_make_a_complete_month(self) -> None:
        """Data to the last trading day complete the month.

        Returns:
            None.
        """
        last = datetime.date(2026, 10, 30)
        assert StudyPeriod.last_complete_month(last) == pd.Period('2026-10')

    def test_mid_month_data_leave_the_month_out(self) -> None:
        """Data to the middle of a month make the month before the last.

        Returns:
            None.
        """
        last = datetime.date(2026, 11, 12)
        assert StudyPeriod.last_complete_month(last) == pd.Period('2026-10')

    def test_a_missing_last_weekday_leaves_the_month_out(self) -> None:
        """Data to Thursday 29 April leave April unfinished.

        Returns:
            None.
        """
        last = datetime.date(2026, 4, 29)
        assert StudyPeriod.last_complete_month(last) == pd.Period('2026-03')
        assert len(
            StudyPeriod.cut(
                pd.DataFrame({'date': pd.to_datetime([last]), 'symbol': 'A'}),
                '2026-04',
            )
        ) == 1

    def test_cut_drops_the_partial_month(self) -> None:
        """Rows after the last complete month are removed.

        Returns:
            None.
        """
        daily = pd.DataFrame(
            {
                'date': pd.to_datetime(
                    ['2026-10-29', '2026-10-30', '2026-11-02', '2026-11-12']
                ),
                'symbol': 'A',
            }
        )
        kept = StudyPeriod.cut(daily)
        assert len(kept) == 2
        assert len(StudyPeriod.cut(daily, '2026-11')) == 4
