# Backtest summary: jt-momentum-india

Top-500 universe, J = 6, K = 6, no skip, long only (winners), holding months 2005-01 to 2026-10 (262 months). After costs unless marked. Newey-West t-statistics in brackets. From the study's `results/` folder.

## Headline

| | Before costs | After costs |
|---|---|---|
| Average return a month | 1.82% (3.28) | 1.75% (3.16) |
| Compound annual return | | 18.2% |
| Worst drawdown | -73.9% | -74.2% |
| CAPM alpha a month, against the IIMA market (risk-free subtracted) | 0.32% (1.36) | 0.25% (1.07) |
| Beta | 1.18 | 1.18 |
| Two-way turnover a month | 0.32 | 0.32 |

## Against benchmarks, after costs

| Benchmark | Months | Strategy mean a month | Benchmark mean a month | Strategy CAGR | Benchmark CAGR | Strategy worst drawdown | Benchmark worst drawdown | Alpha a month (t) |
|---|---|---|---|---|---|---|---|---|
| IIMA Indian market (total return) | 252 | 1.75% | 1.34% | 18.1% | 14.7% | -74.2% | -61.9% | 0.25% (1.07) |
| NIFTY 500 (price plus yield/12), from 2012-03 | 176 | 1.91% | 1.15% | 21.9% | 13.2% | -40.4% | -28.8% | 0.63% (2.06) |
| NIFTY200 Momentum 30 (price plus yield/12), from 2016-07 | 75 | 2.54% | 2.44% | 31.6% | 27.7% | -27.3% | -28.6% | 1.41% (2.05) |

The NIFTY200 Momentum 30 is an investable momentum index; this strategy matched it over 75 months, with a higher beta.

## By period, before costs

| Period | Average return a month (plain t) |
|---|---|
| 2005 to 2009 | 1.99% (1.33) |
| 2010 to 2014 | 1.39% (1.72) |
| 2015 to 2019 | 1.07% (1.18) |
| 2020 to 2026 | 2.56% (3.15) |

## Calendar years, after costs

2005 +75%, 2006 +20%, 2007 +112%, 2008 -71%, 2009 +62%, 2010 +14%, 2011 -25%, 2012 +38%, 2013 -8%, 2014 +81%, 2015 +22%, 2016 -11%, 2017 +85%, 2018 -21%, 2019 -1%, 2020 +43%, 2021 +67%, 2022 -1%, 2023 +75%, 2024 +32%, 2025 -5%, 2026 to October +17%.

## Robustness, after costs

| Check | Average return a month (t) |
|---|---|
| Base | 1.75% (3.16) |
| Brokerage of 0.03% per side | 1.74% (3.14) |
| Trade one day after the ranking close | 1.74% (3.13) |
| -30% charged to every share in the month after its last trade | 1.72% (3.10) |
| -100% charged to every share in the month after its last trade | 1.65% (2.97) |
| Top 200 shares instead of top 500 | 1.53% (2.82) |

## Hedged with NIFTY 50 futures (portfolio C), from 2012-03, 176 months

Average return a month after costs 1.05% (t 2.65), worst drawdown -32.0%, alpha 0.61% (t 1.80). The hedge is the full value of the portfolio, rolled monthly, earning minus the index's total return plus the risk-free rate, with futures costs on a monthly round trip. It needs margin, which the backtest does not charge for.

## Review

An adversarial reviewer checked the study's backtest on 31 October 2026 and found no look-ahead or coding errors; the report is in the study's `results/review/review.md`.
