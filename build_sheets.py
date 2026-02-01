import os, csv, requests, html, shutil, re, urllib.parse, json
from pathlib import Path
from datetime import datetime

# ============================================================
# 1. 核心配置 (修正 404 與 品牌設定)
# ============================================================
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQShAl0-TbUU0MQdYVe53im2T6lXQgh_7g-bdL6HHpIBFtA2yfIAMbPw4J9RgZUkROb9AAiMhnRC0kH/pub?output=csv"
PROJECT_NAME = "taichung-houses"
BASE_URL = f"https://shihkailin.github.io/{PROJECT_NAME}"
SITE_TITLE, SITE_SLOGAN = "SK-L 大台中房地產", "林世塏｜專業顧問 · 誠信置產 · 台中精選房產"
GA4_ID = "G-B7WP9BTP8X"
MY_NAME, MY_PHONE, MY_LINE_URL = "林世塏", "0938-615-351", "https://line.me/ti/p/FDsMyAYDv"

# 路徑定義
POSTS_DIR, GEOCACHE_PATH = Path("posts"), Path("geocache.json")
IMG_RAW_BASE = f"https://raw.githubusercontent.com/ShihKaiLin/{PROJECT_NAME}/main/images/"
DEFAULT_HERO = f"{IMG_RAW_BASE}hero_bg.jpg"

# 經紀人資訊 (鎖定側邊欄)
LEGAL_INFO = """
<div style="margin-top:20px; padding-top:15px; border-top:1.5px solid #edf2f7; font-size:11px; color:#718096; line-height:2;">
    📍 英柏國際地產有限公司<br>
    中市地價二字第 1070029259 號<br>
    經紀人：王一媖 (103) 中市經紀字第 00678 號
</div>
"""
MAPS_API_KEY = os.getenv("MAPS_API_KEY", "AIzaSyDzgnI2Ucv622CRkWwo2GE5JRrs_Y4HQY0")

# ============================================================
# 2. 邏輯處理 (強化數據轉換)
# ============================================================
def esc(s): return html.escape(str(s or "").strip())
def norm(s): return str(s or "").strip().replace("\ufeff", "")
def get_num(s): 
    nums = re.findall(r'\d+\.?\d*', str(s).replace(',', ''))
    return float(nums[0]) if nums else 0

def normalize_imgs(f):
    if not f: return [f"https://placehold.co/900x600?text={SITE_TITLE}"]
    raw = re.split(r'[|｜]+', str(f))
    return [i if i.startswith("http") else f"{IMG_RAW_BASE}{i.lstrip('/')}" for i in raw if i.strip()]

