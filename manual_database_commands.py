# init

import psycopg2
import pandas as pd

import os
from datetime import datetime
from utils import get_confirmation, load_config, parse_link_args


def get_unlinked_livephoto_ids(db_config: dict, user_config: dict) -> pd.DataFrame:
    """Identify unlinked Live Photo assets in Immich database.

    Args:
        live_video_suffix: File suffix pattern for video assets (e.g. '_3.mov')
        db_config: Dictionary containing PostgreSQL connection parameters

    Returns:
        DataFrame containing photo-video asset pairs needing linkage

    Raises:
        ConnectionError: If database connection fails.
    """
    unlinked_photo_assets_df = pd.DataFrame()

    # Identify all unlinked photo IDs.
    # Three step process
    # 1. Get all video filenames
    # 2. Get all photo filenames with identical *base* names as the videos.
    #   - e.g., Photo File: "IMG_1234.heic"; Video File: "IMG_1234.MOV"
    # 3. Filter out problematic photo file candidates:
    #   - Duplicated photos
    #   - Photo/Video files with identical filenames but mismatched timestamps.
    with psycopg2.connect(**db_config) as conn:
        with conn.cursor() as cur:
            # 0. Get user name
            cur.execute(
                """
                SELECT id FROM users WHERE name = %s
                """,
                (user_config["name"],),
            )

            user_id = cur.fetchone()