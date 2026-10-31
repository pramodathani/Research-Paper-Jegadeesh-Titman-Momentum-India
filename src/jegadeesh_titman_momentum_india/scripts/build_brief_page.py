"""Command-line program that builds the hand-off brief's HTML page."""

from pathlib import Path

import pandas as pd

from jegadeesh_titman_momentum_india.momentum.brief_page import BriefPage


class BuildBriefPageApplication:
    """Writes strategy_brief.html from strategy_brief.md and the results."""

    FOLDER = Path('handoff/jt-momentum-india/skills/jt-momentum-india')

    def run(self) -> None:
        """Builds the page.

        Returns:
            None.
        """
        references = self.FOLDER / 'references'
        text = (references / 'strategy_brief.md').read_text()
        grid = pd.read_parquet('data/derived/grid.parquet')
        rows = grid[
            (grid['universe'] == 'U2')
            & ~grid['skip']
            & (grid['formation_months'] == 6)
            & (grid['holding_months'] == 6)
            & (grid['leg'] == 'buy')
            & (grid['month'] >= '2005-01-01')
        ]
        strategy = rows.set_index(rows['month'].dt.to_period('M'))['net']
        market = pd.read_csv('results/market_monthly.csv', index_col=0)
        market.index = pd.PeriodIndex(market.index, freq='M')
        page = BriefPage().render(text, strategy, market['market_return'])
        (references / 'strategy_brief.html').write_text(page)
        print(f'{len(page)} characters written')


if __name__ == '__main__':
    BuildBriefPageApplication().run()
