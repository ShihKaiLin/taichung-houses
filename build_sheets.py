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
# 1. 核心品牌資產配置 (Core Branding Assets)
# ============================================================
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQShAl0-TbUU0MQdYVe53im2T6lXQgh_7g-bdL6HHpIBFtA2yfIAMbPw4J9RgZUkROb9AAiMhnRC0kH/pub?output=csv"
BASE_URL = "https://shihkailin.github.io/taichung-houses"

SITE_TITLE = "SK-L 大台中房地產"
SITE_SLOGAN = "林世塏｜專業顧問 · 誠信置產 · 台中精選房產"
GA4_ID = "G-B7WP9BTP8X"

MY_NAME = "林世塏"
MY_PHONE = "0938-615-351"
MY_LINE_URL = "https://line.me/ti/p/FDsMyAYDv"

# Google Maps 座標快取系統 (保護你的 API 錢包)
MAPS_API_KEY = os.getenv("MAPS_API_KEY", "").strip()
GEOCACHE_PATH = Path("geocache.json")
GEOCODE_SLEEP_SEC = 0.2

# 靜態資源路徑
IMG_RAW_BASE = "https://raw.githubusercontent.com/ShihKaiLin/taichung-houses/main/images/"
DEFAULT_HERO = f"{IMG_RAW_BASE}hero_bg.jpg"
POSTS_DIR = Path("posts")

# SEO 自動化索引路徑
CATEGORY_DIRS = ["area", "feature", "price", "posts", "agent"]

# ============================================================
# 2. 核心邏輯工具 (Advanced Logic Engine)
# ============================================================
def esc(s):
    """ 防止 HTML 注入，確保特殊字元正確呈現 """
    return html.escape(str(s or "").strip())

def norm_text(s):
    """ 清理字串中的隱形字元與多餘空格 """
    return str(s or "").strip().replace("\ufeff", "")

def safe_slug(label: str) -> str:
    """ 產生符合 URL 規範的乾淨路徑 """
    label = norm_text(label)
    return urllib.parse.quote(label, safe="") if label else "unknown"

def split_tags(s):
    """ 強大的標籤拆分器，支援各種分隔符號 """
    if not s: return []
    parts = re.split(r"[、,，;；\|\｜/\\\n\r]+", str(s))
    return [p.strip() for p in parts if p.strip()]

def get_pure_price_num(p_str):
    """ 從字串中提取純數字價格，用於排序與分級 """
    nums = re.findall(r'\d+', str(p_str).replace(',', ''))
    return float(nums[0]) if nums else 0

def get_price_bucket(price_num):
    """ 自動化預算分區系統 """
    if price_num == 0: return "面議"
    if price_num < 800: return "800萬以下"
    if price_num < 1500: return "800-1500萬"
    if price_num < 2500: return "1500-2500萬"
    if price_num < 4000: return "2500-4000萬"
    return "4000萬以上"

def normalize_imgs(img_field):
    """ 究極多圖輪播解析：支援外部網址、本地路徑與多圖 | 分隔 """
    if not img_field: return ["https://placehold.co/900x600?text=SK-L+Property"]
    raw_list = re.split(r'[|｜]+', str(img_field))
    urls = []
    for img in raw_list:
        img = img.strip()
        if not img: continue
        if img.startswith("http"): urls.append(img)
        else: urls.append(f"{IMG_RAW_BASE}{img.lstrip('/')}")
    return urls if urls else [DEFAULT_HERO]

# ============================================================
# 3. UI 視覺系統與 SEO 樣式 (The Design Language)
# ============================================================
LEGAL_FOOTER = f"""
<div class="sk-footer">
    <div class="sk-footer-inner">
        <strong class="sk-corp">英柏國際地產有限公司</strong>
        <p class="sk-lic">
            中市地價二字第 1070029259 號<br>
            經紀人：王一媖（103）中市經紀字第 00678 號
        </p>
        <div class="sk-slogan">專業誠信 · 卓越服務 · 深耕台中</div>
        <div class="sk-copyright">© 2026 SK-L Branding. All Rights Reserved.</div>
    </div>
</div>
"""

