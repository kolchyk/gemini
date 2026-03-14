"""User-friendly error formatting for Gemini API and related exceptions."""

import re


ERROR_MESSAGES: dict[int, str] = {
    400: "Невірний запит. Перевірте введені дані та спробуйте знову.",
    401: "Проблема з авторизацією. Перевірте GEMINI_API_KEY.",
    403: "Доступ заборонено. Можливо, модель або функція недоступна для вашого акаунта.",
    404: "Ресурс не знайдено. Модель або ендпоінт можуть бути змінені.",
    429: "Перевищено ліміт запитів. Зачекайте кілька хвилин перед повторною спробою.",
    500: "Внутрішня помилка сервера Google. Спробуйте пізніше.",
    502: "Сервіс тимчасово недоступний. Спробуйте через кілька хвилин.",
    503: "Модель зараз перевантажена запитами. Це тимчасово — спробуйте ще раз через 1–2 хвилини.",
    504: "Час очікування відповіді минув. Спробуйте ще раз або спростіть запит.",
}


def format_api_error(exc: Exception) -> str:
    raw = str(exc)

    match = re.search(r"'code':\s*(\d+).*?'message':\s*['\"]([^'\"]*)['\"]", raw)
    if match:
        code = int(match.group(1))
        api_message = match.group(2)
        friendly = ERROR_MESSAGES.get(code)
        if friendly:
            return f"{friendly} Деталі: {api_message}"
        return f"Помилка API ({code}): {api_message}"

    for code, message in ERROR_MESSAGES.items():
        if str(code) in raw:
            return message

    if len(raw) > 200:
        return f"Виникла помилка: {raw[:200]}…"
    return f"Виникла помилка: {raw}"


def format_error_with_retry(exc: Exception, action: str = "операцію") -> str:
    msg = format_api_error(exc)
    raw = str(exc).lower()
    if any(s in raw for s in ("503", "429", "504", "unavailable", "resource_exhausted")):
        msg += f" Спробуйте повторити {action} через кілька хвилин."
    return msg
