/**
 * 資料處理模組
 * 負責從 Google Sheets 讀取資料並處理
 */

// Google Sheets CSV 連結（請替換為您的試算表連結）
const SHEET_CSV_URL = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vQShAl0-TbUU0MQdYVe53im2T6lXQgh_7g-bdL6HHpIBFtA2yfIAMbPw4J9RgZUkROb9AAiMhnRC0kH/pub?output=csv';

// 全域變數
let allProperties = [];
let filteredProperties = [];

/**
 * 從 Google Sheets 讀取資料
 */
async function loadPropertiesData() {
    try {
        console.log('開始載入資料...');
        
        const response = await fetch(SHEET_CSV_URL);
        const csvText = await response.text();
        
        // 解析 CSV
        const properties = parseCSV(csvText);
        
        console.log(`成功載入 ${properties.length} 筆資料`);
        
        return properties;
        
    } catch (error) {
        console.error('載入資料失敗:', error);
        return [];
    }
}

/**
 * 解析 CSV 文字為物件陣列
 */
function parseCSV(csvText) {
    const lines = csvText.split('\n');
    const headers = lines[0].split(',').map(h => h.trim());
    
    const properties = [];
    
    for (let i = 1; i < lines.length; i++) {
        const line = lines[i].trim();
        if (!line) continue;
        
        const values = parseCSVLine(line);
        
        // 建立物件
        const property = {
            id: i - 1,
            url: values[0] || '',
            name: values[1] || '',
            district: values[2] || '',
            address: values[3] || '',
            price: parseFloat(values[4]) || 0,
            lat: parseFloat(values[5]) || 0,
            lng: parseFloat(values[6]) || 0,
            features: values[7] || '',
            image1: values[8] || 'https://via.placeholder.com/400x300?text=No+Image',
            image2: values[9] || '',
            image3: values[10] || '',
            tags: values[11] || '出售中',
            agentName: values[12] || '林世塏',
            agentPhone: values[13] || '0938-615-351',
            agentLine: values[14] || 'https://line.me/ti/p/FDsMyAYDv_',
            updated: values[15] || '',
            status: values[16] || '上架'
        };
        
        // 只加入上架且有經緯度的物件
        if (property.status === '上架' && property.lat && property.lng) {
            properties.push(property);
        }
    }
    
    return properties;
}

/**
 * 解析 CSV 行（處理逗號和引號）
 */
function parseCSVLine(line) {
    const values = [];
    let current = '';
    let inQuotes = false;
    
    for (let i = 0; i < line.length; i++) {
        const char = line[i];
        
        if (char === '"') {
            inQuotes = !inQuotes;
        } else if (char === ',' && !inQuotes) {
            values.push(current.trim());
            current = '';
        } else {
            current += char;
        }
    }
    
    values.push(current.trim());
    
    return values;
}

/**
 * 篩選物件
 */
function filterProperties(district, priceRange, keyword) {
    let filtered = [...allProperties];
    
    // 行政區篩選
    if (district) {
        filtered = filtered.filter(p => p.district === district);
    }
    
    // 價格區間篩選
    if (priceRange) {
        const [min, max] = priceRange.split('-').map(Number);
        filtered = filtered.filter(p => p.price >= min && p.price <= max);
    }
    
    // 關鍵字搜尋
    if (keyword) {
        const kw = keyword.toLowerCase();
        filtered = filtered.filter(p => 
            p.name.toLowerCase().includes(kw) ||
            p.features.toLowerCase().includes(kw) ||
            p.address.toLowerCase().includes(kw)
        );
    }
    
    return filtered;
}

/**
 * 取得所有行政區列表
 */
function getDistricts() {
    const districts = [...new Set(allProperties.map(p => p.district))];
    return districts.sort();
}

/**
 * 格式化價格顯示
 */
function formatPrice(price) {
    if (price >= 10000) {
        return `${(price / 10000).toFixed(2)} 億`;
    } else {
        return `${price} 萬`;
    }
}

/**
 * 產生物件卡片 HTML
 */
function generatePropertyCard(property) {
    return `
        <div class="property-card animate-slide-in-up">
            <img src="${property.image1}" alt="${property.name}" onerror="this.src='https://via.placeholder.com/400x300?text=No+Image'">
            <div class="property-card-content">
                <span class="district">${property.district}</span>
                <h3>${property.name}</h3>
                <div class="price">${formatPrice(property.price)}</div>
                <div class="address">
                    <i class="fas fa-map-marker-alt mr-2 text-gray-400"></i>
                    ${property.address}
                </div>
                <div class="features">
                    <i class="fas fa-home mr-2 text-gray-400"></i>
                    ${property.features || '詳情請洽詢'}
                </div>
                <a href="./property-detail.html?id=${property.id}" class="btn-view">
                    <i class="fas fa-info-circle mr-2"></i>查看詳情
                </a>
            </div>
        </div>
    `;
}

/**
 * 產生地圖 Popup HTML
 */
function generatePopupHTML(property) {
    return `
        <div class="custom-popup">
            <img src="${property.image1}" alt="${property.name}" onerror="this.src='https://via.placeholder.com/280x180?text=No+Image'">
            <div class="custom-popup-content">
                <h3>${property.name}</h3>
                <div class="price">${formatPrice(property.price)}</div>
                <div class="address">
                    <i class="fas fa-map-marker-alt mr-2"></i>
                    ${property.district}
                </div>
                <div class="features">
                    ${property.features || '詳情請洽詢'}
                </div>
                <a href="./property-detail.html?id=${property.id}" class="btn-link">
                    <i class="fas fa-info-circle mr-2"></i>查看詳情
                </a>
            </div>
        </div>
    `;
}
