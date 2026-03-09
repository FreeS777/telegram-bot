import requests
from telegram import Update
from telegram.ext import ContextTypes

from app.security.auth import is_allowed
from app.services.memory_service import clear_memory, set_voice_mode
from app.services.system_service import run_command
from app.services.windows_agent_service import check_windows_agent, send_windows_action
from app.utils.text_utils import safe_html, truncate
from app.services.windows_agent_service import get_windows_screenshot, open_windows_url
from app.services.windows_agent_service import unlock_windows_screen


async def deny_access(update: Update) -> None:
    if update.message:
        await update.message.reply_text("Доступ запрещён.")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        await deny_access(update)
        return

    text = (
        "Бот запущен и работает.\n\n"
        "Команды:\n"
        "/help — список команд\n"
        "/ping — проверка\n"
        "/ip — внешний IP сервера\n"
        "/search текст — поиск в Google\n"
        "/server — общая сводка\n"
        "/uptime — время работы\n"
        "/disk — место на диске\n"
        "/ram — память\n"
        "/top — топ процессов\n"
        "/services — важные сервисы\n"
        "/docker — контейнеры Docker\n"
        "/nginx — статус Nginx\n"
        "/logs — логи бота\n"
        "/net — сеть\n"
        "/whoami — пользователь и хост\n"
        "/reboot — перезагрузка Linux сервера через 1 минуту\n"
        "/cancel_reboot — отменить перезагрузку Linux сервера\n"
        "/clear — очистить память диалога\n"
        "/voice_on — включить голосовые ответы\n"
        "/voice_off — выключить голосовые ответы\n\n"
        "Windows agent:\n"
        "/win_status — статус Windows-агента\n"
        "/win_lock — заблокировать экран Windows\n"
        "/win_unlock_screen — попытаться снять блокировку экрана\n"
        "/win_logout — выйти из текущей сессии Windows\n"
        "/win_shutdown — выключить Windows ПК\n"
        "/win_reboot — перезагрузить ПК\n\n"
        "/win_screenshot — сделать скриншот Windows\n"
        "/win_open_url URL — открыть ссылку в браузере Windows\n"
        "Можно писать обычные сообщения и присылать голосовухи."
    )
    await update.message.reply_text(text)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        await deny_access(update)
        return

    text = (
        "Доступные команды:\n\n"
        "/ping — проверка бота\n"
        "/ip — внешний IP\n"
        "/search текст — поиск в Google\n"
        "/server — hostname / uptime / load / RAM / disk\n"
        "/uptime — сколько сервер работает\n"
        "/disk — место на диске\n"
        "/ram — память\n"
        "/top — топ процессов по CPU\n"
        "/services — systemd-статус важных сервисов\n"
        "/docker — docker ps\n"
        "/nginx — статус nginx\n"
        "/logs — последние логи бота\n"
        "/net — IP и сетевые интерфейсы\n"
        "/whoami — текущий пользователь\n"
        "/reboot — перезагрузка Linux сервера через 1 минуту\n"
        "/cancel_reboot — отмена перезагрузки Linux сервера\n"
        "/clear — очистить память диалога\n"
        "/voice_on — включить голосовые ответы\n"
        "/voice_off — выключить голосовые ответы\n\n"
        "Windows agent:\n"
        "/win_status — статус Windows-агента\n"
        "/win_lock — заблокировать экран Windows\n"
        "/win_logout — выйти из Windows\n"
        "/win_unlock_screen — попытаться снять блокировку Windows\n"        
        "/win_shutdown — выключить ПК\n"
        "/win_reboot — перезагрузить Windows\n\n"
        "/win_screenshot — сделать скриншот экрана Windows\n"
        "/win_open_url URL — открыть ссылку в браузере Windows\n"
        "Также можно писать обычный текст и присылать voice message."
    )
    await update.message.reply_text(text)


async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        await deny_access(update)
        return

    clear_memory()
    await update.message.reply_text("Память диалога очищена.")


async def voice_on_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        await deny_access(update)
        return

    set_voice_mode(True)
    await update.message.reply_text("Голосовые ответы включены.")


async def voice_off_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        await deny_access(update)
        return

    set_voice_mode(False)
    await update.message.reply_text("Голосовые ответы выключены.")


