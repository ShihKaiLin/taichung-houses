import os, csv, requests, html, shutil, re, urllib.parse, json
from pathlib import Path
from datetime import datetime

# ============================================================
# 1. 核心品牌與路徑配置 (解決 404 與 故障碼)
# ============================================================
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQShAl0-TbUU0MQdYVe53im2T6lXQgh_7g-bdL6HHpIBFtA2yfIAMbPw4J9RgZUkROb9AAiMhnRC0kH/pub?output=csv"

# 重要：修正專案路徑，解決圖 2 的 404 問題
PROJECT_NAME = "taichung-houses"
BASE_URL = f"https://shihkailin.github.io/{PROJECT_NAME}"

SITE_TITLE = "SK-L 大台中房地產"
SITE_SLOGAN = "林世塏｜專業顧問 · 誠信置產 · 台中精選房產"
GA4_ID = "G-B7WP9BTP8X"

MY_NAME = "林世塏"
MY_PHONE = "0938-615-351"
MY_LINE_URL = "https://line.me/ti/p/FDsMyAYDv"

# 依要求：定義僅顯示於詳情頁側邊的經紀資訊 (鎖定紅色框選區)
LEGAL_FOOTER_HTML = """
<div style="margin-top: 20px; padding-top: 15px; border-top: 1.5px solid #edf2f7; font-size: 11px; color: #718096; line-height: 1.8; font-weight: 500;">
    英柏國際地產有限公司<br>
    中市地價二字第 1070029259 號<br>
    經紀人：王一媖 (103) 中市經紀字第 00678 號
</div>
"""

# 路徑與 API 配置
POSTS_DIR = Path("posts")
GEOCACHE_PATH = Path("geocache.json")
MAPS_API_KEY = os.getenv("MAPS_API_KEY", "AIzaSyDzgnI2Ucv622CRkWwo2GE5JRrs_Y4HQY0")
IMG_RAW_BASE = f"https://raw.githubusercontent.com/ShihKaiLin/{PROJECT_NAME}/main/images/"
DEFAULT_HERO = f"{IMG_RAW_BASE}hero_bg.jpg"

