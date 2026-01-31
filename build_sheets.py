import os, csv, requests, html, shutil, re, urllib.parse
from pathlib import Path

# --- 1. 核心配置 (每次執行都會抓取此網址的最新資料) ---
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQShAl0-TbUU0MQdYVe53im2T6lXQgh_7g-bdL6HHpIBFtA2yfIAMbPw4J9RgZUkROb9AAiMhnRC0kH/pub?output=csv"
MY_PHONE = "0938-615-351"
MY_LINE_URL = "https://line.me/ti/p/FDsMyAYDv"
SITE_TITLE = "林世塏｜台中地圖找房"
GA4_ID = "G-B7WP9BTP8X"
MAPS_API_KEY = "AIzaSyDzgnI2Ucv622CRkWwo2GE5JRrs_Y4HQY0"

# --- 2. 品牌合規資訊 (10px 極致低調小字) ---
COMPANY_INFO = """
<div style="margin-top:20px; padding:15px; border-top:1px solid #f9f9f9; font-size:10px; color:#ddd; line-height:1.4; text-align:center; letter-spacing:0.5px;">
    英柏國際地產有限公司 | 中市地價二字第 1070029259 號<br>
    王一媖 經紀人 (103) 中市經紀字第 00678 號
</div>
"""

def esc(s): return html.escape(str(s or "").strip())

def get_head(title, ga_id, is_home=False, map_data=None):
    ga = f"""<script async src="https://www.googletagmanager.com/gtag/js?id={ga_id}"></script><script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','{ga_id}');</script>""" if ga_id else ""
    
    map_script = ""
    if is_home and map_data:
        map_script = f"""
        <script src="https://maps.googleapis.com/maps/api/js?key={MAPS_API_KEY}&libraries=places"></script>
        <script>
            function initMap() {{
                const mapEl = document.getElementById("map");
                const domain = window.location.hostname;
                
                // 【自保鎖 1】網域保護
                if (!domain.includes("shihkailin.github.io") && !domain.includes("localhost") && !domain.includes("127.0.0.1")) {{
                    mapEl.innerHTML = "<div style='padding:50px 20px; color:#999; text-align:center;'>地圖僅授權特定網域使用</div>";
                    return;
                }}

                // 【自保鎖 2】訪客流量限制 (防止單一訪客刷爆 API)
                let vCount = sessionStorage.getItem("m_c") || 0;
                if (parseInt(vCount) > 15) {{
                    mapEl.innerHTML = "<div style='padding:50px 20px; color:#999; text-align:center;'>今日瀏覽額度已滿，請看下方列表</div>";
                    return;
                }}
                sessionStorage.setItem("m_c", parseInt(vCount) + 1);

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
            :root {{ --alley-blue: #2A58AD; --alley-gray: #f2f4f7; --alley-dark: #333; }}
            body {{ font-family: 'PingFang TC', sans-serif; background: #fff; margin: 0; color: var(--alley-dark); }}
            .container {{ max-width: 480px; margin: auto; min-height: 100vh; padding-bottom: 120px; background: #fff; position: relative; box-shadow: 0 0 20px rgba(0,0,0,0.05); }}
            #map {{ width: 100%; height: 350px; background: #f5f5f5; border-bottom: 1px solid #eee; }}
            .header {{ padding: 25px 20px 10px; }}
            .header h1 {{ font-size: 20px; color: var(--alley-blue); font-weight: 900; margin: 0; }}
            .card {{ display: block; text-decoration: none; color: inherit; margin: 15px 20px; border-radius: 12px; overflow: hidden; border: 1px solid #eee; }}
            .card img {{ width: 100%; height: 220px; object-fit: cover; display: block; }}
            .card-info {{ padding: 15px; }}
            .card-info b {{ font-size: 18px; display: block; margin-bottom: 5px; }}
            .price {{ color: #e53e3e; font-size: 22px; font-weight: 800; }}
            .action-bar {{ position: fixed; bottom: 0; left: 50%; transform: translateX(-50%); width: 100%; max-width: 480px; padding: 10px 15px 30px; display: flex; gap: 8px; background: rgba(255,255,255,0.95); backdrop-filter: blur(10px); border-top: 1px solid #eee; z-index: 200; }}
            .btn {{ flex: 1; text-align: center; padding: 14px; border-radius: 8px; text-decoration: none; font-weight: bold; color: #fff; font-size: 14px; }}
            .btn-call {{ background: var(--alley-dark); }}
            .btn-line {{ background: #00B900; }}
            .back-btn {{ position: absolute; top: 15px; left: 15px; background: #fff; padding: 5px 12px; border-radius: 5px; text-decoration: none; font-size: 13px; z-index: 10; border: 1px solid #ddd; color: #333; }}
        </style>
    </head>
    """

