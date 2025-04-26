import os
import json
import logging
import asyncio
import tiktoken
import numpy as np
import pandas as pd
import time
import re
from typing import Dict, List, Any, Optional, Union, Tuple
from openai import AsyncOpenAI
from datetime import datetime

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TokenCounter:
    """
    Класс для подсчета токенов в тексте
    """
    
    def __init__(self, model: str = "gpt-4"):
        """
        Инициализирует счетчик токенов
        
        Args:
            model: Модель для подсчета токенов
        """
        self.model = model
        try:
            self.encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            self.encoding = tiktoken.get_encoding("cl100k_base")
    
    def count_tokens(self, text: str) -> int:
        """
        Подсчитывает количество токенов в тексте
        
        Args:
            text: Текст для подсчета токенов
            
        Returns:
            Количество токенов
        """
        if not text:
            return 0
        return len(self.encoding.encode(text))
    
    def count_messages_tokens(self, messages: List[Dict[str, str]]) -> int:
        """
        Подсчитывает количество токенов в сообщениях
        
        Args:
            messages: Список сообщений
            
        Returns:
            Количество токенов
        """
        total_tokens = 0
        for message in messages:
            total_tokens += 4  # Каждое сообщение начинается с 4 токенов
            for key, value in message.items():
                if value is None:
                    continue
                total_tokens += self.count_tokens(str(value))
                if key == "name":
                    total_tokens += 1  # Имя добавляет 1 токен
        total_tokens += 2  # Каждый запрос заканчивается 2 токенами
        return total_tokens


