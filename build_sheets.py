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

# ============================================================
# 1. 個人品牌核心配置 (Core Configuration)
# ============================================================
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQShAl0-TbUU0MQdYVe53im2T6lXQgh_7g-bdL6HHpIBFtA2yfIAMbPw4J9RgZUkROb9AAiMhnRC0kH/pub?output=csv"

MY_PHONE = "0938-615-351"
MY_LINE_URL = "https://line.me/ti/p/FDsMyAYDv"
SITE_TITLE = "SK-L 大台中房地產"
GA4_ID = "G-B7WP9BTP8X"

# Google Maps API 關鍵配置
MAPS_API_KEY = os.getenv("MAPS_API_KEY", "AIzaSyDzgnI2Ucv622CRkWwo2GE5JRrs_Y4HQY0")

# 備用英雄圖與圖床邏輯
HERO_BG = "https://raw.githubusercontent.com/ShihKaiLin/taichung-houses/main/images/hero_bg.jpg"

# ============================================================
# 2. 品牌質感法律頁尾 (Legal & Branding Footer)
# ============================================================
LEGAL_FOOTER = """
<div class="sk-legal-footer">
    <div class="sk-footer-inner">
        <div class="sk-brand-info">
            <strong class="sk-corp-name">英柏國際地產有限公司</strong>
            <p class="sk-license">
                中市地價二字第 1070029259 號<br>
                王一媖 經紀人 (103) 中市經紀字第 00678 號
            </p>
        </div>
        <div class="sk-copyright">
            <span>© 2026 SK-L Branding. All Rights Reserved.</span>
            <p class="sk-slogan">專業 · 誠信 · 卓越服務 · 深耕台中房地產</p>
        </div>
    </div>
</div>
<style>
    .sk-legal-footer { 
        margin: 120px 0 0; 
        padding: 80px 25px; 
        text-align: center; 
        border-top: 1px solid #edf2f7; 
        background: linear-gradient(to bottom, #ffffff, #f8fafc); 
        border-radius: 60px 60px 0 0; 
    }
    .sk-corp-name { color: #1A365D; font-size: 16px; display: block; margin-bottom: 12px; letter-spacing: 2px; font-weight: 800; }
    .sk-license { font-size: 12px; color: #718096; line-height: 2; margin-bottom: 30px; }
    .sk-copyright { font-size: 11px; color: #a0aec0; border-top: 1px solid #f1f5f9; padding-top: 30px; }
    .sk-slogan { margin-top: 10px; color: #cbd5e0; letter-spacing: 1px; }
</style>
"""

def esc(s):
    return html.escape(str(s or "").strip())

