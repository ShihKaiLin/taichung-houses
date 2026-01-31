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

# --- 1. 個人品牌核心配置 ---
# 確保這些變數對接正確，這是網站的靈魂
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQShAl0-TbUU0MQdYVe53im2T6lXQgh_7g-bdL6HHpIBFtA2yfIAMbPw4J9RgZUkROb9AAiMhnRC0kH/pub?output=csv"
MY_PHONE = "0938-615-351"
MY_LINE_URL = "https://line.me/ti/p/FDsMyAYDv"
SITE_TITLE = "SK-L 大台中房地產"
GA4_ID = "G-B7WP9BTP8X"

# Google Maps API Key：確保地圖功能運行的關鍵
MAPS_API_KEY = os.getenv("MAPS_API_KEY", "AIzaSyDzgnI2Ucv622CRkWwo2GE5JRrs_Y4HQY0")

# 圖片與路徑
IMG_BASE = "https://raw.githubusercontent.com/ShihKaiLin/taichung-houses/main/images/"
GEOCACHE_PATH = Path("geocache.json")

# --- 2. 品牌質感法律頁尾 (絕對紮實) ---
LEGAL_FOOTER = """
<div style="margin: 120px 0 40px; padding: 40px 20px; text-align: center; border-top: 1px solid #edf2f7; background-color: #fafafa; border-radius: 30px 30px 0 0;">
    <div style="font-size: 11px; color: #718096; line-height: 2; letter-spacing: 1px;">
        <strong style="color: #2d3748; font-size: 13px;">英柏國際地產有限公司</strong><br>
        中市地價二字第 1070029259 號<br>
        王一媖 經紀人 (103) 中市經紀字第 00678 號<br>
        <span style="opacity: 0.7; margin-top: 15px; display: block; font-size: 10px;">
            © 2026 SK-L Branding. 所有圖文內容均受法律保護，轉載必究。
        </span>
    </div>
</div>
"""

def esc(s):
    """HTML 轉義處理"""
    return html.escape(str(s or "").strip())

