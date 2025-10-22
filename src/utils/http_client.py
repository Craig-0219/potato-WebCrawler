"""
HTTP 客戶端 - 處理網頁請求
"""

import requests
from typing import Optional, Dict
import time


class HttpClient:
    """HTTP 請求客戶端"""

    def __init__(self, headers: Optional[Dict[str, str]] = None, delay: float = 1.0):
        """
        初始化 HTTP 客戶端

        Args:
            headers: 自定義請求標頭
            delay: 請求間隔延遲（秒）
        """
        self.session = requests.Session()
        self.delay = delay

        # 預設 User-Agent
        default_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                         '(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        if headers:
            default_headers.update(headers)

        self.session.headers.update(default_headers)
        self.last_request_time = 0

    def get(self, url: str, **kwargs) -> requests.Response:
        """
        發送 GET 請求

        Args:
            url: 目標 URL
            **kwargs: 其他請求參數

        Returns:
            Response 對象
        """
        # 實施請求延遲
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time

        if time_since_last_request < self.delay:
            time.sleep(self.delay - time_since_last_request)

        response = self.session.get(url, **kwargs)
        response.raise_for_status()

        self.last_request_time = time.time()

        return response

    def close(self):
        """關閉會話"""
        self.session.close()
