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
from datetime import datetime, timezone

# ============================================================
# 1. 核心品牌與技術配置
# ============================================================
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQShAl0-TbUU0MQdYVe53im2T6lXQgh_7g-bdL6HHpIBFtA2yfIAMbPw4J9RgZUkROb9AAiMhnRC0kH/pub?output=csv"
BASE_URL = "https://shihkailin.github.io/taichung-houses"

SITE_TITLE = "SK-L 大台中房地產"
SITE_SLOGAN = "林世塏｜專業顧問 · 誠信置產 · 台中精選房產"
GA4_ID = "G-B7WP9BTP8X"

MY_NAME = "林世塏"
MY_PHONE = "0938-615-351"
MY_LINE_ID = "@494zavsl" # 參考截圖中的 LINE ID 格式
MY_LINE_URL = "https://line.me/ti/p/FDsMyAYDv"

# 地圖與座標系統
MAPS_API_KEY = os.getenv("MAPS_API_KEY", "").strip()
GEOCACHE_PATH = Path("geocache.json")

# 靜態資源
IMG_RAW_BASE = "https://raw.githubusercontent.com/ShihKaiLin/taichung-houses/main/images/"
DEFAULT_HERO = f"{IMG_RAW_BASE}hero_bg.jpg"

# ============================================================
# 2. 進階邏輯引擎 (Logic Helpers)
# ============================================================
def esc(s): return html.escape(str(s or "").strip())
def norm(s): return str(s or "").strip().replace("\ufeff", "")

def safe_slug(label: str) -> str:
    return urllib.parse.quote(norm(label), safe="") if label else "unknown"

def split_tags(s):
    if not s: return []
    return [p.strip() for p in re.split(r"[、,，;；\|\｜/\\\n\r]+", str(s)) if p.strip()]

def get_pure_price(p_str):
    nums = re.findall(r'\d+', str(p_str).replace(',', ''))
    return float(nums[0]) if nums else 0

def get_price_bucket(price_num):
    if price_num == 0: return "面議"
    if price_num < 800: return "800萬以下"
    if price_num < 1500: return "800-1500萬"
    if price_num < 2500: return "1500-2500萬"
    return "2500萬以上"

def normalize_imgs(img_field):
    if not img_field: return ["https://placehold.co/900x600?text=SK-L+Property"]
    raw_list = re.split(r'[|｜]+', str(img_field))
    urls = []
    for img in raw_list:
        img = img.strip()
        if not img: continue
        urls.append(img if img.startswith("http") else f"{IMG_RAW_BASE}{img.lstrip('/')}")
    return urls if urls else [DEFAULT_HERO]

