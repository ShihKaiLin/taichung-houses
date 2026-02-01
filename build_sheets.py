import os, csv, requests, html, shutil, re, urllib.parse, json, time
from pathlib import Path
from datetime import datetime

# ============================================================
# 1. 個人品牌核心配置
# ============================================================
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQShAl0-TbUU0MQdYVe53im2T6lXQgh_7g-bdL6HHpIBFtA2yfIAMbPw4J9RgZUkROb9AAiMhnRC0kH/pub?output=csv"
MY_PHONE, MY_LINE_URL = "0938-615-351", "https://line.me/ti/p/FDsMyAYDv"
SITE_TITLE, GA4_ID = "SK-L 大台中房地產", "G-B7WP9BTP8X"
MAPS_API_KEY = os.getenv("MAPS_API_KEY", "AIzaSyDzgnI2Ucv622CRkWwo2GE5JRrs_Y4HQY0")
IMG_BASE = "https://raw.githubusercontent.com/ShihKaiLin/taichung-houses/main/images/"
GEOCACHE_PATH = Path("geocache.json")

# ============================================================
# 2. 品牌質感法律頁尾 (SEO 與品牌形象強化)
# ============================================================
LEGAL_FOOTER = """
<div class="legal-footer-container">
    <div class="legal-footer-content">
        <strong class="company-name">英柏國際地產有限公司</strong>
        <p class="license-info">
            中市地價二字第 1070029259 號<br>
            王一媖 經紀人 (103) 中市經紀字第 00678 號
        </p>
        <div class="copyright-line">
            <span>© 2026 SK-L Branding. All Rights Reserved.</span>
        </div>
        <p class="branding-slogan">專業誠信 · 卓越服務 · 深耕台中</p>
    </div>
</div>
<style>
    .legal-footer-container { margin: 100px 0 40px; padding: 60px 25px; text-align: center; border-top: 1px solid #edf2f7; background-color: #fafafa; border-radius: 50px 50px 0 0; }
    .company-name { color: #1A365D; font-size: 15px; display: block; margin-bottom: 12px; letter-spacing: 1px; font-weight: bold; }
    .license-info { font-size: 12px; color: #718096; line-height: 2; margin: 0; }
    .copyright-line { margin-top: 25px; font-size: 11px; color: #a0aec0; }
    .branding-slogan { margin-top: 10px; font-size: 11px; color: #cbd5e0; }
</style>
"""

def esc(s): return html.escape(str(s or "").strip())

