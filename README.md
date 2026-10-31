# Jegadeesh and Titman (1993) Momentum, Recreated for Indian Shares

This study recreates the relative-strength strategies of Jegadeesh and Titman (1993), "Returns to Buying Winners and Selling Losers", for shares listed on the National Stock Exchange of India. Shares are ranked on their past J-month returns, winners are bought and losers sold, and portfolios are held for K months in overlapping cohorts. Both the paper's long-short portfolios and long-only portfolios that can be traded in India are tested, before and after Indian trading costs.

**In one line:** work in progress; results will appear here after the Results stage.

## Status

The study is at the Intake stage: the paper is filed and the repository laid out. The sections below will be filled in as the study goes on.

## Database

Cleaned prices, returns and results will be stored in TimescaleDB under the schema `jegadeesh_and_titman_research_analyst`, and monthly strategy returns in the shared table `results.strategy_returns`. The tables will be listed here with their sources once they exist. The code in this repository can rebuild all of them from the original sources.

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
