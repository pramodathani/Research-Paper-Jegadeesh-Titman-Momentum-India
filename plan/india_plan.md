# Adapting Jegadeesh and Titman (1993) to Indian markets

Status: draft for Pramod's approval, 2026-10-31. Page numbers refer to the journal's printed pages; see `paper/summary.md`.

## 1. What we will build, in one paragraph

Each month we rank NSE-listed company shares on their return over the past J months (J = 3, 6, 9, 12), split them into ten equal-weighted deciles, buy the top decile (winners) and, in the long-short version, sell the bottom decile (losers). Each month's selection is held for K months (K = 3, 6, 9, 12) as overlapping cohorts, with a no-skip and a skip-a-week version, exactly as on p. 68. We run it on a paper-faithful "all shares" universe and on an investable "top 500" universe, as a long-short research portfolio and as a long-only portfolio that can be traded with delivery orders. Everything is reported before and after Indian costs, with Newey-West t-statistics, and compared with the IIMA momentum factor and NSE's momentum indices.

## 2. What changes for India, and why

| Item | Paper (US) | India version | Why |
|---|---|---|---|
| Universe | All NYSE and AMEX stocks with J months of returns (p. 69) | **U1 "All NSE shares"**: company shares in NSE's EQ, BE and BZ series with J months of returns and a close in the last five trading days of the formation month; ETFs, fund units, rights entitlements, partly paid shares, bonds and SME-platform shares removed. **U2 "Top 500"**: the 500 shares with the highest median daily traded value over the previous six months and a price of at least ₹10 at formation, our stand-in for the NIFTY 500 | U1 matches the paper; U2 is what an investor can trade at size and removes the microcaps and penny stocks that create untradable paper profits (Lesmond et al. 2004; IIMA library drops them too) |
| Dates | Holding months Jan 1965 - Dec 1989, 300 months | **Main sample: holding months Jan 2005 - Oct 2026, 262 months.** Extension Jan 1997 - Dec 2004 reported separately as less reliable | NSE's daily files start in 1995 (one formation year needed); NSE's corporate action list is reliable only from 2005, so earlier returns miss dividends and may miss splits |
| Price data | CRSP daily returns, compounded to months | **NSE daily bhavcopies** (every share that ever traded, so delisted shares are included), adjusted with NSE's corporate action list for splits, bonuses and dividends. **UBI through tradingmachine** is used to cross-check our adjusted prices from Dec 2019 and is the source the hand-off script uses each month | UBI starts on 3 Dec 2019, holds only shares listed today (survivorship bias), has no dividends and misses 15 Feb - 7 Mar 2022 (gaps 1, 2, 7, 24); the paper needs a long history with delisted shares |
| Returns | Total returns | Total returns from 2005 (price, splits, bonuses and cash dividends); price returns plus split/bonus factors before 2005 | Dividend data |
| Size groups (Tables II, III) | Market capitalisation | **Median daily traded value** over the previous six months, terciles within U1; market cap shown for Feb 2024 onward as a check | NSE publishes per-share market cap (PR zip MCAP file) only from Feb 2024; UBI has none (gap 10) |
| Beta groups (Table III) | Scholes-Williams beta from the prior calendar year | Scholes-Williams beta from the prior 12 months of daily returns against the NIFTY 500 | Same idea; Indian index |
| Skip a week | Formed one week after the ranking period ends (p. 70) | Ranking period ends five trading days before the month's last trading day | Daily data makes the gap exact |
| When trades happen | Beginning of month t, using returns up to the end of t−1 | Rank on the close of the last trading day of month t−1 and trade at that close (paper timing). Robustness: trade at the next trading day's close | Signals see only data up to the moment of the trade; the one-day delay shows what a real order would get |
| Trading hours and settlement | NYSE; T+5 in the 1980s | NSE 09:15-15:30; the closing price is the volume-weighted average of the last 30 minutes, so orders go in near the close. Settlement T+1 (T+2 before Jan 2023) | Monthly returns are unaffected; the hand-off must sell first and buy once the sale proceeds are available (gap 19) |
| Short selling | Any stock can be shorted freely | Only covered shorts are allowed. Stock lending (SLB) is thin, so in practice shorting means single-stock futures, which existed for 52 stocks in Jan 2005, 181 in Jul 2024 and 218 in Oct 2026 (F&O bhavcopies) | The paper's long-short portfolio cannot be traded in India as written; see section 4 |
| Costs | One test: 0.5% one way on the risk-adjusted return (p. 77) | Full Indian delivery costs from the shared engine (brokerage, STT 0.1% each side, stamp duty, exchange charges, SEBI fee, GST) plus market impact of 0.1% per side in U2 and 0.3% in U1; futures costs for futures legs. Short side carries no borrowing fee (the engine has none, gap 27), which flatters the paper long-short | ResearchRules require realistic Indian costs before and after |
| Benchmark / market | CRSP value-weighted and equally weighted indices | **NIFTY 500 total return** (price index plus a twelfth of its dividend yield each month where NSE's TRI history cannot be downloaded) as the value-weighted market; equally weighted U1 and U2 returns as the equal-weighted market; **NIFTY200 Momentum 30** and **Nifty500 Momentum 50** as momentum benchmarks for the long-only version; **IIMA WML factor** (Agarwalla, Jacob and Varma, monthly from Nov 1993) as the outside check on the long-short | Indian equivalents |
| Risk-free rate | 1-month T-bill | 91-day T-bill: the RF column of the IIMA monthly file to Dec 2025, then RBI's 91-day T-bill auction yield for 2026 | The engine subtracts no risk-free rate (gap 27), so alphas are computed on excess returns in the study's code |
| Seasonality (Tables IV, V) | January loss, linked to US tax-loss selling | All twelve calendar months, with the January test kept and a **March/April test** added, because the Indian financial year ends on 31 March | Different tax year |
| Delisted shares | Not described in the paper | Kept until their last trade. The engine drops a share from its cohort once it stops trading, so its loss after the last trade is never charged (gap 27). We report a stress test that charges −30% and −100% in the month after a share's last trade | Delisting losses are the biggest survivorship risk in Indian small caps |

## 3. Data plan

All raw files are kept as NSE served them in the git-ignored `data/` folder. Cleaned data go into **TimescaleDB, schema `jegadeesh_and_titman_research_analyst`**, so the monthly refresh only appends new days. Every load is an upsert that is safe to run twice, and the code can rebuild every table from the raw files.

| Source | What | Period | Table in TimescaleDB |
|---|---|---|---|
| NSE CM bhavcopy (old format, then UDiFF from Jul 2024) | Daily close, previous close, traded value, series, ISIN (from about 2018) for every share | Jan 1996 - Oct 2026, about 7,600 files | `daily_prices_raw` |
| NSE corporate actions API, one year per request | Splits, bonuses, dividends with ex-dates | 2005 - 2026 (earlier years kept, flagged) | `corporate_actions`, `adjustment_factors` |
| Derived | Adjusted daily total returns; monthly returns; implausible moves flagged | 1996 - 2026 | `daily_returns`, `monthly_returns`, `return_flags` |
| UBI via `export_prices` | Split- and bonus-adjusted daily candles for today's listed shares | Dec 2019 - Oct 2026 | `ubi_daily_prices` (cross-check only) |
| NSE F&O bhavcopies | Which shares had single-stock futures each month, and their futures closes | 2005 - 2026 | `fno_membership` |
| NSE PR zip MCAP file | Market cap and issued shares | Feb 2024 - Oct 2026 | `market_cap` |
| NSE `ind_close_all` and niftyindices.com | NIFTY 500 (CNX 500 before 2015), NIFTY200 Momentum 30, Nifty500 Momentum 50 closes and dividend yields; TRI history if the niftyindices endpoint can be scripted | Jul 2012 onward from `ind_close_all`; earlier from niftyindices.com | `index_daily` |
| IIMA data library | SMB, HML, WML, MF, RF monthly, survivorship-bias adjusted | Nov 1993 - Dec 2025 | `iima_factors_monthly` |
| RBI | 91-day T-bill yield | 2026 | `risk_free_monthly` |
| Study outputs | Universe membership, ranks, cohort weights, monthly returns of every variant | 2005 - 2026 | `universe_membership`, `rankings`, `strategy_returns_detail`; headline series also in shared `results.strategy_returns` |

Checks before any backtest:

1. Count shares, days and gaps per year.
2. Flag one-day returns below −50% or above +100%. Each one is either matched to a corporate action or set to zero and listed.
3. Compare our adjusted monthly returns with UBI's for every share in both sources, Dec 2019 - Oct 2026. Spot-check known actions such as RELIANCE's 1:1 bonus on 28 Oct 2024 and a sample of splits per year. In 2005 the API showed no split or bonus rows, so early years need extra checking against price jumps.
4. Link renamed shares by ISIN where the files have one.

Already recorded in `workspace/shared/tradingmachine_gaps.md`: gaps 1, 2, 4, 7, 8, 10, 11, 12, 15, 24, 26, 27 and 30 apply to this study. New gaps found during the Data stage will be recorded with `record_gap`.

## 4. The portfolios

| # | Portfolio | Universe | Purpose | Tradeable in India? |
|---|---|---|---|---|
| A | **Paper long-short**: winners decile minus losers decile, all 32 J/K/skip strategies | U1 and U2 | Reproduce Table I and the paper's tests | No: shorting the losers in cash is not allowed. Research only |
| B | **Long-only winners**: top decile, equal weight, K overlapping cohorts | U2 (also U1 for reference) | The strategy an investor can run with delivery (CNC) orders | **Yes** |
| C | **Winners hedged with NIFTY futures**: B plus a short NIFTY 50 futures position of equal value | U2 | A long-short that can be traded: it keeps the stock-selection return and removes most market risk | Yes, with margin |
| D | **F&O long-short**: winners minus losers, both ranked only among shares with single-stock futures that month, losers shorted through futures | F&O list | The closest tradeable version of the paper's short leg | Yes, with margin; small universe (52-218 shares) |

A and B are the core of the study. C and D are extensions, reported after A and B and labelled as such.

## 5. Tables and figures we will reproduce

| Paper | India version |
|---|---|
| Table I (32 strategies, buy, sell, buy−sell) | Same grid for U1 and U2, gross and net of costs, with plain and Newey-West t-statistics, number of months and worst drawdown |
| Table II (beta and size by decile) | Beta against the NIFTY 500 and median traded value (market cap from 2024) by decile, 6/6 |
| Table III (deciles within size and beta groups; CAPM alphas) | Same, with traded-value terciles, beta terciles and alphas against the NIFTY 500 TRI over the T-bill |
| Turnover and the 0.5% cost test (p. 77) | Turnover from the engine and full Indian costs |
| Tables IV and V (calendar months) | 6/6 by calendar month, F-tests, share of positive months, with the March/April focus |
| Table VI (five-year subperiods) | 2005-09, 2010-14, 2015-19, 2020-26 |
| Table VII (36 months in event time) | Same, 6-month ranking, Newey-West t on cumulative returns |
| Table VIII (back-test before 1965) | Not possible. Replaced by the 1997-2004 extension and a look at crash episodes: 2008-09 and the March-April 2020 rebound |
| Table IX (earnings announcements) | Optional extension: NSE results dates exist only from Aug 2007 to Mar 2025 (gap 25). Done last, if time allows |
| New for India | Long-only B against the NIFTY 500 TRI and the momentum indices; C and D; our 6/6 long-short against IIMA WML (correlation and average returns over the same months); delisting stress test |

## 6. Statistics and number of variants

- Every average return comes with its Newey-West t-statistic (the engine's automatic lag count), the number of months and the worst drawdown. The paper's plain t-statistic is shown alongside for comparison.
- Alphas come from regressions on excess returns over the T-bill.
- Variants we will try:
  - Core grid: 4 J × 4 K × 2 skip × 2 universes × 2 portfolios (A, B) = 128.
  - Extensions: C and D for the 16 no-skip strategies (32), the one-day trading delay (16), and two delisting stresses (2), about 50 more.
  - The README and the site will state the total number tried. They will treat the best cell with suspicion, compare it with the Bonferroni bound the paper uses, and lead with 6/6, the paper's own main strategy, instead of the best cell.
- The backtest_reviewer subagent checks the backtest before any result is reported.

## 7. Tests we will write (no network)

1. Bhavcopy parser: old-format and UDiFF sample files give the same columns; series filter; fund units and rights entitlements removed.
2. Corporate action parser: "Bonus 1:1" gives 0.5, "Face Value Split ... From Rs 10/- ... To Re 1/-" gives 0.1, a dividend in rupees, a dividend in % of face value, non-price actions ignored.
3. Adjusted returns on a made-up three-share table with a split, a bonus and a dividend, whose answers are worked out by hand.
4. Implausible-move filter.
5. Monthly compounding, including a share that stops trading mid-month.
6. Ranking: past J-month return windows, the five-day skip, ties, a share with too little history excluded, deciles with share counts not divisible by ten.
7. Universe rules: traded-value ranking, price filter, last-five-days close rule.
8. Portfolio construction through the engine's `OverlappingCohorts`: first and last months, an empty decile, a share that stops trading, the delisting stress.
9. Event-time returns and calendar-month tables on a small series with known answers.
10. TimescaleDB writers: upserts run twice give the same rows (tests use a fake connection, not the real database).
11. One end-to-end test: the whole study on a made-up 40-share, 36-month dataset in seconds.

## 8. Where the Indian version cannot match the paper

1. **Shorter sample:** 262 months in the main sample against the paper's 300, in a market with far fewer traded shares early on (the 3 Jan 2005 bhavcopy has 816 rows across all series, the 30 Oct 2026 UDiFF file 3,641), so early deciles are thinner and t-statistics weaker.
2. **No market cap before 2024:** size groups use traded value, which mixes size with liquidity.
3. **Corporate actions:** dividends only from 2005; split and bonus records thin before 2005 and possibly in 2005 itself. Missed actions show up as false jumps, which we filter but cannot fully repair.
4. **Shorting:** the paper's long-short is a paper portfolio in India; only C and D can be traded, and D's universe is small.
5. **Delisting returns:** unknown; we bound them with a stress test.
6. **Benchmark:** NIFTY 500 total return may have to be approximated from price plus dividend yield.
7. **Earnings tests (Table IX):** limited to Aug 2007 - Mar 2025, and optional.
8. **No pre-sample back-test** like Table VIII.
9. **NSE only:** BSE-only companies are left out, while the paper used NYSE and AMEX together. The IIMA factors use both exchanges, so they will differ from ours somewhat.

## 9. Can this become a trading strategy? Yes

Portfolio B is a portfolio rule rebalanced on a fixed schedule:

1. On the last trading day of each month, rank the top-500-by-traded-value shares on their past J-month return.
2. Buy the top decile, about 50 shares, in equal weights with delivery orders.
3. Hold each month's cohort for K months, so 1/K of the book turns over each month.

This rule can be computed each month from UBI prices through tradingmachine, and run by trading-agent with delivery orders. Portfolio C adds one NIFTY futures hedge order a month.

The hand-off package will:
- fix J and K to the paper's 6/6 unless the results give a strong reason to choose otherwise, chosen before looking at net returns to avoid picking the best cell;
- state the capital needed for 50 to 100 equal positions;
- set risk limits for drawdown and crash periods.

The Hand-off stage and its gate decide whether it is installed.

## 10. Companion site (later stage)

The interactive page will let a reader choose:
- J and K
- skip or no skip
- universe (U1 or U2)
- long-short or long-only (and C or D)
- costs on or off, and the impact cost
- the sample period

It draws from a precomputed grid of monthly returns, so the reader recomputes nothing. A homepage section links to it. A Markdown and a web page give trading-agent's agent the instructions for turning portfolio B into a strategy it can run.
