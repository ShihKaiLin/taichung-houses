import os
import csv
import requests
import html
import shutil
import re
import urllib.parse
import json
from pathlib import Path
from datetime import datetime

# ============================================================
# 1. 核心品牌與路徑配置 (解決 404 與 Actions 故障)
# ============================================================
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQShAl0-TbUU0MQdYVe53im2T6lXQgh_7g-bdL6HHpIBFtA2yfIAMbPw4J9RgZUkROb9AAiMhnRC0kH/pub?output=csv"
PROJECT_NAME = "taichung-houses"
BASE_URL = f"https://shihkailin.github.io/{PROJECT_NAME}"

# 基礎資訊
SITE_TITLE = "SK-L 大台中房地產"
SITE_SLOGAN = "林世塏｜專業顧問 · 誠信置產 · 台中精選房產"
GA4_ID = "G-B7WP9BTP8X"
MY_NAME = "林世塏"
MY_PHONE = "0938-615-351"
MY_LINE_URL = "https://line.me/ti/p/FDsMyAYDv"

# 路徑定義 (修正故障點)
POSTS_DIR = Path("posts")
GEOCACHE_PATH = Path("geocache.json")
IMG_RAW_BASE = f"https://raw.githubusercontent.com/ShihKaiLin/{PROJECT_NAME}/main/images/"
DEFAULT_HERO = f"{IMG_RAW_BASE}hero_bg.jpg"

# 經紀人法規資訊 (鎖定在詳情頁，仿淡水房產網佈局)
LEGAL_FOOTER_HTML = """
<div style="margin-top: 18px; padding-top: 15px; border-top: 1.5px solid #edf2f7; font-size: 11px; color: #718096; line-height: 2.0;">
    📍 英柏國際地產有限公司<br>
    中市地價二字第 1070029259 號<br>
    經紀人：王一媖 (103) 中市經紀字第 00678 號
</div>
"""

MAPS_API_KEY = os.getenv("MAPS_API_KEY", "AIzaSyDzgnI2Ucv622CRkWwo2GE5JRrs_Y4HQY0")

# ============================================================
# 2. 邏輯工具引擎
# ============================================================
def esc(s): return html.escape(str(s or "").strip())
def norm(s): return str(s or "").strip().replace("\ufeff", "")
def get_num(s):
    nums = re.findall(r'\d+\.?\d*', str(s).replace(',', ''))
    return float(nums[0]) if nums else 0

def normalize_imgs(img_field):
    if not img_field: return ["https://placehold.co/900x600?text=SK-L+Property"]
    raw_list = re.split(r'[|｜]+', str(img_field))
    urls = []
    for img in raw_list:
        img = img.strip()
        if not img: continue
        urls.append(img if img.startswith("http") else f"{IMG_RAW_BASE}{img.lstrip('/')}")
    return urls if urls else [DEFAULT_HERO]

