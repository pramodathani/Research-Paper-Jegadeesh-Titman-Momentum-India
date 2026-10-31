# timescale_store.py

- Uploads use COPY into a temporary table and then INSERT ... ON CONFLICT, because to_sql cannot update rows. This makes every load safe to run twice.
- UBI instrument ids are UUIDs, so instrument_id is text, not a number.
