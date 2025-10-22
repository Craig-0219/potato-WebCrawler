"""
資料儲存模組 - 支援多種輸出格式
"""

import json
import csv
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

    def save(self, data: List[Dict[str, Any]], output_path: str):
        """
        儲存為 JSON 格式

        Args:
            data: 資料列表
            output_path: 輸出路徑
        """
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"資料已儲存至: {output_path}")


class CsvStorage(BaseStorage):
    """CSV 格式儲存"""

    def save(self, data: List[Dict[str, Any]], output_path: str):
        """
        儲存為 CSV 格式

        Args:
            data: 資料列表
            output_path: 輸出路徑
        """
        if not data:
            print("沒有資料需要儲存")
            return

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # 取得所有欄位名稱
        fieldnames = list(data[0].keys())

        with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)

        print(f"資料已儲存至: {output_path}")


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
