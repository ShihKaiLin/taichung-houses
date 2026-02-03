/**
 * 地圖模組
 * 負責 Leaflet.js 地圖初始化與標記管理
 */

let map = null;
let markersLayer = null;

/**
 * 初始化 Leaflet 地圖
 */
function initMap() {
    // 建立地圖（中心點設在台中市）
    map = L.map('leaflet-map').setView([24.1477, 120.6736], 12);
    
    // 加入 OpenStreetMap 圖層
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 19
    }).addTo(map);
    
    // 建立標記聚類群組
    markersLayer = L.markerClusterGroup({
        maxClusterRadius: 50,
        spiderfyOnMaxZoom: true,
        showCoverageOnHover: false,
        zoomToBoundsOnClick: true
    });
    
    map.addLayer(markersLayer);
    
    console.log('地圖初始化完成');
}

/**
 * 清除所有標記
 */
function clearMarkers() {
    if (markersLayer) {
        markersLayer.clearLayers();
    }
}

/**
 * 新增物件標記到地圖
 */
function addPropertyMarkers(properties) {
    clearMarkers();
    
    properties.forEach(property => {
        if (!property.lat || !property.lng) return;
        
        // 建立自訂圖示
        const icon = L.divIcon({
            className: 'custom-marker',
            html: '<i class="fas fa-home"></i>',
            iconSize: [40, 40],
            iconAnchor: [20, 20],
            popupAnchor: [0, -20]
        });
        
        // 建立標記
        const marker = L.marker([property.lat, property.lng], { icon: icon });
        
        // 綁定 Popup
        const popupHTML = generatePopupHTML(property);
        marker.bindPopup(popupHTML, {
            maxWidth: 300,
            className: 'custom-popup-wrapper'
        });
        
        // 加入到聚類群組
        markersLayer.addLayer(marker);
    });
    
    // 自動調整地圖視野以包含所有標記
    if (properties.length > 0) {
        const bounds = markersLayer.getBounds();
        if (bounds.isValid()) {
            map.fitBounds(bounds, { padding: [50, 50] });
        }
    }
    
    console.log(`已新增 ${properties.length} 個標記`);
}

/**
 * 飛到指定位置
 */
function flyToLocation(lat, lng, zoom = 15) {
    if (map) {
        map.flyTo([lat, lng], zoom, {
            duration: 1.5
        });
    }
}

/**
 * 重新調整地圖大小（響應式）
 */
function resizeMap() {
    if (map) {
        map.invalidateSize();
    }
}

// 視窗大小改變時重新調整地圖
window.addEventListener('resize', () => {
    setTimeout(resizeMap, 200);
});
