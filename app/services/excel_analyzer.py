import pandas as pd
import numpy as np
import json
import logging
import asyncio
import time
import os
from typing import Dict, List, Any, Optional, Union

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Импортируем оптимизированный OpenAI сервис
from optimized_openai_service import OpenAIService, DataPreprocessor

class ExcelAnalyzer:
    """
    Класс для анализа Excel-файлов с использованием оптимизированного OpenAI сервиса
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Инициализирует анализатор Excel-файлов
        
        Args:
            api_key: API-ключ OpenAI (опционально)
        """
        self.openai_service = OpenAIService(api_key=api_key)
        self.preprocessor = DataPreprocessor()
    
    def load_excel_file(self, file_path: str) -> pd.DataFrame:
        """
        Загружает Excel-файл в DataFrame
        
        Args:
            file_path: Путь к Excel-файлу
            
        Returns:
            DataFrame с данными из Excel-файла
        """
        logger.info(f"Loading Excel file: {file_path}")
        
        try:
            # Определяем, есть ли заголовки в файле
            df_raw = pd.read_excel(file_path, header=None)
            
            # Автоопределение строки заголовков
            best_idx = -1
            max_frac = 0.0
            for idx, row in df_raw.iterrows():
                non_empty = row.dropna()
                if non_empty.empty:
                    continue
                is_str = non_empty.apply(lambda x: isinstance(x, str))
                frac = is_str.sum() / len(non_empty)
                if frac > 0.7 and frac > max_frac:
                    max_frac = frac
                    best_idx = idx
            
            if best_idx < 0:
                # Если не удалось определить строку с заголовками, используем первую строку
                df = pd.read_excel(file_path)
            else:
                # Используем найденную строку как заголовки
                df = pd.read_excel(file_path, header=best_idx)
            
            logger.info(f"Successfully loaded Excel file with {len(df)} rows and {len(df.columns)} columns")
            return df
        except Exception as e:
            logger.error(f"Error loading Excel file: {str(e)}")
            raise
    
    def prepare_data_for_analysis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Подготавливает данные из DataFrame для анализа
        
        Args:
            df: DataFrame с данными
            
        Returns:
            Словарь с подготовленными данными
        """
        logger.info("Preparing data for analysis")
        
        try:
            # Оптимизируем DataFrame
            df_opt = self.preprocessor.optimize_data(df)
            
            # Преобразуем DataFrame в словарь
            data = {
                "data": df_opt.to_dict(orient='records'),
                "columns": list(df_opt.columns),
                "rows_count": len(df_opt),
                "columns_count": len(df_opt.columns)
            }
            
            # Добавляем базовую статистику
            numeric_cols = df_opt.select_dtypes(include=['number']).columns
            if len(numeric_cols) > 0:
                data["numeric_stats"] = {}
                for col in numeric_cols:
                    data["numeric_stats"][col] = {
                        "mean": float(df_opt[col].mean()),
                        "median": float(df_opt[col].median()),
                        "min": float(df_opt[col].min()),
                        "max": float(df_opt[col].max()),
                        "sum": float(df_opt[col].sum())
                    }
            
            # Добавляем информацию о категориальных колонках
            categorical_cols = df_opt.select_dtypes(include=['object', 'category']).columns
            if len(categorical_cols) > 0:
                data["categorical_stats"] = {}
                for col in categorical_cols:
                    if df_opt[col].nunique() < 50:  # Только если не слишком много уникальных значений
                        data["categorical_stats"][col] = df_opt[col].value_counts().to_dict()
            
            logger.info("Data prepared for analysis")
            return data
        except Exception as e:
            logger.error(f"Error preparing data for analysis: {str(e)}")
            raise
    
    def detect_marketplace(self, df: pd.DataFrame) -> Optional[str]:
        """
        Определяет маркетплейс на основе данных
        
        Args:
            df: DataFrame с данными
            
        Returns:
            Название маркетплейса или None, если не удалось определить
        """
        # Проверяем названия колонок
        columns = [col.lower() for col in df.columns]
        
        # Проверяем наличие ключевых слов для разных маркетплейсов
        if any(kw in ' '.join(columns) for kw in ['ozon', 'озон']):
            return 'Ozon'
        elif any(kw in ' '.join(columns) for kw in ['wildberries', 'вайлдберриз', 'вб', 'wb']):
            return 'Wildberries'
        elif any(kw in ' '.join(columns) for kw in ['яндекс', 'yandex', 'маркет']):
            return 'Яндекс.Маркет'
        elif any(kw in ' '.join(columns) for kw in ['aliexpress', 'али', 'tmall']):
            return 'AliExpress'
        elif any(kw in ' '.join(columns) for kw in ['amazon', 'амазон']):
            return 'Amazon'
        elif any(kw in ' '.join(columns) for kw in ['сбер', 'sber', 'мегамаркет']):
            return 'СберМегаМаркет'
        
        # Проверяем содержимое ячеек
        sample_text = ' '.join(df.select_dtypes(include=['object']).values.flatten().astype(str)[:1000])
        if 'ozon' in sample_text.lower() or 'озон' in sample_text.lower():
            return 'Ozon'
        elif 'wildberries' in sample_text.lower() or 'вайлдберриз' in sample_text.lower():
            return 'Wildberries'
        elif 'яндекс' in sample_text.lower() or 'маркет' in sample_text.lower():
            return 'Яндекс.Маркет'
        
        # Если не удалось определить
        return None
    
    def detect_analysis_type(self, df: pd.DataFrame) -> str:
        """
        Определяет тип анализа на основе данных
        
        Args:
            df: DataFrame с данными
            
        Returns:
            Тип анализа (trends, competitors, metrics)
        """
        columns = [col.lower() for col in df.columns]
        
        # Проверяем наличие временных колонок для анализа трендов
        date_columns = [col for col in columns if any(kw in col for kw in ['date', 'дата', 'день', 'неделя', 'месяц', 'год', 'period', 'период'])]
        if date_columns and any(col for col in columns if any(kw in col for kw in ['trend', 'тренд', 'динамика', 'рост', 'падение'])):
            return 'trends'
        
        # Проверяем наличие колонок с конкурентами
        if any(kw in ' '.join(columns) for kw in ['competitor', 'конкурент', 'сравнение']):
            return 'competitors'
        
        # По умолчанию - анализ метрик
        return 'metrics'
    
    async def analyze_excel_file(self, file_path: str) -> Dict[str, Any]:
        """
        Анализирует Excel-файл с использованием OpenAI API
        
        Args:
            file_path: Путь к Excel-файлу
            
        Returns:
            Результаты анализа
        """
        logger.info(f"Starting analysis of Excel file: {file_path}")
        
        try:
            # Загружаем Excel-файл
            df = self.load_excel_file(file_path)
            
            # Определяем маркетплейс
            marketplace = self.detect_marketplace(df)
            logger.info(f"Detected marketplace: {marketplace}")
            
            # Определяем тип анализа
            analysis_type = self.detect_analysis_type(df)
            logger.info(f"Detected analysis type: {analysis_type}")
            
            # Подготавливаем данные для анализа
            data = self.prepare_data_for_analysis(df)
            
            # Засекаем время начала анализа
            start_time = time.time()
            
            # Анализируем данные
            result = await self.openai_service.analyze_raw_data(data, marketplace=marketplace, analysis_type=analysis_type)
            
            # Вычисляем время выполнения
            execution_time = time.time() - start_time
            logger.info(f"Analysis completed in {execution_time:.2f} seconds")
            
            # Добавляем метаданные к результату
            result["metadata"] = {
                "file_name": os.path.basename(file_path),
                "marketplace": marketplace,
                "analysis_type": analysis_type,
                "execution_time": execution_time,
                "rows_count": data["rows_count"],
                "columns_count": data["columns_count"]
            }
            
            return result
        except Exception as e:
            logger.error(f"Error analyzing Excel file: {str(e)}")
            return {"error": f"Error analyzing Excel file: {str(e)}"}


async def main():
    """
    Основная функция для тестирования анализатора Excel-файлов
    """
    # Путь к Excel-файлу
    file_path = "/home/ubuntu/upload/Новая таблица.xlsx"
    
    # API-ключ OpenAI
    api_key = "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"
    
    # Создаем анализатор Excel-файлов
    analyzer = ExcelAnalyzer(api_key=api_key)
    
    # Анализируем Excel-файл
    result = await analyzer.analyze_excel_file(file_path)
    
    # Сохраняем результат в файл
    with open("/home/ubuntu/analysis_result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print("Analysis completed. Results saved to analysis_result.json")


if __name__ == "__main__":
    asyncio.run(main())
