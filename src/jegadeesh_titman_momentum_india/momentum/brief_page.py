"""Turns the strategy brief's Markdown into one self-contained web page."""

import math

import markdown
import pandas as pd

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
body {{ font-family: 'Times New Roman', Tinos, 'Liberation Serif', serif; font-size: 17px; line-height: 1.55; color: #202124; margin: 0; }}
main {{ max-width: 780px; margin: 0 auto; padding: 36px 20px 70px; }}
h1 {{ font-size: 28px; line-height: 1.25; }}
h2 {{ font-size: 21px; margin-top: 34px; border-bottom: 1px solid #dadce0; padding-bottom: 4px; }}
a {{ color: #1a73e8; }}
table {{ border-collapse: collapse; width: 100%; font-size: 15px; border-top: 2px solid #202124; border-bottom: 2px solid #202124; margin: 14px 0; display: block; overflow-x: auto; }}
th {{ border-bottom: 1px solid #202124; text-align: left; padding: 5px 8px; font-weight: normal; font-style: italic; }}
td {{ padding: 4px 8px; vertical-align: top; }}
code {{ font-family: 'JetBrains Mono', monospace; font-size: 14px; background: #f1f3f4; padding: 1px 4px; }}
.bar {{ height: 4px; display: flex; width: 160px; margin: 6px 0 22px; }}
.bar span {{ flex: 1; }}
figure {{ margin: 22px 0; }}
figcaption {{ font-size: 15px; color: #5f6368; }}
</style>
</head>
<body>
<main>
<div class="bar"><span style="background:#4285f4"></span><span style="background:#ea4335"></span><span style="background:#fbbc05"></span><span style="background:#34a853"></span></div>
{body}
</main>
</body>
</html>
"""


class BriefPage:
    """Builds the brief's web page from its Markdown and the monthly returns."""

    WIDTH = 720
    HEIGHT = 300
    LEFT = 52
    BOTTOM = 28

    def render(
        self,
        text: str,
        strategy: pd.Series,
        market: pd.Series,
    ) -> str:
        """Builds the page.

        Args:
            text (str): The brief's Markdown.
            strategy (pd.Series): The strategy's monthly returns by month.
            market (pd.Series): The market's monthly returns by month.

        Returns:
            str: The complete HTML page.
        """
        title = text.splitlines()[0].lstrip('# ').strip()
        body = markdown.markdown(text, extensions=['tables'])
        marker = '<h2>Backtest results</h2>'
        chart = self.chart(strategy, market)
        body = body.replace(marker, marker + chart, 1)
        return PAGE.format(title=title, body=body)

    def chart(self, strategy: pd.Series, market: pd.Series) -> str:
        """Draws growth of one rupee, on a log scale, as an inline SVG.

        Args:
            strategy (pd.Series): The strategy's monthly returns by month.
            market (pd.Series): The market's monthly returns by month.

        Returns:
            str: A figure element with the SVG and a caption.
        """
        common = strategy.dropna().index.intersection(market.dropna().index)
        growth_strategy = (1.0 + strategy.loc[common]).cumprod()
        growth_market = (1.0 + market.loc[common]).cumprod()
        low = math.log10(min(growth_strategy.min(), growth_market.min(), 1.0))
        high = math.log10(max(growth_strategy.max(), growth_market.max()))
        inner_width = self.WIDTH - self.LEFT - 10
        inner_height = self.HEIGHT - self.BOTTOM - 10

        def points(series: pd.Series) -> str:
            """Turns a growth series into SVG polyline points.

            Args:
                series (pd.Series): Growth of one rupee by month.

            Returns:
                str: The points attribute.
            """
            pairs = []
            count = len(series)
            for position, value in enumerate(series):
                x = self.LEFT + inner_width * position / (count - 1)
                level = (math.log10(value) - low) / (high - low)
                y = 10 + inner_height * (1.0 - level)
                pairs.append(f'{x:.1f},{y:.1f}')
            return ' '.join(pairs)

        grid = []
        for decade in range(math.ceil(low), math.floor(high) + 1):
            level = (decade - low) / (high - low)
            y = 10 + inner_height * (1.0 - level)
            grid.append(
                f'<line x1="{self.LEFT}" x2="{self.WIDTH - 10}" y1="{y:.1f}" '
                f'y2="{y:.1f}" stroke="#e8eaed"/>'
                f'<text x="{self.LEFT - 6}" y="{y + 4:.1f}" font-size="12" '
                f'text-anchor="end" fill="#5f6368">{10**decade:g}</text>'
            )
        years = sorted({month.year for month in common})
        labels = []
        for year in years[::4]:
            position = next(
                i for i, month in enumerate(common) if month.year == year
            )
            x = self.LEFT + inner_width * position / (len(common) - 1)
            labels.append(
                f'<text x="{x:.1f}" y="{self.HEIGHT - 8}" font-size="12" '
                f'text-anchor="middle" fill="#5f6368">{year}</text>'
            )
        first = common[0]
        last = common[-1]
        svg = (
            f'<svg viewBox="0 0 {self.WIDTH} {self.HEIGHT}" width="100%" '
            f'role="img" aria-label="Growth of one rupee">'
            + ''.join(grid)
            + ''.join(labels)
            + f'<polyline fill="none" stroke="#5f6368" stroke-width="1.6" '
            f'points="{points(growth_market)}"/>'
            f'<polyline fill="none" stroke="#4285f4" stroke-width="2.2" '
            f'points="{points(growth_strategy)}"/>'
            f'<text x="{self.LEFT + 8}" y="24" font-size="13" fill="#4285f4">'
            f'Strategy after costs</text>'
            f'<text x="{self.LEFT + 8}" y="42" font-size="13" fill="#5f6368">'
            f'Indian market (IIMA)</text></svg>'
        )
        caption = (
            f'Growth of one rupee, log scale, {first} to {last}: the strategy '
            f'after Indian costs and the Indian market.'
        )
        return f'<figure>{svg}<figcaption>{caption}</figcaption></figure>'
