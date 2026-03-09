import platform
import random
import re
from urllib.parse import quote_plus

import requests

from app.services.memory_service import (
    clear_memory,
    clear_pending_action,
    get_pending_action,
    set_pending_action,
    set_voice_mode,
)
from app.services.system_service import run_command
from app.services.windows_agent_service import (
    check_windows_agent,
    get_windows_camera_photo,
    get_windows_screenshot,
    open_windows_url,
    send_windows_action,
    unlock_windows_screen,
)
from app.utils.text_utils import truncate


DANGEROUS_ACTIONS = {
    "reboot",
    "win_lock",
    "win_logout",
    "win_shutdown",
    "win_reboot",
    "win_unlock_screen",
}

ACTION_TITLES = {
    "reboot": "перезагрузка Linux-сервера",
    "win_lock": "блокировка Windows",
    "win_logout": "выход из Windows",
    "win_shutdown": "выключение Windows ПК",
    "win_reboot": "перезагрузка Windows ПК",
    "win_unlock_screen": "снятие блокировки экрана Windows",
}

LINUX_ONLY_ACTIONS = {
    "ip",
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
    "reboot",
}


def is_linux_runtime() -> bool:
    return platform.system().lower() == "linux"


def ensure_linux_runtime(action_name: str) -> dict | None:
    if action_name not in LINUX_ONLY_ACTIONS:
        return None

    if is_linux_runtime():
        return None

    return {
        "type": "text",
        "text": (
            "Эта команда рассчитана на Linux/VPS и локально на Windows работать не будет.\n\n"
            f"Сейчас бот запущен на: {platform.system()}\n"
            "Проверь её уже на VPS после деплоя."
        ),
    }


def is_confirmation_required(action_name: str) -> bool:
    return action_name in DANGEROUS_ACTIONS


def request_action_confirmation(action_name: str, args: dict | None = None) -> str:
    code = str(random.randint(1000, 9999))
    set_pending_action(action_name, args or {}, code)

    title = ACTION_TITLES.get(action_name, action_name)
    return (
        f"⚠️ Нужна подтверждалка.\n\n"
        f"Действие: {title}\n"
        f"Код подтверждения: {code}\n\n"
        f"Напиши:\n"
        f"- {code}\n"
        f"- или /confirm {code}\n"
        f"- или просто 'да'\n\n"
        f"Для отмены: /cancel_action или 'нет'"
    )


def cancel_pending_action_text() -> str:
    pending = get_pending_action()
    if not pending:
        return "Сейчас нет ожидающего опасного действия."
    clear_pending_action()
    return "Окей, опасное действие отменено."


