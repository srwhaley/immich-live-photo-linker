# Immich Live Photo Linker
A utility script that uses the Immich API to fix unlinked Live Photos in Immich
by connecting HEIC/JPEG photos with their corresponding MOV/MP4 video
components.

### Background
iOS Live Photos consist of a photo (HEIC/JPEG) and video (MOV) component. When
importing these into Immich, sometimes the link between these components can be
lost. This script identifies and repairs these broken connections.

For example, when I first imported my 30k images into Immich, ~2k LivePhotos
were randomly not linked. Thus, I created this script to automate the process.

### Features
- Identifies unlinked Live Photo/Video pairs
- Interactive confirmation prompts
- Validation of database connection, server connection, and server credentials
- Creates audit trail CSVs
- Dry run mode for testing

# Usage
***WARNING:*** Ensure you have a backup of your Immich database.

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

See the Immich API key generation instructions [here](https://immich.app/docs/features/command-line-interface#obtain-the-api-key).

Identify your `immich_postgres` container IP via (on the same machine as your Immich server):

```bash
sudo docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' immich_postgres
```

## Running
1. ***WARNING:*** Ensure you have a backup of your Immich database.
2. Test the script in dry-run mode:
   ```bash
   python link_livephoto_videos.py
   ```
3. Once you're ready to link the files, set dry_run=False and run again

# Notes
- This script is specifically designed for iOS Live Photos
- The default video suffix pattern is "_3.mov"
- Always backup your database before running
- Test with dry_run=True first
