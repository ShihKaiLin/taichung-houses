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
# 1. 核心品牌與技術配置 (SEO & Pathing)
# ============================================================
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQShAl0-TbUU0MQdYVe53im2T6lXQgh_7g-bdL6HHpIBFtA2yfIAMbPw4J9RgZUkROb9AAiMhnRC0kH/pub?output=csv"

# 重要：修正 404 問題與資源路徑
PROJECT_NAME = "taichung-houses"
BASE_URL = f"https://shihkailin.github.io/{PROJECT_NAME}"

SITE_TITLE = "SK-L 大台中房地產"
SITE_SLOGAN = "林世塏｜專業顧問 · 誠信置產 · 台中精選房產"
GA4_ID = "G-B7WP9BTP8X"

MY_NAME = "林世塏"
MY_PHONE = "0938-615-351"
MY_LINE_URL = "https://line.me/ti/p/FDsMyAYDv"

# Google Maps API 與座標快取
MAPS_API_KEY = os.getenv("MAPS_API_KEY", "AIzaSyDzgnI2Ucv622CRkWwo2GE5JRrs_Y4HQY0")
GEOCACHE_PATH = Path("geocache.json")

# 資源與 Markdown 路徑
IMG_RAW_BASE = f"https://raw.githubusercontent.com/ShihKaiLin/{PROJECT_NAME}/main/images/"
DEFAULT_HERO = f"{IMG_RAW_BASE}hero_bg.jpg"
POSTS_DIR = Path("posts")

# SEO 分類目錄
CATEGORY_DIRS = ["area", "feature", "price", "life", "agent"]

# --- 修正後的法律頁尾：字體統一、縮小、位置不被按鈕遮擋 ---
LEGAL_FOOTER_HTML = f"""
<div class="sk-legal-footer">
    <div class="sk-footer-inner" style="font-size: 11px; line-height: 2.0; color: #718096; letter-spacing: 1px;">
        英柏國際地產有限公司<br>
        中市地價二字第 1070029259 號<br>
        王一媖 經紀人（103）中市經紀字第 00678 號<br>
        專業誠信 · 卓越服務 · 深耕台中房產
        <div style="margin-top: 15px; color: #cbd5e0;">© 2026 SK-L Branding. All Rights Reserved.</div>
    </div>
</div>
"""

# ============================================================
# 2. 進階邏輯引擎
# ============================================================
def esc(s): return html.escape(str(s or "").strip())
def norm(s): return str(s or "").strip().replace("\ufeff", "")
def safe_slug(label: str) -> str: return urllib.parse.quote(norm(label), safe="") if label else "unknown"

def split_tags(s):
    if not s: return []
    return [p.strip() for p in re.split(r"[、,，;；\|\｜/\\\n\r]+", str(s)) if p.strip()]

def get_num(s):
    """ 從字串提取數字，供搜尋過濾使用 """
    nums = re.findall(r'\d+\.?\d*', str(s).replace(',', ''))
    return float(nums[0]) if nums else 0

def get_price_bucket(price_num):
    if price_num == 0: return "面議"
    if price_num < 1500: return "1500萬以下"
    if price_num < 3000: return "1500-3000萬"
    return "3000萬以上"

def normalize_imgs(img_field):
    if not img_field: return ["https://placehold.co/900x600?text=SK-L+Property"]
    raw_list = re.split(r'[|｜]+', str(img_field))
    urls = []
    for img in raw_list:
        img = img.strip()
        if not img: continue
        urls.append(img if img.startswith("http") else f"{IMG_RAW_BASE}{img.lstrip('/')}")
    return urls if urls else [DEFAULT_HERO]

def md_to_html(md: str):
    lines = (md or "").replace("\r\n", "\n").split("\n")
    out = []
    in_list = False
    for line in lines:
        raw = line.strip()
        if not raw:
            if in_list: out.append("</ul>"); in_list = False
            continue
        if raw.startswith("#"):
            level = max(1, min(len(raw) - len(raw.lstrip("#")), 3))
            out.append(f"<h{level} style='color:var(--navy);margin:40px 0 15px;'>{esc(raw.lstrip('#'))}</h{level}>")
        elif raw.startswith("- "):
            if not in_list: out.append("<ul style='line-height:2.2;color:#475569;'>"); in_list = True
            out.append(f"<li>{esc(raw[2:])}</li>")
        else:
            out.append(f"<p style='line-height:2.0;color:#475569;margin-bottom:12px;'>{esc(raw)}</p>")
    if in_list: out.append("</ul>")
    return "\n".join(out)
    # ============================================================
