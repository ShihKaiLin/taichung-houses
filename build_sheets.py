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
# 這些變數決定了整個網站的靈魂與外觀
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQShAl0-TbUU0MQdYVe53im2T6lXQgh_7g-bdL6HHpIBFtA2yfIAMbPw4J9RgZUkROb9AAiMhnRC0kH/pub?output=csv"
MY_PHONE = "0938-615-351"
MY_LINE_URL = "https://line.me/ti/p/FDsMyAYDv"
SITE_TITLE = "SK-L 大台中房地產"
GA4_ID = "G-B7WP9BTP8X"

# Google Maps API Key：若環境變數沒設定則使用預設
MAPS_API_KEY = os.getenv("MAPS_API_KEY", "AIzaSyDzgnI2Ucv622CRkWwo2GE5JRrs_Y4HQY0")

# 圖片與路徑
IMG_BASE = "https://raw.githubusercontent.com/ShihKaiLin/taichung-houses/main/images/"
GEOCACHE_PATH = Path("geocache.json")

# --- 2. 品牌質感法律頁尾 (絕對不縮水) ---
LEGAL_FOOTER = """
<div style="margin: 120px 0 40px; padding: 30px 20px; text-align: center; border-top: 1px solid #edf2f7; background-color: #fafafa;">
    <div style="font-size: 11px; color: #718096; line-height: 2; letter-spacing: 1px;">
        <strong>英柏國際地產有限公司</strong><br>
        中市地價二字第 1070029259 號<br>
        王一媖 經紀人 (103) 中市經紀字第 00678 號<br>
        <span style="opacity: 0.7; margin-top: 10px; display: block;">
            © 2026 SK-L Branding. 所有圖文內容均受法律保護。
        </span>
    </div>
</div>
"""

def esc(s):
    """HTML 轉義，防止破版"""
    return html.escape(str(s or "").strip())

