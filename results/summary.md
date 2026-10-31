# Results: Jegadeesh and Titman (1993) momentum on NSE shares

All numbers come from the code in this repository, run on 31 October 2026. Returns are average monthly returns. "Gross" is before costs. "Net" is after Indian delivery costs from the shared engine: STT, stamp duty, exchange and SEBI charges, GST, zero brokerage, and market impact of 0.3% per side for all shares (U1) or 0.1% for the top 500 (U2). t-statistics use Newey-West standard errors unless marked "plain". The main sample has 262 holding months, January 2005 to October 2026. Every table is in `summary_tables.md`, and the CSV files in this folder hold every number.

## In plain words

1. **Momentum is strong in India, stronger than in the paper's US data.**
   - Buying the top tenth of NSE shares by 6-month return and selling the bottom tenth, each held 6 months, earned 1.64% a month before costs and 1.36% after across all shares (Newey-West t 3.26 after costs).
   - In the top 500 it earned 1.42% before and 1.28% after (t 3.07).
   - The paper's 6/6 figure is 0.95% a month (t 3.07, p. 70).
   - All 64 winners-minus-losers cells (2 universes × 2 skip settings × 4 J × 4 K) are positive after costs. The weakest is 3/3 in all shares, at 0.49% a month after costs.
2. **The effect shrinks as shares get bigger and more liquid.**
   - In the top 200 by traded value, 6/6 earns 0.99% before costs and 0.85% after (t 1.90).
   - In a long-short limited to shares with stock futures (portfolio D) it earns 0.77% before and 0.65% after (t 1.40). Neither is significant at 5%.
   - Most of the paper-style spread comes from mid and small shares.
3. **The short side cannot be traded in India as the paper assumes.**
   - Charging a 3% a year borrowing fee on the short leg cuts the top-500 long-short to 1.03% a month (t 2.47).
   - The tradeable versions are:
     - the **long-only winners** portfolio: 1.75% a month after costs in the top 500;
     - **winners hedged with NIFTY futures** (portfolio C): 1.05% a month after costs since March 2012, t 2.65, worst drawdown −32%.
4. **Long-only winners mostly earn the market's return.**
   - Against the IIMA market, top-500 winners have a beta of 1.18 and an alpha of only 0.25% a month after costs (t 1.07).
   - Against the NIFTY 500 since 2012 their alpha is 0.63% a month (t 2.06). They returned 21.9% a year against the index's 13.2%, but with a worst drawdown of −40% against −29%.
   - The extra return is real but comes mainly with more risk.
5. **Momentum crashes are the main risk.**
   - In May 2009 the top-500 long-short lost 49% in one month, as beaten-down losers rebounded.
   - The worst drawdown of the 6/6 long-short is −69% in the top 500 and −62% in all shares.
   - From 2010 the top-500 long-short earned 1.55% a month after costs (t 4.55), with a worst drawdown of −33%.
6. **Indian seasonality differs from the US January effect.**
   - The paper finds a 7% loss every January. India has none: January is +1.6% to +2.7%.
   - Instead, March, the last month of India's financial year, is strongly positive (+4.6% in all shares, plain t 5.26).
   - April is negative (−2.5% and −1.2%), as is December.
   - July is the strongest and most reliable month (+3.7% and +4.1%, positive in more than 90% of years).
7. **No long-run reversal in the top 500.**
   - The paper finds about half of the first year's gain lost over months 13 to 36 (Table VII, p. 84).
   - In India, among all shares, the cumulative 6-month winners-minus-losers return peaks at 14.3% after 12 months and stays flat to month 36.
   - In the top 500 it keeps rising, to 17.8% after 36 months.
8. **Our series lines up with the outside benchmark.** The 6/6 long-short has a correlation of 0.75 (all shares) and 0.83 (top 500) with IIMA's Indian WML momentum factor, which averaged 1.15% a month over the same months.

## Table I against the paper (6/6, no skip)