# 3. 視覺樣式系統 (RWD + 多重條件搜尋列 + 地圖互動修復)
# ============================================================
def get_head(title, desc="", og_img="", is_home=False, map_data=None, extra_ld=None):
    seo_desc = esc(desc)[:120] if desc else esc(SITE_SLOGAN)
    og_img = og_img if (og_img and str(og_img).startswith("http")) else DEFAULT_HERO
    
    # 組合 SEO 結構化數據 (JSON-LD)
    lds = [{"@context": "https://schema.org", "@type": "RealEstateAgent", "name": SITE_TITLE, "telephone": MY_PHONE, "url": BASE_URL, "image": og_img}]
    if extra_ld: lds.append(extra_ld)
    
    map_json = json.dumps(map_data, ensure_ascii=False) if map_data else "[]"
    
    # --- 核心地圖與「全能搜尋」JS 邏輯 ---
    map_and_search_js = f"""
    <script src="https://maps.googleapis.com/maps/api/js?key={MAPS_API_KEY}&callback=initMap" async defer></script>
    <script>
        let map;
        function initMap() {{
            const el = document.getElementById('map'); if(!el) return;
            const data = {map_json};
            map = new google.maps.Map(el, {{ 
                center: {{lat: 24.162, lng: 120.647}}, zoom: 12, 
                disableDefaultUI: true, zoomControl: true, 
                styles: [{{"featureType":"poi","stylers":[{{"visibility":"off"}}]}}] 
            }});
            const infoWindow = new google.maps.InfoWindow();
            data.forEach(loc => {{
                if(!loc.lat) return;
                const marker = new google.maps.Marker({{ 
                    position: {{lat: parseFloat(loc.lat), lng: parseFloat(loc.lng)}}, 
                    map: map, title: loc.name, animation: google.maps.Animation.DROP 
                }});
                marker.addListener('click', () => {{
                    infoWindow.setContent(`
                        <div style="padding:10px;width:180px;font-family:sans-serif;">
                            <div style="background:url('${{loc.img}}') center/cover;height:90px;border-radius:8px;margin-bottom:8px;"></div>
                            <h4 style="margin:0;color:#1A365D;font-size:14px;">${{loc.name}}</h4>
                            <div style="color:#C5A059;font-weight:900;font-size:16px;margin:5px 0;">${{loc.price}}</div>
                            <a href="${{loc.url}}" style="display:block;text-align:center;background:#1A365D;color:#fff;text-decoration:none;padding:8px;border-radius:8px;font-size:12px;font-weight:900;">查看分析建議</a>
                        </div>`);
                    infoWindow.open(map, marker);
                }});
            }});
        }}

        // --- 高級多條件搜尋執行邏輯 ---
        function executeSearch() {{
            const area = document.getElementById('s-area').value;
            const type = document.getElementById('s-type').value;
            const rooms = document.getElementById('s-rooms').value;
            const minP = parseFloat(document.getElementById('s-min-p').value) || 0;
            const maxP = parseFloat(document.getElementById('s-max-p').value) || 999999;
            const minS = parseFloat(document.getElementById('s-min-s').value) || 0;
            const maxS = parseFloat(document.getElementById('s-max-s').value) || 999999;

            document.querySelectorAll('.card-anchor').forEach(card => {{
                const d = card.dataset;
                const matchesArea = (area === 'all' || d.area === area);
                const matchesType = (type === 'all' || d.type === type);
                const matchesRooms = (rooms === 'all' || d.rooms.includes(rooms));
                const price = parseFloat(d.priceNum);
                const size = parseFloat(d.sizeNum);
                
                const matchesPrice = (price >= minP && price <= maxP);
                const matchesSize = (size >= minS && size <= maxS);

                card.style.display = (matchesArea && matchesType && matchesRooms && matchesPrice && matchesSize) ? 'block' : 'none';
            }});
            // 搜尋後自動捲動到結果區
            document.getElementById('list-start').scrollIntoView({{behavior: 'smooth'}});
        }}
    </script>""" if is_home else ""

    return f"""<head>
    <meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=0">
    <title>{esc(title)}</title>
    <script type="application/ld+json">{json.dumps(lds)}</script>
    <script async src="https://www.googletagmanager.com/gtag/js?id={GA4_ID}"></script>
    <script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','{GA4_ID}');</script>
    {map_and_search_js}
    <style>
        :root {{ --navy: #1A365D; --gold: #C5A059; --green: #27ae60; --shadow: 0 10px 40px rgba(0,0,0,0.06); }}
        body {{ font-family: 'PingFang TC', sans-serif; margin: 0; background: #f1f5f9; color: #2D3748; -webkit-font-smoothing: antialiased; }}
        
        /* 容器佈局與底部防遮擋 */
        .container {{ width: 100%; max-width: 100%; margin: auto; min-height: 100vh; position: relative; background: #fff; padding-bottom: 150px; }}
        @media (min-width: 768px) {{ .container {{ max-width: 1200px; box-shadow: 0 0 80px rgba(0,0,0,0.05); }} }}
        
        .header {{ background: var(--navy); color: #fff; padding: 18px 20px; display: flex; justify-content: space-between; align-items: center; position: sticky; top: 0; z-index: 1000; }}
        .logo {{ font-weight: 900; letter-spacing: 2px; text-decoration: none; color: #fff; font-size: 20px; }}

        #map {{ height: 350px; background: #eee; width: 100%; border-bottom: 5px solid #fff; }}
        @media (min-width: 768px) {{ #map {{ height: 480px; }} }}
        
        /* 高級搜尋列樣式 (仿截圖設計) */
        .search-box {{ background: #fff; padding: 25px 20px; border-bottom: 1.5px solid #edf2f7; }}
        .search-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 12px; margin-bottom: 15px; }}
        .search-item {{ display: flex; flex-direction: column; gap: 6px; }}
        .search-label {{ font-size: 12px; font-weight: 800; color: var(--navy); letter-spacing: 1px; }}
        .search-select, .search-input {{ padding: 12px; border-radius: 10px; border: 1.5px solid #e2e8f0; font-size: 14px; background: #f8fafc; outline: none; }}
        .search-btn {{ background: var(--green); color: #fff; border: none; padding: 16px; border-radius: 12px; font-weight: 950; font-size: 16px; cursor: pointer; transition: 0.3s; width: 100%; grid-column: 1 / -1; letter-spacing: 2px; box-shadow: 0 5px 15px rgba(39,174,96,0.2); }}
        @media (min-width: 768px) {{ .search-btn {{ grid-column: auto; height: 48px; margin-top: 22px; }} }}

        /* 網格 RWD：手機 2 欄, 電腦 4 欄 */
        .grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; padding: 16px; }}
        @media (min-width: 768px) {{ .grid {{ grid-template-columns: repeat(4, 1fr); gap: 24px; padding: 30px; }} }}
        
        .card {{ border-radius: 24px; overflow: hidden; background: #fff; box-shadow: var(--shadow); border: 1px solid #f1f5f9; display: flex; flex-direction: column; transition: 0.3s; height: 100%; }}
        .card img {{ width: 100%; height: 160px; object-fit: cover; background: #f1f5f9; }}
        @media (min-width: 768px) {{ .card img {{ height: 210px; }} .card:hover {{ transform: translateY(-8px); }} }}
        .card-body {{ padding: 15px; flex-grow: 1; }}
        .card-title {{ font-size: 14px; font-weight: 800; color: var(--navy); margin: 0; line-height: 1.45; height: 40px; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }}
        .card-price {{ color: var(--gold); font-weight: 950; font-size: 18px; margin-top: 10px; }}
        .card-anchor {{ text-decoration: none; color: inherit; }}

        /* 底部行動 Bar：最高層級 */
        .action-bar {{ position: fixed; bottom: 0; left: 50%; transform: translateX(-50%); width: 100%; max-width: 1200px; padding: 25px 25px 45px; display: flex; gap: 15px; background: rgba(255,255,255,0.97); backdrop-filter: blur(25px); border-top: 1.5px solid #f1f1f1; z-index: 10000; }}
        .btn {{ flex: 1; text-align: center; padding: 18px; border-radius: 18px; text-decoration: none; font-weight: 950; color: #fff; font-size: 16px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); }}
        .btn-call {{ background: #111827; }} .btn-line {{ background: #00B900; }}
    </style>
    </head>"""
    # ============================================================