# ============================================================
# 3. 頁面標頭與樣式生成 (Header & UI Styles)
# ============================================================
def get_head(title, desc="", img="", is_home=False, map_data_json="[]"):
    seo_desc = esc(desc)[:80] if desc else f"{SITE_TITLE} - 精選台中優質房產，林世塏專業服務。"
    seo_img = img if img.startswith("http") else HERO_BG
    
    ga_script = f"""
    <script async src="https://www.googletagmanager.com/gtag/js?id={GA4_ID}"></script>
    <script>
        window.dataLayer = window.dataLayer || [];
        function gtag(){{dataLayer.push(arguments);}}
        gtag('js', new Date());
        gtag('config', '{GA4_ID}');
    </script>
    """

    map_script = ""
    if is_home:
        map_script = f"""
        <script src="https://maps.googleapis.com/maps/api/js?key={MAPS_API_KEY}"></script>
        <script>
            function filterAndSort() {{
                const reg = document.querySelector('.tag.f-reg.active').dataset.val;
                const type = document.querySelector('.tag.f-type.active').dataset.val;
                document.querySelectorAll('.property-card').forEach(c => {{
                    const mR = (reg === 'all' || c.dataset.region === reg);
                    const mT = (type === 'all' || c.dataset.type === type);
                    c.style.display = (mR && mT) ? 'block' : 'none';
                }});
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
                const geocoder = new google.maps.Geocoder();
                const locations = {map_data_json};
                locations.forEach(loc => {{
                    geocoder.geocode({{ 'address': loc.address }}, (results, status) => {{
                        if (status === 'OK') {{
                            const marker = new google.maps.Marker({{
                                position: results[0].geometry.location,
                                map: map,
                                title: loc.name
                            }});
                            marker.addListener("click", () => {{ window.location.href = loc.url; }});
                        }}
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
    <meta property="og:image" content="{seo_img}">
    {ga_script}
    {map_script}
    <style>
        :root {{ --navy: #1A365D; --gold: #C5A059; --bg: #F8FAFC; }}
        body {{ font-family: 'PingFang TC', sans-serif; margin: 0; background: #fff; color: #2D3748; }}
        .container {{ max-width: 500px; margin: auto; box-shadow: 0 0 60px rgba(0,0,0,0.05); min-height: 100vh; position: relative; }}
        
        /* Hero Section */
        .hero {{ height: 350px; background: url('{HERO_BG}') center/cover; display: flex; align-items: center; justify-content: center; color: #fff; position: relative; }}
        .hero::after {{ content:''; position:absolute; top:0; left:0; width:100%; height:100%; background: linear-gradient(to bottom, rgba(0,0,0,0.2), rgba(0,0,0,0.6)); }}
        .hero-content {{ position: relative; z-index: 2; text-align: center; }}
        .hero-content h2 {{ font-size: 36px; letter-spacing: 8px; font-weight: 900; text-shadow: 0 2px 10px rgba(0,0,0,0.3); }}
        
        /* Map UI */
        #map {{ height: 320px; border-radius: 30px; border: 6px solid #fff; margin: -60px 20px 0; position: relative; z-index: 10; box-shadow: 0 25px 50px rgba(0,0,0,0.12); }}
        
        /* Filters */
        .filter-group {{ display: flex; gap: 12px; overflow-x: auto; padding: 25px 20px 10px; scrollbar-width: none; }}
        .filter-group::-webkit-scrollbar {{ display: none; }}
        .tag {{ padding: 12px 24px; border-radius: 50px; background: #f1f5f9; font-size: 14px; border: 1px solid #e2e8f0; white-space: nowrap; font-weight: 600; cursor: pointer; transition: 0.3s; }}
        .tag.active {{ background: var(--navy); color: #fff; border-color: var(--navy); box-shadow: 0 5px 15px rgba(26,54,93,0.2); }}
        
        /* Property Cards */
        .property-card {{ margin: 35px 20px; border-radius: 32px; overflow: hidden; background: #fff; box-shadow: 0 15px 45px rgba(0,0,0,0.06); border: 1px solid #f1f5f9; transition: 0.3s; }}
        .card-img-wrap {{ position: relative; height: 320px; overflow: hidden; }}
        .card-img {{ width: 100%; height: 100%; object-fit: cover; }}
        .card-price-tag {{ position: absolute; bottom: 20px; left: 20px; background: var(--navy); color: #fff; padding: 8px 15px; border-radius: 12px; font-weight: 900; font-size: 22px; box-shadow: 0 5px 15px rgba(0,0,0,0.2); }}
        .card-info {{ padding: 25px; }}
        .card-title {{ font-size: 20px; font-weight: 800; color: var(--navy); margin: 0 0 12px; }}
        .badge {{ display: inline-flex; align-items: center; background: #f7fafc; padding: 6px 12px; border-radius: 8px; font-size: 13px; color: #4a5568; margin-right: 8px; margin-bottom: 8px; border: 1px solid #edf2f7; }}
        
        /* Action Bar */
        .action-bar {{ position: fixed; bottom: 0; left: 50%; transform: translateX(-50%); width: 100%; max-width: 500px; padding: 20px 25px 45px; display: flex; gap: 15px; background: rgba(255,255,255,0.95); backdrop-filter: blur(20px); border-top: 1px solid #f1f1f1; z-index: 999; }}
        .btn {{ flex: 1; text-align: center; padding: 18px; border-radius: 22px; text-decoration: none; font-weight: 800; color: #fff; font-size: 16px; }}
        .btn-call {{ background: #1A202C; }} .btn-line {{ background: #00B900; }}
        
        /* Detail Page Extras */
        .slide-wrap {{ display: flex; overflow-x: auto; scroll-snap-type: x mandatory; height: 480px; background: #1a202c; scrollbar-width: none; }}
        .slide-img {{ flex: 0 0 100%; scroll-snap-align: start; object-fit: cover; }}
        .advice-card {{ background: linear-gradient(135deg,#f0f7ff,#e6f0ff); padding: 30px; border-radius: 25px; margin: 30px 0; border-left: 8px solid var(--gold); line-height: 1.8; }}
        .btn-map-link {{ display:block; text-align:center; padding:22px; background:var(--navy); color:#fff; text-decoration:none; border-radius:20px; margin-top:20px; font-weight:800; }}
    </style>
</head>
"""