| | Paper, US 1965–89 (p. 70) | India, all shares (U1) | India, top 500 (U2) | India, top 200 |
|---|---|---|---|---|
| Buy (winners) | 1.74% | 2.22% gross / 2.09% net | 1.82% / 1.75% | 1.59% / 1.53% |
| Sell (losers) | 0.79% | 0.59% / 0.44% | 0.40% / 0.32% | |
| Buy − sell | 0.95% (plain t 3.07) | 1.64% (t 3.92) / 1.36% (t 3.26) | 1.42% (t 3.41) / 1.28% (t 3.07) | 0.99% (t 2.21) / 0.85% (t 1.90) |
| Worst drawdown of buy − sell, net | not reported | −62% | −69% | |
| Months | 300 | 262 | 262 | 262 |
| Turnover, each leg, one-way, a month | about 14% (84.8% over six months, p. 77) | 16% (0.32 bought plus sold) | 16% (0.32) | |

Monthly turnover per leg, counted one way, is a little above the paper's (16% against 14%), because Indian decile membership changes slightly faster. The engine reports bought plus sold, which is why its figure is 0.32. Costs take 0.14% a month from the top-500 long-short and 0.28% from all shares.

The full grid, both panels and both universes, is in `summary_tables.md`. As in the paper:
- J = 6 to 12 with short holding periods does best. The highest after-cost cells are 12/3 in all shares (1.61%) and 9/3 and 12/3 in the top 500 (1.55% and 1.58%).
- The one-week skip raises returns a little.
- Unlike the paper, where 3/3 is the only cell not significant, in India 3/3 is weakest only after costs, because its turnover is highest.

## The other tables

- **Table II, deciles.** Average returns rise almost steadily from decile 1 to decile 10 in both universes. The extreme deciles hold smaller, higher-beta shares, as in the paper. The losers' beta, 1.49 to 1.56, is the highest of any decile. The long-short's beta is −0.28 (U1) and −0.38 (U2), against −0.08 in the paper.
- **Table III, size and beta groups** (6/6, all shares):
  - The long-short is positive and significant in every tercile: 1.62% (small), 2.17% (middle) and 1.45% (large); 1.53%, 1.78% and 1.74% from low to high beta.
  - Its CAPM alpha against the IIMA market ranges from 1.69% to 2.45% a month, all with t above 4.4.
  - Unlike the paper, the losers carry a large negative alpha (−1.11% a month, t −2.41). In the paper the abnormal return came from the winners.
- **Tables IV and V, calendar months:** see finding 6. For all shares the F-test rejects equal months (p = 0.006); for the top 500 it does not (p = 0.17).
- **Table VI, subperiods** (6/6 long-short, gross):

| Period | All shares (plain t) | Top 500 (plain t) |
|---|---|---|
| 2005–2009 | 0.96% (0.87) | 0.54% (0.45) |
| 2010–2014 | 2.44% (3.86) | 2.11% (2.79) |
| 2015–2019 | 2.36% (3.95) | 1.96% (3.38) |
| 2020–2026 | 1.01% (1.56) | 1.18% (1.93) |

  The 2008 crash and the 2009 rebound swamp 2005–09, and 2020–26 is weaker than the 2010s. Split in two halves, top-500 net returns are 1.26% (t 1.72) for 2005-01 to 2015-11 and 1.31% (t 3.26) for 2015-12 to 2026-10. The average holds steady; its significance comes from the second half.
- **Table VII, event time:** see finding 7. Month 1 is positive in India (+1.07% and +1.90%). In the paper it is slightly negative because of short-term reversal (p. 84).
- **Table VIII, before 1965:** has no Indian counterpart. On less reliable 1997–2004 data:
  - the top-500 6/6 long-short earned 2.24% gross (t 2.18);
  - the all-shares version lost 0.18%, because its losers earned 3.06% a month.
  - Before 2006, NSE's corporate action list is thin and many actions had to be inferred from price jumps (see `data/README.md`), so we do not rely on the all-shares extension.
