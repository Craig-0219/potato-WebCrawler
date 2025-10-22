"""
核心爬蟲引擎
"""

from typing import Dict, Any, List, Optional
from ..config.loader import ConfigLoader
from ..utils.http_client import HttpClient
from ..extractors.extractor import DataExtractor
from ..storage.storage import StorageFactory


class WebCrawler:
    """網頁爬蟲核心引擎"""

    def __init__(self, config_path: str):
        """
        初始化爬蟲

        Args:
            config_path: 配置文件路徑
        """
        # 加載配置
        self.config = ConfigLoader.load(config_path)
        ConfigLoader.validate(self.config)

        # 初始化 HTTP 客戶端
        headers = self.config.get('headers', {})
        delay = self.config.get('delay', 1.0)
        self.http_client = HttpClient(headers=headers, delay=delay)

        # 儲存設定
        self.storage_type = self.config.get('output', {}).get('format', 'json')
        self.output_path = self.config.get('output', {}).get('path', 'output/data.json')

        # 爬取結果
        self.results = []

    def crawl(self) -> List[Dict[str, Any]]:
        """
        執行爬蟲

        Returns:
            爬取結果列表
        """
        print(f"開始爬取: {self.config['name']}")
        print(f"目標 URL: {self.config['start_url']}\n")

        try:
            # 發送請求
            response = self.http_client.get(self.config['start_url'])
            print(f"成功獲取網頁內容 (狀態碼: {response.status_code})")

            # 提取資料
            extractor = DataExtractor(response.text)
            data = extractor.extract_all(self.config['extract_rules'])

            self.results.append(data)
            print(f"提取資料: {data}\n")

            # 如果有分頁或多頁爬取邏輯
            if 'pagination' in self.config:
                self._handle_pagination(extractor)

            return self.results

        except Exception as e:
            print(f"爬取過程發生錯誤: {str(e)}")
            raise

        finally:
            self.http_client.close()

    def _handle_pagination(self, initial_extractor: DataExtractor):
        """
        處理分頁爬取

        Args:
            initial_extractor: 初始頁面的提取器
        """
        pagination_config = self.config['pagination']
        max_pages = pagination_config.get('max_pages', 1)
        next_page_selector = pagination_config.get('next_page_selector')
        next_page_type = pagination_config.get('type', 'css')

        current_page = 1

        while current_page < max_pages:
            # 提取下一頁 URL
            if next_page_type == 'css':
                next_urls = initial_extractor.extract_by_css(
                    next_page_selector,
                    attr='href'
                )
            else:
                next_urls = initial_extractor.extract_by_xpath(next_page_selector)

            if not next_urls:
                print("沒有更多頁面")
                break

            next_url = next_urls[0]
            print(f"爬取第 {current_page + 1} 頁: {next_url}")

            try:
                response = self.http_client.get(next_url)
                extractor = DataExtractor(response.text)
                data = extractor.extract_all(self.config['extract_rules'])
                self.results.append(data)
                print(f"提取資料: {data}\n")

                initial_extractor = extractor
                current_page += 1

            except Exception as e:
                print(f"爬取分頁時發生錯誤: {str(e)}")
                break

    def save(self):
        """儲存爬取結果"""
        if not self.results:
            print("沒有資料需要儲存")
            return

        storage = StorageFactory.create(self.storage_type)
        storage.save(self.results, self.output_path)

    def run(self):
        """執行完整的爬取流程"""
        self.crawl()
        self.save()
        print(f"\n爬取完成！共獲取 {len(self.results)} 筆資料")