def get_head(title, desc="", og_img="", is_home=False, map_data=None):
    og_img = og_img if (og_img and str(og_img).startswith("http")) else DEFAULT_HERO
    map_json = json.dumps(map_data, ensure_ascii=False) if map_data else "[]"
    
    # 解決地圖故障：使用 replace 避免 f-string 衝突
    map_js = f"""<script src="https://maps.googleapis.com/maps/api/js?key={MAPS_API_KEY}&callback=initMap" async defer></script>
    <script>
        let map;
        function initMap() {{
            const el = document.getElementById('map'); if(!el) return;
            const data = {map_json};
            map = new google.maps.Map(el, {{ center: {{lat: 24.162, lng: 120.647}}, zoom: 12, disableDefaultUI: true, zoomControl: true }});
            const infoWindow = new google.maps.InfoWindow();
            data.forEach(loc => {{
                const marker = new google.maps.Marker({{ position: {{lat: parseFloat(loc.lat), lng: parseFloat(loc.lng)}}, map: map }});
                marker.addListener('click', () => {{
                    infoWindow.setContent(`<div style="padding:10px;width:180px;"><div style="background:url('${{loc.img}}') center/cover;height:90px;border-radius:8px;"></div><h4 style="margin:5px 0;font-size:14px;">${{loc.name}}</h4><div style="color:#C5A059;font-weight:900;">${{loc.price}}</div><a href="${{loc.url}}" style="display:block;text-align:center;background:#1A365D;color:#fff;padding:8px;border-radius:5px;text-decoration:none;font-size:12px;margin-top:5px;">查看分析 →</a></div>`);
                    infoWindow.open(map, marker);
                }});
            }});
        }}
        function executeSearch() {{
            const area = document.getElementById('s-area').value;
            const type = document.getElementById('s-type').value;
            const rooms = document.getElementById('s-rooms').value;
            document.querySelectorAll('.card-anchor').forEach(card => {{
                const d = card.dataset;
                const matchesArea = (area === 'all' || d.area === area);
                const matchesType = (type === 'all' || d.type === type);
                const matchesRooms = (rooms === 'all' || d.rooms.includes(rooms));
                card.style.display = (matchesArea && matchesType && matchesRooms) ? 'block' : 'none';
            }});
            document.getElementById('list-start').scrollIntoView({{behavior: 'smooth'}});
        }}
    </script>""" if is_home else ""

    return f"""<head>
    <meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
    <title>{esc(title)}</title>
    <script async src="https://www.googletagmanager.com/gtag/js?id={GA4_ID}"></script>
    <script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','{GA4_ID}');</script>
    {map_js}
    <style>
        :root {{ --navy: #1A365D; --gold: #C5A059; --green: #27ae60; }}
        body {{ font-family: sans-serif; margin: 0; background: #f4f7f9; }}
        .container {{ max-width: 1200px; margin: auto; background: #fff; min-height: 100vh; padding-bottom: 150px; position: relative; }}
        .header {{ background: var(--navy); color: #fff; padding: 15px 20px; display: flex; justify-content: space-between; align-items: center; position: sticky; top: 0; z-index: 1000; }}
        #map {{ height: 400px; background: #eee; }}
        .search-box {{ padding: 20px; border-bottom: 1px solid #eee; display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; }}
        .search-select {{ padding: 10px; border-radius: 8px; border: 1px solid #ddd; }}
        .search-btn {{ background: var(--green); color: #fff; border: none; padding: 10px; border-radius: 8px; font-weight: 900; cursor: pointer; }}
        .grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; padding: 15px; }}
        @media (min-width: 768px) {{ .grid {{ grid-template-columns: repeat(4, 1fr); }} }}
        .card {{ border-radius: 15px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.05); border: 1px solid #eee; height: 100%; display: flex; flex-direction: column; }}
        .card img {{ width: 100%; height: 150px; object-fit: cover; }}
        .card-body {{ padding: 12px; flex-grow: 1; }}
        .card-title {{ font-size: 14px; font-weight: 800; color: var(--navy); margin: 0; height: 40px; overflow: hidden; }}
        .card-price {{ color: var(--gold); font-weight: 900; font-size: 18px; margin-top: 10px; }}
        .spec-badge {{ display: inline-block; padding: 4px 10px; background: #f1f5f9; border-radius: 20px; font-size: 11px; margin: 0 5px 5px 0; }}
        .action-bar {{ position: fixed; bottom: 0; width: 100%; max-width: 1200px; padding: 20px; display: flex; gap: 10px; background: #fff; border-top: 1px solid #eee; z-index: 10000; box-sizing: border-box; }}
        .btn {{ flex: 1; text-align: center; padding: 15px; border-radius: 12px; text-decoration: none; font-weight: 900; color: #fff; }}
        .btn-call {{ background: var(--navy); }} .btn-line {{ background: var(--green); }}
    </style></head>"""