async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        await deny_access(update)
        return

    await update.message.reply_text("Я живая. Сервер не уснул 😎")


async def ip_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        await deny_access(update)
        return

    try:
        response = requests.get("https://api.ipify.org", timeout=10)
        response.raise_for_status()
        await update.message.reply_text(f"Внешний IP сервера: {response.text.strip()}")
    except Exception as e:
        await update.message.reply_text(f"Не смогла получить IP: {e}")


async def search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        await deny_access(update)
        return

    if not context.args:
        await update.message.reply_text("Напиши так: /search react router dom")
        return

    query = " ".join(context.args).strip()
    await update.message.reply_text(f"https://www.google.com/search?q={query.replace(' ', '+')}")


async def uptime_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        await deny_access(update)
        return

    output = run_command("uptime -p")
    await update.message.reply_text(f"Uptime: {output}")


async def disk_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        await deny_access(update)
        return

    output = truncate(run_command("df -h /"))
    await update.message.reply_text(
        f"<b>Диск /</b>\n<pre>{safe_html(output)}</pre>",
        parse_mode="HTML"
    )


async def ram_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        await deny_access(update)
        return

    output = truncate(run_command("free -h"))
    await update.message.reply_text(
        f"<b>Память</b>\n<pre>{safe_html(output)}</pre>",
        parse_mode="HTML"
    )


async def server_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        await deny_access(update)
        return

    hostname = run_command("hostname")
    uptime = run_command("uptime -p")
    loadavg = run_command("cat /proc/loadavg")
    mem = truncate(run_command("free -h"))
    disk = truncate(run_command("df -h /"))

    text = (
        f"<b>Сервер: {safe_html(hostname)}</b>\n\n"
        f"<b>Uptime</b>\n<pre>{safe_html(uptime)}</pre>\n"
        f"<b>Load Average</b>\n<pre>{safe_html(loadavg)}</pre>\n"
        f"<b>RAM</b>\n<pre>{safe_html(mem)}</pre>\n"
        f"<b>Disk /</b>\n<pre>{safe_html(disk)}</pre>"
    )
    await update.message.reply_text(text, parse_mode="HTML")


async def top_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        await deny_access(update)
        return

    cmd = "ps -eo pid,ppid,cmd,%mem,%cpu --sort=-%cpu | head -n 12"
    output = truncate(run_command(cmd))
    await update.message.reply_text(
        f"<b>Топ процессов по CPU</b>\n<pre>{safe_html(output)}</pre>",
        parse_mode="HTML"
    )


async def services_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        await deny_access(update)
        return

    bot_status = run_command("systemctl is-active telegram-bot")
    nginx_status = run_command("systemctl is-active nginx")
    docker_status = run_command("systemctl is-active docker")

    text = (
        "<b>Статус сервисов</b>\n\n"
        f"<b>telegram-bot</b>\n<pre>{safe_html(bot_status)}</pre>\n"
        f"<b>nginx</b>\n<pre>{safe_html(nginx_status)}</pre>\n"
        f"<b>docker</b>\n<pre>{safe_html(docker_status)}</pre>"
    )
    await update.message.reply_text(text, parse_mode="HTML")


async def docker_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        await deny_access(update)
        return

    output = truncate(run_command("docker ps --format 'table {{.Names}}\\t{{.Image}}\\t{{.Status}}'"))
    await update.message.reply_text(
        f"<b>Docker containers</b>\n<pre>{safe_html(output)}</pre>",
        parse_mode="HTML"
    )


async def nginx_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        await deny_access(update)
        return

    output = truncate(run_command("systemctl status nginx --no-pager -l", timeout=20))
    await update.message.reply_text(
        f"<b>Nginx status</b>\n<pre>{safe_html(output)}</pre>",
        parse_mode="HTML"
    )


async def logs_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        await deny_access(update)
        return

    output = truncate(run_command("journalctl -u telegram-bot -n 30 --no-pager", timeout=20))
    await update.message.reply_text(
        f"<b>Последние логи telegram-bot</b>\n<pre>{safe_html(output)}</pre>",
        parse_mode="HTML"
    )


