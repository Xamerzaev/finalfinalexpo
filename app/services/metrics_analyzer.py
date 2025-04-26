import logging
import json
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from app.core.config import settings
from app.services.openai_service import openai_service

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MetricsAnalyzer:
    """
    Класс для расширенного анализа метрик
    """
    
    def __init__(self):
        """
        Инициализирует анализатор метрик
        """
        self.category_metrics = {}
        self.product_metrics = {}
        self.account_metrics = {}
        self.seasonal_patterns = {}
        
    def analyze_by_category(self, data: Dict[str, Any], category_column: str = "category") -> Dict[str, Any]:
        """
        Анализирует данные по категориям
        
        Args:
            data: Данные для анализа
            category_column: Название колонки с категориями
            
        Returns:
            Результаты анализа по категориям
        """
        try:
            logger.info(f"Analyzing data by category using column: {category_column}")
            
            # Проверяем, что данные содержат нужную колонку
            if "data" not in data or not data["data"]:
                logger.warning("No data provided for category analysis")
                return {"error": "No data provided for category analysis"}
            
            # Преобразуем данные в DataFrame
            df = pd.DataFrame(data["data"])
            
            # Проверяем наличие колонки с категориями
            if category_column not in df.columns:
                logger.warning(f"Category column '{category_column}' not found in data")
                return {"error": f"Category column '{category_column}' not found in data"}
            
            # Группируем данные по категориям
            category_groups = df.groupby(category_column)
            
            # Анализируем каждую категорию
            category_results = {}
            for category, group in category_groups:
                # Пропускаем пустые категории
                if pd.isna(category) or str(category).strip() == "":
                    continue
                
                # Преобразуем группу в словарь для анализа
                category_data = group.to_dict(orient='records')
                
                # Получаем базовую статистику по категории
                numeric_cols = group.select_dtypes(include=['number']).columns
                
                category_stats = {
                    "count": len(group),
                    "metrics": {}
                }
                
                # Добавляем статистику по числовым колонкам
                for col in numeric_cols:
                    category_stats["metrics"][col] = {
                        "mean": float(group[col].mean()),
                        "median": float(group[col].median()),
                        "min": float(group[col].min()),
                        "max": float(group[col].max()),
                        "sum": float(group[col].sum())
                    }
                
                # Сохраняем результаты для категории
                category_results[str(category)] = category_stats
            
            # Сохраняем результаты анализа по категориям
            self.category_metrics = category_results
            
            # Анализируем тренды по категориям с помощью OpenAI
            trends_analysis = self._analyze_category_trends(category_results)
            
            # Формируем итоговый результат
            result = {
                "category_metrics": category_results,
                "trends_analysis": trends_analysis
            }
            
            return result
        except Exception as e:
            logger.error(f"Error analyzing data by category: {str(e)}")
            return {"error": f"Error analyzing data by category: {str(e)}"}
    
    def analyze_by_product(self, data: Dict[str, Any], product_column: str = "product_id") -> Dict[str, Any]:
        """
        Анализирует данные по товарам
        
        Args:
            data: Данные для анализа
            product_column: Название колонки с идентификаторами товаров
            
        Returns:
            Результаты анализа по товарам
        """
        try:
            logger.info(f"Analyzing data by product using column: {product_column}")
            
            # Проверяем, что данные содержат нужную колонку
            if "data" not in data or not data["data"]:
                logger.warning("No data provided for product analysis")
                return {"error": "No data provided for product analysis"}
            
            # Преобразуем данные в DataFrame
            df = pd.DataFrame(data["data"])
            
            # Проверяем наличие колонки с товарами
            if product_column not in df.columns:
                logger.warning(f"Product column '{product_column}' not found in data")
                return {"error": f"Product column '{product_column}' not found in data"}
            
            # Группируем данные по товарам
            product_groups = df.groupby(product_column)
            
            # Анализируем каждый товар
            product_results = {}
            
            # Ограничиваем количество товаров для анализа
            top_products = min(100, len(product_groups))
            
            # Получаем топ товаров по количеству записей
            top_product_groups = sorted(
                [(product, group) for product, group in product_groups],
                key=lambda x: len(x[1]),
                reverse=True
            )[:top_products]
            
            for product, group in top_product_groups:
                # Пропускаем пустые идентификаторы товаров
                if pd.isna(product) or str(product).strip() == "":
                    continue
                
                # Преобразуем группу в словарь для анализа
                product_data = group.to_dict(orient='records')
                
                # Получаем базовую статистику по товару
                numeric_cols = group.select_dtypes(include=['number']).columns
                
                product_stats = {
                    "count": len(group),
                    "metrics": {}
                }
                
                # Добавляем статистику по числовым колонкам
                for col in numeric_cols:
                    product_stats["metrics"][col] = {
                        "mean": float(group[col].mean()),
                        "median": float(group[col].median()),
                        "min": float(group[col].min()),
                        "max": float(group[col].max()),
                        "sum": float(group[col].sum())
                    }
                
                # Сохраняем результаты для товара
                product_results[str(product)] = product_stats
            
            # Сохраняем результаты анализа по товарам
            self.product_metrics = product_results
            
            # Анализируем тренды по товарам с помощью OpenAI
            trends_analysis = self._analyze_product_trends(product_results)
            
            # Формируем итоговый результат
            result = {
                "product_metrics": product_results,
                "trends_analysis": trends_analysis
            }
            
            return result
        except Exception as e:
            logger.error(f"Error analyzing data by product: {str(e)}")
            return {"error": f"Error analyzing data by product: {str(e)}"}
    
    def analyze_by_account(self, data: Dict[str, Any], account_column: str = "account_id") -> Dict[str, Any]:
        """
        Анализирует данные по кабинетам
        
        Args:
            data: Данные для анализа
            account_column: Название колонки с идентификаторами кабинетов
            
        Returns:
            Результаты анализа по кабинетам
        """
        try:
            logger.info(f"Analyzing data by account using column: {account_column}")
            
            # Проверяем, что данные содержат нужную колонку
            if "data" not in data or not data["data"]:
                logger.warning("No data provided for account analysis")
                return {"error": "No data provided for account analysis"}
            
            # Преобразуем данные в DataFrame
            df = pd.DataFrame(data["data"])
            
            # Проверяем наличие колонки с кабинетами
            if account_column not in df.columns:
                logger.warning(f"Account column '{account_column}' not found in data")
                return {"error": f"Account column '{account_column}' not found in data"}
            
            # Группируем данные по кабинетам
            account_groups = df.groupby(account_column)
            
            # Анализируем каждый кабинет
            account_results = {}
            for account, group in account_groups:
                # Пропускаем пустые идентификаторы кабинетов
                if pd.isna(account) or str(account).strip() == "":
                    continue
                
                # Преобразуем группу в словарь для анализа
                account_data = group.to_dict(orient='records')
                
                # Получаем базовую статистику по кабинету
                numeric_cols = group.select_dtypes(include=['number']).columns
                
                account_stats = {
                    "count": len(group),
                    "metrics": {}
                }
                
                # Добавляем статистику по числовым колонкам
                for col in numeric_cols:
                    account_stats["metrics"][col] = {
                        "mean": float(group[col].mean()),
                        "median": float(group[col].median()),
                        "min": float(group[col].min()),
                        "max": float(group[col].max()),
                        "sum": float(group[col].sum())
                    }
                
                # Сохраняем результаты для кабинета
                account_results[str(account)] = account_stats
            
            # Сохраняем результаты анализа по кабинетам
            self.account_metrics = account_results
            
            # Анализируем тренды по кабинетам с помощью OpenAI
            trends_analysis = self._analyze_account_trends(account_results)
            
            # Формируем итоговый результат
            result = {
                "account_metrics": account_results,
                "trends_analysis": trends_analysis
            }
            
            return result
        except Exception as e:
            logger.error(f"Error analyzing data by account: {str(e)}")
            return {"error": f"Error analyzing data by account: {str(e)}"}
    
    def analyze_ad_sources(self, data: Dict[str, Any], source_column: str = "source") -> Dict[str, Any]:
        """
        Анализирует данные по рекламным источникам
        
        Args:
            data: Данные для анализа
            source_column: Название колонки с источниками
            
        Returns:
            Результаты анализа по рекламным источникам
        """
        try:
            logger.info(f"Analyzing data by ad sources using column: {source_column}")
            
            # Проверяем, что данные содержат нужную колонку
            if "data" not in data or not data["data"]:
                logger.warning("No data provided for ad sources analysis")
                return {"error": "No data provided for ad sources analysis"}
            
            # Преобразуем данные в DataFrame
            df = pd.DataFrame(data["data"])
            
            # Проверяем наличие колонки с источниками
            if source_column not in df.columns:
                logger.warning(f"Source column '{source_column}' not found in data")
                return {"error": f"Source column '{source_column}' not found in data"}
            
            # Группируем данные по источникам
            source_groups = df.groupby(source_column)
            
            # Анализируем каждый источник
            source_results = {}
            for source, group in source_groups:
                # Пропускаем пустые источники
                if pd.isna(source) or str(source).strip() == "":
                    continue
                
                # Преобразуем группу в словарь для анализа
                source_data = group.to_dict(orient='records')
                
                # Получаем базовую статистику по источнику
                numeric_cols = group.select_dtypes(include=['number']).columns
                
                source_stats = {
                    "count": len(group),
                    "metrics": {}
                }
                
                # Добавляем статистику по числовым колонкам
                for col in numeric_cols:
                    source_stats["metrics"][col] = {
                        "mean": float(group[col].mean()),
                        "median": float(group[col].median()),
                        "min": float(group[col].min()),
                        "max": float(group[col].max()),
                        "sum": float(group[col].sum())
                    }
                
                # Сохраняем результаты для источника
                source_results[str(source)] = source_stats
            
            # Анализируем тренды по источникам с помощью OpenAI
            trends_analysis = self._analyze_ad_source_trends(source_results)
            
            # Формируем итоговый результат
            result = {
                "source_metrics": source_results,
                "trends_analysis": trends_analysis
            }
            
            return result
        except Exception as e:
            logger.error(f"Error analyzing data by ad sources: {str(e)}")
            return {"error": f"Error analyzing data by ad sources: {str(e)}"}
    
    def analyze_orders_decline(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Анализирует причины падения заказов
        
        Args:
            data: Данные для анализа
            
        Returns:
            Результаты анализа причин падения заказов
        """
        try:
            logger.info("Analyzing orders decline")
            
            # Проверяем, что данные содержат нужные колонки
            if "data" not in data or not data["data"]:
                logger.warning("No data provided for orders decline analysis")
                return {"error": "No data provided for orders decline analysis"}
            
            # Преобразуем данные в DataFrame
            df = pd.DataFrame(data["data"])
            
            # Проверяем наличие колонки с заказами
            orders_columns = [col for col in df.columns if "order" in col.lower() or "заказ" in col.lower()]
            if not orders_columns:
                logger.warning("No orders column found in data")
                return {"error": "No orders column found in data"}
            
            # Выбираем первую колонку с заказами
            orders_column = orders_columns[0]
            
            # Проверяем наличие колонки с датами
            date_columns = [col for col in df.columns if "date" in col.lower() or "дата" in col.lower()]
            if not date_columns:
                logger.warning("No date column found in data")
                return {"error": "No date column found in data"}
            
            # Выбираем первую колонку с датами
            date_column = date_columns[0]
            
            # Преобразуем колонку с датами в datetime
            df[date_column] = pd.to_datetime(df[date_column], errors='coerce')
            
            # Сортируем данные по дате
            df = df.sort_values(by=date_column)
            
            # Группируем данные по дате и считаем сумму заказов
            orders_by_date = df.groupby(pd.Grouper(key=date_column, freq='D'))[orders_column].sum().reset_index()
            
            # Находим периоды падения заказов
            orders_by_date['prev_orders'] = orders_by_date[orders_column].shift(1)
            orders_by_date['change'] = orders_by_date[orders_column] - orders_by_date['prev_orders']
            orders_by_date['change_pct'] = orders_by_date['change'] / orders_by_date['prev_orders'] * 100
            
            # Находим дни с падением заказов более чем на 10%
            decline_days = orders_by_date[orders_by_date['change_pct'] < -10].copy()
            
            # Если нет дней с падением заказов, возвращаем пустой результат
            if len(decline_days) == 0:
                return {
                    "decline_analysis": "Не обнаружено значительного падения заказов",
                    "factors": {},
                    "recommendations": []
                }
            
            # Анализируем факторы падения заказов
            factors = {}
            
            # Анализ медианной позиции
            position_columns = [col for col in df.columns if "position" in col.lower() or "позиция" in col.lower()]
            if position_columns:
                position_column = position_columns[0]
                position_by_date = df.groupby(pd.Grouper(key=date_column, freq='D'))[position_column].median().reset_index()
                position_by_date = position_by_date.merge(decline_days[[date_column]], on=date_column, how='inner')
                
                if not position_by_date.empty:
                    # Сравниваем медианную позицию в дни падения с предыдущими днями
                    position_by_date['prev_position'] = position_by_date[position_column].shift(1)
                    position_by_date['position_change'] = position_by_date[position_column] - position_by_date['prev_position']
                    position_by_date['position_change_pct'] = position_by_date['position_change'] / position_by_date['prev_position'] * 100
                    
                    # Если медианная позиция ухудшилась (увеличилась) более чем на 10%, считаем это фактором падения
                    if position_by_date['position_change_pct'].mean() > 10:
                        factors["median_position"] = {
                            "impact": "high",
                            "description": "Ухудшение медианной позиции товаров",
                            "data": position_by_date.to_dict(orient='records')
                        }
            
            # Анализ сезонности
            # Проверяем, есть ли данные за предыдущий год
            min_date = df[date_column].min()
            max_date = df[date_column].max()
            date_range = max_date - min_date
            
            if date_range.days > 300:  # Если есть данные за почти год
                # Группируем данные по месяцу и дню
                df['month_day'] = df[date_column].dt.strftime('%m-%d')
                seasonal_orders = df.groupby('month_day')[orders_column].mean().reset_index()
                
                # Находим сезонные паттерны
                seasonal_orders = seasonal_orders.sort_values(by=orders_column)
                low_season_days = seasonal_orders.head(int(len(seasonal_orders) * 0.2))['month_day'].tolist()
                
                # Проверяем, попадают ли дни падения в сезонные паттерны
                decline_days['month_day'] = pd.to_datetime(decline_days[date_column]).dt.strftime('%m-%d')
                seasonal_decline = decline_days[decline_days['month_day'].isin(low_season_days)]
                
                if len(seasonal_decline) > 0:
                    factors["seasonality"] = {
                        "impact": "medium",
                        "description": "Сезонное падение заказов",
                        "data": {
                            "low_season_days": low_season_days,
                            "seasonal_decline_days": seasonal_decline[date_column].dt.strftime('%Y-%m-%d').tolist()
                        }
                    }
            
            # Анализ рекламного давления
            ad_columns = [col for col in df.columns if "ad" in col.lower() or "реклам" in col.lower()]
            if ad_columns:
                ad_column = ad_columns[0]
                ad_by_date = df.groupby(pd.Grouper(key=date_column, freq='D'))[ad_column].sum().reset_index()
                ad_by_date = ad_by_date.merge(decline_days[[date_column]], on=date_column, how='inner')
                
                if not ad_by_date.empty:
                    # Сравниваем рекламное давление в дни падения с предыдущими днями
                    ad_by_date['prev_ad'] = ad_by_date[ad_column].shift(1)
                    ad_by_date['ad_change'] = ad_by_date[ad_column] - ad_by_date['prev_ad']
                    ad_by_date['ad_change_pct'] = ad_by_date['ad_change'] / ad_by_date['prev_ad'] * 100
                    
                    # Если рекламное давление снизилось более чем на 10%, считаем это фактором падения
                    if ad_by_date['ad_change_pct'].mean() < -10:
                        factors["ad_pressure"] = {
                            "impact": "high",
                            "description": "Снижение рекламного давления",
                            "data": ad_by_date.to_dict(orient='records')
                        }
            
            # Анализ ценообразования
            price_columns = [col for col in df.columns if "price" in col.lower() or "цена" in col.lower()]
            if price_columns:
                price_column = price_columns[0]
                price_by_date = df.groupby(pd.Grouper(key=date_column, freq='D'))[price_column].mean().reset_index()
                price_by_date = price_by_date.merge(decline_days[[date_column]], on=date_column, how='inner')
                
                if not price_by_date.empty:
                    # Сравниваем цены в дни падения с предыдущими днями
                    price_by_date['prev_price'] = price_by_date[price_column].shift(1)
                    price_by_date['price_change'] = price_by_date[price_column] - price_by_date['prev_price']
                    price_by_date['price_change_pct'] = price_by_date['price_change'] / price_by_date['prev_price'] * 100
                    
                    # Если цены выросли более чем на 5%, считаем это фактором падения
                    if price_by_date['price_change_pct'].mean() > 5:
                        factors["pricing"] = {
                            "impact": "medium",
                            "description": "Повышение цен",
                            "data": price_by_date.to_dict(orient='records')
                        }
            
            # Анализ наличия товаров
            stock_columns = [col for col in df.columns if "stock" in col.lower() or "наличие" in col.lower()]
            if stock_columns:
                stock_column = stock_columns[0]
                stock_by_date = df.groupby(pd.Grouper(key=date_column, freq='D'))[stock_column].mean().reset_index()
                stock_by_date = stock_by_date.merge(decline_days[[date_column]], on=date_column, how='inner')
                
                if not stock_by_date.empty:
                    # Сравниваем наличие товаров в дни падения с предыдущими днями
                    stock_by_date['prev_stock'] = stock_by_date[stock_column].shift(1)
                    stock_by_date['stock_change'] = stock_by_date[stock_column] - stock_by_date['prev_stock']
                    stock_by_date['stock_change_pct'] = stock_by_date['stock_change'] / stock_by_date['prev_stock'] * 100
                    
                    # Если наличие товаров снизилось более чем на 10%, считаем это фактором падения
                    if stock_by_date['stock_change_pct'].mean() < -10:
                        factors["stock"] = {
                            "impact": "high",
                            "description": "Снижение наличия товаров",
                            "data": stock_by_date.to_dict(orient='records')
                        }
            
            # Анализируем причины падения заказов с помощью OpenAI
            decline_analysis = self._analyze_orders_decline(decline_days.to_dict(orient='records'), factors)
            
            # Формируем итоговый результат
            result = {
                "decline_days": decline_days.to_dict(orient='records'),
                "factors": factors,
                "decline_analysis": decline_analysis
            }
            
            return result
        except Exception as e:
            logger.error(f"Error analyzing orders decline: {str(e)}")
            return {"error": f"Error analyzing orders decline: {str(e)}"}
    
    def analyze_ad_effectiveness(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Анализирует эффективность рекламных инструментов
        
        Args:
            data: Данные для анализа
            
        Returns:
            Результаты анализа эффективности рекламных инструментов
        """
        try:
            logger.info("Analyzing ad effectiveness")
            
            # Проверяем, что данные содержат нужные колонки
            if "data" not in data or not data["data"]:
                logger.warning("No data provided for ad effectiveness analysis")
                return {"error": "No data provided for ad effectiveness analysis"}
            
            # Преобразуем данные в DataFrame
            df = pd.DataFrame(data["data"])
            
            # Проверяем наличие колонок с расходами на рекламу
            ad_spend_columns = [col for col in df.columns if "spend" in col.lower() or "расход" in col.lower()]
            if not ad_spend_columns:
                logger.warning("No ad spend column found in data")
                return {"error": "No ad spend column found in data"}
            
            # Выбираем первую колонку с расходами на рекламу
            ad_spend_column = ad_spend_columns[0]
            
            # Проверяем наличие колонок с заказами или продажами
            orders_columns = [col for col in df.columns if "order" in col.lower() or "заказ" in col.lower()]
            sales_columns = [col for col in df.columns if "sale" in col.lower() or "продаж" in col.lower()]
            
            if not orders_columns and not sales_columns:
                logger.warning("No orders or sales column found in data")
                return {"error": "No orders or sales column found in data"}
            
            # Выбираем колонку с заказами или продажами
            target_column = orders_columns[0] if orders_columns else sales_columns[0]
            
            # Проверяем наличие колонки с рекламными инструментами
            ad_type_columns = [col for col in df.columns if "type" in col.lower() or "тип" in col.lower() or "инструмент" in col.lower()]
            if not ad_type_columns:
                logger.warning("No ad type column found in data")
                return {"error": "No ad type column found in data"}
            
            # Выбираем первую колонку с рекламными инструментами
            ad_type_column = ad_type_columns[0]
            
            # Группируем данные по рекламным инструментам
            ad_type_groups = df.groupby(ad_type_column)
            
            # Анализируем каждый рекламный инструмент
            ad_effectiveness = {}
            for ad_type, group in ad_type_groups:
                # Пропускаем пустые типы рекламы
                if pd.isna(ad_type) or str(ad_type).strip() == "":
                    continue
                
                # Рассчитываем метрики эффективности
                total_spend = group[ad_spend_column].sum()
                total_target = group[target_column].sum()
                
                # Избегаем деления на ноль
                if total_spend == 0:
                    cost_per_target = 0
                else:
                    cost_per_target = total_target / total_spend if total_target > 0 else 0
                
                # Сохраняем результаты для рекламного инструмента
                ad_effectiveness[str(ad_type)] = {
                    "total_spend": float(total_spend),
                    "total_target": float(total_target),
                    "cost_per_target": float(cost_per_target),
                    "count": len(group)
                }
            
            # Сортируем рекламные инструменты по эффективности
            sorted_ad_types = sorted(
                ad_effectiveness.items(),
                key=lambda x: x[1]["cost_per_target"],
                reverse=True
            )
            
            # Формируем рейтинг эффективности
            effectiveness_rating = {}
            for i, (ad_type, metrics) in enumerate(sorted_ad_types):
                effectiveness_rating[ad_type] = {
                    "rank": i + 1,
                    "metrics": metrics
                }
            
            # Анализируем эффективность рекламных инструментов с помощью OpenAI
            effectiveness_analysis = self._analyze_ad_effectiveness(effectiveness_rating)
            
            # Формируем итоговый результат
            result = {
                "ad_effectiveness": effectiveness_rating,
                "effectiveness_analysis": effectiveness_analysis
            }
            
            return result
        except Exception as e:
            logger.error(f"Error analyzing ad effectiveness: {str(e)}")
            return {"error": f"Error analyzing ad effectiveness: {str(e)}"}
    
    def analyze_seasonality(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Анализирует сезонность в данных
        
        Args:
            data: Данные для анализа
            
        Returns:
            Результаты анализа сезонности
        """
        try:
            logger.info("Analyzing seasonality")
            
            # Проверяем, что данные содержат нужные колонки
            if "data" not in data or not data["data"]:
                logger.warning("No data provided for seasonality analysis")
                return {"error": "No data provided for seasonality analysis"}
            
            # Преобразуем данные в DataFrame
            df = pd.DataFrame(data["data"])
            
            # Проверяем наличие колонки с датами
            date_columns = [col for col in df.columns if "date" in col.lower() or "дата" in col.lower()]
            if not date_columns:
                logger.warning("No date column found in data")
                return {"error": "No date column found in data"}
            
            # Выбираем первую колонку с датами
            date_column = date_columns[0]
            
            # Преобразуем колонку с датами в datetime
            df[date_column] = pd.to_datetime(df[date_column], errors='coerce')
            
            # Проверяем наличие колонок с метриками
            numeric_cols = df.select_dtypes(include=['number']).columns
            if len(numeric_cols) == 0:
                logger.warning("No numeric columns found in data")
                return {"error": "No numeric columns found in data"}
            
            # Выбираем топ-5 числовых колонок для анализа
            top_numeric_cols = numeric_cols[:5]
            
            # Добавляем временные компоненты
            df['year'] = df[date_column].dt.year
            df['month'] = df[date_column].dt.month
            df['day_of_week'] = df[date_column].dt.dayofweek
            df['day_of_month'] = df[date_column].dt.day
            df['quarter'] = df[date_column].dt.quarter
            
            # Анализируем сезонность по месяцам
            monthly_seasonality = {}
            for col in top_numeric_cols:
                monthly_data = df.groupby('month')[col].mean().reset_index()
                monthly_seasonality[col] = monthly_data.to_dict(orient='records')
            
            # Анализируем сезонность по дням недели
            weekly_seasonality = {}
            for col in top_numeric_cols:
                weekly_data = df.groupby('day_of_week')[col].mean().reset_index()
                weekly_seasonality[col] = weekly_data.to_dict(orient='records')
            
            # Анализируем сезонность по кварталам
            quarterly_seasonality = {}
            for col in top_numeric_cols:
                quarterly_data = df.groupby('quarter')[col].mean().reset_index()
                quarterly_seasonality[col] = quarterly_data.to_dict(orient='records')
            
            # Сохраняем результаты анализа сезонности
            self.seasonal_patterns = {
                "monthly": monthly_seasonality,
                "weekly": weekly_seasonality,
                "quarterly": quarterly_seasonality
            }
            
            # Анализируем сезонность с помощью OpenAI
            seasonality_analysis = self._analyze_seasonality(self.seasonal_patterns)
            
            # Формируем итоговый результат
            result = {
                "seasonal_patterns": self.seasonal_patterns,
                "seasonality_analysis": seasonality_analysis
            }
            
            return result
        except Exception as e:
            logger.error(f"Error analyzing seasonality: {str(e)}")
            return {"error": f"Error analyzing seasonality: {str(e)}"}
    
    def _analyze_category_trends(self, category_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Анализирует тренды по категориям с помощью OpenAI
        
        Args:
            category_metrics: Метрики по категориям
            
        Returns:
            Результаты анализа трендов по категориям
        """
        try:
            # Формируем промпт для анализа трендов по категориям
            system_prompt = """
            Ты - опытный аналитик данных маркетплейсов. Тебе предоставлены метрики по категориям товаров.
            Проанализируй тренды по категориям. Обрати внимание на:
            - Наиболее и наименее эффективные категории
            - Сравнение метрик между категориями
            - Возможности для оптимизации
            
            Результат представь в формате JSON со следующими полями:
            - trends_analysis: подробный анализ трендов по категориям
            - top_categories: список лучших категорий с объяснением (массив объектов с полями category и reason)
            - bottom_categories: список худших категорий с объяснением (массив объектов с полями category и reason)
            - recommendations: список рекомендаций по оптимизации категорий (массив строк)
            """
            
            # Создаем сообщения для API
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Метрики по категориям: {json.dumps(category_metrics)}"}
            ]
            
            # Отправляем запрос к API
            import asyncio
            loop = asyncio.get_event_loop()
            response = loop.run_until_complete(
                openai_service.chat_completion(messages, temperature=0.2)
            )
            
            # Пытаемся преобразовать ответ в JSON
            try:
                result = json.loads(response["content"])
            except:
                # Если не удалось преобразовать в JSON, возвращаем как есть
                result = {
                    "trends_analysis": response["content"],
                    "top_categories": [],
                    "bottom_categories": [],
                    "recommendations": []
                }
            
            return result
        except Exception as e:
            logger.error(f"Error analyzing category trends: {str(e)}")
            return {
                "trends_analysis": f"Произошла ошибка при анализе трендов по категориям: {str(e)}",
                "top_categories": [],
                "bottom_categories": [],
                "recommendations": []
            }
    
    def _analyze_product_trends(self, product_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Анализирует тренды по товарам с помощью OpenAI
        
        Args:
            product_metrics: Метрики по товарам
            
        Returns:
            Результаты анализа трендов по товарам
        """
        try:
            # Формируем промпт для анализа трендов по товарам
            system_prompt = """
            Ты - опытный аналитик данных маркетплейсов. Тебе предоставлены метрики по товарам.
            Проанализируй тренды по товарам. Обрати внимание на:
            - Наиболее и наименее эффективные товары
            - Сравнение метрик между товарами
            - Возможности для оптимизации
            
            Результат представь в формате JSON со следующими полями:
            - trends_analysis: подробный анализ трендов по товарам
            - top_products: список лучших товаров с объяснением (массив объектов с полями product и reason)
            - bottom_products: список худших товаров с объяснением (массив объектов с полями product и reason)
            - recommendations: список рекомендаций по оптимизации товаров (массив строк)
            """
            
            # Создаем сообщения для API
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Метрики по товарам: {json.dumps(product_metrics)}"}
            ]
            
            # Отправляем запрос к API
            import asyncio
            loop = asyncio.get_event_loop()
            response = loop.run_until_complete(
                openai_service.chat_completion(messages, temperature=0.2)
            )
            
            # Пытаемся преобразовать ответ в JSON
            try:
                result = json.loads(response["content"])
            except:
                # Если не удалось преобразовать в JSON, возвращаем как есть
                result = {
                    "trends_analysis": response["content"],
                    "top_products": [],
                    "bottom_products": [],
                    "recommendations": []
                }
            
            return result
        except Exception as e:
            logger.error(f"Error analyzing product trends: {str(e)}")
            return {
                "trends_analysis": f"Произошла ошибка при анализе трендов по товарам: {str(e)}",
                "top_products": [],
                "bottom_products": [],
                "recommendations": []
            }
    
    def _analyze_account_trends(self, account_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Анализирует тренды по кабинетам с помощью OpenAI
        
        Args:
            account_metrics: Метрики по кабинетам
            
        Returns:
            Результаты анализа трендов по кабинетам
        """
        try:
            # Формируем промпт для анализа трендов по кабинетам
            system_prompt = """
            Ты - опытный аналитик данных маркетплейсов. Тебе предоставлены метрики по кабинетам.
            Проанализируй тренды по кабинетам. Обрати внимание на:
            - Наиболее и наименее эффективные кабинеты
            - Сравнение метрик между кабинетами
            - Возможности для оптимизации
            
            Результат представь в формате JSON со следующими полями:
            - trends_analysis: подробный анализ трендов по кабинетам
            - top_accounts: список лучших кабинетов с объяснением (массив объектов с полями account и reason)
            - bottom_accounts: список худших кабинетов с объяснением (массив объектов с полями account и reason)
            - recommendations: список рекомендаций по оптимизации кабинетов (массив строк)
            """
            
            # Создаем сообщения для API
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Метрики по кабинетам: {json.dumps(account_metrics)}"}
            ]
            
            # Отправляем запрос к API
            import asyncio
            loop = asyncio.get_event_loop()
            response = loop.run_until_complete(
                openai_service.chat_completion(messages, temperature=0.2)
            )
            
            # Пытаемся преобразовать ответ в JSON
            try:
                result = json.loads(response["content"])
            except:
                # Если не удалось преобразовать в JSON, возвращаем как есть
                result = {
                    "trends_analysis": response["content"],
                    "top_accounts": [],
                    "bottom_accounts": [],
                    "recommendations": []
                }
            
            return result
        except Exception as e:
            logger.error(f"Error analyzing account trends: {str(e)}")
            return {
                "trends_analysis": f"Произошла ошибка при анализе трендов по кабинетам: {str(e)}",
                "top_accounts": [],
                "bottom_accounts": [],
                "recommendations": []
            }
    
    def _analyze_ad_source_trends(self, source_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Анализирует тренды по рекламным источникам с помощью OpenAI
        
        Args:
            source_metrics: Метрики по рекламным источникам
            
        Returns:
            Результаты анализа трендов по рекламным источникам
        """
        try:
            # Формируем промпт для анализа трендов по рекламным источникам
            system_prompt = """
            Ты - опытный аналитик данных маркетплейсов. Тебе предоставлены метрики по рекламным источникам.
            Проанализируй тренды по рекламным источникам. Обрати внимание на:
            - Наиболее и наименее эффективные источники
            - Сравнение метрик между источниками
            - Возможности для оптимизации
            
            Результат представь в формате JSON со следующими полями:
            - trends_analysis: подробный анализ трендов по рекламным источникам
            - top_sources: список лучших источников с объяснением (массив объектов с полями source и reason)
            - bottom_sources: список худших источников с объяснением (массив объектов с полями source и reason)
            - recommendations: список рекомендаций по оптимизации рекламных источников (массив строк)
            """
            
            # Создаем сообщения для API
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Метрики по рекламным источникам: {json.dumps(source_metrics)}"}
            ]
            
            # Отправляем запрос к API
            import asyncio
            loop = asyncio.get_event_loop()
            response = loop.run_until_complete(
                openai_service.chat_completion(messages, temperature=0.2)
            )
            
            # Пытаемся преобразовать ответ в JSON
            try:
                result = json.loads(response["content"])
            except:
                # Если не удалось преобразовать в JSON, возвращаем как есть
                result = {
                    "trends_analysis": response["content"],
                    "top_sources": [],
                    "bottom_sources": [],
                    "recommendations": []
                }
            
            return result
        except Exception as e:
            logger.error(f"Error analyzing ad source trends: {str(e)}")
            return {
                "trends_analysis": f"Произошла ошибка при анализе трендов по рекламным источникам: {str(e)}",
                "top_sources": [],
                "bottom_sources": [],
                "recommendations": []
            }
    
    def _analyze_orders_decline(self, decline_days: List[Dict[str, Any]], factors: Dict[str, Any]) -> Dict[str, Any]:
        """
        Анализирует причины падения заказов с помощью OpenAI
        
        Args:
            decline_days: Дни с падением заказов
            factors: Факторы падения заказов
            
        Returns:
            Результаты анализа причин падения заказов
        """
        try:
            # Формируем промпт для анализа причин падения заказов
            system_prompt = """
            Ты - опытный аналитик данных маркетплейсов. Тебе предоставлены данные о днях с падением заказов и факторах, которые могли повлиять на это падение.
            Проанализируй причины падения заказов. Обрати внимание на:
            - Основные факторы, влияющие на падение
            - Взаимосвязи между факторами
            - Возможности для предотвращения падения в будущем
            
            Результат представь в формате JSON со следующими полями:
            - decline_analysis: подробный анализ причин падения заказов
            - primary_factors: список основных факторов падения с объяснением (массив объектов с полями factor и explanation)
            - secondary_factors: список второстепенных факторов падения с объяснением (массив объектов с полями factor и explanation)
            - recommendations: список рекомендаций по предотвращению падения заказов (массив строк)
            """
            
            # Создаем сообщения для API
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Дни с падением заказов: {json.dumps(decline_days)}\nФакторы падения: {json.dumps(factors)}"}
            ]
            
            # Отправляем запрос к API
            import asyncio
            loop = asyncio.get_event_loop()
            response = loop.run_until_complete(
                openai_service.chat_completion(messages, temperature=0.2)
            )
            
            # Пытаемся преобразовать ответ в JSON
            try:
                result = json.loads(response["content"])
            except:
                # Если не удалось преобразовать в JSON, возвращаем как есть
                result = {
                    "decline_analysis": response["content"],
                    "primary_factors": [],
                    "secondary_factors": [],
                    "recommendations": []
                }
            
            return result
        except Exception as e:
            logger.error(f"Error analyzing orders decline: {str(e)}")
            return {
                "decline_analysis": f"Произошла ошибка при анализе причин падения заказов: {str(e)}",
                "primary_factors": [],
                "secondary_factors": [],
                "recommendations": []
            }
    
    def _analyze_ad_effectiveness(self, effectiveness_rating: Dict[str, Any]) -> Dict[str, Any]:
        """
        Анализирует эффективность рекламных инструментов с помощью OpenAI
        
        Args:
            effectiveness_rating: Рейтинг эффективности рекламных инструментов
            
        Returns:
            Результаты анализа эффективности рекламных инструментов
        """
        try:
            # Формируем промпт для анализа эффективности рекламных инструментов
            system_prompt = """
            Ты - опытный аналитик данных маркетплейсов. Тебе предоставлены данные об эффективности рекламных инструментов.
            Проанализируй эффективность рекламных инструментов. Обрати внимание на:
            - Наиболее и наименее эффективные инструменты
            - Факторы, влияющие на эффективность
            - Возможности для оптимизации рекламных кампаний
            
            Результат представь в формате JSON со следующими полями:
            - effectiveness_analysis: подробный анализ эффективности рекламных инструментов
            - top_performers: список лучших инструментов с объяснением (массив объектов с полями ad_type и reason)
            - underperformers: список худших инструментов с объяснением (массив объектов с полями ad_type и reason)
            - recommendations: список рекомендаций по оптимизации рекламных кампаний (массив строк)
            """
            
            # Создаем сообщения для API
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Эффективность рекламных инструментов: {json.dumps(effectiveness_rating)}"}
            ]
            
            # Отправляем запрос к API
            import asyncio
            loop = asyncio.get_event_loop()
            response = loop.run_until_complete(
                openai_service.chat_completion(messages, temperature=0.2)
            )
            
            # Пытаемся преобразовать ответ в JSON
            try:
                result = json.loads(response["content"])
            except:
                # Если не удалось преобразовать в JSON, возвращаем как есть
                result = {
                    "effectiveness_analysis": response["content"],
                    "top_performers": [],
                    "underperformers": [],
                    "recommendations": []
                }
            
            return result
        except Exception as e:
            logger.error(f"Error analyzing ad effectiveness: {str(e)}")
            return {
                "effectiveness_analysis": f"Произошла ошибка при анализе эффективности рекламных инструментов: {str(e)}",
                "top_performers": [],
                "underperformers": [],
                "recommendations": []
            }
    
    def _analyze_seasonality(self, seasonal_patterns: Dict[str, Any]) -> Dict[str, Any]:
        """
        Анализирует сезонность с помощью OpenAI
        
        Args:
            seasonal_patterns: Сезонные паттерны
            
        Returns:
            Результаты анализа сезонности
        """
        try:
            # Формируем промпт для анализа сезонности
            system_prompt = """
            Ты - опытный аналитик данных маркетплейсов. Тебе предоставлены данные о сезонных паттернах.
            Проанализируй сезонность в данных. Обрати внимание на:
            - Месячные, недельные и квартальные паттерны
            - Периоды высокой и низкой активности
            - Возможности для оптимизации с учетом сезонности
            
            Результат представь в формате JSON со следующими полями:
            - seasonality_analysis: подробный анализ сезонности
            - peak_periods: список периодов высокой активности с объяснением (массив объектов с полями period и explanation)
            - low_periods: список периодов низкой активности с объяснением (массив объектов с полями period и explanation)
            - recommendations: список рекомендаций по оптимизации с учетом сезонности (массив строк)
            """
            
            # Создаем сообщения для API
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Сезонные паттерны: {json.dumps(seasonal_patterns)}"}
            ]
            
            # Отправляем запрос к API
            import asyncio
            loop = asyncio.get_event_loop()
            response = loop.run_until_complete(
                openai_service.chat_completion(messages, temperature=0.2)
            )
            
            # Пытаемся преобразовать ответ в JSON
            try:
                result = json.loads(response["content"])
            except:
                # Если не удалось преобразовать в JSON, возвращаем как есть
                result = {
                    "seasonality_analysis": response["content"],
                    "peak_periods": [],
                    "low_periods": [],
                    "recommendations": []
                }
            
            return result
        except Exception as e:
            logger.error(f"Error analyzing seasonality: {str(e)}")
            return {
                "seasonality_analysis": f"Произошла ошибка при анализе сезонности: {str(e)}",
                "peak_periods": [],
                "low_periods": [],
                "recommendations": []
            }

# Создаем экземпляр анализатора метрик
metrics_analyzer = MetricsAnalyzer()
