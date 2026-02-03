/**
 * 台中房地產自動化資料庫 - Google Apps Script
 * 功能：
 * 1. 自動初始化試算表格式
 * 2. 從 591、樂屋網、永義房屋、好房網爬取資料
 * 3. 自動地理編碼（地址 → 經緯度）
 * 4. 自動更新時間戳記
 */

// ============================================================
// 全域設定
// ============================================================

const CONFIG = {
  // Google Maps API Key（請替換為您的 API Key）
  MAPS_API_KEY: 'YOUR_GOOGLE_MAPS_API_KEY',
  
  // 試算表欄位索引（從 1 開始）
  COLUMNS: {
    URL: 1,        // A 欄：網址
    NAME: 2,       // B 欄：案名
    DISTRICT: 3,   // C 欄：行政區
    ADDRESS: 4,    // D 欄：地址
    PRICE: 5,      // E 欄：價格（萬元）
    LAT: 6,        // F 欄：緯度
    LNG: 7,        // G 欄：經度
    FEATURES: 8,   // H 欄：房屋特色
    IMAGE: 9,      // I 欄：圖片網址
    UPDATED: 10,   // J 欄：最後更新
    STATUS: 11     // K 欄：狀態
  },
  
  // 欄位標題
  HEADERS: [
    '網址',
    '案名',
    '行政區',
    '地址',
    '價格（萬）',
    '緯度',
    '經度',
    '房屋特色',
    '圖片網址',
    '最後更新',
    '狀態'
  ]
};

// ============================================================
// 1. 初始化試算表
// ============================================================

/**
 * 初始化試算表格式
 * 使用方式：在 Google Sheets 中執行此函數
 */
function initializeSheet() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  
  // 設定標題列
  const headerRange = sheet.getRange(1, 1, 1, CONFIG.HEADERS.length);
  headerRange.setValues([CONFIG.HEADERS]);
  
  // 格式化標題列
  headerRange
    .setBackground('#1E3A8A')
    .setFontColor('#FFFFFF')
    .setFontWeight('bold')
    .setFontSize(11)
    .setHorizontalAlignment('center')
    .setVerticalAlignment('middle');
  
  // 設定欄位寬度
  sheet.setColumnWidth(CONFIG.COLUMNS.URL, 300);
  sheet.setColumnWidth(CONFIG.COLUMNS.NAME, 200);
  sheet.setColumnWidth(CONFIG.COLUMNS.DISTRICT, 80);
  sheet.setColumnWidth(CONFIG.COLUMNS.ADDRESS, 250);
  sheet.setColumnWidth(CONFIG.COLUMNS.PRICE, 100);
  sheet.setColumnWidth(CONFIG.COLUMNS.LAT, 100);
  sheet.setColumnWidth(CONFIG.COLUMNS.LNG, 100);
  sheet.setColumnWidth(CONFIG.COLUMNS.FEATURES, 200);
  sheet.setColumnWidth(CONFIG.COLUMNS.IMAGE, 300);
  sheet.setColumnWidth(CONFIG.COLUMNS.UPDATED, 150);
  sheet.setColumnWidth(CONFIG.COLUMNS.STATUS, 80);
  
  // 凍結標題列
  sheet.setFrozenRows(1);
  
  // 設定資料驗證（狀態欄位）
  const statusRule = SpreadsheetApp.newDataValidation()
    .requireValueInList(['上架', '下架', '已售出'], true)
    .build();
  sheet.getRange(2, CONFIG.COLUMNS.STATUS, 1000).setDataValidation(statusRule);
  
  SpreadsheetApp.getUi().alert('✅ 試算表初始化完成！');
}

// ============================================================
// 2. 自動觸發器 - 監聽網址欄位變更
// ============================================================

/**
 * 當試算表編輯時自動觸發
 */
