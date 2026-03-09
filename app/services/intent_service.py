import json
import re
from urllib.parse import urlparse

from app.config import INTENT_ROUTER_PROMPT
from app.services.openai_service import ask_router_model


ACTION_NAMES = {
    "chat",
    "ping",
    "ip",
    "search",
    "server",
    "uptime",
    "disk",
    "ram",
    "top",
    "services",
    "docker",
    "nginx",
    "logs",
    "net",
    "whoami",
    "clear",
    "voice_on",
    "voice_off",
    "reboot",
    "win_status",
    "win_screenshot",
    "win_camera",
    "win_lock",
    "win_logout",
    "win_shutdown",
    "win_reboot",
    "win_unlock_screen",
    "win_open_url",
}


def resolve_user_intent(user_text: str) -> dict:
    text = user_text.strip()
    lowered = text.lower()

    rule_based = _rule_based_intent(text, lowered)
    if rule_based is not None:
        return rule_based

    prompt = f'Сообщение пользователя:\n"""\n{text}\n"""'
    raw = ask_router_model(prompt, INTENT_ROUTER_PROMPT)
    parsed = _parse_router_json(raw)

    if parsed is not None:
        return parsed

    return {
        "kind": "chat",
        "action": "chat",
        "args": {},
        "confidence": 0.0,
    }


def _rule_based_intent(text: str, lowered: str) -> dict | None:
    if any(x in lowered for x in ["включи голос", "отвечай голосом", "voice on"]):
        return _action("voice_on")

    if any(x in lowered for x in ["выключи голос", "без голоса", "voice off"]):
        return _action("voice_off")

    if any(x in lowered for x in ["очисти память", "сотри память", "clear memory"]):
        return _action("clear")

    if any(x in lowered for x in ["статус вин", "статус windows", "win status", "статус пк"]):
        return _action("win_status")

    if any(x in lowered for x in ["сделай скрин", "скриншот", "снимок экрана"]):
        return _action("win_screenshot")

    if any(x in lowered for x in ["включи камеру", "фото с камеры", "сделай фото с камеры", "вебкамера"]):
        return _action("win_camera")

    if any(x in lowered for x in ["заблокируй экран", "заблокируй пк", "lock screen"]):
        return _action("win_lock")

    if any(x in lowered for x in ["разлогинь", "выйди из windows", "logout windows"]):
        return _action("win_logout")

    if any(x in lowered for x in ["выключи компьютер", "выключи пк", "shutdown windows"]):
        return _action("win_shutdown")

    if any(x in lowered for x in ["перезагрузи компьютер", "перезагрузи пк", "reboot windows"]):
        return _action("win_reboot")

    if any(x in lowered for x in ["разблокируй экран", "unlock screen", "сними блокировку"]):
        return _action("win_unlock_screen")

    if any(x in lowered for x in ["внешний ip", "мой ip сервера", "ip сервера"]):
        return _action("ip")

    if any(x in lowered for x in ["аптайм", "uptime", "сколько сервер работает"]):
        return _action("uptime")

    if any(x in lowered for x in ["диск сервера", "место на диске", "disk"]):
        return _action("disk")

    if any(x in lowered for x in ["память сервера", "ram сервера", "оперативка сервера"]):
        return _action("ram")

    if any(x in lowered for x in ["топ процессов", "процессы сервера"]):
        return _action("top")

    if any(x in lowered for x in ["сервисы сервера", "статус сервисов"]):
        return _action("services")

    if any(x in lowered for x in ["докер", "docker containers"]):
        return _action("docker")

    if any(x in lowered for x in ["nginx", "энджинкс"]):
        return _action("nginx")

    if any(x in lowered for x in ["логи бота", "покажи логи", "logs"]):
        return _action("logs")

    if any(x in lowered for x in ["сеть сервера", "маршруты сервера", "net"]):
        return _action("net")

    if any(x in lowered for x in ["кто ты на сервере", "whoami", "какой пользователь"]):
        return _action("whoami")

    if any(x in lowered for x in ["сводка сервера", "статус сервера", "server status", "сервер полностью"]):
        return _action("server")

    if any(x in lowered for x in ["перезагрузи сервер", "reboot server", "ребутни сервер"]):
        return _action("reboot")

    # 1) открыть url: и с http(s), и без схемы
    if any(x in lowered for x in ["открой", "open", "запусти в браузере"]):
        url = _extract_or_normalize_url(text)
        if url:
            return {
                "kind": "action",
                "action": "win_open_url",
                "args": {"url": url},
                "confidence": 0.98,
            }

    # 2) если пользователь прислал просто домен, тоже считаем это URL
    maybe_url = _extract_or_normalize_url(text)
    if maybe_url and _looks_like_bare_url(text):
        return {
            "kind": "action",
            "action": "win_open_url",
            "args": {"url": maybe_url},
            "confidence": 0.95,
        }

    search_match = re.match(r"^(найди|поищи|загугли|search)\s+(.+)$", lowered, flags=re.IGNORECASE)
    if search_match:
        query = text.split(maxsplit=1)[1].strip() if len(text.split(maxsplit=1)) > 1 else ""
        if query:
            return {
                "kind": "action",
                "action": "search",
                "args": {"query": query},
                "confidence": 0.96,
            }

    return None


def _action(action_name: str) -> dict:
    return {
        "kind": "action",
        "action": action_name,
        "args": {},
        "confidence": 0.95,
    }


def _extract_or_normalize_url(text: str) -> str | None:
    text = text.strip()

    # Сначала ищем полноценный URL
    full_url_match = re.search(r"(https?://[^\s]+)", text, flags=re.IGNORECASE)
    if full_url_match:
        url = full_url_match.group(1).strip()
        parsed = urlparse(url)
        if parsed.scheme in {"http", "https"} and parsed.netloc:
            return url

    # Потом пробуем вытащить домен без схемы
    bare_domain_match = re.search(
        r"\b((?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,})(/[^\s]*)?\b",
        text,
        flags=re.IGNORECASE,
    )
    if bare_domain_match:
        domain = bare_domain_match.group(1)
        path = bare_domain_match.group(2) or ""
        return f"https://{domain}{path}"

    return None


def _looks_like_bare_url(text: str) -> bool:
    cleaned = text.strip().lower()
    cleaned = cleaned.replace("открой ", "").replace("open ", "").strip()

    if " " in cleaned:
        return False

    return bool(
        re.fullmatch(
            r"(https?://)?((?:[a-z0-9-]+\.)+[a-z]{2,})(/[^\s]*)?",
            cleaned,
            flags=re.IGNORECASE,
        )
    )


def _parse_router_json(raw: str) -> dict | None:
    candidate = raw.strip()

    if candidate.startswith("```"):
        candidate = candidate.strip("`")
        candidate = candidate.replace("json", "", 1).strip()

    match = re.search(r"\{.*\}", candidate, flags=re.DOTALL)
    if match:
        candidate = match.group(0)

    try:
        data = json.loads(candidate)
    except Exception:
        return None

    kind = data.get("kind")
    action = data.get("action")
    args = data.get("args", {})
    confidence = data.get("confidence", 0.0)

    if kind not in {"chat", "action"}:
        return None
    if action not in ACTION_NAMES:
        return None
    if not isinstance(args, dict):
        args = {}
    try:
        confidence = float(confidence)
    except Exception:
        confidence = 0.0

    return {
        "kind": kind,
        "action": action,
        "args": args,
        "confidence": confidence,
    }