async def net_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        await deny_access(update)
        return

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
        f"<b>Внешний IP</b>\n<pre>{safe_html(external_ip)}</pre>\n"
        f"<b>IP интерфейсы</b>\n<pre>{safe_html(ip_brief)}</pre>\n"
        f"<b>Маршруты</b>\n<pre>{safe_html(routes)}</pre>"
    )
    await update.message.reply_text(text, parse_mode="HTML")


async def whoami_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        await deny_access(update)
        return

    user = run_command("whoami")
    hostname = run_command("hostname")
    pwd = run_command("pwd")

    text = (
        f"<b>Пользователь</b>\n<pre>{safe_html(user)}</pre>\n"
        f"<b>Хост</b>\n<pre>{safe_html(hostname)}</pre>\n"
        f"<b>Текущая директория</b>\n<pre>{safe_html(pwd)}</pre>"
    )
    await update.message.reply_text(text, parse_mode="HTML")


async def reboot_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        await deny_access(update)
        return

    result = run_command("sudo shutdown -r +1 'Reboot requested from Telegram bot'")
    text = (
        "Перезагрузка Linux сервера запланирована через 1 минуту.\n"
        "Если передумал — жми /cancel_reboot\n\n"
        f"<pre>{safe_html(result)}</pre>"
    )
    await update.message.reply_text(text, parse_mode="HTML")


async def cancel_reboot_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        await deny_access(update)
        return

    result = run_command("sudo shutdown -c")
    await update.message.reply_text(
        f"Попыталась отменить перезагрузку.\n\n<pre>{safe_html(result)}</pre>",
        parse_mode="HTML"
    )


async def win_status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        await deny_access(update)
        return

    try:
        data = check_windows_agent()

        text = (
            "<b>Windows agent</b>\n\n"
            f"<b>Status</b>\n<pre>{safe_html(str(data.get('status')))}</pre>\n"
            f"<b>Hostname</b>\n<pre>{safe_html(str(data.get('hostname')))}</pre>\n"
            f"<b>Allowed actions</b>\n<pre>{safe_html(', '.join(data.get('allowed_actions', [])))}</pre>"
        )
        await update.message.reply_text(text, parse_mode="HTML")

    except Exception as e:
        await update.message.reply_text(f"Не смогла связаться с Windows agent: {e}")


async def win_lock_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        await deny_access(update)
        return

    try:
        send_windows_action("lock")
        await update.message.reply_text("Экран Windows заблокирован.")
    except Exception as e:
        await update.message.reply_text(f"Не смогла выполнить lock: {e}")


async def win_logout_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        await deny_access(update)
        return

    try:
        send_windows_action("logout")
        await update.message.reply_text("Выход из Windows выполнен.")
    except Exception as e:
        await update.message.reply_text(f"Не смогла выполнить logout: {e}")


async def win_shutdown_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        await deny_access(update)
        return

    try:
        send_windows_action("shutdown")
        await update.message.reply_text("Windows выключается.")
    except Exception as e:
        await update.message.reply_text(f"Не смогла выполнить shutdown: {e}")


async def win_reboot_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        await deny_access(update)
        return

    try:
        send_windows_action("reboot")
        await update.message.reply_text("Windows перезагружается.")
    except Exception as e:
        await update.message.reply_text(f"Не смогла выполнить reboot: {e}")

async def win_screenshot_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_allowed(update):
        await deny_access(update)
        return

    try:
        await update.message.reply_text("Делаю скриншот...")

        image = get_windows_screenshot()

        await update.message.reply_photo(photo=image)

    except Exception as e:
        await update.message.reply_text(f"Не смогла сделать скриншот: {e}")

async def win_open_url(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_allowed(update):
        await deny_access(update)
        return

    if not context.args:
        await update.message.reply_text("Использование: /win_open_url https://site.com")
        return

    url = context.args[0]

    try:
        open_windows_url(url)
        await update.message.reply_text(f"Открываю: {url}")

    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")

async def win_unlock_screen(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_allowed(update):
        await deny_access(update)
        return

    try:
        unlock_windows_screen()
        await update.message.reply_text("Пытаюсь разблокировать экран Windows.")
    except Exception as e:
        await update.message.reply_text(f"Не смогла снять блокировку: {e}")
