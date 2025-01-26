"""
Immich Live Photo Unlinker Script

Unlinks previously linked Live Photos using the audit CSV from the
`link_livephoto_videos.py` script.
"""

import json
import requests
import pandas as pd
from datetime import datetime


def unlink_livephoto_assets(linked_assets_df: pd.DataFrame, api_config: dict):
    """Remove Live Photo links through Immich API.

    Args:
        linked_assets_df: DataFrame containing previously linked assets
        api_config: Dictionary containing Immich API endpoint and credentials
    """
    failed_updates = []
    successful_updates = 0

    for i, asset in linked_assets_df.iterrows():
        print(f"Unlinking asset: {i + 1}/{linked_assets_df.shape[0]}", end="\r")

        payload = json.dumps({"livePhotoVideoId": None})

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
                    "error_status": result.status_code,
                    "error_message": error_msg,
                }
            )

    print("\nUnlink Summary:")
    print(f"Successfully unlinked {successful_updates} files.")

    if failed_updates:
        timestamp = datetime.now().strftime("%Y_%m_%d_%H%M%S")
        out_failed_file = f"failed_unlinks_{timestamp}.csv"

        failed_df = pd.DataFrame(failed_updates)
        failed_df.to_csv(out_failed_file, index=False)
        raise RuntimeError(
            f"Failed to unlink {len(failed_updates)} files. See {out_failed_file} for details."
        )

    return


def get_confirmation(prompt: str) -> bool:
    """Get validated yes/no input from user."""
    while True:
        response = input(prompt).lower()
        if response in ("y", "yes"):
            return True
        if response in ("n", "no"):
            return False
        print("Invalid input. Please enter y/yes or n/no")


def unlink_from_csv(csv_path: str, api_config: dict, dry_run: bool = False):
    """Main function to unlink Live Photos from audit CSV.

    Args:
        csv_path: Path to the audit CSV from linking script
        api_config: Dictionary containing Immich API endpoint and credentials
        dry_run: If True, only show what would be unlinked
    """
    # Load and validate CSV
    try:
        linked_assets_df = pd.read_csv(csv_path)
    except FileNotFoundError:
        raise FileNotFoundError(f"Could not find CSV file: {csv_path}")

    # Check required columns
    required_columns = ["photo_asset_id", "photo_filename"]
    missing_columns = set(required_columns) - set(linked_assets_df.columns)
    if missing_columns:
        raise ValueError(f"CSV missing required columns: {', '.join(missing_columns)}")

    # Check if DataFrame is empty
    if linked_assets_df.empty:
        print("No linked assets found in CSV file.")
        return

    print(f"Found {linked_assets_df.shape[0]} linked Live Photos to unlink.")

    if dry_run:
        print("Dry run complete - no files were unlinked.")
        return

    confirm_unlink = get_confirmation("Would you like to unlink these assets? [y/n] ")
    if not confirm_unlink:
        print("Unlinking cancelled.")
        return

    unlink_livephoto_assets(linked_assets_df, api_config)
    print("Live Photos unlinking complete!")

    return


if __name__ == "__main__":
    # ================================================
    # ⚠️ BEFORE SHARING/COMMITTING: ⚠️
    # 1. Replace all credentials with placeholders
    # 2. Remove any personal IP addresses
    # ================================================
    api_config = {
        "api_key": "YOUR_API_KEY_HERE",
        "url": "http://YOUR_IMMICH_URL:PORT",
    }

    csv_path = "AUDIT_LINKED_ASSETS_FILE.csv"  # Update with your CSV path

    # ================================================
    # ⚠️ BEFORE RUNNING: ⚠️
    # 1. Ensure you have a database backup
    # 2. Run the script with `dry_run=True` for testing
    # ================================================
    unlink_from_csv(
        csv_path=csv_path,
        api_config=api_config,
        dry_run=False,  # Set to False to actually unlink
    )
