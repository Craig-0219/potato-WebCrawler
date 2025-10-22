"""
主程式入口
"""

import sys
import argparse
import logging
from pathlib import Path
from typing import Optional
import yaml
import json

from src.core.crawler import WebCrawler
from src.config.loader import ConfigLoader


# 設定結束碼常數
EXIT_SUCCESS = 0
EXIT_CONFIG_ERROR = 1
EXIT_FILE_NOT_FOUND = 2
EXIT_VALIDATION_ERROR = 3
EXIT_NETWORK_ERROR = 4
EXIT_RUNTIME_ERROR = 5


def setup_logging(log_level: str, log_file: Optional[str] = None) -> None:
    """
    設定日誌系統

    Args:
        log_level: 日誌層級 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: 日誌輸出檔案路徑（選填）
    """
    # 轉換日誌層級
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        numeric_level = logging.INFO

    # 設定日誌格式
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'

    # 設定處理器
    handlers = [logging.StreamHandler(sys.stdout)]

    if log_file:
        try:
            log_path = Path(log_file).resolve()
            log_path.parent.mkdir(parents=True, exist_ok=True)
            handlers.append(logging.FileHandler(log_file, encoding='utf-8'))
        except Exception as e:
            print(f"警告: 無法建立日誌檔案 {log_file}: {e}", file=sys.stderr)

    # 配置 logging
    logging.basicConfig(
        level=numeric_level,
        format=log_format,
        datefmt=date_format,
        handlers=handlers
    )


def validate_config_schema(config: dict) -> tuple[bool, Optional[str]]:
    """
    驗證配置檔案 schema

    Args:
        config: 配置字典

    Returns:
        (是否有效, 錯誤訊息)
    """
    logger = logging.getLogger(__name__)

    # 必要欄位
    required_fields = {
        'name': str,
        'start_url': str,
        'extract_rules': list
    }

    # 檢查必要欄位
    for field, expected_type in required_fields.items():
        if field not in config:
            return False, f"缺少必要欄位: {field}"

        if not isinstance(config[field], expected_type):
            return False, f"欄位 {field} 類型錯誤，預期 {expected_type.__name__}"

    # 檢查 extract_rules 格式
    if not config['extract_rules']:
        return False, "extract_rules 不能為空"

    for i, rule in enumerate(config['extract_rules']):
        if not isinstance(rule, dict):
            return False, f"extract_rules[{i}] 必須是字典"

        # 檢查規則必要欄位
        if 'field' not in rule:
            return False, f"extract_rules[{i}] 缺少 'field' 欄位"

        if 'selector' not in rule:
            return False, f"extract_rules[{i}] 缺少 'selector' 欄位"

        rule_type = rule.get('type', 'css')
        if rule_type not in ['css', 'xpath']:
            return False, f"extract_rules[{i}] 的 type 必須是 'css' 或 'xpath'"

    # 檢查 output 格式（選填）
    if 'output' in config:
        output = config['output']
        if not isinstance(output, dict):
            return False, "output 必須是字典"

        if 'format' in output:
            if output['format'] not in ['json', 'csv']:
                return False, f"不支援的輸出格式: {output['format']}"

    logger.info("配置檔案驗證通過")
    return True, None


