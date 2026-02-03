/**
 * 主應用程式模組
 * 負責整合資料、地圖、UI 互動
 */

// DOM 元素
const loadingEl = document.getElementById('loading');
const propertiesGridEl = document.getElementById('properties-grid');
const noResultsEl = document.getElementById('no-results');
const filterDistrictEl = document.getElementById('filter-district');
const filterPriceEl = document.getElementById('filter-price');
const filterKeywordEl = document.getElementById('filter-keyword');
const searchBtnEl = document.getElementById('search-btn');
const backToTopBtn = document.getElementById('back-to-top');
const mobileMenuBtn = document.getElementById('mobile-menu-btn');
const mobileMenu = document.getElementById('mobile-menu');

/**
 * 初始化應用程式
 */
async function initApp() {
    console.log('初始化應用程式...');
    
    // 初始化地圖
    initMap();
    
    // 載入資料
    allProperties = await loadPropertiesData();
    filteredProperties = [...allProperties];
    
    // 隱藏載入中
    loadingEl.classList.add('hidden');
    
    // 渲染物件列表
    renderProperties(filteredProperties);
    
    // 新增地圖標記
    addPropertyMarkers(filteredProperties);
    
    // 初始化篩選器
    initFilters();
    
    // 綁定事件
    bindEvents();
    
    console.log('應用程式初始化完成');
}

/**
 * 渲染物件列表
 */
function renderProperties(properties) {
    propertiesGridEl.innerHTML = '';
    
    if (properties.length === 0) {
        noResultsEl.classList.remove('hidden');
        return;
    }
    
    noResultsEl.classList.add('hidden');
    
    properties.forEach(property => {
        const cardHTML = generatePropertyCard(property);
        propertiesGridEl.innerHTML += cardHTML;
    });
}

/**
 * 初始化篩選器
 */
function initFilters() {
    // 填充行政區選項
    const districts = getDistricts();
    districts.forEach(district => {
        const option = document.createElement('option');
        option.value = district;
        option.textContent = district;
        filterDistrictEl.appendChild(option);
    });
}

/**
 * 執行篩選
 */
function performFilter() {
    const district = filterDistrictEl.value;
    const priceRange = filterPriceEl.value;
    const keyword = filterKeywordEl.value.trim();
    
    filteredProperties = filterProperties(district, priceRange, keyword);
    
    // 更新 UI
    renderProperties(filteredProperties);
    addPropertyMarkers(filteredProperties);
    
    // 滾動到物件列表
    document.getElementById('properties').scrollIntoView({ behavior: 'smooth' });
    
    console.log(`篩選結果：${filteredProperties.length} 筆`);
}

/**
 * 綁定事件監聽器
 */
function bindEvents() {
    // 搜尋按鈕
    searchBtnEl.addEventListener('click', performFilter);
    
    // Enter 鍵搜尋
    filterKeywordEl.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            performFilter();
        }
    });
    
    // 回到頂部按鈕
    window.addEventListener('scroll', () => {
        if (window.scrollY > 300) {
            backToTopBtn.classList.remove('hidden');
        } else {
            backToTopBtn.classList.add('hidden');
        }
    });
    
    backToTopBtn.addEventListener('click', () => {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });
    
    // 手機版選單
    mobileMenuBtn.addEventListener('click', () => {
        mobileMenu.classList.toggle('hidden');
    });
    
    // 手機版選單連結點擊後關閉選單
    const mobileMenuLinks = mobileMenu.querySelectorAll('a');
    mobileMenuLinks.forEach(link => {
        link.addEventListener('click', () => {
            mobileMenu.classList.add('hidden');
        });
    });
    
    // 平滑滾動
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });
}

/**
 * 顯示錯誤訊息
 */
function showError(message) {
    loadingEl.classList.add('hidden');
    propertiesGridEl.innerHTML = `
        <div class="col-span-full text-center py-16">
            <i class="fas fa-exclamation-triangle text-6xl text-red-400 mb-4"></i>
            <p class="text-xl text-gray-600">${message}</p>
            <button onclick="location.reload()" class="mt-4 bg-forest-600 hover:bg-forest-700 text-white px-6 py-3 rounded-lg font-bold transition-all">
                <i class="fas fa-redo mr-2"></i>重新載入
            </button>
        </div>
    `;
}

// 頁面載入完成後初始化
document.addEventListener('DOMContentLoaded', () => {
    initApp().catch(error => {
        console.error('初始化失敗:', error);
        showError('載入資料失敗，請稍後再試');
    });
});

// 處理頁面可見性變化（用於優化效能）
document.addEventListener('visibilitychange', () => {
    if (!document.hidden && map) {
        setTimeout(() => {
            resizeMap();
        }, 200);
    }
});
