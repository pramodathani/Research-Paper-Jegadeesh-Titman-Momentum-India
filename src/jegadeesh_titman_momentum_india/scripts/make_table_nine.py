"""Command-line program that builds the paper's Table IX on Indian data."""

from pathlib import Path

import pandas as pd

from jegadeesh_titman_momentum_india.momentum.announcement_returns import (
    AnnouncementReturns,
)
from jegadeesh_titman_momentum_india.momentum.event_time_returns import (
    EventTimeReturns,
)
from jegadeesh_titman_momentum_india.momentum.study_runner import StudyRunner
from jegadeesh_titman_momentum_india.momentum.symbol_changes import (
    SymbolChanges,
)


class MakeTableNineApplication:
    """Average 3-day results-day returns of winners minus losers by month."""

    FIRST_FORMATION = pd.Period('2007-07', freq='M')

    def run(self) -> None:
        """Builds results/table9_announcements_U1.csv and _U2.csv.

        Returns:
            None.
        """
        daily = pd.read_parquet('data/derived/daily_returns.parquet')
        daily['date'] = pd.to_datetime(daily['date'])
        runner = StudyRunner(daily)
        maker = AnnouncementReturns()
        filings = maker.read_filings(Path('data/nse/results_dates'))
        changes = SymbolChanges.from_nse_file(
            'data/nse/symbol_changes/symbolchange.csv'
        )
        filings['date'] = filings['broadcast']
        filings = changes.apply(filings, 'date')
        announcements = maker.returns(filings, runner.matrices.returns)
        announcements.to_parquet('data/derived/announcement_returns.parquet')
        matrix = maker.monthly_matrix(
            announcements, runner.months, runner.monthly_returns.columns
        )
        counts = announcements.groupby('month').size()
        counts.to_csv('results/table9_announcements_per_month.csv')
        print(f'{len(announcements)} announcements')
        for universe in ('U1', 'U2'):
            deciles = runner.deciles(universe, 6, False)
            deciles.loc[deciles.index < self.FIRST_FORMATION] = float('nan')
            table = EventTimeReturns().winners_minus_losers(deciles, matrix, 36)
            table = table[['monthly', 'monthly_t']]
            table.to_csv(f'results/table9_announcements_{universe}.csv')


if __name__ == '__main__':
    MakeTableNineApplication().run()
