#!/bin/bash

# Скрипт для запуска системы AI Analytics Assistant

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Запуск системы AI Analytics Assistant...${NC}"

# Проверка наличия Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 не найден. Пожалуйста, установите Python 3.${NC}"
    exit 1
fi

# Проверка наличия Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}Node.js не найден. Пожалуйста, установите Node.js.${NC}"
    exit 1
fi

# Проверка наличия файла .env
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Файл .env не найден. Создаем из .env.example...${NC}"
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${GREEN}Файл .env создан. Пожалуйста, отредактируйте его, указав ваш API ключ OpenAI.${NC}"
    else
        echo -e "${RED}Файл .env.example не найден. Создаем базовый .env файл...${NC}"
        echo "DATABASE_URL=sqlite:///./ai_analytics.db" > .env
        echo "SECRET_KEY=your-secret-key-here" >> .env
        echo "OPENAI_API_KEY=" >> .env
        echo "UPLOAD_FOLDER=./uploads" >> .env
        echo "USE_SAMPLE_DATA=True" >> .env
        echo -e "${GREEN}Базовый файл .env создан. Пожалуйста, отредактируйте его, указав ваш API ключ OpenAI.${NC}"
    fi
fi

# Создание директории для загрузки файлов
mkdir -p uploads

# Установка зависимостей Python
echo -e "${YELLOW}Установка зависимостей Python...${NC}"
pip3 install -r requirements.txt

# Инициализация базы данных
echo -e "${YELLOW}Инициализация базы данных...${NC}"
python3 -m app.db.init_db

# Запуск бэкенда
echo -e "${GREEN}Запуск бэкенда на порту 8000...${NC}"
echo -e "${YELLOW}Для доступа к API: http://localhost:8000${NC}"
echo -e "${YELLOW}Для доступа к документации API: http://localhost:8000/api/v1/docs${NC}"
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Ждем запуска бэкенда
sleep 3

# Запуск фронтенда
echo -e "${YELLOW}Установка зависимостей фронтенда...${NC}"
cd frontend && npm install

echo -e "${GREEN}Запуск фронтенда на порту 3000...${NC}"
echo -e "${YELLOW}Для доступа к веб-интерфейсу: http://localhost:3000${NC}"
npm start &
FRONTEND_PID=$!

# Функция для корректного завершения процессов
cleanup() {
    echo -e "${YELLOW}Завершение работы...${NC}"
    kill $BACKEND_PID
    kill $FRONTEND_PID
    exit 0
}

# Перехват сигналов завершения
trap cleanup SIGINT SIGTERM

# Ожидание завершения
wait $BACKEND_PID $FRONTEND_PID
