import os, csv, requests, html, shutil, re, urllib.parse, json
from pathlib import Path
from datetime import datetime

# ============================================================
# 1. 核心品牌與技術配置 (解決 404 與 連結錯誤)
# ============================================================
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQShAl0-TbUU0MQdYVe53im2T6lXQgh_7g-bdL6HHpIBFtA2yfIAMbPw4J9RgZUkROb9AAiMhnRC0kH/pub?output=csv"
PROJECT_NAME = "taichung-houses"
BASE_URL = f"https://shihkailin.github.io/{PROJECT_NAME}"

SITE_TITLE = "SK-L 大台中房地產"
SITE_SLOGAN = "林世塏｜專業顧問 · 誠信置產 · 台中精選房產"
GA4_ID = "G-B7WP9BTP8X"

MY_NAME = "林世塏"
MY_PHONE = "0938-615-351"
# 已修正：末尾包含底線的正確連結
MY_LINE_URL = "https://line.me/ti/p/FDsMyAYDv_" 

POSTS_DIR = Path("posts")
GEOCACHE_PATH = Path("geocache.json")
MAPS_API_KEY = os.getenv("MAPS_API_KEY", "AIzaSyDzgnI2Ucv622CRkWwo2GE5JRrs_Y4HQY0")
IMG_RAW_BASE = f"https://raw.githubusercontent.com/ShihKaiLin/{PROJECT_NAME}/main/images/"
DEFAULT_HERO = f"{IMG_RAW_BASE}hero_bg.jpg"

LEGAL_FOOTER_HTML = """
<div style="margin-top: 25px; padding-top: 20px; border-top: 1px solid #eef2f6; font-size: 11px; color: #94a3b8; line-height: 2; font-weight: 500;">
    📍 英柏國際地產有限公司<br>
    中市地價二字第 1070029259 號<br>
    經紀人：王一媖 (103) 中市經紀字第 00678 號
</div>
"""

