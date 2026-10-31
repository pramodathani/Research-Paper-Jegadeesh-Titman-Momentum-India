"""The study's schema in the Research Analysts' TimescaleDB."""

import io
import os

import pandas as pd
import psycopg


class TimescaleStore:
    """Creates the study's tables and upserts data frames into them.

    Every write is an upsert, so loading the same data twice changes nothing.

    Attributes:
        schema: The schema this study owns.
        connection: The open database connection.
    """

    SCHEMA = 'jegadeesh_and_titman_research_analyst'

    TABLES = (
        (
            'daily_prices_raw',
            (
                'date date NOT NULL, symbol text NOT NULL, series text NOT NULL, '
                'isin text, open double precision, high double precision, '
                'low double precision, close double precision, '
                'previous_close double precision, volume double precision, '
                'traded_value double precision, '
                'PRIMARY KEY (symbol, series, date)'
            ),
            'date',
        ),
        (
            'ubi_daily_prices',
            (
                'date date NOT NULL, symbol text NOT NULL, '
                'instrument_id text, open double precision, '
                'high double precision, low double precision, '
                'close double precision, volume double precision, '
                'price_factor double precision, '
                'PRIMARY KEY (symbol, date)'
            ),
            'date',
        ),
        (
            'corporate_actions',
            (
                'ex_date date NOT NULL, symbol text NOT NULL, '
                'series text NOT NULL, isin text, subject text NOT NULL, '
                'face_value text, '
                'PRIMARY KEY (symbol, series, subject, ex_date)'
            ),
            'ex_date',
        ),
        (
            'index_daily',
            (
                'date date NOT NULL, index_name text NOT NULL, '
                'close double precision, pe double precision, '
                'pb double precision, div_yield double precision, '
                'PRIMARY KEY (index_name, date)'
            ),
            'date',
        ),
        (
            'fno_stock_futures_daily',
            (
                'date date NOT NULL, symbol text NOT NULL, expiry date NOT NULL, '
                'close double precision, settle double precision, '
                'open_interest double precision, '
                'PRIMARY KEY (symbol, expiry, date)'
            ),
            'date',
        ),
        (
            'daily_returns',
            (
                'date date NOT NULL, symbol text NOT NULL, '
                'ret double precision, '
                'PRIMARY KEY (symbol, date)'
            ),
            'date',
        ),
        (
            'return_flags',
            (
                'date date NOT NULL, symbol text NOT NULL, '
                'kind text NOT NULL, ret_raw double precision, '
                'PRIMARY KEY (symbol, kind, date)'
            ),
            'date',
        ),
        (
            'monthly_returns',
            (
                'month date NOT NULL, symbol text NOT NULL, '
                'ret double precision, '
                'PRIMARY KEY (symbol, month)'
            ),
            'month',
        ),
        (
            'universe_membership',
            (
                'month date NOT NULL, universe text NOT NULL, '
                'symbol text NOT NULL, '
                'PRIMARY KEY (universe, symbol, month)'
            ),
            'month',
        ),
        (
            'strategy_returns_detail',
            (
                'month date NOT NULL, universe text NOT NULL, '
                'skip boolean NOT NULL, formation_months integer NOT NULL, '
                'holding_months integer NOT NULL, leg text NOT NULL, '
                'gross double precision, net double precision, '
                'turnover double precision, holding_count double precision, '
                'PRIMARY KEY (universe, skip, formation_months, '
                'holding_months, leg, month)'
            ),
            'month',
        ),
        (
            'iima_factors_monthly',
            (
                'month date NOT NULL, smb double precision, '
                'hml double precision, wml double precision, '
                'mf double precision, rf double precision, '
                'PRIMARY KEY (month)'
            ),
            'month',
        ),
    )

    def __init__(self, connection: psycopg.Connection | None = None) -> None:
        """Opens the connection from the environment unless one is given.

        Args:
            connection (psycopg.Connection | None): A connection to use, or
                None to connect with RESEARCH_ANALYST_TIMESCALEDB_URL.

        Returns:
            None.
        """
        self.schema = self.SCHEMA
        if connection is None:
            connection = psycopg.connect(
                os.environ['RESEARCH_ANALYST_TIMESCALEDB_URL'],
                autocommit=True,
            )
        self.connection = connection

    def create_tables(self) -> None:
        """Creates the schema, the tables and their hypertables.

        Returns:
            None.
        """
        self.connection.execute(f'CREATE SCHEMA IF NOT EXISTS {self.schema}')
        for name, columns, time_column in self.TABLES:
            self.connection.execute(
                f'CREATE TABLE IF NOT EXISTS {self.schema}.{name} ({columns})'
            )
            self.connection.execute(
                f"SELECT create_hypertable('{self.schema}.{name}', "
                f"by_range('{time_column}'), if_not_exists => TRUE, "
                f'migrate_data => TRUE)'
            )

    def clear(self, table: str) -> None:
        """Empties a derived table before it is rebuilt.

        Args:
            table (str): The table name in the study's schema.

        Returns:
            None.
        """
        self.connection.execute(f'TRUNCATE {self.schema}.{table}')

    def upsert(
        self,
        table: str,
        frame: pd.DataFrame,
        key_columns: list[str],
    ) -> int:
        """Upserts a data frame into a table through a temporary table.

        Args:
            table (str): The table name in the study's schema.
            frame (pd.DataFrame): The rows; column names must match the
                table's.
            key_columns (list[str]): The primary key columns.

        Returns:
            int: The number of rows sent.
        """
        if frame.empty:
            return 0
        frame = frame.drop_duplicates(subset=key_columns, keep='last')
        columns = list(frame.columns)
        column_list = ', '.join(columns)
        update_columns = [c for c in columns if c not in key_columns]
        if update_columns:
            action = 'DO UPDATE SET ' + ', '.join(
                f'{c} = EXCLUDED.{c}' for c in update_columns
            )
        else:
            action = 'DO NOTHING'
        buffer = io.StringIO()
        frame.to_csv(buffer, index=False, header=False, na_rep='\\N')
        with self.connection.transaction():
            self.connection.execute(
                f'CREATE TEMP TABLE staging ON COMMIT DROP AS '
                f'SELECT {column_list} FROM {self.schema}.{table} WITH NO DATA'
            )
            with (
                self.connection.cursor() as cursor,
                cursor.copy(
                    f'COPY staging ({column_list}) FROM STDIN '
                    f"WITH (FORMAT csv, NULL '\\N')"
                ) as copy,
            ):
                copy.write(buffer.getvalue())
            self.connection.execute(
                f'INSERT INTO {self.schema}.{table} ({column_list}) '
                f'SELECT {column_list} FROM staging '
                f'ON CONFLICT ({", ".join(key_columns)}) {action}'
            )
        return len(frame)