# ============================================================
# 3. 究極 UI 設計系統 (The Visual Engine)
# ============================================================
def get_head(title, desc="", og_img="", is_home=False, map_data=None):
    seo_desc = esc(desc)[:120] if desc else esc(SITE_SLOGAN)
    og_img = og_img if (og_img and str(og_img).startswith("http")) else DEFAULT_HERO
    
    # 地圖數據轉為 JS 物件，避免 f-string 混淆
    map_json = json.dumps(map_data, ensure_ascii=False) if map_data else "[]"
    
    # 修正 SyntaxError: 在 f-string 內，CSS/JS 的大括號必須寫成 {{ 和 }}
    return f"""<head>
    <meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=0">
    <title>{esc(title)}</title>
    <meta name="description" content="{seo_desc}">
    <meta property="og:image" content="{esc(og_img)}">
    <script async src="https://www.googletagmanager.com/gtag/js?id={GA4_ID}"></script>
    <script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','{GA4_ID}');</script>
    <style>
        :root {{ --navy: #1A365D; --gold: #C5A059; --light: #F8FAFC; --shadow: 0 10px 40px rgba(0,0,0,0.06); }}
        body {{ font-family: 'PingFang TC', sans-serif; margin: 0; background: #fff; color: #2D3748; -webkit-font-smoothing: antialiased; }}
        .container {{ max-width: 540px; margin: auto; min-height: 100vh; position: relative; box-shadow: 0 0 60px rgba(0,0,0,0.05); }}
        
        /* 頂部導航 */
        .header {{ background: var(--navy); color: #fff; padding: 15px 20px; display: flex; justify-content: space-between; align-items: center; position: sticky; top: 0; z-index: 1000; }}
        .logo {{ font-weight: 900; letter-spacing: 2px; text-decoration: none; color: #fff; font-size: 18px; }}

        /* 地圖區域 */
        #map {{ height: 350px; background: #eee; width: 100%; border-bottom: 5px solid #fff; }}
        
        /* 過濾標籤 */
        .filters {{ padding: 20px 16px 10px; overflow-x: auto; display: flex; gap: 8px; scrollbar-width: none; }}
        .tag {{ padding: 8px 16px; border-radius: 50px; background: var(--light); border: 1px solid #e2e8f0; font-size: 13px; font-weight: 700; cursor: pointer; white-space: nowrap; transition: 0.3s; }}
        .tag.active {{ background: var(--navy); color: #fff; border-color: var(--navy); }}

        /* 物件網格：雙路並進 */
        .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; padding: 16px; }}
        .card {{ border-radius: 20px; overflow: hidden; background: #fff; box-shadow: var(--shadow); border: 1px solid #f1f5f9; text-decoration: none; color: inherit; display: flex; flex-direction: column; }}
        .card img {{ width: 100%; height: 150px; object-fit: cover; background: #f1f5f9; }}
        .card-body {{ padding: 12px; flex-grow: 1; }}
        .card-title {{ font-size: 14px; font-weight: 800; color: var(--navy); margin: 0; line-height: 1.4; height: 40px; overflow: hidden; }}
        .card-price {{ color: var(--gold); font-weight: 900; font-size: 17px; margin-top: 8px; }}

        /* 詳情頁 UI */
        .slider {{ display: flex; overflow-x: auto; scroll-snap-type: x mandatory; height: 400px; background: #000; scrollbar-width: none; }}
        .slider img {{ flex: 0 0 100%; scroll-snap-align: start; object-fit: cover; }}
        .info-box {{ padding: 30px 20px; background: #fff; border-radius: 35px 35px 0 0; margin-top: -35px; position: relative; z-index: 20; }}
        .spec-badge {{ display: inline-block; background: #f1f5f9; padding: 6px 12px; border-radius: 8px; font-size: 12px; color: #64748b; margin: 0 5px 8px 0; font-weight: 700; }}
        
        /* 聯絡資訊側欄 (仿截圖樣式) */
        .contact-sidebar {{ background: #fff; border: 1px solid #edf2f7; border-radius: 20px; padding: 25px; margin: 20px 0; box-shadow: var(--shadow); }}
        .agent-info {{ display: flex; align-items: center; gap: 15px; margin-bottom: 20px; }}
        .agent-photo {{ width: 60px; height: 60px; border-radius: 50%; object-fit: cover; border: 2px solid var(--navy); }}
        .btn-line {{ display: block; text-align: center; background: #00B900; color: #fff; text-decoration: none; padding: 15px; border-radius: 12px; font-weight: 900; margin-top: 15px; }}

        /* 行動 Bar */
        .action-bar {{ position: fixed; bottom: 0; left: 50%; transform: translateX(-50%); width: 100%; max-width: 540px; padding: 15px 20px 35px; display: flex; gap: 10px; background: rgba(255,255,255,0.95); backdrop-filter: blur(15px); border-top: 1px solid #f1f1f1; z-index: 1000; }}
        .btn {{ flex: 1; text-align: center; padding: 16px; border-radius: 15px; text-decoration: none; font-weight: 900; color: #fff; font-size: 15px; }}
    </style>
    {f"<script src='https://maps.googleapis.com/maps/api/js?key={MAPS_API_KEY}'></script>" if is_home and MAPS_API_KEY else ""}
    <script>
        const mapData = {map_json};
        function initMap() {{
            const mapEl = document.getElementById('map');
            if(!mapEl || typeof google === 'undefined') return;
            const map = new google.maps.Map(mapEl, {{ center: {{lat:24.162, lng:120.647}}, zoom: 12, disableDefaultUI: true, zoomControl: true }});
            const infoWindow = new google.maps.InfoWindow();
            mapData.forEach(loc => {{
                if(!loc.lat) return;
                const marker = new google.maps.Marker({{ position: {{lat:loc.lat, lng:loc.lng}}, map: map, title: loc.name }});
                marker.addListener('click', () => {{
                    infoWindow.setContent(`<div style="padding:10px;width:180px;"><h4 style="margin:0;color:#1A365D;">${{loc.name}}</h4><div style="color:#C5A059;font-weight:900;margin:5px 0;">${{loc.price}}</div><a href="${{loc.url}}" style="display:block;text-align:center;background:#1A365D;color:#fff;text-decoration:none;padding:8px;border-radius:8px;font-size:12px;">查看詳情</a></div>`);
                    infoWindow.open(map, marker);
                }});
            }});
        }}
        function filter(area) {{
            document.querySelectorAll('.tag').forEach(t => t.classList.remove('active'));
            event.target.classList.add('active');
            document.querySelectorAll('.card').forEach(c => {{
                c.style.display = (area === 'all' || c.dataset.area === area) ? 'block' : 'none';
            }});
        }}
        window.onload = initMap;
    </script>
    </head>"""

