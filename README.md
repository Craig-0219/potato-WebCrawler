# Potato Web Crawler - 模組化網頁爬蟲

一套簡單易用、高度模組化的 Python 網頁爬蟲框架，支援配置文件驅動，讓你可以輕鬆更改爬蟲目標網站和提取項目。

## 特色功能

- **配置驅動** - 使用 YAML/JSON 配置文件定義爬蟲規則，無需修改程式碼
- **模組化設計** - 清晰的模組劃分，易於擴展和維護
- **多種提取方式** - 支援 CSS Selector 和 XPath 兩種資料提取方式
- **多種輸出格式** - 支援 JSON、CSV 等多種資料儲存格式
- **智慧延遲** - 內建請求延遲機制，避免對目標網站造成負擔
- **分頁支援** - 支援多頁爬取功能

## 專案結構

```
potato-WebCrawler/
├── src/
│   ├── core/           # 核心爬蟲引擎
│   │   └── crawler.py
│   ├── config/         # 配置系統
│   │   └── loader.py
│   ├── extractors/     # 資料提取器
│   │   └── extractor.py
│   ├── storage/        # 儲存模組
│   │   └── storage.py
│   └── utils/          # 工具模組
│       └── http_client.py
├── configs/            # 配置文件目錄
│   ├── template.yaml   # 配置模板
│   ├── example_quotes.yaml
│   └── example_books.yaml
├── examples/           # 範例程式
├── output/             # 輸出目錄
├── main.py             # 主程式入口
└── requirements.txt    # 依賴套件
```

## 安裝

1. 克隆專案

```bash
git clone <repository-url>
cd potato-WebCrawler
```

2. 安裝依賴

```bash
pip install -r requirements.txt
```

## 快速開始

### 基本用法

```bash
# 基本執行
python main.py configs/example_quotes.yaml

# 顯示幫助資訊
python main.py --help

# 顯示版本
python main.py --version
```

### 命令列參數

```bash
# 基本執行
python main.py <配置檔案>
python main.py -c <配置檔案>

# 設定日誌層級
python main.py configs/example.yaml --log-level DEBUG
python main.py configs/example.yaml --log-level INFO    # 預設
python main.py configs/example.yaml --log-level WARNING
python main.py configs/example.yaml --log-level ERROR

# 將日誌輸出到檔案
python main.py configs/example.yaml --log-file crawler.log

# 僅驗證配置檔案，不執行爬蟲
python main.py configs/example.yaml --validate-only
python main.py configs/example.yaml --dry-run

# 安靜模式（僅顯示錯誤）
python main.py configs/example.yaml --quiet

# 組合使用
python main.py configs/example.yaml --log-level DEBUG --log-file debug.log
```

### 1. 使用現有配置

使用預設的範例配置文件：

```bash
# 爬取名言網站
python main.py configs/example_quotes.yaml

# 爬取書籍網站
python main.py configs/example_books.yaml
```

### 2. 創建自己的爬蟲

複製配置模板並修改：

```bash
cp configs/template.yaml configs/my_crawler.yaml
```

編輯 `configs/my_crawler.yaml`：

```yaml
name: "我的新聞爬蟲"
start_url: "https://news.example.com"

extract_rules:
  - field: "title"
    type: "css"
    selector: "h1.article-title"
    multiple: false

  - field: "content"
    type: "css"
    selector: "div.article-content p"
    multiple: true

  - field: "author"
    type: "xpath"
    selector: "//span[@class='author']/text()"
    multiple: false

output:
  format: "json"
  path: "output/news.json"
```

執行爬蟲：

```bash
python main.py configs/my_crawler.yaml
```

## 配置說明

### 基本配置

```yaml
# 爬蟲名稱（必填）
name: "爬蟲名稱"

# 起始 URL（必填）
start_url: "https://example.com"

# HTTP 標頭（選填）
headers:
  User-Agent: "Mozilla/5.0..."
  Accept-Language: "zh-TW,zh;q=0.9"

# 請求延遲秒數（選填，預設 1.0）
delay: 1.0
```

### 資料提取規則

#### CSS Selector 提取

```yaml
extract_rules:
  # 提取文字內容
  - field: "title"
    type: "css"
    selector: "h1.title"
    multiple: false

  # 提取屬性值
  - field: "links"
    type: "css"
    selector: "a.link"
    attr: "href"
    multiple: true
```

#### XPath 提取

```yaml
extract_rules:
  - field: "descriptions"
    type: "xpath"
    selector: "//div[@class='desc']//p/text()"
    multiple: true
```

### 分頁配置

```yaml
pagination:
  max_pages: 5                    # 最大爬取頁數
  type: "css"                     # css 或 xpath
  next_page_selector: "a.next"    # 下一頁連結選擇器
```

### 輸出配置

```yaml
output:
  format: "json"              # json 或 csv
  path: "output/data.json"    # 輸出路徑
```

## 使用範例

### 範例 1: 爬取新聞標題和內容

```yaml
name: "新聞爬蟲"
start_url: "https://news.example.com"

extract_rules:
  - field: "headline"
    type: "css"
    selector: "h1.headline"

  - field: "paragraphs"
    type: "css"
    selector: "article p"
    multiple: true

  - field: "publish_date"
    type: "css"
    selector: "time.published"
    attr: "datetime"

output:
  format: "json"
  path: "output/news.json"
```

### 範例 2: 爬取商品資訊

```yaml
name: "商品爬蟲"
start_url: "https://shop.example.com/products"

extract_rules:
  - field: "product_names"
    type: "css"
    selector: "div.product h2"
    multiple: true

  - field: "prices"
    type: "css"
    selector: "span.price"
    multiple: true

  - field: "images"
    type: "css"
    selector: "img.product-img"
    attr: "src"
    multiple: true

output:
  format: "csv"
  path: "output/products.csv"
```

