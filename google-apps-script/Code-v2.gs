/**
 * 台中房地產自動化資料庫 - Google Apps Script (v2)
 * 新增功能：
 * - 支援多張圖片（圖片1、圖片2、圖片3）
 * - 經紀人資訊（姓名、電話、LINE連結）
 * - 物件標籤（電梯大樓、出售中等）
 */

// ============================================================
// 全域設定
// ============================================================

const CONFIG = {
  // Google Maps API Key（請替換為您的 API Key）
  MAPS_API_KEY: 'YOUR_GOOGLE_MAPS_API_KEY',
  
  // 試算表欄位索引（從 1 開始）
  COLUMNS: {
    URL: 1,          // A 欄：網址
    NAME: 2,         // B 欄：案名
    DISTRICT: 3,     // C 欄：行政區
    ADDRESS: 4,      // D 欄：地址
    PRICE: 5,        // E 欄：價格（萬元）
    LAT: 6,          // F 欄：緯度
    LNG: 7,          // G 欄：經度
    FEATURES: 8,     // H 欄：房屋特色
    IMAGE1: 9,       // I 欄：圖片網址1
    IMAGE2: 10,      // J 欄：圖片網址2
    IMAGE3: 11,      // K 欄：圖片網址3
    TAGS: 12,        // L 欄：標籤（逗號分隔）
    AGENT_NAME: 13,  // M 欄：經紀人姓名
    AGENT_PHONE: 14, // N 欄：聯絡電話
    AGENT_LINE: 15,  // O 欄：LINE連結
    UPDATED: 16,     // P 欄：最後更新
    STATUS: 17       // Q 欄：狀態
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
    '圖片網址1',
    '圖片網址2',
    '圖片網址3',
    '標籤',
    '經紀人姓名',
    '聯絡電話',
    'LINE連結',
    '最後更新',
    '狀態'
  ],
  
  // 預設經紀人資訊
  DEFAULT_AGENT: {
    name: '林世塏',
    phone: '0938-615-351',
    line: 'https://line.me/ti/p/FDsMyAYDv_'
  }
};

// ============================================================
// 1. 初始化試算表
// ============================================================

