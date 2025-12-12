# PowerShell script для синхронизации зависимостей с uv
# Использует режим копирования вместо жестких ссылок для совместимости с OneDrive

$env:UV_LINK_MODE = "copy"
uv sync