def get_head(title, desc="", img="", is_home=False, map_data_json="[]"):
    """生成完整的 Head 區塊，包含極致 SEO 與前端互動邏輯"""
    seo_desc = esc(desc)[:80] if desc else f"{SITE_TITLE} - 精選台中優質房產，林世塏專業服務。"
    seo_img = img if img.startswith("http") else f"{IMG_BASE}hero_bg.jpg"
    
    # 流量追蹤與分析腳本
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
                    if(!loc.lat || !loc.lng) return;
                    const pos = {{lat: parseFloat(loc.lat), lng: parseFloat(loc.lng)}};
                    const marker = new google.maps.Marker({{
                        position: pos,
                        map: map,
                        title: loc.name,
                        optimized: false,
                        animation: google.maps.Animation.DROP
                    }});
                    bounds.extend(pos);
                    
                    // 地圖點擊：彈出預覽視窗，引流至內頁
                    marker.addListener("click", () => {{
                        const content = `
                            <div style="padding:12px; font-family:'PingFang TC', sans-serif; width:220px;">
                                <div style="background-image:url('${{loc.img}}'); background-size:cover; background-position:center; height:130px; border-radius:12px; margin-bottom:12px;"></div>
                                <h4 style="margin:0 0 6px 0; font-size:16px; color:#1A365D; font-weight:800;">${{loc.name}}</h4>
                                <div style="color:#C5A059; font-weight:900; font-size:18px; margin-bottom:12px;">${{loc.price}}</div>
                                <a href="${{loc.url}}" style="display:block; text-align:center; background:#1A365D; color:#fff; text-decoration:none; padding:12px; border-radius:10px; font-size:13px; font-weight:bold;">查看 SK-L 顧問點評</a>
                            </div>`;
                        infoWindow.setContent(content);
                        infoWindow.open(map, marker);
                    }});
                }});
                // 自動縮放至所有圖釘的最佳範圍
                if (locations.length > 0) map.fitBounds(bounds);
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
                        const pA = parseFloat(a.dataset.price) || 0;
                        const pB = parseFloat(b.dataset.price) || 0;
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
                --sk-gray: #718096;
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
            
            /* Hero 區塊 */
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
                letter-spacing: 6px; 
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

            /* 地圖互動區塊 */
            .map-box {{ 
                margin: -50px 20px 0; 
                position: relative; 
                z-index: 10; 
            }}
            #map {{ 
                height: 320px; 
                border-radius: 30px; 
                box-shadow: 0 25px 50px rgba(0,0,0,0.15); 
                border: 6px solid var(--sk-white); 
            }}

            /* 篩選與排序組件 */
            .filter-section {{ padding: 45px 20px 10px; }}
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
                box-shadow: 0 6px 15px rgba(26, 54, 93, 0.3); 
                transform: translateY(-2px);
            }}

            /* 房產物件卡片 */
            .property-card {{ 
                margin: 35px 20px; 
                border-radius: 32px; 
                overflow: hidden; 
                background: var(--sk-white); 
                box-shadow: 0 15px 45px rgba(0,0,0,0.06); 
                border: 1px solid #f1f5f9; 
                transition: transform 0.3s ease;
            }}
            .card-info {{ padding: 25px; }}
            .price {{ 
                font-size: 26px; 
                color: var(--sk-gold); 
                font-weight: 900; 
                letter-spacing: -1px; 
            }}
            
            /* 底部導覽條 */
            .action-bar {{ 
                position: fixed; 
                bottom: 0; 
                left: 50%; 
                transform: translateX(-50%); 
                width: 100%; 
                max-width: 500px; 
                padding: 20px 25px 45px; 
                display: flex; 
                gap: 15px; 
                background: rgba(255,255,255,0.92); 
                backdrop-filter: blur(20px); 
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
            
            /* 物件內頁專用 */
            .back-btn {{ 
                position: absolute; 
                top: 30px; 
                left: 25px; 
                background: var(--sk-white); 
                padding: 12px 22px; 
                border-radius: 18px; 
                text-decoration: none; 
                font-weight: 800; 
                color: var(--sk-navy); 
                z-index: 100; 
                box-shadow: 0 10px 25px rgba(0,0,0,0.12); 
            }}
            .btn-ext-link {{ 
                display: block; 
                text-align: center; 
                padding: 20px; 
                background: #fff; 
                color: var(--sk-navy); 
                text-decoration: none; 
                border-radius: 20px; 
                margin-top: 25px; 
                font-weight: 700; 
                border: 2.5px solid #edf2f7; 
            }}
            .advice-box {{ 
                background: #f0f7ff; 
                padding: 25px; 
                border-radius: 24px; 
                margin-bottom: 35px; 
                border-left: 8px solid var(--sk-gold); 
                line-height: 1.9; 
            }}
        </style>
    </head>
    """

def build():
    out = Path(".")
    # 清理歷史生成目錄
    for p in out.glob("p*"):
        if p.is_dir() and re.match(r'^p\d+$', p.name):
            shutil.rmtree(p)
    
    # 載入地理座標快取，保護 API 額度
    cache = {}
    if GEOCACHE_PATH.exists():
        try:
            with open(GEOCACHE_PATH, 'r', encoding='utf-8') as f:
                cache = json.load(f)
        except Exception as e:
            print(f"Cache Error: {e}")
            cache = {}

    # 下載數據
    try:
        res = requests.get(SHEET_CSV_URL, timeout=15)
        res.encoding = 'utf-8-sig'
        reader = csv.DictReader(res.text.splitlines())
    except Exception as e:
        print(f"Download Error: {e}")
        return

    items, map_data, regions, types = [], [], set(), set()
    num_re = re.compile(r'[^\d.]')
    
    for i, row in enumerate(reader):
        # 清理並讀取資料
        d = {str(k).strip(): str(v).strip() for k, v in row.items() if k}
        
        # 識別案名與狀態
        name = d.get("案名") or next((v for k,v in d.items() if "案名" in k), "")
        if not name or d.get("狀態", "").upper() in ["OFF", "FALSE"]:
            continue
            
        # 尋找原始外部連結 (591/樂屋)
        ext_link = ""
        for val in d.values():
            if str(val).startswith("http") and not any(x in str(val).lower() for x in ['.jpg','.png','.jpeg','.webp']):
                ext_link = val
                break
        
        reg, p_str, use_type, addr = d.get("區域","台中"), d.get("價格","面議"), d.get("用途","住宅"), d.get("地址", "")
        regions.add(reg)
        types.add(use_type)
        
        # 圖片邏輯
        img = d.get("圖片網址") or next((v for k,v in d.items() if "圖片" in k), "")
        if img and not img.startswith("http"):
            img = f"{IMG_BASE}{img.lstrip('/')}"
        if not img:
            img = "https://placehold.co/800x600?text=SK-L+Premium+Property"
        
        # 子網頁目錄
        slug = f"p{i}"
        (out/slug).mkdir(exist_ok=True)
        search_addr = addr if addr else f"台中市{name}"
        
        # 獲取座標
        lat, lng = cache.get(search_addr, {}).get("lat"), cache.get(search_addr, {}).get("lng")
        
        # 旗艦版強內連邏輯
        internal_url = f"./{slug}/"
        map_data.append({
            "name": name, 
            "url": internal_url, 
            "lat": lat, 
            "lng": lng, 
            "img": img, 
            "price": p_str
        })

        # --- 生成物件詳情頁面 (不偷工減料) ---
        ext_btn_html = f'<a href="{ext_link}" target="_blank" class="btn-ext-link">🌐 查看原始物件連結 (591/樂屋網)</a>' if ext_link else ""
        detail_html = f"""
        <div class="container">
            <a href="../" class="back-btn">← 返回列表</a>
            <img src="{img}" style="width:100%; height:500px; object-fit:cover; display:block;">
            <div style="padding:55px 30px; background:#fff; border-radius:50px 50px 0 0; margin-top:-65px; position:relative; z-index:10;">
                <h1 style="font-size:32px; font-weight:900; color:var(--sk-navy); margin:0; line-height:1.3;">{esc(name)}</h1>
                <div class="price" style="margin-top:15px;">{esc(p_str)}</div>
                
                <div style="line-height:2.4; color:#4a5568; margin:40px 0; font-size:16.5px; letter-spacing:0.5px;">
                    {esc(d.get("描述","")).replace('、','<br>• ')}
                </div>
                
                <div class="advice-box">
                    <strong style="color:var(--sk-navy); font-size:18px; display:block; margin-bottom:10px;">💡 SK-L 顧問專業評估</strong>
                    此案位於大台中地區極具潛力的精華地段。如果您對本社區的成交行情、或是銀行貸款成數有任何疑問，歡迎直接點擊下方 LINE 諮詢，我將為您提供專屬的市場分析報告。
                </div>
                
                {ext_btn_html}
                <a href="https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(search_addr)}" target="_blank" style="display:block; text-align:center; padding:22px; background:var(--sk-navy); color:#fff; text-decoration:none; border-radius:20px; margin-top:15px; font-weight:700; box-shadow:0 12px 25px rgba(26,54,93,0.18);">📍 在 Google 地圖中查看位置</a>
                
                {LEGAL_FOOTER}
            </div>
            <div class="action-bar">
                <a href="tel:{MY_PHONE}" class="btn btn-call">致電 SK-L</a>
                <a href="{MY_LINE_URL}" class="btn btn-line">LINE 諮詢</a>
            </div>
        </div>
        """
        (out/slug/"index.html").write_text(f"<!doctype html><html lang='zh-TW'>{get_head(name + ' | 大台中房產推薦', d.get('描述',''), img)}<body>{detail_html}</body></html>", encoding="utf-8")
        
        # --- 生成列表物件卡片 (不偷工減料) ---
        items.append(f'''
            <div class="property-card" data-region="{esc(reg)}" data-type="{esc(use_type)}" data-price="{num_re.sub('', p_str)}">
                <a href="{internal_url}">
                    <img src="{img}" style="width:100%; height:320px; object-fit:cover; display:block;">
                </a>
                <div class="card-info">
                    <h4 style="font-size:20px; margin:0 0 12px 0; font-weight:800; color:var(--sk-navy);">{esc(name)}</h4>
                    <div class="price">{esc(p_str)}</div>
                    <div style="font-size:13px; color:var(--sk-gray); margin-top:10px; font-weight:500;">{esc(reg)} • {esc(use_type)}</div>
                    <a href="{internal_url}" style="display:block; text-align:center; margin-top:20px; padding:18px; background:var(--sk-light); color:var(--sk-navy); text-decoration:none; font-size:14px; font-weight:800; border-radius:18px; transition:0.3s;">查看詳細分析建議</a>
                </div>
            </div>
        ''')

    # 寫回快取
    with open(GEOCACHE_PATH, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

    # 渲染按鈕組 (修正轉義，確保 Actions 穩定)
    reg_btns = "".join([f'<button class="tag f-reg" data-val="{esc(r)}" onclick="setTag(this, \'f-reg\')">{esc(r)}</button>' for r in sorted(regions)])
    type_btns = "".join([f'<button class="tag f-type" data-val="{esc(t)}" onclick="setTag(this, \'f-type\')">{esc(t)}</button>' for t in sorted(types)])

    # --- 生成首頁 HTML (不偷工減料) ---
    home_html = f"""
    <div class="container">
        <div class="hero">
            <div class="hero-content">
                <h2>{esc(SITE_TITLE)}</h2>
                <p>Curated Properties • Professional Analysis</p>
            </div>
        </div>
        
        <div class="map-box"><div id="map"></div></div>
        
        <div class="filter-section">
            <div class="filter-group">
                <button class="tag f-reg active" data-val="all" onclick="setTag(this, 'f-reg')">全部地區</button>
                {reg_btns}
            </div>
            <div class="filter-group" style="margin-top:15px;">
                <button class="tag f-type active" data-val="all" onclick="setTag(this, 'f-type')">所有用途</button>
                {type_btns}
            </div>
            <div class="filter-group" style="margin-top:15px; border-top:1px solid #f1f5f9; padding-top:25px;">
                <button class="tag f-sort active" data-val="none" onclick="setTag(this, 'f-sort')">默認排序</button>
                <button class="tag f-sort" data-val="high" onclick="setTag(this, 'f-sort')">價格：由高至低</button>
                <button class="tag f-sort" data-val="low" onclick="setTag(this, 'f-sort')">價格：由低至高</button>
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
