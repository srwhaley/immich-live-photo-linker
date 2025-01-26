"""
Immich Live Photo Linker Script

Features:
- Identifies unlinked Live Photo/Video pairs
- Interactive confirmation prompts
- Audit trail CSVs
- Dry run mode

Usage:
1. Configure API and DB settings at bottom of file
2. Run: python immich_livephotos.py

Safety:
- Back up your database before running
- Always test with dry_run=True first
"""

import json
import requests
import psycopg2
import pandas as pd

from datetime import datetime


def get_unlinked_livephoto_ids(
    live_video_suffix: str,
    db_config: dict,
) -> pd.DataFrame:
    """Identify unlinked Live Photo assets in Immich database.

    Args:
        live_video_suffix: File suffix pattern for video assets (e.g. '_3.mov')
        db_config: Dictionary containing PostgreSQL connection parameters

    Returns:
        DataFrame containing photo-video asset pairs needing linkage

    Raises:
        ConnectionError: If database connection fails.
    """
    live_video_suffix = live_video_suffix.replace(".", r"\.") + "$"
    unlinked_photo_assets_df = pd.DataFrame()

    # Identify all unlinked photo IDs.
    with psycopg2.connect(**db_config) as conn:
        with conn.cursor() as cur:
            # First, locate all live video assets
            cur.execute(f"""
                SELECT id, "originalFileName", "fileCreatedAt"
                FROM assets 
                WHERE "originalFileName" ~ '{live_video_suffix}';
            """)
            video_assets = cur.fetchall()
            video_assets_df = pd.DataFrame(
                video_assets,
                columns=["video_asset_id", "video_filename", "video_filedate"],
            )

            if video_assets_df.empty:
                print("No unlinked Live Videos identified.")
                quit()

            video_assets_df["photo_basefilename"] = video_assets_df[
                "video_filename"
            ].str.replace(live_video_suffix, "", regex=True)

            # Next, find all live photo assets that are missing livePhotoVideoId's.
            photo_basefilename = tuple(video_assets_df["photo_basefilename"].tolist())
            cur.execute(rf"""
                        SELECT id, "originalFileName", "fileCreatedAt"
                        FROM assets
                        WHERE "livePhotoVideoId" IS NULL
                        AND "originalFileName" !~ '{live_video_suffix}'
                        AND lower("originalFileName") !~ '.mov$'
                        AND lower("originalFileName") !~ '.mp4$'
                        AND regexp_replace("originalFileName", '\..*$', '') IN {photo_basefilename};
                        """)

            unlinked_photo_assets = cur.fetchall()
            unlinked_photo_assets_df = pd.DataFrame(
                unlinked_photo_assets,
                columns=["photo_asset_id", "photo_filename", "photo_filedate"],
            )

            # Finally, left join the video asset df to the unlinked photo df
            if unlinked_photo_assets_df.empty:
                print("No unlinked Live Photos identified.")
                quit()

            unlinked_photo_assets_df["photo_basefilename"] = unlinked_photo_assets_df[
                "photo_filename"
            ].str.replace(r"\..*$", "", regex=True)
            unlinked_photo_assets_df = unlinked_photo_assets_df.merge(
                video_assets_df, on="photo_basefilename", how="left", validate="1:1"
            )

            if unlinked_photo_assets_df["video_asset_id"].isna().any():
                print("Warning: Some photos could not be matched to video assets!")
                o_nfile = unlinked_photo_assets_df.shape[0]
                unlinked_photo_assets_df = unlinked_photo_assets_df.dropna(
                    subset=["video_asset_id"]
                )
                print(
                    f"Removed {o_nfile - unlinked_photo_assets_df.shape[0]} unlinked assets with missing video files."
                )

    return unlinked_photo_assets_df


