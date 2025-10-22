"""
HTTP 客戶端 - 處理網頁請求
"""

import requests
import logging
import time
import random
from typing import Optional, Dict
from urllib.parse import urljoin, urlparse


class HttpClient:
    """HTTP 請求客戶端"""

    def __init__(
        self,
        headers: Optional[Dict[str, str]] = None,
        delay: float = 1.0,
        timeout: int = 30,
        max_retries: int = 3,
        backoff_factor: float = 0.5
    ):
        """
        初始化 HTTP 客戶端

        Args:
            headers: 自定義請求標頭
            delay: 請求間隔延遲（秒）
            timeout: 請求超時時間（秒）
            max_retries: 最大重試次數
            backoff_factor: 退避係數（重試延遲倍數）
        """
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        self.delay = delay
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor

        # 預設 User-Agent
        default_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                         '(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }

        if headers:
            default_headers.update(headers)

        self.session.headers.update(default_headers)
        self.last_request_time = 0
        self.current_base_url = None

        self.logger.debug(f"HTTP 客戶端初始化: delay={delay}s, timeout={timeout}s, max_retries={max_retries}")

    def _apply_delay_with_jitter(self):
        """實施請求延遲（含隨機抖動）"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time

        # 加入 ±20% 的隨機抖動，避免規律性請求
        jitter = random.uniform(0.8, 1.2)
        actual_delay = self.delay * jitter

        if time_since_last_request < actual_delay:
            sleep_time = actual_delay - time_since_last_request
            self.logger.debug(f"請求延遲: {sleep_time:.2f}s")
            time.sleep(sleep_time)

    def resolve_url(self, url: str, base_url: Optional[str] = None) -> str:
        """
        解析 URL，處理相對路徑

        Args:
            url: 目標 URL（可能是相對路徑）
            base_url: 基礎 URL

        Returns:
            完整的絕對 URL
        """
        # 如果沒有提供 base_url，使用當前的 base_url
        if base_url is None:
            base_url = self.current_base_url

        # 如果 URL 已經是完整路徑，直接返回
        if url.startswith(('http://', 'https://')):
            return url

        # 處理相對路徑
        if base_url:
            resolved = urljoin(base_url, url)
            self.logger.debug(f"URL 解析: {url} -> {resolved}")
            return resolved
        else:
            self.logger.warning(f"無法解析相對 URL（缺少 base_url）: {url}")
            return url

    def get(self, url: str, **kwargs) -> requests.Response:
        """
        發送 GET 請求（含重試機制）

        Args:
            url: 目標 URL
            **kwargs: 其他請求參數

        Returns:
            Response 對象

        Raises:
            requests.exceptions.RequestException: 請求失敗
        """
        # 解析相對 URL
        url = self.resolve_url(url)

        # 更新當前 base URL
        parsed = urlparse(url)
        self.current_base_url = f"{parsed.scheme}://{parsed.netloc}"

        # 設定預設 timeout
        if 'timeout' not in kwargs:
            kwargs['timeout'] = self.timeout

        # 實施延遲
        self._apply_delay_with_jitter()

        # 重試邏輯
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                self.logger.debug(f"請求 URL: {url} (嘗試 {attempt + 1}/{self.max_retries})")

                response = self.session.get(url, **kwargs)
                response.raise_for_status()

                self.last_request_time = time.time()

                # 記錄成功資訊
                self.logger.debug(
                    f"請求成功: {url} "
                    f"[狀態碼: {response.status_code}, "
                    f"大小: {len(response.content)} bytes]"
                )

                return response

            except requests.exceptions.Timeout as e:
                last_exception = e
                self.logger.warning(
                    f"請求超時 ({attempt + 1}/{self.max_retries}): {url}"
                )

            except requests.exceptions.ConnectionError as e:
                last_exception = e
                self.logger.warning(
                    f"連線錯誤 ({attempt + 1}/{self.max_retries}): {url} - {str(e)}"
                )

            except requests.exceptions.HTTPError as e:
                last_exception = e
                status_code = e.response.status_code if e.response else 'Unknown'

                # 4xx 錯誤通常不需要重試
                if 400 <= status_code < 500:
                    self.logger.error(f"HTTP 錯誤 {status_code}: {url}")
                    raise

                self.logger.warning(
                    f"HTTP 錯誤 {status_code} ({attempt + 1}/{self.max_retries}): {url}"
                )

            except requests.exceptions.RequestException as e:
                last_exception = e
                self.logger.warning(
                    f"請求失敗 ({attempt + 1}/{self.max_retries}): {url} - {str(e)}"
                )

            # 如果不是最後一次嘗試，等待後重試（指數退避）
            if attempt < self.max_retries - 1:
                backoff_time = self.backoff_factor * (2 ** attempt)
                self.logger.debug(f"等待 {backoff_time:.2f}s 後重試...")
                time.sleep(backoff_time)

        # 所有重試都失敗
        self.logger.error(f"請求失敗，已達最大重試次數 ({self.max_retries}): {url}")
        if last_exception:
            raise last_exception
        else:
            raise requests.exceptions.RequestException(f"請求失敗: {url}")

    def close(self):
        """關閉會話"""
        self.logger.debug("關閉 HTTP 客戶端")
        self.session.close()
