import os
import time

import pandas as pd
import psycopg

from jegadeesh_titman_momentum_india.momentum.daily_return_builder import (
    DailyReturnBuilder,
)

S = 'jegadeesh_and_titman_research_analyst'
t = time.time()
c = psycopg.connect(os.environ['RESEARCH_ANALYST_TIMESCALEDB_URL'])
prices = pd.DataFrame(
    c.execute(
        f'select date,symbol,series,isin,close,previous_close,traded_value from {S}.daily_prices_raw'
    ).fetchall(),
    columns=[
        'date',
        'symbol',
        'series',
        'isin',
        'close',
        'previous_close',
        'traded_value',
    ],
)
prices['date'] = pd.to_datetime(prices['date'])
actions = pd.DataFrame(
    c.execute(
        f'select ex_date,symbol,subject,face_value from {S}.corporate_actions'
    ).fetchall(),
    columns=['ex_date', 'symbol', 'subject', 'face_value'],
)
print('loaded', len(prices), time.time() - t, flush=True)
r, f = DailyReturnBuilder().build(prices, actions)
print('built', len(r), time.time() - t, flush=True)
os.makedirs('data/derived', exist_ok=True)
r.to_parquet('data/derived/daily_returns.parquet')
f.to_parquet('data/derived/return_flags.parquet')
print(f.kind.value_counts())
f['year'] = pd.to_datetime(f.date).dt.year
print(f.groupby(['year', 'kind']).size().unstack(fill_value=0).to_string())
print(r.ret.describe())
