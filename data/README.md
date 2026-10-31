# Data

Everything here is git-ignored except this file. All raw files are exactly as the source served them, fetched on 2026-10-31 with the downloaders in `src/jegadeesh_titman_momentum_india/data/`, which skip files already on disk so a stopped download can simply be started again. Raw exchange data is never published; only derived results are.

| Folder | What | Source | Period | Count |
|---|---|---|---|---|
| `ubi/instruments_nse_equities.parquet` | UBI's instrument master for NSE shares | `export_instruments` (nse, equities) | listed today | 3,543 instruments |
| `ubi/prices_nse_equities_day_adjusted.parquet` | Daily candles adjusted for splits and bonuses, not dividends | `export_prices` (nse, equities, day) | 2019-12-03 to 2026-10-29 | 2,962,743 candles, 2,607 shares; 914 listed symbols have none |
| `nse/bhavcopy/` | Daily cash-market bhavcopy zips, old format to 2024-07-05, UDiFF after | `nsearchives.nseindia.com/content/historical/EQUITIES/...` and `/content/cm/BhavCopy_NSE_CM_...` | 1996-01-01 to 2026-10-30 | 7,628 files; 417 weekdays have none (holidays), listed in `not_available.txt` |
| `nse/fno/` | Daily futures and options bhavcopy zips | `.../historical/DERIVATIVES/...` and `/content/fo/BhavCopy_NSE_FO_...` | 2005-01-03 to 2026-10-30 | 5,387 files; 202 weekdays have none |
| `nse/index/` | `ind_close_all` csv: every NSE index's close, P/E, P/B and dividend yield | `.../content/indices/ind_close_all_DDMMYYYY.csv` | 2012-02-21 to 2026-10-30 | 3,612 files; 258 weekdays have none |
| `nse/corporate_actions/` | NSE corporate actions API, one JSON per year | `nseindia.com/api/corporates-corporateActions` | 2000 to 2026 (ex-dates to 2026-11-06) | 27 files, 41,483 share-series rows after filtering |
| `nse/iima/` | IIMA Indian four-factor monthly file (SMB, HML, WML, MF, RF in percent), survivorship-bias adjusted, release 2025-12 | `faculty.iima.ac.in/iffm/Indian-Fama-French-Momentum/DATA/` | 1993-10 to 2025-12 | 387 months |

## TimescaleDB

Schema `jegadeesh_and_titman_research_analyst`, built by `python -m jegadeesh_titman_momentum_india.scripts.load_database <source>`, where source is `bhavcopy`, `fno`, `index`, `corporate_actions`, `iima` or `ubi`. Every load is an upsert, so running it again changes nothing, and each table can be rebuilt from the raw files above.

| Table | Holds | Rows | Dates |
|---|---|---|---|
| `daily_prices_raw` | NSE bhavcopy rows for series EQ, BE and BZ, prices unadjusted, ISIN from 2013 | 10,735,705 (5,723 symbols) | 1996-01-01 to 2026-10-30 |
| `ubi_daily_prices` | UBI adjusted daily candles, for cross-checks | 2,962,743 | 2019-12-03 to 2026-10-29 |
| `corporate_actions` | Splits, bonuses, dividends and other actions for share series | 41,483 | 2000-01-03 to 2026-11-06 |
| `index_daily` | Index closes, P/E, P/B and dividend yield | 296,883 (237 indices) | 2012-02-21 to 2026-10-30 |
| `fno_stock_futures_daily` | Nearest-expiry stock future of each share each day: close, settle and open interest | 967,094 (563 symbols) | 2005-01-03 to 2026-10-30 |
| `iima_factors_monthly` | IIMA factors in percent | 387 | 1993-10 to 2025-12 |

## Coverage

- **Shares trading in the NSE files:** 1,456 in 1996, 957 in 2005, 1,520 in 2010, 1,807 in 2019, 3,086 in 2026. Includes shares that were later delisted. The counts also include ETFs and other non-company instruments in the EQ series; the Build stage removes them with ISIN prefixes (INF) and name patterns.
- **Stock futures:** 123 distinct shares during 2005, 230 in 2010, 231 in 2024.
- **Series:** EQ 9,884,782 rows, BE 782,676, BZ 68,247.
- **ISIN:** present from 2013, absent before, so renamed shares before 2013 are not linked by ISIN.
- **No hole in 2022:** the NSE files have every session from 15 Feb to 7 Mar 2022, which UBI lacks.

## Checks and known problems

1. **UBI against NSE** (Dec 2019 to Oct 2026, 2,530 shares in both): UBI's close divided by NSE's raw close should step only on corporate action days. Of 709 steps larger than 2%, 462 fall within 5 days of an NSE bonus, split or similar action. 189 persistent steps in 72 shares match no NSE action, and 121 of 591 NSE splits and bonuses have no UBI step. Examples: AHLEAST bonus ex 2022-10-06 stepped in UBI on 2022-12-06; AKI split ex 2023-06-22 stepped on 2024-04-23. So returns are built from NSE data and UBI is used only as a cross-check (gap 32). On the last day the ratio is 1 for 99.96% of shares.
2. **Corporate actions before 2006** are too thin to adjust prices: 2005 has 1 bonus and 0 splits, 2006 has 27 bonuses and 29 splits (gap 31). Earlier splits are detected from price jumps.
3. **Dividend amounts** in the API are text such as "Dividend - Rs 2 Per Share" or a percentage of face value; the Build stage parses them.
4. **Index history:** the NIFTY 500 appears from 2012-02-21 (as S&P CNX 500, CNX 500 from 2013, Nifty 500 from 2015-11-09); the NIFTY200 Momentum 30 and Nifty500 Momentum 50 from 2016-07-07. No total-return index history could be scripted from niftyindices.com. The market return for 2005 to 2011 comes from the IIMA MF column.
5. **Risk-free rate:** the IIMA RF column ends in December 2025; 2026 months need RBI's 91-day T-bill yield, not yet fetched.
6. **Market capitalisation:** not downloaded. NSE's file exists only from February 2024, so size groups use median traded value.
7. **Date formats:** NSE prints some old files' dates with two-digit years (for example 13-Jul-20) and some index files with slashes; both parsers handle them and have tests.