# ============================================================
# 2. 復刻版究極視覺樣式 (CSS)
# ============================================================
CSS_STYLE = """
<style>
    :root { --navy: #1A365D; --gold: #C5A059; --green: #27ae60; --slate: #475569; --gray: #f8fafc; --shadow: 0 15px 45px rgba(0,0,0,0.06); }
    body { font-family: 'PingFang TC', 'Heiti TC', sans-serif; margin: 0; background: #f1f5f9; color: #334155; -webkit-font-smoothing: antialiased; }
    
    /* 容器佈局 */
    .container { width: 100%; max-width: 100%; margin: auto; min-height: 100vh; position: relative; background: #fff; padding-bottom: 160px; box-sizing: border-box; }
    @media (min-width: 768px) { .container { max-width: 1200px; box-shadow: 0 0 100px rgba(0,0,0,0.05); } }
    
    /* 導航列 */
    .header { background: var(--navy); color: #fff; padding: 20px; display: flex; justify-content: space-between; align-items: center; position: sticky; top: 0; z-index: 1000; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
    .logo { font-weight: 950; letter-spacing: 2px; text-decoration: none; color: #fff; font-size: 20px; }

    /* 地圖與搜尋列 */
    #map { height: 400px; background: #e2e8f0; width: 100%; }
    @media (min-width: 768px) { #map { height: 500px; } }
    
    .search-box { background: #fff; padding: 30px 20px; border-bottom: 1px solid #edf2f7; display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 15px; }
    .search-item { display: flex; flex-direction: column; gap: 8px; }
    .search-label { font-size: 11px; font-weight: 900; color: var(--navy); letter-spacing: 1px; }
    .search-select, .search-input { padding: 14px; border-radius: 12px; border: 1.5px solid #e2e8f0; font-size: 14px; background: var(--gray); outline: none; transition: 0.3s; }
    .search-btn { background: var(--green); color: #fff; border: none; padding: 18px; border-radius: 15px; font-weight: 950; font-size: 16px; cursor: pointer; transition: 0.3s; grid-column: 1 / -1; letter-spacing: 2px; box-shadow: 0 10px 20px rgba(39,174,96,0.2); }
    @media (min-width: 768px) { .search-btn { grid-column: auto; height: 52px; margin-top: 24px; } }

    /* 物件卡片網格 */
    .grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; padding: 15px; }
    @media (min-width: 768px) { .grid { grid-template-columns: repeat(4, 1fr); gap: 30px; padding: 40px; } }
    
    .card { border-radius: 24px; overflow: hidden; background: #fff; box-shadow: var(--shadow); border: 1px solid #f1f5f9; display: flex; flex-direction: column; height: 100%; transition: 0.4s; text-decoration: none; color: inherit; }
    .card:hover { transform: translateY(-8px); }
    .card img { width: 100%; height: 160px; object-fit: cover; background: #f8fafc; }
    .card-body { padding: 18px; flex-grow: 1; }
    .card-title { font-size: 14px; font-weight: 850; color: var(--navy); margin: 0; line-height: 1.5; height: 42px; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }
    .card-price { color: var(--gold); font-weight: 950; font-size: 20px; margin-top: 12px; }
    
    /* 詳情頁元件 */
    .badge { display: inline-block; padding: 6px 14px; background: #f1f5f9; color: var(--slate); border-radius: 50px; font-size: 12px; font-weight: 700; margin: 0 5px 10px 0; }
    .contact-card { background: #fff; border: 1.5px solid #edf2f7; border-radius: 30px; padding: 35px; margin: 50px 0; box-shadow: var(--shadow); }
    .agent-photo { width: 70px; height: 70px; border-radius: 50%; object-fit: cover; border: 4px solid #f1f5f9; margin-bottom: 15px; }
    
    /* 底部行動 Bar */
    .action-bar { position: fixed; bottom: 0; left: 50%; transform: translateX(-50%); width: 100%; max-width: 1200px; padding: 25px 25px 45px; display: flex; gap: 15px; background: rgba(255,255,255,0.98); backdrop-filter: blur(15px); border-top: 1px solid #f1f1f1; z-index: 10000; box-sizing: border-box; }
    .btn { flex: 1; text-align: center; padding: 20px; border-radius: 20px; text-decoration: none; font-weight: 950; color: #fff; font-size: 17px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); }
    .btn-call { background: var(--navy); } .btn-line { background: var(--green); }
    
    .sk-footer { padding: 60px 20px; text-align: center; font-size: 11px; color: #cbd5e0; letter-spacing: 1px; }
</style>
"""
# ============================================================
# 3. 互動引擎中心 (地圖小卡復活 + 全能搜尋 JS)
# ============================================================
def get_head(title, desc="", og_img="", is_home=False, map_data=None):
    seo_desc = esc(desc)[:120] if desc else esc(SITE_SLOGAN)
    og_img = og_img if (og_img and str(og_img).startswith("http")) else DEFAULT_HERO
    
    # 這裡使用 json.dumps 確保地圖數據 100% 正確埋入
    map_json = json.dumps(map_data, ensure_ascii=False) if map_data else "[]"
    
    # --- 核心 JavaScript：地圖彈窗與搜尋邏輯 ---
    # 使用 Python 的 replace 處理，避免 f-string 與 JavaScript 模板字串衝突
    map_js_template = """
    <script src="https://maps.googleapis.com/maps/api/js?key=MAPS_API_KEY&callback=initMap" async defer></script>
    <script>
        let map;
        function initMap() {
            const el = document.getElementById('map'); if(!el) return;
            const data = MAP_DATA_JSON;
            map = new google.maps.Map(el, { 
                center: {lat: 24.162, lng: 120.647}, zoom: 12, 
                disableDefaultUI: true, zoomControl: true, 
                styles: [{"featureType":"poi","stylers":[{"visibility":"off"}]}] 
            });
            const infoWindow = new google.maps.InfoWindow();
            
            data.forEach(loc => {
                if(!loc.lat) return;
                const marker = new google.maps.Marker({ 
                    position: {lat: parseFloat(loc.lat), lng: parseFloat(loc.lng)}, 
                    map: map, title: loc.name, animation: google.maps.Animation.DROP 
                });
                
                // 點擊地圖標籤：彈出精美房屋資訊卡 (復刻 TamsuiHome 風格)
                marker.addListener('click', () => {
                    const content = `
                        <div style="padding:10px;width:200px;font-family:sans-serif;">
                            <div style="background:url('${loc.img}') center/cover;height:100px;border-radius:12px;margin-bottom:10px;box-shadow:0 4px 12px rgba(0,0,0,0.1);"></div>
                            <h4 style="margin:0;color:#1A365D;font-size:15px;font-weight:900;line-height:1.4;">${loc.name}</h4>
                            <div style="color:#C5A059;font-weight:950;font-size:18px;margin:8px 0;">${loc.price}</div>
                            <a href="${loc.url}" style="display:block;text-align:center;background:#1A365D;color:#fff;text-decoration:none;padding:12px;border-radius:10px;font-size:13px;font-weight:900;">查看分析建議 →</a>
                        </div>`;
                    infoWindow.setContent(content);
                    infoWindow.open(map, marker);
                });
            });
        }

        // 全能搜尋引擎：支援 區域/類型/房數/總價/坪數 五大篩選
        function executeSearch() {
            const area = document.getElementById('s-area').value;
            const type = document.getElementById('s-type').value;
            const rooms = document.getElementById('s-rooms').value;
            const minP = parseFloat(document.getElementById('s-min-p').value) || 0;
            const maxP = parseFloat(document.getElementById('s-max-p').value) || 999999;
            const minS = parseFloat(document.getElementById('s-min-s').value) || 0;
            const maxS = parseFloat(document.getElementById('s-max-s').value) || 999999;

            document.querySelectorAll('.card-anchor').forEach(card => {
                const d = card.dataset;
                const mArea = (area === 'all' || d.area === area);
                const mType = (type === 'all' || d.type === type);
                const mRooms = (rooms === 'all' || d.rooms.includes(rooms));
                const price = parseFloat(d.priceNum);
                const size = parseFloat(d.sizeNum);
                const mPrice = (price >= minP && price <= maxP);
                const mSize = (size >= minS && size <= maxS);

                card.style.display = (mArea && mType && mRooms && mPrice && mSize) ? 'block' : 'none';
            });
            document.getElementById('list-start').scrollIntoView({behavior: 'smooth'});
        }
    </script>"""
    
    js_ready = map_js_template.replace("MAPS_API_KEY", MAPS_API_KEY).replace("MAP_DATA_JSON", map_json) if is_home else ""

    return f"""<head>
    <meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=0">
    <title>{esc(title)}</title>
    {CSS_STYLE}
    <script async src="https://www.googletagmanager.com/gtag/js?id={GA4_ID}"></script>
    <script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','{GA4_ID}');</script>
    {js_ready}
    </head>"""

