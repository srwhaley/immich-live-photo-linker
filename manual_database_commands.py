# init

import psycopg2
import pandas as pd
from utils import load_config

#   - Photo/Video files with identical filenames but mismatched timestamps.
with psycopg2.connect(**load_config("config.yaml")["database"]) as conn:
    with conn.cursor() as cur:
        # 0. Get user name
        cur.execute(
            """
            delete from system_metadata where key like 'memories-state'; truncate table memory cascade
            """
        )

        # user_id = cur.fetchone()