def get_head(title, desc="", img="", is_home=False, map_data_json="[]"):
    """生成每個頁面的完整 Head 區塊，包含 SEO、CSS 與 JS 邏輯"""
    seo_desc = esc(desc)[:80] if desc else f"{SITE_TITLE} - 提供大台中地區最專業的房屋買賣服務，林世塏親自為您把關。"
    seo_img = img if img.startswith("http") else f"{IMG_BASE}hero_bg.jpg"
    
    # 追蹤與地圖腳本
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
                map = new google.maps.Map(document.getElementById("map"), {{
                    center: {{ lat: 24.162, lng: 120.647 }},
                    zoom: 12,
                    disableDefaultUI: true,
                    zoomControl: true,
                    styles: [{{"featureType":"poi","stylers":[{{"visibility":"off"}}]}}]
                }});
                
                infoWindow = new google.maps.InfoWindow();
                const locations = {map_data_json};
                
                locations.forEach(loc => {{
                    if(!loc.lat || !loc.lng) return;
                    const marker = new google.maps.Marker({{
                        position: {{lat: parseFloat(loc.lat), lng: parseFloat(loc.lng)}},
                        map: map,
                        title: loc.name,
                        icon: 'https://maps.google.com/mapfiles/ms/icons/red-dot.png'
                    }});
                    
                    // 地圖點擊：彈出預覽視窗，引導進入內頁
                    marker.addListener("click", () => {{
                        const content = `
                            <div style="padding:12px; font-family:'PingFang TC', sans-serif; width:200px;">
                                <div style="background-image:url('${{loc.img}}'); background-size:cover; background-position:center; height:120px; border-radius:10px; margin-bottom:10px;"></div>
                                <h4 style="margin:0 0 5px 0; font-size:15px; color:#1A365D;">${{loc.name}}</h4>
                                <div style="color:#C5A059; font-weight:900; font-size:16px; margin-bottom:12px;">${{loc.price}}</div>
                                <a href="${{loc.url}}" style="display:block; text-align:center; background:#1A365D; color:#fff; text-decoration:none; padding:10px; border-radius:8px; font-size:13px; font-weight:bold;">查看 SK-L 顧問建議</a>
                            </div>`;
                        infoWindow.setContent(content);
                        infoWindow.open(map, marker);
                    }});
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
                --sk-dark: #2D3748;
            }}
            body {{ 
                font-family: 'PingFang TC', 'Heiti TC', 'Apple LiGothic', sans-serif; 
                background-color: var(--sk-white); 
                margin: 0; 
                color: var(--sk-dark); 
                -webkit-font-smoothing: antialiased; 
            }}
            .container {{ 
                max-width: 500px; 
                margin: 0 auto; 
                background-color: var(--sk-white); 
                min-height: 100vh; 
                position: relative; 
                box-shadow: 0 0 60px rgba(0,0,0,0.08); 
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
                top:0; 
                left:0; 
                width:100%; 
                height:100%; 
                background:rgba(0,0,0,0.35); 
            }}
            .hero-content {{ 
                position: relative; 
                z-index: 2; 
                text-align: center; 
            }}
            .hero-content h2 {{ 
                font-size: 36px; 
                margin: 0; 
                letter-spacing: 8px; 
                font-weight: 900; 
                text-shadow: 0 4px 10px rgba(0,0,0,0.3);
            }}
            .hero-content p {{ 
                font-size: 14px; 
                opacity: 0.95; 
                margin-top: 12px; 
                letter-spacing: 3px; 
                text-transform: uppercase;
            }}

            /* 地圖區塊 */
            .map-box {{ 
                margin: -50px 20px 0; 
                position: relative; 
                z-index: 10; 
            }}
            #map {{ 
                height: 300px; 
                border-radius: 28px; 
                box-shadow: 0 25px 50px rgba(0,0,0,0.15); 
                border: 6px solid var(--sk-white); 
            }}

            /* 篩選器 */
            .filter-section {{ padding: 40px 20px 10px; }}
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
                color: #4A5568; 
                cursor: pointer; 
                white-space: nowrap; 
                border:none; 
                font-weight: 600; 
                transition: all 0.3s ease; 
            }}
            .tag.active {{ 
                background: var(--sk-navy); 
                color: var(--sk-white); 
                box-shadow: 0 4px 15px rgba(26, 54, 93, 0.25); 
                transform: translateY(-2px);
            }}

            /* 物件卡片 */
            .property-card {{ 
                margin: 30px 20px; 
                border-radius: 30px; 
                overflow: hidden; 
                background: var(--sk-white); 
                box-shadow: 0 15px 40px rgba(0,0,0,0.06); 
                border: 1px solid #f1f5f9; 
            }}
            .card-info {{ padding: 25px; }}
            .price {{ 
                font-size: 26px; 
                color: var(--sk-gold); 
                font-weight: 900; 
                letter-spacing: -1px; 
            }}
            
            /* 動作條 */
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
                backdrop-filter: blur(15px); 
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
                transition: transform 0.2s ease;
            }}
            .btn:active {{ transform: scale(0.96); }}
            .btn-call {{ background: #1A202C; }}
            .btn-line {{ background: #00B900; }}
            
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
                background: var(--sk-white); 
                color: var(--sk-navy); 
                text-decoration: none; 
                border-radius: 18px; 
                margin-top: 25px; 
                font-weight: 700; 
                border: 2px solid #edf2f7; 
            }}
            .advice-box {{ 
                background: #f0f7ff; 
                padding: 25px; 
                border-radius: 22px; 
                margin-bottom: 30px; 
                border-left: 6px solid var(--sk-gold); 
                font-size: 15px; 
                line-height: 1.8; 
            }}
        </style>
    </head>
    """

def build():
    out = Path(".")
    # 徹底清理舊物件目錄
    for p in out.glob("p*"):
        if p.is_dir() and re.match(r'^p\d+$', p.name):
            shutil.rmtree(p)
    
    # 地理座標快取載入
    cache = {}
    if GEOCACHE_PATH.exists():
        try:
            with open(GEOCACHE_PATH, 'r', encoding='utf-8') as f:
                cache = json.load(f)
        except Exception as e:
            print(f"快取載入失敗: {e}")
            cache = {}

    # 讀取數據源
    try:
        res = requests.get(SHEET_CSV_URL, timeout=15)
        res.encoding = 'utf-8-sig'
        reader = csv.DictReader(res.text.splitlines())
    except Exception as e:
        print(f"CSV 下載失敗: {e}")
        return

    items, map_data, regions, types = [], [], set(), set()
    num_re = re.compile(r'[^\d.]')
    
    for i, row in enumerate(reader):
        # 暴力清理欄位名稱
        d = {str(k).strip(): str(v).strip() for k, v in row.items() if k}
        
        # 外部連結偵測（排除圖片，尋找真實網址）
        ext_link = ""
        for val in d.values():
            if str(val).startswith("http") and not any(x in str(val).lower() for x in ['.jpg','.png','.jpeg','.webp']):
                ext_link = val
                break
        
        # 必填項校驗
        name = d.get("案名") or next((v for k,v in d.items() if "案名" in k), "")
        if not name or d.get("狀態", "").upper() in ["OFF", "FALSE"]:
            continue
        
        # 欄位解析
        reg, p_str, use_type, addr = d.get("區域","台中"), d.get("價格","面議"), d.get("用途","住宅"), d.get("地址", "")
        regions.add(reg)
        types.add(use_type)
        
        # 圖片處理
        img = d.get("圖片網址") or next((v for k,v in d.items() if "圖片" in k), "")
        if img and not img.startswith("http"):
            img = f"{IMG_BASE}{img.lstrip('/')}"
        if not img:
            img = "https://placehold.co/800x600?text=SK-L+Premium+Property"
        
        # 子目錄生成
        slug = f"p{i}"
        (out/slug).mkdir(exist_ok=True)
        search_addr = addr if addr else f"台中市{name}"
        
        # 快取座標獲取
        lat, lng = cache.get(search_addr, {}).get("lat"), cache.get(search_addr, {}).get("lng")
        
        # 核心：引流至內頁
        internal_url = f"./{slug}/"
        map_data.append({
            "name": name, 
            "url": internal_url, 
            "lat": lat, 
            "lng": lng, 
            "img": img, 
            "price": p_str
        })

        # --- 生成子網頁詳情 ---
        ext_btn_html = f'<a href="{ext_link}" target="_blank" class="btn-ext-link">🌐 前往 591 / 樂屋網 查看原始連結</a>' if ext_link else ""
        detail_html = f"""
        <div class="container">
            <a href="../" class="back-btn">← 返回列表</a>
            <img src="{img}" style="width:100%; height:500px; object-fit:cover; display:block;">
            <div style="padding:50px 30px; background:#fff; border-radius:45px 45px 0 0; margin-top:-60px; position:relative; z-index:10;">
                <h1 style="font-size:32px; font-weight:900; color:var(--sk-navy); margin:0; line-height:1.3;">{esc(name)}</h1>
                <div class="price" style="margin-top:20px;">{esc(p_str)}</div>
                
                <div style="line-height:2.3; color:#4a5568; margin:35px 0; font-size:16.5px; letter-spacing:0.5px;">
                    {esc(d.get("描述","")).replace('、','<br>• ')}
                </div>
                
                <div class="advice-box">
                    <strong style="color:var(--sk-navy); font-size:18px; display:block; margin-bottom:10px;">💡 SK-L 顧問專業觀點</strong>
                    此案位於大台中地區極具潛力的區域。如果您需要了解該社區最近六個月的真實成交行情、或想評估銀行的房貸成數，歡迎直接點擊下方按鈕與我連繫。
                </div>
                
                {ext_btn_html}
                <a href="https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(search_addr)}" target="_blank" style="display:block; text-align:center; padding:20px; background:var(--sk-navy); color:#fff; text-decoration:none; border-radius:20px; margin-top:15px; font-weight:700; box-shadow:0 12px 25px rgba(26,54,93,0.18);">📍 在 Google 地圖中查看位置</a>
                
                {LEGAL_FOOTER}
            </div>
            <div class="action-bar">
                <a href="tel:{MY_PHONE}" class="btn btn-call">致電 SK-L</a>
                <a href="{MY_LINE_URL}" class="btn btn-line">LINE 諮詢</a>
            </div>
        </div>
        """
        (out/slug/"index.html").write_text(f"<!doctype html><html lang='zh-TW'>{get_head(name + ' | 大台中推薦房產', d.get('描述',''), img)}<body>{detail_html}</body></html>", encoding="utf-8")
        
        # --- 生成列表物件卡片 ---
        items.append(f'''
            <div class="property-card" data-region="{esc(reg)}" data-type="{esc(use_type)}" data-price="{num_re.sub('', p_str)}">
                <a href="{internal_url}">
                    <img src="{img}" style="width:100%; height:320px; object-fit:cover; display:block;">
                </a>
                <div class="card-info">
                    <h4 style="font-size:20px; margin:0 0 12px 0; font-weight:800; color:var(--sk-navy);">{esc(name)}</h4>
                    <div class="price">{esc(p_str)}</div>
                    <div style="font-size:13px; color:#94a3b8; margin-top:10px; font-weight:500;">{esc(reg)} • {esc(use_type)}</div>
                    <a href="{internal_url}" style="display:block; text-align:center; margin-top:20px; padding:18px; background:var(--sk-light); color:var(--sk-navy); text-decoration:none; font-size:14px; font-weight:800; border-radius:18px;">查看詳細分析建議</a>
                </div>
            </div>
        ''')

    # 最終快取保存
    with open(GEOCACHE_PATH, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

    # 篩選按鈕組件 (修正引號確保 Actions 100% 綠燈)
    reg_btns = "".join([f'<button class="tag f-reg" data-val="{esc(r)}" onclick="setTag(this, \'f-reg\')">{esc(r)}</button>' for r in sorted(regions)])
    type_btns = "".join([f'<button class="tag f-type" data-val="{esc(t)}" onclick="setTag(this, \'f-type\')">{esc(t)}</button>' for t in sorted(types)])

    # --- 生成首頁 HTML ---
    home_html = f"""
    <div class="container">
        <div class="hero">
            <div class="hero-content">
                <h2>{esc(SITE_TITLE)}</h2>
                <p>Premium Real Estate • Expert Analysis</p>
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
            <div class="filter-group" style="margin-top:15px; border-top:1px solid #f1f5f9; padding-top:20px;">
                <button class="tag f-sort active" data-val="none" onclick="setTag(this, 'f-sort')">默認排序</button>
                <button class="tag f-sort" data-val="high" onclick="setTag(this, 'f-sort')">價格：由高到低</button>
                <button class="tag f-sort" data-val="low" onclick="setTag(this, 'f-sort')">價格：由低到高</button>
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
