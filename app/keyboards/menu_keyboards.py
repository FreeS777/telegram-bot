from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove


MAIN_MENU_KEYBOARD = ReplyKeyboardMarkup(
    keyboard=[
        ["🏠 Главное меню", "✅ Статус"],
        ["🖥️ Сервер", "🪟 Windows"],
        ["🎤 Голос on", "🔇 Голос off"],
        ["📚 Помощь", "🙈 Скрыть меню"],
    ],
    resize_keyboard=True,
    input_field_placeholder="Выбери кнопку или напиши команду...",
)

SERVER_MENU_KEYBOARD = ReplyKeyboardMarkup(
    keyboard=[
        ["📊 Сводка", "⏱️ Uptime"],
        ["💾 Disk", "🧠 RAM"],
        ["📈 Top", "🧾 Logs"],
        ["🌐 Net", "👤 Whoami"],
        ["⚙️ Services", "🐳 Docker"],
        ["🌍 IP", "🏠 Главное меню"],
    ],
    resize_keyboard=True,
    input_field_placeholder="Раздел Server",
)

WINDOWS_MENU_KEYBOARD = ReplyKeyboardMarkup(
    keyboard=[
        ["📸 Скриншот", "📷 Камера"],
        ["✅ Статус", "🌐 Открыть URL"],
        ["🔒 Lock", "🚪 Logout"],
        ["🔁 Reboot", "🔌 Shutdown"],
        ["🔓 Unlock", "🏠 Главное меню"],
    ],
    resize_keyboard=True,
    input_field_placeholder="Раздел Windows",
)

HIDDEN_MENU = ReplyKeyboardRemove()

MENU_BUTTON_PATTERN = (
    r"^(🏠 Главное меню|✅ Статус|🖥️ Сервер|🪟 Windows|🎤 Голос on|🔇 Голос off|"
    r"📚 Помощь|🙈 Скрыть меню|📊 Сводка|⏱️ Uptime|💾 Disk|🧠 RAM|📈 Top|🧾 Logs|"
    r"🌐 Net|👤 Whoami|⚙️ Services|🐳 Docker|🌍 IP|📸 Скриншот|📷 Камера|"
    r"🔒 Lock|🚪 Logout|🔁 Reboot|🔌 Shutdown|🔓 Unlock|🌐 Открыть URL)$"
)