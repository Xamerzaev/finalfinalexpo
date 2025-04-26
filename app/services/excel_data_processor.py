import pandas as pd
import numpy as np
import os
import re
import logging
from typing import Dict, Any, List, Union, Optional
from app.core.config import settings
from sqlalchemy.orm import Session

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ExcelDataProcessor:
    """
    Класс для обработки Excel-файлов и подготовки данных для анализа
    """
    
    def __init__(self, file_storage_path: str = None):
        """
        Инициализирует процессор Excel-данных
        """
        self.file_storage_path = file_storage_path or settings.UPLOAD_FOLDER
        if not os.path.isabs(self.file_storage_path):
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.file_storage_path = os.path.join(base_dir, self.file_storage_path.lstrip('./'))
            logger.info(f"Using absolute upload folder path: {self.file_storage_path}")
        
    def get_file_path(self, file_id: Union[int, str], db: Optional[Session] = None) -> str:
        """
        Получает полный путь к файлу по его ID
        """
        logger.info(f"Looking for file with ID {file_id} in {self.file_storage_path}")
        if db:
            try:
                from app.models.models import UploadedFile
                file_record = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
                if file_record and file_record.file_path:
                    if os.path.exists(file_record.file_path):
                        return file_record.file_path
                    if not os.path.isabs(file_record.file_path):
                        abs_path = os.path.join(self.file_storage_path, os.path.basename(file_record.file_path))
                        if os.path.exists(abs_path):
                            return abs_path
                        if file_record.cabinet_id:
                            cabinet_path = os.path.join(self.file_storage_path, str(file_record.cabinet_id), os.path.basename(file_record.file_path))
                            if os.path.exists(cabinet_path):
                                return cabinet_path
            except Exception as e:
                logger.warning(f"Error getting file path: {e}")
        # Поиск в файловой системе
        for root, dirs, files in os.walk(self.file_storage_path):
            for fname in files:
                base = os.path.splitext(fname)[0]
                if base.endswith(f"_{file_id}") or base.startswith(f"{file_id}_") or base == str(file_id):
                    return os.path.join(root, fname)
        # Подпапки кабинетов
        for d in os.listdir(self.file_storage_path):
            p = os.path.join(self.file_storage_path, d)
            if os.path.isdir(p):
                for fname in os.listdir(p):
                    if os.path.isfile(os.path.join(p, fname)):
                        return os.path.join(p, fname)
        # По умолчанию
        return os.path.join(self.file_storage_path, f"{file_id}.xlsx")

    def process_excel_file(self, file_path: str) -> Dict[str, Any]:
        logger.info(f"Processing Excel file: {file_path}")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        try:
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
                raise ValueError("Не удалось определить строку с заголовками.")
            # Строка с метками дат (предыдущая)
            date_idx = best_idx - 1 if best_idx > 0 else None
            if date_idx is not None:
                date_labels = df_raw.iloc[date_idx].fillna('').astype(str).tolist()
            else:
                date_labels = [''] * df_raw.shape[1]
            # Заголовки
            raw_headers = df_raw.iloc[best_idx].fillna('').astype(str).tolist()
            headers = [f"column_{i}" if h.strip() == '' else h.strip() for i, h in enumerate(raw_headers)]
            # Формируем DataFrame с данными
            df = df_raw.iloc[best_idx + 1:].copy()
            df.columns = headers
            # Определяем порядок: сначала недели (Wxx), потом остальные
            week_pattern = re.compile(r'^W\d+')
            week_cols = [h for h in headers if week_pattern.match(h)]
            other_cols = [h for h in headers if h not in week_cols]
            ordered_cols = week_cols + other_cols
            df = df[ordered_cols].reset_index(drop=True)
            # Информация по колонкам
            column_info = []
            for col in ordered_cols:
                idx = headers.index(col)
                label = date_labels[idx] if idx < len(date_labels) else ''
                column_info.append({'name': col, 'date_label': label})
            logger.info(f"Extracted columns: {ordered_cols}")
            # Проверка пустоты
            if df.empty or df.shape[1] == 0:
                logger.warning(f"Empty data in file: {file_path}")
                return {'error': 'File contains no data'}
            # Анализ
            result = self._prepare_data_for_analysis(df)
            result['columns_info'] = column_info
            return result
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            raise

    def _prepare_data_for_analysis(self, df: pd.DataFrame) -> Dict[str, Any]:
        df = self._clean_dataframe(df)
        info: Dict[str, Any] = {
            'rows_count': len(df),
            'columns_count': len(df.columns),
            'columns': list(df.columns),
            'data_types': {c: str(df[c].dtype) for c in df.columns},
            'missing_values': {c: int(df[c].isna().sum()) for c in df.columns},
            'sample_rows': df.head(5).to_dict(orient='records')
        }
        # Числовые и категориальные
        num_cols = df.select_dtypes(include=['number']).columns.tolist()
        cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        if num_cols:
            info['numeric_stats'] = df[num_cols].describe().to_dict()
        if cat_cols:
            info['categorical_stats'] = {c: df[c].value_counts().to_dict() for c in cat_cols if df[c].nunique() < 50}
        # Временные ряды
        date_cols = [c for c in df.columns if 'date' in c.lower() or 'time' in c.lower()]
        if date_cols and num_cols:
            ts: Dict[str, Any] = {}
            for dcol in date_cols:
                try:
                    df[dcol] = pd.to_datetime(df[dcol], errors='coerce')
                    for ncol in num_cols[:3]:
                        key = f"{dcol}_{ncol}"
                        ts[key] = df.groupby(pd.Grouper(key=dcol, freq='D'))[ncol].agg(['mean','sum','count']).reset_index().to_dict('records')
                except Exception:
                    pass
            info['time_series'] = ts
        info['data'] = df.head(1000).to_dict(orient='records')
        return info

    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        dfc = df.dropna(axis=1, thresh=int(len(df)*0.1))
        num = dfc.select_dtypes(include=['number']).columns
        dfc[num] = dfc[num].fillna(0)
        obj = dfc.select_dtypes(include=['object']).columns
        dfc[obj] = dfc[obj].fillna('')
        return dfc.drop_duplicates()

    def process_file_by_id(self, file_id: Union[int, str], db: Optional[Session] = None) -> Dict[str, Any]:
        path = self.get_file_path(file_id, db)
        return self.process_excel_file(path)

    def process_file(self, file_id: Union[int, str], db: Session) -> Dict[str, Any]:
        from app.models.models import UploadedFile
        rec = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
        if rec and os.path.exists(rec.file_path):
            path = rec.file_path
        else:
            path = self.get_file_path(file_id, db)
            rec.file_path = path; db.commit()
        res = self.process_excel_file(path)
        rec.processed = True; rec.processing_result = f"{res.get('rows_count')} rows processed"; db.commit()
        return res

# Экземпляры
excel_processor = ExcelDataProcessor()
excel_data_processor = excel_processor
