# 網站部署與維護指南

## 1. 專案架構

本專案採用現代化的前端技術棧，實現了資料與畫面的完全分離。

- **資料庫**: Google Sheets
- **自動化**: Google Apps Script (GAS)
- **前端框架**: Tailwind CSS
- **地圖技術**: Leaflet.js + OpenStreetMap
- **SEO 優化**: Schema.org + Open Graph

### 檔案結構

```
/
├── index.html              # 首頁
├── property-detail.html    # 物件詳情頁面
├── css/
│   └── style.css           # 自訂 CSS
├── js/
│   ├── app.js              # 主應用程式
│   ├── data.js             # 資料處理
│   ├── map.js              # 地圖功能
│   └── property-detail.js  # 詳情頁面功能
├── google-apps-script/
│   └── Code-v2.gs          # Google Apps Script 腳本
└── docs/
    ├── GOOGLE_SHEETS_SETUP.md # Google Sheets 設定指南
    └── DEPLOYMENT_GUIDE.md    # 本部署指南
```

## 2. Google Sheets 設定

請參考 `docs/GOOGLE_SHEETS_SETUP.md` 文件，完成以下步驟：

1. **建立 Google Sheets**：複製一份新的試算表
2. **安裝 Google Apps Script**：將 `google-apps-script/Code-v2.gs` 的內容貼到指令碼編輯器
3. **執行初始化**：在指令碼編輯器中執行 `initializeSheet` 函數
4. **設定觸發器**：建立 `onEdit` 觸發器
5. **取得 Google Maps API Key**：並填入 GAS 腳本中
6. **發佈到網路**：將試算表發佈為 CSV 格式
7. **更新 CSV 連結**：將發佈後的 CSV 連結貼到 `js/data.js` 和 `js/property-detail.js` 中

## 3. 網站部署

本專案已設定好 GitHub Actions，可自動部署到 GitHub Pages。

### 部署流程

1. **修改程式碼**：在本地修改 HTML/CSS/JS 檔案
2. **提交到 GitHub**：使用 `git add`、`git commit`、`git push` 將變更推送到 `main` 分支
3. **自動部署**：GitHub Actions 會自動偵測到變更，並將網站部署到 GitHub Pages
4. **確認部署**：等待 1-2 分鐘，即可在 `https://<您的GitHub用戶名>.github.io/taichung-houses/` 看到更新後的網站

### 注意事項

- **請勿修改 `.github/workflows/main.yml`**：工作流程設定已最佳化，可確保新版靜態網頁正確部署
- **`build_sheets_old.py` 已停用**：舊版的 Python 腳本已重命名，不會再執行

## 4. 資料維護

### 新增物件

1. 在 Google Sheets 的第一欄（A 欄）貼上 591、樂屋網、永義房屋或好房網的物件網址
2. GAS 腳本會自動爬取資料、進行地理編碼，並填入相關欄位

### 修改物件

- 直接在 Google Sheets 中修改資料即可
- 網頁會在下次載入時自動顯示更新後的資料

### 下架物件

- 將物件的「狀態」欄位改為「下架」或「已售出」
- 該物件將不會顯示在網站上

## 5. SEO 與社群分享

本專案已針對 SEO 和社群分享進行了完整優化。

- **元數據**：`index.html` 和 `property-detail.html` 都包含了優化的 `<title>`、`meta description` 和 `keywords`
- **結構化資料**：`property-detail.html` 會自動生成 `RealEstateListing` 的 JSON-LD 標籤，有助於 Google 搜尋排名
- **Open Graph**：`property-detail.html` 會自動生成 `og:title`、`og:description` 和 `og:image`，確保在 Facebook、Threads 等平台分享時有美觀的預覽效果
- **語義化 HTML**：全站使用 `<header>`、`<main>`、`<section>`、`<footer>` 等語義化標籤，有助於搜尋引擎理解網頁內容

## 6. 未來擴充建議

- **進階篩選功能**：增加更多篩選條件，例如：坪數、屋齡、樓層等
- **使用者收藏功能**：讓使用者可以收藏感興趣的物件
- **後台管理介面**：建立一個簡單的後台介面，方便管理物件資料
- **整合更多房仲平台**：擴充 GAS 腳本，支援更多房仲平台的爬蟲
