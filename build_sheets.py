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

# ==========================================
# 1. 個人品牌與環境配置區
# ==========================================
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQShAl0-TbUU0MQdYVe53im2T6lXQgh_7g-bdL6HHpIBFtA2yfIAMbPw4J9RgZUkROb9AAiMhnRC0kH/pub?output=csv"
MY_PHONE = "0938-615-351"
MY_LINE_URL = "https://line.me/ti/p/FDsMyAYDv"
SITE_TITLE = "SK-L 大台中房地產"
GA4_ID = "G-B7WP9BTP8X"

# Google Maps API Key：若環境變數未設定則使用預設
MAPS_API_KEY = os.getenv("MAPS_API_KEY", "AIzaSyDzgnI2Ucv622CRkWwo2GE5JRrs_Y4HQY0")

# 圖片與路徑
IMG_BASE = "https://raw.githubusercontent.com/ShihKaiLin/taichung-houses/main/images/"
GEOCACHE_PATH = Path("geocache.json")

# ==========================================
# 2. 品牌質感法律頁尾
# ==========================================
LEGAL_FOOTER = """
<div style="margin: 120px 0 40px; padding: 45px 25px; text-align: center; border-top: 1px solid #edf2f7; background-color: #fafafa; border-radius: 40px 40px 0 0;">
    <div style="font-size: 11px; color: #718096; line-height: 2.2; letter-spacing: 1.2px;">
        <strong style="color: #2d3748; font-size: 14px; display: block; margin-bottom: 10px;">英柏國際地產有限公司</strong>
        中市地價二字第 1070029259 號<br>
        王一媖 經紀人 (103) 中市經紀字第 00678 號<br>
        <span style="opacity: 0.7; margin-top: 20px; display: block; font-size: 10px;">
            © 2026 SK-L Branding. All Rights Reserved. <br>
            專業誠信 · 卓越服務 · 台中房地產專家
        </span>
    </div>
</div>
"""

def esc(s):
    """防止 HTML 注入與破版"""
    return html.escape(str(s or "").strip())

