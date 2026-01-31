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

# --- 1. 個人品牌與環境配置 ---
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQShAl0-TbUU0MQdYVe53im2T6lXQgh_7g-bdL6HHpIBFtA2yfIAMbPw4J9RgZUkROb9AAiMhnRC0kH/pub?output=csv"
MY_PHONE = "0938-615-351"
MY_LINE_URL = "https://line.me/ti/p/FDsMyAYDv"
SITE_TITLE = "SK-L 大台中房地產"
GA4_ID = "G-B7WP9BTP8X"
MAPS_API_KEY = os.getenv("MAPS_API_KEY", "AIzaSyDzgnI2Ucv622CRkWwo2GE5JRrs_Y4HQY0")
IMG_BASE = "https://raw.githubusercontent.com/ShihKaiLin/taichung-houses/main/images/"
GEOCACHE_PATH = Path("geocache.json")

# --- 2. 質感合規頁尾 (不可或缺的品牌細節) ---
LEGAL_FOOTER = """
<div style="margin: 100px 0 40px; padding: 20px; text-align: center; border-top: 1px solid #f3f4f6;">
    <div style="font-size: 11px; color: #9ca3af; line-height: 1.8; letter-spacing: 0.8px;">
        英柏國際地產有限公司 | 中市地價二字第 1070029259 號<br>
        王一媖 經紀人 (103) 中市經紀字第 00678 號<br>
        <span style="opacity: 0.6;">© 2026 SK-L Branding. All Rights Reserved.</span>
    </div>
</div>
"""

def esc(s):
    return html.escape(str(s or "").strip())