def print_example_unlinked_photo(asset: pd.DataFrame, api_config: dict):
    """Prints example information for a single unlinked Live Photo.

    Args:
        asset: DataFrame containing a single asset example.
        api_config: Dictionary containing Immich API endpoint and credentials.
    """

    def get_asset_info(id):
        url = f"{api_config['url']}/api/assets/{asset[id]}"
        payload = {}
        headers = {
            "Accept": "application/json",
            "x-api-key": api_config["api_key"],
        }

        result = requests.request("GET", url=url, headers=headers, data=payload)
        return result.json()

    live_photo_info = get_asset_info("photo_asset_id")
    live_video_info = get_asset_info("video_asset_id")

    example_file_info = f"""Example Unlinked Live Photo/Video File Information:
    - Live Photo Original Filename: {live_photo_info["originalFileName"]}
    - Live Photo Creation Date: {live_photo_info["fileCreatedAt"]}
    - Live Video Original Filename: {live_video_info["originalFileName"]}
    - Live Video Creation Date: {live_video_info["fileCreatedAt"]}"""

    print(example_file_info)

    return


def link_livephoto_assets(unlinked_livephoto_df: pd.DataFrame, api_config: dict):
    """Update Immich assets through API to establish Live Photo links.

    Args:
        unlinked_livephoto_df: DataFrame containing asset pairs to link
        api_config: Dictionary containing Immich API endpoint and credentials

    Raises:
        RuntimeError: If API requests fail persistently
    """
    failed_updates = []
    successful_updates = 0
    for i, asset in unlinked_livephoto_df.iterrows():
        print(f"Merging asset: {i + 1}/{unlinked_livephoto_df.shape[0]}", end="\r")

        payload = json.dumps({"livePhotoVideoId": asset["video_asset_id"]})

        url = f"{api_config['url']}/api/assets/{asset['photo_asset_id']}"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "x-api-key": api_config["api_key"],
        }

        result = requests.request("PUT", url=url, headers=headers, data=payload)

        if result.status_code == 200:
            successful_updates += 1
        else:
            error_detail = result.json()
            error_msg = f"{error_detail.get('error', 'Unknown error')}: {error_detail.get('message', 'No message provided')}"

            failed_updates.append(
                {
                    "photo_asset_id": asset["photo_asset_id"],
                    "photo_filename": asset["photo_filename"],
                    "photo_filedate": asset["photo_filedate"],
                    "video_asset_id": asset["video_asset_id"],
                    "video_filename": asset["video_filename"],
                    "video_filedate": asset["video_filedate"],
                    "error_status": result.status_code,
                    "error_message": error_msg,
                }
            )

    print("\nUpdate Summary:")
    print(f"Successfully linked {successful_updates} files.")

    if failed_updates:
        timestamp = datetime.now().strftime("%Y_%m_%d_%H%M%S")
        out_failed_file = f"failed_updates_{timestamp}.csv"

        failed_df = pd.DataFrame(failed_updates)
        # Ensure column order
        failed_df = failed_df[
            [
                "photo_asset_id",
                "photo_filename",
                "photo_filedate",
                "video_asset_id",
                "video_filename",
                "video_filedate",
                "error_status",
                "error_message",
            ]
        ]
        failed_df.to_csv(out_failed_file, index=False)

        # Raise exception with summary
        raise RuntimeError(
            f"Failed to update {len(failed_updates)} files. See {out_failed_file} for details."
        )

    return


def validate_config(api_config: dict, db_config: dict):
    """Validate configuration with server connectivity check."""
    # Initial configuration checks
    required_api = {"api_key", "url"}
    required_db = {"host", "dbname", "user", "password", "port"}

    if missing := required_api - api_config.keys():
        raise KeyError(f"Missing API keys: {', '.join(missing)}")
    if missing := required_db - db_config.keys():
        raise KeyError(f"Missing DB keys: {', '.join(missing)}")

    # Server connectivity check
    try:
        response = requests.get(
            f"{api_config['url']}/api/server/ping",
            headers={
                "Accept": "application/json",
            },
            timeout=10,  # Prevent hanging
        )

        if response.status_code != 200:
            raise ConnectionError(f"Server returned {response.status_code}")

    except requests.exceptions.RequestException as e:
        raise ConnectionError(f"Server connection failed: {str(e)}")

    # API key check
    response = requests.get(
        f"{api_config['url']}/api/users/me",
        headers={
            "Accept": "application/json",
            "x-api-key": api_config["api_key"],
        },
        timeout=10,  # Prevent hanging
    )

    if response.status_code != 200:
        error_msg = response.json()
        print(error_msg)
        raise ConnectionError(
            f"API key validation failure: {error_msg['error']} - {error_msg['message']}"
        )


