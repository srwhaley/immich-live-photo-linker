"""Utility functions for the Immich Live Photo Linker/Unlinker scripts."""

import requests
import argparse
import yaml
from pathlib import Path


def get_confirmation(prompt: str) -> bool:
    """Get validated yes/no input from user."""
    while True:
        response = input(prompt).lower()
        if response in ("y", "yes"):
            return True
        if response in ("n", "no"):
            return False
        print("Invalid input. Please enter y/yes or n/no")


def validate_config(config: dict):
    """Validate configuration with server connectivity check."""

    # Check if all three required sections exist
    required_sections = {"api", "database", "user-info"}
    if missing_sections := required_sections - set(config.keys()):
        raise KeyError(
            f"Configuration must contain {', '.join(required_sections)} sections. Missing: {', '.join(missing_sections)}"
        )

    api_config = config["api"]
    db_config = config["database"]
    user_config = config["user-info"]

    # Required configuration keys
    required_api_keys = {"api-key", "url"}
    required_db_keys = {"host", "dbname", "user", "password", "port"}
    required_user_keys = {"name"}

    # Validate API configuration
    if missing := required_api_keys - set(api_config.keys()):
        raise KeyError(f"Missing required API configuration keys: {', '.join(missing)}")

    # Validate database configuration
    if missing := required_db_keys - set(db_config.keys()):
        raise KeyError(
            f"Missing required database configuration keys: {', '.join(missing)}"
        )

    # Validate user_info configuration
    if missing := required_user_keys - set(user_config.keys()):
        raise KeyError(
            f"Missing required user_info configuration keys: {', '.join(missing)}"
        )

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
            "x-api-key": api_config["api-key"],
        },
        timeout=10,  # Prevent hanging
    )

    if response.status_code != 200:
        error_msg = response.json()
        raise ConnectionError(
            f"API key validation failure: {error_msg['error']} - {error_msg['message']}"
        )

    return


def parse_link_args() -> argparse.Namespace:
    """Parse command line arguments for Immich Live Photo Linker.

    Returns:
        argparse.Namespace: Parsed command line arguments containing:
            - dry_run (bool): Whether to perform a dry run
            - test_run (bool): Whether to process only one asset
            - config (str): Path to configuration file
    """
    parser = argparse.ArgumentParser(
        description="Link Live Photo/Video pairs in Immich media server"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform a dry run without making changes",
    )
    parser.add_argument(
        "--test-run", action="store_true", help="Process only one asset as a test"
    )
    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)",
    )

    return parser.parse_args()


def parse_unlink_args() -> argparse.Namespace:
    """Parse command line arguments for Immich Live Photo Unlinker.

    Returns:
        argparse.Namespace: Parsed command line arguments containing:
            - dry_run (bool): Whether to perform a dry run
            - config (str): Path to configuration file
            - linked_csv (str): Path to CSV file containing linked assets
    """
    parser = argparse.ArgumentParser(
        description="Unlink previously linked Live Photo/Video pairs in Immich media server"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform a dry run without making changes",
    )
    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)",
    )
    parser.add_argument(
        "--linked-csv",
        required=True,
        help="Path to CSV file containing linked assets to unlink",
    )

    return parser.parse_args()


def load_config(config_path: str) -> dict:
    """Load and validate configuration from YAML file.

    Args:
        config_path: Path to YAML configuration file

    Returns:
        Dictionary containing validated API and database configurations

    Raises:
        FileNotFoundError: If config file doesn't exist
        KeyError: If required configuration keys are missing
        yaml.YAMLError: If config file is not valid YAML
    """
    # Check if config file exists
    if not Path(config_path).is_file():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    # Load and parse config file
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    # Validate config structure
    validate_config(config)

    return config
