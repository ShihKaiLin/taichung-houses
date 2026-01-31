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
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQShAl0-TbUU0MQdYVe53im2T6lXQgh_7g-bdL6HHpIBFtA2yfIAMbPw4J9RgZUkROb9AAiMhnRC0kH/pub?output=csv"
MY_PHONE = "0938-615-351"
MY_LINE_URL = "https://line.me/ti/p/FDsMyAYDv"
SITE_TITLE = "SK-L 大台中房地產"
GA4_ID = "G-B7WP9BTP8X"
MAPS_API_KEY = os.getenv("MAPS_API_KEY", "AIzaSyDzgnI2Ucv622CRkWwo2GE5JRrs_Y4HQY0")
IMG_BASE = "https://raw.githubusercontent.com/ShihKaiLin/taichung-houses/main/images/"
GEOCACHE_PATH = Path("geocache.json")

# --- 2. 品牌質感法律頁尾 ---
LEGAL_FOOTER = """
<div style="margin: 100px 0 40px; padding: 25px; text-align: center; border-top: 1px solid #edf2f7;">
    <div style="font-size: 11px; color: #a0aec0; line-height: 1.8; letter-spacing: 0.8px;">
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
    
    # 流量追蹤
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
            let map;
            function initMap() {{
                map = new google.maps.Map(document.getElementById("map"), {{
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
                        position: {{lat: parseFloat(loc.lat), lng: parseFloat(loc.lng)}},
                        map: map,
                        title: loc.name
                    }});
                    // 地圖圖釘點擊導向內頁
                    marker.addListener("click", () => {{
                        window.location.href = loc.url;
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
            :root {{ --sk-navy: #1A365D; --sk-gold: #C5A059; --sk-bg: #F7FAFC; }}
            body {{ font-family: 'PingFang TC', sans-serif; background: #fff; margin: 0; color: #2d3748; -webkit-font-smoothing: antialiased; }}
            .container {{ max-width: 500px; margin: auto; background: #fff; min-height: 100vh; position: relative; box-shadow: 0 0 40px rgba(0,0,0,0.06); }}
            
            .hero {{ height: 320px; background: url('{IMG_BASE}hero_bg.jpg') center/cover; display: flex; align-items: center; justify-content: center; color: #fff; position: relative; }}
            .hero::after {{ content:''; position:absolute; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.3); }}
            .hero-content {{ position: relative; z-index: 2; text-align: center; }}
            .hero-content h2 {{ font-size: 34px; margin: 0; letter-spacing: 5px; font-weight: 900; }}

            .map-box {{ margin: -40px 20px 0; position: relative; z-index: 10; }}
            #map {{ height: 280px; border-radius: 24px; box-shadow: 0 15px 40px rgba(0,0,0,0.1); border: 5px solid #fff; }}

            .filter-section {{ padding: 35px 20px 10px; }}
            .filter-group {{ display: flex; gap: 10px; overflow-x: auto; padding-bottom: 15px; scrollbar-width: none; }}
            .filter-group::-webkit-scrollbar {{ display: none; }}
            
            .tag {{ padding: 10px 20px; border-radius: 50px; background: #f1f5f9; font-size: 13px; color: #64748b; cursor: pointer; white-space: nowrap; border:none; font-weight: 600; transition: 0.3s; }}
            .tag.active {{ background: var(--sk-navy); color: #fff; box-shadow: 0 4px 12px rgba(26,54,93,0.2); }}

            .property-card {{ margin: 30px 20px; border-radius: 28px; overflow: hidden; background: #fff; box-shadow: 0 12px 30px rgba(0,0,0,0.05); border: 1px solid #edf2f7; }}
            .card-info {{ padding: 25px; }}
            .price {{ font-size: 24px; color: var(--sk-gold); font-weight: 900; }}
            
            .action-bar {{ position: fixed; bottom: 0; left: 50%; transform: translateX(-50%); width: 100%; max-width: 500px; padding: 15px 25px 40px; display: flex; gap: 12px; background: rgba(255,255,255,0.92); backdrop-filter: blur(15px); border-top: 1px solid #f1f1f1; z-index: 999; }}
            .btn {{ flex: 1; text-align: center; padding: 18px; border-radius: 20px; text-decoration: none; font-weight: 800; color: #fff; font-size: 15px; }}
            .btn-call {{ background: #1A202C; }}
            .btn-line {{ background: #00B900; }}
            
            .back-btn {{ position: absolute; top: 25px; left: 25px; background: #fff; padding: 12px 20px; border-radius: 16px; text-decoration: none; font-weight: 800; color: var(--sk-navy); z-index: 100; box-shadow: 0 5px 15px rgba(0,0,0,0.1); }}
            .btn-ext-link {{ display: block; text-align: center; padding: 16px; background: #fff; color: var(--sk-navy); text-decoration: none; border-radius: 16px; margin-top: 15px; font-weight: 700; border: 1.5px solid #edf2f7; }}
            .advice-box {{ background: #ebf8ff; padding: 22px; border-radius: 20px; margin-bottom: 25px; border-left: 6px solid #3182ce; }}
        </style>
    </head>
    """

