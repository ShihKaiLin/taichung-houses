/**
 * 物件詳情頁面 JavaScript
 * 負責載入物件資料並渲染頁面
 */

// Google Sheets CSV 連結
const SHEET_CSV_URL = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vQShAl0-TbUU0MQdYVe53im2T6lXQgh_7g-bdL6HHpIBFtA2yfIAMbPw4J9RgZUkROb9AAiMhnRC0kH/pub?output=csv';

let currentProperty = null;
let lightbox = null;

/**
 * 從 URL 參數取得物件 ID
 */
function getPropertyIdFromURL() {
    const params = new URLSearchParams(window.location.search);
    return params.get('id');
}

/**
 * 載入物件資料
 */
async function loadPropertyData(propertyId) {
    try {
        const response = await fetch(SHEET_CSV_URL);
        const csvText = await response.text();
        
        const properties = parseCSV(csvText);
        
        // 根據 ID 尋找物件（ID 是 row index）
        const property = properties[parseInt(propertyId)];
        
        if (!property) {
            showError('找不到此物件');
            return null;
        }
        
        return property;
        
    } catch (error) {
        console.error('載入資料失敗:', error);
        showError('載入資料失敗，請稍後再試');
        return null;
    }
}

/**
 * 解析 CSV
 */
function parseCSV(csvText) {
    const lines = csvText.split('\n');
    const properties = [];
    
    for (let i = 1; i < lines.length; i++) {
        const line = lines[i].trim();
        if (!line) continue;
        
        const values = parseCSVLine(line);
        
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
            image1: values[8] || 'https://via.placeholder.com/800x600?text=No+Image',
            image2: values[9] || '',
            image3: values[10] || '',
            tags: values[11] || '出售中',
            agentName: values[12] || '林世塏',
            agentPhone: values[13] || '0938-615-351',
            agentLine: values[14] || 'https://line.me/ti/p/FDsMyAYDv_',
            updated: values[15] || '',
            status: values[16] || '上架'
        };
        
        if (property.status === '上架') {
            properties.push(property);
        }
    }
    
    return properties;
}

/**
 * 解析 CSV 行
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
 * 渲染物件詳情
 */
function renderPropertyDetail(property) {
    currentProperty = property;
    
    // 更新頁面標題
    document.getElementById('page-title').textContent = `${property.name} | SK-L 大台中地產戰略`;
    document.getElementById('page-description').content = `${property.name} - ${property.district} - ${formatPrice(property.price)} - ${property.features}`;
    
    // 更新 Open Graph
    document.getElementById('og-title').content = property.name;
    document.getElementById('og-description').content = `${property.district} - ${formatPrice(property.price)}`;
    document.getElementById('og-url').content = window.location.href;
    document.getElementById('og-image').content = property.image1;
    
    // 更新 Schema.org
    const schema = {
        "@context": "https://schema.org",
        "@type": "RealEstateListing",
        "name": property.name,
        "description": property.features,
        "url": window.location.href,
        "image": [property.image1, property.image2, property.image3].filter(img => img),
        "offers": {
            "@type": "Offer",
            "price": property.price * 10000,
            "priceCurrency": "TWD"
        },
        "address": {
            "@type": "PostalAddress",
            "addressLocality": property.district,
            "addressCountry": "TW"
        }
    };
    document.getElementById('schema-json').textContent = JSON.stringify(schema, null, 2);
    
    // 更新標籤
    const tagsContainer = document.getElementById('property-tags');
    const tags = property.tags.split(',').map(t => t.trim()).filter(t => t);
    tagsContainer.innerHTML = tags.map((tag, index) => {
        const className = index === 0 ? 'tag tag-success' : 'tag tag-primary';
        return `<span class="${className}">${tag}</span>`;
    }).join('');
    
    // 更新基本資訊
    document.getElementById('property-name').textContent = property.name;
    document.getElementById('property-address').textContent = property.address;
    document.getElementById('property-price').textContent = formatPrice(property.price);
    document.getElementById('property-features').textContent = property.features || '詳情請洽詢';
    document.getElementById('property-district').textContent = property.district;
    document.getElementById('property-updated').textContent = property.updated || '未提供';
    document.getElementById('original-link').href = property.url;
    
    // 更新圖片
    renderImages(property);
    
    // 更新經紀人資訊
    document.getElementById('agent-name').textContent = property.agentName;
    document.getElementById('phone-number').textContent = property.agentPhone;
    document.getElementById('agent-line').href = property.agentLine;
    document.getElementById('agent-phone').href = `tel:${property.agentPhone.replace(/-/g, '')}`;
    
    // 手機版聯絡按鈕
    document.getElementById('mobile-line').href = property.agentLine;
    document.getElementById('mobile-phone').href = `tel:${property.agentPhone.replace(/-/g, '')}`;
    
    // 初始化燈箱
    initLightbox();
}

