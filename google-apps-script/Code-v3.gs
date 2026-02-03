/**
 * 台中房地產自動化資料庫 - Google Apps Script (v3)
 * 更新內容：
 * - 修正永義房屋網址支援（buy.yungyi-house.com.tw, x.ychouse.tw, ycut.com.tw）
 * - 優化樂屋網爬蟲
 * - 改善錯誤處理
 * - 支援更多網址格式
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
    STATUS: 17       // Q 欄：狀態（上架/下架/已售出）
  },
  
  // 預設經紀人資訊
  DEFAULT_AGENT: {
    NAME: '林世塏',
    PHONE: '0938-615-351',
    LINE: 'https://line.me/ti/p/FDsMyAYDv_'
  },
  
  // 台中市各區預設座標
  DISTRICT_COORDS: {
    '中區': {lat: 24.1438, lng: 120.6794},
    '東區': {lat: 24.1375, lng: 120.7038},
    '南區': {lat: 24.1163, lng: 120.6644},
    '西區': {lat: 24.1431, lng: 120.6728},
    '北區': {lat: 24.1620, lng: 120.6839},
    '西屯區': {lat: 24.1816, lng: 120.6179},
    '南屯區': {lat: 24.1380, lng: 120.6426},
    '北屯區': {lat: 24.1811, lng: 120.7155},
    '豐原區': {lat: 24.2566, lng: 120.7246},
    '大里區': {lat: 24.0990, lng: 120.6773},
    '太平區': {lat: 24.1244, lng: 120.7678},
    '清水區': {lat: 24.2646, lng: 120.5686},
    '沙鹿區': {lat: 24.2364, lng: 120.5686},
    '大甲區': {lat: 24.3475, lng: 120.6242},
    '東勢區': {lat: 24.2551, lng: 120.8240},
    '梧棲區': {lat: 24.2554, lng: 120.5282},
    '烏日區': {lat: 24.1052, lng: 120.6237},
    '神岡區': {lat: 24.2628, lng: 120.6653},
    '大肚區': {lat: 24.1532, lng: 120.5405},
    '大雅區': {lat: 24.2285, lng: 120.6497},
    '后里區': {lat: 24.3045, lng: 120.7118},
    '霧峰區': {lat: 24.0623, lng: 120.7003},
    '潭子區': {lat: 24.2098, lng: 120.7076},
    '龍井區': {lat: 24.1928, lng: 120.5431},
    '外埔區': {lat: 24.3317, lng: 120.6563},
    '和平區': {lat: 24.2930, lng: 121.0189},
    '石岡區': {lat: 24.2733, lng: 120.7837},
    '新社區': {lat: 24.2321, lng: 120.8096}
  }
};

// ============================================================
// 1. 初始化函數
// ============================================================

function initializeSheet() {
  const sheet = SpreadsheetApp.getActiveSheet();
  
  // 設定標題列
  const headers = [
    '網址', '案名', '行政區', '地址', '價格（萬元）',
    '緯度', '經度', '房屋特色',
    '圖片網址1', '圖片網址2', '圖片網址3',
    '標籤', '經紀人姓名', '聯絡電話', 'LINE連結',
    '最後更新', '狀態'
  ];
  
  sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
  
  // 設定標題列樣式
  const headerRange = sheet.getRange(1, 1, 1, headers.length);
  headerRange.setBackground('#003D5C');
  headerRange.setFontColor('#FFFFFF');
  headerRange.setFontWeight('bold');
  headerRange.setHorizontalAlignment('center');
  
  // 設定欄位寬度
  sheet.setColumnWidth(CONFIG.COLUMNS.URL, 400);
  sheet.setColumnWidth(CONFIG.COLUMNS.NAME, 250);
  sheet.setColumnWidth(CONFIG.COLUMNS.DISTRICT, 80);
  sheet.setColumnWidth(CONFIG.COLUMNS.ADDRESS, 250);
  sheet.setColumnWidth(CONFIG.COLUMNS.PRICE, 100);
  sheet.setColumnWidth(CONFIG.COLUMNS.LAT, 100);
  sheet.setColumnWidth(CONFIG.COLUMNS.LNG, 100);
  sheet.setColumnWidth(CONFIG.COLUMNS.FEATURES, 300);
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
  
  SpreadsheetApp.getUi().alert('✅ 試算表初始化完成！\n\n支援的房仲平台：\n- 591 房屋交易網\n- 樂屋網\n- 永義房屋\n- 好房網');
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
    } else if (url.includes('yungyi-house.com.tw') || url.includes('ychouse.tw') || url.includes('ycut.com.tw')) {
      scrapeYungyi(sheet, row, url);
    } else if (url.includes('housefun.com.tw')) {
      scrapeHousefun(sheet, row, url);
    } else {
      SpreadsheetApp.getUi().alert('⚠️ 不支援的網址類型\n\n目前支援：\n- 591 房屋交易網\n- 樂屋網\n- 永義房屋\n- 好房網');
    }
  } catch (error) {
    Logger.log('爬取失敗: ' + error);
    sheet.getRange(row, CONFIG.COLUMNS.NAME).setValue('❌ 爬取失敗：' + error.message);
  }
}

// ============================================================
// 3. 網站爬蟲函數
// ============================================================

function scrape591(sheet, row, url) {
  try {
    const response = UrlFetchApp.fetch(url, {muteHttpExceptions: true, followRedirects: true});
    const html = response.getContentText();
    
    // 檢查是否被重定向到其他網站
    const finalUrl = response.getHeaders()['Location'] || url;
    if (finalUrl.includes('rakuya.com.tw')) {
      scrapeRakuya(sheet, row, finalUrl);
      return;
    }
    
    // 解析基本資訊
    const nameMatch = html.match(/<h1[^>]*>([^<]+)</i) || html.match(/<title>([^<|]+)/i);
    const addressMatch = html.match(/地址[：:]\s*([^<\n]+)/i) || html.match(/address[^>]*>([^<]+)</i);
    const priceMatch = html.match(/([0-9,]+)\s*萬/i);
    
    const name = nameMatch ? nameMatch[1].trim() : '';
    const address = addressMatch ? addressMatch[1].trim() : '';
    const price = priceMatch ? parseInt(priceMatch[1].replace(/,/g, '')) : '';
    const district = extractDistrict(address);
    
    // 填入資料
    sheet.getRange(row, CONFIG.COLUMNS.NAME).setValue(name || '請手動填入案名');
    sheet.getRange(row, CONFIG.COLUMNS.DISTRICT).setValue(district);
    sheet.getRange(row, CONFIG.COLUMNS.ADDRESS).setValue(address);
    sheet.getRange(row, CONFIG.COLUMNS.PRICE).setValue(price);
    sheet.getRange(row, CONFIG.COLUMNS.TAGS).setValue('出售中');
    sheet.getRange(row, CONFIG.COLUMNS.STATUS).setValue('上架');
    
    fillDefaultAgent(sheet, row);
    
    if (address) {
      geocodeAddress(sheet, row, address);
    }
    
    updateTimestamp(sheet, row);
    
    SpreadsheetApp.getUi().alert('✅ 591 資料爬取完成！\n\n請手動補充：\n- 圖片網址\n- 房屋特色');
    
  } catch (error) {
    throw new Error('591 爬取失敗: ' + error.message);
  }
}

function scrapeRakuya(sheet, row, url) {
  try {
    const response = UrlFetchApp.fetch(url, {muteHttpExceptions: true});
    const html = response.getContentText();
    
    // 從 title 標籤提取案名
    const titleMatch = html.match(/<title>([^<|]+)/i);
    const name = titleMatch ? titleMatch[1].trim() : '';
    
    // 從頁面內容提取地址
    const addressMatch = html.match(/台中市[^<\n]{5,30}/i) || html.match(/南投縣[^<\n]{5,30}/i);
    const address = addressMatch ? addressMatch[0].trim() : '';
    
    // 提取價格
    const priceMatch = html.match(/([0-9,]+)\s*萬/i);
    const price = priceMatch ? parseInt(priceMatch[1].replace(/,/g, '')) : '';
    
    const district = extractDistrict(address);
    
    // 填入資料
    sheet.getRange(row, CONFIG.COLUMNS.NAME).setValue(name);
    sheet.getRange(row, CONFIG.COLUMNS.DISTRICT).setValue(district);
    sheet.getRange(row, CONFIG.COLUMNS.ADDRESS).setValue(address);
    sheet.getRange(row, CONFIG.COLUMNS.PRICE).setValue(price);
    sheet.getRange(row, CONFIG.COLUMNS.TAGS).setValue('出售中');
    sheet.getRange(row, CONFIG.COLUMNS.STATUS).setValue('上架');
    
    fillDefaultAgent(sheet, row);
    
    if (address) {
      geocodeAddress(sheet, row, address);
    }
    
    updateTimestamp(sheet, row);
    
    SpreadsheetApp.getUi().alert('✅ 樂屋網資料爬取完成！\n\n請手動補充：\n- 圖片網址\n- 房屋特色');
    
  } catch (error) {
    throw new Error('樂屋網爬取失敗: ' + error.message);
  }
}

function scrapeYungyi(sheet, row, url) {
  try {
    // 如果是短網址，先取得重定向後的完整網址
    const response = UrlFetchApp.fetch(url, {muteHttpExceptions: true, followRedirects: true});
    const html = response.getContentText();
    
    // 從 title 標籤提取案名
    const titleMatch = html.match(/<title>([^<|]+)/i);
    let name = titleMatch ? titleMatch[1].trim() : '';
    
    // 移除網站名稱後綴
    name = name.replace(/\s*\|.*$/, '').trim();
    
    // 提取地址
    const addressMatch = html.match(/台中市[^<\n]{5,50}/i);
    const address = addressMatch ? addressMatch[0].trim() : '';
    
    // 提取價格
    const priceMatch = html.match(/([0-9,]+)\s*萬/i);
    const price = priceMatch ? parseInt(priceMatch[1].replace(/,/g, '')) : '';
    
    const district = extractDistrict(address);
    
    // 填入資料
    sheet.getRange(row, CONFIG.COLUMNS.NAME).setValue(name);
    sheet.getRange(row, CONFIG.COLUMNS.DISTRICT).setValue(district);
    sheet.getRange(row, CONFIG.COLUMNS.ADDRESS).setValue(address);
    sheet.getRange(row, CONFIG.COLUMNS.PRICE).setValue(price);
    sheet.getRange(row, CONFIG.COLUMNS.TAGS).setValue('電梯大樓, 出售中');
    sheet.getRange(row, CONFIG.COLUMNS.STATUS).setValue('上架');
    
    fillDefaultAgent(sheet, row);
    
    if (address) {
      geocodeAddress(sheet, row, address);
    }
    
    updateTimestamp(sheet, row);
    
    SpreadsheetApp.getUi().alert('✅ 永義房屋資料爬取完成！\n\n請手動補充：\n- 圖片網址\n- 房屋特色');
    
  } catch (error) {
    throw new Error('永義房屋爬取失敗: ' + error.message);
  }
}

function scrapeHousefun(sheet, row, url) {
  try {
    const response = UrlFetchApp.fetch(url, {muteHttpExceptions: true});
    const html = response.getContentText();
    
    const titleMatch = html.match(/<title>([^<|]+)/i);
    const name = titleMatch ? titleMatch[1].trim() : '';
    
    const addressMatch = html.match(/台中市[^<\n]{5,30}/i);
    const address = addressMatch ? addressMatch[0].trim() : '';
    
    const priceMatch = html.match(/([0-9,]+)\s*萬/i);
    const price = priceMatch ? parseInt(priceMatch[1].replace(/,/g, '')) : '';
    
    const district = extractDistrict(address);
    
    sheet.getRange(row, CONFIG.COLUMNS.NAME).setValue(name);
    sheet.getRange(row, CONFIG.COLUMNS.DISTRICT).setValue(district);
    sheet.getRange(row, CONFIG.COLUMNS.ADDRESS).setValue(address);
    sheet.getRange(row, CONFIG.COLUMNS.PRICE).setValue(price);
    sheet.getRange(row, CONFIG.COLUMNS.TAGS).setValue('出售中');
    sheet.getRange(row, CONFIG.COLUMNS.STATUS).setValue('上架');
    
    fillDefaultAgent(sheet, row);
    
    if (address) {
      geocodeAddress(sheet, row, address);
    }
    
    updateTimestamp(sheet, row);
    
    SpreadsheetApp.getUi().alert('✅ 好房網資料爬取完成！\n\n請手動補充：\n- 圖片網址\n- 房屋特色');
    
  } catch (error) {
    throw new Error('好房網爬取失敗: ' + error.message);
  }
}

// ============================================================
// 4. 輔助函數
// ============================================================

function extractDistrict(address) {
  if (!address) return '';
  
  // 提取台中市行政區
  const districtMatch = address.match(/台中市([^市區]{2,3}區)/);
  if (districtMatch) {
    return districtMatch[1];
  }
  
  // 如果沒有找到，嘗試直接匹配區名
  for (const district in CONFIG.DISTRICT_COORDS) {
    if (address.includes(district)) {
      return district;
    }
  }
  
  return '';
}

function geocodeAddress(sheet, row, address) {
  try {
    if (CONFIG.MAPS_API_KEY === 'YOUR_GOOGLE_MAPS_API_KEY') {
      // 如果沒有設定 API Key，使用預設座標
      const district = sheet.getRange(row, CONFIG.COLUMNS.DISTRICT).getValue();
      if (district && CONFIG.DISTRICT_COORDS[district]) {
        const coords = CONFIG.DISTRICT_COORDS[district];
        sheet.getRange(row, CONFIG.COLUMNS.LAT).setValue(coords.lat);
        sheet.getRange(row, CONFIG.COLUMNS.LNG).setValue(coords.lng);
      }
      return;
    }
    
    const geocodeUrl = 'https://maps.googleapis.com/maps/api/geocode/json?address=' + 
                       encodeURIComponent(address) + 
                       '&key=' + CONFIG.MAPS_API_KEY;
    
    const response = UrlFetchApp.fetch(geocodeUrl);
    const data = JSON.parse(response.getContentText());
    
    if (data.status === 'OK' && data.results.length > 0) {
      const location = data.results[0].geometry.location;
      sheet.getRange(row, CONFIG.COLUMNS.LAT).setValue(location.lat);
      sheet.getRange(row, CONFIG.COLUMNS.LNG).setValue(location.lng);
    } else {
      // 如果地理編碼失敗，使用預設座標
      const district = sheet.getRange(row, CONFIG.COLUMNS.DISTRICT).getValue();
      if (district && CONFIG.DISTRICT_COORDS[district]) {
        const coords = CONFIG.DISTRICT_COORDS[district];
        sheet.getRange(row, CONFIG.COLUMNS.LAT).setValue(coords.lat);
        sheet.getRange(row, CONFIG.COLUMNS.LNG).setValue(coords.lng);
      }
    }
  } catch (error) {
    Logger.log('地理編碼失敗: ' + error);
    // 使用預設座標
    const district = sheet.getRange(row, CONFIG.COLUMNS.DISTRICT).getValue();
    if (district && CONFIG.DISTRICT_COORDS[district]) {
      const coords = CONFIG.DISTRICT_COORDS[district];
      sheet.getRange(row, CONFIG.COLUMNS.LAT).setValue(coords.lat);
      sheet.getRange(row, CONFIG.COLUMNS.LNG).setValue(coords.lng);
    }
  }
}

function fillDefaultAgent(sheet, row) {
  sheet.getRange(row, CONFIG.COLUMNS.AGENT_NAME).setValue(CONFIG.DEFAULT_AGENT.NAME);
  sheet.getRange(row, CONFIG.COLUMNS.AGENT_PHONE).setValue(CONFIG.DEFAULT_AGENT.PHONE);
  sheet.getRange(row, CONFIG.COLUMNS.AGENT_LINE).setValue(CONFIG.DEFAULT_AGENT.LINE);
}

function updateTimestamp(sheet, row) {
  const now = new Date();
  const timestamp = Utilities.formatDate(now, 'Asia/Taipei', 'yyyy-MM-dd HH:mm:ss');
  sheet.getRange(row, CONFIG.COLUMNS.UPDATED).setValue(timestamp);
}