def build():
    root = Path(".")
    # 初始化
    for d in ["area", "life"]: 
        if (root/d).exists(): shutil.rmtree(root/d)
        (root/d).mkdir(exist_ok=True)
    for p in root.glob("p*"):
        if p.is_dir() and re.match(r'^p\d+$', p.name): shutil.rmtree(p)

    # 座標快取
    geocache = {}
    if GEOCACHE_PATH.exists():
        try: geocache = json.loads(GEOCACHE_PATH.read_text(encoding="utf-8"))
        except: pass

    # 抓取試算表
    res = requests.get(SHEET_CSV_URL)
    res.encoding = "utf-8-sig"
    reader = list(csv.DictReader(res.text.splitlines()))
    
    all_items, map_data, sitemap_urls = [], [], [f"{BASE_URL}/"]

    for i, row in enumerate(reader):
        d = {norm(k): norm(v) for k, v in row.items() if k}
        if d.get("狀態", "").upper() == "OFF" or not d.get("案名"): continue
        
        slug = f"p{i}"
        (root / slug).mkdir(exist_ok=True)
        item_path = f"/{PROJECT_NAME}/{slug}/"
        sitemap_urls.append(f"{BASE_URL}/{slug}/")
        
        imgs = normalize_imgs(d.get("圖片網址", ""))
        price = d.get("價格", "面議")
        
        # 座標處理
        addr = d.get("地址", f"台中市{d.get('區域')}{d.get('案名')}")
        geo = geocache.get(addr)
        if geo and "lat" in geo:
            map_data.append({"name": d['案名'], "price": price, "url": item_path, "lat": geo["lat"], "lng": geo["lng"], "img": imgs[0]})

        # 生成詳情頁
        detail_html = f"""<div class="container">
            <div class="header"><a href="/{PROJECT_NAME}/" style="color:#fff;text-decoration:none;">← {SITE_TITLE}</a></div>
            <img src="{imgs[0]}" style="width:100%;height:300px;object-fit:cover;">
            <div style="padding:20px;">
                <h1 style="color:var(--navy);">{esc(d['案名'])}</h1>
                <div style="font-size:32px;color:var(--gold);font-weight:900;">{esc(price)}</div>
                <div style="margin:20px 0;">
                    <span class="spec-badge">📍 {esc(d.get('區域'))}</span>
                    <span class="spec-badge">🏠 {esc(d.get('用途'))}</span>
                    <span class="spec-badge">📐 {esc(d.get('坪數'))}坪</span>
                </div>
                <div style="line-height:2;color:#444;background:#f9f9f9;padding:20px;border-radius:10px;">
                    {esc(d.get('描述','')).replace('、','<br>• ')}
                </div>
                <div style="margin-top:30px;padding:20px;border:1px solid #eee;border-radius:15px;text-align:center;">
                    <strong>{MY_NAME}｜專業房產顧問</strong>
                    {LEGAL_FOOTER_HTML}
                    <a href="{MY_LINE_URL}" style="display:block;background:var(--green);color:#fff;padding:15px;margin-top:15px;border-radius:10px;text-decoration:none;font-weight:900;">💬 加 LINE 諮詢詳情</a>
                </div>
            </div>
            <div class="action-bar"><a class="btn btn-call" href="tel:{MY_PHONE}">📞 撥打電話</a><a class="btn btn-line" href="{MY_LINE_URL}">💬 LINE 諮詢</a></div>
        </div>"""
        (root / slug / "index.html").write_text(f"<!doctype html><html>{get_head(d['案名'])}<body>{detail_html}</body></html>", encoding="utf-8")
        
        all_items.append({"name": d['案名'], "area": d.get('區域'), "type": d.get('用途'), "rooms": d.get('格局'), "price": price, "price_num": get_num(price), "img": imgs[0], "url": item_path})

    # 首頁
    home_cards = "".join([f'<a href="{it["url"]}" class="card-anchor" data-area="{it["area"]}" data-type="{it["type"]}" data-rooms="{it["rooms"]}"><div class="card"><img src="{it["img"]}"><div class="card-body"><h3 class="card-title">{esc(it["name"])}</h3><div class="card-price">{esc(it["price"])}</div></div></div></a>' for it in all_items[::-1]])
    home_html = f"""<div class="container">
        <div class="header"><div class="logo">{SITE_TITLE}</div></div>
        <div id="map"></div>
        <div class="search-box">
            <select class="search-select" id="s-area"><option value="all">所有區域</option>{"".join([f'<option value="{a}">{a}</option>' for a in sorted(set(x['area'] for x in all_items if x['area']))])}</select>
            <select class="search-select" id="s-type"><option value="all">所有類型</option><option value="透天">透天</option><option value="大樓">大樓</option></select>
            <button class="search-btn" onclick="executeSearch()">🔍 搜尋物件</button>
        </div>
        <div id="list-start"></div><div class="grid">{home_cards}</div>
        <div class="action-bar"><a class="btn btn-call" href="tel:{MY_PHONE}">📞 撥打電話</a><a class="btn btn-line" href="{MY_LINE_URL}">💬 LINE 諮詢</a></div>
    </div>"""
    (root / "index.html").write_text(f"<!doctype html><html>{get_head(SITE_TITLE, is_home=True, map_data=map_data)}<body>{home_html}</body></html>", encoding="utf-8")

    # Sitemap
    (root / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + "".join([f'<url><loc>{u}</loc></url>' for u in sitemap_urls]) + '</urlset>', encoding="utf-8")
    print("✅ 建置成功！")

if __name__ == "__main__": build()
