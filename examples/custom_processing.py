"""
進階範例 - 自定義資料處理
"""

import sys
sys.path.append('..')

from src.core.crawler import WebCrawler


def custom_data_processing():
    """自定義資料處理範例"""

    # 創建爬蟲
    crawler = WebCrawler("../configs/example_quotes.yaml")

    # 爬取資料
    data = crawler.crawl()

    # 自定義處理邏輯
    print("=== 開始處理資料 ===")

    for item in data:
        print(f"\n標題: {item.get('title', 'N/A')}")

        # 處理名言列表
        quotes = item.get('quotes', [])
        if quotes:
            print(f"名言數量: {len(quotes)}")
            print("前 3 條名言:")
            for i, quote in enumerate(quotes[:3], 1):
                print(f"  {i}. {quote}")

        # 處理作者列表
        authors = item.get('authors', [])
        if authors:
            print(f"作者: {', '.join(set(authors[:5]))}")

    # 儲存處理後的資料
    crawler.save()
    print("\n=== 資料處理完成 ===")


if __name__ == "__main__":
    custom_data_processing()
