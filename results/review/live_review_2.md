# Live review 2: commits fba0bd2, 1721a74, d56d18e (after 2059a3a)

Reviewer: backtest_reviewer, 2026-10-31. No source files were changed. Scratch scripts are in /tmp/rv.

## What changed
- make_live_tables.py: `_decile_rows` (10 deciles + 10-1 per group, 64 specs; size/beta groups only for U1, 32 specs) and `_event` (per universe/skip/J: 36-month event-time and 3-day announcement spreads).
- app.js: Tables 4-8 and Figure 5 now look up `snapshot.live` for the chosen J, K, gap and universe; Figures 6-7 (January) are new.
- make_results.py: robustness checks and portfolios C/D now cover all 16 J/K pairs (608 and 64 rows).

## Check 1: 6/6 equals the fixed tables (pass)
- Table II U1/U2 vs live `U?|0|6|6`.joint.All.deciles: mean, t, alpha, alpha t, beta within 5e-6 / 5e-5 (rounding to 5 and 4 places); traded value within 0.05 crore (rounded to 0.1); months = 262 on both sides.
- Table III, all 7 groups (U1): max difference 5e-5.
- Table VII U1/U2: all 36 monthly, monthly_t, cumulative, cumulative_t within 5e-6 / 5e-5.
- Table IX U1/U2: announce and announce_t within 5e-6 / 5e-5.
- Robustness: the 152 old rows (the earlier J in 6,12 by K in 3,6 subset) are present unchanged in the new 608-row file (max difference 0). Portfolios C/D: the 16 old rows are unchanged in the new 64-row file.
- snapshot.json `live` equals results/live/live_tables.json exactly.

## Check 2: other J/K consistent with the main grid (pass)
- For all 64 specs, live decile 10, decile 1 and 10-1 gross means equal table1_main.csv buy/sell/long_short gross_mean within 5e-6, and the 10-1 t within 5e-5.
- The robustness `base` rows (96) equal table1_main.csv (no gap) exactly: gross and net mean, months.

## Check 3: look-ahead
- Event time (EventTimeReturns.spread_matrix): deciles at row t (ranking ends at the end of month t, or a week earlier with the gap) are followed from month t+1 (lag >= 1). No look-ahead.
- Size terciles: median daily traded value before each formation date (StudyRunner.liquidity). Beta terciles: Scholes-Williams beta on the 252 days ending at the formation date; the lead term is masked on the last day (scholes_williams_beta.py `_slope`, shift -1 sets market[-1] = NaN), so no future day enters. No look-ahead.
- Announcement window (days -2 to 0, announcement_returns.py): 7.6% of the 106,727 announcements have day 0 on the month's 1st trading day and 3.1% on the 2nd, so for lag 1 part of the window is in the formation month (inside the ranking window when there is no gap). This existed in the fixed Table IX too. Test: dropping announcements with day 0 on the 1st or 2nd trading day changes U1 (no gap) months 1/2/3 from 0.89/0.35/0.85% to 0.39/0.02/0.30%. Months 2 and 3 cannot overlap the ranking period, yet they fall by about as much as month 1, so this is a sample effect, not a lag-1 overlap bias. U2 barely changes (1.24 to 1.21% at lag 1). Still, the U1 announcement result depends on early-month announcements; worth saying.

## Check 4: JS lookups
- Keys use `${universe}|${skip}|${j}|${k}`, with skip, j and k held as Numbers (readHash and bind use Number()), so they match the JSON keys. `announce[month - 1]` and the x axis `index + 1` are correctly 1-based. Decile rows are unpacked in the order [label, mean, t, alpha, alpha_t, beta, traded], which matches `_decile_rows`. There are no None values in any live decile or event array.
- renderRobustness and the C/D rows ignore the gap. The captions say so ("no gap"; "C and D have no gap"), but with gap = 1 the B row has a gap while C/D do not.
- The B row's net figure follows the impact/brokerage sliders (returns()), but C/D and Table 8 use the fixed default costs.
- The Table 6 caption says "Live in ... universe", but renderEvent always shows both universes and ignores state.universe. Only the caption is wrong.
- A hash such as #j7 makes liveEntry return undefined, and update() throws in renderFurther before renderDeciles etc. readHash does not check J/K against {3,6,9,12}. This was already true for renderFurther; it now also blanks Tables 4-8.

## Check 5: January charts (Figure 7) and Table 9
- "Reversed in every January" negates the net return (`-value`), which turns the January trading cost into a gain. A reversed strategy should earn -gross minus costs (plus the cost of flipping the book). From the snapshot, 6/6 net: U2 reversed January mean -2.55% shown vs -2.83% (-gross - cost); U1 -1.36% vs -1.92%. The bias favours the reversal, so the conclusion "the reversal loses" is conservative, but the reversed net numbers in Table 9 and Figure 7 are too high by 2x the January cost.

## Check 6: when months are added
- update_study order: table nine (rewrites data/derived/announcement_returns.parquet) runs before make live tables, so the announcement matrix is fresh. Main sample end comes from StudyPeriod.end(). The JS uses snapshot.main_sample/months. The hard-coded '2005-01' (renderTradeable) and '2007-07' (first announcement formation) are fixed design starts, so they are fine.
- Event-time and decile tables are fixed to 2005-01..END and ignore the page's sample selector. The note says so.
- Nothing found that breaks.

## Check 7: tests
- pytest: 100 passed. No test covers `_decile_rows`, `_event`, the robustness/C-D loops or the JS lookups. The cross-checks above (Checks 1-2) could become a regression test.

## Variants
variants_tried.txt was updated (robustness 512 series, C/D 32). No new parameters were searched; these only fill in the existing 16-cell grid.

## Verdict: sound with caveats
1. January reversal (Table 9, Figure 7) negates net returns, which credits costs to the reversed strategy: +0.28%/Jan (U2 6/6) and +0.56%/Jan (U1 6/6). Fix: reverse = -gross - cost (and, ideally, add the flip turnover).
2. U1 announcement spreads depend on announcements on the 1st/2nd trading day of a month (10.7% of events). Without them, the U1 month-1 spread drops from 0.89% (t 2.99) to 0.39% (t 1.24). This is not look-ahead (months 2-3 move as much), but report it, or start the window at day 0 >= the 3rd trading day for lag 1.
3. The Table 7 B row has a gap and follows the cost sliders while the C/D rows do not; the Table 6 caption claims it is live in universe. Fix the captions or align them.
4. readHash accepts any J/K; an invalid hash blanks all the looked-up tables. Fix: validate against {3,6,9,12}.
5. No tests for the new precompute. Fix: add the 6/6 equality and the grid-consistency checks as tests.
