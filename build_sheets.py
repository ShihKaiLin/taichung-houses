import os, csv, requests, html, shutil, re, urllib.parse
from pathlib import Path

# --- 1. 配置區 ---
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQShAl0-TbUU0MQdYVe53im2T6lXQgh_7g-bdL6HHpIBFtA2yfIAMbPw4J9RgZUkROb9AAiMhnRC0kH/pub?output=csv"
MY_PHONE = "0938-615-351"
MY_LINE_URL = "https://line.me/ti/p/FDsMyAYDv"
SITE_TITLE = "林世塏｜台中地圖找房"
GA4_ID = "G-B7WP9BTP8X"
MAPS_API_KEY = "AIzaSyDzgnI2Ucv622CRkWwo2GE5JRrs_Y4HQY0"
GITHUB_IMG_BASE = "https://raw.githubusercontent.com/ShihKaiLin/taichung-houses/main/images/"

# --- 2. 品牌合規資訊 ---
COMPANY_INFO = """
<div style="margin-top:40px; padding:20px; border-top:1px solid #f2f2f2; font-size:10px; color:#bbb; text-align:center; line-height:1.6;">
    英柏國際地產有限公司 | 中市地價二字第 1070029259 號<br>
    王一媖 經紀人 (103) 中市經紀字第 00678 號
</div>
"""

def esc(s): return html.escape(str(s or "").strip())

def get_head(title, ga_id, is_home=False, map_data=None):
    ga = f"""<script async src="https://www.googletagmanager.com/gtag/js?id={ga_id}"></script><script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','{ga_id}');</script>""" if ga_id else ""
    
    map_script = ""
    if is_home and map_data:
        # 修復大括號解析問題
        map_script = f"""
        <script src="https://maps.googleapis.com/maps/api/js?key={MAPS_API_KEY}&libraries=places"></script>
        <script>
            function initMap() {{
                const mapEl = document.getElementById("map");
                const map = new google.maps.Map(mapEl, {{
                    center: {{ lat: 24.162, lng: 120.647 }},
                    zoom: 12,
                    disableDefaultUI: true,
                    zoomControl: true,
                    styles: [{{ "featureType": "poi", "stylers": [{{ "visibility": "off" }}] }}]
                }});
                const geocoder = new google.maps.Geocoder();
                const locations = {map_data};
                locations.forEach(loc => {{
                    geocoder.geocode({{ 'address': loc.address }}, (results, status) => {{
                        if (status === 'OK') {{
                            const marker = new google.maps.Marker({{
                                map: map,
                                position: results[0].geometry.location,
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
        {ga}{map_script}
        <style>
            :root {{ --primary: #1A365D; --accent: #E53E3E; --bg: #F7FAFC; }}
            body {{ font-family: 'PingFang TC', sans-serif; background: var(--bg); margin: 0; color: #2D3748; }}
            .container {{ max-width: 500px; margin: auto; min-height: 100vh; padding-bottom: 120px; background: #fff; position: relative; }}
            .hero-banner {{
                position: relative; height: 280px; 
                background: url('{GITHUB_IMG_BASE}hero_bg.jpg') center/cover no-repeat;
                display: flex; flex-direction: column; align-items: center; justify-content: center; color: #fff;
            }}
            .hero-banner::after {{
                content: ''; position: absolute; top: 0; left: 0; width: 100%; height: 100%;
                background: rgba(0,0,0,0.3);
            }
            .brand-logo {{ position: relative; z-index: 2; width: 100px; filter: drop-shadow(0 4px 10px rgba(0,0,0,0.3)); }}
            .hero-text {{ position: relative; z-index: 2; margin-top: 10px; text-align: center; }}
            .hero-text h2 {{ font-size: 22px; margin: 0; font-weight: 800; letter-spacing: 2px; text-shadow: 0 2px 4px rgba(0,0,0,0.5); }}
            .map-wrapper {{ padding: 15px; margin-top: -30px; position: relative; z-index: 10; }}
            #map {{ width: 100%; height: 300px; border-radius: 20px; box-shadow: 0 8px 20px rgba(0,0,0,0.15); border: 4px solid #fff; }}
            .card {{ display: block; text-decoration: none; color: inherit; margin: 20px; background: #fff; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.05); border: 1px solid #f0f0f0; }}
            .card img {{ width: 100%; height: 240px; object-fit: cover; }}
            .card-info {{ padding: 20px; }}
            .price-tag {{ color: var(--accent); font-size: 22px; font-weight: 900; }}
            .btn-view {{ margin-top: 15px; display: block; text-align: center; padding: 12px; background: #EDF2F7; color: var(--primary); border-radius: 10px; font-weight: 600; font-size: 14px; text-decoration: none; }}
            .action-bar {{ position: fixed; bottom: 0; left: 50%; transform: translateX(-50%); width: 100%; max-width: 500px; padding: 15px 20px 35px; display: flex; gap: 12px; background: rgba(255,255,255,0.9); backdrop-filter: blur(15px); border-top: 1px solid #f0f0f0; z-index: 999; }}
            .btn {{ flex: 1; text-align: center; padding: 16px; border-radius: 12px; text-decoration: none; font-weight: 700; color: #fff; font-size: 15px; }}
            .btn-call {{ background: #2D3748; }}
            .btn-line {{ background: #00B900; }}
            .back-btn {{ position: absolute; top: 20px; left: 20px; background: rgba(255,255,255,0.9); padding: 8px 16px; border-radius: 10px; text-decoration: none; font-size: 14px; z-index: 100; font-weight: bold; color: var(--primary); }}
        </style>
    </head>
    """

