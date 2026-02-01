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
# 1. 核心品牌與技術配置 (SEO 地基)
# ============================================================
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQShAl0-TbUU0MQdYVe53im2T6lXQgh_7g-bdL6HHpIBFtA2yfIAMbPw4J9RgZUkROb9AAiMhnRC0kH/pub?output=csv"
BASE_URL = "https://shihkailin.github.io/taichung-houses"

SITE_TITLE = "SK-L 大台中房地產"
SITE_SLOGAN = "林世塏｜專業顧問 · 誠信置產 · 台中精選房產"
GA4_ID = "G-B7WP9BTP8X"

MY_NAME = "林世塏"
MY_PHONE = "0938-615-351"
MY_LINE_URL = "https://line.me/ti/p/FDsMyAYDv" # 已修正為您的正確網址

# Google Maps API 與快取系統
MAPS_API_KEY = os.getenv("MAPS_API_KEY", "AIzaSyDzgnI2Ucv622CRkWwo2GE5JRrs_Y4HQY0")
GEOCACHE_PATH = Path("geocache.json")

# 靜態資源路徑
IMG_RAW_BASE = "https://raw.githubusercontent.com/ShihKaiLin/taichung-houses/main/images/"
DEFAULT_HERO = f"{IMG_RAW_BASE}hero_bg.jpg"
POSTS_DIR = Path("posts")

# SEO 自動索引分類路徑
CATEGORY_DIRS = ["area", "feature", "price", "life", "agent"]

