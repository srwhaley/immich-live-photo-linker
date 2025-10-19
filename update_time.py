import psycopg2
import pandas as pd
from utils import load_config
from datetime import datetime
import json
import requests
import pytz
tz = pytz.timezone('US/Central')

config = load_config("config.yaml")
api_config = config["api"]
db_config = config["database"]

#   - Photo/Video files with identical filenames but mismatched timestamps.
with psycopg2.connect(**db_config) as conn:
    with conn.cursor() as cur:
        # 0. get ids in album
        query = """SELECT "assetsId" FROM album_asset WHERE "albumsId" = '143d2730-a291-4a77-8c75-dbb43882b485'"""
        cur.execute(query)
        ids = tuple([i[0] for i in cur.fetchall()])

        query = r"""
            SELECT id, "originalFileName", "localDateTime" 
            FROM asset
            WHERE id in %s AND
            "originalFileName" ~ '20[0-9]+-[0-9]+-[0-9]+.*'
        """
        cur.execute(query, (ids,))

        df = pd.DataFrame(cur.fetchall(), columns=['id', 'filename', 'datetime'])

df['newtime'] =  ''
for i, row in df.iterrows():
    form = '%Y-%m-%d_%H-%M-%S'
    newt = tz.localize(datetime.strptime(row['filename'][:19], form)).isoformat()
    df.at[i, 'newtime'] = newt

print('here')

failed_updates = []
successful_updates = 0
for i, asset in df.iterrows():
    print(f"Updating asset: {i + 1}/{df.shape[0]}", end="\r")

    payload = json.dumps({"dateTimeOriginal": asset["newtime"]})

    url = f"{api_config['url']}/api/assets/{asset['id']}"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "x-api-key": api_config["api-key"],
    }

    result = requests.request("PUT", url=url, headers=headers, data=payload)

    if result.status_code == 200:
        successful_updates += 1
    else:
        error_detail = result.json()
        error_msg = f"{error_detail.get('error', 'Unknown error')}: {error_detail.get('message', 'No message provided')}"
        print()
        failed_updates.append(asset)

print(failed_updates)