def get_confirmation(prompt: str) -> bool:
    """Get validated yes/no input from user."""
    while True:
        response = input(prompt).lower()
        if response in ("y", "yes"):
            return True
        if response in ("n", "no"):
            return False
        print("Invalid input. Please enter y/yes or n/no")


def repair_live_photos(
    live_video_suffix: str,
    immich_api_config: dict,
    immich_db_config: dict,
    dry_run: bool = False,
):
    validate_config(api_config=immich_api_config, db_config=immich_db_config)

    print("1/2: Identifying unlinked Live Photo assets...")
    unlinked_photo_assets_df = get_unlinked_livephoto_ids(
        live_video_suffix=live_video_suffix, db_config=immich_db_config
    )

    print(f"Identified {unlinked_photo_assets_df.shape[0]} unlinked Live Photos.")
    print_example_unlinked_photo(
        asset=unlinked_photo_assets_df.loc[0], api_config=immich_api_config
    )

    # Save record
    save_record = get_confirmation("Save record of assets? [y/n] ")
    if save_record:
        timestamp = datetime.now().strftime("%Y_%m_%d_%H%M%S")
        out_file = f"linked_assets_{timestamp}.csv".replace("-", "_")
        unlinked_photo_assets_df.to_csv(out_file, index=False)
        print(f"File saved to: {out_file}")

    if dry_run:
        print("Dry run of Live Photo linking completed.")
        return

    # Confirm Link
    confirm_link = get_confirmation("Would you like to link these assets? [y/n] ")
    if not confirm_link:
        print("Live Photo linking cancelled.")
        return None

    print("2/2: Linking Live Photos and Live Video assets...")
    link_livephoto_assets(
        unlinked_livephoto_df=unlinked_photo_assets_df, api_config=immich_api_config
    )

    print("Live Photos linking complete!")

    return


if __name__ == "__main__":
    # ================================================
    # ⚠️ BEFORE SHARING/COMMITTING: ⚠️
    # 1. Replace all credentials with placeholders
    # 2. Remove any personal IP addresses
    # ================================================

    # Immich API configuration info.
    api_config = {
        "api_key": "YOUR_API_KEY_HERE",
        "url": "http://YOUR_IMMICH_URL:PORT",
    }

    # The PostGres host IP can be found from the `immich_postgres` docker
    # container via (with sudo permission):
    # `sudo docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' immich_postgres`
    db_config = {
        "dbname": "immich",
        "user": "postgres",
        "password": "YOUR_POSTGRES_PASSWORD",  # found in `.env` config file.
        "host": "YOUR_POSTGRES_HOST_IP",  # see comment above to find this.
        "port": "5432",
    }

    # The file suffix that is used to link your LivePhotos.
    # The suffix is the only naming difference from the original LivePhoto
    # filename. E.g.:
    # Live Photo Filename: "1234.heic"; Live Video Filename: "1234_3.mov"
    live_video_suffix = "_3.mov"

    # ================================================
    # ⚠️ BEFORE RUNNING: ⚠️
    # 1. Ensure you have a database backup
    # 2. Run the script with `dry_run=True` for testing
    # ================================================
    repair_live_photos(
        live_video_suffix=live_video_suffix,
        immich_api_config=api_config,
        immich_db_config=db_config,
        dry_run=True,
    )