# 品牌法律頁尾 (解決 NameError)
LEGAL_FOOTER = f"""
<div class="sk-footer">
    <div class="sk-footer-inner">
        <strong class="sk-corp">英柏國際地產有限公司</strong>
        <p class="sk-lic">中市地價二字第 1070029259 號<br>經紀人：王一媖（103）中市經紀字第 00678 號</p>
        <div class="sk-slogan">專業誠信 · 卓越服務 · 深耕台中房產</div>
        <div class="sk-copyright">© 2026 SK-L Branding. All Rights Reserved.</div>
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
            out.append(f"<h{level} style='color:var(--navy);margin:40px 0 20px;'>{esc(raw.lstrip('#'))}</h{level}>")
        elif raw.startswith("- "):
            if not in_list: out.append("<ul style='line-height:2.0;color:#475569;'>"); in_list = True
            out.append(f"<li>{esc(raw[2:])}</li>")
        else:
            out.append(f"<p style='line-height:2.2;color:#475569;margin-bottom:15px;'>{esc(raw)}</p>")
    if in_list: out.append("</ul>")
    return "\n".join(out)

# ============================================================
# 3. 頁面標頭與 RWD 視覺系統
# ============================================================
def get_head(title, desc="", og_img="", is_home=False, map_data=None, extra_ld=None):
    seo_desc = esc(desc)[:120] if desc else esc(SITE_SLOGAN)
    og_img = og_img if (og_img and str(og_img).startswith("http")) else DEFAULT_HERO
    
    # 組合 SEO 結構化數據
    lds = [{"@context": "https://schema.org", "@type": "RealEstateAgent", "name": SITE_TITLE, "telephone": MY_PHONE, "url": BASE_URL}]
    if extra_ld: lds.append(extra_ld)
    
    map_json = json.dumps(map_data, ensure_ascii=False) if map_data else "[]"
    map_logic = f"""
    <script src="https://maps.googleapis.com/maps/api/js?key={MAPS_API_KEY}&callback=initMap" async defer></script>
    <script>
        function initMap() {{
            const el = document.getElementById('map'); if(!el) return;
            const data = {map_json};
            const map = new google.maps.Map(el, {{ center: {{lat: 24.162, lng: 120.647}}, zoom: 12, disableDefaultUI: true, zoomControl: true, styles: [{{"featureType":"poi","stylers":[{{"visibility":"off"}}]}}] }});
            const infoWindow = new google.maps.InfoWindow();
            data.forEach(loc => {{
                if(!loc.lat) return;
                const marker = new google.maps.Marker({{ position: {{lat: parseFloat(loc.lat), lng: parseFloat(loc.lng)}}, map: map, title: loc.name, animation: google.maps.Animation.DROP }});
                marker.addListener('click', () => {{
                    infoWindow.setContent(`<div style="padding:10px;width:180px;"><div style="background:url('${{loc.img}}') center/cover;height:90px;border-radius:8px;margin-bottom:8px;"></div><h4 style="margin:0;color:#1A365D;font-size:14px;">${{loc.name}}</h4><div style="color:#C5A059;font-weight:900;font-size:16px;margin:5px 0;">${{loc.price}}</div><a href="${{loc.url}}" style="display:block;text-align:center;background:#1A365D;color:#fff;text-decoration:none;padding:8px;border-radius:8px;font-size:12px;font-weight:900;">查看分析建議</a></div>`);
                    infoWindow.open(map, marker);
                }});
            }});
        }}
        function filter(area) {{
            document.querySelectorAll('.tag').forEach(t => t.classList.remove('active'));
            event.target.classList.add('active');
            document.querySelectorAll('.card-anchor').forEach(c => {{
                c.style.display = (area === 'all' || c.dataset.area === area) ? 'block' : 'none';
            }});
        }}
    </script>""" if is_home else ""

    return f"""<head>
    <meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=0">
    <title>{esc(title)}</title>
    <meta name="description" content="{seo_desc}">
    <meta property="og:title" content="{esc(title)}"><meta property="og:image" content="{esc(og_img)}">
    <script type="application/ld+json">{json.dumps(lds)}</script>
    <script async src="https://www.googletagmanager.com/gtag/js?id={GA4_ID}"></script>
    <script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','{GA4_ID}');</script>
    {map_logic}
    <style>
        :root {{ --navy: #1A365D; --gold: #C5A059; --light: #F8FAFC; --shadow: 0 10px 40px rgba(0,0,0,0.06); }}
        body {{ font-family: 'PingFang TC', sans-serif; margin: 0; background: #f1f5f9; color: #2D3748; -webkit-font-smoothing: antialiased; }}
        
        /* RWD 容器：電腦版自動寬度 */
        .container {{ width: 100%; max-width: 100%; margin: auto; min-height: 100vh; position: relative; background: #fff; }}
        @media (min-width: 768px) {{ .container {{ max-width: 1200px; box-shadow: 0 0 80px rgba(0,0,0,0.05); }} }}
        
        .header {{ background: var(--navy); color: #fff; padding: 18px 20px; display: flex; justify-content: space-between; align-items: center; position: sticky; top: 0; z-index: 1000; }}
        .logo {{ font-weight: 900; letter-spacing: 2px; text-decoration: none; color: #fff; font-size: 20px; }}

        #map {{ height: 350px; background: #eee; width: 100%; border-bottom: 5px solid #fff; }}
        @media (min-width: 768px) {{ #map {{ height: 500px; }} }}
        
        .filters {{ padding: 25px 16px 10px; overflow-x: auto; display: flex; gap: 10px; scrollbar-width: none; }}
        .tag {{ padding: 10px 22px; border-radius: 50px; background: var(--light); border: 1px solid #e2e8f0; font-size: 13px; font-weight: 700; cursor: pointer; white-space: nowrap; transition: 0.3s; }}
        .tag.active {{ background: var(--navy); color: #fff; border-color: var(--navy); box-shadow: 0 5px 15px rgba(26,54,93,0.2); }}

        /* 網格 RWD：手機 2 欄, 電腦 4 欄 */
        .grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; padding: 16px; }}
        @media (min-width: 768px) {{ .grid {{ grid-template-columns: repeat(4, 1fr); gap: 24px; padding: 30px; }} }}
        
        .card {{ border-radius: 24px; overflow: hidden; background: #fff; box-shadow: var(--shadow); border: 1px solid #f1f5f9; display: flex; flex-direction: column; transition: 0.3s; height: 100%; }}
        .card img {{ width: 100%; height: 160px; object-fit: cover; background: #f1f5f9; }}
        @media (min-width: 768px) {{ .card img {{ height: 210px; }} .card:hover {{ transform: translateY(-10px); }} }}
        .card-body {{ padding: 15px; flex-grow: 1; }}
        .card-title {{ font-size: 15px; font-weight: 800; color: var(--navy); margin: 0; line-height: 1.45; height: 44px; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }}
        .card-price {{ color: var(--gold); font-weight: 900; font-size: 19px; margin-top: 10px; }}
        .card-anchor {{ text-decoration: none; color: inherit; }}

        .slider {{ display: flex; overflow-x: auto; scroll-snap-type: x mandatory; height: 420px; background: #000; scrollbar-width: none; }}
        @media (min-width: 768px) {{ .slider {{ height: 650px; }} }}
        .slider img {{ flex: 0 0 100%; scroll-snap-align: start; object-fit: cover; }}
        
        .info-box {{ padding: 40px 20px; background: #fff; border-radius: 40px 40px 0 0; margin-top: -40px; position: relative; z-index: 20; }}
        @media (min-width: 768px) {{ .info-box {{ max-width: 850px; margin: -60px auto 0; border-radius: 50px; box-shadow: var(--shadow); padding: 60px; }} }}
        .spec-badge {{ display: inline-block; background: #f1f5f9; padding: 8px 15px; border-radius: 10px; font-size: 13px; color: #64748b; margin: 0 6px 10px 0; font-weight: 700; border: 1px solid #edf2f7; text-decoration: none; }}
        
        .contact-card {{ background: #fff; border: 1px solid #edf2f7; border-radius: 25px; padding: 30px; margin: 30px 0; box-shadow: var(--shadow); display: flex; flex-direction: column; }}
        @media (min-width: 768px) {{ .contact-card {{ flex-direction: row; align-items: center; justify-content: space-between; }} }}
        .agent-info {{ display: flex; align-items: center; gap: 20px; }}
        .agent-photo {{ width: 70px; height: 70px; border-radius: 50%; object-fit: cover; border: 3px solid var(--navy); }}
        .btn-line-cta {{ display: block; text-align: center; background: #00B900; color: #fff; text-decoration: none; padding: 18px 35px; border-radius: 15px; font-weight: 950; margin-top: 20px; box-shadow: 0 8px 20px rgba(0,185,0,0.25); font-size: 16px; }}
        @media (min-width: 768px) {{ .btn-line-cta {{ margin-top: 0; }} }}

        .sk-footer {{ margin-top: 120px; padding: 100px 25px; background: linear-gradient(to bottom, #ffffff, #f9fafb); border-top: 1px solid #edf2f7; text-align: center; border-radius: 60px 60px 0 0; }}
        .sk-corp {{ color: var(--navy); font-size: 18px; font-weight: 900; letter-spacing: 2px; }}
        .sk-lic {{ color: var(--slate); font-size: 12px; line-height: 2.2; margin: 25px 0; }}
        .sk-slogan {{ color: var(--gold); font-size: 14px; font-weight: 800; letter-spacing: 4px; }}

        .action-bar {{ position: fixed; bottom: 0; left: 50%; transform: translateX(-50%); width: 100%; max-width: 1200px; padding: 25px 25px 45px; display: flex; gap: 15px; background: rgba(255,255,255,0.97); backdrop-filter: blur(25px); border-top: 1.5px solid #f1f1f1; z-index: 1000; visibility: visible; }}
        .btn {{ flex: 1; text-align: center; padding: 18px; border-radius: 18px; text-decoration: none; font-weight: 950; color: #fff; font-size: 16px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); }}
        .btn-call {{ background: #111827; }} .btn-line {{ background: #00B900; }}
    </style>
    </head>"""# ============================================================
# 4. 建置引擎主邏輯 (The SEO & Content Engine)
# ============================================================
def build():
    root = Path(".")
    
    # 徹底清理舊分頁，確保搜尋引擎索引不混亂
    for d in CATEGORY_DIRS: 
        if (root/d).exists(): shutil.rmtree(root/d)
        (root/d).mkdir(exist_ok=True)
    for p in root.glob("p*"):
        if p.is_dir() and re.match(r'^p\d+$', p.name): shutil.rmtree(p)
    
    # 座標快取處理：修正型別判斷，確保使用「地址」作為唯一 Key
    geocache = {}
    if GEOCACHE_PATH.exists():
        try:
            raw_content = GEOCACHE_PATH.read_text(encoding="utf-8")
            loaded_cache = json.loads(raw_content)
            if isinstance(loaded_cache, dict): geocache = loaded_cache
        except: pass

    # 從雲端獲取最新案源
    try:
        res = requests.get(SHEET_CSV_URL, timeout=20)
        res.encoding = "utf-8-sig"
        reader = csv.DictReader(res.text.splitlines())
    except Exception as e:
        print(f"❌ 試算表抓取失敗: {e}")
        return
    
    all_items = []
    area_groups, feat_groups, price_groups = {}, {}, {}
    map_data, sitemap_urls = [], [f"{BASE_URL}/"]

    # --- 遍歷資料庫物件並生成 SEO 內容 ---
    for i, row in enumerate(reader):
        d = {norm(k): norm(v) for k, v in row.items() if k}
        if d.get("狀態", "").upper() in ["OFF", "FALSE", "NO"]: continue
        if not d.get("案名"): continue
        
        name, reg, price = d["案名"], d.get("區域", "台中"), d.get("價格", "面議")
        price_num = get_pure_price(price)
        price_bucket = get_price_bucket(price_num)
        imgs = normalize_imgs(d.get("圖片網址", ""))
        features = split_tags(d.get("特色", ""))
        slug = f"p{i}"
        (root / slug).mkdir(exist_ok=True)
        s_url = f"{BASE_URL}/{slug}/"
        sitemap_urls.append(s_url)

        # 座標處理：精確對比地址字串
        addr = d.get("地址", f"台中市{reg}{name}")
        geo = geocache.get(addr)
        if geo and isinstance(geo, dict) and "lat" in geo:
            map_data.append({
                "name": name, "price": price, "url": f"./{slug}/", 
                "lat": geo["lat"], "lng": geo["lng"], "img": imgs[0]
            })

        # 生成高品質詳情頁 (含 JSON-LD)
        listing_ld = {
            "@context": "https://schema.org",
            "@type": "RealEstateListing",
            "name": name, "description": d.get('描述','')[:150],
            "image": imgs[0], "url": s_url,
            "address": {"@type": "PostalAddress", "addressLocality": reg, "addressCountry": "TW"}
        }
        
        slides = "".join([f'<img src="{u}" loading="lazy" alt="{esc(name)}">' for u in imgs])
        
        # 建立 SEO 分類標籤 (增加內部連結權重)
        badges = [
            f'<a class="spec-badge" href="/area/{safe_slug(reg)}/">📍 {reg}</a>',
            f'<a class="spec-badge" href="/price/{safe_slug(price_bucket)}/">💰 {price_bucket}</a>'
        ]
        for f in features: badges.append(f'<a class="spec-badge" href="/feature/{safe_slug(f)}/">✨ {f}</a>')

        # 組合詳情頁 HTML
        detail_html = f"""<div class="container">
            <div class="header">
                <a href="../" class="logo">← {SITE_TITLE}</a>
                <div style="font-size:12px; font-weight:700;">台中精選置產專家</div>
            </div>
            <div class="slider">{slides}</div>
            <div class="info-box">
                <div style="color:var(--gold); font-weight:950; font-size:14px; letter-spacing:4px; margin-bottom:15px; text-transform:uppercase;">SK-L Exclusive Listing</div>
                <h1 style="font-size:32px; font-weight:950; color:var(--navy); margin:0 0 15px; line-height:1.4;">{esc(name)}</h1>
                <div style="font-size:38px; color:var(--gold); font-weight:950; margin-bottom:30px; letter-spacing:-1px;">{esc(price)}</div>
                <div class="badge-row">{" ".join(badges)}</div>
                
                <div style="line-height:2.4; font-size:17px; color:#475569; margin-bottom:50px; letter-spacing:0.5px;">
                    {esc(d.get('描述','')).replace('、','<br>• ')}
                </div>
                
                <div class="contact-card">
                    <div class="agent-info">
                        <img src="{IMG_RAW_BASE}agent_photo.jpg" class="agent-photo" onerror="this.src='https://placehold.co/100x100?text=SK-L'">
                        <div><strong style="font-size:20px; color:var(--navy);">{esc(MY_NAME)}</strong><br><span style="font-size:13px; color:var(--slate); font-weight:700;">專業房產顧問 · 您的置產助手</span></div>
                    </div>
                    <a href="{MY_LINE_URL}" target="_blank" class="btn-line-cta">💬 加 LINE 立即諮詢案情</a>
                </div>
                
                <div style="background:#f8fafc; padding:35px; border-radius:30px; font-size:16px; color:var(--slate); line-height:1.9; margin-top:40px; border-left:6px solid var(--navy);">
                    <strong>💡 SK-L 置產顧問分析：</strong><br>
                    此物件位於{reg}核心區段，具備極佳的保值潛力。若您想了解該社區近一年的實價登錄行情、銀行鑑價金額，或是想安排實地看屋，歡迎直接點擊 LINE 聯繫，我將提供您最詳盡的數據報告。
                </div>

                <a href="http://maps.google.com/?q={urllib.parse.quote(addr)}" target="_blank" style="display:block; text-align:center; padding:22px; background:var(--navy); color:#fff; text-decoration:none; border-radius:20px; font-weight:950; margin-top:35px; letter-spacing:1px; box-shadow: 0 10px 30px rgba(26,54,93,0.25);">📍 在地圖上開啟導航位置</a>
                {LEGAL_FOOTER}
            </div>
            <div class="action-bar"><a class="btn btn-call" href="tel:{MY_PHONE}">📞 立即致電</a><a class="btn btn-line" href="{MY_LINE_URL}" target="_blank">💬 LINE 諮詢</a></div>
        </div>"""
        (root / slug / "index.html").write_text(f"<!doctype html><html lang='zh-TW'>{get_head(name, d.get('描述',''), imgs[0], extra_ld=listing_ld)}<body>{detail_html}</body></html>", encoding="utf-8")

        # 建立全局物件索引
        item = {"name": name, "area": reg, "price": price, "img": imgs[0], "url": f"/{slug}/"}
        all_items.append(item)
        area_groups.setdefault(reg, []).append(item)
        price_groups.setdefault(price_bucket, []).append(item)
        for f in features: feat_groups.setdefault(f, []).append(item)

    # ============================================================
    # 5. 生成分類入口分頁 (SEO Landing Pages)
    # ============================================================
    def build_list_page(path, title, items):
        cards_html = "".join([f'<a href="{it["url"]}" class="card-anchor property-card" data-area="{it["area"]}"><div class="card"><img src="{it["img"]}" loading="lazy" alt="{esc(it["name"])}"><div class="card-body"><h3 class="card-title">{esc(it["name"])}</h3><div class="card-price">{esc(it["price"])}</div><div style="margin-top:15px; font-size:12px; color:var(--navy); font-weight:900; border-top:1px solid #f1f5f9; padding-top:12px; text-align:center;">查看專業顧問建議 →</div></div></div></a>' for it in items])
        body_content = f"""<div class="container">
            <div class="header"><a href="/" class="logo">{SITE_TITLE}</a></div>
            <div style="padding:50px 20px 10px;"><h1 style="font-size:32px; color:var(--navy); font-weight:980; letter-spacing:-1px;">{title}</h1></div>
            <div class="grid">{cards_html}</div>
            {LEGAL_FOOTER}
            <div class="action-bar"><a class="btn btn-call" href="tel:{MY_PHONE}">📞 直接致電</a><a class="btn btn-line" href="{MY_LINE_URL}" target="_blank">💬 LINE 諮詢</a></div>
        </div>"""
        (root / path).mkdir(parents=True, exist_ok=True)
        (root / path / "index.html").write_text(f"<!doctype html><html lang='zh-TW'>{get_head(title)}<body>{body_content}</body></html>", encoding="utf-8")

    # 生成 Area, Feature, Price 三大維度索引
    for ar, its in area_groups.items(): 
        build_list_page(f"area/{safe_slug(ar)}", f"{ar}精選房產物件清單", its[::-1])
        sitemap_urls.append(f"{BASE_URL}/area/{safe_slug(ar)}/")
    for ft, its in feat_groups.items(): 
        build_list_page(f"feature/{safe_slug(ft)}", f"特色推薦：{ft}房產", its[::-1])
        sitemap_urls.append(f"{BASE_URL}/feature/{safe_slug(ft)}/")
    for pb, its in price_groups.items(): 
        build_list_page(f"price/{safe_slug(pb)}", f"預算帶搜尋：{pb}", its[::-1])
        sitemap_urls.append(f"{BASE_URL}/price/{safe_slug(pb)}/")

    # --- 處理 Markdown 文章系統 (Life Posts) ---
    post_links = []
    if POSTS_DIR.exists():
        for md_file in sorted(POSTS_DIR.glob("*.md")):
            slug = safe_slug(md_file.stem)
            md_content = md_file.read_text(encoding="utf-8")
            html_content = md_to_html(md_content)
            (root / "life" / slug).mkdir(parents=True, exist_ok=True)
            (root / "life" / slug / "index.html").write_text(f"<!doctype html><html lang='zh-TW'>{get_head(md_file.stem)}<body><div class='container'><div class='header'><a href='/life/' class='logo'>← 房產指南專區</a></div><div style='padding:60px 25px;max-width:800px;margin:auto;'>{html_content}<div style='margin-top:80px;border-top:2px solid #f1f5f9;padding-top:40px;'><a class='spec-badge' href='/'>🏠 回首頁查看最新物件</a><a class='spec-badge' href='tel:{MY_PHONE}'>📞 聯絡顧問：{MY_NAME}</a></div></div>{LEGAL_FOOTER}</div></body></html>", encoding="utf-8")
            post_links.append(f"<a class='spec-badge' href='/life/{slug}/' style='display:block;padding:30px;margin-bottom:20px;background:#f8fafc;font-size:20px;border-radius:20px;border:1px solid #edf2f7; text-decoration:none;'>📝 {md_file.stem}</a>")
            sitemap_urls.append(f"{BASE_URL}/life/{slug}/")
    
    life_body = f"<div class='container'><div class='header'><a href='/' class='logo'>← 回首頁</a></div><div style='padding:50px 25px;'><h1>房產生活與區域深度指南</h1><p style='color:#64748b;margin-bottom:50px;font-size:18px;'>深入了解台中各區發展趨勢、捷運利多與專業買屋建議。</p>{''.join(post_links)}</div>{LEGAL_FOOTER}</div>"
    (root / "life" / "index.html").write_text(f"<!doctype html><html>{get_head('房產生活指南')}<body>{life_body}</body></html>", encoding="utf-8")
    sitemap_urls.append(f"{BASE_URL}/life/")

    # 聯絡頁 (SEO 入口之一)
    build_list_page("agent", "關於專業置產顧問：林世塏", [])
    sitemap_urls.append(f"{BASE_URL}/agent/")

    # ============================================================
    # 6. 生成主首頁 (Home Engine) 與 Sitemap
    # ============================================================
    reg_btns = "".join([f'<button class="tag" onclick="filter(\'{a}\')">{a}</button>' for a in sorted(area_groups.keys())])
    home_cards = "".join([f'<a href="{it["url"]}" class="card-anchor property-card" data-area="{it["area"]}"><div class="card"><img src="{it["img"]}" loading="lazy" alt="{esc(it["name"])}"><div class="card-body"><h3 class="card-title">{esc(it["name"])}</h3><div class="card-price">{esc(it["price"])}</div><div style="margin-top:15px; font-size:12px; color:var(--navy); font-weight:900; border-top:1px solid #f1f5f9; padding-top:12px; text-align:center;">查看專業顧問建議 →</div></div></div></a>' for it in all_items[::-1]])
    
    home_html = f"""<div class="container">
        <div class="header">
            <a href="./" class="logo">{SITE_TITLE}</a>
            <div style="font-size:12px;opacity:0.8;font-weight:700;">{SITE_SLOGAN}</div>
        </div>
        <div id="map"></div>
        <div class="filters">
            <button class="tag active" onclick="filter('all')">全部區域</button>
            {reg_btns}
        </div>
        <div class="grid">{home_cards}</div>
        {LEGAL_FOOTER}
        <div class="action-bar">
            <a class="btn btn-call" href="tel:{MY_PHONE}">📞 立即致電</a>
            <a class="btn btn-line" href="{MY_LINE_URL}" target="_blank">💬 加 LINE 諮詢</a>
        </div>
    </div>"""
    (root / "index.html").write_text(f"<!doctype html><html lang='zh-TW'>{get_head(SITE_TITLE, is_home=True, map_data=map_data)}<body>{home_html}</body></html>", encoding="utf-8")

    # 生成 Sitemap.xml (讓 Google 爬蟲自動收錄全站 131+ 個頁面)
    xml = '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    for u in sorted(set(sitemap_urls)):
        xml += f'<url><loc>{u}</loc><lastmod>{datetime.now().strftime("%Y-%m-%d")}</lastmod><changefreq>weekly</changefreq></url>'
    (root / "sitemap.xml").write_text(xml + '</urlset>', encoding="utf-8")

    print(f"🚀 SEO 旗艦引擎 5.0 建置完成！共索引 {len(all_items)} 個物件，地圖點位：{len(map_data)}")

if __name__ == "__main__":
    build()
