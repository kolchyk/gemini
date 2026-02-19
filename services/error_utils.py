"""User-friendly error formatting for Gemini API and related exceptions."""

import re


# Map HTTP status codes to user-friendly Ukrainian messages
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
    """
    Converts API exceptions into user-friendly Ukrainian messages.
    
    Handles Gemini/Google GenAI errors in format:
    ServerError: 503 UNAVAILABLE. {'error': {'code': 503, 'message': '...', 'status': 'UNAVAILABLE'}}
    
    Returns:
        User-friendly error message in Ukrainian.
    """
    raw = str(exc)
    
    # Try to extract error dict from the exception string (handles both ' and " quotes)
    match = re.search(r"'code':\s*(\d+).*?'message':\s*['\"]([^'\"]*)['\"]", raw)
    if match:
        code = int(match.group(1))
        api_message = match.group(2)
        friendly = ERROR_MESSAGES.get(code)
        if friendly:
            return f"**{friendly}**\n\n_Деталі: {api_message}_"
        return f"**Помилка API ({code})**\n\n_{api_message}_"
    
    # Fallback: detect status code by pattern "503 UNAVAILABLE" etc.
    for code, message in ERROR_MESSAGES.items():
        if str(code) in raw and ("UNAVAILABLE" in raw or "RESOURCE_EXHAUSTED" in raw or "UNAUTHENTICATED" in raw):
            return f"**{message}**\n\n_({raw[:120]}…)_" if len(raw) > 120 else f"**{message}**\n\n_{raw}_"
    
    # Check for common patterns
    if "503" in raw or "UNAVAILABLE" in raw:
        return f"**{ERROR_MESSAGES[503]}**\n\n_{raw[:150]}…_" if len(raw) > 150 else f"**{ERROR_MESSAGES[503]}**\n\n_{raw}_"
    if "429" in raw or "RESOURCE_EXHAUSTED" in raw:
        return ERROR_MESSAGES[429]
    if "401" in raw or "UNAUTHENTICATED" in raw:
        return ERROR_MESSAGES[401]
    
    # Generic fallback: truncate long technical messages
    if len(raw) > 200:
        return f"**Виникла помилка**\n\n_{raw[:200]}…_"
    return f"**Виникла помилка**\n\n_{raw}_"


def format_error_with_retry(exc: Exception, action: str = "операцію") -> str:
    """
    Formats error and adds retry suggestion for transient errors (503, 429, 504).
    """
    msg = format_api_error(exc)
    raw = str(exc).lower()
    if "503" in raw or "429" in raw or "504" in raw or "unavailable" in raw or "resource_exhausted" in raw:
        msg += f"\n\n🔄 _Натисніть кнопку ще раз через кілька хвилин, щоб повторити {action}._"
    return msg
