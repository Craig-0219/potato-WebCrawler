"""
核心爬蟲引擎
"""

import logging
from typing import Dict, Any, List, Optional, Set
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
        self.logger = logging.getLogger(__name__)

        # 加載配置
        self.config = ConfigLoader.load(config_path)
        ConfigLoader.validate(self.config)

        # 初始化 HTTP 客戶端
        headers = self.config.get('headers', {})
        delay = self.config.get('delay', 1.0)
        timeout = self.config.get('timeout', 30)
        max_retries = self.config.get('max_retries', 3)

        self.http_client = HttpClient(
            headers=headers,
            delay=delay,
            timeout=timeout,
            max_retries=max_retries
        )

        # 儲存設定
        self.storage_type = self.config.get('output', {}).get('format', 'json')
        self.output_path = self.config.get('output', {}).get('path', 'output/data.json')

        # 爬取結果
        self.results = []

        # URL 去重集合
        self.visited_urls: Set[str] = set()

        self.logger.debug(f"爬蟲初始化完成: {self.config['name']}")

    def crawl(self) -> List[Dict[str, Any]]:
        """
        執行爬蟲

        Returns:
            爬取結果列表
        """
        self.logger.info(f"開始爬取: {self.config['name']}")
        self.logger.info(f"目標 URL: {self.config['start_url']}")

        try:
            # 發送請求
            self.logger.debug(f"正在請求網頁...")
            response = self.http_client.get(self.config['start_url'])
            self.logger.info(f"成功獲取網頁內容 (狀態碼: {response.status_code})")

            # 記錄已訪問的 URL
            self.visited_urls.add(response.url)

            # 提取資料
            self.logger.debug("開始提取資料...")
            extractor = DataExtractor(response.text)
            data = extractor.extract_all(self.config['extract_rules'])

            self.results.append(data)
            self.logger.info(f"成功提取資料，包含 {len(data)} 個欄位")
            self.logger.debug(f"提取的資料: {data}")

            # 如果有分頁或多頁爬取邏輯
            if 'pagination' in self.config:
                self.logger.info("偵測到分頁配置，開始處理分頁...")
                self._handle_pagination(extractor)

            return self.results

        except Exception as e:
            self.logger.error(f"爬取過程發生錯誤: {str(e)}")
            self.logger.debug("詳細錯誤資訊", exc_info=True)
            raise

        finally:
            self.http_client.close()
            self.logger.debug("HTTP 客戶端已關閉")

    def _is_valid_next_page(self, extractor: DataExtractor, selector: str, selector_type: str) -> bool:
        """
        檢查下一頁連結是否有效

        Args:
            extractor: 資料提取器
            selector: 選擇器
            selector_type: 選擇器類型 (css 或 xpath)

        Returns:
            是否為有效的下一頁連結
        """
        try:
            if selector_type == 'css':
                # 檢查元素是否存在且未被禁用
                elements = extractor.soup.select(selector)
                if not elements:
                    return False

                element = elements[0]

                # 檢查常見的禁用狀態
                # 1. disabled 屬性
                if element.get('disabled'):
                    self.logger.debug("下一頁連結已禁用 (disabled 屬性)")
                    return False

                # 2. disabled class
                element_classes = element.get('class', [])
                if isinstance(element_classes, list):
                    disabled_classes = {'disabled', 'inactive', 'unavailable'}
                    if any(cls in disabled_classes for cls in element_classes):
                        self.logger.debug(f"下一頁連結已禁用 (class: {element_classes})")
                        return False

                # 3. aria-disabled
                if element.get('aria-disabled') == 'true':
                    self.logger.debug("下一頁連結已禁用 (aria-disabled)")
                    return False

                # 4. 檢查是否有 href
                href = element.get('href')
                if not href or href in ['#', 'javascript:void(0)', 'javascript:;']:
                    self.logger.debug(f"下一頁連結無效 (href: {href})")
                    return False

                return True

            else:  # xpath
                # XPath 的情況，只檢查是否存在結果
                results = extractor.tree.xpath(selector)
                return len(results) > 0

        except Exception as e:
            self.logger.warning(f"檢查下一頁連結時發生錯誤: {e}")
            return False

    def _handle_pagination(self, page_extractor: DataExtractor):
        """
        處理分頁爬取

        Args:
            page_extractor: 當前頁面的提取器
        """
        pagination_config = self.config['pagination']
        max_pages = pagination_config.get('max_pages', 1)
        next_page_selector = pagination_config.get('next_page_selector')
        next_page_type = pagination_config.get('type', 'css')

        self.logger.debug(f"分頁設定: 最多 {max_pages} 頁")
        current_page = 1

        while current_page < max_pages:
            # 檢查下一頁連結是否有效
            if not self._is_valid_next_page(page_extractor, next_page_selector, next_page_type):
                self.logger.info(f"已到達最後一頁（第 {current_page} 頁）")
                break

            # 提取下一頁 URL
            if next_page_type == 'css':
                next_urls = page_extractor.extract_by_css(
                    next_page_selector,
                    attr='href'
                )
            else:
                next_urls = page_extractor.extract_by_xpath(
                    next_page_selector,
                    attr='href'
                )

            if not next_urls or not next_urls[0]:
                self.logger.info(f"無法找到下一頁 URL（第 {current_page} 頁）")
                break

            next_url = next_urls[0]

            # URL 去重檢查
            # 使用 http_client 的 resolve_url 來標準化 URL
            resolved_url = self.http_client.resolve_url(next_url)

            if resolved_url in self.visited_urls:
                self.logger.warning(f"偵測到重複 URL，停止分頁: {resolved_url}")
                break

            self.logger.info(f"正在爬取第 {current_page + 1} 頁: {resolved_url}")

            try:
                # 請求下一頁（http_client 會自動處理相對 URL）
                response = self.http_client.get(next_url)

                # 記錄已訪問的 URL
                self.visited_urls.add(response.url)

                # 提取資料
                page_extractor = DataExtractor(response.text)
                data = page_extractor.extract_all(self.config['extract_rules'])

                self.results.append(data)
                self.logger.debug(f"第 {current_page + 1} 頁資料提取完成")

                current_page += 1

            except Exception as e:
                self.logger.warning(f"爬取第 {current_page + 1} 頁時發生錯誤: {str(e)}")
                self.logger.debug("詳細錯誤資訊", exc_info=True)
                break

        self.logger.info(f"分頁爬取完成，共爬取 {current_page} 頁")

    def save(self):
        """儲存爬取結果"""
        if not self.results:
            self.logger.warning("沒有資料需要儲存")
            return

        self.logger.info(f"正在儲存資料到 {self.output_path}...")
        storage = StorageFactory.create(self.storage_type)
        storage.save(self.results, self.output_path)
        self.logger.info(f"資料儲存完成！格式: {self.storage_type}")

    def run(self):
        """執行完整的爬取流程"""
        self.crawl()
        self.save()
        self.logger.info(f"爬取任務完成！共獲取 {len(self.results)} 筆資料")
