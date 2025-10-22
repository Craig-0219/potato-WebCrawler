# 核心改進說明

本文檔詳細說明了對 Potato Web Crawler 核心模組的重要改進。

## 改進總覽

### 🔴 關鍵修復（會導致功能失敗）

1. ✅ **相對連結處理**
2. ✅ **HTTP 錯誤處理與重試機制**
3. ✅ **XPath 屬性提取支援**
4. ✅ **URL 去重機制**

### 🟡 品質提升（增強穩定性）

5. ✅ **分頁狀態檢測**
6. ✅ **變數命名優化**
7. ✅ **請求延遲隨機化**

---

## 詳細改進說明

### 1. 相對連結處理

**問題**：分頁中的 `next_url` 可能是相對路徑（如 `/page/2`），直接請求會失敗。

**解決方案**：
- 在 `HttpClient` 中實作 `resolve_url()` 方法
- 使用 `urllib.parse.urljoin()` 自動處理相對 URL
- 追蹤當前 `base_url`，自動解析所有相對路徑

**範例**：
```python
# 自動處理相對 URL
http_client.get("/page/2")  # 會自動解析為 https://example.com/page/2
```

**程式碼位置**：`src/utils/http_client.py:74-100`

---

### 2. HTTP 錯誤處理與重試機制

**問題**：
- 網路不穩定時單次請求容易失敗
- 缺乏超時設定
- 錯誤訊息不夠詳細

**解決方案**：
- ✅ 實作自動重試機制（預設 3 次）
- ✅ 指數退避策略（0.5s, 1s, 2s...）
- ✅ 設定請求超時（預設 30 秒）
- ✅ 區分不同錯誤類型：
  - `Timeout` - 超時錯誤
  - `ConnectionError` - 連線錯誤
  - `HTTPError 4xx` - 客戶端錯誤（不重試）
  - `HTTPError 5xx` - 伺服器錯誤（會重試）
- ✅ 詳細的日誌記錄

**配置範例**：
```yaml
timeout: 30       # 請求超時 30 秒
max_retries: 3    # 最多重試 3 次
delay: 1.0        # 請求間隔 1 秒
```

**程式碼位置**：`src/utils/http_client.py:102-192`

---

### 3. XPath 屬性提取支援

**問題**：XPath 提取器缺少 `attr` 參數支援，無法像 CSS Selector 一樣方便地提取屬性。

**解決方案**：
- 在 `extract_by_xpath()` 加入 `attr` 參數
- 自動在 XPath 後加上 `/@attr`
- 與 CSS Selector 保持一致的介面

**使用範例**：
```yaml
# 方法 1: 使用 attr 參數（推薦）
- field: "links"
  type: "xpath"
  selector: "//a[@class='link']"
  attr: "href"
  multiple: true

# 方法 2: 直接在 XPath 中指定
- field: "links"
  type: "xpath"
  selector: "//a[@class='link']/@href"
  multiple: true
```

**程式碼位置**：`src/extractors/extractor.py:50-70`

---

### 4. URL 去重機制

**問題**：
- 分頁可能形成循環，導致無限爬取
- 同一頁面可能被重複訪問

**解決方案**：
- 實作 `visited_urls` 集合追蹤已訪問的 URL
- 在訪問新頁面前檢查是否已訪問
- 使用標準化 URL（resolve_url）避免同一頁面的不同表示

**效果**：
```
INFO - 正在爬取第 2 頁: https://example.com/page/2
INFO - 正在爬取第 3 頁: https://example.com/page/3
WARNING - 偵測到重複 URL，停止分頁: https://example.com/page/3
```

**程式碼位置**：`src/core/crawler.py:50, 71, 194-200, 209`

---

### 5. 分頁狀態檢測

**問題**：
- 有些網站的「下一頁」按鈕在最後一頁仍存在但被禁用
- 直接提取會導致 404 錯誤

**解決方案**：
實作 `_is_valid_next_page()` 方法，檢查：

1. **disabled 屬性** - `<a disabled>`
2. **disabled class** - `class="disabled inactive unavailable"`
3. **aria-disabled** - `aria-disabled="true"`
4. **無效 href** - `href="#"` 或 `href="javascript:void(0)"`

**範例**：
```html
<!-- 會被正確識別為無效連結 -->
<a href="#" class="next disabled">下一頁</a>
<a href="javascript:void(0)" class="next">下一頁</a>
<a href="/page/2" aria-disabled="true">下一頁</a>
```

**程式碼位置**：`src/core/crawler.py:98-153`

---

### 6. 請求延遲隨機化（Jitter）

**問題**：固定延遲容易被識別為機器人行為。

