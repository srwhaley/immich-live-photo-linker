# Immich Live Photo Linker
A utility script that uses the Immich API to fix unlinked Live Photos in Immich
by connecting HEIC/JPEG photos with their corresponding MOV/MP4 video
components.

In the event of any issues with asset linking, an unlinking script is also
provided.

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

One can link Live Photos/Videos one-by-one in the Immich web app, but this is
overwhelming when thousands of images need linked. Thus, I created this script
to automate the process.

For background, I first imported my 30k iOS images into Immich using the Immich
CLI, 10% of my Live Photos were randomly not linked to their video counterparts.
This script was a life saver for repairing my library.

### Script Features
- Identifies unlinked Live Photo/Video pairs
- Interactive confirmation prompts
- Validation of database connection, server connection, and server credentials
- Creates audit trail CSVs
- Dry run and test run modes
- Command line interface

# Linking Script Usage
***WARNING:*** Ensure you have a backup of your Immich database.

## Requirements
- Python 3.9+
- Immich API key
- Immich Postgres Database access
    - See instructions in `config.yaml` for finding this IP
- Script package dependencies (`requirements.txt`)

### Example Script Run
```bash
# Dry run to test configuration and see what would be linked
python link_livephoto_videos.py --dry-run

# Test run to process a single asset
python link_livephoto_videos.py --test-run

# Full run to process all unlinked assets
python link_livephoto_videos.py
```

Example output:
```bash
jacob@server:~/immich_scripts$ python link_livephoto_videos.py 
1/2: Identifying unlinked Live Photo assets...
Identified 1753 unlinked Live Photos.
Example Unlinked Live Photo/Video File Information:
    - Live Photo Original Filename: 2DE2659F-F48E-4396-91E3-A4C302231853.heic
    - Live Photo Creation Date: 2022-06-03T21:02:35.193Z
    - Live Video Original Filename: 2DE2659F-F48E-4396-91E3-A4C302231853_3.mov
    - Live Video Creation Date: 2022-06-03T21:02:34.000Z
Would you like to link these assets? [y/n] y

2/2: Linking Live Photos and Live Video assets...
Record of identified Live Photo/Video assets saved to: linked_assets_2025_01_26_044630.csv
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
Update the cloned `config.yaml` file with your Immich API and database settings.

Otherwise, create your own config file and copy the content structure from the
`config.yaml` file in this repo.

To identify the Immich Postgres database IP, you can run:

```
sudo docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' immich_postgres
```

## Running
1. ***WARNING:*** Ensure you have a backup of your Immich database.
2. Test the script in dry-run mode:
   ```bash
   python link_livephoto_videos.py --dry-run
   ```
3. Test with a single asset:
   ```bash
   python link_livephoto_videos.py --test-run
   ```
4. Once you're ready to link all files:
   ```bash
   python link_livephoto_videos.py
   ```

# Unlinking Script Usage
In the event that some major issue occurred with the linking script, an
unlinking script is also available.

## Running
1. Ensure you have a backup of your Immich postgres database
2. Configure the script using the same `config.yaml` file as the linking script
3. Test the script in dry-run mode:
   ```bash
   python unlink_livephoto_videos.py --linked-csv "path/to/linked_assets_audit.csv" --dry-run
   ```
4. Once you've confirmed the process is ready:
   ```bash
   python unlink_livephoto_videos.py --linked-csv "path/to/linked_assets_audit.csv"
   ```

# Notes
- This script was designed and tested for iOS Live Photos.
- Always backup your database before running.
- Test with `--dry-run` first, then `--test-run` before running the full
  process.
- Use `--config` flag to specify a different config file location if needed.
