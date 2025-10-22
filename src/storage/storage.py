"""
資料儲存模組 - 支援多種輸出格式
"""

import json
import csv
import logging
from pathlib import Path
from typing import List, Dict, Any
from abc import ABC, abstractmethod


class BaseStorage(ABC):
    """儲存基類"""

    @abstractmethod
    def save(self, data: List[Dict[str, Any]], output_path: str):
        """儲存資料"""
        pass


class JsonStorage(BaseStorage):
    """JSON 格式儲存"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def save(self, data: List[Dict[str, Any]], output_path: str):
        """
        儲存為 JSON 格式

        Args:
            data: 資料列表
            output_path: 輸出路徑
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        self.logger.debug(f"正在寫入 JSON 檔案: {output_path}")

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        file_size = output_file.stat().st_size
        self.logger.info(f"JSON 檔案已儲存: {output_path} ({file_size} bytes)")


class CsvStorage(BaseStorage):
    """CSV 格式儲存"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def save(self, data: List[Dict[str, Any]], output_path: str):
        """
        儲存為 CSV 格式

        Args:
            data: 資料列表
            output_path: 輸出路徑
        """
        if not data:
            self.logger.warning("沒有資料需要儲存")
            return

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # 取得所有欄位名稱
        fieldnames = list(data[0].keys())
        self.logger.debug(f"CSV 欄位: {', '.join(fieldnames)}")

        with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)

        file_size = output_file.stat().st_size
        self.logger.info(f"CSV 檔案已儲存: {output_path} ({file_size} bytes, {len(data)} 筆資料)")


class StorageFactory:
    """儲存工廠類"""

    _storage_map = {
        'json': JsonStorage,
        'csv': CsvStorage,
    }

    @classmethod
    def create(cls, storage_type: str) -> BaseStorage:
        """
        創建儲存實例

        Args:
            storage_type: 儲存類型 (json, csv)

        Returns:
            儲存實例
        """
        storage_class = cls._storage_map.get(storage_type.lower())

        if not storage_class:
            raise ValueError(f"不支援的儲存類型: {storage_type}")

        return storage_class()