**解決方案**：
- 加入 ±20% 的隨機抖動
- 例如：delay=1.0 → 實際延遲在 0.8-1.2 秒之間

**效果**：
```
DEBUG - 請求延遲: 0.87s
DEBUG - 請求延遲: 1.13s
DEBUG - 請求延遲: 0.94s
```

**程式碼位置**：`src/utils/http_client.py:60-72`

---

### 7. 變數命名優化

**改進**：
- `initial_extractor` → `page_extractor`
- 更準確反映變數在迴圈中的角色

**程式碼位置**：`src/core/crawler.py:155, 212`

---

## 配置文件變更

### 新增可選參數

```yaml
# HTTP 請求設定（選填）
delay: 1.0           # 請求間隔延遲（預設 1.0）
timeout: 30          # 請求超時時間（預設 30）
max_retries: 3       # 最大重試次數（預設 3）
```

### XPath 屬性提取

```yaml
extract_rules:
  # 現在 XPath 也支援 attr 參數
  - field: "links"
    type: "xpath"
    selector: "//a[@class='link']"
    attr: "href"      # 自動加入 /@href
    multiple: true
```

---

## 日誌改進

### DEBUG 層級輸出範例

```bash
python main.py configs/example.yaml --log-level DEBUG

# 輸出：
DEBUG - HTTP 客戶端初始化: delay=1.0s, timeout=30s, max_retries=3
DEBUG - 正在請求網頁...
DEBUG - 請求延遲: 0.94s
DEBUG - 請求 URL: https://example.com (嘗試 1/3)
DEBUG - 請求成功: https://example.com [狀態碼: 200, 大小: 12543 bytes]
DEBUG - 資料提取器初始化完成
DEBUG - 開始提取資料...
DEBUG - 欄位 'title' 提取成功
DEBUG - 欄位 'links' 提取成功: 15 個項目
DEBUG - 分頁設定: 最多 5 頁
DEBUG - URL 解析: /page/2 -> https://example.com/page/2
DEBUG - 下一頁連結已禁用 (class: ['next', 'disabled'])
INFO - 已到達最後一頁（第 3 頁）
```

---

## 錯誤處理改進

### 網路錯誤

```bash
WARNING - 連線錯誤 (1/3): https://example.com - Connection refused
DEBUG - 等待 0.50s 後重試...
WARNING - 連線錯誤 (2/3): https://example.com - Connection refused
DEBUG - 等待 1.00s 後重試...
WARNING - 連線錯誤 (3/3): https://example.com - Connection refused
ERROR - 請求失敗，已達最大重試次數 (3): https://example.com
```

### HTTP 錯誤

```bash
# 4xx 錯誤不重試
ERROR - HTTP 錯誤 404: https://example.com/page/99

# 5xx 錯誤會重試
WARNING - HTTP 錯誤 503 (1/3): https://example.com
DEBUG - 等待 0.50s 後重試...
```

---

## 效能影響

### 記憶體

- URL 去重集合：每個 URL 約 100 bytes
- 10000 個 URL ≈ 1 MB（可忽略）

### 速度

- 隨機延遲：±20% 對總時間影響很小
- 重試機制：僅在失敗時觸發
- URL 去重：O(1) 查找，幾乎無影響

---

## 向後相容性

✅ **完全向後相容**

- 所有新參數都有預設值
- 現有配置文件無需修改即可使用
- 新功能為可選啟用

---

## 未來可擴展功能

以下是建議但尚未實作的功能（進階需求）：

1. **Robots.txt 支援** - 自動遵守網站爬蟲規則
2. **多起點 URL** - `start_urls: [...]` 支援多個起始頁面
3. **代理池** - 輪換代理 IP
4. **User-Agent 旋轉** - 輪換瀏覽器標識
5. **並發爬取** - 多線程/協程支援
6. **Session 保持** - Cookie 和登入狀態管理
7. **動態網頁支援** - Selenium/Playwright 整合

---

## 測試建議

### 測試相對 URL 處理

```yaml
pagination:
  next_page_selector: "a.next"  # href="/page/2"
```

### 測試重試機制

```bash
# 使用 DEBUG 層級查看重試過程
python main.py configs/example.yaml --log-level DEBUG
```

### 測試 URL 去重

```yaml
# 設定較大的 max_pages，觀察是否正確停止
pagination:
  max_pages: 100
```

---

## 總結

這些改進顯著提升了爬蟲的：

1. **穩定性** - 自動重試、錯誤處理
2. **可靠性** - URL 去重、分頁檢測
3. **實用性** - 相對 URL、XPath 屬性
4. **禮貌性** - 隨機延遲、超時設定
5. **可維護性** - 詳細日誌、清晰命名

所有改進都保持了模組化架構，不影響現有功能，且完全向後相容。
