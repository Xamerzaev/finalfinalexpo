import logging
import json
import time
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from app.core.config import settings
from app.services.openai_service import openai_service

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TaskManager:
    """
    Класс для автоматического создания и управления задачами
    """
    
    def __init__(self):
        """
        Инициализирует менеджер задач
        """
        self.tasks = []
        self.task_categories = {
            "marketing": "Маркетинг",
            "content": "Контент",
            "pricing": "Ценообразование",
            "logistics": "Логистика",
            "product": "Товары",
            "advertising": "Реклама",
            "analytics": "Аналитика"
        }
        self.task_priorities = {
            "high": "Высокий",
            "medium": "Средний",
            "low": "Низкий"
        }
    
    def create_task(
        self,
        title: str,
        description: str,
        category: str = "analytics",
        priority: str = "medium",
        due_date: Optional[str] = None,
        assignee: Optional[str] = None,
        related_metrics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Создает новую задачу
        
        Args:
            title: Заголовок задачи
            description: Описание задачи
            category: Категория задачи
            priority: Приоритет задачи
            due_date: Срок выполнения задачи (формат: YYYY-MM-DD)
            assignee: Исполнитель задачи
            related_metrics: Связанные метрики
            
        Returns:
            Созданная задача
        """
        # Проверяем категорию
        if category not in self.task_categories:
            category = "analytics"
        
        # Проверяем приоритет
        if priority not in self.task_priorities:
            priority = "medium"
        
        # Если срок не указан, устанавливаем на неделю вперед
        if not due_date:
            due_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        # Создаем задачу
        task = {
            "id": int(time.time()),
            "title": title,
            "description": description,
            "category": category,
            "category_name": self.task_categories[category],
            "priority": priority,
            "priority_name": self.task_priorities[priority],
            "due_date": due_date,
            "assignee": assignee,
            "related_metrics": related_metrics or [],
            "status": "new",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Добавляем задачу в список
        self.tasks.append(task)
        
        logger.info(f"Created task: {title}")
        
        return task
    
    def get_tasks(
        self,
        category: Optional[str] = None,
        priority: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Получает список задач с фильтрацией
        
        Args:
            category: Категория задач для фильтрации
            priority: Приоритет задач для фильтрации
            status: Статус задач для фильтрации
            
        Returns:
            Список задач
        """
        filtered_tasks = self.tasks
        
        # Фильтруем по категории
        if category:
            filtered_tasks = [task for task in filtered_tasks if task["category"] == category]
        
        # Фильтруем по приоритету
        if priority:
            filtered_tasks = [task for task in filtered_tasks if task["priority"] == priority]
        
        # Фильтруем по статусу
        if status:
            filtered_tasks = [task for task in filtered_tasks if task["status"] == status]
        
        return filtered_tasks
    
    def update_task(self, task_id: int, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Обновляет задачу
        
        Args:
            task_id: ID задачи
            updates: Обновления для задачи
            
        Returns:
            Обновленная задача или None, если задача не найдена
        """
        # Находим задачу по ID
        for i, task in enumerate(self.tasks):
            if task["id"] == task_id:
                # Обновляем задачу
                for key, value in updates.items():
                    if key in task:
                        task[key] = value
                
                # Обновляем время изменения
                task["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Обновляем название категории и приоритета, если они изменились
                if "category" in updates:
                    task["category_name"] = self.task_categories.get(updates["category"], "Другое")
                
                if "priority" in updates:
                    task["priority_name"] = self.task_priorities.get(updates["priority"], "Средний")
                
                logger.info(f"Updated task: {task['title']}")
                
                return task
        
        logger.warning(f"Task with ID {task_id} not found")
        return None
    
    def delete_task(self, task_id: int) -> bool:
        """
        Удаляет задачу
        
        Args:
            task_id: ID задачи
            
        Returns:
            True, если задача удалена, иначе False
        """
        # Находим задачу по ID
        for i, task in enumerate(self.tasks):
            if task["id"] == task_id:
                # Удаляем задачу
                del self.tasks[i]
                
                logger.info(f"Deleted task with ID {task_id}")
                
                return True
        
        logger.warning(f"Task with ID {task_id} not found")
        return False
    
    def generate_tasks_from_analysis(self, analysis_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Генерирует задачи на основе результатов анализа
        
        Args:
            analysis_result: Результаты анализа
            
        Returns:
            Список созданных задач
        """
        generated_tasks = []
        
        try:
            # Проверяем наличие рекомендаций в результатах анализа
            if "recommendations" in analysis_result and isinstance(analysis_result["recommendations"], list):
                recommendations = analysis_result["recommendations"]
                
                # Создаем задачи на основе рекомендаций
                for recommendation in recommendations:
                    if not recommendation:
                        continue
                    
                    # Определяем категорию задачи на основе текста рекомендации
                    category = self._determine_task_category(recommendation)
                    
                    # Определяем приоритет задачи на основе текста рекомендации
                    priority = self._determine_task_priority(recommendation)
                    
                    # Создаем задачу
                    task = self.create_task(
                        title=recommendation[:100] + ("..." if len(recommendation) > 100 else ""),
                        description=recommendation,
                        category=category,
                        priority=priority
                    )
                    
                    generated_tasks.append(task)
            
            # Проверяем наличие возможностей в результатах анализа
            if "opportunities" in analysis_result and isinstance(analysis_result["opportunities"], list):
                opportunities = analysis_result["opportunities"]
                
                # Создаем задачи на основе возможностей
                for opportunity in opportunities:
                    if not opportunity:
                        continue
                    
                    # Определяем категорию задачи на основе текста возможности
                    category = self._determine_task_category(opportunity)
                    
                    # Определяем приоритет задачи на основе текста возможности
                    priority = self._determine_task_priority(opportunity)
                    
                    # Создаем задачу
                    task = self.create_task(
                        title="Использовать возможность: " + opportunity[:80] + ("..." if len(opportunity) > 80 else ""),
                        description=opportunity,
                        category=category,
                        priority=priority
                    )
                    
                    generated_tasks.append(task)
            
            # Проверяем наличие угроз в результатах анализа
            if "threats" in analysis_result and isinstance(analysis_result["threats"], list):
                threats = analysis_result["threats"]
                
                # Создаем задачи на основе угроз
                for threat in threats:
                    if not threat:
                        continue
                    
                    # Определяем категорию задачи на основе текста угрозы
                    category = self._determine_task_category(threat)
                    
                    # Для угроз устанавливаем высокий приоритет
                    priority = "high"
                    
                    # Создаем задачу
                    task = self.create_task(
                        title="Устранить угрозу: " + threat[:80] + ("..." if len(threat) > 80 else ""),
                        description=threat,
                        category=category,
                        priority=priority
                    )
                    
                    generated_tasks.append(task)
            
            logger.info(f"Generated {len(generated_tasks)} tasks from analysis")
            
            return generated_tasks
        except Exception as e:
            logger.error(f"Error generating tasks from analysis: {str(e)}")
            return []
    
    def generate_tasks_from_metrics(self, metrics_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Генерирует задачи на основе метрик
        
        Args:
            metrics_data: Данные метрик
            
        Returns:
            Список созданных задач
        """
        try:
            # Формируем промпт для генерации задач на основе метрик
            system_prompt = """
            Ты - опытный аналитик данных маркетплейсов. Тебе предоставлены данные метрик.
            Твоя задача - сгенерировать список задач на основе этих метрик.
            Задачи должны быть конкретными, действенными и направленными на улучшение показателей.
            
            Результат представь в формате JSON со следующим полем:
            - tasks: список задач (массив объектов со следующими полями):
              - title: заголовок задачи (краткое описание)
              - description: подробное описание задачи
              - category: категория задачи (одна из: marketing, content, pricing, logistics, product, advertising, analytics)
              - priority: приоритет задачи (одна из: high, medium, low)
              - related_metrics: список связанных метрик (массив строк)
            """
            
            # Создаем сообщения для API
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Данные метрик: {json.dumps(metrics_data)}"}
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
                # Если не удалось преобразовать в JSON, возвращаем пустой список
                logger.warning("Failed to parse JSON response from OpenAI")
                return []
            
            # Проверяем наличие задач в результате
            if "tasks" not in result or not isinstance(result["tasks"], list):
                logger.warning("No tasks found in OpenAI response")
                return []
            
            # Создаем задачи
            generated_tasks = []
            for task_data in result["tasks"]:
                # Проверяем наличие необходимых полей
                if "title" not in task_data or "description" not in task_data:
                    continue
                
                # Создаем задачу
                task = self.create_task(
                    title=task_data["title"],
                    description=task_data["description"],
                    category=task_data.get("category", "analytics"),
                    priority=task_data.get("priority", "medium"),
                    related_metrics=task_data.get("related_metrics", [])
                )
                
                generated_tasks.append(task)
            
            logger.info(f"Generated {len(generated_tasks)} tasks from metrics")
            
            return generated_tasks
        except Exception as e:
            logger.error(f"Error generating tasks from metrics: {str(e)}")
            return []
    
    def check_existing_tasks(self, new_task: Dict[str, Any], similarity_threshold: float = 0.7) -> bool:
        """
        Проверяет, существует ли уже похожая задача
        
        Args:
            new_task: Новая задача
            similarity_threshold: Порог сходства для определения дубликатов
            
        Returns:
            True, если похожая задача уже существует, иначе False
        """
        try:
            # Если нет существующих задач, возвращаем False
            if not self.tasks:
                return False
            
            # Формируем промпт для проверки сходства задач
            system_prompt = """
            Ты - эксперт по определению сходства текстов. Тебе предоставлены две задачи.
            Твоя задача - определить, являются ли они дубликатами или очень похожими задачами.
            Оцени сходство по шкале от 0 до 1, где 0 - совершенно разные задачи, 1 - идентичные задачи.
            
            Результат представь в формате JSON со следующим полем:
            - similarity: оценка сходства (число от 0 до 1)
            """
            
            # Проверяем каждую существующую задачу
            for existing_task in self.tasks:
                # Создаем сообщения для API
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Задача 1: {json.dumps(new_task)}\nЗадача 2: {json.dumps(existing_task)}"}
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
                    # Если не удалось преобразовать в JSON, пропускаем
                    continue
                
                # Проверяем сходство
                if "similarity" in result and isinstance(result["similarity"], (int, float)):
                    if result["similarity"] >= similarity_threshold:
                        logger.info(f"Found similar existing task: {existing_task['title']}")
                        return True
            
            return False
        except Exception as e:
            logger.error(f"Error checking existing tasks: {str(e)}")
            return False
    
    def prioritize_tasks(self) -> List[Dict[str, Any]]:
        """
        Приоритизирует задачи
        
        Returns:
            Список приоритизированных задач
        """
        # Сортируем задачи по приоритету и дате создания
        prioritized_tasks = sorted(
            self.tasks,
            key=lambda x: (
                0 if x["priority"] == "high" else (1 if x["priority"] == "medium" else 2),
                x["created_at"]
            )
        )
        
        return prioritized_tasks
    
    def _determine_task_category(self, text: str) -> str:
        """
        Определяет категорию задачи на основе текста
        
        Args:
            text: Текст для анализа
            
        Returns:
            Категория задачи
        """
        # Ключевые слова для каждой категории
        category_keywords = {
            "marketing": ["маркетинг", "бренд", "продвижение", "целевая аудитория", "маркетинговый"],
            "content": ["контент", "описание", "фото", "изображение", "текст", "видео"],
            "pricing": ["цена", "ценообразование", "скидка", "акция", "стоимость"],
            "logistics": ["логистика", "доставка", "склад", "хранение", "отправка"],
            "product": ["товар", "продукт", "ассортимент", "характеристики", "свойства"],
            "advertising": ["реклама", "рекламный", "кампания", "объявление", "бюджет", "ставка"],
            "analytics": ["аналитика", "анализ", "метрика", "показатель", "данные", "статистика"]
        }
        
        # Подсчитываем количество ключевых слов для каждой категории
        category_scores = {}
        for category, keywords in category_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword.lower() in text.lower():
                    score += 1
            category_scores[category] = score
        
        # Выбираем категорию с наибольшим количеством совпадений
        if category_scores:
            max_score = max(category_scores.values())
            if max_score > 0:
                # Если есть совпадения, выбираем категорию с наибольшим количеством совпадений
                for category, score in category_scores.items():
                    if score == max_score:
                        return category
        
        # Если нет совпадений, возвращаем категорию по умолчанию
        return "analytics"
    
    def _determine_task_priority(self, text: str) -> str:
        """
        Определяет приоритет задачи на основе текста
        
        Args:
            text: Текст для анализа
            
        Returns:
            Приоритет задачи
        """
        # Ключевые слова для каждого приоритета
        priority_keywords = {
            "high": ["срочно", "критично", "немедленно", "высокий приоритет", "важно", "критический", "значительное падение", "резкое снижение"],
            "medium": ["средний приоритет", "умеренный", "в ближайшее время", "скоро", "заметное снижение", "некоторое падение"],
            "low": ["низкий приоритет", "несрочно", "когда будет время", "незначительное снижение", "небольшое падение"]
        }
        
        # Подсчитываем количество ключевых слов для каждого приоритета
        priority_scores = {}
        for priority, keywords in priority_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword.lower() in text.lower():
                    score += 1
            priority_scores[priority] = score
        
        # Выбираем приоритет с наибольшим количеством совпадений
        if priority_scores:
            max_score = max(priority_scores.values())
            if max_score > 0:
                # Если есть совпадения, выбираем приоритет с наибольшим количеством совпадений
                for priority, score in priority_scores.items():
                    if score == max_score:
                        return priority
        
        # Если нет совпадений, возвращаем приоритет по умолчанию
        return "medium"

# Создаем экземпляр менеджера задач
task_manager = TaskManager()
