# Gemini Image Generator

Веб-додаток для генерації зображень за допомогою Google Gemini API.

## Функціонал

- Завантаження до двох зображень
- Введення текстового промпту
- Генерація нового зображення на основі завантажених зображень та промпту
- Завантаження згенерованого зображення

## Локальний запуск

1. Встановіть залежності:
```bash
pip install -r requirements.txt
```

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
- `requirements.txt` - залежності Python
- `Procfile` - конфігурація для Heroku
- `gemini.py` - оригінальний скрипт (для довідки)

## Примітки

- Переконайтеся, що у вас є дійсний API ключ Google Gemini
- Генерація зображень може зайняти деякий час
- Рекомендується завантажувати принаймні одне зображення для кращих результатів

