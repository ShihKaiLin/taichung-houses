import os, csv, requests, html, shutil, re, json
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup

# ============================================================
# 1. 核心品牌配置 (SK-L Agency Branding)
# ============================================================
SITE_TITLE = "SK-L 大台中地產戰略"
PROJECT_NAME = "taichung-houses"
BASE_URL = f"https://shihkailin.github.io/{PROJECT_NAME}"
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQShAl0-TbUU0MQdYVe53im2T6lXQgh_7g-bdL6HHpIBFtA2yfIAMbPw4J9RgZUkROb9AAiMhnRC0kH/pub?output=csv"
MAP_KEY = os.getenv("MAPS_API_KEY", "AIzaSyDzgnI2Ucv622CRkWwo2GE5JRrs_Y4HQY0")

AGENT_INFO = {
    "name": "林世塏", 
    "title": "大台中房產置產顧問",
    "phone": "0938-615-351", 
    "line": "https://line.me/ti/p/FDsMyAYDv_",
    "photo": f"https://raw.githubusercontent.com/ShihKaiLin/{PROJECT_NAME}/main/images/agent_photo.jpg"
}

# ============================================================
# 2. 升級版 CSS 視覺系統（全寬度地圖 + 頂部篩選列）
# ============================================================
CSS = f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@300;400;500;700;900&display=swap');
    
    :root {{
        --primary-navy: #003D5C;
        --primary-green: #4CAF50;
        --primary-blue: #2196F3;
        --accent-gold: #D4AF37;
        --bg-light: #F5F7FA;
        --bg-white: #FFFFFF;
        --text-dark: #1A1A1A;
        --text-gray: #6B7280;
        --border-light: #E5E7EB;
        --shadow-sm: 0 2px 8px rgba(0,0,0,0.08);
        --shadow-md: 0 4px 16px rgba(0,0,0,0.12);
        --shadow-lg: 0 8px 32px rgba(0,0,0,0.16);
    }}
    
    * {{
        box-sizing: border-box;
        margin: 0;
        padding: 0;
    }}
    
    body {{
        font-family: 'Noto Sans TC', -apple-system, BlinkMacSystemFont, sans-serif;
        background: var(--bg-light);
        color: var(--text-dark);
        line-height: 1.7;
        overflow-x: hidden;
    }}
    
    /* ========== 導航欄 ========== */
    .navbar {{
        position: fixed;
        top: 0;
        width: 100%;
        z-index: 5000;
        background: var(--primary-navy);
        padding: 18px 60px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: var(--shadow-md);
        transition: all 0.3s ease;
    }}
    
    .logo {{
        font-weight: 900;
        font-size: 22px;
        letter-spacing: 4px;
        text-decoration: none;
        color: var(--bg-white);
        text-transform: uppercase;
        transition: all 0.3s ease;
    }}
    
    .logo:hover {{
        color: var(--primary-green);
        transform: scale(1.05);
    }}
    
    .nav-links {{
        display: flex;
        gap: 35px;
        list-style: none;
    }}
    
    .nav-links a {{
        color: var(--bg-white);
        text-decoration: none;
        font-weight: 500;
        font-size: 16px;
        transition: all 0.3s ease;
        position: relative;
    }}
    
    .nav-links a::after {{
        content: '';
        position: absolute;
        bottom: -5px;
        left: 0;
        width: 0;
        height: 2px;
        background: var(--primary-green);
        transition: width 0.3s ease;
    }}
    
    .nav-links a:hover::after {{
        width: 100%;
    }}
    
    /* ========== Hero 區域 ========== */
    .hero {{
        height: 75vh;
        min-height: 600px;
        background: linear-gradient(135deg, rgba(0,61,92,0.85) 0%, rgba(76,175,80,0.65) 100%), 
                    url('https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=1920&q=80') center/cover;
        display: flex;
        align-items: center;
        justify-content: center;
        text-align: center;
        color: var(--bg-white);
        position: relative;
        margin-top: 60px;
    }}
    
    .hero::before {{
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: radial-gradient(circle at center, transparent 0%, rgba(0,0,0,0.3) 100%);
    }}
    
    .hero-content {{
        position: relative;
        z-index: 10;
        max-width: 900px;
        padding: 0 30px;
    }}
    
    .hero-content h1 {{
        font-size: 64px;
        font-weight: 900;
        margin: 0 0 20px 0;
        letter-spacing: 6px;
        text-shadow: 2px 4px 12px rgba(0,0,0,0.3);
        animation: fadeInUp 1s ease;
    }}
    
    .hero-content p {{
        font-size: 22px;
        font-weight: 400;
        letter-spacing: 2px;
        opacity: 0.95;
        animation: fadeInUp 1.2s ease;
    }}
    
    @keyframes fadeInUp {{
        from {{
            opacity: 0;
            transform: translateY(30px);
        }}
        to {{
            opacity: 1;
            transform: translateY(0);
        }}
    }}
    
    /* ========== 地圖容器（全寬度） ========== */
    .map-container {{
        width: 100%;
        position: relative;
        background: var(--bg-white);
        box-shadow: var(--shadow-sm);
    }}
    
    /* ========== 頂部橫向篩選列 ========== */
    .filter-bar {{
        width: 100%;
        background: var(--bg-white);
        padding: 20px 40px;
        display: flex;
        gap: 15px;
        align-items: center;
        flex-wrap: wrap;
        border-bottom: 2px solid var(--border-light);
        box-shadow: var(--shadow-sm);
    }}
    
    .filter-group {{
        display: flex;
        flex-direction: column;
        gap: 5px;
        min-width: 150px;
        flex: 1;
    }}
    
    .filter-group label {{
        font-weight: 600;
        font-size: 13px;
        color: var(--text-gray);
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    
    .filter-group select {{
        width: 100%;
        padding: 12px 15px;
        border: 2px solid var(--border-light);
        border-radius: 8px;
        font-size: 15px;
        font-family: 'Noto Sans TC', sans-serif;
        transition: all 0.3s ease;
        background: var(--bg-white);
        cursor: pointer;
    }}
    
    .filter-group select:focus {{
        outline: none;
        border-color: var(--primary-green);
        box-shadow: 0 0 0 3px rgba(76,175,80,0.1);
    }}
    
    .filter-btn {{
        padding: 12px 35px;
        background: var(--primary-green);
        color: var(--bg-white);
        border: none;
        border-radius: 8px;
        font-size: 15px;
        font-weight: 700;
        cursor: pointer;
        transition: all 0.3s ease;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-top: auto;
        box-shadow: 0 2px 8px rgba(76,175,80,0.3);
    }}
    
    .filter-btn:hover {{
        background: #45a049;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(76,175,80,0.4);
    }}
    
    /* ========== 地圖區域（全寬度） ========== */
    #map {{
        height: 600px;
        width: 100%;
        filter: grayscale(20%) contrast(100%);
    }}
    
    /* ========== 物件網格 ========== */
    .section-title {{
        text-align: center;
        font-size: 42px;
        font-weight: 900;
        color: var(--text-dark);
        margin: 80px 0 50px;
        letter-spacing: 2px;
    }}
    
    .grid {{
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
        gap: 40px;
        padding: 0 60px 100px;
        max-width: 1400px;
        margin: 0 auto;
    }}
    
    .card-anchor {{
        text-decoration: none;
        color: inherit;
        display: block;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    }}
    
    .card {{
        background: var(--bg-white);
        border-radius: 16px;
        overflow: hidden;
        box-shadow: var(--shadow-sm);
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        height: 100%;
        display: flex;
        flex-direction: column;
    }}
    
    .card-anchor:hover .card {{
        transform: translateY(-8px);
        box-shadow: var(--shadow-lg);
    }}
    
    .card-img-wrapper {{
        position: relative;
        width: 100%;
        height: 280px;
        overflow: hidden;
    }}
    
    .card-img {{
        width: 100%;
        height: 100%;
        object-fit: cover;
        transition: transform 0.6s cubic-bezier(0.4, 0, 0.2, 1);
    }}
    
    .card-anchor:hover .card-img {{
        transform: scale(1.08);
    }}
    
    .card-badge {{
        position: absolute;
        top: 20px;
        left: 20px;
        background: var(--primary-green);
        color: var(--bg-white);
        padding: 8px 18px;
        border-radius: 8px;
        font-weight: 700;
        font-size: 14px;
        letter-spacing: 1px;
        box-shadow: var(--shadow-sm);
    }}
    
    .card-body {{
        padding: 28px;
        flex: 1;
        display: flex;
        flex-direction: column;
        gap: 12px;
    }}
    
    .card-area {{
        color: var(--primary-navy);
        font-weight: 600;
        font-size: 14px;
        text-transform: uppercase;
        letter-spacing: 1.5px;
    }}
    
    .card-title {{
        font-size: 22px;
        font-weight: 700;
        color: var(--text-dark);
        line-height: 1.4;
        margin: 0;
    }}
    
    .card-price {{
        font-size: 32px;
        font-weight: 900;
        color: var(--primary-green);
        margin-top: auto;
    }}
    
    .card-price span {{
        font-size: 18px;
        font-weight: 500;
        color: var(--text-gray);
    }}
    
    /* ========== 關於區域 ========== */
    .about-section {{
        background: var(--bg-white);
        padding: 120px 60px;
        display: flex;
        align-items: center;
        gap: 80px;
        max-width: 1400px;
        margin: 80px auto;
        border-radius: 20px;
        box-shadow: var(--shadow-sm);
    }}
    
    .about-img {{
        width: 450px;
        height: 600px;
        object-fit: cover;
        border-radius: 20px;
        box-shadow: 30px 30px 0 var(--primary-green);
        transition: all 0.4s ease;
    }}
    
    .about-img:hover {{
        transform: translate(-5px, -5px);
        box-shadow: 35px 35px 0 var(--primary-green);
    }}
    
    .about-content {{
        flex: 1;
    }}
    
    .about-content h3 {{
        font-size: 38px;
        font-weight: 900;
        color: var(--text-dark);
        margin-bottom: 15px;
        letter-spacing: 1px;
    }}
    
    .about-content p {{
        font-size: 18px;
        line-height: 2;
        color: var(--text-gray);
    }}
    
    /* ========== 聯絡欄 ========== */
    .contact-bar {{
        position: fixed;
        bottom: 40px;
        left: 50%;
        transform: translateX(-50%);
        width: 90%;
        max-width: 600px;
        background: var(--primary-navy);
        padding: 20px;
        border-radius: 20px;
        display: flex;
        gap: 15px;
        z-index: 10000;
        box-shadow: var(--shadow-lg);
        animation: slideUp 0.6s ease;
    }}
    
    @keyframes slideUp {{
        from {{
            opacity: 0;
            transform: translate(-50%, 100px);
        }}
        to {{
            opacity: 1;
            transform: translate(-50%, 0);
        }}
    }}
    
    .btn-contact {{
        flex: 1;
        text-align: center;
        padding: 18px;
        border-radius: 12px;
        text-decoration: none;
        color: var(--bg-white);
        font-weight: 900;
        font-size: 16px;
        transition: all 0.3s ease;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
    }}
    
    .btn-line {{
        background: #06C755;
    }}
    
    .btn-line:hover {{
        background: #05B04C;
        transform: translateY(-3px);
        box-shadow: 0 8px 20px rgba(6,199,85,0.4);
    }}
    
    .btn-phone {{
        background: var(--primary-green);
    }}
    
    .btn-phone:hover {{
        background: #45a049;
        transform: translateY(-3px);
        box-shadow: 0 8px 20px rgba(76,175,80,0.4);
    }}
    
    /* ========== 詳細頁面 ========== */
    .detail-hero {{
        height: 65vh;
        min-height: 500px;
        background-size: cover;
        background-position: center;
        position: relative;
        margin-top: 60px;
    }}
    
    .detail-hero::before {{
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(to bottom, transparent 0%, rgba(0,0,0,0.6) 100%);
    }}
    
    .detail-content {{
        padding: 80px 60px;
        max-width: 1000px;
        margin: 0 auto;
    }}
    
    .detail-content h1 {{
        font-size: 48px;
        font-weight: 900;
        color: var(--text-dark);
        margin-bottom: 30px;
        letter-spacing: 1px;
    }}
    
    .detail-price {{
        font-size: 56px;
        font-weight: 900;
        color: var(--primary-green);
        margin-bottom: 40px;
    }}
    
    .detail-price span {{
        font-size: 28px;
        font-weight: 500;
        color: var(--text-gray);
    }}
    
    .detail-description {{
        font-size: 20px;
        line-height: 2.2;
        color: var(--text-gray);
        background: var(--bg-white);
        padding: 50px;
        border-radius: 20px;
        box-shadow: var(--shadow-sm);
    }}
    
    /* ========== 響應式設計 ========== */
    @media (max-width: 1024px) {{
        .grid {{
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            gap: 30px;
            padding: 0 40px 80px;
        }}
        
        .about-section {{
            flex-direction: column;
            padding: 80px 40px;
        }}
        
        .about-img {{
            width: 100%;
            max-width: 450px;
            height: 500px;
        }}
        
        .filter-bar {{
            padding: 15px 20px;
        }}
    }}
    
    @media (max-width: 768px) {{
        .navbar {{
            padding: 15px 25px;
        }}
        
        .logo {{
            font-size: 18px;
            letter-spacing: 2px;
        }}
        
        .nav-links {{
            display: none;
        }}
        
        .hero {{
            height: 60vh;
            min-height: 500px;
        }}
        
        .hero-content h1 {{
            font-size: 42px;
            letter-spacing: 3px;
        }}
        
        .hero-content p {{
            font-size: 18px;
        }}
        
        .filter-bar {{
            flex-direction: column;
            gap: 10px;
        }}
        
        .filter-group {{
            width: 100%;
            min-width: auto;
        }}
        
        .filter-btn {{
            width: 100%;
        }}
        
        #map {{
            height: 400px;
        }}
        
        .grid {{
            grid-template-columns: 1fr;
            padding: 0 20px 60px;
        }}
        
        .about-section {{
            padding: 60px 25px;
            gap: 40px;
        }}
        
        .about-img {{
            height: 400px;
            box-shadow: 20px 20px 0 var(--primary-green);
        }}
        
        .about-content h3 {{
            font-size: 32px;
        }}
        
        .about-content p {{
            font-size: 16px;
        }}
        
        .contact-bar {{
            width: 95%;
            bottom: 20px;
            padding: 15px;
            flex-direction: column;
            gap: 10px;
        }}
        
        .detail-content {{
            padding: 60px 25px;
        }}
        
        .detail-content h1 {{
            font-size: 36px;
        }}
        
        .detail-price {{
            font-size: 42px;
        }}
        
        .detail-description {{
            font-size: 18px;
            padding: 35px 25px;
        }}
    }}