def build():
    out = Path(".")
    for p in out.glob("p*"):
        if p.is_dir() and re.match(r'^p\d+$', p.name): shutil.rmtree(p)
    
    cache = {}
    if GEOCACHE_PATH.exists():
        try: cache = json.loads(GEOCACHE_PATH.read_text(encoding="utf-8"))
        except: cache = {}

    res = requests.get(SHEET_CSV_URL)
    res.encoding = 'utf-8-sig'
    reader = csv.DictReader(res.text.splitlines())
    
    items, map_data, regions, types = [], [], set(), set()
    num_re = re.compile(r'[^\d.]')
    
    for i, row in enumerate(reader):
        d = {str(k).strip(): str(v).strip() for k, v in row.items() if k}
        
        # 外部連結偵測
        ext_link = ""
        for val in d.values():
            if str(val).startswith("http") and not any(x in str(val).lower() for x in ['.jpg','.png','.jpeg','.webp']):
                ext_link = val
                break
        
        name = d.get("案名") or next((v for k,v in d.items() if "案名" in k), "")
        if not name or d.get("狀態", "").upper() in ["OFF", "FALSE"]: continue
        
        reg, p_str, use_type, addr = d.get("區域","台中"), d.get("價格","面議"), d.get("用途","住宅"), d.get("地址", "")
        regions.add(reg); types.add(use_type)
        
        img = d.get("圖片網址") or next((v for k,v in d.items() if "圖片" in k), "")
        if img and not img.startswith("http"): img = f"{IMG_BASE}{img.lstrip('/')}"
        if not img: img = "https://placehold.co/800x600?text=SK-L+Premium"
        
        slug = f"p{i}"
        (out/slug).mkdir(exist_ok=True)
        search_addr = addr if addr else f"台中市{name}"
        
        # 座標與留客邏輯
        lat, lng = cache.get(search_addr, {}).get("lat"), cache.get(search_addr, {}).get("lng")
        internal_url = f"./{slug}/"
        map_data.append({"name":name, "url":internal_url, "lat":lat, "lng":lng})

        # 子網頁詳情頁
        ext_btn = f'<a href="{ext_link}" target="_blank" class="btn-ext-link">🌐 查看原始物件網頁 (591/樂屋網)</a>' if ext_link else ""
        detail = f"""
        <div class="container">
            <a href="../" class="back-btn">← 返回列表</a>
            <img src="{img}" style="width:100%;height:460px;object-fit:cover;display:block;">
            <div style="padding:45px 25px;background:#fff;border-radius:40px 40px 0 0;margin-top:-50px;position:relative;z-index:10;">
                <h1 style="font-size:30px;font-weight:900;color:var(--sk-navy);margin:0;">{esc(name)}</h1>
                <div class="price" style="margin-top:10px;">{esc(p_str)}</div>
                <div style="line-height:2.2;color:#4a5568;margin:30px 0;font-size:16px;">{esc(d.get("描述","")).replace('、','<br>• ')}</div>
                
                <div class="advice-box">
                    <strong style="color:#2b6cb0;display:block;margin-bottom:8px;">💡 SK-L 顧問專業點評</strong>
                    此案位於 {esc(reg)} 核心地段，具備極佳保值性。若您想了解該社區近一年的成交實價或貸款條件，歡迎點擊下方 LINE 諮詢，我將為您提供專屬評估報告。
                </div>
                
                {ext_btn}
                <a href="https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(search_addr)}" target="_blank" style="display:block;text-align:center;padding:18px;background:var(--sk-navy);color:#fff;text-decoration:none;border-radius:18px;margin-top:15px;font-weight:700;">📍 開啟 Google 地圖導航</a>
                {LEGAL_FOOTER}
            </div>
            <div class="action-bar"><a href="tel:{MY_PHONE}" class="btn btn-call">致電 SK-L</a><a href="{MY_LINE_URL}" class="btn btn-line">LINE 諮詢</a></div>
        </div>
        """
        (out/slug/"index.html").write_text(f"<!doctype html><html lang='zh-TW'>{get_head(name + ' | ' + reg + '買屋推薦', d.get('描述',''), img)}<body>{detail}</body></html>", encoding="utf-8")
        
        # 首頁卡片
        items.append(f'''
            <div class="property-card" data-region="{esc(reg)}" data-type="{esc(use_type)}" data-price="{num_re.sub('', p_str)}">
                <a href="{internal_url}"><img src="{img}" style="width:100%;height:280px;object-fit:cover;display:block;"></a>
                <div class="card-info">
                    <h4 style="margin:0 0 10px;">{esc(name)}</h4>
                    <div class="price">{esc(p_str)}</div>
                    <div style="font-size:12px;color:#94a3b8;margin-top:5px;">{esc(reg)} • {esc(use_type)}</div>
                    <a href="{internal_url}" style="display:block;text-align:center;margin-top:20px;padding:14px;background:#f8fafc;color:var(--sk-navy);text-decoration:none;font-size:13px;font-weight:700;border-radius:15px;">查看 SK-L 專業建議</a>
                </div>
            </div>
        ''')

    # 寫回快取並生成首頁
    GEOCACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    reg_btns = "".join([f"<button class='tag f-reg' data-val='{esc(r)}' onclick='setTag(this, \"f-reg\")'>{esc(r)}</button>" for r in sorted(regions)])
    type_btns = "".join([f"<button class='tag f-type' data-val='{esc(t)}' onclick='setTag(this, \"f-type\")'>{esc(t)}</button>" for t in sorted(types)])
    
    home_html = f"""<div class="container"><div class="hero"><div class="hero-content"><h2>{esc(SITE_TITLE)}</h2><p>Curated Properties • Professional Consulting</p></div></div><div class="map-box"><div id="map"></div></div><div class="filter-section"><div class="filter-group"><button class="tag f-reg active" data-val="all" onclick="setTag(this, 'f-reg')">全部地區</button>{reg_btns}</div><div class="filter-group" style="margin-top:12px;"><button class="tag f-type active" data-val="all" onclick="setTag(this, 'f-type')">所有用途</button>{type_btns}</div><div class="filter-group" style="margin-top:12px; border-top:1px solid #edf2f7; padding-top:20px;"><button class="tag f-sort active" data-val="none" onclick="setTag(this, 'f-sort')">預設排序</button><button class="tag f-sort" data-val="high" onclick="setTag(this, 'f-sort')">價格：高至低</button><button class="tag f-sort" data-val="low" onclick="setTag(this, 'f-sort')">價格：低至高</button></div></div><div id="list">{''.join(items)}</div>{LEGAL_FOOTER}<div class="action-bar"><a href="tel:{MY_PHONE}" class="btn btn-call">致電 SK-L</a><a href="{MY_LINE_URL}" class="btn btn-line">LINE 諮詢</a></div></div>"""
    (out/"index.html").write_text(f"<!doctype html><html lang='zh-TW'>{get_head(SITE_TITLE, is_home=True, map_data_json=json.dumps(map_data, ensure_ascii=False))}<body>{home_html}</body></html>", encoding="utf-8")

if __name__ == "__main__": build()
