import json
import os

CONFIG_FILE = "config.json"
DEFAULT_CONFIG = {"daily_limit": 50, "delay_seconds": 30}


def load_config() -> dict:
    if not os.path.exists(CONFIG_FILE):
        return dict(DEFAULT_CONFIG)
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return dict(DEFAULT_CONFIG)


def save_config(config: dict) -> None:
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def validate_config(config: dict) -> tuple:
    daily_limit = config.get("daily_limit")
    delay_seconds = config.get("delay_seconds")
    if daily_limit is not None:
        try:
            daily_limit = int(daily_limit)
        except (ValueError, TypeError):
            return False, "daily_limit must be a number"
        if not 1 <= daily_limit <= 500:
            return False, "daily_limit must be between 1 and 500"
    if delay_seconds is not None:
        try:
            delay_seconds = int(delay_seconds)
        except (ValueError, TypeError):
            return False, "delay_seconds must be a number"
        if not 10 <= delay_seconds <= 300:
            return False, "delay_seconds must be between 10 and 300"
    return True, None
