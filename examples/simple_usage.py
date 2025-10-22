"""
簡單使用範例 - 直接在程式碼中使用爬蟲
"""

import sys
sys.path.append('..')

from src.core.crawler import WebCrawler


def example_1():
    """範例 1: 使用配置文件"""
    print("=== 範例 1: 使用配置文件 ===")

    crawler = WebCrawler("../configs/example_quotes.yaml")
    crawler.run()


def example_2():
    """範例 2: 程式化創建爬蟲（需要先創建配置文件）"""
    print("\n=== 範例 2: 爬取書籍資料 ===")

    crawler = WebCrawler("../configs/example_books.yaml")
    data = crawler.crawl()

    # 處理爬取的資料
    print(f"總共爬取 {len(data)} 筆資料")

    # 儲存資料
    crawler.save()


if __name__ == "__main__":
    # 執行範例 1
    # example_1()

    # 執行範例 2
    example_2()
