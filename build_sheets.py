import os, csv, requests, html, shutil, re, urllib.parse
from pathlib import Path

# --- 1. 個人品牌配置 ---
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQShAl0-TbUU0MQdYVe53im2T6lXQgh_7g-bdL6HHpIBFtA2yfIAMbPw4J9RgZUkROb9AAiMhnRC0kH/pub?output=csv"
MY_PHONE = "0938-615-351"
MY_LINE_URL = "https://line.me/ti/p/FDsMyAYDv"
SITE_TITLE = "SK-L 大台中房地產"
GA4_ID = "G-B7WP9BTP8X"
MAPS_API_KEY = "AIzaSyDzgnI2Ucv622CRkWwo2GE5JRrs_Y4HQY0"
GITHUB_IMG_BASE = "https://raw.githubusercontent.com/ShihKaiLin/taichung-houses/main/images/"

# --- 2. 質感合規資訊 (法律要求必備) ---
LEGAL_FOOTER = """
<div style="margin: 100px 0 40px; padding: 20px; text-align: center; border-top: 1px solid #f9f9f9;">
    <div style="font-size: 10px; color: #ddd; line-height: 1.6; letter-spacing: 0.5px;">
        英柏國際地產有限公司 | 中市地價二字第 1070029259 號<br>
        王一媖 經紀人 (103) 中市經紀字第 00678 號<br>
        <span style="opacity: 0.5;">© 2026 SK-L Branding</span>
    </div>
</div>
"""

def esc(s): return html.escape(str(s or "").strip())

def get_head(title, ga_id, is_home=False, map_data=None):
    ga = f"""<script async src="https://www.googletagmanager.com/gtag/js?id={ga_id}"></script><script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','{ga_id}');</script>""" if ga_id else ""
    script = ""
    if is_home:
        script = f"""
        <script src="https://maps.googleapis.com/maps/api/js?key={MAPS_API_KEY}"></script>
        <script>
            function filterAndSort() {{
                const reg = document.querySelector('.tag.f-reg.active').dataset.val;
                const type = document.querySelector('.tag.f-type.active').dataset.val;
                const sort = document.querySelector('.tag.f-sort.active').dataset.val;
                let cards = Array.from(document.querySelectorAll('.property-card'));
                cards.forEach(card => {{
                    const mReg = (reg === 'all' || card.dataset.region === reg);
                    const mType = (type === 'all' || card.dataset.type === type);
                    card.style.display = (mReg && mType) ? 'block' : 'none';
                }});
                if(sort !== 'none') {{
                    cards.sort((a, b) => {{
                        const pA = parseFloat(a.dataset.price) || 0;
                        const pB = parseFloat(b.dataset.price) || 0;
                        return sort === 'high' ? pB - pA : pA - pB;
                    }});
                    const list = document.getElementById('list');
                    cards.forEach(c => list.appendChild(c));
                }}
            }}
            function setTag(btn, cls) {{
                btn.parentElement.querySelectorAll('.'+cls).forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                filterAndSort();
            }}
            function initMap() {{
                const map = new google.maps.Map(document.getElementById("map"), {{
                    center: {{ lat: 24.162, lng: 120.647 }}, zoom: 12, 
                    disableDefaultUI: true, zoomControl: true,
                    styles: [{{ "featureType": "poi", "stylers": [{{ "visibility": "off" }}] }}]
                }});
                const geocoder = new google.maps.Geocoder();
                const locations = {map_data};
                locations.forEach(loc => {{
                    geocoder.geocode({{ 'address': loc.address }}, (results, status) => {{
                        if (status === 'OK') {{
                            const marker = new google.maps.Marker({{ position: results[0].geometry.location, map: map, title: loc.name }});
                            marker.addListener("click", () => {{ 
                                if(loc.url.startsWith('http')) window.open(loc.url, '_blank');
                                else window.location.href = loc.url;
                            }});
                        }}
                    }});
                }});
            }}
            window.onload = initMap;
        </script>
        """
    return f"""<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=0"><title>{esc(title)}</title>{ga}{script}<style>:root {{ --sk-navy: #1A365D; --sk-gold: #C5A059; --sk-bg: #FFFFFF; }}body {{ font-family: 'PingFang TC', sans-serif; background: #fff; margin: 0; -webkit-font-smoothing: antialiased; }}.container {{ max-width: 500px; margin: auto; background: #fff; min-height: 100vh; position: relative; box-shadow: 0 0 40px rgba(0,0,0,0.05); }}.hero {{ position: relative; height: 320px; background: url('{GITHUB_IMG_BASE}hero_bg.jpg') center/cover; display: flex; align-items: center; justify-content: center; color: #fff; }}.hero::after {{ content:''; position:absolute; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.3); }}.hero-content {{ position: relative; z-index: 2; text-align: center; }}.hero-content h2 {{ font-size: 32px; margin: 0; letter-spacing: 5px; font-weight: 900; }}.map-box {{ margin: -40px 20px 0; position: relative; z-index: 10; }}#map {{ height: 280px; border-radius: 20px; box-shadow: 0 15px 40px rgba(0,0,0,0.1); border: 5px solid #fff; }}.filter-section {{ padding: 35px 20px 10px; }}.filter-group {{ display: flex; gap: 10px; overflow-x: auto; padding-bottom: 15px; scrollbar-width: none; }}.filter-group::-webkit-scrollbar {{ display: none; }}.tag {{ padding: 8px 18px; border-radius: 50px; background: #f0f2f5; font-size: 13px; color: #666; cursor: pointer; white-space: nowrap; border:none; font-weight: 600; }}.tag.active {{ background: var(--sk-navy); color: #fff; }}.property-card {{ margin: 30px 20px; border-radius: 24px; overflow: hidden; background: #fff; box-shadow: 0 10px 30px rgba(0,0,0,0.05); }}.property-card img {{ width: 100%; height: 280px; object-fit: cover; display: block; }}.card-info {{ padding: 25px; }}.price {{ font-size: 22px; color: var(--sk-gold); font-weight: 900; }}.action-bar {{ position: fixed; bottom: 0; left: 50%; transform: translateX(-50%); width: 100%; max-width: 500px; padding: 15px 25px 40px; display: flex; gap: 12px; background: rgba(255,255,255,0.85); backdrop-filter: blur(15px); border-top: 1px solid #f1f1f1; z-index: 999; }}.btn {{ flex: 1; text-align: center; padding: 18px; border-radius: 18px; text-decoration: none; font-weight: 800; color: #fff; font-size: 15px; }}.btn-call {{ background: #1A202C; }} .btn-line {{ background: #00B900; }}.back-btn {{ position: absolute; top: 25px; left: 25px; background: #fff; padding: 10px 20px; border-radius: 14px; text-decoration: none; font-weight: 800; color: var(--sk-navy); z-index: 100; box-shadow: 0 5px 15px rgba(0,0,0,0.1); }}.btn-ext-main {{ display: block; text-align: center; padding: 16px; background: var(--sk-navy); color: #fff; text-decoration: none; border-radius: 14px; margin-top: 15px; font-weight: 700; font-size: 15px; letter-spacing: 1px; }}</style></head>"""