/**
 * 初始化試算表格式
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
  sheet.setColumnWidth(CONFIG.COLUMNS.IMAGE1, 300);
  sheet.setColumnWidth(CONFIG.COLUMNS.IMAGE2, 300);
  sheet.setColumnWidth(CONFIG.COLUMNS.IMAGE3, 300);
  sheet.setColumnWidth(CONFIG.COLUMNS.TAGS, 150);
  sheet.setColumnWidth(CONFIG.COLUMNS.AGENT_NAME, 100);
  sheet.setColumnWidth(CONFIG.COLUMNS.AGENT_PHONE, 120);
  sheet.setColumnWidth(CONFIG.COLUMNS.AGENT_LINE, 250);
  sheet.setColumnWidth(CONFIG.COLUMNS.UPDATED, 150);
  sheet.setColumnWidth(CONFIG.COLUMNS.STATUS, 80);
  
  // 凍結標題列
  sheet.setFrozenRows(1);
  
  // 設定資料驗證（狀態欄位）
  const statusRule = SpreadsheetApp.newDataValidation()
    .requireValueInList(['上架', '下架', '已售出'], true)
    .build();
  sheet.getRange(2, CONFIG.COLUMNS.STATUS, 1000).setDataValidation(statusRule);
  
  SpreadsheetApp.getUi().alert('✅ 試算表初始化完成！\n\n新增欄位：\n- 圖片網址2、圖片網址3\n- 標籤\n- 經紀人姓名、聯絡電話、LINE連結');
}

// ============================================================
// 2. 自動觸發器
// ============================================================

function onEdit(e) {
  const sheet = e.source.getActiveSheet();
  const range = e.range;
  
  // 只處理網址欄位（A 欄）的變更
  if (range.getColumn() !== CONFIG.COLUMNS.URL) return;
  if (range.getRow() === 1) return;
  
  const url = range.getValue();
  if (!url || typeof url !== 'string' || !url.startsWith('http')) return;
  
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
      SpreadsheetApp.getUi().alert('⚠️ 不支援的網址類型');
    }
  } catch (error) {
    Logger.log('爬取失敗: ' + error);
    sheet.getRange(row, CONFIG.COLUMNS.NAME).setValue('❌ 爬取失敗');
  }
}

// ============================================================
// 3. 網站爬蟲函數（增強版）
// ============================================================

function scrape591(sheet, row, url) {
  try {
    const response = UrlFetchApp.fetch(url, {muteHttpExceptions: true});
    const html = response.getContentText();
    
    // 解析基本資訊
    const nameMatch = html.match(/<h1[^>]*class="[^"]*house-title[^"]*"[^>]*>([^<]+)</i);
    const addressMatch = html.match(/<span[^>]*class="[^"]*addr[^"]*"[^>]*>([^<]+)</i);
    const priceMatch = html.match(/<span[^>]*class="[^"]*price[^"]*"[^>]*>([0-9,]+)</i);
    
    // 解析多張圖片
    const imageMatches = html.match(/<img[^>]*class="[^"]*swiper-slide-img[^"]*"[^>]*src="([^"]+)"/gi) || [];
    const images = imageMatches.slice(0, 3).map(img => {
      const match = img.match(/src="([^"]+)"/);
      return match ? match[1] : '';
    });
    
    // 解析標籤
    const tagMatches = html.match(/<span[^>]*class="[^"]*tag[^"]*"[^>]*>([^<]+)</gi) || [];
    const tags = tagMatches.slice(0, 3).map(tag => {
      const match = tag.match(/>([^<]+)</);
      return match ? match[1].trim() : '';
    }).filter(t => t).join(', ');
    
    const name = nameMatch ? nameMatch[1].trim() : '';
    const address = addressMatch ? addressMatch[1].trim() : '';
    const price = priceMatch ? parseInt(priceMatch[1].replace(/,/g, '')) : '';
    const district = extractDistrict(address);
    
    // 填入資料
    sheet.getRange(row, CONFIG.COLUMNS.NAME).setValue(name);
    sheet.getRange(row, CONFIG.COLUMNS.DISTRICT).setValue(district);
    sheet.getRange(row, CONFIG.COLUMNS.ADDRESS).setValue(address);
    sheet.getRange(row, CONFIG.COLUMNS.PRICE).setValue(price);
    sheet.getRange(row, CONFIG.COLUMNS.IMAGE1).setValue(images[0] || '');
    sheet.getRange(row, CONFIG.COLUMNS.IMAGE2).setValue(images[1] || '');
    sheet.getRange(row, CONFIG.COLUMNS.IMAGE3).setValue(images[2] || '');
    sheet.getRange(row, CONFIG.COLUMNS.TAGS).setValue(tags || '出售中');
    sheet.getRange(row, CONFIG.COLUMNS.STATUS).setValue('上架');
    
    // 填入預設經紀人資訊
    fillDefaultAgent(sheet, row);
    
    // 地理編碼
    if (address) {
      geocodeAddress(sheet, row, address);
    }
    
    updateTimestamp(sheet, row);
    
    SpreadsheetApp.getUi().alert('✅ 591 資料爬取成功！');
    
  } catch (error) {
    throw new Error('591 爬取失敗: ' + error);
  }
}

function scrapeRakuya(sheet, row, url) {
  try {
    const response = UrlFetchApp.fetch(url, {muteHttpExceptions: true});
    const html = response.getContentText();
    
    const nameMatch = html.match(/<h1[^>]*>([^<]+)</i);
    const addressMatch = html.match(/地址[：:]\s*([^<\n]+)/i);
    const priceMatch = html.match(/總價[：:]\s*([0-9,]+)/i);
    
    const imageMatches = html.match(/<img[^>]*src="([^"]*\/house\/[^"]+)"/gi) || [];
    const images = imageMatches.slice(0, 3).map(img => {
      const match = img.match(/src="([^"]+)"/);
      return match ? match[1] : '';
    });
    
    const name = nameMatch ? nameMatch[1].trim() : '';
    const address = addressMatch ? addressMatch[1].trim() : '';
    const price = priceMatch ? parseInt(priceMatch[1].replace(/,/g, '')) : '';
    const district = extractDistrict(address);
    
    sheet.getRange(row, CONFIG.COLUMNS.NAME).setValue(name);
    sheet.getRange(row, CONFIG.COLUMNS.DISTRICT).setValue(district);
    sheet.getRange(row, CONFIG.COLUMNS.ADDRESS).setValue(address);
    sheet.getRange(row, CONFIG.COLUMNS.PRICE).setValue(price);
    sheet.getRange(row, CONFIG.COLUMNS.IMAGE1).setValue(images[0] || '');
    sheet.getRange(row, CONFIG.COLUMNS.IMAGE2).setValue(images[1] || '');
    sheet.getRange(row, CONFIG.COLUMNS.IMAGE3).setValue(images[2] || '');
    sheet.getRange(row, CONFIG.COLUMNS.TAGS).setValue('出售中');
    sheet.getRange(row, CONFIG.COLUMNS.STATUS).setValue('上架');
    
    fillDefaultAgent(sheet, row);
    
    if (address) {
      geocodeAddress(sheet, row, address);
    }
    
    updateTimestamp(sheet, row);
    
    SpreadsheetApp.getUi().alert('✅ 樂屋網資料爬取成功！');
    
  } catch (error) {
    throw new Error('樂屋網爬取失敗: ' + error);
  }
}

function scrapeEtwarm(sheet, row, url) {
  try {
    const response = UrlFetchApp.fetch(url, {muteHttpExceptions: true});
    const html = response.getContentText();
    
    const nameMatch = html.match(/<h2[^>]*class="[^"]*title[^"]*"[^>]*>([^<]+)</i);
    const addressMatch = html.match(/地址[：:]\s*([^<\n]+)/i);
    const priceMatch = html.match(/售價[：:]\s*([0-9,]+)/i);
    
    const imageMatches = html.match(/<img[^>]*src="([^"]+)"/gi) || [];
    const images = imageMatches.slice(0, 3).map(img => {
      const match = img.match(/src="([^"]+)"/);
      return match ? match[1] : '';
    });
    
    const name = nameMatch ? nameMatch[1].trim() : '';
    const address = addressMatch ? addressMatch[1].trim() : '';
    const price = priceMatch ? parseInt(priceMatch[1].replace(/,/g, '')) : '';
    const district = extractDistrict(address);
    
    sheet.getRange(row, CONFIG.COLUMNS.NAME).setValue(name);
    sheet.getRange(row, CONFIG.COLUMNS.DISTRICT).setValue(district);
    sheet.getRange(row, CONFIG.COLUMNS.ADDRESS).setValue(address);
    sheet.getRange(row, CONFIG.COLUMNS.PRICE).setValue(price);
    sheet.getRange(row, CONFIG.COLUMNS.IMAGE1).setValue(images[0] || '');
    sheet.getRange(row, CONFIG.COLUMNS.IMAGE2).setValue(images[1] || '');
    sheet.getRange(row, CONFIG.COLUMNS.IMAGE3).setValue(images[2] || '');
    sheet.getRange(row, CONFIG.COLUMNS.TAGS).setValue('出售中');
    sheet.getRange(row, CONFIG.COLUMNS.STATUS).setValue('上架');
    
    fillDefaultAgent(sheet, row);
    
    if (address) {
      geocodeAddress(sheet, row, address);
    }
    
    updateTimestamp(sheet, row);
    
    SpreadsheetApp.getUi().alert('✅ 永義房屋資料爬取成功！');
    
  } catch (error) {
    throw new Error('永義房屋爬取失敗: ' + error);
  }
}

function scrapeHousefun(sheet, row, url) {
  try {
    const response = UrlFetchApp.fetch(url, {muteHttpExceptions: true});
    const html = response.getContentText();
    
    const nameMatch = html.match(/<h1[^>]*>([^<]+)</i);
    const addressMatch = html.match(/地址[：:]\s*([^<\n]+)/i);
    const priceMatch = html.match(/總價[：:]\s*([0-9,]+)/i);
    
    const imageMatches = html.match(/<img[^>]*class="[^"]*swiper-slide-img[^"]*"[^>]*src="([^"]+)"/gi) || [];
    const images = imageMatches.slice(0, 3).map(img => {
      const match = img.match(/src="([^"]+)"/);
      return match ? match[1] : '';
    });
    
    const name = nameMatch ? nameMatch[1].trim() : '';
    const address = addressMatch ? addressMatch[1].trim() : '';
    const price = priceMatch ? parseInt(priceMatch[1].replace(/,/g, '')) : '';
    const district = extractDistrict(address);
    
    sheet.getRange(row, CONFIG.COLUMNS.NAME).setValue(name);
    sheet.getRange(row, CONFIG.COLUMNS.DISTRICT).setValue(district);
    sheet.getRange(row, CONFIG.COLUMNS.ADDRESS).setValue(address);
    sheet.getRange(row, CONFIG.COLUMNS.PRICE).setValue(price);
    sheet.getRange(row, CONFIG.COLUMNS.IMAGE1).setValue(images[0] || '');
    sheet.getRange(row, CONFIG.COLUMNS.IMAGE2).setValue(images[1] || '');
    sheet.getRange(row, CONFIG.COLUMNS.IMAGE3).setValue(images[2] || '');
    sheet.getRange(row, CONFIG.COLUMNS.TAGS).setValue('出售中');
    sheet.getRange(row, CONFIG.COLUMNS.STATUS).setValue('上架');
    
    fillDefaultAgent(sheet, row);
    
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
// 4. 地理編碼
// ============================================================

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
    }
    
  } catch (error) {
    Logger.log('地理編碼錯誤: ' + error);
  }
}

// ============================================================
// 5. 輔助函數
// ============================================================

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

function fillDefaultAgent(sheet, row) {
  sheet.getRange(row, CONFIG.COLUMNS.AGENT_NAME).setValue(CONFIG.DEFAULT_AGENT.name);
  sheet.getRange(row, CONFIG.COLUMNS.AGENT_PHONE).setValue(CONFIG.DEFAULT_AGENT.phone);
  sheet.getRange(row, CONFIG.COLUMNS.AGENT_LINE).setValue(CONFIG.DEFAULT_AGENT.line);
}

function updateTimestamp(sheet, row) {
  const now = new Date();
  const timestamp = Utilities.formatDate(now, 'Asia/Taipei', 'yyyy-MM-dd HH:mm:ss');
  sheet.getRange(row, CONFIG.COLUMNS.UPDATED).setValue(timestamp);
}

// ============================================================
// 6. 選單功能
// ============================================================

function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('🏠 房地產工具')
    .addItem('📋 初始化試算表', 'initializeSheet')
    .addItem('🔄 手動更新所有經緯度', 'batchGeocodeAll')
    .addItem('👤 批次填入預設經紀人資訊', 'batchFillAgent')
    .addItem('📊 資料統計', 'showStatistics')
    .addToUi();
}

function batchGeocodeAll() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  const lastRow = sheet.getLastRow();
  
  let count = 0;
  
  for (let row = 2; row <= lastRow; row++) {
    const address = sheet.getRange(row, CONFIG.COLUMNS.ADDRESS).getValue();
    const lat = sheet.getRange(row, CONFIG.COLUMNS.LAT).getValue();
    
    if (address && !lat) {
      geocodeAddress(sheet, row, address);
      count++;
      Utilities.sleep(200);
    }
  }
  
  SpreadsheetApp.getUi().alert(`✅ 已更新 ${count} 筆資料的經緯度`);
}

function batchFillAgent() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  const lastRow = sheet.getLastRow();
  
  let count = 0;
  
  for (let row = 2; row <= lastRow; row++) {
    const agentName = sheet.getRange(row, CONFIG.COLUMNS.AGENT_NAME).getValue();
    
    if (!agentName) {
      fillDefaultAgent(sheet, row);
      count++;
    }
  }
  
  SpreadsheetApp.getUi().alert(`✅ 已填入 ${count} 筆預設經紀人資訊`);
}

function showStatistics() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  const lastRow = sheet.getLastRow();
  
  let total = lastRow - 1;
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