</style>
"""

def esc(s): 
    """HTML 轉義函數"""
    return html.escape(str(s or "").strip())

class SKL_Agency:
    def __init__(self):
        self.points = []
        self.items = []
        self.areas = set()
        self.types = set()

    def build_layout(self, title, body, is_home=False):
        """建立頁面佈局"""
        map_js = ""
        if is_home:
            data = json.dumps(self.points, ensure_ascii=False)
            map_js = f"""
            <script>
                var map;
                var markers = [];
                var infoWindow;
                
                window.initMap = function() {{
                    map = new google.maps.Map(document.getElementById('map'), {{ 
                        center: {{lat:24.162, lng:120.647}}, 
                        zoom:12, 
                        disableDefaultUI: false,
                        zoomControl: true,
                        mapTypeControl: false,
                        streetViewControl: false,
                        fullscreenControl: true,
                        styles: [
                            {{
                                "featureType": "all",
                                "elementType": "geometry",
                                "stylers": [{{"saturation": -20}}]
                            }},
                            {{
                                "featureType": "water",
                                "elementType": "geometry.fill",
                                "stylers": [{{"color": "#c8d7d4}}]
                            }}
                        ]
                    }});
                    
                    infoWindow = new google.maps.InfoWindow();
                    const pts = {data};
                    
                    pts.forEach((p, index) => {{
                        // 創建自定義藍色圓形標記，帶房屋圖示
                        const marker = new google.maps.Marker({{ 
                            position: {{lat: parseFloat(p.lat), lng: parseFloat(p.lng)}}, 
                            map: map,
                            icon: {{
                                path: google.maps.SymbolPath.CIRCLE,
                                scale: 12,
                                fillColor: '#2196F3',
                                fillOpacity: 1,
                                strokeColor: '#FFFFFF',
                                strokeWeight: 3
                            }},
                            title: p.name,
                            animation: google.maps.Animation.DROP
                        }});
                        
                        marker.addListener('click', () => {{ 
                            infoWindow.setContent(`
                                <div style="padding:15px;width:220px;font-family:'Noto Sans TC',sans-serif;">
                                    <img src="${{p.img}}" style="width:100%;border-radius:8px;margin-bottom:10px;" alt="${{p.name}}">
                                    <h4 style="margin:8px 0;font-size:16px;color:#1A1A1A;font-weight:700;">${{p.name}}</h4>
                                    <div style="font-size:22px;font-weight:900;color:#4CAF50;margin:8px 0;">${{p.price}}萬</div>
                                    <a href="${{p.url}}" style="display:inline-block;margin-top:10px;padding:10px 20px;background:#4CAF50;color:#fff;text-decoration:none;border-radius:8px;font-size:14px;font-weight:700;">查看詳情</a>
                                </div>
                            `); 
                            infoWindow.open(map, marker); 
                        }});
                        
                        markers.push(marker);
                    }});
                }}
                
                // 篩選功能
                window.filterProperties = function() {{
                    const area = document.getElementById('filter-area').value;
                    const type = document.getElementById('filter-type').value;
                    const rooms = document.getElementById('filter-rooms').value;
                    const price = document.getElementById('filter-price').value;
                    
                    const cards = document.querySelectorAll('.card-anchor');
                    cards.forEach(card => {{
                        const cardArea = card.dataset.area || '';
                        const cardType = card.dataset.type || '';
                        const cardRooms = card.dataset.rooms || '';
                        const cardPrice = parseFloat(card.dataset.price) || 0;
                        
                        let show = true;
                        
                        if (area !== 'all' && cardArea !== area) show = false;
                        if (type !== 'all' && cardType !== type) show = false;
                        if (rooms !== 'all' && cardRooms !== rooms) show = false;
                        
                        if (price !== 'all') {{
                            const [min, max] = price.split('-').map(p => parseFloat(p) || Infinity);
                            if (max) {{
                                if (cardPrice < min || cardPrice > max) show = false;
                            }} else {{
                                if (cardPrice < min) show = false;
                            }}
                        }}
                        
                        card.style.display = show ? 'block' : 'none';
                    }});
                }}
            </script>
            <script src="https://maps.googleapis.com/maps/api/js?key={MAP_KEY}&callback=initMap"></script>
            """
        
        return f"""<!DOCTYPE html>
<html lang='zh-TW'>
<head>
    <meta charset='utf-8'>
    <meta name='viewport' content='width=device-width,initial-scale=1'>
    <title>{esc(title)}</title>
    <meta name='description' content='SK-L 大台中地產戰略 - 專業房產置產顧問，為您提供台中精華區優質物件'>
    {CSS}
</head>
<body>{body}{map_js}</body>
</html>"""

    def run(self):
        """主執行函數"""
        # 清理舊目錄
        for f in ["area", "life"]:
            if Path(f).exists(): 
                shutil.rmtree(f)
            Path(f).mkdir(exist_ok=True)
        
        # 獲取資料
        res = requests.get(SHEET_URL)
        res.encoding = "utf-8-sig"
        rows = list(csv.DictReader(res.text.splitlines()))
        
        # 處理每個物件
        for i, r in enumerate(rows):
            name = r.get("案名", "").strip()
            if not name or r.get("狀態", "").upper() == "OFF": 
                continue
            
            # 處理圖片
            img = r.get("圖片網址", "").split('|')[0]
            if not img.startswith("http"): 
                img = f"https://raw.githubusercontent.com/ShihKaiLin/{PROJECT_NAME}/main/images/{img.lstrip('/')}"
            
            # 建立物件目錄
            slug = f"p{i}"
            Path(slug).mkdir(exist_ok=True)
            url = f"/{PROJECT_NAME}/{slug}/"
            
            # 收集篩選選項
            area = r.get("區域", "").strip()
            prop_type = r.get("類型", "").strip()
            if area:
                self.areas.add(area)
            if prop_type:
                self.types.add(prop_type)
            
            # 加入地圖標記（使用區域預設座標）
            # 台中市各區中心點座標
            area_coords = {
                "北屯區": {"lat": 24.1810, "lng": 120.7417},
                "南區": {"lat": 24.1005, "lng": 120.6634},
                "南屯區": {"lat": 24.1397, "lng": 120.6178},
                "大里區": {"lat": 24.0990, "lng": 120.6773},
                "西屯區": {"lat": 24.1816, "lng": 120.6194},
                "西區": {"lat": 24.1392, "lng": 120.6736},
                "沙鹿區": {"lat": 24.2259, "lng": 120.5686},
                "豐原區": {"lat": 24.2567, "lng": 120.7233},
                "中區": {"lat": 24.1439, "lng": 120.6820},
                "東區": {"lat": 24.1373, "lng": 120.7038}
            }
            
            if area and area in area_coords:
                # 加入小随機偏移以避免所有標記重疊
                import random
                offset_lat = random.uniform(-0.01, 0.01)
                offset_lng = random.uniform(-0.01, 0.01)
                self.points.append({
                    "name": name, 
                    "price": r.get("價格", ""), 
                    "img": img, 
                    "url": url, 
                    "lat": area_coords[area]["lat"] + offset_lat, 
                    "lng": area_coords[area]["lng"] + offset_lng
                })
                print(f"✅ {name}: {area} 區域座標")
            else:
                print(f"⚠️  {name}: 無法定位（區域: {area}）")
            
            # 建立詳細頁面
            detail = f"""
            <nav class="navbar">
                <a href="/{PROJECT_NAME}/" class="logo">SK-L AGENCY</a>
            </nav>
            <div class="detail-hero" style="background-image:url('{img}');"></div>
            <div class="detail-content">
                <h1>{esc(name)}</h1>
                <div class="detail-price">{esc(r.get('價格', ''))} <span>萬</span></div>
                <div class="detail-description">{esc(r.get('描述', ''))}</div>
            </div>
            <div class="contact-bar">
                <a class="btn-contact btn-line" href="{AGENT_INFO['line']}">💬 LINE 諮詢</a>
                <a class="btn-contact btn-phone" href="tel:{AGENT_INFO['phone']}">📞 電話聯絡</a>
            </div>
            """
            Path(f"{slug}/index.html").write_text(self.build_layout(name, detail), encoding="utf-8")
            self.items.append(r)
        
        # 建立篩選選項
        area_opts = "".join([f"<option value='{a}'>{a}</option>" for a in sorted(self.areas)])
        type_opts = "".join([f"<option value='{t}'>{t}</option>" for t in sorted(self.types)])
        
        # 建立物件卡片
        cards = ""
        for x in self.items[::-1]:
            idx = rows.index(x)
            img_url = self.points[self.items.index(x)]['img'] if self.items.index(x) < len(self.points) else ''
            price = x.get('價格', '0')
            rooms = x.get('房數', '')
            cards += f"""
            <a href='/{PROJECT_NAME}/p{idx}/' class='card-anchor' 
               data-area='{esc(x.get('區域', ''))}' 
               data-type='{esc(x.get('類型', ''))}' 
               data-rooms='{esc(rooms)}'
               data-price='{price}'>
                <div class='card'>
                    <div class='card-img-wrapper'>
                        <img src='{img_url}' class='card-img' alt='{esc(x.get('案名', ''))}'>
                        <div class='card-badge'>精選物件</div>
                    </div>
                    <div class='card-body'>
                        <div class='card-area'>{esc(x.get('區域', ''))}</div>
                        <h3 class='card-title'>{esc(x.get('案名', ''))}</h3>
                        <div class='card-price'>{esc(price)} <span>萬</span></div>
                    </div>
                </div>
            </a>
            """
        
        # 建立首頁
        home = f"""
        <nav class="navbar">
            <a href="#" class="logo">SK-L REAL ESTATE</a>
            <ul class="nav-links">
                <li><a href="#map">地圖搜尋</a></li>
                <li><a href="#properties">精選物件</a></li>
                <li><a href="#about">關於我們</a></li>
                <li><a href="{AGENT_INFO['line']}">聯絡我們</a></li>
            </ul>
        </nav>
        
        <section class="hero">
            <div class="hero-content">
                <h1>大台中置產專家</h1>
                <p>{AGENT_INFO['name']} · 深耕台中精華區 · 專業誠信服務</p>
            </div>
        </section>
        
        <div class="map-container" id="map-section">
            <div class="filter-bar">
                <div class="filter-group">
                    <label>區域</label>
                    <select id="filter-area">
                        <option value="all">全部區域</option>
                        {area_opts}
                    </select>
                </div>
                <div class="filter-group">
                    <label>類型</label>
                    <select id="filter-type">
                        <option value="all">全部類型</option>
                        {type_opts}
                    </select>
                </div>
                <div class="filter-group">
                    <label>房數</label>
                    <select id="filter-rooms">
                        <option value="all">不限</option>
                        <option value="1">1房</option>
                        <option value="2">2房</option>
                        <option value="3">3房</option>
                        <option value="4">4房以上</option>
                    </select>
                </div>
                <div class="filter-group">
                    <label>價格區間</label>
                    <select id="filter-price">
                        <option value="all">不限</option>
                        <option value="0-1000">1000萬以下</option>
                        <option value="1000-2000">1000-2000萬</option>
                        <option value="2000-3000">2000-3000萬</option>
                        <option value="3000-99999">3000萬以上</option>
                    </select>
                </div>
                <button class="filter-btn" onclick="filterProperties()">🔍 搜尋</button>
            </div>
            <div id="map"></div>
        </div>
        
        <h2 class="section-title" id="properties">精選物件</h2>
        <div class="grid" id="property-grid">
            {cards}
        </div>
        
        <section class="about-section" id="about">
            <img src="{AGENT_INFO['photo']}" class="about-img" alt="{AGENT_INFO['name']}">
            <div class="about-content">
                <h3>{AGENT_INFO['name']}</h3>
                <p>{AGENT_INFO['title']}</p>
                <p style="margin-top:25px;">我們致力於為每一位客戶提供精準的市場分析與專業的置產建議。深耕大台中地區多年，熟悉各區域特色與發展潛力，我們不只是仲介，更是您最值得信賴的置產顧問。無論您是首購族、換屋族或投資客，我們都能為您量身打造最適合的購屋方案。</p>
            </div>
        </section>
        
        <div class="contact-bar">
            <a class="btn-contact btn-line" href="{AGENT_INFO['line']}">💬 LINE 諮詢</a>
            <a class="btn-contact btn-phone" href="tel:{AGENT_INFO['phone']}">📞 {AGENT_INFO['phone']}</a>
        </div>
        """
        
        Path("index.html").write_text(self.build_layout(SITE_TITLE, home, True), encoding="utf-8")
        print(f"✅ 成功生成 {len(self.items)} 個物件頁面")

if __name__ == "__main__":
    try:
        agency = SKL_Agency()
        agency.run()
        print("✅ 網站生成完成！")
    except Exception as e:
        print(f"❌ 錯誤：{e}")
        import traceback
        traceback.print_exc()
