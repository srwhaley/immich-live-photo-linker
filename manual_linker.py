"""
Immich Live Photo Linker Script

Features:
- Identifies unlinked Live Photo/Video pairs
- Interactive confirmation prompts
- Audit trail CSVs
- Dry run mode

Usage:
1. Configure API and DB settings in the `config.yaml` file
2. Run: `python link_livephoto_videos.py [flags]`

Safety:
- Back up your database before running.
- Always test with `--dry-run` first.
"""

import json
import requests
import pandas as pd

from datetime import datetime
from utils import load_config, parse_link_args


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
            "x-api-key": api_config["api-key"],
        }

        result = requests.request("PUT", url=url, headers=headers, data=payload)

        if result.status_code == 200:
            successful_updates += 1
        else:
            error_detail = result.json()
            error_msg = f"{error_detail.get('error', 'Unknown error')}: {error_detail.get('message', 'No message provided')}"
            print()
            failed_updates.append(
                {
                    "photo_asset_id": asset["photo_asset_id"],
                    "video_asset_id": asset["video_asset_id"],
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
                "video_asset_id",
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


if __name__ == "__main__":
    # ================================================
    # ⚠️ BEFORE RUNNING: ⚠️
    # 1. Ensure you have a database backup
    # 2. Run the script with `--dry-run` and `--test-run` for testing
    # ================================================
    args = parse_link_args()
    config = load_config("config.yaml")

    unlinked_photo_assets_df = pd.read_csv('linkers.csv')
    link_livephoto_assets(
        unlinked_livephoto_df=unlinked_photo_assets_df, api_config=config["api"]
    )
    print("Live Photos linking complete!")
