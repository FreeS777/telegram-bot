import time
import logging
import requests

from app.config import WIN_AGENT_URL, WIN_AGENT_TOKEN

logger = logging.getLogger(__name__)

TIMEOUT = 10


def _ensure_config() -> None:
    if not WIN_AGENT_URL or not WIN_AGENT_TOKEN:
        raise RuntimeError("Windows agent config is missing")


def _headers() -> dict:
    return {
        "X-Agent-Token": WIN_AGENT_TOKEN,
        "Content-Type": "application/json",
    }


def check_windows_agent() -> dict:
    _ensure_config()

    response = requests.get(
        f"{WIN_AGENT_URL}/health",
        headers=_headers(),
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


def send_windows_action(action: str) -> dict:
    _ensure_config()

    response = requests.post(
        f"{WIN_AGENT_URL}/action",
        headers=_headers(),
        json={
            "action": action,
            "timestamp": int(time.time()),
        },
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    return response.json()

def get_windows_screenshot() -> bytes:
    _ensure_config()

    response = requests.get(
        f"{WIN_AGENT_URL}/screenshot",
        headers=_headers(),
        timeout=20,
    )

    response.raise_for_status()
    return response.content

def open_windows_url(url: str):

    _ensure_config()

    response = requests.post(
        f"{WIN_AGENT_URL}/open_url",
        headers=_headers(),
        json={
            "action": url,
            "timestamp": int(time.time()),
        },
        timeout=10,
    )

    response.raise_for_status()

def unlock_windows_screen() -> dict:
    _ensure_config()

    response = requests.post(
        f"{WIN_AGENT_URL}/unlock_screen",
        headers=_headers(),
        timeout=10,
    )

    response.raise_for_status()
    return response.json()
