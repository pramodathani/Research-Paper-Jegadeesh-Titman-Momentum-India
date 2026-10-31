# daily_return_builder.py

- NSE's PREVCLOSE is not adjusted on ex-dates (RELIANCE 2024-10-28: close 1334.35, previous close 2655.7), so every return divides by the previous close times the action's price factor, not by the previous row's adjusted close.
- Actions are placed on the first trading day on or after the ex-date, up to 10 days later, because some ex-dates fall on holidays.
- The action list is incomplete before 2006 and has gaps after, so a move below -38% or above +60% with no listed action is compared with common split and bonus ratios (1:1 bonus 0.5, 10 to 1 split 0.1, and so on) within 5%. A match is treated as a missed action. Shares priced under 5 rupees are skipped because a one-paisa tick is a 100% move there (VISESHINFO, BIRLACOT).
- Genuine -50% single-day crashes are impossible under NSE's circuit limits except on ex-dates, so treating a halving as a missed 1:1 bonus errs on the side of keeping a loser out of the losers' portfolio. This is the biggest judgement call in the returns and is reported through return_flags.
- Anything still below -50% or above +100% is set to zero and listed. 1,009 days were zeroed and 718 inferred over 1996 to 2026.
- A share in both EQ and BE on one day keeps EQ.