function onEdit(e) {
  const sheet = e.source.getActiveSheet();
  const range = e.range;
  
  // 只處理網址欄位（A 欄）的變更
  if (range.getColumn() !== CONFIG.COLUMNS.URL) return;
  
  // 跳過標題列
  if (range.getRow() === 1) return;
  
  const url = range.getValue();
  
  // 檢查是否為有效網址
  if (!url || typeof url !== 'string' || !url.startsWith('http')) return;
  
  // 判斷網址類型並爬取資料
  const row = range.getRow();
  
  try {
    if (url.includes('591.com.tw')) {
      scrape591(sheet, row, url);
    } else if (url.includes('rakuya.com.tw')) {
      scrapeRakuya(sheet, row, url);
    } else if (url.includes('etwarm.com.tw')) {
      scrapeEtwarm(sheet, row, url);
    } else if (url.includes('housefun.com.tw')) {
      scrapeHousefun(sheet, row, url);
    } else {
      SpreadsheetApp.getUi().alert('⚠️ 不支援的網址類型\n\n目前支援：591、樂屋網、永義房屋、好房網');
    }
  } catch (error) {
    Logger.log('爬取失敗: ' + error);
    sheet.getRange(row, CONFIG.COLUMNS.NAME).setValue('❌ 爬取失敗');
  }
}

// ============================================================
// 3. 網站爬蟲函數
// ============================================================

/**
 * 爬取 591 網站資料
 */
function scrape591(sheet, row, url) {
  try {
    const response = UrlFetchApp.fetch(url, {muteHttpExceptions: true});
    const html = response.getContentText();
    
    // 解析 HTML（使用正則表達式）
    const nameMatch = html.match(/<h1[^>]*class="[^"]*house-title[^"]*"[^>]*>([^<]+)</i);
    const addressMatch = html.match(/<span[^>]*class="[^"]*addr[^"]*"[^>]*>([^<]+)</i);
    const priceMatch = html.match(/<span[^>]*class="[^"]*price[^"]*"[^>]*>([0-9,]+)</i);
    const imageMatch = html.match(/<img[^>]*class="[^"]*main-img[^"]*"[^>]*src="([^"]+)"/i);
    
    const name = nameMatch ? nameMatch[1].trim() : '';
    const address = addressMatch ? addressMatch[1].trim() : '';
    const price = priceMatch ? parseInt(priceMatch[1].replace(/,/g, '')) : '';
    const image = imageMatch ? imageMatch[1] : '';
    
    // 提取行政區
    const district = extractDistrict(address);
    
    // 填入資料
    sheet.getRange(row, CONFIG.COLUMNS.NAME).setValue(name);
    sheet.getRange(row, CONFIG.COLUMNS.DISTRICT).setValue(district);
    sheet.getRange(row, CONFIG.COLUMNS.ADDRESS).setValue(address);
    sheet.getRange(row, CONFIG.COLUMNS.PRICE).setValue(price);
    sheet.getRange(row, CONFIG.COLUMNS.IMAGE).setValue(image);
    sheet.getRange(row, CONFIG.COLUMNS.STATUS).setValue('上架');
    
    // 地理編碼
    if (address) {
      geocodeAddress(sheet, row, address);
    }
    
    // 更新時間戳記
    updateTimestamp(sheet, row);
    
    SpreadsheetApp.getUi().alert('✅ 591 資料爬取成功！');
    
  } catch (error) {
    throw new Error('591 爬取失敗: ' + error);
  }
}

/**
 * 爬取樂屋網資料
 */
function scrapeRakuya(sheet, row, url) {
  try {
    const response = UrlFetchApp.fetch(url, {muteHttpExceptions: true});
    const html = response.getContentText();
    
    const nameMatch = html.match(/<h1[^>]*>([^<]+)</i);
    const addressMatch = html.match(/地址[：:]\s*([^<\n]+)/i);
    const priceMatch = html.match(/總價[：:]\s*([0-9,]+)/i);
    const imageMatch = html.match(/<img[^>]*src="([^"]*\/house\/[^"]+)"/i);
    
    const name = nameMatch ? nameMatch[1].trim() : '';
    const address = addressMatch ? addressMatch[1].trim() : '';
    const price = priceMatch ? parseInt(priceMatch[1].replace(/,/g, '')) : '';
    const image = imageMatch ? imageMatch[1] : '';
    
    const district = extractDistrict(address);
    
    sheet.getRange(row, CONFIG.COLUMNS.NAME).setValue(name);
    sheet.getRange(row, CONFIG.COLUMNS.DISTRICT).setValue(district);
    sheet.getRange(row, CONFIG.COLUMNS.ADDRESS).setValue(address);
    sheet.getRange(row, CONFIG.COLUMNS.PRICE).setValue(price);
    sheet.getRange(row, CONFIG.COLUMNS.IMAGE).setValue(image);
    sheet.getRange(row, CONFIG.COLUMNS.STATUS).setValue('上架');
    
    if (address) {
      geocodeAddress(sheet, row, address);
    }
    
    updateTimestamp(sheet, row);
    
    SpreadsheetApp.getUi().alert('✅ 樂屋網資料爬取成功！');
    
  } catch (error) {
    throw new Error('樂屋網爬取失敗: ' + error);
  }
}

