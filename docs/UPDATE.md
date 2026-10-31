# Updating the study with new data

The study moves forward on its own: no date is typed into the code. The last
holding month is the last complete month in the price data (a month is
complete when no weekday remains after the last price date; if the month's
last weekday was an exchange holiday, pass `--through-month`).

## One command

From the repository root, with `RESEARCH_ANALYST_TIMESCALEDB_URL` set:

    .venv/bin/python -m jegadeesh_titman_momentum_india.scripts.update_study

Options: `--skip-download` (use the files already in `data/nse`),
`--through-month YYYY-MM`, `--from-step "<step name>"` (resume after a
failure). The run writes `results/update_report.md` with each step's status
and time. A full run takes roughly an hour; the 64-specification
precompute (`make live tables`) is the slowest step.

## What each step does

| Step | Writes |
|---|---|
| download (7 sources) | `data/nse/...` raw NSE files, resumable |
| load (5 sources) | TimescaleDB raw tables (upserts, safe to repeat) |
| build returns | `data/derived/daily_returns.parquet`, cut at the last complete month; DB `daily_returns` |
| run grid | `data/derived/grid.parquet`; DB monthly returns, universes, strategy returns |
| make results, table nine, further results | `results/*.csv`, `results/further/*.csv` |
| make live tables | `results/live/live_tables.json`, `equal_market.csv` (the 64 specifications the page looks up) |
| make summary tables, charts | `results/summary_tables.md`, `results/charts/` |
| build snapshot | `site/data/snapshot.json`, which the page reads |
| build brief page | the hand-off brief |
| store shared results | `results.strategy_returns` in TimescaleDB |
| check page text | prints quoted figures that no longer match |

## What updates itself on the page

Dates, month counts, the number of trading days and symbols, the headline
6/6 numbers in the abstract and section 4.1, the sample choices (halves are
recomputed), and every table and figure.

## What needs a human

1. Read the `check_page_text` output. Sentences in sections 3 to 4.8 quote
   numbers typed by hand; edit `site/index.html` where it says STALE and
   re-read the listed sections.
2. Re-read `results/summary.md` for the January and Section III sentences.
3. Run `pytest`, commit in phases, then ask for `github_push`,
   `publish_site` and, if the brief changed, `install_into_trading_agent`.
4. Note that the Indian factor library (IIMA) lags: market-based alphas stop
   at its last month, and the page says so.
