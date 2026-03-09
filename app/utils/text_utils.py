import html


def safe_html(text: str) -> str:
    return html.escape(text)


def truncate(text: str, limit: int = 3500) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + "\n\n...обрезано..."


def truncate_for_tts(text: str, limit: int = 1200) -> str:
    text = text.strip()
    if len(text) <= limit:
        return text

    cut = text[:limit]
    last_dot = max(cut.rfind("."), cut.rfind("!"), cut.rfind("?"), cut.rfind("\n"))
    if last_dot > 300:
        cut = cut[: last_dot + 1]

    return cut.strip() + " ..."