/**
 * 爬取永義房屋資料
 */
function scrapeEtwarm(sheet, row, url) {
  try {
    const response = UrlFetchApp.fetch(url, {muteHttpExceptions: true});
    const html = response.getContentText();
    
    const nameMatch = html.match(/<h2[^>]*class="[^"]*title[^"]*"[^>]*>([^<]+)</i);
    const addressMatch = html.match(/地址[：:]\s*([^<\n]+)/i);
    const priceMatch = html.match(/售價[：:]\s*([0-9,]+)/i);
    const imageMatch = html.match(/<img[^>]*class="[^"]*main[^"]*"[^>]*src="([^"]+)"/i);
    
    const name = nameMatch ? nameMatch[1].trim() : '';
    const address = addressMatch ? addressMatch[1].trim() : '';
    const price = priceMatch ? parseInt(priceMatch[1].replace(/,/g, '')) : '';
    const image = imageMatch ? imageMatch[1] : '';
    
    const district = extractDistrict(address);
    
    sheet.getRange(row, CONFIG.COLUMNS.NAME).setValue(name);
    sheet.getRange(row, CONFIG.COLUMNS.DISTRICT).setValue(district);
    sheet.getRange(row, CONFIG.COLUMNS.ADDRESS).setValue(address);
    sheet.getRange(row, CONFIG.COLUMNS.PRICE).setValue(price);
    sheet.getRange(row, CONFIG.COLUMNS.IMAGE).setValue(image);
    sheet.getRange(row, CONFIG.COLUMNS.STATUS).setValue('上架');
    
    if (address) {
      geocodeAddress(sheet, row, address);
    }
    
    updateTimestamp(sheet, row);
    
    SpreadsheetApp.getUi().alert('✅ 永義房屋資料爬取成功！');
    
  } catch (error) {
    throw new Error('永義房屋爬取失敗: ' + error);
  }
}

/**
 * 爬取好房網資料
 */
function scrapeHousefun(sheet, row, url) {
  try {
    const response = UrlFetchApp.fetch(url, {muteHttpExceptions: true});
    const html = response.getContentText();
    
    const nameMatch = html.match(/<h1[^>]*>([^<]+)</i);
    const addressMatch = html.match(/地址[：:]\s*([^<\n]+)/i);
    const priceMatch = html.match(/總價[：:]\s*([0-9,]+)/i);
    const imageMatch = html.match(/<img[^>]*class="[^"]*swiper-slide-img[^"]*"[^>]*src="([^"]+)"/i);
    
    const name = nameMatch ? nameMatch[1].trim() : '';
    const address = addressMatch ? addressMatch[1].trim() : '';
    const price = priceMatch ? parseInt(priceMatch[1].replace(/,/g, '')) : '';
    const image = imageMatch ? imageMatch[1] : '';
    
    const district = extractDistrict(address);
    
    sheet.getRange(row, CONFIG.COLUMNS.NAME).setValue(name);
    sheet.getRange(row, CONFIG.COLUMNS.DISTRICT).setValue(district);
    sheet.getRange(row, CONFIG.COLUMNS.ADDRESS).setValue(address);
    sheet.getRange(row, CONFIG.COLUMNS.PRICE).setValue(price);
    sheet.getRange(row, CONFIG.COLUMNS.IMAGE).setValue(image);
    sheet.getRange(row, CONFIG.COLUMNS.STATUS).setValue('上架');
    
    if (address) {
      geocodeAddress(sheet, row, address);
    }
    
    updateTimestamp(sheet, row);
    
    SpreadsheetApp.getUi().alert('✅ 好房網資料爬取成功！');
    
  } catch (error) {
    throw new Error('好房網爬取失敗: ' + error);
  }
}