def build():
    out = Path(".")
    # 清理舊物件頁面
    for p in out.glob("p*"):
        if p.is_dir() and re.match(r'^p\d+$', p.name): shutil.rmtree(p)

    print("📡 正在同步 Google 試算表最新物件...")
    try:
        res = requests.get(SHEET_CSV_URL)
        res.encoding = 'utf-8-sig'
        reader = csv.DictReader(res.text.splitlines())
    except Exception as e:
        print(f"❌ 同步失敗: {e}")
        return

    items, map_data = [], []

    for i, row in enumerate(reader):
        row = {str(k).strip().replace('\ufeff', ''): str(v).strip() for k, v in row.items() if k}
        # 自動識別勾選框 (TRUE/ON 都算勾選)
        status = str(row.get("狀態", "")).upper()
        if status not in ["ON", "TRUE"] or not row.get("案名"): continue

        name, price, addr = row.get("案名",""), row.get("價格",""), row.get("地址","")
        img = str(row.get("圖片網址",""))
        if not img.startswith("http"):
            img = f"https://raw.githubusercontent.com/ShihKaiLin/taichung-houses/main/images/{img.lstrip('/')}"
        
        slug = f"p{i}"
        (out/slug).mkdir(exist_ok=True)
        
        # 定位文字：地址優先，沒地址用案名
        loc_text = addr if addr else f"台中市{name}"
        map_data.append({"name": name, "address": loc_text, "url": f"./{slug}/"})

        detail_html = f"""
        <div class="container">
            <a href="../" class="back-btn">← 返回列表</a>
            <img src="{img}" style="width:100%; height:320px; object-fit:cover;">
            <div style="padding:25px;">
                <h1 style="font-size:24px; font-weight:900;">{esc(name)}</h1>
                <div class="price">{esc(price)}</div>
                <div style="margin-top:20px; background:var(--alley-gray); padding:20px; border-radius:12px; font-size:15px; color:#444; line-height:1.7;">
                    {esc(row.get("描述","")).replace('、', '<br>• ')}
                </div>
                <a href="http://maps.google.com/?q={urllib.parse.quote(loc_text)}" target="_blank" style="display:block; text-align:center; padding:12px; background:var(--alley-blue); border-radius:8px; color:#fff; text-decoration:none; margin-top:15px; font-weight:bold;">📍 開啟導航</a>
                {COMPANY_INFO}
            </div>
            <div class="action-bar"><a href="tel:{MY_PHONE}" class="btn btn-call">致電聯繫</a><a href="{MY_LINE_URL}" class="btn btn-line">LINE 諮詢</a></div>
        </div>
        """
        (out/slug/"index.html").write_text(f"<!doctype html><html>{get_head(name, GA4_ID)}<body>{detail_html}</body></html>", encoding="utf-8")
        items.append(f'<a href="./{slug}/" class="card"><div><img src="{img}"></div><div class="card-info"><b>{esc(name)}</b><div class="price">{esc(price)}</div></div></a>')

    # 生成首頁
    home_html = f"""
    <div class="container">
        <div id="map"></div>
        <div class="header"><h1>{SITE_TITLE}</h1></div>
        {''.join(items)}
        {COMPANY_INFO}
    </div>
    """
    (out/"index.html").write_text(f"<!doctype html><html>{get_head(SITE_TITLE, GA4_ID, True, map_data)}<body>{home_html}</body></html>", encoding="utf-8")
    print(f"✅ 同步完成！共生成 {len(items)} 個物件。")

if __name__ == "__main__": build()
