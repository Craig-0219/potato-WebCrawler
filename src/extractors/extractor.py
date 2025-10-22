"""
資料提取器 - 支援 CSS Selector 和 XPath
"""

import logging
from bs4 import BeautifulSoup
from lxml import etree
from typing import List, Dict, Any, Optional


class DataExtractor:
    """資料提取器"""

    def __init__(self, html: str):
        """
        初始化提取器

        Args:
            html: HTML 內容
        """
        self.logger = logging.getLogger(__name__)
        self.html = html
        self.soup = BeautifulSoup(html, 'lxml')
        self.tree = etree.HTML(html)
        self.logger.debug("資料提取器初始化完成")

    def extract_by_css(self, selector: str, attr: Optional[str] = None) -> List[str]:
        """
        使用 CSS Selector 提取資料

        Args:
            selector: CSS 選擇器
            attr: 要提取的屬性名稱，None 表示提取文本

        Returns:
            提取結果列表
        """
        elements = self.soup.select(selector)
        results = []

        for element in elements:
            if attr:
                value = element.get(attr, '')
            else:
                value = element.get_text(strip=True)
            results.append(value)

        return results

    def extract_by_xpath(self, xpath: str) -> List[str]:
        """
        使用 XPath 提取資料

        Args:
            xpath: XPath 表達式

        Returns:
            提取結果列表
        """
        results = self.tree.xpath(xpath)

        # 轉換為字符串列表
        return [str(r).strip() if not isinstance(r, str) else r.strip() for r in results]

    def extract_all(self, rules: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        根據規則提取所有資料

        Args:
            rules: 提取規則列表
                  [{
                      "field": "title",
                      "type": "css",  # or "xpath"
                      "selector": "h1.title",
                      "attr": None,  # optional
                      "multiple": False  # optional, 是否提取多個
                  }]

        Returns:
            提取結果字典
        """
        data = {}

        for rule in rules:
            field = rule['field']
            rule_type = rule.get('type', 'css')
            selector = rule['selector']
            attr = rule.get('attr')
            multiple = rule.get('multiple', False)

            try:
                if rule_type == 'css':
                    results = self.extract_by_css(selector, attr)
                elif rule_type == 'xpath':
                    results = self.extract_by_xpath(selector)
                else:
                    raise ValueError(f"不支援的提取類型: {rule_type}")

                # 根據 multiple 設定決定返回單個還是多個結果
                if multiple:
                    data[field] = results
                    self.logger.debug(f"欄位 '{field}' 提取成功: {len(results)} 個項目")
                else:
                    data[field] = results[0] if results else None
                    self.logger.debug(f"欄位 '{field}' 提取成功")

            except Exception as e:
                self.logger.warning(f"提取欄位 '{field}' 時發生錯誤: {str(e)}")
                self.logger.debug(f"選擇器: {selector}, 類型: {rule_type}")
                data[field] = None if not multiple else []

        return data
