# Техническая документация AI Analytics Assistant

## Архитектура системы

AI Analytics Assistant построен на основе современной архитектуры с разделением на бэкенд и фронтенд:

### Бэкенд

- **Фреймворк**: FastAPI
- **База данных**: SQLite (можно заменить на PostgreSQL)
- **ORM**: SQLAlchemy
- **Аутентификация**: JWT
- **Обработка данных**: Pandas
- **Интеграция с ИИ**: OpenAI API

### Фронтенд

- **Фреймворк**: React
- **UI библиотека**: Material-UI
- **Управление состоянием**: React Context API
- **Маршрутизация**: React Router
- **HTTP клиент**: Axios

## Структура проекта

```
ai_analytics_assistant/
├── app/                      # Бэкенд (FastAPI)
│   ├── api/                  # API эндпоинты
│   │   ├── endpoints/        # Модули API
│   │   └── __init__.py       # Инициализация API
│   ├── core/                 # Ядро приложения
│   │   ├── config.py         # Конфигурация
│   │   └── security.py       # Безопасность и аутентификация
│   ├── db/                   # Работа с базой данных
│   │   ├── base.py           # Базовые модели
│   │   ├── init_db.py        # Инициализация БД
│   │   └── session.py        # Сессии БД
│   ├── models/               # Модели данных
│   │   └── models.py         # SQLAlchemy модели
│   ├── schemas/              # Pydantic схемы
│   │   └── schemas.py        # Схемы валидации
│   ├── services/             # Бизнес-логика
│   │   ├── excel_data_processor.py  # Обработка Excel
│   │   └── openai_service.py        # Интеграция с OpenAI
│   └── main.py               # Точка входа
├── frontend/                 # Фронтенд (React)
│   ├── public/               # Статические файлы
│   └── src/                  # Исходный код
│       ├── components/       # React компоненты
│       │   ├── analytics/    # Компоненты аналитики
│       │   ├── auth/         # Компоненты аутентификации
│       │   ├── cabinets/     # Компоненты кабинетов
│       │   ├── common/       # Общие компоненты
│       │   ├── dashboard/    # Компоненты дашборда
│       │   ├── layout/       # Компоненты макета
│       │   ├── projects/     # Компоненты проектов
│       │   └── reports/      # Компоненты отчетов
│       ├── contexts/         # React контексты
│       ├── services/         # Сервисы
│       └── App.js            # Главный компонент
├── docs/                     # Документация
├── uploads/                  # Директория для загрузки файлов
├── .env.example              # Пример файла окружения
├── requirements.txt          # Зависимости Python
└── run.sh                    # Скрипт запуска
```

## База данных

### Схема базы данных

Система использует следующие основные таблицы:

- **User**: Пользователи системы
- **Project**: Проекты
- **Cabinet**: Кабинеты маркетплейсов
- **UploadedFile**: Загруженные файлы
- **Metric**: Метрики
- **MetricValue**: Значения метрик
- **Report**: Отчеты
- **Task**: Задачи
- **AnalysisResult**: Результаты анализа

## API эндпоинты

### Аутентификация

- `POST /api/v1/auth/login`: Вход в систему
- `POST /api/v1/auth/register`: Регистрация
- `GET /api/v1/auth/me`: Информация о текущем пользователе

### Проекты

- `GET /api/v1/projects`: Список проектов
- `POST /api/v1/projects`: Создание проекта
- `GET /api/v1/projects/{project_id}`: Получение проекта
- `PUT /api/v1/projects/{project_id}`: Обновление проекта
- `DELETE /api/v1/projects/{project_id}`: Удаление проекта

### Кабинеты

- `GET /api/v1/cabinets`: Список кабинетов
- `POST /api/v1/cabinets`: Создание кабинета
- `GET /api/v1/cabinets/{cabinet_id}`: Получение кабинета
- `PUT /api/v1/cabinets/{cabinet_id}`: Обновление кабинета
- `DELETE /api/v1/cabinets/{cabinet_id}`: Удаление кабинета

### Файлы

- `POST /api/v1/files/upload`: Загрузка файла
- `GET /api/v1/files/files`: Список файлов
- `GET /api/v1/files/files/{file_id}`: Получение файла
- `DELETE /api/v1/files/files/{file_id}`: Удаление файла

### Аналитика

- `POST /api/v1/analytics/analyze`: Запуск анализа
- `GET /api/v1/analytics/cabinet/{cabinet_id}`: Получение аналитики кабинета

### Отчеты

- `GET /api/v1/reports`: Список отчетов
- `POST /api/v1/reports`: Создание отчета
- `GET /api/v1/reports/{report_id}`: Получение отчета
- `DELETE /api/v1/reports/{report_id}`: Удаление отчета

## Интеграция с OpenAI

Система использует OpenAI API для анализа данных и генерации отчетов. Для работы с API необходимо указать API ключ в файле `.env`:

```
OPENAI_API_KEY=your-api-key-here
```

## Обработка Excel-файлов

Система поддерживает загрузку и обработку Excel-файлов (.xlsx, .xls) и CSV-файлов (.csv) с данными маркетплейсов. Обработка файлов выполняется с помощью библиотеки Pandas.

## Развертывание

### Локальное развертывание

1. Установите зависимости Python: `pip install -r requirements.txt`
2. Установите зависимости Node.js: `cd frontend && npm install`
3. Создайте файл `.env` на основе `.env.example`
4. Запустите скрипт `run.sh`

### Продакшн развертывание

Для продакшн развертывания рекомендуется:

1. Использовать PostgreSQL вместо SQLite
2. Настроить NGINX для проксирования запросов
3. Использовать Gunicorn для запуска FastAPI
4. Собрать статическую версию React приложения
5. Настроить HTTPS с помощью Let's Encrypt
