"""
主程式入口
"""

import sys
from pathlib import Path
from src.core.crawler import WebCrawler


def main():
    """主函數"""
    if len(sys.argv) < 2:
        print("使用方式: python main.py <配置文件路徑>")
        print("範例: python main.py configs/example.yaml")
        sys.exit(1)

    config_path = sys.argv[1]

    if not Path(config_path).exists():
        print(f"錯誤: 配置文件不存在 - {config_path}")
        sys.exit(1)

    try:
        # 創建並執行爬蟲
        crawler = WebCrawler(config_path)
        crawler.run()

    except Exception as e:
        print(f"執行失敗: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
