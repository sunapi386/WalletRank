# Resolves the address to stake key

import pandas as pd
from sqlalchemy import create_engine, text

CONFIG_PSQL_PATH = 'postgresql+psycopg2://cardano:qwe123@mini.ds:5432/dbsync'
psql_engine = create_engine(CONFIG_PSQL_PATH)

with psql_engine.connect() as conn:
   with conn.execution_options(yield_per=100).execute(text("select * from sender_reciver_amount_id")) as result:
      for partition in result.partitions():
         # partition is an iterable that will be at most 100 items
         for row in partition:
            print(f"{row}")
            break
         break
