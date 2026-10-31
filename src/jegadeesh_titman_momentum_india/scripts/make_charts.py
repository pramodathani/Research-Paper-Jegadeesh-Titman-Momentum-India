"""Command-line program that draws the README's charts from results/."""

from pathlib import Path

import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd

from jegadeesh_titman_momentum_india.momentum.study_period import (
    StudyPeriod,
)

BLUE = '#4285F4'
RED = '#EA4335'
YELLOW = '#FBBC05'
GREEN = '#34A853'
GREY = '#5F6368'


class MakeChartsApplication:
    """Draws wealth curves and the Table I heat map."""

    def run(self) -> None:
        """Draws every chart into results/charts.

        Returns:
            None.
        """
        results = Path('results')
        charts = results / 'charts'
        charts.mkdir(parents=True, exist_ok=True)
        grid = pd.read_parquet('data/derived/grid.parquet')
        grid = grid[grid['month'] >= '2005-01-01']
        self._wealth(grid, results, charts / 'wealth_6_6.png')
        self._heat_map(results, charts / 'table1_heat_map.png')

    def _series(
        self,
        grid: pd.DataFrame,
        universe: str,
        leg: str,
        column: str,
    ) -> pd.Series:
        """Picks the 6/6 no-skip series.

        Args:
            grid (pd.DataFrame): The strategy returns.
            universe (str): U1 or U2.
            leg (str): buy, sell or long_short.
            column (str): gross or net.

        Returns:
            pd.Series: Monthly returns indexed by month.
        """
        rows = grid[
            (grid['universe'] == universe)
            & ~grid['skip']
            & (grid['formation_months'] == 6)
            & (grid['holding_months'] == 6)
            & (grid['leg'] == leg)
        ]
        return rows.set_index('month')[column].dropna()

    def _wealth(
        self,
        grid: pd.DataFrame,
        results: Path,
        path: Path,
    ) -> None:
        """Plots growth of one rupee for the main 6/6 portfolios.

        Args:
            grid (pd.DataFrame): The strategy returns.
            results (Path): The results folder.
            path (Path): Where to save the picture.

        Returns:
            None.
        """
        figure, axis = plt.subplots(figsize=(9, 5))
        lines = [
            (
                'U2',
                'buy',
                'net',
                BLUE,
                'Top-500 winners, long only, after costs',
            ),
            (
                'U2',
                'long_short',
                'net',
                GREEN,
                'Top-500 winners minus losers, after costs',
            ),
            ('U2', 'sell', 'gross', RED, 'Top-500 losers, before costs'),
        ]
        for universe, leg, column, colour, label in lines:
            series = self._series(grid, universe, leg, column)
            axis.plot(
                series.index,
                (1 + series).cumprod(),
                color=colour,
                linewidth=1.8,
                label=label,
            )
        market = pd.read_csv(results / 'market_monthly.csv', index_col=0)
        market.index = pd.PeriodIndex(market.index, freq='M').to_timestamp()
        market = market['market_return'].loc['2005-01-01':]
        axis.plot(
            market.index,
            (1 + market).cumprod(),
            color=YELLOW,
            linewidth=1.8,
            label='Indian market (IIMA, all shares, value weighted)',
        )
        axis.set_yscale('log')
        axis.set_ylabel('Growth of one rupee (log scale)')
        axis.set_title(
            f'J = 6, K = 6 momentum portfolios on NSE shares, 2005 to {StudyPeriod.end()[:4]}',
            fontsize=11,
        )
        axis.grid(True, color='#E8EAED')
        axis.legend(frameon=False, fontsize=9)
        for side in ('top', 'right'):
            axis.spines[side].set_visible(False)
        figure.tight_layout()
        figure.savefig(path, dpi=150)
        plt.close(figure)

    def _heat_map(self, results: Path, path: Path) -> None:
        """Plots average monthly winners-minus-losers returns over J and K.

        Args:
            results (Path): The results folder.
            path (Path): Where to save the picture.

        Returns:
            None.
        """
        table = pd.read_csv(results / 'table1_main.csv')
        figure, axes = plt.subplots(1, 2, figsize=(10, 4))
        for axis, universe in zip(axes, ('U1', 'U2')):
            rows = table[
                (table['universe'] == universe)
                & ~table['skip']
                & (table['leg'] == 'long_short')
            ]
            grid = (
                rows.pivot(
                    index='formation_months',
                    columns='holding_months',
                    values='net_mean',
                )
                * 100
            )
            image = axis.imshow(grid.to_numpy(), cmap='Greens', vmin=0)
            axis.set_xticks(range(4), [str(k) for k in grid.columns])
            axis.set_yticks(range(4), [str(j) for j in grid.index])
            axis.set_xlabel('K, months held')
            axis.set_ylabel('J, months ranked')
            name = 'All shares (U1)' if universe == 'U1' else 'Top 500 (U2)'
            axis.set_title(f'{name}: % a month after costs', fontsize=10)
            for row in range(4):
                for column in range(4):
                    value = grid.iloc[row, column]
                    shade = (
                        'white' if value > 0.75 * grid.max().max() else 'black'
                    )
                    axis.text(
                        column,
                        row,
                        f'{grid.iloc[row, column]:.2f}',
                        ha='center',
                        va='center',
                        fontsize=9,
                        color=shade,
                    )
            figure.colorbar(image, ax=axis, shrink=0.8)
        figure.tight_layout()
        figure.savefig(path, dpi=150)
        plt.close(figure)


if __name__ == '__main__':
    MakeChartsApplication().run()