# ============================================================
# 4. 主建置邏輯 (Main Build Logic)
# ============================================================
def build():
    out = Path(".")
    for p in out.glob("p*"):
        if p.is_dir() and re.match(r'^p\d+$', p.name): shutil.rmtree(p)
    
    res = requests.get(SHEET_CSV_URL)
    res.encoding = 'utf-8-sig'
    reader = csv.DictReader(res.text.splitlines())
    
    items, map_data, regions, types = [], [], set(), set()
    
    for i, row in enumerate(reader):
        d = {str(k).strip(): str(v).strip() for k, v in row.items() if k}
        name = d.get("案名") or next((v for k,v in d.items() if "案名" in k), "")
        if not name or d.get("狀態", "").upper() in ["OFF", "FALSE"]: continue
        
        # 多圖輪播邏輯
        raw_imgs = d.get("圖片網址", "").split('|')
        imgs = [url.strip() for url in raw_imgs if url.strip().startswith('http')]
        if not imgs: imgs = [HERO_BG]
        
        reg, p_str, slug, addr = d.get("區域","台中"), d.get("價格","面議"), f"p{i}", d.get("地址", "")
        regions.add(reg); types.add(d.get("用途","住宅"))
        
        (out/slug).mkdir(exist_ok=True)
        i_url = f"./{slug}/"
        map_data.append({"name":name, "url":i_url, "address": addr or f"台中市{name}"})
        
        # 生成輪播圖片標籤
        slides_html = "".join([f'<img src="{u}" class="slide-img">' for u in imgs])
        
        # --- 物件詳情頁面 ---
        detail = f"""
        <div class="container">
            <a href="../" style="position:absolute;top:30px;left:25px;background:rgba(255,255,255,0.9);padding:12px 25px;border-radius:18px;text-decoration:none;font-weight:800;color:var(--navy);z-index:100;backdrop-filter:blur(15px);box-shadow:0 5px 15px rgba(0,0,0,0.1);">← 返回列表</a>
            <div class="slide-wrap">{slides_html}</div>
            <div style="padding:45px 30px;background:#fff;border-radius:50px 50px 0 0;margin-top:-60px;position:relative;z-index:20;">
                <h1 style="font-size:32px;font-weight:900;color:var(--navy);margin:0 0 15px;line-height:1.3;">{esc(name)}</h1>
                <div class="price" style="font-size:34px;color:var(--gold);font-weight:900;">{esc(p_str)}</div>
                
                <div style="margin:25px 0;">
                    <span class="badge">📍 {esc(reg)}</span>
                    <span class="badge">🏠 {esc(d.get("用途","住宅"))}</span>
                </div>
                
                <div style="line-height:2.4;font-size:17px;color:#4a5568;margin-bottom:40px;">
                    {esc(d.get("描述","")).replace('、','<br>• ')}
                </div>
                
                <div class="advice-card">
                    <strong style="color:var(--navy);font-size:18px;display:block;margin-bottom:10px;">💡 SK-L 置產顧問解析</strong>
                    此物件具備市場稀缺性。若想了解該社區近一年的實價登錄行情，或銀行貸款成數評估，歡迎直接點擊下方 LINE 諮詢。
                </div>
                
                <a href="https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(addr or name)}" target="_blank" class="btn-map-link">📍 在地圖上開啟位置</a>
                {LEGAL_FOOTER}
            </div>
            <div class="action-bar">
                <a href="tel:{MY_PHONE}" class="btn btn-call">致電 SK-L</a>
                <a href="{MY_LINE_URL}" class="btn btn-line">LINE 諮詢</a>
            </div>
        </div>
        """
        (out/slug/"index.html").write_text(f"<!doctype html><html lang='zh-TW'>{get_head(name, d.get('描述',''), imgs[0])}<body>{detail}</body></html>", encoding="utf-8")
        
        # --- 首頁物件卡片 ---
        items.append(f'''
        <div class="property-card" data-region="{esc(reg)}" data-type="{esc(d.get("用途","住宅"))}">
            <a href="{i_url}" class="card-img-wrap">
                <img src="{imgs[0]}" class="card-img">
                <div class="card-price-tag">{esc(p_str)}</div>
            </a>
            <div class="card-info">
                <h4 class="card-title">{esc(name)}</h4>
                <div class="badge">{esc(reg)}</div>
                <div class="badge">{esc(d.get("用途","住宅"))}</div>
                <a href="{i_url}" style="display:block;text-align:center;margin-top:20px;padding:16px;background:#f8fafc;color:var(--navy);text-decoration:none;font-weight:800;border-radius:15px;border:1px solid #edf2f7;">查看專業解析建議</a>
            </div>
        </div>''')

    # 篩選按鈕生成
    reg_btns = "".join([f"<button class='tag f-reg' data-val='{esc(r)}' onclick='setTag(this,\"f-reg\")'>{esc(r)}</button>" for r in sorted(regions)])
    type_btns = "".join([f"<button class='tag f-type' data-val='{esc(t)}' onclick='setTag(this,\"f-type\")'>{esc(t)}</button>" for t in sorted(types)])
    
    # --- 首頁總結 ---
    home_html = f"""
    <div class="container">
        <div class="hero"><div class="hero-content"><h2>{esc(SITE_TITLE)}</h2><p style="letter-spacing:4px;opacity:0.9;">PREMIUM REAL ESTATE</p></div></div>
        <div id="map"></div>
        <div class="filter-group">
            <button class="tag f-reg active" data-val="all" onclick="setTag(this,'f-reg')">全部區域</button>
            {reg_btns}
        </div>
        <div class="filter-group" style="padding-top:0;">
            <button class="tag f-type active" data-val="all" onclick="setTag(this,'f-type')">所有用途</button>
            {type_btns}
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

if __name__ == "__main__":
    build()
