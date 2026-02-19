#   Gemini Hub

Веб-додаток для генерації зображень за допомогою Google Gemini API.

## Функціонал

- Завантаження до двох зображень
- Введення текстового промпту
- Генерація нового зображення на основі завантажених зображень та промпту
- Завантаження згенерованого зображення

## Локальний запуск

1. Встановіть uv (якщо ще не встановлено):
```bash
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Встановіть залежності:

**Якщо проект знаходиться в OneDrive**, використовуйте скрипт `sync.ps1`:
```powershell
.\sync.ps1
```

Або встановіть змінну середовища вручну:
```powershell
$env:UV_LINK_MODE = "copy"
uv sync
```

**Якщо проект НЕ в OneDrive**, просто виконайте:
```bash
uv sync
```

Або якщо ви хочете встановити залежності глобально:
```bash
uv pip install -e .
```

**Примітка:** OneDrive не підтримує жорсткі посилання (hard links), тому необхідно використовувати режим копіювання (`UV_LINK_MODE=copy`). Також рекомендується виключити папку `.venv` з синхронізації OneDrive.

2. Встановіть змінну середовища:
```bash
export GEMINI_API_KEY="your-api-key-here"
```

На Windows:
```cmd
set GEMINI_API_KEY=your-api-key-here
```

3. Запустіть додаток:
```bash
# З використанням uv
uv run streamlit run app.py

# Або звичайним способом (якщо залежності встановлені глобально)
streamlit run app.py
```

## Деплой на Heroku

1. Створіть новий додаток на Heroku:
```bash
heroku create your-app-name
```

2. Встановіть змінну середовища GEMINI_API_KEY:
```bash
heroku config:set GEMINI_API_KEY=your-api-key-here
```

3. Деплойте додаток:
```bash
git init
git add .
git commit -m "Initial commit"
git push heroku main
```

4. Відкрийте додаток:
```bash
heroku open
```

## Структура проекту

- `app.py` - основний файл Streamlit додатку
- `pyproject.toml` - конфігурація проекту та залежності (для uv)
- `sync.ps1` - PowerShell скрипт для синхронізації залежностей (для OneDrive)
- `Procfile` - конфігурація для Heroku

## Примітки

- Переконайтеся, що у вас є дійсний API ключ Google Gemini
- Генерація зображень може зайняти деякий час
- Рекомендується завантажувати принаймні одне зображення для кращих результатів

## Використання uv

Проект використовує [uv](https://github.com/astral-sh/uv) - швидкий менеджер пакетів Python.

Основні команди:
- `uv sync` - встановити залежності з pyproject.toml
- `uv run <command>` - запустити команду в віртуальному середовищі uv
- `uv add <package>` - додати новий пакет до проекту
- `uv remove <package>` - видалити пакет з проекту