def get_head(title, desc="", img="", is_home=False, map_data_json="[]"):
    """生成完整的 Head 區塊，包含 SEO、CSS 與地圖互動邏輯"""
    seo_desc = esc(desc)[:80] if desc else f"{SITE_TITLE} - 精選台中優質房產，林世塏專業服務。"
    seo_img = img if img.startswith("http") else f"{IMG_BASE}hero_bg.jpg"
    
    # 流量追蹤腳本
    ga_script = f"""
    <script async src="https://www.googletagmanager.com/gtag/js?id={GA4_ID}"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){{dataLayer.push(arguments);}}
      gtag('js', new Date());
      gtag('config', '{GA4_ID}');
    </script>""" if GA4_ID else ""

    map_script = ""
    if is_home:
        map_script = f"""
        <script src="https://maps.googleapis.com/maps/api/js?key={MAPS_API_KEY}"></script>
        <script>
            let map, infoWindow;
            const geocoder = new google.maps.Geocoder();
            
            function initMap() {{
                const bounds = new google.maps.LatLngBounds();
                map = new google.maps.Map(document.getElementById("map"), {{
                    center: {{ lat: 24.162, lng: 120.647 }},
                    zoom: 12,
                    disableDefaultUI: true,
                    zoomControl: true,
                    styles: [
                        {{"featureType":"poi","stylers":[{{"visibility":"off"}}]}},
                        {{"featureType":"transit","stylers":[{{"visibility":"off"}}]}},
                        {{"elementType":"geometry","stylers":[{{"color":"#f5f5f5"}}]}}
                    ]
                }});
                
                infoWindow = new google.maps.InfoWindow();
                const locations = {map_data_json};
                
                locations.forEach(loc => {{
                    // 地圖復活邏輯：前端備援補抓座標
                    if (loc.lat && loc.lng) {{
                        createMarker(loc, bounds);
                    }} else if (loc.address) {{
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
                const pos = {{lat: parseFloat(loc.lat), lng: parseFloat(loc.lng)}};
                const marker = new google.maps.Marker({{
                    position: pos,
                    map: map,
                    title: loc.name,
                    optimized: false,
                    animation: google.maps.Animation.DROP
                }});
                bounds.extend(pos);
                map.fitBounds(bounds);

                marker.addListener("click", () => {{
                    const content = `
                        <div style="padding:15px; font-family:'PingFang TC', sans-serif; width:220px;">
                            <div style="background-image:url('${{loc.img}}'); background-size:cover; background-position:center; height:130px; border-radius:15px; margin-bottom:12px; box-shadow:0 4px 10px rgba(0,0,0,0.1);"></div>
                            <h4 style="margin:0 0 6px 0; font-size:17px; color:#1A365D; font-weight:800; line-height:1.4;">${{loc.name}}</h4>
                            <div style="color:#C5A059; font-weight:900; font-size:19px; margin-bottom:15px;">${{loc.price}}</div>
                            <a href="${{loc.url}}" style="display:block; text-align:center; background:#1A365D; color:#fff; text-decoration:none; padding:12px; border-radius:12px; font-size:14px; font-weight:bold; transition:0.3s;">查看 SK-L 專業建議</a>
                        </div>`;
                    infoWindow.setContent(content);
                    infoWindow.open(map, marker);
                }});
            }}

            function filterAndSort() {{
                const reg = document.querySelector('.tag.f-reg.active').dataset.val;
                const type = document.querySelector('.tag.f-type.active').dataset.val;
                const sort = document.querySelector('.tag.f-sort.active').dataset.val;
                let cards = Array.from(document.querySelectorAll('.property-card'));
                
                cards.forEach(c => {{
                    const mR = (reg === 'all' || c.dataset.region === reg);
                    const mT = (type === 'all' || c.dataset.type === type);
                    c.style.display = (mR && mT) ? 'block' : 'none';
                }});
                
                if(sort !== 'none') {{
                    cards.sort((a,b) => {{
                        const pA = parseFloat(a.dataset.price.replace(/[^0-9.]/g, '')) || 0;
                        const pB = parseFloat(b.dataset.price.replace(/[^0-9.]/g, '')) || 0;
                        return sort === 'high' ? pB - pA : pA - pB;
                    }});
                    const list = document.getElementById('list');
                    cards.forEach(c => list.appendChild(c));
                }}
            }}

            function setTag(btn, cls) {{
                btn.parentElement.querySelectorAll('.'+cls).forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                filterAndSort();
            }}
            window.onload = initMap;
        </script>"""

    return f"""
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=0">
        <title>{esc(title)}</title>
        <meta name="description" content="{seo_desc}">
        <meta property="og:title" content="{esc(title)}">
        <meta property="og:description" content="{seo_desc}">
        <meta property="og:image" content="{seo_img}">
        <meta property="og:type" content="website">
        {ga_script}
        {map_script}
        <style>
            :root {{ 
                --sk-navy: #1A365D; 
                --sk-gold: #C5A059; 
                --sk-light: #F8FAFC; 
                --sk-white: #FFFFFF;
                --sk-text: #2D3748;
                --sk-gray: #94A3B8;
            }}
            body {{ 
                font-family: 'PingFang TC', 'Microsoft JhengHei', sans-serif; 
                background-color: var(--sk-white); 
                margin: 0; 
                color: var(--sk-text); 
                -webkit-font-smoothing: antialiased; 
            }}
            .container {{ 
                max-width: 500px; 
                margin: 0 auto; 
                background-color: var(--sk-white); 
                min-height: 100vh; 
                position: relative; 
                box-shadow: 0 0 60px rgba(0,0,0,0.1); 
            }}
            
            /* Hero Banner */
            .hero {{ 
                height: 350px; 
                background: url('{IMG_BASE}hero_bg.jpg') center/cover; 
                display: flex; 
                align-items: center; 
                justify-content: center; 
                color: var(--sk-white); 
                position: relative; 
            }}
            .hero::after {{ 
                content:''; 
                position:absolute; 
                top:0; left:0; width:100%; height:100%; 
                background:rgba(0,0,0,0.35); 
            }}
            .hero-content {{ 
                position: relative; 
                z-index: 2; 
                text-align: center; 
            }}
            .hero-content h2 {{ 
                font-size: 38px; 
                margin: 0; 
                letter-spacing: 7px; 
                font-weight: 900; 
                text-shadow: 0 4px 15px rgba(0,0,0,0.4);
            }}
            .hero-content p {{ 
                font-size: 14px; 
                opacity: 0.9; 
                margin-top: 15px; 
                letter-spacing: 4px; 
                text-transform: uppercase;
                font-weight: 300;
            }}

            /* 地圖與打點區塊 */
            .map-box {{ 
                margin: -55px 20px 0; 
                position: relative; 
                z-index: 10; 
            }}
            #map {{ 
                height: 320px; 
                border-radius: 32px; 
                box-shadow: 0 25px 55px rgba(0,0,0,0.18); 
                border: 6px solid var(--sk-white); 
            }}

            /* 篩選與排序標籤 */
            .filter-section {{ padding: 50px 20px 10px; }}
            .filter-group {{ 
                display: flex; 
                gap: 12px; 
                overflow-x: auto; 
                padding-bottom: 15px; 
                -ms-overflow-style: none; 
                scrollbar-width: none; 
            }}
            .filter-group::-webkit-scrollbar {{ display: none; }}
            
            .tag {{ 
                padding: 12px 24px; 
                border-radius: 50px; 
                background: var(--sk-light); 
                font-size: 13px; 
                color: var(--sk-gray); 
                cursor: pointer; 
                white-space: nowrap; 
                border:none; 
                font-weight: 600; 
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); 
            }}
            .tag.active {{ 
                background: var(--sk-navy); 
                color: var(--sk-white); 
                box-shadow: 0 6px 18px rgba(26, 54, 93, 0.3); 
                transform: translateY(-2px);
            }}

            /* 物件展示卡片 */
            .property-card {{ 
                margin: 35px 20px; 
                border-radius: 35px; 
                overflow: hidden; 
                background: var(--sk-white); 
                box-shadow: 0 15px 45px rgba(0,0,0,0.07); 
                border: 1px solid #f1f5f9; 
                transition: transform 0.3s ease;
            }}
            .card-info {{ padding: 28px; }}
            .price {{ 
                font-size: 28px; 
                color: var(--sk-gold); 
                font-weight: 900; 
                letter-spacing: -1px; 
            }}
            
            /* 固定底部導覽 */
            .action-bar {{ 
                position: fixed; 
                bottom: 0; 
                left: 50%; 
                transform: translateX(-50%); 
                width: 100%; 
                max-width: 500px; 
                padding: 22px 25px 45px; 
                display: flex; 
                gap: 15px; 
                background: rgba(255,255,255,0.92); 
                backdrop-filter: blur(25px); 
                border-top: 1px solid #f1f1f1; 
                z-index: 999; 
            }}
            .btn {{ 
                flex: 1; 
                text-align: center; 
                padding: 20px; 
                border-radius: 22px; 
                text-decoration: none; 
                font-weight: 800; 
                color: var(--sk-white); 
                font-size: 16px; 
                transition: all 0.2s ease;
            }}
            .btn:active {{ transform: scale(0.96); }}
            .btn-call {{ background: #1A202C; }}
            .btn-line {{ background: #00B900; }}
            
            /* 子網頁專用細節 */
            .back-btn {{ 
                position: absolute; 
                top: 35px; 
                left: 25px; 
                background: var(--sk-white); 
                padding: 12px 24px; 
                border-radius: 20px; 
                text-decoration: none; 
                font-weight: 800; 
                color: var(--sk-navy); 
                z-index: 100; 
                box-shadow: 0 12px 30px rgba(0,0,0,0.15); 
            }}
            .btn-ext-link {{ 
                display: block; 
                text-align: center; 
                padding: 22px; 
                background: #fff; 
                color: var(--sk-navy); 
                text-decoration: none; 
                border-radius: 22px; 
                margin-top: 30px; 
                font-weight: 700; 
                border: 2.5px solid #edf2f7; 
            }}
            .advice-box {{ 
                background: #f0f8ff; 
                padding: 28px; 
                border-radius: 28px; 
                margin-bottom: 40px; 
                border-left: 8px solid var(--sk-gold); 
                line-height: 2; 
            }}
        </style>
    </head>
    """

