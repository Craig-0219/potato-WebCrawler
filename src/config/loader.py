"""
配置加載器 - 支援 YAML 和 JSON 格式
"""

import json
import yaml
from pathlib import Path
from typing import Dict, Any


class ConfigLoader:
    """配置文件加載器"""

    @staticmethod
    def load(config_path: str) -> Dict[str, Any]:
        """
        加載配置文件

        Args:
            config_path: 配置文件路徑

        Returns:
            配置字典
        """
        path = Path(config_path)

        if not path.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_path}")

        with open(path, 'r', encoding='utf-8') as f:
            if path.suffix in ['.yaml', '.yml']:
                return yaml.safe_load(f)
            elif path.suffix == '.json':
                return json.load(f)
            else:
                raise ValueError(f"不支援的配置文件格式: {path.suffix}")

    @staticmethod
    def validate(config: Dict[str, Any]) -> bool:
        """
        驗證配置文件格式

        Args:
            config: 配置字典

        Returns:
            是否有效
        """
        required_fields = ['name', 'start_url', 'extract_rules']

        for field in required_fields:
            if field not in config:
                raise ValueError(f"配置文件缺少必要欄位: {field}")

        return True