def build():
    out = Path(".")
    for p in out.glob("p*"):
        if p.is_dir() and re.match(r'^p\d+$', p.name): shutil.rmtree(p)

    res = requests.get(SHEET_CSV_URL); res.encoding = 'utf-8-sig'
    reader = csv.DictReader(res.text.splitlines())
    items, map_data, regions, types = [], [], set(), set()

    for i, row in enumerate(reader):
        row = {str(k).strip().replace('\ufeff', ''): str(v).strip() for k, v in row.items() if k}
        if str(row.get("狀態", "")).upper() not in ["ON", "TRUE"] or not row.get("案名"): continue

        name, price_str = row.get("案名",""), row.get("價格","")
        # 精確抓取試算表中的「外部連結網址」
        ext_link = row.get("外部連結網址", "").strip()
        
        price_val = re.sub(r'[^\d.]', '', price_str)
        reg, type_val, addr = row.get("區域", "台中市"), row.get("用途", "住宅"), row.get("地址", "")
        regions.add(reg); types.add(type_val)
        
        img = str(row.get("圖片網址",""))
        if not img.startswith("http"): img = f"{GITHUB_IMG_BASE}{img.lstrip('/')}"
        
        slug = f"p{i}"
        (out/slug).mkdir(exist_ok=True)
        loc_text = addr if addr else f"台中市{name}"
        
        # 核心邏輯：首頁跳轉網址
        main_dest = ext_link if ext_link.startswith("http") else f"./{slug}/"
        map_data.append({"name": name, "address": loc_text, "url": main_dest})

        # 子網頁生成：補足外部連結按鈕
        ext_btn = f'<a href="{ext_link}" target="_blank" class="btn-ext-main">🌐 查看原始物件連結 (591/樂屋)</a>' if ext_link.startswith("http") else ""

        detail_html = f"""
        <div class="container">
            <a href="../" class="back-btn">← 返回</a>
            <img src="{img}" style="width:100%; height:450px; object-fit:cover; display:block;">
            <div style="padding:40px 25px; margin-top:-50px; background:#fff; border-radius:40px 40px 0 0; position:relative;">
                <h1 style="font-size:28px; font-weight:800; color:var(--sk-navy); margin:0;">{esc(name)}</h1>
                <div class="price">{esc(price_str)}</div>
                <div style="line-height:2.1; color:#4a5568; margin-top:25px; font-size:16px;">{esc(row.get("描述","")).replace('、','<br>• ')}</div>
                {ext_btn}
                <a href="https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(loc_text)}" target="_blank" style="display:block; text-align:center; padding:18px; border:1.5px solid var(--sk-navy); color:var(--sk-navy); text-decoration:none; border-radius:15px; margin-top:15px; font-weight:700;">📍 前往地圖導航</a>
                {LEGAL_FOOTER}
            </div>
            <div class="action-bar"><a href="tel:{MY_PHONE}" class="btn btn-call">致電 SK-L</a><a href="{MY_LINE_URL}" class="btn btn-line">LINE 諮詢</a></div>
        </div>
        """
        (out/slug/"index.html").write_text(f"<!doctype html><html lang='zh-TW'>{get_head(name, GA4_ID)}<body>{detail_html}</body></html>", encoding="utf-8")
        
        is_ext = ext_link.startswith("http")
        target = 'target="_blank"' if is_ext else ""
        items.append(f'''
            <div class="property-card" data-region="{esc(reg)}" data-type="{esc(type_val)}" data-price="{price_val}">
                <a href="{main_dest}" {target}><img src="{img}"></a>
                <div class="card-info">
                    <h4>{esc(name)}</h4>
                    <div class="price">{esc(price_str)}</div>
                    <div style="font-size:12px; color:#999;">{esc(reg)} • {esc(type_val)}</div>
                    <a href="{main_dest}" {target} style="display:block; text-align:center; margin-top:15px; padding:14px; background:#f8fafc; color:var(--sk-navy); text-decoration:none; font-size:13px; font-weight:700; border-radius:12px;">{'查看詳細資訊' if not is_ext else '開啟原始網頁'}</a>
                </div>
            </div>
        ''')

    reg_btns = ''.join([f'<button class="tag f-reg" data-val="{esc(r)}" onclick="setTag(this, \'f-reg\')">{esc(r)}</button>' for r in sorted(regions)])
    type_btns = ''.join([f'<button class="tag f-type" data-val="{esc(t)}" onclick="setTag(this, \'f-type\')">{esc(t)}</button>' for t in sorted(types)])

    home_html = f"""<div class="container"><div class="hero"><div class="hero-content"><h2>{SITE_TITLE}</h2><p>Curated Real Estate • Taichung</p></div></div><div class="map-box"><div id="map"></div></div><div class="filter-section"><div class="filter-group"><button class="tag f-reg active" data-val="all" onclick="setTag(this, 'f-reg')">全部地區</button>{reg_btns}</div><div class="filter-group" style="margin-top:10px;"><button class="tag f-type active" data-val="all" onclick="setTag(this, 'f-type')">所有用途</button>{type_btns}</div><div class="filter-group" style="margin-top:10px; border-top:1px solid #f0f0f0; padding-top:15px;"><button class="tag f-sort active" data-val="none" onclick="setTag(this, 'f-sort')">預設排序</button><button class="tag f-sort" data-val="high" onclick="setTag(this, 'f-sort')">價格：高至低</button><button class="tag f-sort" data-val="low" onclick="setTag(this, 'f-sort')">價格：低至高</button></div></div><div id="list">{''.join(items)}</div>{LEGAL_FOOTER}<div class="action-bar"><a href="tel:{MY_PHONE}" class="btn btn-call">致電 SK-L</a><a href="{MY_LINE_URL}" class="btn btn-line">LINE 諮詢</a></div></div>"""
    (out/"index.html").write_text(f"<!doctype html><html lang='zh-TW'>{get_head(SITE_TITLE, GA4_ID, True, map_data)}<body>{home_html}</body></html>", encoding="utf-8")

if __name__ == "__main__": build()
