# Review: live tables, renderFurther (Tables 9-14), StudyPeriod, grouped deciles skip

Reviewer: backtest_reviewer, 2026-10-31. Source files were not changed. Scratch scripts: /tmp/rv/js_replica.py, /tmp/rv/skipcheck.py.

## What was checked
- make_live_tables.py: 64 specs (U1/U2 x skip 0/1 x J x K): Section III (WRSS, decile profits, decomposition, lead-lag), buy-and-hold, joint F tests.
- app.js renderFurther: Table 9 (January flip), 11 (flat charge), 12 (alphas, VW and EW market), 13 (buy-and-hold, looked up), 10 and 14 (looked up).
- study_period.py and every script's END; grouped_decile_runs.decile_returns skip change.

## Results
1. **JS matches Python.** I re-implemented the renderFurther formulas in Python against snapshot.json:
   - flat_cost_test.csv, all 32 rows: largest gaps are 5e-6 in mean, 6e-5 in annual alpha and 0.002 in alpha t.
   - january_reversal.csv, 4 rows: means within 4e-6, t within 0.001, January counts identical (22; 16/15/18/17 losing).
   - alpha_by_market_weighting.csv, 12 rows: alpha within 5e-6, t within 0.002, beta within 1e-4.
   The gaps come from rounding the snapshot to 1e-4. Both sides use OLS t for alpha (ReturnStatistics.market_model) and plain t for the January t.
2. **The live JSON matches the further CSVs.** U1|0|6|6 Section III equals section3_profit_summary.csv (256 months, 0.0684, t 3.3448; deciles 0.1090, t 3.9988, corr 0.9332). The decomposition equals section3_decomposition.csv. Joint "All" (F 4.541 / 5.0817) equals table3_joint_tests.csv. Hold 0.0179, t 4.3177 equals buy_and_hold_vs_rebalanced.csv.
3. **The decile_returns skip change is correct.** decile_returns(None, None, J, K, u, skip)['10-1'] equals the main grid's gross long_short exactly (largest gap 0.0, 262 months) for U1 skip 6/6, U2 skip 12/3 and U1 no-skip 6/6. The skip goes through runner.past_returns, the same path as the grid.
4. **No look-ahead found** in:
   - the ranking windows, which end at the formation date or 5 trading days before it;
   - the holding returns, which start the month after formation (BuyAndHold loop formation+1; ProfitSources shift(-K));
   - the equally weighted market, which uses U1 eligibility shifted by 1;
   - the size terciles (past median traded value) and beta terciles (the 252 days up to the formation date).
   The known ex-post element is the "N extreme shares dropped" row in Panel B: shares are chosen by realised K-month returns above 1000%. It is labelled and is a diagnostic only.
5. **Tests:** `pytest`: 100 passed.

## Findings (most serious first)
1. **Table 10, Panels B and C do not vary with J (Panel B not with the gap either), although the caption says "Live in J, K, gap and universe".**
   - ProfitSources.decomposition() never uses past_returns: it uses only the universe and the horizon K. In live_tables.json there is exactly one distinct decomposition across the 8 (J, skip) pairs for each universe and K I checked.
   - lead_lag() measures the market over `self.horizon` (K) months (profit_sources.py, lead_lag: `logs.rolling(self.horizon)`), not over the J-month ranking window that its docstring describes. For J≠K, e.g. 12/3, the regressor is the 3-month market return. This is identical to the paper only at J=K=6.
   - Fix: pass J for the lead-lag window, or say in the caption that Panels B and C depend on K only.
2. **The value-weighted market and its alphas stop at 2025-12, and the gap grows with every refresh.**
   - The snapshot's `market` and `wml` end 2025-12 (348 non-null), while `rf` is forward-filled to 2026-10 (iima_factors.py:47-48).
   - So Table 12 (VW), Table 11 alphas (252 months against 262 for the means), the Table 14 zero-alpha F tests (dropna in JointTests) and the Panel C lead-lag (252 months) use samples that end 2025-12, while their captions say "2005 to {end}".
   - The risk-free rate for every new month repeats Dec 2025's, and the footnote is hardcoded "The risk-free rate for 2026 repeats December 2025's" (index.html:178), which will be wrong in 2027.
   - Fix: show the months used for each alpha, or extend the market (e.g. NIFTY 500 TRI after the IIMA release), and fill the footnote from data.
3. **The month-completeness rule can accept a month that is one trading day short.** last_complete_month allows one remaining weekday. With data to Thursday 2026-10-29 it returns 2026-10 complete (checked), although Friday 2026-10-30 was a trading day and is in the data. A refresh run before the last bhavcopy is published would form portfolios a day early and record a short final month. It would then be silently restated on the next run.
   - The current data are fine: they run to 2026-10-30, the last weekday of the month.
   - Fix: use an NSE holiday calendar, or require the last weekday unless a known holiday intervenes. At the least, print a warning when the rule uses its one-day allowance.
4. **The sample choices are fixed in index.html:67.** "first half" = 2005-01|2015-11 and "second half" = 2015-12|END. app.js:801 replaces only '2026-10', so the halves become unequal as months are added. The "2010 to" option is also fixed (acceptable). Old shared URLs with `from2015.12to2026.10` set a sample that no select option matches. Fix: build the half split from snapshot.main_sample.
5. **The page text and the default Table 9 view disagree.**
   - Section 4.8 (index.html:146) says January momentum is "+1.6% to +3.2%" with t "−1.1 to −1.9". These are the 4 gross specs in january_reversal.csv.
   - The default view (U2, net, all 16 J/K) shows January spreads of 1.02%–3.08% with t −0.79 to −1.89. For U1 net the range is 0.04%–1.46% with t −0.04 to −1.22 (computed from the snapshot).
   - Fix: reword the sentence to "for 6/6 and 12/3 before costs", or quote the range of the default view.
6. **Lower-severity items:**
   - StudyPeriod.end() silently falls back to '2026-10' when grid.parquet is missing (study_period.py:22,82-83). After an extension, a missing grid would give stale ENDs without any error. Raising would be safer once the study is past the first build.
   - make_table_nine.py has no END cut. It relies on daily_returns already being cut by build_returns, which is fine as long as update_study's order is kept.
   - No hardcoded '2026-10' remains in the scripts. In app.js it is only the default replaced on load (line 51) and the replace() anchor (line 801). StudyPeriod.FALLBACK_END is the only Python literal.
   - Captions of Tables 10, 13 and 14 say "before costs" and are not affected by the sample control. This is correct but easy to misread next to the live Tables 9, 11 and 12.

## Verdict: sound with caveats
The numbers the browser computes reproduce the Python results. The new skip path is exact, and I found no look-ahead. The caveats are labelling and refresh issues: Panels B and C are not J-specific, the VW-market alphas end 2025-12 while the captions say otherwise, the completeness rule can accept a short month, the sample halves are fixed, and one prose range differs from the default view.