def parse_arguments() -> argparse.Namespace:
    """
    解析命令行參數

    Returns:
        解析後的參數
    """
    parser = argparse.ArgumentParser(
        description='Potato Web Crawler - 模組化網頁爬蟲工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用範例:
  python main.py configs/example.yaml
  python main.py -c configs/example.yaml --log-level DEBUG
  python main.py -c configs/example.yaml --dry-run
  python main.py -c configs/example.yaml --log-file crawler.log

更多資訊請參考: README.md
        """
    )

    # 配置檔案參數
    parser.add_argument(
        'config',
        nargs='?',
        type=str,
        help='配置文件路徑 (YAML 或 JSON)'
    )

    parser.add_argument(
        '-c', '--config',
        dest='config_file',
        type=str,
        help='配置文件路徑 (替代位置參數)'
    )

    # 日誌相關
    parser.add_argument(
        '--log-level',
        type=str,
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help='日誌層級 (預設: INFO)'
    )

    parser.add_argument(
        '--log-file',
        type=str,
        help='日誌輸出檔案路徑'
    )

    # 執行模式
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='僅驗證配置檔案，不執行爬蟲'
    )

    parser.add_argument(
        '-v', '--validate-only',
        action='store_true',
        help='僅驗證配置檔案格式'
    )

    # 輸出控制
    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='安靜模式，減少輸出'
    )

    parser.add_argument(
        '--version',
        action='version',
        version='Potato Web Crawler v1.0.0'
    )

    return parser.parse_args()


def load_and_validate_config(config_path: Path) -> tuple[Optional[dict], int]:
    """
    載入並驗證配置檔案

    Args:
        config_path: 配置檔案路徑

    Returns:
        (配置字典, 結束碼)
    """
    logger = logging.getLogger(__name__)

    # 檢查檔案是否存在
    if not config_path.exists():
        logger.error(f"配置檔案不存在: {config_path}")
        return None, EXIT_FILE_NOT_FOUND

    # 檢查檔案權限
    if not config_path.is_file():
        logger.error(f"路徑不是檔案: {config_path}")
        return None, EXIT_FILE_NOT_FOUND

    try:
        # 嘗試載入配置
        config = ConfigLoader.load(str(config_path))
        logger.info(f"成功載入配置檔案: {config_path}")

    except yaml.YAMLError as e:
        logger.error(f"YAML 解析錯誤: {e}")
        logger.debug(f"詳細錯誤資訊", exc_info=True)
        return None, EXIT_CONFIG_ERROR

    except json.JSONDecodeError as e:
        logger.error(f"JSON 解析錯誤: {e}")
        logger.debug(f"詳細錯誤資訊", exc_info=True)
        return None, EXIT_CONFIG_ERROR

    except ValueError as e:
        logger.error(f"配置格式錯誤: {e}")
        return None, EXIT_CONFIG_ERROR

    except PermissionError:
        logger.error(f"無權限讀取檔案: {config_path}")
        return None, EXIT_FILE_NOT_FOUND

    except Exception as e:
        logger.error(f"載入配置檔案時發生未預期的錯誤: {e}")
        logger.debug("詳細錯誤資訊", exc_info=True)
        return None, EXIT_CONFIG_ERROR

    # 驗證配置格式
    try:
        is_valid, error_msg = validate_config_schema(config)
        if not is_valid:
            logger.error(f"配置驗證失敗: {error_msg}")
            return None, EXIT_VALIDATION_ERROR

        logger.info("配置驗證通過")

    except Exception as e:
        logger.error(f"驗證配置時發生錯誤: {e}")
        logger.debug("詳細錯誤資訊", exc_info=True)
        return None, EXIT_VALIDATION_ERROR

    return config, EXIT_SUCCESS


def run_crawler(config_path: Path, dry_run: bool = False) -> int:
    """
    執行爬蟲

    Args:
        config_path: 配置檔案路徑
        dry_run: 是否為測試執行

    Returns:
        結束碼
    """
    logger = logging.getLogger(__name__)

    if dry_run:
        logger.info("執行模式: 測試執行（不會實際爬取資料）")
        return EXIT_SUCCESS

    try:
        # 創建並執行爬蟲
        logger.info("開始初始化爬蟲...")
        crawler = WebCrawler(str(config_path))

        logger.info("開始執行爬蟲任務...")
        crawler.run()

        logger.info("爬蟲任務完成！")
        return EXIT_SUCCESS

    except ConnectionError as e:
        logger.error(f"網路連線錯誤: {e}")
        logger.info("請檢查網路連線或目標網站是否可訪問")
        return EXIT_NETWORK_ERROR

    except TimeoutError as e:
        logger.error(f"連線逾時: {e}")
        logger.info("目標網站回應時間過長，請稍後再試")
        return EXIT_NETWORK_ERROR

    except PermissionError as e:
        logger.error(f"權限錯誤: {e}")
        logger.info("請檢查輸出目錄的寫入權限")
        return EXIT_RUNTIME_ERROR

    except KeyboardInterrupt:
        logger.warning("使用者中斷執行")
        return EXIT_RUNTIME_ERROR

    except Exception as e:
        logger.error(f"執行爬蟲時發生錯誤: {e}")
        logger.debug("詳細錯誤資訊", exc_info=True)
        return EXIT_RUNTIME_ERROR


def main() -> int:
    """
    主函數

    Returns:
        結束碼
    """
    # 解析命令行參數
    args = parse_arguments()

    # 確定配置檔案路徑
    config_path_str = args.config_file or args.config

    if not config_path_str:
        print("錯誤: 請指定配置檔案路徑", file=sys.stderr)
        print("使用 --help 查看使用說明", file=sys.stderr)
        return EXIT_CONFIG_ERROR

    # 設定日誌
    if args.quiet:
        log_level = 'ERROR'
    else:
        log_level = args.log_level

    setup_logging(log_level, args.log_file)
    logger = logging.getLogger(__name__)

    # 顯示啟動資訊
    logger.info("=" * 60)
    logger.info("Potato Web Crawler v1.0.0")
    logger.info("=" * 60)

    # 標準化配置檔案路徑
    try:
        config_path = Path(config_path_str).resolve()
        logger.debug(f"解析配置檔案路徑: {config_path}")
    except Exception as e:
        logger.error(f"無效的檔案路徑: {config_path_str}")
        logger.debug(f"路徑解析錯誤: {e}", exc_info=True)
        return EXIT_FILE_NOT_FOUND

    # 載入並驗證配置
    config, exit_code = load_and_validate_config(config_path)

    if exit_code != EXIT_SUCCESS:
        return exit_code

    # 如果只是驗證模式，到此結束
    if args.validate_only:
        logger.info("✓ 配置檔案驗證通過")
        return EXIT_SUCCESS

    # 執行爬蟲
    return run_crawler(config_path, args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
