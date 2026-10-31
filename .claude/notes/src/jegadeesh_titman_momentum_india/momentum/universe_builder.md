# universe_builder.py

- Liquidity counts days without trading as zero, so a share traded on fewer than half of the last 126 days has a median of zero and cannot enter the top 500.
- U1 has no price floor, to stay close to the paper; U2 requires a last close of at least 10 rupees.
- Formation is on the last trading day of each month, and the universe uses only data up to that day.
