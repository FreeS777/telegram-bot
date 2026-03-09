import time
import requests

from app.config import WIN_AGENT_URL, WIN_AGENT_TOKEN


def _headers() -> dict:
    return {
        "X-Agent-Token": WIN_AGENT_TOKEN,
    }


def check_windows_agent() -> dict:
    response = requests.get(
        f"{WIN_AGENT_URL}/health",
        headers=_headers(),
        timeout=15,
    )
    response.raise_for_status()
    return response.json()


def send_windows_action(action: str) -> dict:
    response = requests.post(
        f"{WIN_AGENT_URL}/action",
        headers=_headers(),
        json={
            "action": action,
            "timestamp": int(time.time()),
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def get_windows_screenshot() -> bytes:
    response = requests.get(
        f"{WIN_AGENT_URL}/screenshot",
        headers=_headers(),
        timeout=60,
    )
    response.raise_for_status()

    content_type = response.headers.get("content-type", "").lower()
    if "image/" not in content_type:
        body_preview = response.text[:300] if response.text else "<empty>"
        raise RuntimeError(
            f"/screenshot вернул не картинку. content-type={content_type}, body={body_preview}"
        )

    return response.content


def get_windows_camera_photo() -> bytes:
    response = requests.get(
        f"{WIN_AGENT_URL}/camera",
        headers=_headers(),
        timeout=60,
    )
    response.raise_for_status()

    content_type = response.headers.get("content-type", "").lower()
    if "image/" not in content_type:
        body_preview = response.text[:300] if response.text else "<empty>"
        raise RuntimeError(
            f"/camera вернул не картинку. content-type={content_type}, body={body_preview}"
        )

    return response.content


def open_windows_url(url: str) -> dict:
    response = requests.post(
        f"{WIN_AGENT_URL}/open-url",
        headers=_headers(),
        json={"url": url},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def unlock_windows_screen() -> dict:
    response = requests.post(
        f"{WIN_AGENT_URL}/unlock-screen",
        headers=_headers(),
        timeout=30,
    )
    response.raise_for_status()
    return response.json()