def get_head(title, map_data=None, is_home=False):
    map_json = json.dumps(map_data, ensure_ascii=False) if map_data else "[]"
    # 地圖與搜尋 JavaScript 復活
    js = f"""<script src="https://maps.googleapis.com/maps/api/js?key={MAPS_API_KEY}&callback=initMap" async defer></script>
    <script>
        let map;
        function initMap() {{
            const el = document.getElementById('map'); if(!el) return;
            map = new google.maps.Map(el, {{ center: {{lat: 24.16, lng: 120.64}}, zoom: 12, disableDefaultUI: true, zoomControl: true }});
            const infoWindow = new google.maps.InfoWindow();
            const data = {map_json};
            data.forEach(loc => {{
                const marker = new google.maps.Marker({{ position: {{lat: parseFloat(loc.lat), lng: parseFloat(loc.lng)}}, map: map }});
                marker.addListener('click', () => {{
                    infoWindow.setContent(`<div style="padding:10px;width:180px;"><img src="${{loc.img}}" style="width:100%;height:90px;object-fit:cover;border-radius:8px;"><h4 style="margin:8px 0;font-size:14px;">${{loc.name}}</h4><div style="color:#C5A059;font-weight:900;">${{loc.price}}</div><a href="${{loc.url}}" style="display:block;text-align:center;background:#1A365D;color:#fff;padding:10px;border-radius:8px;text-decoration:none;font-size:12px;margin-top:8px;">查看詳細建議 →</a></div>`);
                    infoWindow.open(map, marker);
                }});
            }});
        }}
        function executeSearch() {{
            const area = document.getElementById('s-area').value;
            const type = document.getElementById('s-type').value;
            const minP = parseFloat(document.getElementById('s-min-p').value) || 0;
            const maxP = parseFloat(document.getElementById('s-max-p').value) || 999999;
            const minS = parseFloat(document.getElementById('s-min-s').value) || 0;
            const maxS = parseFloat(document.getElementById('s-max-s').value) || 999999;

            document.querySelectorAll('.card-anchor').forEach(card => {{
                const d = card.dataset;
                const p = parseFloat(d.priceNum);
                const s = parseFloat(d.sizeNum);
                const mArea = (area === 'all' || d.area === area);
                const mType = (type === 'all' || d.type === type);
                const mPrice = (p >= minP && p <= maxP);
                const mSize = (s >= minS && s <= maxS);
                card.style.display = (mArea && mType && mPrice && mSize) ? 'block' : 'none';
            }});
            document.getElementById('list-start').scrollIntoView({{behavior:'smooth'}});
        }}
    </script>""" if is_home else ""

    return f"""<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
    <title>{esc(title)} | {SITE_TITLE}</title>
    <script async src="https://www.googletagmanager.com/gtag/js?id={GA4_ID}"></script>
    <script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','{GA4_ID}');</script>
    {js}
    <style>
        :root {{ --navy: #1A365D; --gold: #C5A059; --green: #27ae60; --gray: #f8fafc; }}
        body {{ font-family: -apple-system, sans-serif; margin: 0; background: #f1f5f9; color: #334155; }}
        .container {{ max-width: 1200px; margin: auto; background: #fff; min-height: 100vh; position: relative; padding-bottom: 160px; }}
        .header {{ background: var(--navy); color: #fff; padding: 18px 20px; display: flex; justify-content: space-between; position: sticky; top:0; z-index:1000; font-weight:900; letter-spacing:1px; }}
        #map {{ height: 400px; background: #e2e8f0; }}
        .search-box {{ padding: 25px; border-bottom: 1px solid #e2e8f0; display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 12px; }}
        .search-item {{ display: flex; flex-direction: column; gap: 5px; }}
        .search-label {{ font-size: 11px; font-weight: 800; color: var(--navy); }}
        .search-select, .search-input {{ padding: 12px; border-radius: 10px; border: 1.5px solid #e2e8f0; background: var(--gray); font-size:14px; outline:none; }}
        .search-btn {{ background: var(--green); color: #fff; border: none; padding: 15px; border-radius: 12px; font-weight: 900; cursor: pointer; grid-column: 1 / -1; margin-top: 10px; }}
        @media (min-width: 768px) {{ .search-btn {{ grid-column: auto; margin-top: 21px; }} }}
        .grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; padding: 15px; }}
        @media (min-width: 768px) {{ .grid {{ grid-template-columns: repeat(4, 1fr); gap: 25px; padding: 30px; }} }}
        .card {{ border-radius: 20px; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.05); border: 1px solid #f1f5f9; display: flex; flex-direction: column; transition: 0.3s; height: 100%; text-decoration: none; color: inherit; }}
        .card img {{ width: 100%; height: 160px; object-fit: cover; }}
        .card-body {{ padding: 15px; flex-grow: 1; }}
        .card-title {{ font-size: 14px; font-weight: 800; color: var(--navy); margin: 0; line-height: 1.5; height: 42px; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }}
        .card-price {{ color: var(--gold); font-weight: 950; font-size: 19px; margin-top: 10px; }}
        .badge {{ display: inline-block; padding: 5px 12px; background: #f1f5f9; border-radius: 50px; font-size: 11px; font-weight: 700; margin: 0 5px 8px 0; }}
        .action-bar {{ position: fixed; bottom: 0; width: 100%; max-width: 1200px; padding: 25px; display: flex; gap: 15px; background: rgba(255,255,255,0.98); backdrop-filter: blur(10px); border-top: 1px solid #f1f5f9; box-sizing: border-box; z-index: 10000; }}
        .btn {{ flex: 1; text-align: center; padding: 18px; border-radius: 18px; text-decoration: none; font-weight: 950; color: #fff; font-size: 16px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); }}
        .btn-call {{ background: #1e293b; }} .btn-line {{ background: #00B900; }}
    </style></head>"""