# 4. 建置引擎主邏輯 (SEO 核心 + 多功能搜尋數據埋入)
# ============================================================
def build():
    root = Path(".")
    
    # 初始化：建立 SEO 分類目錄
    for d in CATEGORY_DIRS: 
        if (root/d).exists(): shutil.rmtree(root/d)
        (root/d).mkdir(exist_ok=True)
    for p in root.glob("p*"):
        if p.is_dir() and re.match(r'^p\d+$', p.name): shutil.rmtree(p)
    
    # 座標快取：修正 TypeError (使用地址字串作為 Key)
    geocache = {}
    if GEOCACHE_PATH.exists():
        try:
            raw_cache = json.loads(GEOCACHE_PATH.read_text(encoding="utf-8"))
            if isinstance(raw_cache, dict): geocache = raw_cache
        except: pass

    # 抓取試算表資料
    try:
        res = requests.get(SHEET_CSV_URL, timeout=25)
        res.encoding = "utf-8-sig"
        reader = csv.DictReader(res.text.splitlines())
    except Exception as e:
        print(f"❌ 試算表連線失敗: {e}"); return
    
    all_items = []
    area_groups, feat_groups, price_groups = {}, {}, {}
    map_data, sitemap_urls = [], [f"{BASE_URL}/"]

    # --- 遍歷物件並生成 SEO 與搜尋屬性 ---
    for i, row in enumerate(reader):
        d = {norm(k): norm(v) for k, v in row.items() if k}
        if d.get("狀態", "").upper() in ["OFF", "FALSE"]: continue
        if not d.get("案名"): continue
        
        name, reg, price = d["案名"], d.get("區域", "台中"), d.get("價格", "面議")
        price_num = get_num(price)
        size_num = get_num(d.get("坪數", "0"))
        u_type = d.get("用途", "住宅")
        u_rooms = d.get("格局", "0房")
        
        imgs = normalize_imgs(d.get("圖片網址", ""))
        slug = f"p{i}"
        (root / slug).mkdir(exist_ok=True)
        
        # 修正 404 路徑問題
        item_path = f"/{PROJECT_NAME}/{slug}/"
        sitemap_urls.append(f"{BASE_URL}/{slug}/")

        # 座標處理
        addr = d.get("地址", f"台中市{reg}{name}")
        geo = geocache.get(addr)
        if geo and isinstance(geo, dict) and "lat" in geo:
            map_data.append({"name": name, "price": price, "url": item_path, "lat": geo["lat"], "lng": geo["lng"], "img": imgs[0]})

        # 生成詳情頁 (含 JSON-LD)
        ld = {"@context": "https://schema.org", "@type": "RealEstateListing", "name": name, "description": d.get('描述','')[:150], "image": imgs[0], "url": f"{BASE_URL}/{slug}/"}
        slides = "".join([f'<img src="{u}" loading="lazy">' for u in imgs])
        badges = [f'<a class="spec-badge" href="/{PROJECT_NAME}/area/{safe_slug(reg)}/">📍 {reg}</a>', f'<a class="spec-badge" href="/{PROJECT_NAME}/price/{safe_slug(get_price_bucket(price_num))}/">💰 {price_num}萬</a>']
        for f in split_tags(d.get("特色", "")): badges.append(f'<a class="spec-badge" href="/{PROJECT_NAME}/feature/{safe_slug(f)}/">✨ {f}</a>')

        detail_html = f"""<div class="container">
            <div class="header"><a href="/{PROJECT_NAME}/" class="logo">← {SITE_TITLE}</a></div>
            <div class="slider">{slides}</div>
            <div class="info-box">
                <h1 style="font-size:32px;font-weight:950;color:var(--navy);margin:0 0 15px;">{esc(name)}</h1>
                <div style="font-size:38px;color:var(--gold);font-weight:950;margin-bottom:30px;">{esc(price)}</div>
                <div class="badge-row">{" ".join(badges)}</div>
                <div style="line-height:2.4;font-size:17px;color:#475569;margin-bottom:50px;">{esc(d.get('描述','')).replace('、','<br>• ')}</div>
                <div class="contact-card">
                    <div class="agent-info">
                        <img src="{IMG_RAW_BASE}agent_photo.jpg" class="agent-photo" onerror="this.src='https://placehold.co/100x100?text=SK-L'">
                        <div><strong style="font-size:20px;color:var(--navy);">{esc(MY_NAME)}</strong><br><span style="font-size:13px;color:var(--slate);">專業房產顧問 · 深耕台中</span></div>
                    </div>
                    <a href="{MY_LINE_URL}" target="_blank" class="btn-line-cta">💬 加 LINE 立即諮詢案情</a>
                </div>
                <a href="http://maps.google.com/?q={urllib.parse.quote(addr)}" target="_blank" style="display:block;text-align:center;padding:22px;background:var(--navy);color:#fff;text-decoration:none;border-radius:20px;font-weight:950;margin-top:30px;box-shadow:0 10px 25px rgba(26,54,93,0.2);">📍 在地圖上開啟導航</a>
                {LEGAL_FOOTER_HTML}
            </div>
            <div class="action-bar"><a class="btn btn-call" href="tel:{MY_PHONE}">📞 立即致電</a><a class="btn btn-line" href="{MY_LINE_URL}" target="_blank">💬 LINE 諮詢</a></div>
        </div>"""
        (root / slug / "index.html").write_text(f"<!doctype html><html lang='zh-TW'>{get_head(name, d.get('描述',''), imgs[0], extra_ld=ld)}<body>{detail_html}</body></html>", encoding="utf-8")

        item = {"name": name, "area": reg, "price": price, "price_num": price_num, "size_num": size_num, "type": u_type, "rooms": u_rooms, "img": imgs[0], "url": item_path}
        all_items.append(item)
        area_groups.setdefault(reg, []).append(item)
        price_groups.setdefault(get_price_bucket(price_num), []).append(item)

    # --- 生成首頁與多功能搜尋列 ---
    area_opts = "".join([f'<option value="{a}">{a}</option>' for a in sorted(area_groups.keys())])
    home_cards = "".join([f'<a href="{it["url"]}" class="card-anchor" data-area="{it["area"]}" data-type="{it["type"]}" data-rooms="{it["rooms"]}" data-price-num="{it["price_num"]}" data-size-num="{it["size_num"]}"><div class="card"><img src="{it["img"]}" loading="lazy"><div class="card-body"><h3 class="card-title">{esc(it["name"])}</h3><div class="card-price">{esc(it["price"])}</div><div style="margin-top:12px;font-size:11px;color:var(--navy);font-weight:900;border-top:1px solid #f1f5f9;padding-top:10px;">查看專業建議 →</div></div></div></a>' for it in all_items[::-1]])
    
    home_html = f"""<div class="container">
        <div class="header"><a href="./" class="logo">{SITE_TITLE}</a></div>
        <div id="map"></div>
        <div class="search-box">
            <div class="search-grid">
                <div class="search-item"><label class="search-label">行政區域</label><select class="search-select" id="s-area"><option value="all">全部地區</option>{area_opts}</select></div>
                <div class="search-item"><label class="search-label">房屋類型</label><select class="search-select" id="s-type"><option value="all">不限</option><option value="透天">透天/別墅</option><option value="大樓">電梯大樓</option><option value="土地">土地/農地</option></select></div>
                <div class="search-item"><label class="search-label">格局</label><select class="search-select" id="s-rooms"><option value="all">不限</option><option value="1房">1房</option><option value="2房">2房</option><option value="3房">3房</option><option value="4房">4房以上</option></select></div>
                <div class="search-item"><label class="search-label">總價 (萬)</label><div style="display:flex;gap:5px;"><input class="search-input" id="s-min-p" placeholder="最低"> <input class="search-input" id="s-max-p" placeholder="最高"></div></div>
                <div class="search-item"><label class="search-label">坪數</label><div style="display:flex;gap:5px;"><input class="search-input" id="s-min-s" placeholder="最少"> <input class="search-input" id="s-max-s" placeholder="最多"></div></div>
                <button class="search-btn" onclick="executeSearch()">🔍 開始篩選物件</button>
            </div>
        </div>
        <div id="list-start"></div><div class="grid">{home_cards}</div>{LEGAL_FOOTER_HTML}
        <div class="action-bar"><a class="btn btn-call" href="tel:{MY_PHONE}">📞 撥打電話</a><a class="btn btn-line" href="{MY_LINE_URL}" target="_blank">💬 LINE 諮詢</a></div>
    </div>"""
    (root / "index.html").write_text(f"<!doctype html><html lang='zh-TW'>{get_head(SITE_TITLE, is_home=True, map_data=map_data)}<body>{home_html}</body></html>", encoding="utf-8")

    # 生成 Sitemap.xml
    xml = '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    for u in sorted(set(sitemap_urls)): xml += f'<url><loc>{u}</loc><lastmod>{datetime.now().strftime("%Y-%m-%d")}</lastmod></url>'
    (root / "sitemap.xml").write_text(xml + '</urlset>', encoding="utf-8")
    print(f"✅ 旗艦引擎建置完成！地圖點位：{len(map_data)}")

if __name__ == "__main__": build()