def get_head(title, desc="", og_img="", og_url="", is_home=False, map_data=None):
    seo_desc = esc(desc)[:120] if desc else esc(SITE_SLOGAN)
    og_img = og_img if (og_img and str(og_img).startswith("http")) else DEFAULT_HERO
    
    # 注入 JSON-LD：讓 Google 認識 SK-L 品牌與物件
    json_ld = {{
        "@context": "https://schema.org",
        "@type": "RealEstateAgent",
        "name": SITE_TITLE,
        "telephone": MY_PHONE,
        "url": BASE_URL,
        "image": og_img,
        "areaServed": "Taichung City, Taiwan",
        "address": {{"@type": "PostalAddress", "addressLocality": "Taichung", "addressCountry": "TW"}}
    }}
    
    map_json = json.dumps(map_data, ensure_ascii=False) if map_data else "[]"
    map_script = ""
    if is_home and MAPS_API_KEY:
        map_script = f"""
        <script src="https://maps.googleapis.com/maps/api/js?key={MAPS_API_KEY}"></script>
        <script>
            function initMap() {{
                const mapEl = document.getElementById('map'); if(!mapEl) return;
                const map = new google.maps.Map(mapEl, {{
                    center: {{lat:24.162, lng:120.647}}, zoom: 12, 
                    disableDefaultUI: true, zoomControl: true,
                    styles: [{{"featureType":"poi","stylers":[{{"visibility":"off"}}]}}]
                }});
                const infoWindow = new google.maps.InfoWindow();
                const locations = {map_json};
                locations.forEach(loc => {{
                    if(!loc.lat) return;
                    const marker = new google.maps.Marker({{ position: {{lat:loc.lat, lng:loc.lng}}, map: map, title: loc.name }});
                    marker.addListener('click', () => {{
                        const content = `
                            <div style="padding:10px;width:220px;font-family:sans-serif;">
                                <div style="background:url('${{loc.img}}') center/cover;height:110px;border-radius:12px;margin-bottom:10px;"></div>
                                <h4 style="margin:0;color:#1A365D;font-size:15px;line-height:1.4;">${{loc.name}}</h4>
                                <div style="color:#C5A059;font-weight:900;font-size:18px;margin:8px 0 12px;">${{loc.price}}</div>
                                <a href="${{loc.url}}" style="display:block;text-align:center;background:#1A365D;color:#fff;text-decoration:none;padding:12px;border-radius:10px;font-size:13px;font-weight:bold;">查看分析建議</a>
                            </div>`;
                        infoWindow.setContent(content);
                        infoWindow.open(map, marker);
                    }});
                }});
            }}
            window.onload = initMap;
        </script>
        """

    return f"""<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=0">
    <title>{esc(title)}</title>
    <meta name="description" content="{seo_desc}">
    <meta property="og:title" content="{esc(title)}">
    <meta property="og:image" content="{esc(og_img)}">
    <meta property="og:url" content="{esc(og_url)}">
    <script type="application/ld+json">{json.dumps(json_ld)}</script>
    <script async src="https://www.googletagmanager.com/gtag/js?id={GA4_ID}"></script>
    <script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','{GA4_ID}');</script>
    {map_script}
    <style>
        :root {{ --navy: #1A365D; --gold: #C5A059; --slate: #64748B; --light: #F8FAFC; --shadow: 0 15px 45px rgba(0,0,0,0.08); }}
        body {{ font-family: 'PingFang TC','Microsoft JhengHei',sans-serif; margin: 0; background: #fff; color: #2D3748; -webkit-font-smoothing: antialiased; }}
        .container {{ max-width: 520px; margin: auto; min-height: 100vh; position: relative; box-shadow: 0 0 80px rgba(0,0,0,0.05); background: #fff; }}
        
        /* 品牌導航 */
        .nav-bar {{ display: flex; gap: 15px; overflow-x: auto; padding: 18px 20px; background: rgba(255,255,255,0.96); backdrop-filter: blur(15px); border-bottom: 1px solid #f1f5f9; position: sticky; top: 0; z-index: 100; scrollbar-width: none; }}
        .nav-item {{ white-space: nowrap; text-decoration: none; color: var(--slate); font-size: 14px; font-weight: 800; padding: 8px 12px; transition: 0.3s; }}
        .nav-item.active {{ color: var(--navy); border-bottom: 3px solid var(--navy); }}

        /* 首頁 Hero 與地圖 */
        .hero {{ height: 280px; background: url('{DEFAULT_HERO}') center/cover; display: flex; align-items: center; justify-content: center; color: #fff; position: relative; }}
        .hero::after {{ content:''; position:absolute; top:0; left:0; width:100%; height:100%; background: linear-gradient(to bottom, rgba(0,0,0,0.1), rgba(0,0,0,0.5)); }}
        .hero-content {{ position: relative; z-index: 2; text-align: center; }}
        .hero-content h1 {{ font-size: 34px; letter-spacing: 6px; font-weight: 950; text-shadow: 0 2px 12px rgba(0,0,0,0.4); margin: 0; }}
        #map {{ height: 320px; border-radius: 35px; border: 6px solid #fff; margin: -55px 16px 0; position: relative; z-index: 10; box-shadow: 0 25px 50px rgba(0,0,0,0.15); background: #f1f5f9; }}
        
        /* 兩路並進網格系統 (Mobile-First Luxury Grid) */
        .grid-list {{ display: grid; grid-template-columns: 1fr 1fr; gap: 14px; padding: 25px 16px; }}
        .card {{ border-radius: 28px; overflow: hidden; background: #fff; box-shadow: var(--shadow); border: 1px solid #f1f5f9; text-decoration: none; display: flex; flex-direction: column; transition: 0.4s cubic-bezier(0.165, 0.84, 0.44, 1); }}
        .card:active {{ transform: scale(0.96); opacity: 0.9; }}
        .card img {{ width: 100%; height: 165px; object-fit: cover; background: #f3f4f6; display: block; }}
        .card-body {{ padding: 15px; flex-grow: 1; }}
        .card-title {{ font-size: 15px; font-weight: 900; color: var(--navy); margin: 0; line-height: 1.45; height: 42px; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }}
        .card-price {{ color: var(--gold); font-weight: 950; font-size: 18px; margin-top: 10px; }}

        /* 詳情頁：究極多圖滑動輪播 (Image Slider) */
        .slider {{ display: flex; overflow-x: auto; scroll-snap-type: x mandatory; height: 480px; background: #000; scrollbar-width: none; }}
        .slider::-webkit-scrollbar {{ display: none; }}
        .slider img {{ flex: 0 0 100%; scroll-snap-align: start; object-fit: cover; }}
        
        /* 詳情內文資訊佈局 */
        .detail-box {{ padding: 50px 25px; background: #fff; border-radius: 55px 55px 0 0; margin-top: -60px; position: relative; z-index: 20; box-shadow: 0 -15px 30px rgba(0,0,0,0.03); }}
        .badge-row {{ display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 35px; }}
        .badge {{ background: var(--light); padding: 10px 18px; border-radius: 14px; font-size: 13px; color: var(--slate); font-weight: 700; text-decoration: none; border: 1.5px solid #edf2f7; }}
        .advice-box {{ background: linear-gradient(135deg, #f0f7ff, #e6f0ff); padding: 35px 30px; border-radius: 28px; border-left: 8px solid var(--gold); margin: 40px 0; line-height: 2.0; font-size: 17px; color: var(--navy); box-shadow: 0 10px 25px rgba(26,54,93,0.05); }}
        
        /* 質感頁尾 */
        .sk-footer {{ margin-top: 120px; padding: 100px 25px; background: linear-gradient(to bottom, #ffffff, #f9fafb); border-top: 1px solid #edf2f7; text-align: center; border-radius: 60px 60px 0 0; }}
        .sk-corp {{ color: var(--navy); font-size: 18px; font-weight: 900; letter-spacing: 2px; text-transform: uppercase; }}
        .sk-lic {{ color: var(--slate); font-size: 12px; line-height: 2.2; margin: 25px 0; }}
        .sk-slogan {{ color: var(--gold); font-size: 14px; font-weight: 800; letter-spacing: 4px; }}
        .sk-copyright {{ color: #cbd5e0; font-size: 11px; margin-top: 40px; letter-spacing: 1px; }}

        /* 底部行動 Bar (Two-Stage Call to Action) */
        .action-bar {{ position: fixed; bottom: 0; left: 50%; transform: translateX(-50%); width: 100%; max-width: 520px; padding: 25px 25px 45px; display: flex; gap: 15px; background: rgba(255,255,255,0.97); backdrop-filter: blur(25px); border-top: 1.5px solid #f1f1f1; z-index: 999; }}
        .btn {{ flex: 1; text-align: center; padding: 20px; border-radius: 22px; text-decoration: none; font-weight: 950; color: #fff; font-size: 16px; box-shadow: 0 8px 20px rgba(0,0,0,0.1); transition: 0.3s; }}
        .btn:active {{ transform: scale(0.95); }}
        .btn-call {{ background: #111827; }} .btn-line {{ background: #00B900; }}
        .btn-map-nav {{ display:block; text-align:center; padding:22px; background:var(--navy); color:#fff; text-decoration:none; border-radius:22px; margin-top:30px; font-weight:950; letter-spacing:1px; box-shadow: 0 8px 20px rgba(26,54,93,0.2); }}
    </style>
    <script>
        function filterByArea(area) {{
            document.querySelectorAll('.property-card').forEach(c => {{
                c.style.display = (area === 'all' || c.dataset.area === area) ? 'block' : 'none';
            }});
        }}
        function setTag(btn, cls) {{
            btn.parentElement.querySelectorAll('.'+cls).forEach(b=>b.classList.remove('active'));
            btn.classList.add('active');
        }}
    </script>
    </head>"""

