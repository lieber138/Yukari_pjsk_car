"""Configuration helpers for the PJSK car bot services."""

from __future__ import annotations

import copy
import json
import os
from pathlib import Path
from typing import Any

DEFAULT_CONFIG: dict[str, Any] = {
    "server": {
        "host": "0.0.0.0",
        "port": 8765,
    },
    "bridge": {
        "napcat_ws_url": "ws://localhost:3001",
        "server_ws_url": "ws://localhost:8765",
        "reconnect_initial_delay": 1,
        "reconnect_max_delay": 30,
        "car_response_timeout": 30,
    },
    "runner": {
        "start_bridge": False,
        "startup_delay": 2,
        "health_check_interval": 2,
        "shutdown_timeout": 5,
    },
}


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Merge nested dictionaries without mutating either input."""
    merged = copy.deepcopy(base)

    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value

    return merged


def load_config(path: str | os.PathLike[str] | None = None) -> dict[str, Any]:
    """Load config.json and fill missing keys with safe defaults.

    The path can be overridden with the BOT_CONFIG_PATH environment variable.
    If config.json does not exist yet, defaults are returned so fresh checkouts can
    still start with the historical local development values.
    """
    config_path = Path(path or os.getenv("BOT_CONFIG_PATH", "config.json"))

    if not config_path.exists():
        return copy.deepcopy(DEFAULT_CONFIG)

    with config_path.open("r", encoding="utf-8") as file:
        user_config = json.load(file)

    if not isinstance(user_config, dict):
        raise ValueError(f"配置文件 {config_path} 的顶层必须是 JSON 对象")

    return _deep_merge(DEFAULT_CONFIG, user_config)