def _normalize_confirmation_text(text: str) -> str:
    text = text.strip().lower()
    text = text.replace("ё", "е")
    text = re.sub(r"[\"'`.,!?;:()\[\]{}\-]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def try_handle_confirmation_text(user_text: str) -> dict | None:
    pending = get_pending_action()
    if not pending:
        return None

    raw_text = user_text.strip()
    normalized = _normalize_confirmation_text(user_text)
    code = str(pending.get("code", "")).strip()

    negative_values = {
        "нет",
        "не",
        "отмена",
        "cancel",
        "no",
        "не надо",
        "не подтверждаю",
    }

    positive_values = {
        "да",
        "ага",
        "подтверждаю",
        "подтвердить",
        "ok",
        "okay",
        "yes",
        "да подтверждаю",
        "подтверждаю да",
    }

    if normalized in negative_values:
        clear_pending_action()
        return {"type": "text", "text": "Окей, отменяю опасное действие."}

    if normalized in positive_values or raw_text == code or normalized == code:
        clear_pending_action()
        return execute_action(
            pending.get("action_name", ""),
            pending.get("args", {}),
        )

    return {
        "type": "text",
        "text": (
            f"Жду подтверждение. Напиши код {code}, "
            f"или просто 'да', или 'нет' для отмены."
        ),
    }


def confirm_pending_action_by_code(code: str) -> dict:
    pending = get_pending_action()
    if not pending:
        return {"type": "text", "text": "Сейчас нет ожидающего подтверждения."}

    expected = str(pending.get("code", "")).strip()
    if code.strip() != expected:
        return {"type": "text", "text": "Код не совпал. Ничего не выполнила."}

    clear_pending_action()
    return execute_action(
        pending.get("action_name", ""),
        pending.get("args", {}),
    )


def execute_action(action_name: str, args: dict | None = None) -> dict:
    args = args or {}

    linux_guard = ensure_linux_runtime(action_name)
    if linux_guard is not None:
        return linux_guard

    if action_name == "ping":
        return {"type": "text", "text": "Я живая. Сервер не уснул 😏"}

    if action_name == "clear":
        clear_memory()
        return {"type": "text", "text": "Память диалога очищена."}

    if action_name == "voice_on":
        set_voice_mode(True)
        return {"type": "text", "text": "Голосовые ответы включены."}

    if action_name == "voice_off":
        set_voice_mode(False)
        return {"type": "text", "text": "Голосовые ответы выключены."}

    if action_name == "ip":
        try:
            response = requests.get("https://api.ipify.org", timeout=10)
            response.raise_for_status()
            return {"type": "text", "text": f"Внешний IP сервера: {response.text.strip()}"}
        except Exception as e:
            return {"type": "text", "text": f"Не смогла получить IP: {e}"}

    if action_name == "search":
        query = str(args.get("query", "")).strip()
        if not query:
            return {"type": "text", "text": "Не вижу поискового запроса. Пример: найди react router dom"}
        url = f"https://www.google.com/search?q={quote_plus(query)}"
        return {"type": "text", "text": url}

    if action_name == "uptime":
        return {"type": "text", "text": f"Uptime: {run_command('uptime -p')}"}

    if action_name == "disk":
        output = truncate(run_command("df -h /"))
        return {"type": "text", "text": f"Диск /\n\n{output}"}

    if action_name == "ram":
        output = truncate(run_command("free -h"))
        return {"type": "text", "text": f"Память\n\n{output}"}

    if action_name == "top":
        output = truncate(run_command("ps -eo pid,ppid,cmd,%mem,%cpu --sort=-%cpu | head -n 12"))
        return {"type": "text", "text": f"Топ процессов по CPU\n\n{output}"}

    if action_name == "services":
        bot_status = run_command("systemctl is-active telegram-bot")
        nginx_status = run_command("systemctl is-active nginx")
        docker_status = run_command("systemctl is-active docker")
        text = (
            "Статус сервисов\n\n"
            f"telegram-bot: {bot_status}\n"
            f"nginx: {nginx_status}\n"
            f"docker: {docker_status}"
        )
        return {"type": "text", "text": text}

    if action_name == "docker":
        output = truncate(run_command("docker ps --format 'table {{.Names}}\\t{{.Image}}\\t{{.Status}}'"))
        return {"type": "text", "text": f"Docker containers\n\n{output}"}

    if action_name == "nginx":
        output = truncate(run_command("systemctl status nginx --no-pager -l", timeout=20))
        return {"type": "text", "text": f"Nginx status\n\n{output}"}

    if action_name == "logs":
        output = truncate(run_command("journalctl -u telegram-bot -n 30 --no-pager", timeout=20))
        return {"type": "text", "text": f"Последние логи telegram-bot\n\n{output}"}

    if action_name == "net":
        ip_brief = truncate(run_command("ip -br a"))
        routes = truncate(run_command("ip route"))
        external_ip = "не удалось получить"
        try:
            response = requests.get("https://api.ipify.org", timeout=10)
            response.raise_for_status()
            external_ip = response.text.strip()
        except Exception:
            pass

        text = (
            "Сеть сервера\n\n"
            f"Внешний IP:\n{external_ip}\n\n"
            f"Интерфейсы:\n{ip_brief}\n\n"
            f"Маршруты:\n{routes}"
        )
        return {"type": "text", "text": text}

    if action_name == "whoami":
        user = run_command("whoami")
        hostname = run_command("hostname")
        pwd = run_command("pwd")
        text = (
            "Кто я на сервере\n\n"
            f"Пользователь: {user}\n"
            f"Хост: {hostname}\n"
            f"Текущая директория: {pwd}"
        )
        return {"type": "text", "text": text}

    if action_name == "server":
        hostname = run_command("hostname")
        uptime = run_command("uptime -p")
        loadavg = run_command("cat /proc/loadavg")
        mem = truncate(run_command("free -h"))
        disk = truncate(run_command("df -h /"))
        text = (
            f"Сервер: {hostname}\n\n"
            f"Uptime:\n{uptime}\n\n"
            f"Load Average:\n{loadavg}\n\n"
            f"RAM:\n{mem}\n\n"
            f"Disk /:\n{disk}"
        )
        return {"type": "text", "text": text}

    if action_name == "reboot":
        result = run_command("sudo shutdown -r +1 'Reboot requested from Telegram bot'")
        text = (
            "Перезагрузка Linux сервера запланирована через 1 минуту.\n"
            "Если передумаешь — дай знать, и добавим отдельную отмену.\n\n"
            f"{result}"
        )
        return {"type": "text", "text": text}

    if action_name == "win_status":
        try:
            data = check_windows_agent()
            text = (
                "Windows agent\n\n"
                f"Status: {data.get('status')}\n"
                f"Hostname: {data.get('hostname')}\n"
                f"User: {data.get('user')}\n"
                f"Platform: {data.get('platform')}"
            )
            return {"type": "text", "text": text}
        except Exception as e:
            return {"type": "text", "text": f"Не смогла получить статус Windows agent: {e}"}

    if action_name == "win_screenshot":
        try:
            image_bytes = get_windows_screenshot()
            return {
                "type": "photo",
                "bytes": image_bytes,
                "filename": "windows_screenshot.png",
                "caption": "Скриншот с Windows ПК",
            }
        except Exception as e:
            return {"type": "text", "text": f"Не смогла получить скриншот: {e}"}

    if action_name == "win_camera":
        try:
            image_bytes = get_windows_camera_photo()
            return {
                "type": "photo",
                "bytes": image_bytes,
                "filename": "windows_camera.jpg",
                "caption": "Фото с веб-камеры Windows",
            }
        except Exception as e:
            return {"type": "text", "text": f"Не смогла получить фото с камеры: {e}"}

    if action_name == "win_open_url":
        url = str(args.get("url", "")).strip()
        if not url:
            return {"type": "text", "text": "Не вижу URL. Пример: открой https://youtube.com"}
        try:
            open_windows_url(url)
            return {"type": "text", "text": f"Открыла ссылку на Windows: {url}"}
        except Exception as e:
            return {"type": "text", "text": f"Не смогла открыть URL: {e}"}

    if action_name == "win_lock":
        try:
            send_windows_action("lock")
            return {"type": "text", "text": "ПК заблокирован."}
        except Exception as e:
            return {"type": "text", "text": f"Не смогла заблокировать Windows: {e}"}

    if action_name == "win_logout":
        try:
            send_windows_action("logout")
            return {"type": "text", "text": "Команда выхода из Windows отправлена."}
        except Exception as e:
            return {"type": "text", "text": f"Не смогла выполнить logout: {e}"}

    if action_name == "win_shutdown":
        try:
            send_windows_action("shutdown")
            return {"type": "text", "text": "Команда выключения Windows отправлена."}
        except Exception as e:
            return {"type": "text", "text": f"Не смогла выключить Windows ПК: {e}"}

    if action_name == "win_reboot":
        try:
            send_windows_action("reboot")
            return {"type": "text", "text": "Команда перезагрузки Windows отправлена."}
        except Exception as e:
            return {"type": "text", "text": f"Не смогла перезагрузить Windows ПК: {e}"}

    if action_name == "win_unlock_screen":
        try:
            unlock_windows_screen()
            return {"type": "text", "text": "Попыталась снять блокировку экрана Windows."}
        except Exception as e:
            return {"type": "text", "text": f"Не смогла снять блокировку экрана: {e}"}

    return {"type": "text", "text": f"Неизвестное действие: {action_name}"}