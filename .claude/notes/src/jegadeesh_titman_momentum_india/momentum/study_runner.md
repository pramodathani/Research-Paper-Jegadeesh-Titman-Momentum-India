# study_runner.py

- No-skip ranking ends at the month's last trading day. Skip moves both ends of the window back 5 trading days, and the cohort is still bought at month end, so the gap is a week between the end of the ranking window and the purchase, as in the paper's Panel B.
- Impact cost is 0.3% per side for U1 and 0.1% for U2; brokerage is zero for delivery (discount brokers) and can be set. Engine costs include STT, stamp duty, exchange and SEBI charges and GST.
- The short leg is a paper portfolio: it pays the same delivery costs on its turnover as a long leg and no borrowing fee, because the shared engine has none (gap 27). So long-short net returns flatter what a real short would earn.