def get_head(title, desc="", img="", is_home=False, map_data_json="[]"):
    # 極致 SEO 優化
    seo_desc = esc(desc)[:80] if desc else f"{SITE_TITLE} - 精選台中優質房產，林世塏為您專業服務。"
    seo_img = img if img.startswith("http") else f"{IMG_BASE}hero_bg.jpg"
    
    # 流量追蹤與分析
    ga_script = f"""
    <script async src="https://www.googletagmanager.com/gtag/js?id={GA4_ID}"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){{dataLayer.push(arguments);}}
      gtag('js', new Date());
      gtag('config', '{GA4_ID}');
    </script>
    """ if GA4_ID else ""

    map_script = ""
    if is_home:
        map_script = f"""
        <script src="https://maps.googleapis.com/maps/api/js?key={MAPS_API_KEY}"></script>
        <script>
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

            function initMap() {{
                const map = new google.maps.Map(document.getElementById("map"), {{
                    center: {{ lat: 24.162, lng: 120.647 }},
                    zoom: 12,
                    disableDefaultUI: true,
                    zoomControl: true,
                    styles: [{{"featureType":"poi","stylers":[{{"visibility":"off"}}]}}]
                }});
                const locations = {map_data_json};
                locations.forEach(loc => {{
                    if(!loc.lat || !loc.lng) return;
                    const marker = new google.maps.Marker({{
                        position: {{lat: loc.lat, lng: loc.lng}},
                        map: map,
                        title: loc.name
                    }});
                    // 地圖打點點擊後引導至內頁，刷出停留率
                    marker.addListener("click", () => {{
                        window.location.href = loc.internal_url;
                    }});
                }});
            }}
            window.onload = initMap;
        </script>
        """

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
            :root {{ --sk-navy: #1A365D; --sk-gold: #C5A059; --sk-light: #F7FAFC; --sk-dark: #2D3748; }}
            body {{ font-family: 'PingFang TC', 'Heiti TC', sans-serif; background: #fff; margin: 0; color: var(--sk-dark); -webkit-font-smoothing: antialiased; }}
            .container {{ max-width: 500px; margin: auto; background: #fff; min-height: 100vh; position: relative; box-shadow: 0 0 50px rgba(0,0,0,0.08); }}
            
            .hero {{ height: 320px; background: url('{IMG_BASE}hero_bg.jpg') center/cover; display: flex; align-items: center; justify-content: center; color: #fff; position: relative; }}
            .hero::after {{ content:''; position:absolute; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.35); }}
            .hero-content {{ position: relative; z-index: 2; text-align: center; }}
            .hero-content h2 {{ font-size: 34px; margin: 0; letter-spacing: 6px; font-weight: 900; }}
            .hero-content p {{ font-size: 14px; opacity: 0.9; margin-top: 10px; letter-spacing: 2px; }}

            .map-box {{ margin: -45px 20px 0; position: relative; z-index: 10; }}
            #map {{ height: 280px; border-radius: 24px; box-shadow: 0 20px 40px rgba(0,0,0,0.12); border: 6px solid #fff; }}

            .filter-section {{ padding: 35px 20px 10px; }}
            .filter-group {{ display: flex; gap: 10px; overflow-x: auto; padding-bottom: 15px; -ms-overflow-style: none; scrollbar-width: none; }}
            .filter-group::-webkit-scrollbar {{ display: none; }}
            
            .tag {{ padding: 10px 22px; border-radius: 50px; background: var(--sk-light); font-size: 13px; color: #4A5568; cursor: pointer; white-space: nowrap; border:none; font-weight: 600; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); }}
            .tag.active {{ background: var(--sk-navy); color: #fff; transform: translateY(-2px); box-shadow: 0 4px 12px rgba(26, 54, 93, 0.2); }}

            .property-card {{ margin: 30px 20px; border-radius: 28px; overflow: hidden; background: #fff; box-shadow: 0 12px 35px rgba(0,0,0,0.06); border: 1px solid #f1f5f9; transition: transform 0.3s ease; }}
            .card-info {{ padding: 25px; }}
            .price {{ font-size: 24px; color: var(--sk-gold); font-weight: 900; letter-spacing: -0.5px; }}
            
            .action-bar {{ position: fixed; bottom: 0; left: 50%; transform: translateX(-50%); width: 100%; max-width: 500px; padding: 18px 25px 42px; display: flex; gap: 15px; background: rgba(255,255,255,0.92); backdrop-filter: blur(20px); border-top: 1px solid #f1f1f1; z-index: 999; }}
            .btn {{ flex: 1; text-align: center; padding: 18px; border-radius: 20px; text-decoration: none; font-weight: 800; color: #fff; font-size: 16px; transition: 0.2s; }}
            .btn-call {{ background: #1A202C; }}
            .btn-line {{ background: #00B900; }}
            
            .back-btn {{ position: absolute; top: 25px; left: 25px; background: #fff; padding: 12px 22px; border-radius: 16px; text-decoration: none; font-weight: 800; color: var(--sk-navy); z-index: 100; box-shadow: 0 8px 20px rgba(0,0,0,0.1); }}
            .btn-ext-link {{ display: block; text-align: center; padding: 18px; background: #fff; color: var(--sk-navy); text-decoration: none; border-radius: 16px; margin-top: 20px; font-weight: 700; border: 2px solid #edf2f7; }}
            .advice-box {{ background: #f0f7ff; padding: 22px; border-radius: 20px; margin-bottom: 25px; border-left: 6px solid #3182ce; font-size: 15px; line-height: 1.7; }}
        </style>
    </head>
    """

def build():
    out = Path(".")
    # 清理舊檔案
    for p in out.glob("p*"):
        if p.is_dir() and re.match(r'^p\d+$', p.name):
            shutil.rmtree(p)
    
    # 安全加載地理快取
    cache = {}
    if GEOCACHE_PATH.exists():
        try:
            with open(GEOCACHE_PATH, 'r', encoding='utf-8') as f:
                cache = json.load(f)
        except:
            cache = {}

    # 抓取試算表
    res = requests.get(SHEET_CSV_URL)
    res.encoding = 'utf-8-sig'
    reader = csv.DictReader(res.text.splitlines())
    
    items, map_data, regions, types = [], [], set(), set()
    num_re = re.compile(r'[^\d.]')
    
    for i, row in enumerate(reader):
        d = {str(k).strip(): str(v).strip() for k, v in row.items() if k}
        
        # 外部連結邏輯 (確保不抓到圖片)
        ext_link = ""
        for val in d.values():
            if str(val).startswith("http") and not any(x in str(val).lower() for x in ['.jpg','.png','.jpeg','.webp']):
                ext_link = val
                break
        
        name = d.get("案名") or next((v for k,v in d.items() if "案名" in k), "")
        if not name or d.get("狀態", "").upper() in ["OFF", "FALSE"]:
            continue
        
        reg, p_str, use_type, addr = d.get("區域","台中"), d.get("價格","面議"), d.get("用途","住宅"), d.get("地址", "")
        regions.add(reg)
        types.add(use_type)
        
        img = d.get("圖片網址") or next((v for k,v in d.items() if "圖片" in k), "")
        if img and not img.startswith("http"):
            img = f"{IMG_BASE}{img.lstrip('/')}"
        if not img:
            img = "https://placehold.co/800x600?text=SK-L+Premium+Property"
        
        slug = f"p{i}"
        (out/slug).mkdir(exist_ok=True)
        search_addr = addr if addr else f"台中市{name}"
        
        # 座標處理
        lat, lng = cache.get(search_addr, {}).get("lat"), cache.get(search_addr, {}).get("lng")
        
        # 旗艦版邏輯：強制內連增加停留時間
        internal_url = f"./{slug}/"
        map_data.append({
            "name": name, 
            "address": search_addr, 
            "internal_url": internal_url, 
            "lat": lat, 
            "lng": lng
        })

        # --- 生成物件詳情頁面 ---
        ext_btn_html = f'<a href="{ext_link}" target="_blank" class="btn-ext-link">🌐 前往原始物件網頁 (591/樂屋網)</a>' if ext_link else ""
        detail_html = f"""
        <div class="container">
            <a href="../" class="back-btn">← 返回列表</a>
            <img src="{img}" style="width:100%; height:480px; object-fit:cover; display:block;">
            <div style="padding:45px 25px; background:#fff; border-radius:40px 40px 0 0; margin-top:-50px; position:relative; z-index:10;">
                <h1 style="font-size:32px; font-weight:900; color:var(--sk-navy); margin:0; line-height:1.2;">{esc(name)}</h1>
                <div class="price" style="margin-top:15px;">{esc(p_str)}</div>
                
                <div style="line-height:2.2; color:#4a5568; margin:35px 0; font-size:16px;">
                    {esc(d.get("描述","")).replace('、','<br>• ')}
                </div>
                
                <div class="advice-box">
                    <strong style="color:#2b6cb0; font-size:17px; display:block; margin-bottom:8px;">💡 SK-L 顧問專業評估</strong>
                    台中房市近期變動頻繁，此物件所在的 {esc(reg)} 區域具備優質生活機能。若您對本案的學區細節、社區成交行情或銀行貸款成數有疑問，歡迎直接點擊下方 LINE 諮詢，我將為您提供最精準的資訊。
                </div>
                
                {ext_btn_html}
                <a href="https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(search_addr)}" target="_blank" style="display:block; text-align:center; padding:18px; background:var(--sk-navy); color:#fff; text-decoration:none; border-radius:18px; margin-top:15px; font-weight:700; box-shadow:0 10px 20px rgba(26,54,93,0.15);">📍 開啟 Google 地圖導航</a>
                
                {LEGAL_FOOTER}
            </div>
            <div class="action-bar">
                <a href="tel:{MY_PHONE}" class="btn btn-call">致電 SK-L</a>
                <a href="{MY_LINE_URL}" class="btn btn-line">LINE 諮詢</a>
            </div>
        </div>
        """
        (out/slug/"index.html").write_text(f"<!doctype html><html lang='zh-TW'>{get_head(name + ' | ' + reg + '房產專家 SK-L', d.get('描述',''), img)}<body>{detail_html}</body></html>", encoding="utf-8")
        
        # --- 生成首頁物件卡片 ---
        items.append(f'''
            <div class="property-card" data-region="{esc(reg)}" data-type="{esc(use_type)}" data-price="{num_re.sub('', p_str)}">
                <a href="{internal_url}">
                    <img src="{img}" style="width:100%; height:300px; object-fit:cover; display:block;">
                </a>
                <div class="card-info">
                    <h4 style="font-size:18px; margin:0 0 10px; font-weight:800;">{esc(name)}</h4>
                    <div class="price">{esc(p_str)}</div>
                    <div style="font-size:13px; color:#94a3b8; margin-top:8px;">{esc(reg)} • {esc(use_type)}</div>
                    <a href="{internal_url}" style="display:block; text-align:center; margin-top:20px; padding:15px; background:var(--sk-light); color:var(--sk-navy); text-decoration:none; font-size:14px; font-weight:700; border-radius:15px;">查看詳細分析建議</a>
                </div>
            </div>
        ''')

    # 寫回快取與按鈕生成
    with open(GEOCACHE_PATH, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

    # 修正 Actions 引號轉義
    reg_btns = "".join([f"<button class='tag f-reg' data-val='{esc(r)}' onclick='setTag(this, \"f-reg\")'>{esc(r)}</button>" for r in sorted(regions)])
    type_btns = "".join([f"<button class='tag f-type' data-val='{esc(t)}' onclick='setTag(this, \"f-type\")'>{esc(t)}</button>" for t in sorted(types)])

    # --- 生成首頁 HTML ---
    home_html = f"""
    <div class="container">
        <div class="hero">
            <div class="hero-content">
                <h2>{esc(SITE_TITLE)}</h2>
                <p>Curated Properties • Professional Consulting</p>
            </div>
        </div>
        
        <div class="map-box"><div id="map"></div></div>
        
        <div class="filter-section">
            <div class="filter-group">
                <button class="tag f-reg active" data-val="all" onclick="setTag(this, 'f-reg')">全部地區</button>
                {reg_btns}
            </div>
            <div class="filter-group" style="margin-top:12px;">
                <button class="tag f-type active" data-val="all" onclick="setTag(this, 'f-type')">所有用途</button>
                {type_btns}
            </div>
            <div class="filter-group" style="margin-top:12px; border-top:1px solid #f3f4f6; padding-top:18px;">
                <button class="tag f-sort active" data-val="none" onclick="setTag(this, 'f-sort')">預設排序</button>
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