# ============================================================
# 4. 主建置核心 (The Real Estate Engine)
# ============================================================
def build():
    root = Path(".")
    
    # 嚴謹初始化：清理舊檔案與分類目錄
    for d in CATEGORY_DIRS: 
        if (root/d).exists(): shutil.rmtree(root/d)
        (root/d).mkdir(exist_ok=True)
    for p in root.glob("p*"):
        if p.is_dir() and re.match(r'^p\d+$', p.name): shutil.rmtree(p)

    # 座標快取載入 (省錢必備)
    geocache = {{}}
    if GEOCACHE_PATH.exists():
        try: geocache = json.loads(GEOCACHE_PATH.read_text(encoding="utf-8"))
        except: pass

    # 抓取雲端試算表資料
    res = requests.get(SHEET_CSV_URL); res.encoding = "utf-8-sig"
    reader = csv.DictReader(res.text.splitlines())
    
    all_items = []
    area_groups, feature_groups, price_groups = {{}}, {{}}, {{}}
    map_data = []

    # 資料迭代處理
    for i, row in enumerate(reader):
        d = {{norm_text(k): norm_text(v) for k, v in row.items() if k}}
        if d.get("狀態", "").upper() in ["OFF", "FALSE", "NO"]: continue
        if not d.get("案名"): continue
        
        name = d["案名"]
        area = d.get("區域", "台中")
        price = d.get("價格", "面議")
        price_val = get_pure_price_num(price)
        price_bucket = get_price_bucket(price_val)
        imgs = normalize_imgs(d.get("圖片網址", ""))
        slug = f"p{{i}}"
        (root / slug).mkdir(exist_ok=True)
        internal_url = f"/{{slug}}/"
        
        # 標籤特徵拆分
        features = split_tags(d.get("特色", ""))
        
        # 座標快取對比 (Geocoding Logic)
        addr = d.get("地址", f"台中市{{area}}{{name}}")
        geo = geocache.get(addr, {{}})
        if geo.get("lat"):
            map_data.append({{
                "name": name, "price": price, "img": imgs[0], 
                "url": f"{{BASE_URL}}{{internal_url}}", "lat": geo["lat"], "lng": geo["lng"]
            }})

        # 生成奢侈感詳情頁 (Slider + Content)
        slides_html = "".join([f'<img src="{{u}}" loading="lazy" alt="{{esc(name)}}">' for u in imgs])
        badges_html = f'<a class="badge" href="/area/{{safe_slug(area)}}/">📍 {{area}}</a>'
        badges_html += "".join([f'<a class="badge" href="/feature/{{safe_slug(f)}}/">✨ {{f}}</a>' for f in features])
        badges_html += f'<a class="badge" href="/price/{{safe_slug(price_bucket)}}/">💰 {{price_bucket}}</a>'

        detail_content = f"""<div class="container">
            <div class="nav-bar">
                <a class="nav-item" href="/">精選物件</a>
                <a class="nav-item" href="/agent/">關於世塏</a>
            </div>
            <a href="../" style="position:absolute;top:95px;left:20px;background:rgba(255,255,255,0.92);padding:14px 25px;border-radius:18px;text-decoration:none;font-weight:950;color:var(--navy);z-index:100;backdrop-filter:blur(20px);box-shadow:0 8px 20px rgba(0,0,0,0.12);">← 返回清單</a>
            <div class="slider">{{slides_html}}</div>
            <div class="detail-box">
                <div style="color:var(--gold);font-weight:950;font-size:14px;letter-spacing:4px;margin-bottom:15px;text-transform:uppercase;">SK-L Exclusive Listing</div>
                <h1 style="font-size:32px;font-weight:980;color:var(--navy);margin:0;line-height:1.4;">{{esc(name)}}</h1>
                <div class="card-price" style="font-size:38px;margin:20px 0;">{{esc(price)}}</div>
                <div class="badge-row">{{badges_html}}</div>
                <div style="line-height:2.4;font-size:18px;color:#475569;margin-bottom:50px;letter-spacing:0.5px;">{{esc(d.get('描述','')).replace('、','<br>• ')}}</div>
                <div class="advice-box">
                    <strong style="color:var(--navy);font-size:20px;display:block;margin-bottom:15px;">💡 SK-L 置產顧問深度解析</strong>
                    此物件位於{{area}}核心區域，具備極佳的保值與增值潛力。若您對本案感興趣，建議直接點擊下方 LINE 索取該社區近期的成交行情分析與詳細產權資料。
                </div>
                <a href="https://www.google.com/maps/search/?api=1&query={{urllib.parse.quote(addr)}}" target="_blank" class="btn-map-nav">📍 前往物件地圖導航位置</a>
                {{LEGAL_FOOTER}}
            </div>
            <div class="action-bar">
                <a class="btn btn-call" href="tel:{{MY_PHONE}}">📞 立即致電</a>
                <a class="btn btn-line" href=" {{MY_LINE_URL}} ">💬 LINE 諮詢</a>
            </div>
        </div>"""
        
        # 寫入子網頁
        (root / slug / "index.html").write_text(f"<!doctype html><html lang='zh-TW'>{{get_head(name, d.get('描述',''), imgs[0], og_url=f'{{BASE_URL}}{{internal_url}}')}}<body>{{detail_content}}</body></html>", encoding="utf-8")

        # 整理全站資料庫
        item_data = {{"name": name, "area": area, "price": price, "img": imgs[0], "url": f"{{BASE_URL}}{{internal_url}}", "features": features}}
        all_items.append(item_data)
        
        # 多維度分類處理
        area_groups.setdefault(area, []).append(item_data)
        price_groups.setdefault(price_bucket, []).append(item_data)
        for f in features: feature_groups.setdefault(f, []).append(item_data)

    # ============================================================
    # 5. 生成分類入口與 SEO 索引頁面 (SEO List Generation)
    # ============================================================
    def build_list_page(target_path, title, items_list):
        cards = "".join([f"""<a href="{{it['url']}}" class="card property-card" data-area="{{it['area']}}">
            <img src="{{it['img']}}" loading="lazy" alt="{{it['name']}}"><div class="card-body"><h3 class="card-title">{{it['name']}}</h3><div class="card-price">{{it['price']}}</div></div></a>""" for it in items_list])
        body_html = f"""<div class="container">
            <div class="nav-bar"><a class="nav-item" href="/">精選首頁</a><a class="nav-item" href="/agent/">關於世塏</a></div>
            <div style="padding:45px 20px 10px;"><h1 style="font-size:28px;color:var(--navy);font-weight:980;">{{title}}</h1></div>
            <div class="grid-list">{{cards}}</div>{{LEGAL_FOOTER}}
            <div class="action-bar"><a class="btn btn-call" href="tel:{{MY_PHONE}}">📞 立即致電</a><a class="btn btn-line" href="{{MY_LINE_URL}}">💬 LINE 諮詢</a></div>
        </div>"""
        (root / target_path).mkdir(parents=True, exist_ok=True)
        (root / target_path / "index.html").write_text(f"<!doctype html><html lang='zh-TW'>{{get_head(title)}}<body>{{body_html}}</body></html>", encoding="utf-8")

    # 生成分類頁面
    for ar, its in area_groups.items(): build_list_page(f"area/{{safe_slug(ar)}}", f"{{ar}}精選房產物件清單", its[::-1])
    for ft, its in feature_groups.items(): build_list_page(f"feature/{{safe_slug(ft)}}", f"特色推薦：{{ft}}房產", its[::-1])
    for pb, its in price_groups.items(): build_list_page(f"price/{{safe_slug(pb)}}", f"預算帶搜尋：{{pb}}", its[::-1])

    # 生成主首頁 (Home Grid + Map Engine)
    area_btns = "".join([f"<button class='tag' onclick='setTag(this,\"tag\");filterByArea(\"{{a}}\")'>{{a}}</button>" for a in sorted(area_groups.keys())])
    home_cards_html = "".join([f"""<a href="{{it['url']}}" class="card property-card" data-area="{{it['area']}}">
        <img src="{{it['img']}}" loading="lazy" alt="{{it['name']}}"><div class="card-body"><h3 class="card-title">{{it['name']}}</h3><div class="card-price">{{it['price']}}</div></div></a>""" for it in all_items[::-1]])
    
    home_html = f"""<div class="container">
        <div class="hero"><div class="hero-content"><h1>{{SITE_TITLE}}</h1><p style="letter-spacing:4px;margin-top:12px;font-weight:900;">{{SITE_SLOGAN}}</p></div></div>
        <div id="map"></div>
        <div class="filter-section">
            <div class="filter-group"><button class="tag active" onclick="setTag(this,'tag');filterByArea('all')">全部區域</button>{{area_btns}}</div>
        </div>
        <div class="grid-list" id="list_container">{{home_cards_html}}</div>{{LEGAL_FOOTER}}
        <div class="action-bar"><a class="btn btn-call" href="tel:{{MY_PHONE}}">📞 立即致電</a><a class="btn btn-line" href="{{MY_LINE_URL}}">💬 LINE 諮詢</a></div>
    </div>"""
    (root / "index.html").write_text(f"<!doctype html><html lang='zh-TW'>{{get_head(SITE_TITLE, is_home=True, map_data=map_data)}}<body>{home_html}</body></html>", encoding="utf-8")

    # 生成聯絡頁面 (Agent Page)
    build_list_page("agent", "關於專業顧問林世塏", []) 

    print(f"🚀 SK-L 究極旗艦引擎建置完成！共處理 {{len(all_items)}} 個物件。")

if __name__ == "__main__": build()
