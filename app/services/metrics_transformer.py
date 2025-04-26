import pandas as pd
import numpy as np
import re
import logging
from typing import Dict, List, Any, Tuple, Optional, Union

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MetricsTransformer:
    """
    Класс для преобразования таблиц с метриками в строках в формат с метриками в столбцах
    и улучшенной обработки данных для анализа
    """
    
    def __init__(self):
        """
        Инициализирует трансформер метрик
        """
        # Шаблоны для распознавания метрик
        self.metric_patterns = {
            'выкупы': r'выкуп|выкуп\w+',
            'заказы': r'заказ|заказ\w+',
            'конверсия': r'конверс|конверс\w+',
            'динамика': r'динам|динам\w+',
            'скидки': r'скидк|скидк\w+',
            'процент': r'%|процент|доля',
            'цена': r'цен\w+|стоимост|руб'
        }
        
        # Шаблоны для распознавания единиц измерения
        self.unit_patterns = {
            'рубли': r'руб|\₽',
            'штуки': r'шт',
            'проценты': r'%|п\.п\.',
            'количество': r'кол-во|количество'
        }
        
        # Шаблоны для распознавания периодов
        self.period_patterns = {
            'день': r'день|дн\.|д\.',
            'неделя': r'недел|нед\.|н\.|w\d+',
            'месяц': r'месяц|мес\.|м\.',
            'год': r'год|г\.'
        }
        
        # Шаблоны для распознавания дат
        self.date_patterns = [
            r'\d{1,2}[./-]\d{1,2}[./-]\d{2,4}',  # DD.MM.YYYY, DD/MM/YYYY, DD-MM-YYYY
            r'\d{2,4}[./-]\d{1,2}[./-]\d{1,2}',  # YYYY.MM.DD, YYYY/MM/DD, YYYY-MM-DD
            r'\d{1,2}[./-]\d{1,2}',              # DD.MM, DD/MM, DD-MM
            r'\d{1,2}\s+[а-яА-Я]+',              # DD месяц
            r'[а-яА-Я]+\s+\d{1,2}'               # месяц DD
        ]
    
    def detect_table_structure(self, df: pd.DataFrame) -> str:
        """
        Определяет структуру таблицы (стандартная или транспонированная)
        
        Args:
            df: DataFrame для анализа
            
        Returns:
            Тип структуры таблицы: 'standard' или 'transposed'
        """
        logger.info("Определение структуры таблицы")
        
        # Проверяем заголовки столбцов
        column_headers = df.columns.tolist()
        column_headers_str = ' '.join([str(h).lower() for h in column_headers])
        
        # Проверяем первые несколько строк
        first_rows = []
        for i in range(min(10, len(df))):
            row_values = df.iloc[i].tolist()
            row_str = ' '.join([str(v).lower() for v in row_values if pd.notna(v)])
            first_rows.append(row_str)
        
        first_rows_str = ' '.join(first_rows)
        
        # Подсчитываем количество метрик в заголовках и в первых строках
        metrics_in_headers = sum(1 for pattern in self.metric_patterns.values() 
                                if re.search(pattern, column_headers_str))
        
        metrics_in_rows = sum(1 for pattern in self.metric_patterns.values() 
                             if re.search(pattern, first_rows_str))
        
        # Проверяем наличие дат в заголовках
        dates_in_headers = 0
        for header in column_headers:
            header_str = str(header).lower()
            for pattern in self.date_patterns:
                if re.search(pattern, header_str):
                    dates_in_headers += 1
                    break
        
        # Если в заголовках больше метрик, чем в строках, то структура стандартная
        # Если в строках больше метрик, чем в заголовках, то структура транспонированная
        # Если в заголовках много дат, то структура, вероятно, транспонированная
        if metrics_in_headers > metrics_in_rows and dates_in_headers < len(column_headers) / 3:
            logger.info("Определена стандартная структура таблицы")
            return 'standard'
        else:
            logger.info("Определена транспонированная структура таблицы")
            return 'transposed'
    
    def identify_metric_rows(self, df: pd.DataFrame) -> Dict[int, Dict[str, Any]]:
        """
        Идентифицирует строки с метриками и их характеристики
        
        Args:
            df: DataFrame для анализа
            
        Returns:
            Словарь с индексами строк с метриками и их характеристиками
        """
        logger.info("Идентификация строк с метриками")
        
        metric_rows = {}
        
        for i, row in df.iterrows():
            # Преобразуем строку в строковый формат для поиска
            row_str = ' '.join([str(v).lower() for v in row.values if pd.notna(v)])
            
            # Проверяем наличие метрик в строке
            metric_type = None
            for metric_name, pattern in self.metric_patterns.items():
                if re.search(pattern, row_str):
                    metric_type = metric_name
                    break
            
            if metric_type:
                # Определяем единицу измерения
                unit = None
                for unit_name, pattern in self.unit_patterns.items():
                    if re.search(pattern, row_str):
                        unit = unit_name
                        break
                
                # Определяем название метрики
                metric_name = None
                for j, value in enumerate(row.values):
                    if pd.notna(value) and isinstance(value, str) and len(value) > 3:
                        # Проверяем, что это не просто числовое значение
                        if not re.match(r'^[\d\s,.%]+$', value):
                            metric_name = value
                            break
                
                # Если не нашли название, используем первое непустое значение
                if not metric_name:
                    for value in row.values:
                        if pd.notna(value):
                            metric_name = str(value)
                            break
                
                # Сохраняем информацию о метрике
                metric_rows[i] = {
                    'type': metric_type,
                    'unit': unit,
                    'name': metric_name,
                    'values': [v for v in row.values if pd.notna(v) and isinstance(v, (int, float)) or 
                              (isinstance(v, str) and re.match(r'^[\d\s,.%]+$', v))]
                }
        
        logger.info(f"Найдено {len(metric_rows)} строк с метриками")
        return metric_rows
    
    def identify_date_columns(self, df: pd.DataFrame) -> Dict[int, str]:
        """
        Идентифицирует столбцы с датами или периодами
        
        Args:
            df: DataFrame для анализа
            
        Returns:
            Словарь с индексами столбцов с датами и их значениями
        """
        logger.info("Идентификация столбцов с датами")
        
        date_columns = {}
        
        # Проверяем заголовки столбцов
        for j, header in enumerate(df.columns):
            header_str = str(header).lower()
            
            # Проверяем наличие дат в заголовке
            for pattern in self.date_patterns:
                if re.search(pattern, header_str):
                    date_columns[j] = header
                    break
            
            # Проверяем наличие периодов в заголовке
            if j not in date_columns:
                for period_name, pattern in self.period_patterns.items():
                    if re.search(pattern, header_str):
                        date_columns[j] = header
                        break
        
        # Если не нашли даты в заголовках, проверяем первую строку
        if not date_columns and len(df) > 0:
            first_row = df.iloc[0]
            for j, value in enumerate(first_row):
                if pd.notna(value):
                    value_str = str(value).lower()
                    
                    # Проверяем наличие дат в значении
                    for pattern in self.date_patterns:
                        if re.search(pattern, value_str):
                            date_columns[j] = value
                            break
                    
                    # Проверяем наличие периодов в значении
                    if j not in date_columns:
                        for period_name, pattern in self.period_patterns.items():
                            if re.search(pattern, value_str):
                                date_columns[j] = value
                                break
        
        logger.info(f"Найдено {len(date_columns)} столбцов с датами")
        return date_columns
    
    def transform_transposed_table(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Преобразует транспонированную таблицу в стандартный формат
        
        Args:
            df: DataFrame для преобразования
            
        Returns:
            Преобразованный DataFrame
        """
        logger.info("Преобразование транспонированной таблицы")
        
        # Идентифицируем строки с метриками
        metric_rows = self.identify_metric_rows(df)
        
        if not metric_rows:
            logger.warning("Не найдены строки с метриками, возвращаем исходную таблицу")
            return df
        
        # Идентифицируем столбцы с датами
        date_columns = self.identify_date_columns(df)
        
        # Создаем новый DataFrame
        new_data = []
        
        # Для каждой даты создаем строку с метриками
        for j in range(len(df.columns)):
            if j in date_columns:
                date_value = date_columns[j]
                
                # Создаем словарь для новой строки
                new_row = {'date': date_value}
                
                # Добавляем значения метрик
                for i, metric_info in metric_rows.items():
                    if j < len(df.iloc[i]) and pd.notna(df.iloc[i, j]):
                        # Пытаемся преобразовать значение в число
                        try:
                            value = df.iloc[i, j]
                            if isinstance(value, str):
                                # Удаляем пробелы, заменяем запятые на точки
                                value = value.replace(' ', '').replace(',', '.')
                                # Удаляем символы процентов
                                value = value.replace('%', '')
                                # Преобразуем в число
                                value = float(value)
                            new_row[metric_info['name']] = value
                        except (ValueError, TypeError):
                            # Если не удалось преобразовать, оставляем как есть
                            new_row[metric_info['name']] = df.iloc[i, j]
                
                # Добавляем строку в новые данные
                new_data.append(new_row)
        
        # Создаем новый DataFrame
        new_df = pd.DataFrame(new_data)
        
        # Добавляем информацию о метриках
        metric_info = {}
        for i, info in metric_rows.items():
            metric_info[info['name']] = {
                'type': info['type'],
                'unit': info['unit']
            }
        
        # Сохраняем информацию о метриках в атрибуте DataFrame
        new_df.attrs['metric_info'] = metric_info
        
        logger.info(f"Создан новый DataFrame с {len(new_df)} строками и {len(new_df.columns)} столбцами")
        return new_df
    
    def clean_and_convert_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Очищает и преобразует данные для анализа
        
        Args:
            df: DataFrame для очистки и преобразования
            
        Returns:
            Очищенный и преобразованный DataFrame
        """
        logger.info("Очистка и преобразование данных")
        
        # Создаем копию DataFrame
        df_clean = df.copy()
        
        # Преобразуем столбцы с датами
        date_columns = []
        for col in df_clean.columns:
            col_str = str(col).lower()
            if 'дата' in col_str or 'date' in col_str:
                try:
                    df_clean[col] = pd.to_datetime(df_clean[col], errors='coerce')
                    date_columns.append(col)
                except:
                    pass
        
        # Преобразуем числовые столбцы
        for col in df_clean.columns:
            if col not in date_columns:
                # Проверяем, содержит ли столбец числовые значения
                numeric_values = 0
                for value in df_clean[col]:
                    if pd.notna(value):
                        if isinstance(value, (int, float)):
                            numeric_values += 1
                        elif isinstance(value, str):
                            # Проверяем, можно ли преобразовать строку в число
                            try:
                                # Удаляем пробелы, заменяем запятые на точки
                                value_clean = value.replace(' ', '').replace(',', '.')
                                # Удаляем символы процентов
                                value_clean = value_clean.replace('%', '')
                                float(value_clean)
                                numeric_values += 1
                            except (ValueError, TypeError):
                                pass
                
                # Если более 50% значений числовые, преобразуем столбец
                if numeric_values > 0.5 * df_clean[col].count():
                    # Преобразуем столбец в числовой формат
                    df_clean[col] = df_clean[col].apply(lambda x: self._convert_to_numeric(x))
        
        # Удаляем строки, где все значения NaN
        df_clean = df_clean.dropna(how='all')
        
        # Удаляем столбцы, где все значения NaN
        df_clean = df_clean.dropna(axis=1, how='all')
        
        logger.info(f"После очистки: {len(df_clean)} строк и {len(df_clean.columns)} столбцов")
        return df_clean
    
    def _convert_to_numeric(self, value) -> Optional[float]:
        """
        Преобразует значение в числовой формат
        
        Args:
            value: Значение для преобразования
            
        Returns:
            Числовое значение или None, если преобразование невозможно
        """
        if pd.isna(value):
            return None
        
        if isinstance(value, (int, float)):
            return float(value)
        
        if isinstance(value, str):
            # Удаляем пробелы, заменяем запятые на точки
            value_clean = value.replace(' ', '').replace(',', '.')
            # Удаляем символы процентов
            value_clean = value_clean.replace('%', '')
            
            try:
                return float(value_clean)
            except (ValueError, TypeError):
                return None
        
        return None
    
    def process_excel_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Обрабатывает данные из Excel-файла для анализа
        
        Args:
            df: DataFrame с данными из Excel-файла
            
        Returns:
            Словарь с обработанными данными для анализа
        """
        logger.info("Обработка данных из Excel-файла")
        
        # Определяем структуру таблицы
        structure = self.detect_table_structure(df)
        
        # Если структура транспонированная, преобразуем таблицу
        if structure == 'transposed':
            df_transformed = self.transform_transposed_table(df)
        else:
            df_transformed = df
        
        # Очищаем и преобразуем данные
        df_clean = self.clean_and_convert_data(df_transformed)
        
        # Подготавливаем данные для анализа
        result = {
            'original_structure': structure,
            'rows_count': len(df_clean),
            'columns_count': len(df_clean.columns),
            'columns': list(df_clean.columns),
            'data_types': {c: str(df_clean[c].dtype) for c in df_clean.columns},
            'missing_values': {c: int(df_clean[c].isna().sum()) for c in df_clean.columns},
            'sample_rows': df_clean.head(5).to_dict(orient='records')
        }
        
        # Добавляем информацию о метриках, если она есть
        if hasattr(df_clean, 'attrs') and 'metric_info' in df_clean.attrs:
            result['metric_info'] = df_clean.attrs['metric_info']
        
        # Добавляем статистику по числовым столбцам
        numeric_cols = df_clean.select_dtypes(include=['number']).columns.tolist()
        if numeric_cols:
            result['numeric_stats'] = {}
            for col in numeric_cols:
                result['numeric_stats'][col] = {
                    'mean': float(df_clean[col].mean()),
                    'median': float(df_clean[col].median()),
                    'min': float(df_clean[col].min()),
                    'max': float(df_clean[col].max()),
                    'sum': float(df_clean[col].sum()),
                    'std': float(df_clean[col].std()),
                    'count': int(df_clean[col].count()),
                    'missing': int(df_clean[col].isna().sum())
                }
        
        # Добавляем данные для анализа
        result['data'] = df_clean.to_dict(orient='records')
        
        # Сохраняем преобразованный DataFrame
        result['transformed_df'] = df_clean
        
        logger.info("Данные успешно обработаны")
        return result


# Создаем экземпляр класса для использования
metrics_transformer = MetricsTransformer()