def build():
    out = Path(".")
    # 清理舊物件
    for p in out.glob("p*"):
        if p.is_dir() and re.match(r'^p\d+$', p.name): shutil.rmtree(p)

    res = requests.get(SHEET_CSV_URL)
    res.encoding = 'utf-8-sig'
    reader = csv.DictReader(res.text.splitlines())
    items, map_data = [], []

    for i, row in enumerate(reader):
        row = {str(k).strip().replace('\ufeff', ''): str(v).strip() for k, v in row.items() if k}
        if str(row.get("狀態", "")).upper() not in ["ON", "TRUE"] or not row.get("案名"): continue

        name, price, addr = row.get("案名",""), row.get("價格",""), row.get("地址","")
        img = str(row.get("圖片網址",""))
        if not img.startswith("http"): img = f"{GITHUB_IMG_BASE}{img.lstrip('/')}"
        
        slug = f"p{i}"
        (out/slug).mkdir(exist_ok=True)
        loc_text = addr if addr else f"台中市{name}"
        map_data.append({"name": name, "address": loc_text, "url": f"./{slug}/"})

        detail_html = f"""
        <div class="container">
            <a href="../" class="back-btn">✕ 關閉詳情</a>
            <img src="{img}" style="width:100%; height:380px; object-fit:cover; display:block;">
            <div style="padding:30px; margin-top:-30px; background:#fff; border-radius:30px 30px 0 0; position:relative;">
                <h1 style="font-size:26px; font-weight:800; color:var(--primary); margin:0;">{esc(name)}</h1>
                <div class="price-tag" style="margin:10px 0 25px;">{esc(price)}</div>
                <div style="line-height:1.8; color:#4A5568; font-size:16px; background:#F7FAFC; padding:20px; border-radius:15px;">
                    {esc(row.get("描述","")).replace('、', '<br>• ')}
                </div>
                <a href="http://maps.google.com/?q={urllib.parse.quote(loc_text)}" target="_blank" style="display:block; text-align:center; padding:16px; background:var(--primary); border-radius:12px; color:#fff; text-decoration:none; margin-top:25px; font-weight:700;">📍 前往現場導航</a>
                {COMPANY_INFO}
            </div>
            <div class="action-bar"><a href="tel:{MY_PHONE}" class="btn btn-call">致電聯繫</a><a href="{MY_LINE_URL}" class="btn btn-line">LINE 諮詢</a></div>
        </div>
        """
        (out/slug/"index.html").write_text(f"<!doctype html><html>{get_head(name, GA4_ID)}<body>{detail_html}</body></html>", encoding="utf-8")
        
        items.append(f'''
            <div class="card">
                <a href="./{slug}/"><img src="{img}"></a>
                <div class="card-info">
                    <b>{esc(name)}</b>
                    <div class="price-tag">{esc(price)}</div>
                    <a href="./{slug}/" class="btn-view">查看詳情空間</a>
                </div>
            </div>
        ''')

    home_html = f"""
    <div class="container">
        <div class="hero-banner">
            <img src="{GITHUB_IMG_BASE}logo.jpg" class="brand-logo">
            <div class="hero-text">
                <h2>{SITE_TITLE}</h2>
                <p style="margin:0; font-size:12px; opacity:0.8; letter-spacing:1px;">EVERCEDAR INTERNATIONAL REALTY</p>
            </div>
        </div>
        <div class="map-wrapper"><div id="map"></div></div>
        {''.join(items)}
        {COMPANY_INFO}
    </div>
    """
    (out/"index.html").write_text(f"<!doctype html><html>{get_head(SITE_TITLE, GA4_ID, True, map_data)}<body>{home_html}</body></html>", encoding="utf-8")

if __name__ == "__main__": build()