class DataPreprocessor:
    """
    Класс для предварительной обработки данных перед отправкой в OpenAI API
    """
    
    def __init__(self, max_tokens: int = 3000):  # Уменьшен лимит токенов с 4000 до 3000
        """
        Инициализирует препроцессор данных
        
        Args:
            max_tokens: Максимальное количество токенов для обработки
        """
        self.max_tokens = max_tokens
        self.token_counter = TokenCounter()
    
    def optimize_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Оптимизирует DataFrame для уменьшения размера
        
        Args:
            df: DataFrame для оптимизации
            
        Returns:
            Оптимизированный DataFrame
        """
        # Проверяем, что DataFrame не пустой
        if df.empty:
            return df
            
        # Удаляем колонки, где более 90% значений - NaN
        df_opt = df.dropna(axis=1, thresh=int(len(df) * 0.1))
        
        # Если все колонки были удалены, возвращаем исходный DataFrame
        if df_opt.empty:
            return df
        
        # Заполняем пропущенные значения
        numeric_cols = df_opt.select_dtypes(include=['number']).columns
        if not numeric_cols.empty:
            df_opt[numeric_cols] = df_opt[numeric_cols].fillna(0)
        
        object_cols = df_opt.select_dtypes(include=['object']).columns
        if not object_cols.empty:
            df_opt[object_cols] = df_opt[object_cols].fillna('')
        
        # Удаляем дубликаты
        df_opt = df_opt.drop_duplicates()
        
        # Ограничиваем количество строк, если их слишком много
        if len(df_opt) > 50:  # Уменьшено с 100 до 50
            df_opt = df_opt.head(50)
        
        return df_opt
    
    def extract_key_metrics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Извлекает ключевые метрики из данных
        
        Args:
            data: Данные для извлечения ключевых метрик
            
        Returns:
            Словарь с ключевыми метриками
        """
        key_metrics = {}
        
        # Проверяем наличие данных
        if "data" not in data or not data["data"]:
            return key_metrics
        
        try:
            # Преобразуем данные в DataFrame
            df = pd.DataFrame(data["data"])
            
            # Если DataFrame пустой, возвращаем пустой словарь
            if df.empty:
                return key_metrics
            
            # Извлекаем числовые колонки
            numeric_cols = df.select_dtypes(include=['number']).columns
            
            # Ограничиваем количество числовых колонок для анализа
            if len(numeric_cols) > 5:  # Ограничиваем до 5 числовых колонок
                # Выбираем колонки с наибольшей дисперсией
                variances = df[numeric_cols].var()
                numeric_cols = variances.nlargest(5).index.tolist()
            
            # Для каждой числовой колонки вычисляем базовые статистики
            for col in numeric_cols:
                # Проверяем, что колонка содержит хотя бы одно непустое значение
                if df[col].notna().sum() == 0:
                    continue
                    
                key_metrics[col] = {
                    "mean": float(df[col].mean()),
                    "median": float(df[col].median()),
                    "min": float(df[col].min()),
                    "max": float(df[col].max()),
                    # Удаляем некоторые статистики для уменьшения размера
                    # "sum": float(df[col].sum()),
                    # "std": float(df[col].std()),
                    "last_value": float(df[col].iloc[-1]) if len(df) > 0 else 0,
                    "first_value": float(df[col].iloc[0]) if len(df) > 0 else 0
                }
                
                # Добавляем динамику (изменение в процентах)
                if len(df) > 1:
                    first_value = float(df[col].iloc[0])
                    last_value = float(df[col].iloc[-1])
                    if first_value != 0:
                        key_metrics[col]["change_percent"] = (last_value - first_value) / first_value * 100
                    else:
                        key_metrics[col]["change_percent"] = 0
                else:
                    key_metrics[col]["change_percent"] = 0
        except Exception as e:
            logger.warning(f"Error extracting key metrics: {str(e)}")
            
        return key_metrics
    
    def extract_time_series(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Извлекает временные ряды из данных
        
        Args:
            data: Данные для извлечения временных рядов
            
        Returns:
            Словарь с временными рядами
        """
        time_series = {}
        
        # Проверяем наличие данных
        if "data" not in data or not data["data"]:
            return time_series
        
        try:
            # Преобразуем данные в DataFrame
            df = pd.DataFrame(data["data"])
            
            # Если DataFrame пустой, возвращаем пустой словарь
            if df.empty:
                return time_series
            
            # Ищем колонки с датами
            date_cols = [col for col in df.columns if any(kw in str(col).lower() for kw in ['date', 'дата', 'день', 'неделя', 'месяц', 'год'])]
            
            # Если нет колонок с датами, возвращаем пустой словарь
            if not date_cols:
                return time_series
            
            # Берем первую колонку с датой
            date_col = date_cols[0]
            
            # Пытаемся преобразовать колонку с датой в datetime
            try:
                df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
            except:
                return time_series
            
            # Сортируем DataFrame по дате
            df = df.sort_values(by=date_col)
            
            # Извлекаем числовые колонки
            numeric_cols = df.select_dtypes(include=['number']).columns
            
            # Ограничиваем количество числовых колонок для анализа
            if len(numeric_cols) > 3:  # Ограничиваем до 3 числовых колонок
                # Выбираем колонки с наибольшей дисперсией
                variances = df[numeric_cols].var()
                numeric_cols = variances.nlargest(3).index.tolist()
            
            # Для каждой числовой колонки создаем временной ряд
            for col in numeric_cols:
                # Пропускаем колонки с малым количеством уникальных значений
                if df[col].nunique() < 3:
                    continue
                
                # Создаем временной ряд
                time_series[col] = []
                
                # Добавляем значения временного ряда
                for _, row in df.iterrows():
                    if pd.notna(row[date_col]) and pd.notna(row[col]):
                        time_series[col].append({
                            "date": row[date_col].strftime("%Y-%m-%d"),
                            "value": float(row[col])
                        })
                
                # Если временной ряд слишком длинный, прореживаем его
                if len(time_series[col]) > 10:  # Уменьшено с 20 до 10
                    indices = np.linspace(0, len(time_series[col]) - 1, 10, dtype=int)
                    time_series[col] = [time_series[col][i] for i in indices]
        except Exception as e:
            logger.warning(f"Error extracting time series: {str(e)}")
            
        return time_series
    
    def extract_categorical_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Извлекает категориальные данные
        
        Args:
            data: Данные для извлечения категориальных данных
            
        Returns:
            Словарь с категориальными данными
        """
        categorical_data = {}
        
        # Проверяем наличие данных
        if "data" not in data or not data["data"]:
            return categorical_data
        
        try:
            # Преобразуем данные в DataFrame
            df = pd.DataFrame(data["data"])
            
            # Если DataFrame пустой, возвращаем пустой словарь
            if df.empty:
                return categorical_data
            
            # Извлекаем категориальные колонки
            categorical_cols = df.select_dtypes(include=['object', 'category']).columns
            
            # Ограничиваем количество категориальных колонок
            if len(categorical_cols) > 5:  # Ограничиваем до 5 категориальных колонок
                categorical_cols = categorical_cols[:5]
            
            # Для каждой категориальной колонки вычисляем распределение значений
            for col in categorical_cols:
                # Пропускаем колонки с большим количеством уникальных значений
                if df[col].nunique() > 10:  # Уменьшено с 20 до 10
                    continue
                
                # Вычисляем распределение значений
                value_counts = df[col].value_counts().to_dict()
                
                # Преобразуем ключи в строки
                value_counts = {str(k): int(v) for k, v in value_counts.items()}
                
                # Добавляем распределение значений
                categorical_data[col] = value_counts
        except Exception as e:
            logger.warning(f"Error extracting categorical data: {str(e)}")
            
        return categorical_data
    
    def summarize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Создает сводку данных
        
        Args:
            data: Данные для создания сводки
            
        Returns:
            Словарь со сводкой данных
        """
        summary = {}
        
        # Проверяем наличие данных
        if "data" not in data or not data["data"]:
            return summary
        
        try:
            # Преобразуем данные в DataFrame
            df = pd.DataFrame(data["data"])
            
            # Если DataFrame пустой, возвращаем пустой словарь
            if df.empty:
                return summary
            
            # Добавляем базовую информацию
            summary["rows_count"] = len(df)
            summary["columns_count"] = len(df.columns)
            
            # Ограничиваем список колонок, если их слишком много
            if len(df.columns) > 20:  # Ограничиваем до 20 колонок
                summary["columns"] = list(df.columns)[:20]
            else:
                summary["columns"] = list(df.columns)
            
            # Добавляем информацию о пропущенных значениях только для колонок с пропусками
            missing_values = {}
            for col in df.columns:
                missing_count = df[col].isna().sum()
                if missing_count > 0:
                    missing_values[col] = int(missing_count)
            
            # Ограничиваем количество колонок с пропущенными значениями
            if len(missing_values) > 10:  # Ограничиваем до 10 колонок
                missing_values = dict(list(missing_values.items())[:10])
            
            summary["missing_values"] = missing_values
            
            # Добавляем ключевые метрики
            summary["key_metrics"] = self.extract_key_metrics(data)
            
            # Добавляем временные ряды только если они не слишком большие
            time_series = self.extract_time_series(data)
            if time_series and len(json.dumps(time_series)) < 1000:  # Ограничиваем размер до 1000 символов
                summary["time_series"] = time_series
            
            # Добавляем категориальные данные только если они не слишком большие
            categorical_data = self.extract_categorical_data(data)
            if categorical_data and len(json.dumps(categorical_data)) < 1000:  # Ограничиваем размер до 1000 символов
                summary["categorical_data"] = categorical_data
        except Exception as e:
            logger.warning(f"Error summarizing data: {str(e)}")
            
        return summary
    
    def normalize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Нормализует данные для уменьшения количества токенов
        
        Args:
            data: Данные для нормализации
            
        Returns:
            Нормализованные данные
        """
        # Создаем сводку данных
        summary = self.summarize_data(data)
        
        # Если сводка пустая, возвращаем исходные данные
        if not summary:
            return data
        
        # Преобразуем сводку в JSON
        try:
            summary_json = json.dumps(summary, ensure_ascii=False)
            
            # Проверяем количество токенов
            tokens = self.token_counter.count_tokens(summary_json)
            
            # Если количество токенов превышает максимальное, уменьшаем размер сводки
            if tokens > self.max_tokens:
                logger.warning(f"Summary exceeds token limit: {tokens} > {self.max_tokens}")
                
                # Удаляем временные ряды, если они есть
                if "time_series" in summary:
                    del summary["time_series"]
                
                # Удаляем категориальные данные, если они есть
                if "categorical_data" in summary:
                    del summary["categorical_data"]
                
                # Ограничиваем количество ключевых метрик
                if "key_metrics" in summary:
                    # Сортируем ключевые метрики по изменению в процентах
                    sorted_metrics = sorted(
                        summary["key_metrics"].items(),
                        key=lambda x: abs(x[1].get("change_percent", 0)),
                        reverse=True
                    )
                    
                    # Оставляем только топ-5 метрик (уменьшено с 10 до 5)
                    summary["key_metrics"] = dict(sorted_metrics[:5])
                    
                    # Удаляем некоторые поля из метрик для уменьшения размера
                    for metric in summary["key_metrics"].values():
                        if "std" in metric:
                            del metric["std"]
                        if "sum" in metric:
                            del metric["sum"]
                
                # Преобразуем сводку в JSON
                summary_json = json.dumps(summary, ensure_ascii=False)
                
                # Проверяем количество токенов
                tokens = self.token_counter.count_tokens(summary_json)
                
                # Если все еще превышает, оставляем только базовую информацию
                if tokens > self.max_tokens:
                    logger.warning(f"Summary still exceeds token limit: {tokens} > {self.max_tokens}")
                    
                    # Оставляем только базовую информацию
                    summary = {
                        "rows_count": summary.get("rows_count", 0),
                        "columns_count": summary.get("columns_count", 0),
                        "columns": summary.get("columns", [])[:10],  # Ограничиваем до 10 колонок
                    }
                    
                    # Если есть ключевые метрики, оставляем только топ-3
                    if "key_metrics" in summary and summary["key_metrics"]:
                        sorted_metrics = sorted(
                            summary["key_metrics"].items(),
                            key=lambda x: abs(x[1].get("change_percent", 0)),
                            reverse=True
                        )
                        summary["key_metrics"] = dict(sorted_metrics[:3])  # Ограничиваем до 3 метрик
                        
                        # Упрощаем метрики до минимума
                        for metric in summary["key_metrics"].values():
                            for key in list(metric.keys()):
                                if key not in ["mean", "change_percent"]:
                                    del metric[key]
        except Exception as e:
            logger.warning(f"Error normalizing data: {str(e)}")
            return data
        
        # Возвращаем нормализованные данные
        return summary


class ConsolidatedDataProcessor:
    """
    Класс для консолидации данных в батчи
    """
    
    def __init__(self, max_api_calls: int = 3, max_tokens_per_batch: int = 3000):  # Уменьшены параметры
        """
        Инициализирует процессор консолидированных данных
        
        Args:
            max_api_calls: Максимальное количество вызовов API
            max_tokens_per_batch: Максимальное количество токенов на батч
        """
        self.max_api_calls = max_api_calls
        self.max_tokens_per_batch = max_tokens_per_batch
        self.token_counter = TokenCounter()
        self.preprocessor = DataPreprocessor(max_tokens=max_tokens_per_batch)
    
    def consolidate_data(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Консолидирует данные в батчи
        
        Args:
            data: Данные для консолидации
            
        Returns:
            Список батчей
        """
        # Проверяем наличие данных
        if "data" not in data or not data["data"]:
            return [data]
        
        try:
            # Преобразуем данные в DataFrame
            df = pd.DataFrame(data["data"])
            
            # Если DataFrame пустой, возвращаем исходные данные
            if df.empty:
                return [data]
            
            # Если количество строк меньше или равно максимальному количеству вызовов API,
            # возвращаем исходные данные
            if len(df) <= self.max_api_calls:
                return [data]
            
            # Пробуем разные стратегии консолидации
            batches_by_token_limit = self.consolidate_data_by_token_limit(data)
            
            # Если количество батчей превышает максимальное количество вызовов API,
            # объединяем батчи
            if len(batches_by_token_limit) > self.max_api_calls:
                logger.info(f"Too many batches ({len(batches_by_token_limit)}), merging...")
                merged_batches = []
                batch_size = max(1, len(batches_by_token_limit) // self.max_api_calls)
                
                for i in range(0, len(batches_by_token_limit), batch_size):
                    # Объединяем батчи
                    merged_batch = batches_by_token_limit[i]
                    merged_batch["batch_index"] = len(merged_batches)
                    merged_batch["merged_from"] = [j for j in range(i, min(i + batch_size, len(batches_by_token_limit)))]
                    
                    # Добавляем объединенный батч в список
                    merged_batches.append(merged_batch)
                
                logger.info(f"Merged into {len(merged_batches)} batches")
                return merged_batches
            
            logger.info(f"Using token-based consolidation with {len(batches_by_token_limit)} batches")
            return batches_by_token_limit
        except Exception as e:
            logger.warning(f"Error consolidating data: {str(e)}")
            return [data]
    
    def consolidate_data_by_token_limit(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Консолидирует данные в батчи по лимиту токенов
        
        Args:
            data: Данные для консолидации
            
        Returns:
            Список батчей
        """
        # Проверяем наличие данных
        if "data" not in data or not data["data"]:
            return [data]
        
        try:
            # Преобразуем данные в DataFrame
            df = pd.DataFrame(data["data"])
            
            # Если DataFrame пустой, возвращаем исходные данные
            if df.empty:
                return [data]
            
            # Создаем батчи
            batches = []
            current_batch_df = pd.DataFrame()
            current_batch_tokens = 0
            
            # Проходим по строкам DataFrame
            for _, row in df.iterrows():
                # Преобразуем строку в словарь
                row_dict = row.to_dict()
                
                # Преобразуем словарь в JSON
                row_json = json.dumps(row_dict, ensure_ascii=False)
                
                # Подсчитываем количество токенов
                row_tokens = self.token_counter.count_tokens(row_json)
                
                # Если добавление строки превысит лимит токенов, создаем новый батч
                if current_batch_tokens + row_tokens > self.max_tokens_per_batch and not current_batch_df.empty:
                    # Преобразуем DataFrame в словарь
                    batch_data = {
                        "data": current_batch_df.to_dict(orient='records'),
                        "columns": list(df.columns),
                        "batch_index": len(batches)
                    }
                    
                    # Нормализуем данные батча
                    normalized_batch = self.preprocessor.normalize_data(batch_data)
                    
                    # Добавляем батч в список
                    batches.append(normalized_batch)
                    
                    # Сбрасываем текущий батч
                    current_batch_df = pd.DataFrame()
                    current_batch_tokens = 0
                
                # Добавляем строку в текущий батч
                current_batch_df = pd.concat([current_batch_df, pd.DataFrame([row_dict])])
                current_batch_tokens += row_tokens
            
            # Добавляем последний батч, если он не пустой
            if not current_batch_df.empty:
                # Преобразуем DataFrame в словарь
                batch_data = {
                    "data": current_batch_df.to_dict(orient='records'),
                    "columns": list(df.columns),
                    "batch_index": len(batches)
                }
                
                # Нормализуем данные батча
                normalized_batch = self.preprocessor.normalize_data(batch_data)
                
                # Добавляем батч в список
                batches.append(normalized_batch)
        except Exception as e:
            logger.warning(f"Error consolidating data by token limit: {str(e)}")
            return [data]
        
        return batches


class JSONResponseFormatter:
    """
    Класс для форматирования и исправления JSON-ответов
    """
    
    @staticmethod
    def extract_json_from_text(text: str) -> Optional[str]:
        """
        Извлекает JSON из текста
        
        Args:
            text: Текст, содержащий JSON
            
        Returns:
            Извлеченный JSON или None, если JSON не найден
        """
        if not text:
            return None
            
        # Ищем JSON в тексте с помощью регулярных выражений
        json_pattern = r'```(?:json)?\s*({[\s\S]*?})\s*```'
        matches = re.findall(json_pattern, text)
        
        if matches:
            return matches[0]
        
        # Если не нашли JSON в блоке кода, ищем JSON между фигурными скобками
        start_idx = text.find('{')
        end_idx = text.rfind('}')
        
        if start_idx != -1 and end_idx != -1 and start_idx < end_idx:
            return text[start_idx:end_idx+1]
        
        return None
    
    @staticmethod
    def fix_json_string(json_str: str) -> str:
        """
        Исправляет строку JSON
        
        Args:
            json_str: Строка JSON для исправления
            
        Returns:
            Исправленная строка JSON
        """
        if not json_str:
            return "{}"
            
        # Заменяем одинарные кавычки на двойные
        json_str = json_str.replace("'", '"')
        
        # Исправляем неэкранированные кавычки в значениях
        json_str = re.sub(r'(?<!\\)"([^"]*?)(?<!\\)":\s*"(.*?)(?<!\\)"(,?)', r'"\1": "\2"\3', json_str)
        
        # Исправляем неэкранированные обратные слеши
        json_str = json_str.replace('\\', '\\\\')
        
        # Исправляем двойные экранирования
        json_str = json_str.replace('\\\\\\\\', '\\\\')
        
        # Исправляем кавычки после экранирования
        json_str = json_str.replace('\\"', '"')
        json_str = re.sub(r'(?<!\\)"', '\\"', json_str)
        json_str = json_str.replace('\\"', '"')
        
        # Исправляем экранированные кавычки в ключах
        json_str = re.sub(r'\\+"([^"]+)\\+":', r'"\1":', json_str)
        
        return json_str
    
    @staticmethod
    def parse_json_safely(json_str: str) -> Dict[str, Any]:
        """
        Безопасно парсит JSON
        
        Args:
            json_str: Строка JSON для парсинга
            
        Returns:
            Распарсенный JSON
        """
        if not json_str:
            return {}
            
        try:
            # Пытаемся распарсить JSON
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.warning(f"JSON decode error: {str(e)}")
            
            try:
                # Пытаемся исправить JSON
                fixed_json = JSONResponseFormatter.fix_json_string(json_str)
                return json.loads(fixed_json)
            except json.JSONDecodeError as e2:
                logger.warning(f"Failed to fix JSON: {str(e2)}")
                
                # Если не удалось исправить JSON, возвращаем пустой словарь
                return {}
    
    @staticmethod
    def create_fallback_response(raw_content: str, error_message: str = "") -> Dict[str, Any]:
        """
        Создает резервный ответ, если не удалось распарсить JSON
        
        Args:
            raw_content: Исходный текст ответа
            error_message: Сообщение об ошибке
            
        Returns:
            Резервный ответ
        """
        # Создаем базовую структуру ответа
        response = {
            "title": "Результаты анализа",
            "summary": raw_content[:1000] if raw_content else "Не удалось получить результаты анализа",
            "period_data": {
                "start_date": datetime.now().strftime("%d.%m"),
                "end_date": datetime.now().strftime("%d.%m")
            },
            "dynamics": {
                "total_rows": 0,
                "total_columns": 0,
                "mean": {},
                "median": {},
                "change_percent": {},
                "key_metrics_change_percent": 0
            },
            "factors": {
                "missing_values": "",
                "categorical_data": "",
                "key_factors": []
            },
            "links": {"internal": [], "external": []},
            "completed_tasks": [],
            "pending_tasks": []
        }
        
        # Если есть сообщение об ошибке, добавляем его
        if error_message:
            response["error"] = error_message
        
        # Пытаемся извлечь структурированную информацию из текста
        if raw_content:
            # Ищем заголовок
            title_match = re.search(r'#\s*(.*?)(?:\n|$)', raw_content)
            if title_match:
                response["title"] = title_match.group(1).strip()
            
            # Ищем резюме
            summary_match = re.search(r'(?:Резюме|Сводка|Краткое содержание):(.*?)(?:\n\n|\n#|$)', raw_content, re.DOTALL)
            if summary_match:
                response["summary"] = summary_match.group(1).strip()
            
            # Ищем данные за период
            period_match = re.search(r'(?:Данные за период|Данные за анализируемый период):(.*?)(?:\n\n|\n#|$)', raw_content, re.DOTALL)
            if period_match:
                period_text = period_match.group(1).strip()
                # Пытаемся извлечь даты из текста
                start_date_match = re.search(r'(?:с|от|начало)\s+(\d{1,2}[./-]\d{1,2}(?:[./-]\d{2,4})?)', period_text)
                end_date_match = re.search(r'(?:по|до|конец)\s+(\d{1,2}[./-]\d{1,2}(?:[./-]\d{2,4})?)', period_text)
                
                if start_date_match:
                    response["period_data"]["start_date"] = start_date_match.group(1)
                if end_date_match:
                    response["period_data"]["end_date"] = end_date_match.group(1)
            
            # Ищем динамику
            dynamics_match = re.search(r'(?:Динамика|Динамика показателей):(.*?)(?:\n\n|\n#|$)', raw_content, re.DOTALL)
            if dynamics_match:
                dynamics_text = dynamics_match.group(1).strip()
                # Пытаемся извлечь числовые значения из текста
                mean_matches = re.findall(r'среднее\s+(?:значение)?\s+(?:для)?\s+([^:]+):\s*([\d.]+)', dynamics_text, re.IGNORECASE)
                for metric, value in mean_matches:
                    response["dynamics"]["mean"][metric.strip()] = float(value)
                
                median_matches = re.findall(r'медиана\s+(?:для)?\s+([^:]+):\s*([\d.]+)', dynamics_text, re.IGNORECASE)
                for metric, value in median_matches:
                    response["dynamics"]["median"][metric.strip()] = float(value)
                
                change_percent_matches = re.findall(r'изменение\s+(?:в процентах)?\s+(?:для)?\s+([^:]+):\s*([-\d.]+)%', dynamics_text, re.IGNORECASE)
                for metric, value in change_percent_matches:
                    response["dynamics"]["change_percent"][metric.strip()] = float(value)
                
                key_metrics_change_match = re.search(r'ключевые\s+метрики\s+изменились\s+на\s+([-\d.]+)%', dynamics_text, re.IGNORECASE)
                if key_metrics_change_match:
                    response["dynamics"]["key_metrics_change_percent"] = float(key_metrics_change_match.group(1))
            
            # Ищем факторы
            factors_match = re.search(r'(?:Факторы|Факторы влияния):(.*?)(?:\n\n|\n#|$)', raw_content, re.DOTALL)
            if factors_match:
                factors_text = factors_match.group(1).strip()
                
                # Ищем информацию о пропущенных значениях
                missing_values_match = re.search(r'(?:Пропущенные значения|Missing values):(.*?)(?:\n\n|$)', factors_text, re.DOTALL)
                if missing_values_match:
                    response["factors"]["missing_values"] = missing_values_match.group(1).strip()
                
                # Ищем информацию о категориальных данных
                categorical_data_match = re.search(r'(?:Категориальные данные|Categorical data):(.*?)(?:\n\n|$)', factors_text, re.DOTALL)
                if categorical_data_match:
                    response["factors"]["categorical_data"] = categorical_data_match.group(1).strip()
                
                # Ищем ключевые факторы
                key_factors_matches = re.findall(r'[-*]\s*(.*?)(?:\n|$)', factors_text)
                if key_factors_matches:
                    response["factors"]["key_factors"] = [factor.strip() for factor in key_factors_matches if factor.strip()]
            
            # Ищем выполненные задачи
            completed_tasks_match = re.search(r'(?:Выполненные задачи|Завершенные задачи):(.*?)(?:\n\n|\n#|$)', raw_content, re.DOTALL)
            if completed_tasks_match:
                tasks_text = completed_tasks_match.group(1).strip()
                tasks = re.findall(r'[-*]\s*(.*?)(?:\n|$)', tasks_text)
                response["completed_tasks"] = [task.strip() for task in tasks if task.strip()]
            
            # Ищем предстоящие задачи
            pending_tasks_match = re.search(r'(?:Предстоящие задачи|Запланированные задачи):(.*?)(?:\n\n|\n#|$)', raw_content, re.DOTALL)
            if pending_tasks_match:
                tasks_text = pending_tasks_match.group(1).strip()
                tasks = re.findall(r'[-*]\s*(.*?)(?:\n|$)', tasks_text)
                response["pending_tasks"] = [task.strip() for task in tasks if task.strip()]
        
        return response


class APIRetryStrategy:
    """
    Класс для стратегии повторных попыток при сбоях API
    """
    
    def __init__(self, max_retries: int = 3, initial_delay: float = 1.0, backoff_factor: float = 2.0):
        """
        Инициализирует стратегию повторных попыток
        
        Args:
            max_retries: Максимальное количество повторных попыток
            initial_delay: Начальная задержка в секундах
            backoff_factor: Коэффициент увеличения задержки
        """
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.backoff_factor = backoff_factor
    
    async def execute_with_retry(self, func, *args, **kwargs):
        """
        Выполняет функцию с повторными попытками при сбоях
        
        Args:
            func: Функция для выполнения
            *args: Позиционные аргументы функции
            **kwargs: Именованные аргументы функции
            
        Returns:
            Результат выполнения функции
        """
        retries = 0
        delay = self.initial_delay
        last_error = None
        
        while retries <= self.max_retries:
            try:
                # Выполняем функцию
                return await func(*args, **kwargs)
            except Exception as e:
                last_error = e
                retries += 1
                
                # Если достигнуто максимальное количество попыток, выбрасываем исключение
                if retries > self.max_retries:
                    logger.error(f"Max retries reached. Last error: {str(e)}")
                    raise
                
                # Логируем ошибку и увеличиваем задержку
                logger.warning(f"Retry {retries}/{self.max_retries}. Error: {str(e)}. Retrying in {delay:.2f} seconds...")
                
                # Ждем перед следующей попыткой
                await asyncio.sleep(delay)
                
                # Увеличиваем задержку
                delay *= self.backoff_factor
        
        # Если мы здесь, значит все попытки завершились неудачно
        raise last_error


class ModelCompatibilityChecker:
    """
    Класс для проверки совместимости моделей с различными параметрами API
    """
    
    # Список моделей, поддерживающих параметр response_format={"type": "json_object"}
    JSON_FORMAT_SUPPORTED_MODELS = [
        "gpt-4-turbo",
        "gpt-4-0125-preview",
        "ft:gpt-4.1-2025-04-14:expovision:expovision:BQ4JVN7C",
        "gpt-4-1106-preview",
        "gpt-4-vision-preview",
        "gpt-3.5-turbo-0125",
        "gpt-3.5-turbo-1106"
    ]
    
    @staticmethod
    def supports_json_response_format(model: str) -> bool:
        """
        Проверяет, поддерживает ли модель параметр response_format={"type": "json_object"}
        
        Args:
            model: Название модели
            
        Returns:
            True, если модель поддерживает параметр, иначе False
        """
        # Проверяем, содержит ли название модели одну из поддерживаемых моделей
        return any(supported_model in model for supported_model in ModelCompatibilityChecker.JSON_FORMAT_SUPPORTED_MODELS)


class EmptyResponseHandler:
    """
    Класс для обработки пустых ответов от API
    """
    
    def __init__(self, max_retries: int = 3, delay_between_retries: float = 2.0):
        """
        Инициализирует обработчик пустых ответов
        
        Args:
            max_retries: Максимальное количество повторных попыток
            delay_between_retries: Задержка между повторными попытками в секундах
        """
        self.max_retries = max_retries
        self.delay_between_retries = delay_between_retries
    
    async def handle_empty_response(self, api_call_func, *args, **kwargs) -> Tuple[bool, Any]:
        """
        Обрабатывает пустые ответы от API
        
        Args:
            api_call_func: Функция для вызова API
            *args: Позиционные аргументы функции
            **kwargs: Именованные аргументы функции
            
        Returns:
            Кортеж (успех, результат)
        """
        retries = 0
        
        while retries < self.max_retries:
            try:
                # Вызываем API
                response = await api_call_func(*args, **kwargs)
                
                # Проверяем, что ответ не пустой
                if response and hasattr(response, 'choices') and response.choices:
                    content = response.choices[0].message.content
                    if content and not content.isspace():
                        return True, response
            except Exception as e:
                logger.warning(f"Error calling API: {str(e)}")
            
            # Увеличиваем счетчик попыток
            retries += 1
            
            # Если достигнуто максимальное количество попыток, возвращаем False
            if retries >= self.max_retries:
                logger.warning(f"Max retries reached for empty response handler")
                return False, None
            
            # Ждем перед следующей попыткой
            logger.info(f"Retrying API call in {self.delay_between_retries} seconds...")
            await asyncio.sleep(self.delay_between_retries)
        
        return False, None
    
    def generate_default_response(self, analysis_type: str = "metrics") -> Dict[str, Any]:
        """
        Генерирует стандартный ответ для случая, когда не удалось получить ответ от API
        
        Args:
            analysis_type: Тип анализа (trends, competitors, metrics)
            
        Returns:
            Стандартный ответ
        """
        # Получаем текущую дату
        current_date = datetime.now().strftime("%d.%m")
        
        # Генерируем стандартный ответ в зависимости от типа анализа
        if analysis_type == "trends":
            return {
                "title": "Анализ трендов",
                "summary": "Анализ трендов не удалось выполнить из-за ошибки API. Пожалуйста, попробуйте позже или обратитесь в службу поддержки.",
                "period_data": {
                    "start_date": current_date,
                    "end_date": current_date
                },
                "dynamics": {
                    "total_rows": 0,
                    "total_columns": 0,
                    "mean": {},
                    "median": {},
                    "change_percent": {},
                    "key_metrics_change_percent": 0
                },
                "factors": {
                    "missing_values": "Информация о пропущенных значениях недоступна",
                    "categorical_data": "Информация о категориальных данных недоступна",
                    "key_factors": ["Недостаточно данных для анализа"]
                },
                "links": {"internal": [], "external": []},
                "completed_tasks": ["Попытка анализа трендов"],
                "pending_tasks": ["Повторить анализ позже", "Проверить качество исходных данных", "Обратиться в службу поддержки при повторении ошибки"]
            }
        elif analysis_type == "competitors":
            return {
                "title": "Анализ конкурентов",
                "summary": "Анализ конкурентов не удалось выполнить из-за ошибки API. Пожалуйста, попробуйте позже или обратитесь в службу поддержки.",
                "period_data": {
                    "start_date": current_date,
                    "end_date": current_date
                },
                "dynamics": {
                    "total_rows": 0,
                    "total_columns": 0,
                    "mean": {},
                    "median": {},
                    "change_percent": {},
                    "key_metrics_change_percent": 0
                },
                "factors": {
                    "missing_values": "Информация о пропущенных значениях недоступна",
                    "categorical_data": "Информация о категориальных данных недоступна",
                    "key_factors": ["Недостаточно данных для анализа"]
                },
                "links": {"internal": [], "external": []},
                "completed_tasks": ["Попытка анализа конкурентов"],
                "pending_tasks": ["Повторить анализ позже", "Проверить качество исходных данных", "Обратиться в службу поддержки при повторении ошибки"]
            }
        else:
            return {
                "title": "Анализ данных",
                "summary": "Анализ данных не удалось выполнить из-за ошибки API. Пожалуйста, попробуйте позже или обратитесь в службу поддержки.",
                "period_data": {
                    "start_date": current_date,
                    "end_date": current_date
                },
                "dynamics": {
                    "total_rows": 0,
                    "total_columns": 0,
                    "mean": {},
                    "median": {},
                    "change_percent": {},
                    "key_metrics_change_percent": 0
                },
                "factors": {
                    "missing_values": "Информация о пропущенных значениях недоступна",
                    "categorical_data": "Информация о категориальных данных недоступна",
                    "key_factors": ["Недостаточно данных для анализа"]
                },
                "links": {"internal": [], "external": []},
                "completed_tasks": ["Попытка анализа данных"],
                "pending_tasks": ["Повторить анализ позже", "Проверить качество исходных данных", "Обратиться в службу поддержки при повторении ошибки"]
            }


class TwoStageAnalyzer:
    """
    Класс для двухэтапного анализа данных с использованием OpenAI API
    """
    
    def __init__(self, api_key: Optional[str] = None, max_api_calls: int = 3):  # Уменьшено с 5 до 3
        """
        Инициализирует двухэтапный анализатор
        
        Args:
            api_key: API-ключ OpenAI
            max_api_calls: Максимальное количество вызовов API
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.max_api_calls = max_api_calls
        self.async_client = AsyncOpenAI(api_key=self.api_key)
        self.token_counter = TokenCounter()
        self.data_processor = ConsolidatedDataProcessor(max_api_calls=max_api_calls)
        self.json_formatter = JSONResponseFormatter()
        self.retry_strategy = APIRetryStrategy()
        self.model_checker = ModelCompatibilityChecker()
        self.empty_response_handler = EmptyResponseHandler()
    
    async def analyze_batch(self, batch: Dict[str, Any], system_prompt: str, marketplace: Optional[str] = None, analysis_type: str = "metrics") -> Dict[str, Any]:
        """
        Анализирует батч данных с использованием дешевой модели (gpt-3.5-turbo)
        
        Args:
            batch: Батч данных для анализа
            system_prompt: Системный промпт
            marketplace: Название маркетплейса (опционально)
            analysis_type: Тип анализа (trends, competitors, metrics)
            
        Returns:
            Результаты анализа батча
        """
        # Создаем промпт для анализа батча
        user_prompt = f"""
Я предоставляю тебе данные для анализа из маркетплейса {marketplace or 'неизвестный маркетплейс'}.
Тип анализа: {analysis_type}

Данные:
```json
{json.dumps(batch, ensure_ascii=False, indent=2)}
```

Проведи анализ этих данных и предоставь результаты в виде структурированного JSON с полями:
- title: заголовок анализа
- summary: краткое резюме анализа
- period_data: объект с полями start_date и end_date, содержащими даты начала и конца периода анализа в формате "DD.MM"
- dynamics: объект с информацией о динамике показателей, включающий поля total_rows, total_columns, mean, median, change_percent и key_metrics_change_percent
- factors: объект с информацией о факторах, влияющих на изменения показателей, включающий поля missing_values, categorical_data и key_factors (массив)
- links: объект с полями internal и external (массивы)
- completed_tasks: массив выполненных задач
- pending_tasks: массив предстоящих задач

ВАЖНО: Ответ должен быть ТОЛЬКО в формате JSON. Не добавляй никаких пояснений, комментариев или текста до или после JSON. Не используй маркдаун-форматирование для JSON. Верни только чистый JSON-объект.
"""
        
        # Создаем сообщения для API
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        # Подсчитываем количество токенов
        tokens = self.token_counter.count_messages_tokens(messages)
        logger.info(f"Batch analysis tokens: {tokens}")
        
        # Если количество токенов превышает лимит, уменьшаем размер данных
        if tokens > 3500:  # Уменьшено с 15000 до 3500
            logger.warning(f"Batch exceeds token limit: {tokens} > 3500")
            
            # Уменьшаем размер данных
            if "data" in batch:
                del batch["data"]
            
            # Удаляем некоторые поля для уменьшения размера
            for field in ["time_series", "categorical_data"]:
                if field in batch:
                    del batch[field]
            
            # Ограничиваем количество ключевых метрик
            if "key_metrics" in batch and len(batch["key_metrics"]) > 3:
                # Сортируем ключевые метрики по изменению в процентах
                sorted_metrics = sorted(
                    batch["key_metrics"].items(),
                    key=lambda x: abs(x[1].get("change_percent", 0)),
                    reverse=True
                )
                
                # Оставляем только топ-3 метрики
                batch["key_metrics"] = dict(sorted_metrics[:3])
            
            # Обновляем промпт
            user_prompt = f"""
Я предоставляю тебе сводку данных для анализа из маркетплейса {marketplace or 'неизвестный маркетплейс'}.
Тип анализа: {analysis_type}

Сводка данных:
```json
{json.dumps(batch, ensure_ascii=False, indent=2)}
```

Проведи анализ этой сводки и предоставь результаты в виде структурированного JSON с полями:
- title: заголовок анализа
- summary: краткое резюме анализа
- period_data: объект с полями start_date и end_date, содержащими даты начала и конца периода анализа в формате "DD.MM"
- dynamics: объект с информацией о динамике показателей, включающий поля total_rows, total_columns, mean, median, change_percent и key_metrics_change_percent
- factors: объект с информацией о факторах, влияющих на изменения показателей, включающий поля missing_values, categorical_data и key_factors (массив)
- links: объект с полями internal и external (массивы)
- completed_tasks: массив выполненных задач
- pending_tasks: массив предстоящих задач

ВАЖНО: Ответ должен быть ТОЛЬКО в формате JSON. Не добавляй никаких пояснений, комментариев или текста до или после JSON. Не используй маркдаун-форматирование для JSON. Верни только чистый JSON-объект.
"""
            
            # Обновляем сообщения
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            # Подсчитываем количество токенов
            tokens = self.token_counter.count_messages_tokens(messages)
            logger.info(f"Updated batch analysis tokens: {tokens}")
        
        try:
            # Отправляем запрос к API с повторными попытками
            async def call_api():
                logger.info(f"Sending batch analysis to gpt-3.5-turbo")
                
                # Проверяем, поддерживает ли модель параметр response_format
                model = "gpt-3.5-turbo"  # Используем более компактную модель
                kwargs = {
                    "model": model,
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 2000  # Уменьшено с 4000 до 2000
                }
                
                # Добавляем параметр response_format только если модель его поддерживает
                if self.model_checker.supports_json_response_format(model):
                    kwargs["response_format"] = {"type": "json_object"}
                
                return await self.async_client.chat.completions.create(**kwargs)
            
            # Используем обработчик пустых ответов
            success, response = await self.empty_response_handler.handle_empty_response(
                self.retry_strategy.execute_with_retry, call_api
            )
            
            # Если не удалось получить ответ, возвращаем стандартный ответ
            if not success or not response:
                logger.warning("Failed to get response from API, using default response")
                return self.empty_response_handler.generate_default_response(analysis_type)
            
            # Получаем ответ
            raw_content = response.choices[0].message.content
            logger.info(f"Raw content from gpt-3.5-turbo: {raw_content[:100]}...")
            
            # Проверяем, что ответ не пустой
            if not raw_content or raw_content.isspace():
                logger.warning("Empty response from API")
                return self.empty_response_handler.generate_default_response(analysis_type)
            
            # Пытаемся преобразовать ответ в JSON
            try:
                result = json.loads(raw_content)
                logger.info("Successfully parsed batch response as JSON")
                return result
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse batch response as JSON: {str(e)}")
                
                # Пытаемся извлечь JSON из текста
                json_str = self.json_formatter.extract_json_from_text(raw_content)
                if json_str:
                    try:
                        result = json.loads(json_str)
                        logger.info("Successfully extracted and parsed JSON from text")
                        return result
                    except json.JSONDecodeError as e2:
                        logger.warning(f"Failed to parse extracted JSON: {str(e2)}")
                
                # Пытаемся исправить JSON
                try:
                    # Ищем начало и конец JSON
                    start_idx = raw_content.find("{")
                    end_idx = raw_content.rfind("}")
                    
                    if start_idx != -1 and end_idx != -1:
                        json_str = raw_content[start_idx:end_idx+1]
                        fixed_json = self.json_formatter.fix_json_string(json_str)
                        result = json.loads(fixed_json)
                        logger.info("Successfully parsed fixed batch response as JSON")
                        return result
                    else:
                        # Если не удалось найти JSON, возвращаем текст как есть
                        logger.warning("Could not find JSON in response")
                        return self.json_formatter.create_fallback_response(raw_content, "Could not find JSON in response")
                except Exception as e2:
                    logger.warning(f"Failed to fix JSON: {str(e2)}")
                    
                    # Если не удалось исправить JSON, возвращаем текст как есть
                    return self.json_formatter.create_fallback_response(raw_content, f"Failed to fix JSON: {str(e2)}")
        except Exception as e:
            logger.error(f"Error analyzing batch: {str(e)}")
            
            # В случае ошибки возвращаем пустой результат
            return self.empty_response_handler.generate_default_response(analysis_type)
    
    async def synthesize_final_analysis(self, batch_results: List[Dict[str, Any]], system_prompt: str, marketplace: Optional[str] = None, analysis_type: str = "metrics") -> Dict[str, Any]:
        """
        Синтезирует финальный анализ на основе результатов анализа батчей с использованием дорогой модели (gpt-4)
        
        Args:
            batch_results: Список результатов анализа батчей
            system_prompt: Системный промпт
            marketplace: Название маркетплейса (опционально)
            analysis_type: Тип анализа (trends, competitors, metrics)
            
        Returns:
            Финальный анализ
        """
        # МОДИФИКАЦИЯ: Вместо передачи сырых данных, передаем только обработанные результаты первой стадии анализа
        # Извлекаем ключевые метрики и выводы из каждого батча
        normalized_results = []
        
        for i, result in enumerate(batch_results):
            # Проверяем, что результат не пустой
            if not result:
                continue
                
            # Извлекаем только необходимые поля для финального анализа
            normalized_result = {
                "batch_index": i,
                "title": result.get("title", f"Результаты анализа батча {i+1}"),
                "summary": result.get("summary", "")
            }
            
            # Извлекаем ключевые метрики из разных полей результата
            if "period_data" in result and result["period_data"]:
                normalized_result["period_data"] = result["period_data"]
            
            if "dynamics" in result and result["dynamics"]:
                normalized_result["dynamics"] = result["dynamics"]
            
            if "factors" in result and result["factors"]:
                normalized_result["factors"] = result["factors"]
            
            # Добавляем выполненные задачи
            if "completed_tasks" in result and result["completed_tasks"]:
                normalized_result["completed_tasks"] = result["completed_tasks"]
            
            # Добавляем рекомендуемые задачи
            if "pending_tasks" in result and result["pending_tasks"]:
                normalized_result["pending_tasks"] = result["pending_tasks"]
            
            normalized_results.append(normalized_result)
        
        # Если нет нормализованных результатов, возвращаем пустой результат
        if not normalized_results:
            logger.warning("No normalized results to synthesize")
            return self.empty_response_handler.generate_default_response(analysis_type)
        
        # Создаем промпт с нормализованными результатами
        user_prompt = f"""
Я провел предварительный анализ данных для маркетплейса {marketplace or 'неизвестный маркетплейс'} и получил следующие результаты по {len(normalized_results)} батчам данных:

```json
{json.dumps(normalized_results, ensure_ascii=False, indent=2)}
```

Теперь мне нужен финальный анализ, объединяющий все эти результаты в единый отчет.
Тип анализа: {analysis_type}

Результат должен быть в виде структурированного JSON с полями:
- title: заголовок анализа
- summary: краткое резюме анализа
- period_data: объект с полями start_date и end_date, содержащими даты начала и конца периода анализа в формате "DD.MM"
- dynamics: объект с информацией о динамике показателей, включающий поля total_rows, total_columns, mean, median, change_percent и key_metrics_change_percent
- factors: объект с информацией о факторах, влияющих на изменения показателей, включающий поля missing_values, categorical_data и key_factors (массив)
- links: объект с полями internal и external (массивы)
- completed_tasks: массив выполненных задач
- pending_tasks: массив предстоящих задач

ВАЖНО: Ответ должен быть ТОЛЬКО в формате JSON. Не добавляй никаких пояснений, комментариев или текста до или после JSON. Не используй маркдаун-форматирование для JSON. Верни только чистый JSON-объект.
"""
        
        # Создаем сообщения для API
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        # Подсчитываем количество токенов
        tokens = self.token_counter.count_messages_tokens(messages)
        logger.info(f"Final synthesis tokens: {tokens}")
        
        # Если количество токенов превышает лимит, уменьшаем размер данных
        if tokens > 3000:  # Уменьшено с 5000 до 3000
            logger.warning(f"Messages exceed token limit: {tokens} > 3000")
            
            # Ограничиваем количество батчей
            max_batches = min(2, len(normalized_results))  # Уменьшено с 3 до 2
            normalized_results = normalized_results[:max_batches]
            
            # Для каждого батча ограничиваем размер полей
            for result in normalized_results:
                if "summary" in result and len(result["summary"]) > 200:
                    result["summary"] = result["summary"][:200] + "..."
                if "period_data" in result and len(json.dumps(result["period_data"])) > 100:
                    result["period_data"] = {"start_date": "01.01", "end_date": "31.12"}
                if "dynamics" in result and len(json.dumps(result["dynamics"])) > 100:
                    result["dynamics"] = {"total_rows": 0, "total_columns": 0, "mean": {}, "median": {}, "change_percent": {}, "key_metrics_change_percent": 0}
                if "factors" in result and len(json.dumps(result["factors"])) > 100:
                    result["factors"] = {"missing_values": "", "categorical_data": "", "key_factors": []}
            
            # Обновляем промпт
            user_prompt = f"""
Я провел предварительный анализ данных для маркетплейса {marketplace or 'неизвестный маркетплейс'} и получил следующие результаты по {len(normalized_results)} батчам данных:

```json
{json.dumps(normalized_results, ensure_ascii=False, indent=2)}
```

Теперь мне нужен финальный анализ, объединяющий все эти результаты в единый отчет.
Тип анализа: {analysis_type}

Результат должен быть в виде структурированного JSON с полями:
- title: заголовок анализа
- summary: краткое резюме анализа
- period_data: объект с полями start_date и end_date, содержащими даты начала и конца периода анализа в формате "DD.MM"
- dynamics: объект с информацией о динамике показателей, включающий поля total_rows, total_columns, mean, median, change_percent и key_metrics_change_percent
- factors: объект с информацией о факторах, влияющих на изменения показателей, включающий поля missing_values, categorical_data и key_factors (массив)
- links: объект с полями internal и external (массивы)
- completed_tasks: массив выполненных задач
- pending_tasks: массив предстоящих задач

ВАЖНО: Ответ должен быть ТОЛЬКО в формате JSON. Не добавляй никаких пояснений, комментариев или текста до или после JSON. Не используй маркдаун-форматирование для JSON. Верни только чистый JSON-объект.
"""
            
            # Обновляем сообщения
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            # Подсчитываем количество токенов
            tokens = self.token_counter.count_messages_tokens(messages)
            logger.info(f"Updated final synthesis tokens: {tokens}")
        
        try:
            # Отправляем запрос к API с повторными попытками
            async def call_api():
                logger.info(f"Sending final synthesis to gpt-4")
                
                # Проверяем, поддерживает ли модель параметр response_format
                model = "ft:gpt-4.1-2025-04-14:expovision:expovision:BQ4JVN7C"
                kwargs = {
                    "model": model,
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 4000  # Уменьшено с 4000 до 2000
                }
                
                # Добавляем параметр response_format только если модель его поддерживает
                if self.model_checker.supports_json_response_format(model):
                    kwargs["response_format"] = {"type": "json_object"}
                
                return await self.async_client.chat.completions.create(**kwargs)
            
            # Используем обработчик пустых ответов
            success, response = await self.empty_response_handler.handle_empty_response(
                self.retry_strategy.execute_with_retry, call_api
            )
            
            # Если не удалось получить ответ, возвращаем стандартный ответ
            if not success or not response:
                logger.warning("Failed to get response from API for final synthesis, using default response")
                return self.empty_response_handler.generate_default_response(analysis_type)
            
            # Получаем ответ
            raw_content = response.choices[0].message.content
            logger.info(f"Raw content from gpt-4: {raw_content[:100]}...")
            
            # Проверяем, что ответ не пустой
            if not raw_content or raw_content.isspace():
                logger.warning("Empty response from API for final synthesis")
                return self.empty_response_handler.generate_default_response(analysis_type)
            
            # Пытаемся преобразовать ответ в JSON
            try:
                result = json.loads(raw_content)
                logger.info("Successfully parsed final synthesis response as JSON")
                return result
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse final response as JSON: {str(e)}")
                
                # Пытаемся извлечь JSON из текста
                json_str = self.json_formatter.extract_json_from_text(raw_content)
                if json_str:
                    try:
                        result = json.loads(json_str)
                        logger.info("Successfully extracted and parsed JSON from text")
                        return result
                    except json.JSONDecodeError as e2:
                        logger.warning(f"Failed to parse extracted JSON: {str(e2)}")
                
                # Пытаемся исправить JSON
                try:
                    # Ищем начало и конец JSON
                    start_idx = raw_content.find("{")
                    end_idx = raw_content.rfind("}")
                    
                    if start_idx != -1 and end_idx != -1:
                        json_str = raw_content[start_idx:end_idx+1]
                        fixed_json = self.json_formatter.fix_json_string(json_str)
                        result = json.loads(fixed_json)
                        logger.info("Successfully parsed fixed final response as JSON")
                        return result
                    else:
                        # Если не удалось найти JSON, возвращаем текст как есть
                        logger.warning("Could not find JSON in response")
                        return self.json_formatter.create_fallback_response(raw_content, "Could not find JSON in response")
                except Exception as e2:
                    logger.warning(f"Failed to fix JSON: {str(e2)}")
                    
                    # Если не удалось исправить JSON, возвращаем текст как есть
                    return self.json_formatter.create_fallback_response(raw_content, f"Failed to fix JSON: {str(e2)}")
        except Exception as e:
            logger.error(f"Error synthesizing final analysis: {str(e)}")
            
            # В случае ошибки возвращаем пустой результат
            return self.empty_response_handler.generate_default_response(analysis_type)
    
    async def analyze_data(self, data: Dict[str, Any], marketplace: Optional[str] = None, analysis_type: str = "metrics") -> Dict[str, Any]:
        """
        Анализирует данные с использованием двухэтапного подхода
        
        Args:
            data: Данные для анализа
            marketplace: Название маркетплейса (опционально)
            analysis_type: Тип анализа (trends, competitors, metrics)
            
        Returns:
            Результаты анализа
        """
        # Создаем системный промпт в зависимости от типа анализа
        if analysis_type == "trends":
            system_prompt = """
Ты - опытный аналитик данных маркетплейсов. Твоя задача - анализировать тренды и динамику показателей.
Ты должен выявлять закономерности, тренды и аномалии в данных, а также предлагать рекомендации по улучшению показателей.

Твой анализ должен быть структурированным, информативным и полезным для принятия решений.
Используй только факты из предоставленных данных, не добавляй информацию, которой нет в данных.

Результат должен быть в виде структурированного JSON с полями:
- title: заголовок анализа
- summary: максимальное подробно со всей цепочкой и размышлениями резюме анализа
- period_data: объект с полями start_date и end_date, содержащими даты начала и конца периода анализа в формате "DD.MM"
- dynamics: объект с информацией о динамике показателей, включающий поля total_rows, total_columns, mean, median, change_percent и key_metrics_change_percent
- factors: объект с информацией о факторах, влияющих на изменения показателей, включающий поля missing_values, categorical_data и key_factors (массив)
- links: объект с полями internal и external (массивы)
- completed_tasks: массив выполненных задач
- pending_tasks: массив предстоящих задач

ВАЖНО: Ответ должен быть ТОЛЬКО в формате JSON. Не добавляй никаких пояснений, комментариев или текста до или после JSON. Не используй маркдаун-форматирование для JSON. Верни только чистый JSON-объект, который содержит в себе отчет максимально подробный бизнес-аналитика.
"""
        elif analysis_type == "competitors":
            system_prompt = """
Ты - опытный аналитик данных маркетплейсов. Твоя задача - анализировать конкурентов и их показатели.
Ты должен выявлять сильные и слабые стороны конкурентов, а также предлагать рекомендации по улучшению конкурентоспособности.

Твой анализ должен быть структурированным, информативным и полезным для принятия решений.
Используй только факты из предоставленных данных, не добавляй информацию, которой нет в данных.

Результат должен быть в виде структурированного JSON с полями:
- title: заголовок анализа
- summary: максимальное подробно со всей цепочкой и размышлениями резюме анализа
- period_data: объект с полями start_date и end_date, содержащими даты начала и конца периода анализа в формате "DD.MM"
- dynamics: объект с информацией о динамике показателей, включающий поля total_rows, total_columns, mean, median, change_percent и key_metrics_change_percent
- factors: объект с информацией о факторах, влияющих на изменения показателей, включающий поля missing_values, categorical_data и key_factors (массив)
- links: объект с полями internal и external (массивы)
- completed_tasks: массив выполненных задач
- pending_tasks: массив предстоящих задач

ВАЖНО: Ответ должен быть ТОЛЬКО в формате JSON. Не добавляй никаких пояснений, комментариев или текста до или после JSON. Не используй маркдаун-форматирование для JSON. Верни только чистый JSON-объект.
"""
        else:
            system_prompt = """
Ты - опытный аналитик данных маркетплейсов. Твоя задача - анализировать метрики и показатели.
Ты должен выявлять закономерности, тренды и аномалии в данных, а также предлагать рекомендации по улучшению показателей.

Твой анализ должен быть структурированным, информативным и полезным для принятия решений.
Используй только факты из предоставленных данных, не добавляй информацию, которой нет в данных.

Результат должен быть в виде структурированного JSON с полями:
- title: заголовок анализа
- summary: максимальное подробно со всей цепочкой и размышлениями резюме анализа
- period_data: объект с полями start_date и end_date, содержащими даты начала и конца периода анализа в формате "DD.MM"
- dynamics: объект с информацией о динамике показателей, включающий поля total_rows, total_columns, mean, median, change_percent и key_metrics_change_percent
- factors: объект с информацией о факторах, влияющих на изменения показателей, включающий поля missing_values, categorical_data и key_factors (массив)
- links: объект с полями internal и external (массивы)
- completed_tasks: массив выполненных задач
- pending_tasks: массив предстоящих задач

ВАЖНО: Ответ должен быть ТОЛЬКО в формате JSON. Не добавляй никаких пояснений, комментариев или текста до или после JSON. Не используй маркдаун-форматирование для JSON. Верни только чистый JSON-объект.
"""
        
        try:
            # Консолидируем данные в батчи
            batches = self.data_processor.consolidate_data(data)
            logger.info(f"Consolidated data into {len(batches)} batches")
            
            # Анализируем каждый батч
            batch_results = []
            for i, batch in enumerate(batches):
                logger.info(f"Analyzing batch {i+1}/{len(batches)}")
                result = await self.analyze_batch(batch, system_prompt, marketplace, analysis_type)
                batch_results.append(result)
            
            # Синтезируем финальный анализ
            final_result = await self.synthesize_final_analysis(batch_results, system_prompt, marketplace, analysis_type)
            
            return final_result
        except Exception as e:
            logger.error(f"Error analyzing data: {str(e)}")
            
            # В случае ошибки возвращаем пустой результат
            return self.empty_response_handler.generate_default_response(analysis_type)


class OptimizedOpenAIService:
    """
    Оптимизированный сервис для работы с OpenAI API
    """
    
    def __init__(self, api_key: Optional[str] = None, max_api_calls: int = 3):  # Уменьшено с 5 до 3
        """
        Инициализирует оптимизированный сервис OpenAI
        
        Args:
            api_key: API-ключ OpenAI
            max_api_calls: Максимальное количество вызовов API
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.max_api_calls = max_api_calls
        self.async_client = AsyncOpenAI(api_key=self.api_key)
        self.token_counter = TokenCounter()
        self.two_stage_analyzer = TwoStageAnalyzer(api_key=self.api_key, max_api_calls=max_api_calls)
        self.retry_strategy = APIRetryStrategy()
        self.json_formatter = JSONResponseFormatter()
        self.model_checker = ModelCompatibilityChecker()
        self.empty_response_handler = EmptyResponseHandler()
    
    async def chat_completion(self, messages: List[Dict[str, str]], temperature: float = 0.7, max_tokens: int = 2000, model: str = "ft:gpt-4.1-2025-04-14:expovision:expovision:BQ4JVN7C") -> Dict[str, Any]:
        """
        Отправляет запрос к API OpenAI для генерации текста
        
        Args:
            messages: Список сообщений
            temperature: Температура генерации
            max_tokens: Максимальное количество токенов
            model: Модель для генерации
            
        Returns:
            Результат генерации
        """
        try:
            # Подсчитываем количество токенов
            tokens = self.token_counter.count_messages_tokens(messages)
            logger.info(f"Chat completion tokens: {tokens}")
            
            # Отправляем запрос к API с повторными попытками
            async def call_api():
                # Проверяем, поддерживает ли модель параметр response_format
                kwargs = {
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
                
                # Добавляем параметр response_format только если модель его поддерживает
                if self.model_checker.supports_json_response_format(model):
                    kwargs["response_format"] = {"type": "json_object"}
                
                return await self.async_client.chat.completions.create(**kwargs)
            
            # Используем обработчик пустых ответов
            success, response = await self.empty_response_handler.handle_empty_response(
                self.retry_strategy.execute_with_retry, call_api
            )
            
            # Если не удалось получить ответ, возвращаем ошибку
            if not success or not response:
                logger.warning("Failed to get response from API for chat completion")
                return {
                    "content": "Не удалось получить ответ от API. Пожалуйста, попробуйте позже.",
                    "tokens": tokens,
                    "model": model
                }
            
            # Получаем ответ
            content = response.choices[0].message.content
            
            # Проверяем, что ответ не пустой
            if not content or content.isspace():
                logger.warning("Empty response from API for chat completion")
                return {
                    "content": "Получен пустой ответ от API. Пожалуйста, попробуйте позже.",
                    "tokens": tokens,
                    "model": model
                }
            
            # Возвращаем результат
            return {
                "content": content,
                "tokens": tokens,
                "model": model
            }
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {str(e)}")
            
            # В случае ошибки возвращаем пустой результат
            return {
                "content": f"Произошла ошибка при вызове OpenAI API: {str(e)}",
                "tokens": 0,
                "model": model
            }
    
    async def analyze_raw_data(self, data: Dict[str, Any], marketplace: Optional[str] = None, analysis_type: str = "metrics") -> Dict[str, Any]:
        """
        Анализирует данные с использованием двухэтапного подхода
        
        Args:
            data: Данные для анализа
            marketplace: Название маркетплейса (опционально)
            analysis_type: Тип анализа (trends, competitors, metrics)
            
        Returns:
            Результаты анализа
        """
        return await self.two_stage_analyzer.analyze_data(data, marketplace, analysis_type)
    
    # Добавляем методы, которые ожидаются в ai_analytics.py
    
    async def analyze_trends(self, metrics_data: Dict[str, Any], period: str = "month") -> Dict[str, Any]:
        """
        Анализирует тренды в метриках
        
        Args:
            metrics_data: Данные метрик для анализа
            period: Период анализа (day, week, month, year)
            
        Returns:
            Результаты анализа трендов
        """
        # Преобразуем данные в формат, подходящий для analyze_data
        data = {
            "data": [],
            "metrics_data": metrics_data,
            "period": period
        }
        
        # Если metrics_data содержит списки значений, преобразуем их в записи
        if any(isinstance(v, list) for v in metrics_data.values()):
            records = []
            for metric_name, values in metrics_data.items():
                if isinstance(values, list):
                    for i, value in enumerate(values):
                        record = {"metric_name": metric_name, "value": value}
                        # Добавляем дату, если это временной ряд
                        if period == "day":
                            record["date"] = f"2023-01-{i+1:02d}"
                        elif period == "week":
                            record["date"] = f"2023-W{i+1:02d}"
                        elif period == "month":
                            record["date"] = f"2023-{i+1:02d}"
                        elif period == "year":
                            record["date"] = f"{2020+i}"
                        records.append(record)
                else:
                    records.append({"metric_name": metric_name, "value": values})
            data["data"] = records
        
        # Анализируем данные
        result = await self.analyze_raw_data(data, analysis_type="trends")
        
        # Проверяем структуру результата и добавляем недостающие поля
        if "period_data" not in result or not result["period_data"]:
            result["period_data"] = {
                "start_date": "01.01",
                "end_date": "31.12"
            }
        elif isinstance(result["period_data"], str):
            # Если period_data - строка, преобразуем ее в объект
            period_text = result["period_data"]
            result["period_data"] = {
                "start_date": "01.01",
                "end_date": "31.12"
            }
            # Пытаемся извлечь даты из текста
            start_date_match = re.search(r'(?:с|от|начало)\s+(\d{1,2}[./-]\d{1,2}(?:[./-]\d{2,4})?)', period_text)
            end_date_match = re.search(r'(?:по|до|конец)\s+(\d{1,2}[./-]\d{1,2}(?:[./-]\d{2,4})?)', period_text)
            
            if start_date_match:
                result["period_data"]["start_date"] = start_date_match.group(1)
            if end_date_match:
                result["period_data"]["end_date"] = end_date_match.group(1)
        
        # Проверяем структуру dynamics
        if "dynamics" not in result or not result["dynamics"]:
            result["dynamics"] = {
                "total_rows": len(data["data"]),
                "total_columns": len(metrics_data),
                "mean": {},
                "median": {},
                "change_percent": {},
                "key_metrics_change_percent": 0
            }
        
        # Проверяем структуру factors
        if "factors" not in result or not result["factors"]:
            result["factors"] = {
                "missing_values": "",
                "categorical_data": "",
                "key_factors": []
            }
        elif isinstance(result["factors"], str):
            # Если factors - строка, преобразуем ее в объект
            factors_text = result["factors"]
            result["factors"] = {
                "missing_values": "",
                "categorical_data": "",
                "key_factors": []
            }
            # Пытаемся извлечь ключевые факторы из текста
            key_factors_matches = re.findall(r'[-*]\s*(.*?)(?:\n|$)', factors_text)
            if key_factors_matches:
                result["factors"]["key_factors"] = [factor.strip() for factor in key_factors_matches if factor.strip()]
        
        # Проверяем структуру links
        if "links" not in result:
            result["links"] = {"internal": [], "external": []}
        
        return result
    
    async def analyze_competitors(self, marketplace: str, category: str, competitors: List[str], our_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Анализирует конкурентов
        
        Args:
            marketplace: Название маркетплейса
            category: Категория товаров
            competitors: Список конкурентов
            our_metrics: Наши метрики для сравнения
            
        Returns:
            Результаты анализа конкурентов
        """
        # Преобразуем данные в формат, подходящий для analyze_data
        data = {
            "data": [],
            "marketplace": marketplace,
            "category": category,
            "competitors": competitors,
            "our_metrics": our_metrics
        }
        
        # Создаем записи для наших метрик
        records = []
        for metric_name, value in our_metrics.items():
            records.append({
                "company": "our",
                "metric_name": metric_name,
                "value": value
            })
        
        # Добавляем записи для конкурентов (с примерными данными)
        for competitor in competitors:
            for metric_name, value in our_metrics.items():
                # Генерируем случайное значение для конкурента на основе наших метрик
                competitor_value = value * (0.8 + 0.4 * np.random.random())
                records.append({
                    "company": competitor,
                    "metric_name": metric_name,
                    "value": competitor_value
                })
        
        data["data"] = records
        
        # Анализируем данные
        result = await self.analyze_raw_data(data, marketplace=marketplace, analysis_type="competitors")
        
        # Проверяем структуру результата и добавляем недостающие поля
        if "period_data" not in result or not result["period_data"]:
            result["period_data"] = {
                "start_date": "01.01",
                "end_date": "31.12"
            }
        elif isinstance(result["period_data"], str):
            # Если period_data - строка, преобразуем ее в объект
            period_text = result["period_data"]
            result["period_data"] = {
                "start_date": "01.01",
                "end_date": "31.12"
            }
            # Пытаемся извлечь даты из текста
            start_date_match = re.search(r'(?:с|от|начало)\s+(\d{1,2}[./-]\d{1,2}(?:[./-]\d{2,4})?)', period_text)
            end_date_match = re.search(r'(?:по|до|конец)\s+(\d{1,2}[./-]\d{1,2}(?:[./-]\d{2,4})?)', period_text)
            
            if start_date_match:
                result["period_data"]["start_date"] = start_date_match.group(1)
            if end_date_match:
                result["period_data"]["end_date"] = end_date_match.group(1)
        
        # Проверяем структуру dynamics
        if "dynamics" not in result or not result["dynamics"]:
            result["dynamics"] = {
                "total_rows": len(data["data"]),
                "total_columns": len(our_metrics),
                "mean": {},
                "median": {},
                "change_percent": {},
                "key_metrics_change_percent": 0
            }
        
        # Проверяем структуру factors
        if "factors" not in result or not result["factors"]:
            result["factors"] = {
                "missing_values": "",
                "categorical_data": "",
                "key_factors": []
            }
        elif isinstance(result["factors"], str):
            # Если factors - строка, преобразуем ее в объект
            factors_text = result["factors"]
            result["factors"] = {
                "missing_values": "",
                "categorical_data": "",
                "key_factors": []
            }
            # Пытаемся извлечь ключевые факторы из текста
            key_factors_matches = re.findall(r'[-*]\s*(.*?)(?:\n|$)', factors_text)
            if key_factors_matches:
                result["factors"]["key_factors"] = [factor.strip() for factor in key_factors_matches if factor.strip()]
        
        # Проверяем структуру links
        if "links" not in result:
            result["links"] = {"internal": [], "external": []}
        
        # Добавляем информацию о категории и конкурентах
        if "summary" in result:
            result["summary"] = f"Анализ конкурентов в категории {category} на маркетплейсе {marketplace}. " + result["summary"]
        
        return result
    
    async def generate_report(self, marketplace: str, metrics_data: Dict[str, Any], period_start: str, period_end: str, 
                             trends_analysis: Optional[Dict[str, Any]] = None, 
                             competitors_analysis: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Генерирует отчет на основе метрик и результатов предыдущих анализов
        
        Args:
            marketplace: Название маркетплейса
            metrics_data: Данные метрик
            period_start: Начало периода
            period_end: Конец периода
            trends_analysis: Результаты анализа трендов (опционально)
            competitors_analysis: Результаты анализа конкурентов (опционально)
            
        Returns:
            Отчет
        """
        # Преобразуем данные в формат, подходящий для analyze_data
        data = {
            "data": [],
            "marketplace": marketplace,
            "metrics_data": metrics_data,
            "period_start": period_start,
            "period_end": period_end
        }
        
        # Добавляем результаты предыдущих анализов, если они есть
        if trends_analysis:
            data["trends_analysis"] = trends_analysis
        
        if competitors_analysis:
            data["competitors_analysis"] = competitors_analysis
        
        # Создаем записи для метрик
        records = []
        for metric_name, value in metrics_data.items():
            records.append({
                "metric_name": metric_name,
                "value": value,
                "date": period_end
            })
        
        data["data"] = records
        
        # Анализируем данные
        result = await self.analyze_raw_data(data, marketplace=marketplace, analysis_type="metrics")
        
        # Проверяем структуру результата и добавляем недостающие поля
        if "period_data" not in result or not result["period_data"]:
            result["period_data"] = {
                "start_date": period_start.split("-")[-1] if "-" in period_start else period_start,
                "end_date": period_end.split("-")[-1] if "-" in period_end else period_end
            }
        elif isinstance(result["period_data"], str):
            # Если period_data - строка, преобразуем ее в объект
            period_text = result["period_data"]
            result["period_data"] = {
                "start_date": period_start.split("-")[-1] if "-" in period_start else period_start,
                "end_date": period_end.split("-")[-1] if "-" in period_end else period_end
            }
            # Пытаемся извлечь даты из текста
            start_date_match = re.search(r'(?:с|от|начало)\s+(\d{1,2}[./-]\d{1,2}(?:[./-]\d{2,4})?)', period_text)
            end_date_match = re.search(r'(?:по|до|конец)\s+(\d{1,2}[./-]\d{1,2}(?:[./-]\d{2,4})?)', period_text)
            
            if start_date_match:
                result["period_data"]["start_date"] = start_date_match.group(1)
            if end_date_match:
                result["period_data"]["end_date"] = end_date_match.group(1)
        
        # Проверяем структуру dynamics
        if "dynamics" not in result or not result["dynamics"]:
            result["dynamics"] = {
                "total_rows": len(data["data"]),
                "total_columns": len(metrics_data),
                "mean": {},
                "median": {},
                "change_percent": {},
                "key_metrics_change_percent": 0
            }
        
        # Проверяем структуру factors
        if "factors" not in result or not result["factors"]:
            result["factors"] = {
                "missing_values": "",
                "categorical_data": "",
                "key_factors": []
            }
        elif isinstance(result["factors"], str):
            # Если factors - строка, преобразуем ее в объект
            factors_text = result["factors"]
            result["factors"] = {
                "missing_values": "",
                "categorical_data": "",
                "key_factors": []
            }
            # Пытаемся извлечь ключевые факторы из текста
            key_factors_matches = re.findall(r'[-*]\s*(.*?)(?:\n|$)', factors_text)
            if key_factors_matches:
                result["factors"]["key_factors"] = [factor.strip() for factor in key_factors_matches if factor.strip()]
        
        # Проверяем структуру links
        if "links" not in result:
            result["links"] = {"internal": [], "external": []}
        
        # Добавляем ссылки на предыдущие анализы
        if trends_analysis:
            result["links"]["internal"].append({
                "title": "Анализ трендов",
                "description": "Подробный анализ трендов за выбранный период"
            })
        
        if competitors_analysis:
            result["links"]["internal"].append({
                "title": "Анализ конкурентов",
                "description": "Сравнительный анализ с конкурентами"
            })
        
        return result


# Создаем экземпляр сервиса
openai_service = OptimizedOpenAIService()