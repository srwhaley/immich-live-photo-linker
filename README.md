# Immich Live Photo Linker
A utility script that uses the Immich API to fix unlinked Live Photos in Immich
by connecting HEIC/JPEG photos with their corresponding MOV/MP4 video
components.

In the event of any issues with asset linking, an unlinking script is also available.

### Contents

- [Overview](#overview)
   - [Background](#background)
   - [Script Features](#script-features)
- [Live Photo Linking Script Usage](#linking-script-usage)
    - [Requirements](#requirements)
    - [Details](#details)
    - [Installation](#installation)
    - [Configuration](#configuration)
    - [Running](#running)
- [Live Photo Unlinking Script Usage](#unlinking-script-usage)
- [Notes](#notes)

# Overview
### Background
iOS Live Photos consist of a photo (HEIC/JPEG) and video (MOV) component. When
importing Live Photos into Immich, sometimes the link between these components
can be lost. This script identifies and repairs these broken connections.

When I first imported my 30k iOS images into Immich using the Immich CLI, 10% of
my Live Photos were randomly not linked to their video counterparts.

One can link Live Photos/Videos one-by-one in the Immich web app, but this is
overwhelming when thousands of images need linked. Thus, I created this script
to automate the process.

### Script Features
- Identifies unlinked Live Photo/Video pairs
- Interactive confirmation prompts
- Validation of database connection, server connection, and server credentials
- Creates audit trail CSVs
- Dry run mode for testing

# Linking Script Usage
***WARNING:*** Ensure you have a backup of your Immich database.

## Requirements
- Python 3.9+
- Immich API key
- Immich Postgres Database access
- Script package dependencies (`requirements.txt`)

## Details
This script is meant to connect Live Video files to their Live Photo file
counterparts. Your Live Video filenames should share the same prefix as the
Live Photo filenames. Example:

- Live Photo Filename: `1234.heic`
- Live Video Filename: `1234_3.mov`

### Example Script Run
```bash
jacob@server:~/immich_scripts$ python link_livephoto_videos.py 
1/2: Identifying unlinked Live Photo assets...
Identified 1753 unlinked Live Photos.
Example Unlinked Live Photo/Video File Information:
    - Live Photo Original Filename: 2DE2659F-F48E-4396-91E3-A4C302231853.heic
    - Live Photo Creation Date: 2022-06-03T21:02:35.193Z
    - Live Video Original Filename: 2DE2659F-F48E-4396-91E3-A4C302231853_3.mov
    - Live Video Creation Date: 2022-06-03T21:02:34.000Z
Record of identified Live Photo/Video assets saved to: linked_assets_2025_01_26_044630.csv
Would you like to link these assets? [y/n] y
2/2: Linking Live Photos and Live Video assets...
Merging asset: 1753/1753
Update Summary:
Successfully linked 1753 files.
Live Photos linking complete!
```

## Installation
1. Clone this repository
2. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration
Edit the following variables in the bottom of the script:

```python
api_config = {
    "api_key": "YOUR_API_KEY_HERE",
    "url": "http://YOUR_IMMICH_URL:PORT"
}

db_config = {
    "dbname": "immich",
    "user": "postgres",
    "password": "YOUR_POSTGRES_PASSWORD",  # see your immich .env file
    "host": "YOUR_POSTGRES_HOST_IP",  # see the instructions in the script/below to find this
    "port": "5432"
}

live_video_suffix = "_3.mov"  # Adjust based on your Live Photo naming pattern
```

## Running
1. ***WARNING:*** Ensure you have a backup of your Immich database.
2. Test the script in dry-run mode (set `dry_run=True` in the script):
   ```bash
   python link_livephoto_videos.py
   ```
3. Once you're ready to link the files, set `dry_run=False` and run again

# Unliking Script Usage
In the event that some major issue occurred with the linking script, an unlinking script is 
also available.

## Running
1. Ensure you have a backup of your Immich postgres database
2. Configure the script as you did with the linking script, ensuring you have added the correct `.csv` path.
3. Test the script in dry-run mode (`dry_run=True`)\
   ```bash
   python unlink_livephoto_videos.py
   ```
5. Once you've confirmed the process is ready, run the linking script with `dry_run=False`. 

# Notes
- This script is specifically designed for iOS Live Photos
- The default video suffix pattern is "_3.mov"
- Always backup your database before running
- Test with `dry_run=True` first