def build():
    root = Path(".")
    for d in ["area", "life"]: 
        if (root/d).exists(): shutil.rmtree(root/d); (root/d).mkdir()
    for p in root.glob("p*"):
        if p.is_dir() and re.match(r'^p\d+$', p.name): shutil.rmtree(p)

    geocache = {}
    if GEOCACHE_PATH.exists():
        try: geocache = json.loads(GEOCACHE_PATH.read_text(encoding="utf-8"))
        except: pass

    res = requests.get(SHEET_CSV_URL)
    res.encoding = "utf-8-sig"
    reader = list(csv.DictReader(res.text.splitlines()))
    
    all_items, map_data, sitemap_urls = [], [], [f"{BASE_URL}/"]

    for i, row in enumerate(reader):
        d = {norm(k): norm(v) for k, v in row.items() if k}
        if d.get("狀態", "").upper() == "OFF" or not d.get("案名"): continue
        
        slug = f"p{i}"
        (root / slug).mkdir(exist_ok=True)
        item_path, full_item_url = f"/{PROJECT_NAME}/{slug}/", f"{BASE_URL}/{slug}/"
        sitemap_urls.append(full_item_url)
        
        imgs = normalize_imgs(d.get("圖片網址", ""))
        price_val, size_val = d.get("價格", "面議"), d.get("坪數", "0")
        
        # 標記地圖點位
        addr = d.get("地址", f"台中市{d.get('區域')}{d.get('案名')}")
        geo = geocache.get(addr)
        if geo and "lat" in geo:
            map_data.append({"name": d['案名'], "price": price_val, "url": item_path, "lat": geo["lat"], "lng": geo["lng"], "img": imgs[0]})

        # 生成詳情頁 (整合經紀人側欄)
        detail_html = f"""<div class="container">
            <div class="header"><a href="/{PROJECT_NAME}/" style="color:#fff;text-decoration:none;">← {SITE_TITLE}</a></div>
            <img src="{imgs[0]}" style="width:100%;height:350px;object-fit:cover;">
            <div style="padding:25px;">
                <h1 style="color:var(--navy);font-size:28px;font-weight:950;margin-bottom:10px;">{esc(d['案名'])}</h1>
                <div style="font-size:38px;color:var(--gold);font-weight:950;margin-bottom:25px;">{esc(price_val)}</div>
                <div style="margin-bottom:30px;">
                    <span class="badge">📍 {esc(d.get('區域'))}</span>
                    <span class="badge">🏠 {esc(d.get('用途'))}</span>
                    <span class="badge">📐 {esc(size_val)}坪</span>
                    <span class="badge">🛋️ {esc(d.get('格局'))}</span>
                </div>
                <div style="line-height:2.4;color:#475569;background:#f8fafc;padding:30px;border-radius:20px;border:1px solid #edf2f7;font-size:17px;">
                    {esc(d.get('描述','')).replace('、','<br>• ')}
                </div>
                <div style="margin-top:40px;padding:30px;border:1.5px solid #edf2f7;border-radius:25px;background:#fff;box-shadow:0 10px 30px rgba(0,0,0,0.03);">
                    <div style="display:flex;align-items:center;gap:15px;margin-bottom:15px;">
                        <img src="{IMG_RAW_BASE}agent_photo.jpg" style="width:60px;height:60px;border-radius:50%;object-fit:cover;">
                        <strong>{MY_NAME}｜台中置產專業顧問</strong>
                    </div>
                    {LEGAL_INFO}
                    <a href="{MY_LINE_URL}" style="display:block;background:var(--green);color:#fff;padding:18px;margin-top:20px;border-radius:15px;text-decoration:none;font-weight:950;text-align:center;">💬 立即加 LINE 諮詢物件分析</a>
                </div>
            </div>
            <div class="action-bar"><a class="btn btn-call" href="tel:{MY_PHONE}">📞 撥打電話</a><a class="btn btn-line" href="{MY_LINE_URL}">💬 LINE 諮詢</a></div>
        </div>"""
        (root / slug / "index.html").write_text(f"<!doctype html><html lang='zh-TW'>{get_head(d['案名'])}<body>{detail_html}</body></html>", encoding="utf-8")
        
        all_items.append({
            "name": d['案名'], "area": d.get('區域'), "type": d.get('用途'), 
            "price": price_val, "price_num": get_num(price_val), 
            "size_num": get_num(size_val), "img": imgs[0], "url": item_path
        })

    # 生成首頁 (仿淡水房產網格線)
    area_opts = "".join([f'<option value="{a}">{a}</option>' for a in sorted(set(x['area'] for x in all_items if x['area']))])
    home_cards = "".join([f'<a href="{it["url"]}" class="card-anchor" data-area="{it["area"]}" data-type="{it["type"]}" data-price-num="{it["price_num"]}" data-size-num="{it["size_num"]}"><div class="card"><img src="{it["img"]}"><div class="card-body"><h3 class="card-title">{esc(it["name"])}</h3><div class="card-price">{esc(it["price"])}</div><div style="margin-top:10px;font-size:11px;color:var(--navy);font-weight:800;">查看分析建議 →</div></div></div></a>' for it in all_items[::-1]])
    
    home_html = f"""<div class="container">
        <div class="header"><div>{SITE_TITLE}</div></div>
        <div id="map"></div>
        <div class="search-box">
            <div class="search-item"><label class="search-label">行政區域</label><select class="search-select" id="s-area"><option value="all">不限區域</option>{area_opts}</select></div>
            <div class="search-item"><label class="search-label">物件類型</label><select class="search-select" id="s-type"><option value="all">不限類型</option><option value="透天">透天/別墅</option><option value="大樓">電梯大樓</option><option value="土地">土地/農地</option></select></div>
            <div class="search-item"><label class="search-label">預算(萬)</label><div style="display:flex;gap:5px;"><input class="search-input" id="s-min-p" placeholder="最低"> <input class="search-input" id="s-max-p" placeholder="最高"></div></div>
            <div class="search-item"><label class="search-label">坪數</label><div style="display:flex;gap:5px;"><input class="search-input" id="s-min-s" placeholder="最少"> <input class="search-input" id="s-max-s" placeholder="最多"></div></div>
            <button class="search-btn" onclick="executeSearch()">🔍 開始篩選台中物件</button>
        </div>
        <div id="list-start"></div><div class="grid">{home_cards}</div>
        <div class="action-bar"><a class="btn btn-call" href="tel:{MY_PHONE}">📞 立即撥打</a><a class="btn btn-line" href="{MY_LINE_URL}">💬 LINE 諮詢</a></div>
    </div>"""
    (root / "index.html").write_text(f"<!doctype html><html lang='zh-TW'>{get_head(SITE_TITLE, is_home=True, map_data=map_data)}<body>{home_html}</body></html>", encoding="utf-8")

    # Sitemap
    (root / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + "".join([f'<url><loc>{u}</loc></url>' for u in sitemap_urls]) + '</urlset>', encoding="utf-8")
    print(f"✅ 旗艦 11.0 建置完成！地圖點位：{len(map_data)}")

if __name__ == "__main__": build()
