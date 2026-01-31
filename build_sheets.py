import os
import csv
import requests
import html
import shutil
import re
import urllib.parse
import json
import time
from pathlib import Path
from datetime import datetime

# ============================================================
# 1. 個人品牌核心配置 (Core Configuration)
# ============================================================
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQShAl0-TbUU0MQdYVe53im2T6lXQgh_7g-bdL6HHpIBFtA2yfIAMbPw4J9RgZUkROb9AAiMhnRC0kH/pub?output=csv"

# 個人聯絡資訊
MY_PHONE = "0938-615-351"
MY_LINE_URL = "https://line.me/ti/p/FDsMyAYDv"
SITE_TITLE = "SK-L 大台中房地產"
GA4_ID = "G-B7WP9BTP8X"

# Google Maps API 關鍵配置
# 優先使用 GitHub Secret 的變數，保護 API 安全
MAPS_API_KEY = os.getenv("MAPS_API_KEY", "AIzaSyDzgnI2Ucv622CRkWwo2GE5JRrs_Y4HQY0")

# 靜態資源與快取路徑
IMG_BASE = "https://raw.githubusercontent.com/ShihKaiLin/taichung-houses/main/images/"
GEOCACHE_PATH = Path("geocache.json")

# ============================================================
# 2. 品牌質感法律頁尾 (Legal & Branding Footer)
# ============================================================
LEGAL_FOOTER = """
<div class="legal-footer-container">
    <div class="legal-footer-content">
        <strong class="company-name">英柏國際地產有限公司</strong>
        <p class="license-info">
            中市地價二字第 1070029259 號<br>
            王一媖 經紀人 (103) 中市經紀字第 00678 號
        </p>
        <div class="copyright-line">
            <span class="copyright-year">© 2026 SK-L Branding.</span>
            <span class="copyright-reserve">All Rights Reserved.</span>
        </div>
        <p class="branding-slogan">專業誠信 · 卓越服務 · 深耕台中</p>
    </div>
</div>

<style>
    .legal-footer-container {
        margin: 120px 0 40px;
        padding: 60px 25px;
        text-align: center;
        border-top: 1px solid #edf2f7;
        background-color: #fafafa;
        border-radius: 50px 50px 0 0;
    }
    .company-name {
        color: #2d3748;
        font-size: 15px;
        display: block;
        margin-bottom: 12px;
        letter-spacing: 1px;
    }
    .license-info {
        font-size: 12px;
        color: #718096;
        line-height: 2;
        margin: 0;
    }
    .copyright-line {
        margin-top: 25px;
        font-size: 11px;
        color: #a0aec0;
        letter-spacing: 0.5px;
    }
    .branding-slogan {
        margin-top: 10px;
        font-size: 11px;
        color: #cbd5e0;
        font-weight: 300;
    }
</style>
"""

# ============================================================
# 3. 基礎函數 (Helper Functions)
# ============================================================
def esc(s):
    """ 防止 HTML 注入與字元破壞 """
    return html.escape(str(s or "").strip())

