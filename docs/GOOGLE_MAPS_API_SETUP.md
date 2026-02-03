# Google Maps API Key 取得與設定教學

## 為什麼需要 Google Maps API Key？

Google Apps Script 中的地理編碼功能（將地址轉換為經緯度）需要使用 Google Maps Geocoding API。雖然 Google 提供免費額度（每月 $200 美元的免費使用量，約等於 40,000 次地理編碼請求），但仍需要建立 API Key 來使用這項服務。

---

## 步驟 1：前往 Google Cloud Console

1. 開啟瀏覽器，前往 [Google Cloud Console](https://console.cloud.google.com/)
2. 使用您的 Google 帳號登入（建議使用與 Google Sheets 相同的帳號）

---

## 步驟 2：建立新專案

1. 點擊頁面上方的專案選擇器（預設顯示「選取專案」）
2. 在彈出視窗中，點擊右上角的「**新增專案**」按鈕
3. 輸入專案名稱，例如：`台中房產網站`
4. 點擊「**建立**」按鈕
5. 等待專案建立完成（約需 10-30 秒）

---

## 步驟 3：啟用 Geocoding API

1. 在左側選單中，點擊「**API 和服務**」→「**程式庫**」
2. 在搜尋框中輸入 `Geocoding API`
3. 點擊搜尋結果中的「**Geocoding API**」
4. 點擊「**啟用**」按鈕
5. 等待 API 啟用完成

---

## 步驟 4：建立 API Key

1. 在左側選單中，點擊「**API 和服務**」→「**憑證**」
2. 點擊頁面上方的「**+ 建立憑證**」按鈕
3. 選擇「**API 金鑰**」
4. 系統會自動產生一組 API Key，並顯示在彈出視窗中
5. **重要**：請立即複製這組 API Key（格式類似：`AIzaSyD1234567890abcdefghijklmnopqrstuv`）

---

## 步驟 5：限制 API Key 使用範圍（建議）

為了安全起見，建議限制 API Key 的使用範圍：

1. 在 API Key 建立完成的彈出視窗中，點擊「**限制金鑰**」
2. 或在「憑證」頁面中，點擊剛建立的 API Key 名稱
3. 在「API 限制」區段中，選擇「**限制金鑰**」
4. 勾選「**Geocoding API**」
5. 點擊頁面下方的「**儲存**」按鈕

---

## 步驟 6：填入 Google Apps Script

現在您已經取得了 API Key，接下來要將它填入 Google Apps Script 腳本中。

### 6.1 開啟 Google Sheets

1. 開啟您的房地產資料試算表
2. 點擊選單列的「**擴充功能**」→「**Apps Script**」

### 6.2 找到 API Key 填入位置

在 Apps Script 編輯器中，找到以下這段程式碼（約在第 5-10 行）：

```javascript
// ==================== 設定區 ====================
var GOOGLE_MAPS_API_KEY = "YOUR_GOOGLE_MAPS_API_KEY"; // 請替換為您的 Google Maps API Key
```

### 6.3 替換 API Key

將 `YOUR_GOOGLE_MAPS_API_KEY` 替換為您在步驟 4 複製的 API Key。

**修改前**：
```javascript
var GOOGLE_MAPS_API_KEY = "YOUR_GOOGLE_MAPS_API_KEY";
```

**修改後**：
```javascript
var GOOGLE_MAPS_API_KEY = "AIzaSyD1234567890abcdefghijklmnopqrstuv";
```

### 6.4 儲存腳本

1. 點擊工具列的「**儲存專案**」圖示（磁碟圖示）
2. 或按下快捷鍵 `Ctrl + S`（Windows）或 `Cmd + S`（Mac）

---

## 步驟 7：測試 API Key

1. 在 Google Sheets 中，於第一欄（A 欄）貼上一個 591 物件網址
2. 等待幾秒鐘，腳本會自動執行
3. 如果「緯度」和「經度」欄位自動填入了數值，表示 API Key 設定成功！

---

## 常見問題

### Q1：API Key 會收費嗎？

Google 提供每月 $200 美元的免費額度，約等於 40,000 次地理編碼請求。對於一般房產網站來說，這個額度綽綽有餘。除非您每天新增數百筆物件，否則不會產生費用。

### Q2：如何查看 API 使用量？

1. 前往 [Google Cloud Console](https://console.cloud.google.com/)
2. 選擇您的專案
3. 點擊左側選單的「**API 和服務**」→「**資訊主頁**」
4. 即可查看各 API 的使用量統計

### Q3：API Key 洩漏怎麼辦？

如果您不小心將 API Key 公開（例如：上傳到 GitHub），請立即：

1. 前往 [Google Cloud Console](https://console.cloud.google.com/)
2. 點擊「**API 和服務**」→「**憑證**」
3. 找到洩漏的 API Key，點擊右側的「**刪除**」圖示
4. 重新建立一組新的 API Key

### Q4：可以不使用 API Key 嗎？

如果您不想使用 Google Maps API，可以採用以下替代方案：

**方案 1：手動輸入經緯度**
- 在 Google Sheets 中手動填入「緯度」和「經度」欄位
- 可以使用 [Google Maps](https://www.google.com/maps) 查詢地址的經緯度（在地圖上點擊位置，即可在下方看到座標）

**方案 2：使用台中區域預設座標**
- 目前網站已內建台中各區的預設座標
- 如果 API Key 未設定，系統會自動使用區域中心點座標
- 雖然不如精確地址準確，但仍可在地圖上顯示大致位置

---

## 完整設定檢查清單

- [ ] 已建立 Google Cloud 專案
- [ ] 已啟用 Geocoding API
- [ ] 已建立 API Key
- [ ] 已限制 API Key 使用範圍（建議）
- [ ] 已將 API Key 填入 Google Apps Script
- [ ] 已儲存 Apps Script
- [ ] 已測試地理編碼功能

---

如果您在設定過程中遇到任何問題，請隨時向我提問！
