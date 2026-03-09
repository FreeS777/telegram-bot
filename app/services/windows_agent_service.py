import io
import os
import time

import requests


WIN_AGENT_URL = os.getenv("WIN_AGENT_URL", "").rstrip("/")
WIN_AGENT_TOKEN = os.getenv("WIN_AGENT_TOKEN", "")
REQUEST_TIMEOUT = int(os.getenv("WIN_AGENT_TIMEOUT", "25"))


def _ensure_agent_config() -> None:
    if not WIN_AGENT_URL:
        raise RuntimeError("WIN_AGENT_URL is missing in environment")
    if not WIN_AGENT_TOKEN:
        raise RuntimeError("WIN_AGENT_TOKEN is missing in environment")


def _headers() -> dict:
    _ensure_agent_config()
    return {
        "X-Agent-Token": WIN_AGENT_TOKEN,
    }


def check_windows_agent() -> dict:
    response = requests.get(
        f"{WIN_AGENT_URL}/health",
        headers=_headers(),
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


def send_windows_action(action: str) -> dict:
    payload = {
        "action": action,
        "timestamp": int(time.time()),
    }

    response = requests.post(
        f"{WIN_AGENT_URL}/action",
        json=payload,
        headers=_headers(),
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


def get_windows_screenshot():
    response = requests.get(
        f"{WIN_AGENT_URL}/screenshot",
        headers=_headers(),
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()

    image = io.BytesIO(response.content)
    image.name = "windows_screenshot.png"
    image.seek(0)
    return image


def get_windows_camera_photo():
    response = requests.get(
        f"{WIN_AGENT_URL}/camera",
        headers=_headers(),
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()

    image = io.BytesIO(response.content)
    image.name = "windows_camera.jpg"
    image.seek(0)
    return image


def open_windows_url(url: str) -> dict:
    payload = {
        "action": url,
        "timestamp": int(time.time()),
    }

    response = requests.post(
        f"{WIN_AGENT_URL}/open_url",
        json=payload,
        headers=_headers(),
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


def unlock_windows_screen() -> dict:
    response = requests.post(
        f"{WIN_AGENT_URL}/unlock_screen",
        headers=_headers(),
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()