# ============================================================
# 4. 頁面頭部生成 (Header Generation)
# ============================================================
def get_head(title, desc="", img="", is_home=False, map_data_json="[]"):
    """ 
    生成完整的 Head 區塊 
    包含：極致 SEO、社群 OG 標籤、品牌樣式、地圖邏輯 
    """
    seo_desc = esc(desc)[:80] if desc else f"{SITE_TITLE} - 精選台中優質房產，林世塏為您提供最專業的不動產服務。"
    seo_img = img if img.startswith("http") else f"{IMG_BASE}hero_bg.jpg"
    
    # 追蹤腳本
    ga_script = ""
    if GA4_ID:
        ga_script = f"""
        <script async src="https://www.googletagmanager.com/gtag/js?id={GA4_ID}"></script>
        <script>
            window.dataLayer = window.dataLayer || [];
            function gtag(){{dataLayer.push(arguments);}}
            gtag('js', new Date());
            gtag('config', '{GA4_ID}');
        </script>
        """

    # 地圖互動核心腳本
    map_script = ""
    if is_home:
        map_script = f"""
        <script src="https://maps.googleapis.com/maps/api/js?key={MAPS_API_KEY}"></script>
        <script>
            let map, infoWindow;
            const geocoder = new google.maps.Geocoder();
            
            function initMap() {{
                const bounds = new google.maps.LatLngBounds();
                
                // 初始化地圖：恢復原始圖資，確保路名標籤清晰
                const mapOptions = {{
                    center: {{ lat: 24.162, lng: 120.647 }},
                    zoom: 12,
                    disableDefaultUI: true,
                    zoomControl: true,
                    gestureHandling: 'greedy',
                    clickableIcons: false
                }};
                
                map = new google.maps.Map(document.getElementById("map"), mapOptions);
                infoWindow = new google.maps.InfoWindow();
                
                const locations = {map_data_json};
                
                locations.forEach(loc => {{
                    // 前端 Geocoding 雙備援邏輯
                    if (loc.lat && loc.lng) {{
                        createMarker(loc, bounds);
                    } else if (loc.address) {{
                        geocoder.geocode({{ 'address': loc.address }}, (results, status) => {{
                            if (status === 'OK') {{
                                loc.lat = results[0].geometry.location.lat();
                                loc.lng = results[0].geometry.location.lng();
                                createMarker(loc, bounds);
                            }}
                        }});
                    }}
                }});
            }}

            function createMarker(loc, bounds) {{
                const position = {{
                    lat: parseFloat(loc.lat), 
                    lng: parseFloat(loc.lng)
                }};
                
                const marker = new google.maps.Marker({{
                    position: position,
                    map: map,
                    title: loc.name,
                    optimized: false,
                    animation: google.maps.Animation.DROP
                }});
                
                bounds.extend(position);
                map.fitBounds(bounds);

                // 地圖預覽視窗互動
                marker.addListener("click", () => {{
                    const previewContent = `
                        <div class="map-preview-card">
                            <div class="map-preview-img" style="background-image: url('${{loc.img}}');"></div>
                            <div class="map-preview-body">
                                <h4 class="map-preview-title">${{loc.name}}</h4>
                                <div class="map-preview-price">${{loc.price}}</div>
                                <a href="${{loc.url}}" class="map-preview-btn">查看詳情建議</a>
                            </div>
                        </div>
                        <style>
                            .map-preview-card { padding: 10px; width: 220px; font-family: sans-serif; }
                            .map-preview-img { width: 100%; height: 130px; border-radius: 12px; background-size: cover; background-position: center; margin-bottom: 12px; }
                            .map-preview-title { margin: 0 0 5px 0; font-size: 16px; color: #1A365D; font-weight: 800; line-height: 1.4; }
                            .map-preview-price { color: #C5A059; font-weight: 900; font-size: 19px; margin-bottom: 12px; }
                            .map-preview-btn { display: block; text-align: center; background: #1A365D; color: #fff; text-decoration: none; padding: 12px; border-radius: 10px; font-size: 13px; font-weight: bold; }
                        </style>
                    `;
                    infoWindow.setContent(previewContent);
                    infoWindow.open(map, marker);
                }});
            }}

            function filterAndSort() {{
                const activeReg = document.querySelector('.tag.f-reg.active').dataset.val;
                const activeType = document.querySelector('.tag.f-type.active').dataset.val;
                const activeSort = document.querySelector('.tag.f-sort.active').dataset.val;
                
                let cards = Array.from(document.querySelectorAll('.property-card'));
                
                cards.forEach(card => {{
                    const matchReg = (activeReg === 'all' || card.dataset.region === activeReg);
                    const matchType = (activeType === 'all' || card.dataset.type === activeType);
                    card.style.display = (matchReg && matchType) ? 'block' : 'none';
                }});
                
                if (activeSort !== 'none') {{
                    cards.sort((a, b) => {{
                        const valA = parseFloat(a.dataset.price.replace(/[^0-9.]/g, '')) || 0;
                        const valB = parseFloat(b.dataset.price.replace(/[^0-9.]/g, '')) || 0;
                        return activeSort === 'high' ? valB - valA : valA - valB;
                    }});
                    const listContainer = document.getElementById('list');
                    cards.forEach(card => listContainer.appendChild(card));
                }}
            }}

            function setTag(button, cssClass) {{
                const parent = button.parentElement;
                parent.querySelectorAll('.' + cssClass).forEach(btn => btn.classList.remove('active'));
                button.classList.add('active');
                filterAndSort();
            }}
            
            window.onload = initMap;
        </script>
        """

    return f"""
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=0">
        
        <title>{esc(title)}</title>
        <meta name="description" content="{seo_desc}">
        
        <meta property="og:title" content="{esc(title)}">
        <meta property="og:description" content="{seo_desc}">
        <meta property="og:image" content="{seo_img}">
        <meta property="og:type" content="website">
        <meta property="og:site_name" content="{SITE_TITLE}">
        
        {ga_script}
        {map_script}
        
        <style>
            :root {{ 
                --sk-navy: #1A365D; 
                --sk-gold: #C5A059; 
                --sk-light: #F8FAFC; 
                --sk-white: #FFFFFF;
                --sk-text-main: #2D3748;
                --sk-text-muted: #94A3B8;
            }}

            body {{ 
                font-family: 'PingFang TC', 'Microsoft JhengHei', 'Heiti TC', sans-serif; 
                background-color: #f7fafc; 
                margin: 0; 
                color: var(--sk-text-main); 
                -webkit-font-smoothing: antialiased; 
            }}

            .container {{ 
                max-width: 500px; 
                margin: 0 auto; 
                background-color: var(--sk-white); 
                min-height: 100vh; 
                position: relative; 
                box-shadow: 0 0 60px rgba(0,0,0,0.12); 
            }}
            
            /* --- Hero 區塊樣式 --- */
            .hero-banner {{ 
                height: 380px; 
                background: url('{IMG_BASE}hero_bg.jpg') center/cover; 
                display: flex; 
                align-items: center; 
                justify-content: center; 
                color: var(--sk-white); 
                position: relative; 
            }}
            .hero-banner::after {{ 
                content: ''; 
                position: absolute; 
                top: 0; 
                left: 0; 
                width: 100%; 
                height: 100%; 
                background: rgba(0,0,0,0.38); 
            }}
            .hero-content {{ 
                position: relative; 
                z-index: 2; 
                text-align: center; 
            }}
            .hero-title {{ 
                font-size: 40px; 
                margin: 0; 
                letter-spacing: 8px; 
                font-weight: 900; 
                text-shadow: 0 4px 20px rgba(0,0,0,0.5);
            }}
            .hero-subtitle {{ 
                font-size: 15px; 
                opacity: 0.9; 
                margin-top: 18px; 
                letter-spacing: 5px; 
                text-transform: uppercase;
                font-weight: 300;
            }}

            /* --- 地圖容器樣式 --- */
            .map-wrapper {{ 
                margin: -60px 20px 0; 
                position: relative; 
                z-index: 10; 
            }}
            #map {{ 
                height: 340px; 
                border-radius: 35px; 
                box-shadow: 0 30px 60px rgba(0,0,0,0.2); 
                border: 8px solid var(--sk-white); 
            }}

            /* --- 篩選器樣式 --- */
            .filter-container {{ padding: 55px 20px 10px; }}
            .filter-row {{ 
                display: flex; 
                gap: 12px; 
                overflow-x: auto; 
                padding-bottom: 15px; 
                scrollbar-width: none; 
            }}
            .filter-row::-webkit-scrollbar {{ display: none; }}
            
            .tag {{ 
                padding: 14px 26px; 
                border-radius: 60px; 
                background: #f1f5f9; 
                font-size: 14px; 
                color: #64748b; 
                cursor: pointer; 
                white-space: nowrap; 
                border: none; 
                font-weight: 600; 
                transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275); 
            }}
            .tag.active {{ 
                background: var(--sk-navy); 
                color: var(--sk-white); 
                box-shadow: 0 8px 20px rgba(26, 54, 93, 0.35); 
                transform: translateY(-3px);
            }}

            /* --- 物件卡片樣式 --- */
            .property-card {{ 
                margin: 40px 20px; 
                border-radius: 40px; 
                overflow: hidden; 
                background: var(--sk-white); 
                box-shadow: 0 20px 50px rgba(0,0,0,0.08); 
                border: 1px solid #f1f5f9; 
                transition: transform 0.3s ease;
            }}
            .card-image-box {{ width: 100%; height: 340px; overflow: hidden; }}
            .card-image {{ width: 100%; height: 100%; object-fit: cover; transition: transform 0.6s ease; }}
            .property-card:hover .card-image {{ transform: scale(1.08); }}
            
            .card-body {{ padding: 30px; }}
            .card-title {{ font-size: 22px; margin: 0 0 12px 0; font-weight: 800; color: var(--sk-navy); }}
            .card-price {{ font-size: 30px; color: var(--sk-gold); font-weight: 900; letter-spacing: -1px; }}
            .card-meta {{ font-size: 14px; color: var(--sk-text-muted); margin-top: 15px; font-weight: 500; }}
            
            .card-btn {{ 
                display: block; 
                text-align: center; 
                margin-top: 25px; 
                padding: 20px; 
                background: #f8fafc; 
                color: var(--sk-navy); 
                text-decoration: none; 
                font-size: 15px; 
                font-weight: 800; 
                border-radius: 22px; 
                transition: 0.3s;
            }}
            .card-btn:hover {{ background: #edf2f7; }}

            /* --- 底部導航條 --- */
            .action-bar {{ 
                position: fixed; 
                bottom: 0; 
                left: 50%; 
                transform: translateX(-50%); 
                width: 100%; 
                max-width: 500px; 
                padding: 25px 25px 50px; 
                display: flex; 
                gap: 18px; 
                background: rgba(255,255,255,0.95); 
                backdrop-filter: blur(20px); 
                border-top: 1px solid #f1f1f1; 
                z-index: 999; 
            }}
            .btn-nav {{ 
                flex: 1; 
                text-align: center; 
                padding: 22px; 
                border-radius: 24px; 
                text-decoration: none; 
                font-weight: 800; 
                color: var(--sk-white); 
                font-size: 17px; 
                box-shadow: 0 10px 20px rgba(0,0,0,0.1);
            }}
            .btn-call {{ background: #1A202C; }}
            .btn-line {{ background: #00B900; }}

            /* --- 物件內頁專用 --- */
            .back-navigation {{ 
                position: absolute; 
                top: 40px; 
                left: 30px; 
                background: var(--sk-white); 
                padding: 14px 26px; 
                border-radius: 22px; 
                text-decoration: none; 
                font-weight: 800; 
                color: var(--sk-navy); 
                z-index: 100; 
                box-shadow: 0 15px 35px rgba(0,0,0,0.18); 
            }}
            .detail-image-box {{ width: 100%; height: 550px; object-fit: cover; display: block; }}
            .detail-info-card {{ 
                padding: 65px 35px; 
                background: var(--sk-white); 
                border-radius: 60px 60px 0 0; 
                margin-top: -85px; 
                position: relative; 
                z-index: 10; 
            }}
            .detail-title {{ font-size: 36px; font-weight: 900; color: var(--sk-navy); margin: 0; line-height: 1.3; }}
            .detail-price {{ font-size: 34px; color: var(--sk-gold); font-weight: 900; margin-top: 20px; }}
            .detail-desc {{ line-height: 2.5; color: #4a5568; margin: 45px 0; font-size: 17.5px; letter-spacing: 1px; }}
            
            .expert-advice-box {{ 
                background: #f0f8ff; 
                padding: 35px; 
                border-radius: 35px; 
                margin-bottom: 50px; 
                border-left: 10px solid var(--sk-gold); 
                line-height: 2.1; 
                font-size: 16px;
            }}
            .external-link-btn {{ 
                display: block; 
                text-align: center; 
                padding: 24px; 
                background: #fff; 
                color: var(--sk-navy); 
                text-decoration: none; 
                border-radius: 24px; 
                margin-top: 35px; 
                font-weight: 800; 
                border: 2px solid #edf2f7; 
            }}
            .google-maps-btn {{ 
                display: block; 
                text-align: center; 
                padding: 24px; 
                background: var(--sk-navy); 
                color: var(--sk-white); 
                text-decoration: none; 
                border-radius: 24px; 
                margin-top: 20px; 
                font-weight: 800; 
                box-shadow: 0 15px 35px rgba(26, 54, 93, 0.25); 
            }}
        </style>
    </head>
    """