def get_head(title, desc="", img="", is_home=False, map_data_json="[]"):
    seo_desc = esc(desc)[:80] if desc else f"{SITE_TITLE} - 精選台中優質房產，林世塏專業顧問服務。"
    seo_img = img if img.startswith("http") else f"{IMG_BASE}hero_bg.jpg"
    ga = f"""<script async src="https://www.googletagmanager.com/gtag/js?id={GA4_ID}"></script><script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','{GA4_ID}');</script>"""
    
    script = ""
    if is_home:
        script = f"""
        <script src="https://maps.googleapis.com/maps/api/js?key={MAPS_API_KEY}"></script>
        <script>
            let map, infoWindow;
            function initMap() {{
                const mapOptions = {{ 
                    center: {{ lat: 24.162, lng: 120.647 }}, 
                    zoom: 12, 
                    disableDefaultUI: true, 
                    zoomControl: true,
                    styles: [{{"featureType":"poi","stylers":[{{"visibility":"off"}}]}}]
                }};
                map = new google.maps.Map(document.getElementById("map"), mapOptions);
                infoWindow = new google.maps.InfoWindow();
                const locations = {map_data_json};
                locations.forEach(loc => {{
                    if (loc.lat && loc.lng) {{
                        const marker = new google.maps.Marker({{ 
                            position: {{lat: parseFloat(loc.lat), lng: parseFloat(loc.lng)}}, 
                            map: map, 
                            title: loc.name 
                        }});
                        marker.addListener("click", () => {{
                            const content = `
                                <div style="padding:10px;width:180px;font-family:sans-serif;">
                                    <h4 style="margin:0 0 5px;color:#1A365D;font-size:14px;">${{loc.name}}</h4>
                                    <div style="color:#C5A059;font-weight:900;margin-bottom:10px;font-size:16px;">${{loc.price}}</div>
                                    <a href="${{loc.url}}" style="display:block;text-align:center;background:#1A365D;color:#fff;text-decoration:none;padding:10px;border-radius:8px;font-size:12px;font-weight:bold;">查看分析建議</a>
                                </div>`;
                            infoWindow.setContent(content); infoWindow.open(map, marker);
                        }});
                    }}
                }});
            }}
            function filterAndSort() {{
                const reg = document.querySelector('.tag.f-reg.active').dataset.val;
                const type = document.querySelector('.tag.f-type.active').dataset.val;
                const sort = document.querySelector('.tag.f-sort.active').dataset.val;
                let cards = Array.from(document.querySelectorAll('.property-card'));
                cards.forEach(c => {{
                    const mR = (reg === 'all' || c.dataset.region === reg);
                    const mT = (type === 'all' || c.dataset.type === type);
                    c.style.display = (mR && mT) ? 'block' : 'none';
                }});
                if(sort !== 'none') {{
                    cards.sort((a,b) => {{
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
                btn.classList.add('active'); filterAndSort();
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
    <meta property="og:image" content="{seo_img}">
    <meta property="og:type" content="website">
    {ga}{script}
    <style>
        :root{{--sk-navy:#1A365D;--sk-gold:#C5A059;--sk-light:#F7FAFC;}}
        body{{font-family:'PingFang TC',sans-serif;margin:0;background:#fff;-webkit-font-smoothing:antialiased;}}
        .container{{max-width:500px;margin:auto;min-height:100vh;position:relative;box-shadow:0 0 40px rgba(0,0,0,0.05);}}
        .hero{{height:320px;background:url('{IMG_BASE}hero_bg.jpg') center/cover;display:flex;align-items:center;justify-content:center;color:#fff;position:relative;}}
        .hero::after{{content:'';position:absolute;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.3);}}
        .hero-content{{position:relative;z-index:2;text-align:center;}}.hero-content h2{{font-size:32px;margin:0;letter-spacing:5px;font-weight:900;}}
        .map-box{{margin:-40px 20px 0;position:relative;z-index:10;}}
        #map{{height:280px;border-radius:20px;box-shadow:0 15px 40px rgba(0,0,0,0.1);border:5px solid #fff;}}
        .filter-section{{padding:35px 20px 10px;}}
        .filter-group{{display:flex;gap:10px;overflow-x:auto;padding-bottom:15px;scrollbar-width:none;}}
        .tag{{padding:10px 18px;border-radius:50px;background:#f0f2f5;font-size:13px;color:#666;cursor:pointer;white-space:nowrap;border:none;font-weight:600;margin:0 5px 10px 0;transition:0.3s;}}
        .tag.active{{background:var(--sk-navy);color:#fff;}}
        .property-card{{margin:30px 20px;border-radius:24px;overflow:hidden;background:#fff;box-shadow:0 10px 30px rgba(0,0,0,0.05);border:1px solid #f0f0f0;}}
        .price{{font-size:24px;color:var(--sk-gold);font-weight:900;}}
        .action-bar{{position:fixed;bottom:0;left:50%;transform:translateX(-50%);width:100%;max-width:500px;padding:15px 25px 40px;display:flex;gap:12px;background:rgba(255,255,255,0.95);backdrop-filter:blur(10px);border-top:1px solid #f1f1f1;z-index:999;}}
        .btn{{flex:1;text-align:center;padding:18px;border-radius:18px;text-decoration:none;font-weight:800;color:#fff;font-size:15px;}}
        .btn-call{{background:#1A202C;}} .btn-line{{background:#00B900;}}
        .btn-ext{{display:block;text-align:center;padding:16px;background:#fff;color:var(--sk-navy);text-decoration:none;border-radius:14px;margin-top:15px;font-weight:700;border:1.5px solid #eee;}}
        .advice-box{{background:#f0f7ff;padding:20px;border-radius:15px;margin-bottom:20px;border-left:5px solid var(--sk-gold);font-size:14px;color:var(--sk-navy);}}
    </style></head>"""