## 日誌系統

### 日誌層級說明

- **DEBUG** - 顯示詳細的除錯資訊，包括每個步驟的細節
- **INFO** - 顯示一般執行資訊（預設層級）
- **WARNING** - 僅顯示警告和錯誤
- **ERROR** - 僅顯示錯誤資訊
- **CRITICAL** - 僅顯示嚴重錯誤

### 日誌輸出範例

```bash
# INFO 層級輸出
2025-10-22 14:30:15 - __main__ - INFO - ============================================================
2025-10-22 14:30:15 - __main__ - INFO - Potato Web Crawler v1.0.0
2025-10-22 14:30:15 - __main__ - INFO - ============================================================
2025-10-22 14:30:15 - __main__ - INFO - 成功載入配置檔案: configs/example.yaml
2025-10-22 14:30:15 - __main__ - INFO - 配置檔案驗證通過
2025-10-22 14:30:15 - src.core.crawler - INFO - 開始爬取: 範例爬蟲
2025-10-22 14:30:15 - src.core.crawler - INFO - 目標 URL: https://example.com
```

### 日誌檔案

使用 `--log-file` 參數可將日誌儲存到檔案：

```bash
python main.py configs/example.yaml --log-file logs/crawler.log
```

日誌會同時輸出到終端和檔案，方便後續分析。

## 錯誤處理

程式提供詳細的錯誤訊息和結束碼：

| 結束碼 | 說明 | 常見原因 |
|--------|------|----------|
| 0 | 成功執行 | 爬蟲順利完成 |
| 1 | 配置錯誤 | YAML/JSON 格式錯誤 |
| 2 | 檔案不存在 | 配置檔案路徑錯誤 |
| 3 | 驗證錯誤 | 配置格式不符合要求 |
| 4 | 網路錯誤 | 無法連線目標網站 |
| 5 | 執行錯誤 | 爬取過程發生錯誤 |

### 常見錯誤處理

**配置格式錯誤**
```bash
$ python main.py configs/bad.yaml
2025-10-22 14:30:15 - __main__ - ERROR - YAML 解析錯誤: ...
# 解決方案: 檢查 YAML 語法，確保縮排正確
```

**網路連線錯誤**
```bash
$ python main.py configs/example.yaml
2025-10-22 14:30:15 - __main__ - ERROR - 網路連線錯誤: ...
2025-10-22 14:30:15 - __main__ - INFO - 請檢查網路連線或目標網站是否可訪問
# 解決方案: 檢查網路連線，確認目標網站可訪問
```

**權限錯誤**
```bash
$ python main.py configs/example.yaml
2025-10-22 14:30:15 - __main__ - ERROR - 權限錯誤: ...
# 解決方案: 確認輸出目錄有寫入權限
```

## 配置檔案驗證

在實際執行前，可以先驗證配置檔案：

```bash
# 方法 1: 使用 --validate-only
python main.py configs/my_config.yaml --validate-only

# 方法 2: 使用 --dry-run
python main.py configs/my_config.yaml --dry-run
```

成功輸出：
```
✓ 配置檔案驗證通過
```

失敗輸出：
```
ERROR - 配置驗證失敗: 缺少必要欄位: start_url
```

## 進階使用

### 自定義 HTTP 標頭

某些網站需要特定的 HTTP 標頭：

```yaml
headers:
  User-Agent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
  Accept: "text/html,application/xhtml+xml"
  Accept-Language: "zh-TW,zh;q=0.9"
  Referer: "https://example.com"
```

### 處理動態延遲

調整請求延遲以避免被封鎖：

```yaml
delay: 2.0  # 每次請求間隔 2 秒
```

## 模組說明

### 核心模組 (src/core)

- `crawler.py` - 主要爬蟲引擎，協調各模組運作

### 配置模組 (src/config)

- `loader.py` - 配置文件加載器，支援 YAML/JSON

### 提取模組 (src/extractors)

- `extractor.py` - 資料提取器，支援 CSS Selector 和 XPath

### 儲存模組 (src/storage)

- `storage.py` - 資料儲存適配器，支援 JSON、CSV

### 工具模組 (src/utils)

- `http_client.py` - HTTP 客戶端，處理網頁請求

## 常見問題

### Q: 如何新增爬取一個新網站？

A: 複製 `configs/template.yaml`，修改 `start_url` 和 `extract_rules`，然後執行：

```bash
python main.py configs/your_config.yaml
```

### Q: 如何知道要用什麼 CSS Selector？

A: 使用瀏覽器的開發者工具（F12），在元素上右鍵選擇「檢查」，然後右鍵選擇「Copy > Copy selector」。

### Q: CSS Selector 和 XPath 哪個比較好？

A: CSS Selector 比較簡潔易讀，適合大多數情況；XPath 功能更強大，適合複雜的選擇需求。

### Q: 如何避免被網站封鎖？

A:
1. 增加請求延遲 (`delay` 參數)
2. 使用合適的 User-Agent
3. 遵守網站的 robots.txt 規則
4. 不要過度頻繁地爬取

## 注意事項

1. **遵守法律法規** - 請確保你的爬蟲行為符合當地法律和網站服務條款
2. **尊重 robots.txt** - 檢查並遵守目標網站的爬蟲規則
3. **合理延遲** - 設定適當的請求延遲，避免對網站造成負擔
4. **錯誤處理** - 網站結構可能變更，定期檢查和更新配置文件

## 授權

MIT License

## 貢獻

歡迎提交 Issue 和 Pull Request！

## 聯絡

如有問題或建議，請開啟 Issue。