# ============================================================
# 2. 旗艦級美學視覺系統 (徹底告別醜版面)
# ============================================================
CSS_STYLE = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&family=Noto+Sans+TC:wght@400;700;900&display=swap');
    :root { 
        --navy: #0F172A; --gold: #B59461; --green: #10B981; 
        --bg: #F8FAFC; --shadow: 0 25px 60px rgba(15, 23, 42, 0.08); 
    }
    body { font-family: 'Inter', 'Noto Sans TC', sans-serif; margin: 0; background: var(--bg); color: #1E293B; -webkit-font-smoothing: antialiased; line-height: 1.6; }
    
    .container { width: 100%; max-width: 1200px; margin: auto; background: #fff; min-height: 100vh; position: relative; padding-bottom: 200px; box-sizing: border-box; }
    
    /* 質感導航 */
    .header { background: var(--navy); color: #fff; padding: 25px 30px; display: flex; justify-content: space-between; align-items: center; position: sticky; top: 0; z-index: 1000; box-shadow: 0 4px 30px rgba(0,0,0,0.1); }
    .logo { font-weight: 900; font-size: 24px; letter-spacing: 1px; color: #fff; text-decoration: none; }

    /* 地圖與漂浮搜尋列 */
    #map { height: 450px; background: #E2E8F0; width: 100%; border-bottom: 8px solid #fff; }
    .search-box { 
        background: #fff; padding: 40px; margin: -60px auto 0; border-radius: 40px; 
        box-shadow: 0 40px 100px rgba(15,23,42,0.12); position: relative; z-index: 10;
        width: 92%; display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 20px; box-sizing: border-box;
    }
    .search-item { display: flex; flex-direction: column; gap: 10px; }
    .search-label { font-size: 11px; font-weight: 900; color: var(--navy); text-transform: uppercase; letter-spacing: 2px; opacity: 0.5; }
    .search-select, .search-input { 
        padding: 16px; border-radius: 18px; border: 1px solid #E2E8F0; font-size: 15px; 
        background: #F8FAFC; outline: none; transition: 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .search-select:focus, .search-input:focus { border-color: var(--gold); background: #fff; box-shadow: 0 0 0 5px rgba(181, 148, 97, 0.1); }
    .search-btn { 
        background: var(--navy); color: #fff; border: none; padding: 22px; border-radius: 20px; 
        font-weight: 900; font-size: 16px; cursor: pointer; transition: 0.4s; grid-column: 1 / -1; letter-spacing: 2px;
    }
    .search-btn:hover { background: var(--gold); transform: translateY(-3px); }

    /* 高質感物件卡片 */
    .grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; padding: 60px 20px; }
    @media (min-width: 768px) { .grid { grid-template-columns: repeat(3, 1fr); gap: 45px; padding: 80px 40px; } }
    
    .card { 
        border-radius: 45px; overflow: hidden; background: #fff; border: 1px solid #F1F5F9; 
        display: flex; flex-direction: column; height: 100%; transition: 0.5s cubic-bezier(0.2, 0.8, 0.2, 1); text-decoration: none; color: inherit;
    }
    .card:hover { transform: translateY(-15px); box-shadow: 0 50px 100px rgba(15, 23, 42, 0.15); border-color: var(--gold); }
    .card img { width: 100%; height: 260px; object-fit: cover; transition: 0.5s; }
    .card-body { padding: 35px; flex-grow: 1; display: flex; flex-direction: column; }
    .card-title { font-size: 19px; font-weight: 900; color: var(--navy); line-height: 1.5; margin: 0; }
    .card-price { color: var(--gold); font-weight: 950; font-size: 28px; margin-top: 15px; letter-spacing: -1.5px; }
    
    .badge { display: inline-block; padding: 10px 20px; background: #F1F5F9; color: #64748B; border-radius: 16px; font-size: 12px; font-weight: 800; margin: 0 10px 12px 0; }
    
    /* 底部固定行動 Bar */
    .action-bar { 
        position: fixed; bottom: 0; left: 50%; transform: translateX(-50%); width: 100%; max-width: 1200px; 
        padding: 30px 30px 50px; display: flex; gap: 20px; background: rgba(255,255,255,0.92); backdrop-filter: blur(25px); 
        border-top: 1px solid #F1F5F9; z-index: 10000; box-sizing: border-box; 
    }
    .btn { flex: 1; text-align: center; padding: 24px; border-radius: 24px; text-decoration: none; font-weight: 950; color: #fff; font-size: 18px; transition: 0.3s; }
    .btn-call { background: var(--navy); } .btn-line { background: var(--green); }
    .btn:hover { transform: scale(0.97); opacity: 0.9; }
</style>
"""
# ============================================================
# 3. 互動引擎中心 (地圖資訊視窗復活 + 智慧篩選 JS)
# ============================================================
def get_head(title, desc="", og_img="", is_home=False, map_data=None):
    seo_desc = esc(desc)[:120] if desc else esc(SITE_SLOGAN)
    og_img = og_img if (og_img and str(og_img).startswith("http")) else DEFAULT_HERO
    map_json = json.dumps(map_data, ensure_ascii=False) if map_data else "[]"
    
    # 核心 JS 邏輯：解決地圖功能與搜尋過濾
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
                styles: [{"featureType":"poi","elementType":"all","stylers":[{"visibility":"off"}]}]
            });
            const infoWindow = new google.maps.InfoWindow();
            data.forEach(loc => {
                if(!loc.lat) return;
                const marker = new google.maps.Marker({ 
                    position: {lat: parseFloat(loc.lat), lng: parseFloat(loc.lng)}, 
                    map: map
                });
                marker.addListener('click', () => {
                    const content = `
                        <div style="padding:15px; width:220px; font-family:'Noto Sans TC',sans-serif;">
                            <div style="background:url('${loc.img}') center/cover; height:120px; border-radius:18px; margin-bottom:12px; box-shadow:0 8px 25px rgba(0,0,0,0.1);"></div>
                            <h4 style="margin:0; color:#0F172A; font-size:16px; font-weight:900;">${loc.name}</h4>
                            <div style="color:#B59461; font-weight:900; font-size:22px; margin:10px 0;">${loc.price}</div>
                            <a href="${loc.url}" style="display:block; text-align:center; background:#0F172A; color:#fff; text-decoration:none; padding:12px; border-radius:12px; font-size:13px; font-weight:900;">查看專家分析建議 →</a>
                        </div>`;
                    infoWindow.setContent(content);
                    infoWindow.open(map, marker);
                });
            });
        }
        function executeSearch() {
            const area = document.getElementById('s-area').value;
            const type = document.getElementById('s-type').value;
            const minP = parseFloat(document.getElementById('s-min-p').value) || 0;
            const maxP = parseFloat(document.getElementById('s-max-p').value) || 999999;
            const minS = parseFloat(document.getElementById('s-min-s').value) || 0;
            const maxS = parseFloat(document.getElementById('s-max-s').value) || 999999;

            document.querySelectorAll('.card-anchor').forEach(card => {
                const d = card.dataset;
                const p = parseFloat(d.priceNum);
                const s = parseFloat(d.sizeNum);
                const matchesArea = (area === 'all' || d.area === area);
                const matchesType = (type === 'all' || d.type === type);
                const matchesPrice = (p >= minP && p <= maxP);
                const matchesSize = (s >= minS && s <= maxS);

                card.style.display = (matchesArea && matchesType && matchesPrice && matchesSize) ? 'block' : 'none';
            });
            document.getElementById('list-start').scrollIntoView({behavior: 'smooth', block: 'start'});
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

# 正規化工具函數
def esc(s): return html.escape(str(s or "").strip())
def norm(s): return str(s or "").strip().replace("\\ufeff", "")
def get_num(s):
    nums = re.findall(r'\\d+\\.?\\d*', str(s).replace(',', ''))
    return float(nums[0]) if nums else 0

def normalize_imgs(img_field):
    if not img_field: return ["https://placehold.co/1200x800?text=SK-L+Branding"]
    raw_list = re.split(r'[|｜]+', str(img_field))
    return [i if i.startswith("http") else f"{IMG_RAW_BASE}{i.lstrip('/')}" for i in raw_list if i.strip()]
    # ============================================================
# 4. 建置引擎主邏輯 (全功能組裝、SEO 置產文章、Sitemap)
# ============================================================
def build():
    root = Path(".")
    for d in ["area", "life"]: 
        if (root/d).exists(): shutil.rmtree(root/d)
        (root/d).mkdir(exist_ok=True)
    for p in root.glob("p*"):
        if p.is_dir() and re.match(r'^p\\d+$', p.name): shutil.rmtree(p)

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
        item_path = f"/{PROJECT_NAME}/{slug}/"
        sitemap_urls.append(f"{BASE_URL}/{slug}/")
        
        imgs = normalize_imgs(d.get("圖片網址", ""))
        price_val, size_val = d.get("價格", "面議"), d.get("坪數", "0")
        
        # 標記地圖點位
        addr = d.get("地址", f"台中市{d.get('區域')}{d.get('案名')}")
        geo = geocache.get(addr)
        if geo and "lat" in geo:
            map_data.append({"name": d['案名'], "price": price_val, "url": item_path, "lat": geo["lat"], "lng": geo["lng"], "img": imgs[0]})

        # 精品詳情頁組裝 (整合顧問卡片與法律字號)
        detail_html = f\"\"\"<div class="container">
            <div class="header"><a href="/{PROJECT_NAME}/" class="logo">← {SITE_TITLE}</a></div>
            <div style="position:relative; height:480px; overflow:hidden;"><img src="{imgs[0]}" style="width:100%; height:100%; object-fit:cover;"><div style="position:absolute; bottom:0; left:0; width:100%; height:250px; background:linear-gradient(to top, #fff, transparent);"></div></div>
            <div style="padding:0 50px 80px;">
                <h1 style="font-size:42px; font-weight:900; color:var(--navy); margin-bottom:15px; letter-spacing:-1px;">{esc(d['案名'])}</h1>
                <div style="font-size:55px; color:var(--gold); font-weight:950; margin-bottom:45px; letter-spacing:-2px;">{esc(price_val)}</div>
                <div style="margin-bottom:50px;"><span class="badge">📍 {esc(d.get('區域'))}</span><span class="badge">🏠 {esc(d.get('用途'))}</span><span class="badge">📐 {esc(size_val)}坪</span></div>
                <div style="line-height:2.4; font-size:19px; color:#475569; background:#F8FAFC; padding:45px; border-radius:45px; border:1px solid #F1F5F9; margin-bottom:60px;">{esc(d.get('描述','')).replace('、','<br>• ')}</div>
                <div style="background:#fff; border-radius:45px; padding:45px; border:1px solid #F1F5F9; box-shadow:0 30px 70px rgba(15,23,42,0.04);">
                    <div style="display:flex; align-items:center; gap:30px; margin-bottom:15px;">
                        <img src="{IMG_RAW_BASE}agent_photo.jpg" style="width:90px; height:90px; border-radius:50%; object-fit:cover; border:6px solid #F8FAFC;" onerror="this.src='https://placehold.co/150x150?text=SK-L'">
                        <div><div style="font-size:26px; font-weight:900; color:var(--navy);">{esc(MY_NAME)}</div><div style="font-size:15px; color:#94a3b8; font-weight:700;">台中房產置產專業顧問</div></div>
                    </div>
                    {LEGAL_FOOTER_HTML}
                    <a href="{MY_LINE_URL}" target="_blank" style="display:block; background:var(--green); color:#fff; text-decoration:none; text-align:center; padding:25px; border-radius:24px; font-weight:950; margin-top:40px; font-size:19px; box-shadow:0 15px 35px rgba(16,185,129,0.25);">💬 立即加 LINE 索取完整物件分析</a>
                </div>
            </div>
            <div class="action-bar"><a class="btn btn-call" href="tel:{MY_PHONE}">📞 服務專線</a><a class="btn btn-line" href="{MY_LINE_URL}" target="_blank">💬 LINE 諮詢</a></div>
        </div>\"\"\"
        (root / slug / "index.html").write_text(f"<!doctype html><html lang='zh-TW'>{get_head(d['案名'], d.get('描述',''), imgs[0])}<body>{detail_html}</body></html>", encoding="utf-8")
        
        all_items.append({"name":d['案名'],"area":d.get('區域'),"type":d.get('用途'),"price":price_val,"price_num":get_num(price_val),"size_num":get_num(size_val),"img":imgs[0],"url":item_path})

    # 處理 SEO 置產文章系統 (Markdown)
    if POSTS_DIR.exists():
        for md_file in POSTS_DIR.glob("*.md"):
            slug = urllib.parse.quote(md_file.stem)
            (root / "life" / slug).mkdir(parents=True, exist_ok=True)
            content = md_file.read_text(encoding="utf-8").replace('\\n','<br>')
            post_html = f\"\"\"<div class="container"><div class="header"><a href="/{PROJECT_NAME}/" class="logo">← 回首頁</a></div><div style="padding:100px 50px; max-width:900px; margin:auto; line-height:2.5; font-size:20px;"><h1 style="color:var(--navy); font-size:45px; margin-bottom:60px; font-weight:900;">{esc(md_file.stem)}</h1>{content}</div></div>\"\"\"
            (root / "life" / slug / "index.html").write_text(f"<!doctype html><html lang='zh-TW'>{get_head(md_file.stem)}<body>{post_html}</body></html>", encoding="utf-8")
            sitemap_urls.append(f"{BASE_URL}/life/{slug}/")

    # 首頁組裝 (仿淡水房產網佈局)
    area_opts = "".join([f'<option value="{a}">{a}</option>' for a in sorted(set(x['area'] for x in all_items if x['area']))])
    home_cards = "".join([f'<a href="{it["url"]}" class="card-anchor" data-area="{it["area"]}" data-type="{it["type"]}" data-price-num="{it["price_num"]}" data-size-num="{it["size_num"]}"><div class="card"><img src="{it["img"]}" loading="lazy"><div class="card-body"><h3 class="card-title">{esc(it["name"])}</h3><div class="card-price">{esc(it["price"])}</div><div style="margin-top:25px; font-size:12px; color:var(--navy); font-weight:900; opacity:0.4; text-align:right; letter-spacing:1px;">EXPLORE PROPERTY →</div></div></div></a>' for it in all_items[::-1]])
    
    home_html = f\"\"\"<div class="container"><div class="header"><div class="logo">{SITE_TITLE}</div></div><div id="map"></div>
        <div class="search-box">
            <div class="search-item"><label class="search-label">行政區域</label><select class="search-select" id="s-area"><option value="all">不限區域</option>{area_opts}</select></div>
            <div class="search-item"><label class="search-label">房屋類型</label><select class="search-select" id="s-type"><option value="all">不限類型</option><option value="透天">透天/別墅</option><option value="大樓">電梯大樓</option><option value="土地">土地/農地</option></select></div>
            <div class="search-item"><label class="search-label">預算(萬)</label><div style="display:flex;gap:10px;"><input class="search-input" id="s-min-p" placeholder="最低"> <input class="search-input" id="s-max-p" placeholder="最高"></div></div>
            <button class="search-btn" onclick="executeSearch()">🔍 搜尋台中優選房產</button>
        </div>
        <div id="list-start"></div><div class="grid">{home_cards}</div>
        <div class="action-bar"><a class="btn btn-call" href="tel:{MY_PHONE}">📞 服務專線</a><a class="btn btn-line" href="{MY_LINE_URL}" target="_blank">💬 LINE 諮詢</a></div>
    </div>\"\"\"
    (root / "index.html").write_text(f"<!doctype html><html lang='zh-TW'>{get_head(SITE_TITLE, is_home=True, map_data=map_data)}<body>{home_html}</body></html>", encoding="utf-8")

    (root / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + "".join([f'<url><loc>{u}</loc></url>' for u in sitemap_urls]) + '</urlset>', encoding="utf-8")
    print(f"✅ SK-L 旗艦美學版部署成功！")

if __name__ == "__main__": build()