def build():
    out = Path(".")
    for p in out.glob("p*"):
        if p.is_dir() and re.match(r'^p\d+$', p.name): shutil.rmtree(p)
    
    cache = {}
    if GEOCACHE_PATH.exists():
        try: cache = json.loads(GEOCACHE_PATH.read_text(encoding="utf-8"))
        except: pass

    res = requests.get(SHEET_CSV_URL); res.encoding = 'utf-8-sig'
    reader = csv.DictReader(res.text.splitlines())
    items, map_data, regions, types = [], [], set(), set()
    
    for i, row in enumerate(reader):
        d = {str(k).strip(): str(v).strip() for k, v in row.items() if k}
        name = d.get("案名") or next((v for k,v in d.items() if "案名" in k), "")
        if not name or d.get("狀態", "").upper() in ["OFF", "FALSE"]: continue
        
        ext_link = next((v for v in d.values() if str(v).startswith("http") and not any(x in str(v).lower() for x in ['.jpg','.png','.jpeg','.webp'])), "")
        reg, p_str, slug, addr = d.get("區域","台中"), d.get("價格","面議"), f"p{i}", d.get("地址", "")
        regions.add(reg); types.add(d.get("用途","住宅"))
        
        img = d.get("圖片網址") or next((v for k,v in d.items() if "圖片" in k), "")
        if img and not img.startswith("http"): img = f"{IMG_BASE}{img.lstrip('/')}"
        
        (out/slug).mkdir(exist_ok=True)
        search_addr = addr if addr else f"台中市{name}"
        lat, lng = cache.get(search_addr, {}).get("lat"), cache.get(search_addr, {}).get("lng")
        
        # ✅ 強制內頁連結邏輯，點擊卡片或地圖都進入子網頁
        internal_url = f"./{slug}/"
        map_data.append({"name":name, "price":p_str, "img":img, "url":internal_url, "lat":lat, "lng":lng})

        ext_btn = f'<a href="{ext_link}" target="_blank" class="btn-ext">🌐 查看原始網頁 (591/樂屋)</a>' if ext_link else ""
        detail = f"""<div class="container">
            <a href="../" style="position:absolute;top:25px;left:25px;background:#fff;padding:10px 20px;border-radius:14px;text-decoration:none;font-weight:800;color:var(--sk-navy);z-index:100;box-shadow:0 5px 15px rgba(0,0,0,0.1);">← 返回</a>
            <img src="{img}" style="width:100%;height:450px;object-fit:cover;display:block;">
            <div style="padding:40px 25px;background:#fff;border-radius:40px 40px 0 0;margin-top:-50px;position:relative;">
                <h1 style="font-size:28px;font-weight:800;color:var(--sk-navy);margin:0;">{esc(name)}</h1>
                <div class="price">{esc(p_str)}</div>
                <div style="line-height:2.1;color:#4a5568;margin:25px 0;font-size:16px;">{esc(d.get("描述","")).replace('、','<br>• ')}</div>
                <div class="advice-box">
                    <strong>💡 SK-L 顧問建議</strong><br>
                    此案地段具備極佳保值性。若您想了解該社區近期的實價登錄行情，或需要銀行鑑價參考，歡迎點擊下方 LINE 諮詢。
                </div>
                {ext_btn}
                <a href="https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(search_addr)}" target="_blank" style="display:block;text-align:center;padding:18px;background:var(--sk-navy);color:#fff;text-decoration:none;border-radius:15px;margin-top:15px;font-weight:700;">📍 前往地圖導航</a>
                {LEGAL_FOOTER}
            </div>
            <div class="action-bar"><a href="tel:{MY_PHONE}" class="btn btn-call">致電 SK-L</a><a href="{MY_LINE_URL}" class="btn btn-line">LINE 諮詢</a></div>
        </div>"""
        (out/slug/"index.html").write_text(f"<!doctype html><html lang='zh-TW'>{get_head(name + ' | ' + reg + '房產', d.get('描述',''), img)}<body>{detail}</body></html>", encoding="utf-8")
        
        # ✅ 修復：預先清理價格字元，解決 f-string 反斜線報錯問題
        pure_price = "".join(filter(str.isdigit, p_str)) or "0"
        items.append(f'''<div class="property-card" data-region="{esc(reg)}" data-type="{esc(d.get("用途","住宅"))}" data-price="{pure_price}"><a href="{internal_url}"><img src="{img}" style="width:100%;height:280px;object-fit:cover;display:block;"></a><div class="card-info" style="padding:25px;"><h4>{esc(name)}</h4><div class="price">{esc(p_str)}</div><div style="font-size:12px;color:#999;">{esc(reg)} • {esc(d.get("用途","住宅"))}</div><a href="{internal_url}" style="display:block;text-align:center;margin-top:15px;padding:14px;background:#f8fafc;color:var(--sk-navy);text-decoration:none;font-size:13px;font-weight:700;border-radius:12px;">查看 SK-L 專業建議</a></div></div>''')

    reg_btns = "".join([f"<button class='tag f-reg' data-val='{esc(r)}' onclick='setTag(this, \"f-reg\")'>{esc(r)}</button>" for r in sorted(regions)])
    type_btns = "".join([f"<button class='tag f-type' data-val='{esc(t)}' onclick='setTag(this, \"f-type\")'>{esc(t)}</button>" for t in sorted(types)])
    
    home_html = f"""<div class="container"><div class="hero"><div class="hero-content"><h2>{esc(SITE_TITLE)}</h2><p>Curated Real Estate • Taichung</p></div></div><div class="map-box"><div id="map"></div></div><div class="filter-section"><div class="filter-group"><button class="tag f-reg active" data-val="all" onclick="setTag(this, 'f-reg')">全部地區</button>{reg_btns}</div><div class="filter-group" style="margin-top:10px;"><button class="tag f-type active" data-val="all" onclick="setTag(this, 'f-type')">所有用途</button>{type_btns}</div><div class="filter-group" style="margin-top:10px; border-top:1px solid #f0f0f0; padding-top:15px;"><button class="tag f-sort active" data-val="none" onclick="setTag(this, 'f-sort')">預設排序</button><button class="tag f-sort" data-val="high" onclick="setTag(this, 'f-sort')">價格：高至低</button><button class="tag f-sort" data-val="low" onclick="setTag(this, 'f-sort')">價格：低至高</button></div></div><div id="list">{''.join(items)}</div>{LEGAL_FOOTER}<div class="action-bar"><a href="tel:{MY_PHONE}" class="btn btn-call">致電 SK-L</a><a href="{MY_LINE_URL}" class="btn btn-line">LINE 諮詢</a></div></div>"""
    (out/"index.html").write_text(f"<!doctype html><html lang='zh-TW'>{get_head(SITE_TITLE, is_home=True, map_data_json=json.dumps(map_data, ensure_ascii=False))}<body>{home_html}</body></html>", encoding="utf-8")

if __name__ == "__main__": build()