- **Table IX, results announcements** (106,727 quarterly results filed with NSE, formations July 2007 to 2025; NSE's filing list thins after March 2025, gap 25):
  - Past winners beat past losers by 0.89% (all shares, plain t 2.99) and 1.24% (top 500, t 3.56) over the three days around results announced in the first month after ranking. The gap stays positive through month 3 and fades by month 5.
  - Among all shares it turns negative in months 15 to 18 (−0.70%, t −2.01, and −0.81%, t −2.16).
  - This is the paper's pattern: +0.55% to +0.90% in months 1 to 6, about −0.7% in months 11 to 18 (p. 88). Part of the momentum return arrives when results are announced, as the paper's delayed-reaction story predicts.

## Robustness (6/6, net of costs, Newey-West t)

| Check | All shares, long-short | Top 500, long-short | Top 500, winners only |
|---|---|---|---|
| Base | 1.36% (3.26) | 1.28% (3.07) | 1.75% (3.16) |
| Trade one day after the formation close | 1.41% (3.38) | 1.28% (3.02) | 1.74% (3.13) |
| Brokerage of 0.03% per side | 1.34% (3.20) | 1.26% (3.02) | 1.74% (3.14) |
| Market impact doubled to 0.6% per side (all shares) | 1.16% (2.78) | | |
| −30% charged to every share in the month after its last trade | 1.43% (3.44) | 1.28% (3.08) | 1.72% (3.10) |
| −100% charged the same way | 1.60% (3.80) | 1.28% (3.07) | 1.65% (2.97) |
| Borrowing fee of 3% a year on the short leg | 1.11% (2.66) | 1.03% (2.47) | |
| Top 200 instead of top 500 | | 0.85% (1.90) | 1.53% (2.82) |

Delisting losses help the long-short, because vanished shares sit mostly among the losers. They cost the winners 0.10% a month at the −100% extreme.

The backtest reviewer's fragility checks, run before the final fixes, are in `review/fragility.csv`:
- dropping 2005–09 raises the top-500 long-short to 1.73% gross (t 5.10);
- clipping returns at the 1st and 99th percentiles leaves it at 1.55%;
- restricting to shares priced at ₹50 or more lowers it to 1.33%.

## Portfolios that can be traded

| Portfolio, J = 6, K = 6 | Months | Mean, net | NW t | Worst drawdown | Alpha (t) |
|---|---|---|---|---|---|
| B: top-500 winners, long only | 262 | 1.75% | 3.16 | −74% | 0.25% (1.07) against the IIMA market |
| C: B hedged with NIFTY 50 futures, since 2012-03 | 176 | 1.05% | 2.65 | −32% | 0.61% (1.80) |
| D: long-short among F&O shares, losers shorted through stock futures | 256 | 0.65% | 1.40 | −67% | 1.02% (2.34) |

C and D for J = 12, K = 3 earn 1.38% (t 3.21) and 0.68% (t 1.18) after costs. All four C and D pairs are in `summary_tables.md`.

## What was tried

The core grid has 192 series: 2 universes × 2 skip settings × 4 J × 4 K × 3 legs (winners, losers, long-short), of which 64 are long-short. The robustness checks add about 130 series on 4 J and K pairs, and portfolios C and D add 16. The 6/6 strategy was chosen as the lead before any results were seen, because it is the paper's own (plan, section 9).
- 42 of the 64 long-short cells have a gross Newey-West t above 3.16, the Bonferroni cut-off for 64 two-sided tests, and 20 do after costs (the reviewer counted 49 before the final fixes).
- The best cells (12/3, 9/3) should be read with suspicion. We report 6/6 instead.

## Review

The backtest_reviewer subagent checked the backtest on 31 October 2026 (`review/review.md`).
- **No errors found:**
  - it found no look-ahead and no coding errors;
  - it reproduced the headline exactly;
  - it checked known actions: RELIANCE's 2024 bonus, INFY's 2014 bonus and HDFCBANK's 2019 split.
- **Five points, all handled:**
  1. The short leg is not tradeable. It is reported as a paper benchmark, with a borrowing-fee stress and the tradeable C and D.
  2. The result depends on size. The top-200 universe is added.
  3. Significance depends on the sample period. Half-sample results are reported.
  4. Some real crashes (UNITECH 2008, YESBANK 2020) were mistaken for splits or zeroed. The rule now keeps a move as real if it rebounds by more than 30% within five days or does not come back.
  5. 0.3% impact is optimistic for all shares. 0.6% is reported.
- **Wrong previous closes:** the review also found NSE files with wrong previous-close values; these are now repaired from the prior day's close.
- **Before and after the fixes:** the 6/6 top-500 long-short moved from 1.54% to 1.42% a month before costs.

## Library gaps met

- Gap 27: the engine drops a share that stops trading from its cohort without charging a loss, has no risk-free rate in its alpha, and has no borrowing fee. The study adds its own delisting stress, its own excess-return alphas and a borrowing-fee stress.
- Gap 31: NSE corporate actions are thin before 2006.
- Gap 32: UBI's split and bonus factors are missing or misdated for some shares.
- Gaps 1, 2, 7, 8, 10, 11, 12 and 15: no long history, no delisted shares, no dividends, no corporate action list, no market cap, no index constituents, no total-return index and no risk-free rate in tradingmachine. This is why the study builds everything from NSE files.

## Caveats

- **Risk-free rate:** the IIMA file ends in December 2025, so the ten 2026 months repeat December 2025's rate.
- **Size:** measured by traded value, because India has no market-cap history before 2024.
- **NIFTY 500 total return:** approximated as price plus a twelfth of the dividend yield, and available only from 2012. Before that, the IIMA market series is used.
- **Costs:** zero brokerage, as at discount brokers, and no depository charges.
- **Short leg:** shorts pay delivery costs and, in the base case, no borrowing fee.
- **Portfolio D:** ignores the futures basis and the cost of carry.
- **Data before 2006:** less reliable, as described above.

## Further tests from the paper (results/further/)

All numbers come from `scripts/make_further_results.py`. U1 = all shares, U2 = top 500 by liquidity. Not yet reviewed by backtest_reviewer and not yet on the companion page.

**January reversal (footnote 15 idea: do the opposite in January).** In India momentum does not lose in January, so flipping the spread in January cuts the return rather than adding to it.

| Universe, J/K | Normal mean/month | Reversed mean/month | Normal compound a year | Reversed compound a year | Januaries reversal loses / gains (of 22) | t of the reversal's January return |
|---|---|---|---|---|---|---|
| U1 6/6 | 1.64% | 1.36% | 18.5% | 14.6% | 16 / 6 | -1.47 |
| U1 12/3 | 1.90% | 1.63% | 20.3% | 16.4% | 15 / 7 | -1.13 |
| U2 6/6 | 1.42% | 0.97% | 15.2% | 9.2% | 18 / 4 | -1.93 |
| U2 12/3 | 1.74% | 1.21% | 17.0% | 9.8% | 17 / 5 | -1.78 |

The reversal still has a positive overall return only because the other 11 months carry it. The average January momentum spread is +1.6% to +3.2%, so reversing it gives up that amount. The result is not significant at 5% (t between -1.1 and -1.9), and the worst January for the reversal is 2012 for U1 (momentum was -15% that January and the reversal made +15%). By-year figures: `january_reversal_by_year.csv`.

**Section III, profit sources.** Weighted relative strength (WRSS) averages 6.8% a month in U1 (NW t 3.34) and 6.1% in U2 (t 2.85); correlation with the decile spread is 0.93 (U1) and 0.97 (U2), against 0.95 in the paper. Lead-lag coefficient theta: -0.84 (t -1.97) for U1 whole sample, halves -0.95 and -0.46; the paper has -2.29 (t -1.74). The sign matches the paper. The U1 decomposition is dominated by noise from tiny shares (beta variance 8.5), so rely on U2 (dispersion +0.0050, factor 0.00002, idiosyncratic 0.0021).

**Tables III and IV joint tests.** Equal decile returns are rejected for all groups (F 4.5, p 1.5e-5) and zero alphas too (F 5.1, p 1e-6). The size split: the F-test for equal returns across deciles rejects for small and mid shares (p 0.01 and 0.004) but not for the largest third (p 0.16).

**Buy-and-hold vs monthly rebalanced.** Buy-and-hold deciles earn slightly more in every cell (e.g. U1 6/6 1.79% vs 1.64% a month, NW t 4.32).

**Flat 0.5% one-way cost test (paper: 9.29% a year).** U1 6/6 after 0.5% one-way: 1.30% a month, alpha 18.2% a year (t 4.01). U2 6/6: 1.09% a month, alpha 16.6% (t 3.58). Momentum survives the paper's flat charge across all 32 cells (alpha t 1.6 to 4.0).

**Alphas against an equally weighted market.** Long-short alpha 1.99% a month (t 5.88) U1, 1.81% (t 5.21) U2; the loser leg's alpha is -1.27% (t -6.41) against the equally weighted market, so most of India's momentum profit comes from the short side, which the long-only portfolio cannot capture.

Also written: Table IV and VI by size (`table4_by_size.csv`, `table6_by_size.csv`), event-time betas (`table7_betas_*.csv`) and the 1997 to 2004 event-time extension (`table7_extension_1997_2004_*.csv`).
