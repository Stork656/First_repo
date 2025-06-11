@echo off

:: Задаем UTF-8
chcp 65001 >nul 

:: Для того чтобы считывать переменные с задержкой
setlocal enabledelayedexpansion

:: Запрос пути к папке с проектом
set /p PROJECT_DIR=Введите полный путь к папке с контейнером: 

:: Переходим в папку проекта
cd /d "%PROJECT_DIR%" || (
    echo Ошибка: Не удалось перейти в папку "%PROJECT_DIR%"
    pause
    exit /b 1
)

:: Проверка и создание виртуального окружения
if not exist ".venv" (
    echo Создание виртуального окружения...
    python -m venv .venv
    if errorlevel 1 (
        echo Ошибка создания виртуального окружения
        pause
        exit /b 1
    )
) else (
    echo Виртуальное окружение уже существует.
)

:: Активация виртуального окружения
call .venv\Scripts\activate.bat

:: Установка зависимостей, если нужно
pip show -q tensorflow >nul 2>&1
if errorlevel 1 (
    echo Устанавка зависимостей из requirements.txt...
    pip install --upgrade pip
    pip install -r requirements.txt
) else (
    echo Зависимости уже установлены.
)

:: Запрос данных для подключения
set /p IMAP_SERVER=Введите IMAP вашего сервера: 
set /p IMAP_PORT=Введите порт IMAP: 

:: Запрос SSL с обработкой y/n
set /p IMAP_USE_SSL=Использовать SSL? (y - если да / n - если нет): 
if /i "%IMAP_USE_SSL%"=="y" (
    set IMAP_USE_SSL=true
) else (
    set IMAP_USE_SSL=false
)

set /p EMAIL_USER=Введите email пользователя: 
set /p EMAIL_PASS=Введите пароль от email: 
set /p API_URL=Введите URL API (например, http://127.0.0.1:8000/predict): 

:: Перезапуск Docker контейнера (удалить если есть и запустить заново)
echo Перезапуск Docker контейнера spam-filter-container...
docker rm -f spam-filter-container >nul 2>&1
docker run -d -p 8000:8000 --name spam-filter-container spam-filter

:: Ждём запуска API внутри контейнера (на всякий случай)
timeout /t 10 >nul

:: Экспорт переменных окружения
set IMAP_SERVER=%IMAP_SERVER%
set IMAP_PORT=%IMAP_PORT%
set IMAP_USE_SSL=%IMAP_USE_SSL%
set EMAIL_USER=%EMAIL_USER%
set EMAIL_PASS=%EMAIL_PASS%
set API_URL=%API_URL%

echo.
echo Запуск email фильтра. Для остановки нажмите Ctrl+C.

:: Запускаем скрипта
python email_filter.py

:: Остановка контейнера
echo.
echo Остановка и удаление Docker контейнера...

docker stop spam-filter-container
docker rm spam-filter-container

echo Контейнер остановлен и удалён.
pause
exit /b
