# Jegadeesh and Titman (1993) Momentum, Recreated for Indian Shares

This study recreates the relative-strength strategies of Jegadeesh and Titman (1993), "Returns to Buying Winners and Selling Losers", for shares listed on the National Stock Exchange of India. Shares are ranked on their past J-month returns, winners are bought and losers sold, and portfolios are held for K months in overlapping cohorts. Both the paper's long-short portfolios and long-only portfolios that can be traded in India are tested, before and after Indian trading costs.

**In one line:** work in progress; results will appear here after the Results stage.

## Status

The study is at the Build and test stage: the data are downloaded and stored, the package is written and tested, and the first grid of 32 strategies has run. Results, costs, the companion site and the hand-off package follow.

## Database

All data and results are stored in TimescaleDB under the schema `jegadeesh_and_titman_research_analyst`, so a monthly refresh only has to append new days. Every load is an upsert that is safe to run twice, and every table can be rebuilt from the raw files with the scripts in `src/jegadeesh_titman_momentum_india/scripts/`.

| Table | Holds | Source |
|---|---|---|
| `daily_prices_raw` | NSE daily prices for series EQ, BE and BZ, unadjusted | NSE bhavcopy files, 1996 to 2026 |
| `ubi_daily_prices` | UBI daily candles adjusted for splits and bonuses, used for cross-checks | UBI through `export_prices`, 2019 to 2026 |
| `corporate_actions` | Splits, bonuses, dividends and other actions | NSE corporate actions API, 2000 to 2026 |
| `index_daily` | Index closes, P/E, P/B and dividend yield | NSE `ind_close_all` files, 2012 to 2026 |
| `fno_stock_futures_daily` | Nearest-expiry stock futures prices | NSE derivatives bhavcopy, 2005 to 2026 |
| `iima_factors_monthly` | IIMA SMB, HML, WML, market premium and risk-free rate in percent | IIMA data library, 1993 to 2025 |
| `daily_returns` | Adjusted daily total returns | Built from the tables above |
| `return_flags` | Days whose return was inferred from a split ratio or zeroed | Built |
| `monthly_returns` | Calendar-month returns by share | Built |
| `universe_membership` | Shares in the all-shares (U1) and top-500 (U2) universes each month | Built |
| `strategy_returns_detail` | Monthly gross and net returns of every J, K, skip and universe | Built |

Monthly strategy returns also go to the shared table `results.strategy_returns` when the Results stage is done.

## Repository layout

```
paper/        the paper's citation, summary and related work (PDF git-ignored)
plan/         the plan for adapting the study to India
src/jegadeesh_titman_momentum_india/
  data/       downloaders and parsers, one class per source
  momentum/   returns, rankings, portfolios and statistics
  site/       the interactive companion page
  scripts/    one command-line program per step
tests/        unit tests on small made-up data, no network
results/      tables, charts and summary
data/         raw and intermediate data, git-ignored
```

## Citation

See `CITATION.cff`. Please also cite the original paper:

Jegadeesh, N., and Titman, S. (1993). Returns to Buying Winners and Selling Losers: Implications for Stock Market Efficiency. *The Journal of Finance*, 48(1), 65-91. https://doi.org/10.1111/j.1540-6261.1993.tb04702.x