# ============================================================
# 4. 建置引擎 (The Build Engine)
# ============================================================
def build():
    root = Path(".")
    # 初始化
    for p in root.glob("p*"):
        if p.is_dir() and re.match(r'^p\d+$', p.name): shutil.rmtree(p)
    
    # 快取處理 (修正 TypeError)
    geocache = {}
    if GEOCACHE_PATH.exists():
        try:
            raw_cache = json.loads(GEOCACHE_PATH.read_text(encoding="utf-8"))
            if isinstance(raw_cache, dict): geocache = raw_cache
        except: pass

    res = requests.get(SHEET_CSV_URL); res.encoding = "utf-8-sig"
    reader = csv.DictReader(res.text.splitlines())
    
    all_items, map_data, regions = [], [], set()

    for i, row in enumerate(reader):
        d = {norm(k): norm(v) for k, v in row.items() if k}
        if d.get("狀態", "").upper() in ["OFF", "FALSE"]: continue
        if not d.get("案名"): continue
        
        name, reg, price = d["案名"], d.get("區域", "台中"), d.get("價格", "面議")
        imgs = normalize_imgs(d.get("圖片網址", ""))
        slug = f"p{i}"
        (root / slug).mkdir(exist_ok=True)
        regions.add(reg)

        # 座標快取邏輯
        addr = d.get("地址", f"台中市{reg}{name}")
        lat, lng = geocache.get(addr, {}).get("lat"), geocache.get(addr, {}).get("lng")
        if lat: map_data.append({"name": name, "price": price, "url": f"./{slug}/", "lat": lat, "lng": lng, "img": imgs[0]})

        # 格局標籤 (參考截圖精華)
        specs = [f"📍 {reg}", f"🏠 {d.get('用途','住宅')}"]
        if d.get("格局"): specs.append(f"🛏️ {d['格局']}")
        if d.get("坪數"): specs.append(f"📐 {d['坪數']}坪")

        # 生成詳情頁
        slides = "".join([f'<img src="{u}" loading="lazy">' for u in imgs])
        detail_html = f"""<div class="container">
            <div class="header"><a href="../" class="logo">← {SITE_TITLE}</a></div>
            <div class="slider">{slides}</div>
            <div class="info-box">
                <h1 style="font-size:28px;font-weight:900;color:var(--navy);margin:0 0 10px;">{esc(name)}</h1>
                <div style="font-size:32px;color:var(--gold);font-weight:900;margin-bottom:20px;">{esc(price)}</div>
                <div style="margin-bottom:25px;">{" ".join([f'<span class="spec-badge">{esc(s)}</span>' for s in specs])}</div>
                <div style="line-height:2.2;font-size:16px;color:#4a5568;">{esc(d.get('描述')).replace('、','<br>• ')}</div>
                
                <div class="contact-sidebar">
                    <div class="agent-info">
                        <img src="{IMG_RAW_BASE}agent_photo.jpg" class="agent-photo">
                        <div><strong style="font-size:18px;">{esc(MY_NAME)}</strong><br><span style="font-size:12px;color:#94a3b8;">專業房產顧問</span></div>
                    </div>
                    <div style="font-size:14px;color:#4a5568;line-height:1.6;">想了解此案「成交行情」或「貸款成數」？請點擊下方直接諮詢。</div>
                    <a href="{MY_LINE_URL}" class="btn-line">💬 加 LINE 諮詢 (ID: {MY_LINE_ID})</a>
                </div>
                <a href="http://maps.google.com/?q={urllib.parse.quote(addr)}" target="_blank" style="display:block;text-align:center;padding:18px;background:var(--navy);color:#fff;text-decoration:none;border-radius:15px;font-weight:900;margin-top:20px;">📍 在地圖上開啟導航</a>
                <div style="margin-top:60px;text-align:center;color:#cbd5e0;font-size:11px;">英柏國際地產有限公司｜經紀人：王一媖 (103) 中市經紀字第 00678 號</div>
            </div>
            <div class="action-bar"><a class="btn" style="background:#111827;" href="tel:{MY_PHONE}">📞 直接致電</a><a class="btn" style="background:#00B900;" href="{MY_LINE_URL}">💬 LINE 諮詢</a></div>
        </div>"""
        (root / slug / "index.html").write_text(f"<!doctype html><html lang='zh-TW'>{get_head(name, d.get('描述'), imgs[0])}<body>{detail_html}</body></html>", encoding="utf-8")

        all_items.append({"name": name, "area": reg, "price": price, "img": imgs[0], "url": f"./{slug}/"})

    # 生成首頁
    reg_btns = "".join([f'<button class="tag" onclick="filter(\'{a}\')">{a}</button>' for a in sorted(regions)])
    home_cards = "".join([f"""<a href="{it['url']}" class="card" data-area="{it['area']}"><img src="{it['img']}"><div class="card-body"><h3 class="card-title">{it['name']}</h3><div class="card-price">{it['price']}</div></div></a>""" for it in all_items[::-1]])
    
    home_html = f"""<div class="container">
        <div class="header"><a href="./" class="logo">{SITE_TITLE}</a><span style="font-size:12px;opacity:0.8;">{SITE_SLOGAN}</span></div>
        <div id="map"></div>
        <div class="filters"><button class="tag active" onclick="filter('all')">全部區域</button>{reg_btns}</div>
        <div class="grid">{home_cards}</div>
        <div style="padding:60px 20px 100px;text-align:center;color:#cbd5e0;font-size:11px;">英柏國際地產有限公司｜© 2026 SK-L Branding</div>
        <div class="action-bar"><a class="btn" style="background:#111827;" href="tel:{MY_PHONE}">📞 直接致電</a><a class="btn" style="background:#00B900;" href="{MY_LINE_URL}">💬 LINE 諮詢</a></div>
    </div>"""
    (root / "index.html").write_text(f"<!doctype html><html lang='zh-TW'>{get_head(SITE_TITLE, is_home=True, map_data=map_data)}<body>{home_html}</body></html>", encoding="utf-8")

    print(f"✅ 建置完成！共處理 {len(all_items)} 個物件。")

if __name__ == "__main__": build()