/**
 * 渲染圖片
 */
function renderImages(property) {
    const images = [property.image1, property.image2, property.image3].filter(img => img);
    
    // 設定主圖
    const mainImage = document.getElementById('main-image');
    mainImage.src = images[0];
    mainImage.alt = property.name;
    
    // 渲染縮圖
    const thumbnailsContainer = document.getElementById('thumbnails');
    thumbnailsContainer.innerHTML = images.map((img, index) => `
        <img src="${img}" 
             alt="${property.name} - 圖片 ${index + 1}" 
             class="thumbnail ${index === 0 ? 'active' : ''} w-full h-32 object-cover rounded-lg shadow-md"
             onclick="changeMainImage(${index})"
             data-index="${index}">
    `).join('');
}

/**
 * 切換主圖
 */
function changeMainImage(index) {
    const images = [currentProperty.image1, currentProperty.image2, currentProperty.image3].filter(img => img);
    
    const mainImage = document.getElementById('main-image');
    mainImage.src = images[index];
    
    // 更新縮圖 active 狀態
    document.querySelectorAll('.thumbnail').forEach((thumb, i) => {
        if (i === index) {
            thumb.classList.add('active');
        } else {
            thumb.classList.remove('active');
        }
    });
}

/**
 * 初始化燈箱
 */
function initLightbox() {
    const images = [currentProperty.image1, currentProperty.image2, currentProperty.image3].filter(img => img);
    
    lightbox = GLightbox({
        elements: images.map((img, index) => ({
            href: img,
            type: 'image',
            title: `${currentProperty.name} - 圖片 ${index + 1}`
        }))
    });
}

/**
 * 開啟燈箱
 */
function openLightbox(index) {
    if (lightbox) {
        lightbox.openAt(index);
    }
}

/**
 * 格式化價格
 */
function formatPrice(price) {
    if (price >= 10000) {
        return `${(price / 10000).toFixed(2)} 億`;
    } else {
        return `${price.toLocaleString()}`;
    }
}

/**
 * 顯示錯誤訊息
 */
function showError(message) {
    document.querySelector('main').innerHTML = `
        <div class="container mx-auto px-4 py-16 text-center">
            <i class="fas fa-exclamation-triangle text-6xl text-red-400 mb-4"></i>
            <h1 class="text-2xl font-bold text-gray-900 mb-4">${message}</h1>
            <a href="./index.html" class="inline-block bg-forest-600 hover:bg-forest-700 text-white px-6 py-3 rounded-lg font-bold transition-all">
                <i class="fas fa-arrow-left mr-2"></i>返回首頁
            </a>
        </div>
    `;
}

/**
 * 初始化頁面
 */
async function initPage() {
    const propertyId = getPropertyIdFromURL();
    
    if (!propertyId) {
        showError('缺少物件 ID');
        return;
    }
    
    const property = await loadPropertyData(propertyId);
    
    if (property) {
        renderPropertyDetail(property);
    }
}

// 頁面載入完成後初始化
document.addEventListener('DOMContentLoaded', initPage);