# ============================================================
# 4. 資料正規化與轉換工具
# ============================================================
def esc(s): return html.escape(str(s or "").strip())
def norm(s): return str(s or "").strip().replace("\ufeff", "")
def get_num(s):
    nums = re.findall(r'\d+\.?\d*', str(s).replace(',', ''))
    return float(nums[0]) if nums else 0

def split_tags(s):
    if not s: return []
    return [p.strip() for p in re.split(r"[、,，;；\|\｜/\\\n\r]+", str(s)) if p.strip()]

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
# 5. 建置引擎主邏輯 (全功能組裝、搜尋數據埋入、Sitemap 生成)
# ============================================================
def build():
    root = Path(".")
    
    # 初始化：建立 SEO 分類目錄並清理舊物件
    for d in ["area", "life"]: 
        if (root/d).exists(): shutil.rmtree(root/d)
        (root/d).mkdir(exist_ok=True)
    for p in root.glob("p*"):
        if p.is_dir() and re.match(r'^p\d+$', p.name): shutil.rmtree(p)
    
    # 座標快取處理：解決 TypeError 故障
    geocache = {}
    if GEOCACHE_PATH.exists():
        try:
            raw_cache = json.loads(GEOCACHE_PATH.read_text(encoding="utf-8"))
            if isinstance(raw_cache, dict): geocache = raw_cache
        except: pass

    # 獲取試算表資料
    try:
        res = requests.get(SHEET_CSV_URL, timeout=30)
        res.encoding = "utf-8-sig"
        reader = list(csv.DictReader(res.text.splitlines()))
    except Exception as e:
        print(f"❌ 試算表連線失敗: {e}"); return
    
    all_items = []
    area_groups = {}
    map_data, sitemap_urls = [], [f"{BASE_URL}/"]

    # --- 遍歷物件生成內容 ---
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
        
        # 修正 404 路徑：GitHub Pages 絕對路徑
        item_path = f"/{PROJECT_NAME}/{slug}/"
        sitemap_urls.append(f"{BASE_URL}/{slug}/")

        # 座標點位處理 (標籤彈窗數據)
        addr = d.get("地址", f"台中市{reg}{name}")
        geo = geocache.get(addr)
        if geo and isinstance(geo, dict) and "lat" in geo:
            map_data.append({
                "name": name, "price": price, "url": item_path, 
                "lat": geo["lat"], "lng": geo["lng"], "img": imgs[0]
            })

        # 生成詳情頁 (標籤雲 + 經紀人側邊欄)
        badges = [
            f'<span class="badge">📍 {reg}</span>',
            f'<span class="badge">🏠 {u_type}</span>',
            f'<span class="badge">📐 {size_num}坪</span>',
            f'<span class="badge">🛋️ {u_rooms}</span>'
        ]
        
        detail_html = f"""<div class="container">
            <div class="header"><a href="/{PROJECT_NAME}/" class="logo">← {SITE_TITLE}</a></div>
            <img src="{imgs[0]}" style="width:100%; height:380px; object-fit:cover;" alt="{esc(name)}">
            <div style="padding:30px;">
                <div style="color:var(--gold); font-weight:900; font-size:12px; letter-spacing:3px; margin-bottom:12px;">PREMIUM LISTING</div>
                <h1 style="font-size:32px; font-weight:950; color:var(--navy); margin:0 0 10px; line-height:1.3;">{esc(name)}</h1>
                <div style="font-size:45px; color:var(--gold); font-weight:950; margin-bottom:30px;">{esc(price)}</div>
                <div style="margin-bottom:35px;">{" ".join(badges)}</div>
                
                <div style="line-height:2.4; font-size:18px; color:var(--slate); margin-bottom:50px; background:var(--gray); padding:30px; border-radius:25px; border:1px solid #edf2f7;">
                    {esc(d.get('描述','')).replace('、','<br>• ')}
                </div>

                <div class="contact-card">
                    <div style="display:flex; align-items:center; gap:20px;">
                        <img src="{IMG_RAW_BASE}agent_photo.jpg" class="agent-photo" onerror="this.src='https://placehold.co/100x100?text=SK-L'">
                        <div>
                            <strong style="font-size:22px; color:var(--navy);">{esc(MY_NAME)}</strong><br>
                            <span style="font-size:14px; color:var(--slate);">您的台中置產專家</span>
                        </div>
                    </div>
                    {LEGAL_FOOTER_HTML}
                    <a href="{MY_LINE_URL}" target="_blank" class="btn-line-cta">💬 加 LINE 立即諮詢分析建議</a>
                </div>
                
                <a href="http://maps.google.com/?q={urllib.parse.quote(addr)}" target="_blank" style="display:block; text-align:center; padding:22px; background:var(--navy); color:#fff; text-decoration:none; border-radius:20px; font-weight:950; margin-top:35px; font-size:16px;">📍 在 Google 地圖上查看正確位置</a>
                
                <div class="sk-footer">© 2026 {SITE_TITLE}. All Rights Reserved.</div>
            </div>
            <div class="action-bar"><a class="btn btn-call" href="tel:{MY_PHONE}">📞 撥打電話</a><a class="btn btn-line" href="{MY_LINE_URL}" target="_blank">💬 LINE 諮詢</a></div>
        </div>"""
        (root / slug / "index.html").write_text(f"<!doctype html><html lang='zh-TW'>{get_head(name, d.get('描述',''), imgs[0])}<body>{detail_html}</body></html>", encoding="utf-8")

        item = {"name": name, "area": reg, "price": price, "price_num": price_num, "size_num": size_num, "type": u_type, "rooms": u_rooms, "img": imgs[0], "url": item_path}
        all_items.append(item)
        area_groups.setdefault(reg, []).append(item)

    # --- 生成首頁與全能搜尋引擎 ---
    area_opts = "".join([f'<option value="{a}">{a}</option>' for a in sorted(area_groups.keys())])
    home_cards = "".join([f'<a href="{it["url"]}" class="card-anchor" data-area="{it["area"]}" data-type="{it["type"]}" data-rooms="{it["rooms"]}" data-price-num="{it["price_num"]}" data-size-num="{it["size_num"]}"><div class="card"><img src="{it["img"]}" loading="lazy"><div class="card-body"><h3 class="card-title">{esc(it["name"])}</h3><div class="card-price">{esc(it["price"])}</div><div style="margin-top:15px; font-size:11px; color:var(--navy); font-weight:900; border-top:1.5px solid #f1f5f9; padding-top:12px; text-align:center; letter-spacing:1px;">VIEW ANALYSIS →</div></div></div></a>' for it in all_items[::-1]])
    
    home_html = f"""<div class="container">
        <div class="header"><div class="logo">{SITE_TITLE}</div></div>
        <div id="map"></div>
        <div class="search-box">
            <div class="search-item"><label class="search-label">行政區域</label><select class="search-select" id="s-area"><option value="all">全部台中地區</option>{area_opts}</select></div>
            <div class="search-item"><label class="search-label">房屋類型</label><select class="search-select" id="s-type"><option value="all">不限類型</option><option value="透天">透天/別墅</option><option value="大樓">電梯大樓</option><option value="土地">土地/農地</option></select></div>
            <div class="search-item"><label class="search-label">房數格局</label><select class="search-select" id="s-rooms"><option value="all">不限</option><option value="1房">1房</option><option value="2房">2房</option><option value="3房">3房</option><option value="4房">4房以上</option></select></div>
            <div class="search-item"><label class="search-label">預算(萬)</label><div style="display:flex; gap:5px;"><input class="search-input" id="s-min-p" placeholder="最低"> <input class="search-input" id="s-max-p" placeholder="最高"></div></div>
            <div class="search-item"><label class="search-label">總坪數</label><div style="display:flex; gap:5px;"><input class="search-input" id="s-min-s" placeholder="最少"> <input class="search-input" id="s-max-s" placeholder="最多"></div></div>
            <button class="search-btn" onclick="executeSearch()">🔍 立即篩選置產物件</button>
        </div>
        <div id="list-start"></div><div class="grid">{home_cards}</div>
        <div class="sk-footer">© 2026 {SITE_TITLE}. All Rights Reserved.</div>
        <div class="action-bar"><a class="btn btn-call" href="tel:{MY_PHONE}">📞 服務電話</a><a class="btn btn-line" href="{MY_LINE_URL}" target="_blank">💬 LINE 諮詢</a></div>
    </div>"""
    (root / "index.html").write_text(f"<!doctype html><html lang='zh-TW'>{get_head(SITE_TITLE, is_home=True, map_data=map_data)}<body>{home_html}</body></html>", encoding="utf-8")

    # 生成 Sitemap.xml
    xml = '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    for u in sorted(set(sitemap_urls)): xml += f'<url><loc>{u}</loc><lastmod>{datetime.now().strftime("%Y-%m-%d")}</lastmod></url>'
    (root / "sitemap.xml").write_text(xml + '</urlset>', encoding="utf-8")
    print(f"✅ SK-L 旗艦 12.0 組裝完成！地圖點位：{len(map_data)}")

if __name__ == "__main__":
    build()