# ============================================================
# 5. 主建置邏輯 (Main Build Logic)
# ============================================================
def build():
    out = Path(".")
    
    # 執行前的檔案清理，確保無殘留
    print("--- 正在清理舊有的物件目錄 ---")
    for p in out.glob("p*"):
        if p.is_dir() and re.match(r'^p\d+$', p.name):
            shutil.rmtree(p)
    
    # 座標快取安全讀取
    cache = {}
    if GEOCACHE_PATH.exists():
        try:
            with open(GEOCACHE_PATH, 'r', encoding='utf-8') as f:
                cache = json.load(f)
            print(f"--- 成功載入快取資料，共計 {len(cache)} 筆座標 ---")
        except Exception as e:
            print(f"--- 快取載入失敗: {e} ---")
            cache = {}

    # 抓取 Google 試算表
    print(f"--- 正在連線至 Google Sheets 下載資料 ---")
    try:
        res = requests.get(SHEET_CSV_URL, timeout=20)
        res.raise_for_status()
        res.encoding = 'utf-8-sig'
        reader = csv.DictReader(res.text.splitlines())
    except Exception as e:
        print(f"--- 試算表下載失敗: {e} ---")
        return

    items_html_list = []
    map_data_list = []
    regions_set = set()
    types_set = set()
    
    # 資料處理迴圈
    for i, row in enumerate(reader):
        # 清理欄位內容
        d = {str(k).strip(): str(v).strip() for k, v in row.items() if k}
        
        # 基本欄位判定
        name = d.get("案名") or next((v for k,v in d.items() if "案名" in k), "")
        if not name or d.get("狀態", "").upper() in ["OFF", "FALSE"]:
            continue
            
        # 尋找原始外部連結 (591 / 樂屋)
        ext_link = ""
        for val in d.values():
            if str(val).startswith("http") and not any(x in str(val).lower() for x in ['.jpg','.png','.jpeg','.webp']):
                ext_link = val
                break
        
        reg = d.get("區域", "台中")
        price_str = d.get("價格", "面議")
        use_type = d.get("用途", "住宅")
        address = d.get("地址", "")
        
        regions_set.add(reg)
        types_set.add(use_type)
        
        # 圖片處理邏輯
        img_url = d.get("圖片網址") or next((v for k,v in d.items() if "圖片" in k), "")
        if img_url and not img_url.startswith("http"):
            img_url = f"{IMG_BASE}{img_url.lstrip('/')}"
        if not img_url:
            img_url = "https://placehold.co/800x600?text=SK-L+Premium+Property"
        
        # 產生唯一 Slug 並建立目錄
        slug = f"p{i}"
        (out / slug).mkdir(exist_ok=True)
        
        # 判定座標搜索地址
        search_target = address if address else f"台中市{name}"
        lat = cache.get(search_target, {}).get("lat")
        lng = cache.get(search_target, {}).get("lng")
        
        # 建立導向路徑
        internal_target_url = f"./{slug}/"
        
        # 封裝地圖數據
        map_data_list.append({
            "name": name, 
            "address": search_target,
            "url": internal_target_url, 
            "lat": lat, 
            "lng": lng, 
            "img": img_url, 
            "price": price_str
        })

        # --- 生成子網頁詳情頁面 ---
        ext_btn_snippet = f'<a href="{ext_link}" target="_blank" class="external-link-btn">🌐 前往 591 / 樂屋網 查看原始連結</a>' if ext_link else ""
        
        detail_html_body = f"""
        <div class="container">
            <a href="../" class="back-navigation">← 返回列表</a>
            <img src="{img_url}" class="detail-image-box">
            
            <div class="detail-info-card">
                <h1 class="detail-title">{esc(name)}</h1>
                <div class="detail-price">{esc(price_str)}</div>
                
                <div class="detail-desc">
                    {esc(d.get("描述","")).replace('、','<br>• ')}
                </div>
                
                <div class="expert-advice-box">
                    <strong style="color:var(--sk-navy); font-size:20px; display:block; margin-bottom:12px;">💡 SK-L 顧問專業點評</strong>
                    此物件位於大台中精華區位，生活機能與未來的增值潛力兼具。如果您想了解本社區最近一年的實價登錄行情，或需要專業評估銀行貸款成數，歡迎直接點擊下方 LINE 按鈕與我聯繫。
                </div>
                
                {ext_btn_snippet}
                
                <a href="https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(search_target)}" 
                   target="_blank" class="google-maps-btn">
                   📍 在 Google 地圖中查看位置
                </a>
                
                {LEGAL_FOOTER}
            </div>
            
            <div class="action-bar">
                <a href="tel:{MY_PHONE}" class="btn-nav btn-call">致電 SK-L</a>
                <a href="{MY_LINE_URL}" class="btn-nav btn-line">LINE 諮詢</a>
            </div>
        </div>
        """
        
        (out / slug / "index.html").write_text(
            f"<!doctype html><html lang='zh-TW'>{get_head(name + ' | 大台中房產推薦', d.get('描述',''), img_url)}<body>{detail_html_body}</body></html>", 
            encoding="utf-8"
        )
        
        # --- 生成首頁物件卡片清單 ---
        items_html_list.append(f'''
            <div class="property-card" data-region="{esc(reg)}" data-type="{esc(use_type)}" data-price="{esc(price_str)}">
                <a href="{internal_target_url}" class="card-image-box">
                    <img src="{img_url}" class="card-image" loading="lazy">
                </a>
                <div class="card-body">
                    <h4 class="card-title">{esc(name)}</h4>
                    <div class="card-price">{esc(price_str)}</div>
                    <div class="card-meta">
                        <span class="meta-reg">{esc(reg)}</span> • 
                        <span class="meta-type">{esc(use_type)}</span>
                    </div>
                    <a href="{internal_target_url}" class="card-btn">查看詳細顧問建議</a>
                </div>
            </div>
        ''')

    # 保存座標快取，保護下一次 Build 的效能
    with open(GEOCACHE_PATH, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=4)

    # 渲染篩選按鈕組
    reg_btns_html = "".join([
        f'<button class="tag f-reg" data-val="{esc(r)}" onclick="setTag(this, \'f-reg\')">{esc(r)}</button>' 
        for r in sorted(regions_set)
    ])
    type_btns_html = "".join([
        f'<button class="tag f-type" data-val="{esc(t)}" onclick="setTag(this, \'f-type\')">{esc(t)}</button>' 
        for t in sorted(types_set)
    ])

    # --- 生成首頁 HTML ---
    home_html_body = f"""
    <div class="container">
        <div class="hero-banner">
            <div class="hero-content">
                <h2 class="hero-title">{esc(SITE_TITLE)}</h2>
                <p class="hero-subtitle">Premium Real Estate • Professional Analysis</p>
            </div>
        </div>
        
        <div class="map-wrapper">
            <div id="map"></div>
        </div>
        
        <div class="filter-container">
            <div class="filter-row">
                <button class="tag f-reg active" data-val="all" onclick="setTag(this, 'f-reg')">全部地區</button>
                {reg_btns_html}
            </div>
            
            <div class="filter-row" style="margin-top:20px;">
                <button class="tag f-type active" data-val="all" onclick="setTag(this, 'f-type')">所有用途</button>
                {type_btns_html}
            </div>
            
            <div class="filter-row" style="margin-top:20px; border-top:1px solid #f1f5f9; padding-top:25px;">
                <button class="tag f-sort active" data-val="none" onclick="setTag(this, 'f-sort')">默認排序</button>
                <button class="tag f-sort" data-val="high" onclick="setTag(this, 'f-sort')">價格：由高到低</button>
                <button class="tag f-sort" data-val="low" onclick="setTag(this, 'f-sort')">價格：由低到高</button>
            </div>
        </div>
        
        <div id="list">
            {''.join(items_html_list)}
        </div>
        
        {LEGAL_FOOTER}
        
        <div class="action-bar">
            <a href="tel:{MY_PHONE}" class="btn-nav btn-call">致電 SK-L</a>
            <a href="{MY_LINE_URL}" class="btn-nav btn-line">LINE 諮詢</a>
        </div>
    </div>
    """
    
    (out / "index.html").write_text(
        f"<!doctype html><html lang='zh-TW'>{get_head(SITE_TITLE, is_home=True, map_data_json=json.dumps(map_data_list, ensure_ascii=False))}<body>{home_html_body}</body></html>", 
        encoding="utf-8"
    )
    print(f"--- 建置完成！共生成 {len(items_html_list)} 個物件頁面 ---")

if __name__ == "__main__":
    build()