def build():
    out = Path(".")
    # 執行前的目錄清理
    for p in out.glob("p*"):
        if p.is_dir() and re.match(r'^p\d+$', p.name):
            shutil.rmtree(p)
    
    # 讀取快取座標 (如有)
    cache = {}
    if GEOCACHE_PATH.exists():
        try:
            with open(GEOCACHE_PATH, 'r', encoding='utf-8') as f:
                cache = json.load(f)
        except:
            cache = {}

    # 下載數據源
    res = requests.get(SHEET_CSV_URL, timeout=15)
    res.encoding = 'utf-8-sig'
    reader = csv.DictReader(res.text.splitlines())
    
    items, map_data, regions, types = [], [], set(), set()
    num_re = re.compile(r'[^\d.]')
    
    for i, row in enumerate(reader):
        d = {str(k).strip(): str(v).strip() for k, v in row.items() if k}
        
        # 案名與狀態判定
        name = d.get("案名") or next((v for k,v in d.items() if "案名" in k), "")
        if not name or d.get("狀態", "").upper() in ["OFF", "FALSE"]:
            continue
            
        # 外部連結偵測
        ext_link = ""
        for val in d.values():
            if str(val).startswith("http") and not any(x in str(val).lower() for x in ['.jpg','.png','.jpeg','.webp']):
                ext_link = val
                break
        
        reg, p_str, use_type, addr = d.get("區域","台中"), d.get("價格","面議"), d.get("用途","住宅"), d.get("地址", "")
        regions.add(reg)
        types.add(use_type)
        
        # 圖片網址處理
        img = d.get("圖片網址") or next((v for k,v in d.items() if "圖片" in k), "")
        if img and not img.startswith("http"):
            img = f"{IMG_BASE}{img.lstrip('/')}"
        if not img:
            img = "https://placehold.co/800x600?text=SK-L+Premium+Property"
        
        # 子資料夾生成
        slug = f"p{i}"
        (out/slug).mkdir(exist_ok=True)
        search_addr = addr if addr else f"台中市{name}"
        
        # 快取座標
        lat, lng = cache.get(search_addr, {}).get("lat"), cache.get(search_addr, {}).get("lng")
        
        # 內部導向路徑
        internal_url = f"./{slug}/"
        map_data.append({
            "name": name, 
            "address": search_addr,
            "url": internal_url, 
            "lat": lat, 
            "lng": lng, 
            "img": img, 
            "price": p_str
        })

        # --- 生成子網頁詳情 ---
        ext_btn_html = f'<a href="{ext_link}" target="_blank" class="btn-ext-link">🌐 查看 591 / 樂屋網 原始連結</a>' if ext_link else ""
        detail_html = f"""
        <div class="container">
            <a href="../" class="back-btn">← 返回列表</a>
            <img src="{img}" style="width:100%; height:520px; object-fit:cover; display:block;">
            <div style="padding:60px 30px; background:#fff; border-radius:55px 55px 0 0; margin-top:-75px; position:relative; z-index:10;">
                <h1 style="font-size:34px; font-weight:900; color:var(--sk-navy); margin:0; line-height:1.4;">{esc(name)}</h1>
                <div class="price" style="margin-top:20px;">{esc(p_str)}</div>
                
                <div style="line-height:2.4; color:#4a5568; margin:45px 0; font-size:17px; letter-spacing:0.8px;">
                    {esc(d.get("描述","")).replace('、','<br>• ')}
                </div>
                
                <div class="advice-box">
                    <strong style="color:var(--sk-navy); font-size:20px; display:block; margin-bottom:12px;">💡 SK-L 顧問專業點評</strong>
                    此物件位於大台中精華區位，生活機能與保值性兼具。如果您想了解本社區最近一年的實價登錄行情，或需要評估銀行貸款成數，歡迎直接點擊下方 LINE 按鈕與我聯繫。
                </div>
                
                {ext_btn_html}
                <a href="https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(search_addr)}" target="_blank" style="display:block; text-align:center; padding:22px; background:var(--sk-navy); color:#fff; text-decoration:none; border-radius:22px; margin-top:15px; font-weight:700; box-shadow:0 15px 30px rgba(26,54,93,0.22);">📍 在 Google 地圖中查看位置</a>
                
                {LEGAL_FOOTER}
            </div>
            <div class="action-bar">
                <a href="tel:{MY_PHONE}" class="btn btn-call">致電 SK-L</a>
                <a href="{MY_LINE_URL}" class="btn btn-line">LINE 諮詢</a>
            </div>
        </div>
        """
        (out/slug/"index.html").write_text(f"<!doctype html><html lang='zh-TW'>{get_head(name + ' | 大台中房產推薦', d.get('描述',''), img)}<body>{detail_html}</body></html>", encoding="utf-8")
        
        # --- 生成首頁卡片 ---
        items.append(f'''
            <div class="property-card" data-region="{esc(reg)}" data-type="{esc(use_type)}" data-price="{esc(p_str)}">
                <a href="{internal_url}">
                    <img src="{img}" style="width:100%; height:330px; object-fit:cover; display:block;">
                </a>
                <div class="card-info">
                    <h4 style="font-size:21px; margin:0 0 12px 0; font-weight:800; color:var(--sk-navy);">{esc(name)}</h4>
                    <div class="price">{esc(p_str)}</div>
                    <div style="font-size:14px; color:var(--sk-gray); margin-top:12px; font-weight:500;">{esc(reg)} • {esc(use_type)}</div>
                    <a href="{internal_url}" style="display:block; text-align:center; margin-top:25px; padding:18px; background:var(--sk-light); color:var(--sk-navy); text-decoration:none; font-size:15px; font-weight:800; border-radius:20px;">查看詳細顧問建議</a>
                </div>
            </div>
        ''')

    # 保存快取
    with open(GEOCACHE_PATH, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

    # 篩選標籤
    reg_btns = "".join([f'<button class="tag f-reg" data-val="{esc(r)}" onclick="setTag(this, \'f-reg\')">{esc(r)}</button>' for r in sorted(regions)])
    type_btns = "".join([f'<button class="tag f-type" data-val="{esc(t)}" onclick="setTag(this, \'f-type\')">{esc(t)}</button>' for t in sorted(types)])

    # --- 生成首頁 HTML ---
    home_html = f"""
    <div class="container">
        <div class="hero">
            <div class="hero-content">
                <h2>{esc(SITE_TITLE)}</h2>
                <p>Premium Real Estate • Professional Analysis</p>
            </div>
        </div>
        
        <div class="map-box"><div id="map"></div></div>
        
        <div class="filter-section">
            <div class="filter-group">
                <button class="tag f-reg active" data-val="all" onclick="setTag(this, 'f-reg')">全部地區</button>
                {reg_btns}
            </div>
            <div class="filter-group" style="margin-top:18px;">
                <button class="tag f-type active" data-val="all" onclick="setTag(this, 'f-type')">所有用途</button>
                {type_btns}
            </div>
            <div class="filter-group" style="margin-top:18px; border-top:1px solid #f1f5f9; padding-top:25px;">
                <button class="tag f-sort active" data-val="none" onclick="setTag(this, 'f-sort')">預設排序</button>
                <button class="tag f-sort" data-val="high" onclick="setTag(this, 'f-sort')">價格：高至低</button>
                <button class="tag f-sort" data-val="low" onclick="setTag(this, 'f-sort')">價格：低至高</button>
            </div>
        </div>
        
        <div id="list">{''.join(items)}</div>
        
        {LEGAL_FOOTER}
        
        <div class="action-bar">
            <a href="tel:{MY_PHONE}" class="btn btn-call">致電 SK-L</a>
            <a href="{MY_LINE_URL}" class="btn btn-line">LINE 諮詢</a>
        </div>
    </div>
    """
    (out/"index.html").write_text(f"<!doctype html><html lang='zh-TW'>{get_head(SITE_TITLE, is_home=True, map_data_json=json.dumps(map_data, ensure_ascii=False))}<body>{home_html}</body></html>", encoding="utf-8")

if __name__ == "__main__": build()