// ============================================================
// 4. 地理編碼（地址 → 經緯度）
// ============================================================

/**
 * 使用 Google Maps Geocoding API 將地址轉換為經緯度
 */
function geocodeAddress(sheet, row, address) {
  try {
    const apiKey = CONFIG.MAPS_API_KEY;
    
    if (apiKey === 'YOUR_GOOGLE_MAPS_API_KEY') {
      Logger.log('請設定 Google Maps API Key');
      return;
    }
    
    const url = `https://maps.googleapis.com/maps/api/geocode/json?address=${encodeURIComponent(address)}&key=${apiKey}`;
    const response = UrlFetchApp.fetch(url);
    const data = JSON.parse(response.getContentText());
    
    if (data.status === 'OK' && data.results.length > 0) {
      const location = data.results[0].geometry.location;
      sheet.getRange(row, CONFIG.COLUMNS.LAT).setValue(location.lat);
      sheet.getRange(row, CONFIG.COLUMNS.LNG).setValue(location.lng);
    } else {
      Logger.log('地理編碼失敗: ' + data.status);
    }
    
  } catch (error) {
    Logger.log('地理編碼錯誤: ' + error);
  }
}

// ============================================================
// 5. 輔助函數
// ============================================================

/**
 * 從地址中提取行政區
 */
function extractDistrict(address) {
  if (!address) return '';
  
  const districts = [
    '中區', '東區', '南區', '西區', '北區', '西屯區', '南屯區', '北屯區',
    '豐原區', '大里區', '太平區', '清水區', '沙鹿區', '大甲區', '東勢區',
    '梧棲區', '烏日區', '神岡區', '大肚區', '大雅區', '后里區', '霧峰區',
    '潭子區', '龍井區', '外埔區', '和平區', '石岡區', '大安區', '新社區'
  ];
  
  for (const district of districts) {
    if (address.includes(district)) {
      return district;
    }
  }
  
  return '';
}

/**
 * 更新時間戳記
 */
function updateTimestamp(sheet, row) {
  const now = new Date();
  const timestamp = Utilities.formatDate(now, 'Asia/Taipei', 'yyyy-MM-dd HH:mm:ss');
  sheet.getRange(row, CONFIG.COLUMNS.UPDATED).setValue(timestamp);
}

// ============================================================
// 6. 選單功能
// ============================================================

/**
 * 建立自訂選單
 */
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('🏠 房地產工具')
    .addItem('📋 初始化試算表', 'initializeSheet')
    .addItem('🔄 手動更新所有經緯度', 'batchGeocodeAll')
    .addItem('📊 資料統計', 'showStatistics')
    .addToUi();
}

/**
 * 批次更新所有列的經緯度
 */
function batchGeocodeAll() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  const lastRow = sheet.getLastRow();
  
  let count = 0;
  
  for (let row = 2; row <= lastRow; row++) {
    const address = sheet.getRange(row, CONFIG.COLUMNS.ADDRESS).getValue();
    const lat = sheet.getRange(row, CONFIG.COLUMNS.LAT).getValue();
    
    // 只處理有地址但沒有經緯度的列
    if (address && !lat) {
      geocodeAddress(sheet, row, address);
      count++;
      Utilities.sleep(200); // 避免超過 API 限制
    }
  }
  
  SpreadsheetApp.getUi().alert(`✅ 已更新 ${count} 筆資料的經緯度`);
}

/**
 * 顯示資料統計
 */
function showStatistics() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  const lastRow = sheet.getLastRow();
  
  let total = lastRow - 1; // 扣除標題列
  let active = 0;
  let sold = 0;
  let inactive = 0;
  
  for (let row = 2; row <= lastRow; row++) {
    const status = sheet.getRange(row, CONFIG.COLUMNS.STATUS).getValue();
    if (status === '上架') active++;
    else if (status === '已售出') sold++;
    else if (status === '下架') inactive++;
  }
  
  const message = `
📊 資料統計報告

總物件數：${total}
✅ 上架中：${active}
❌ 下架：${inactive}
💰 已售出：${sold}
  `;
  
  SpreadsheetApp.getUi().alert(message);
}
