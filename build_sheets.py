import os, csv, requests, html, shutil, re, urllib.parse, json, time
from pathlib import Path

# ============================================================
# 1) Core Configuration
# ============================================================
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQShAl0-TbUU0MQdYVe53im2T6lXQgh_7g-bdL6HHpIBFtA2yfIAMbPw4J9RgZUkROb9AAiMhnRC0kH/pub?output=csv"
MY_PHONE, MY_LINE_URL = "0938-615-351", "https://line.me/ti/p/FDsMyAYDv"
SITE_TITLE, GA4_ID = "SK-L 大台中房地產", "G-B7WP9BTP8X"
IMG_BASE = "https://raw.githubusercontent.com/ShihKaiLin/taichung-houses/main/images/"

# ✅ 請用環境變數 / GitHub Secrets：MAPS_API_KEY
MAPS_API_KEY = os.getenv("MAPS_API_KEY", "").strip()

GEOCACHE_PATH = Path("geocache.json")
GEOCODE_SLEEP_SEC = 0.25
GEOCODE_TIMEOUT = 20
GEOCODE_RETRY = 2
GEOCODE_REGION = "tw"
GEOCODE_LANGUAGE = "zh-TW"

# ============================================================
# 2) Footer
# ============================================================
LEGAL_FOOTER = """
<div class="sk-legal-footer">
  <div class="sk-footer-inner">
    <div class="sk-brand-info">
      <strong class="sk-corp-name">英柏國際地產有限公司</strong>
      <p class="sk-license">中市地價二字第 1070029259 號<br>王一媖 經紀人 (103) 中市經紀字第 00678 號</p>
    </div>
    <div class="sk-copyright">
      <span>© 2026 SK-L Branding. All Rights Reserved.</span>
      <p class="sk-slogan">專業 · 誠信 · 卓越服務 · 深耕台中房地產</p>
    </div>
  </div>
</div>
<style>
  .sk-legal-footer { margin: 120px 0 0; padding: 80px 25px; text-align: center; border-top: 1px solid #edf2f7; background: linear-gradient(to bottom, #ffffff, #f8fafc); border-radius: 60px 60px 0 0; }
  .sk-corp-name { color: #1A365D; font-size: 16px; display: block; margin-bottom: 12px; letter-spacing: 2px; font-weight: 800; }
  .sk-license { font-size: 12px; color: #718096; line-height: 2; margin-bottom: 30px; }
  .sk-copyright { font-size: 11px; color: #a0aec0; border-top: 1px solid #f1f5f9; padding-top: 30px; }
  .sk-slogan { margin-top: 10px; color: #cbd5e0; letter-spacing: 1px; }
</style>
"""

def esc(s):
    return html.escape(str(s or "").strip())

def norm_addr(s: str) -> str:
    s = str(s or "").strip()
    s = s.replace("臺中市", "台中市")
    s = re.sub(r"\s+", " ", s)
    return s

def load_cache():
    if GEOCACHE_PATH.exists():
        try:
            return json.loads(GEOCACHE_PATH.read_text(encoding="utf-8"))
        except:
            return {}
    return {}

def save_cache(cache: dict):
    GEOCACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")

def geocode_address(addr: str, cache: dict):
    addr = norm_addr(addr)
    if not addr:
        return None, None, "EMPTY"

    if addr in cache and isinstance(cache[addr], dict):
        lat = cache[addr].get("lat")
        lng = cache[addr].get("lng")
        if lat is not None and lng is not None:
            return lat, lng, "CACHE"

    if not MAPS_API_KEY:
        cache[addr] = {"lat": None, "lng": None, "status": "NO_API_KEY"}
        return None, None, "NO_API_KEY"

    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": addr,
        "key": MAPS_API_KEY,
        "region": GEOCODE_REGION,
        "language": GEOCODE_LANGUAGE,
    }

    last_status = "ERROR"
    for attempt in range(GEOCODE_RETRY + 1):
        try:
            r = requests.get(url, params=params, timeout=GEOCODE_TIMEOUT)
            data = r.json()
            status = data.get("status") or "ERROR"
            last_status = status

            if status == "OK" and data.get("results"):
                loc = data["results"][0]["geometry"]["location"]
                lat = float(loc["lat"])
                lng = float(loc["lng"])
                cache[addr] = {"lat": lat, "lng": lng, "status": "OK"}
                return lat, lng, "OK"

            if status in ("OVER_QUERY_LIMIT", "UNKNOWN_ERROR"):
                time.sleep(max(GEOCODE_SLEEP_SEC, 0.6) * (attempt + 1))
                continue

            cache[addr] = {"lat": None, "lng": None, "status": status}
            return None, None, status

        except Exception:
            time.sleep(max(GEOCODE_SLEEP_SEC, 0.6) * (attempt + 1))
            continue

    cache[addr] = {"lat": None, "lng": None, "status": last_status}
    return None, None, last_status

# ============================================================
# 3) Head / SEO / Scripts
# ============================================================
def get_head(title, desc="", img="", is_home=False, map_data_json="[]"):
    seo_desc = esc(desc)[:80] if desc else f"{SITE_TITLE} - 精選台中優質房產，林世塏為您提供專業置產服務。"
    seo_img = img if str(img).startswith("http") else f"{IMG_BASE}hero_bg.jpg"
    ga = (f"<script async src=\"https://www.googletagmanager.com/gtag/js?id={GA4_ID}\"></script>"
          f"<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}"
          f"gtag('js',new Date());gtag('config','{GA4_ID}');</script>") if GA4_ID else ""

    json_ld = (f"<script type=\"application/ld+json\">"
               f"{{\"@context\":\"https://schema.org\",\"@type\":\"RealEstateAgent\","
               f"\"name\":\"{esc(SITE_TITLE)}\",\"telephone\":\"{esc(MY_PHONE)}\","
               f"\"url\":\"https://shihkailin.github.io/taichung-houses/\"}}</script>")

    map_script = ""
    if is_home and MAPS_API_KEY:
        map_script = f"""
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
      if(loc.lat == null || loc.lng == null) return;

      const marker = new google.maps.Marker({{
        position: {{ lat: loc.lat, lng: loc.lng }},
        map: map,
        title: loc.name,
        animation: google.maps.Animation.DROP
      }});

      marker.addListener("click", () => {{
        const content = `
          <div style="padding:10px;width:220px;font-family:sans-serif;">
            <div style="background:url('${{loc.img}}') center/cover;height:110px;border-radius:10px;margin-bottom:10px;"></div>
            <h4 style="margin:0;color:#1A365D;font-size:14px;line-height:1.4;">${{loc.name}}</h4>
            <div style="color:#C5A059;font-weight:900;font-size:16px;margin:6px 0 10px;">${{loc.price}}</div>
            <a href="${{loc.url}}" style="display:block;text-align:center;background:#1A365D;color:#fff;text-decoration:none;padding:10px;border-radius:10px;font-size:12px;font-weight:bold;">查看詳情</a>
          </div>`;
        infoWindow.setContent(content);
        infoWindow.open(map, marker);
      }});
    }});
  }}

  function filterAndSort() {{
    const reg  = document.querySelector('.tag.f-reg.active').dataset.val;
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
    btn.classList.add('active');
    filterAndSort();
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
{ga}{json_ld}{map_script}
<style>
:root{{--sk-navy:#1A365D;--sk-gold:#C5A059;--sk-light:#F8FAFC;--sk-shadow:0 15px 45px rgba(0,0,0,0.08);}}
body{{font-family:'PingFang TC','Microsoft JhengHei',sans-serif;margin:0;background:#fff;-webkit-font-smoothing:antialiased;}}
.container{{max-width:500px;margin:auto;background:#fff;min-height:100vh;position:relative;box-shadow:0 0 60px rgba(0,0,0,0.05);}}
.hero{{height:340px;background:url('{IMG_BASE}hero_bg.jpg') center/cover;display:flex;align-items:center;justify-content:center;color:#fff;position:relative;}}
.hero::after{{content:'';position:absolute;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.35);}}
.hero-content{{position:relative;z-index:2;text-align:center;}}
.hero-content h2{{font-size:34px;margin:0;letter-spacing:6px;font-weight:900;text-shadow:0 2px 10px rgba(0,0,0,0.3);}}
.map-box{{margin:-50px 20px 0;position:relative;z-index:10;}}
#map{{height:300px;border-radius:24px;box-shadow:var(--sk-shadow);border:6px solid #fff;}}
.filter-section{{padding:40px 20px 10px;}}
.filter-group{{display:flex;gap:10px;overflow-x:auto;padding-bottom:15px;scrollbar-width:none;}}
.tag{{padding:12px 22px;border-radius:50px;background:var(--sk-light);font-size:13px;color:#4A5568;cursor:pointer;white-space:nowrap;border:1px solid #edf2f7;font-weight:600;transition:0.3s;}}
.tag.active{{background:var(--sk-navy);color:#fff;border-color:var(--sk-navy);box-shadow:0 5px 15px rgba(26,54,93,0.2);}}
.property-card{{margin:35px 20px;border-radius:28px;overflow:hidden;background:#fff;box-shadow:var(--sk-shadow);border:1px solid #f1f5f9;}}
.price{{font-size:26px;color:var(--sk-gold);font-weight:900;letter-spacing:-0.5px;}}
.action-bar{{position:fixed;bottom:0;left:50%;transform:translateX(-50%);width:100%;max-width:500px;padding:20px 25px 45px;display:flex;gap:15px;background:rgba(255,255,255,0.96);backdrop-filter:blur(20px);border-top:1px solid #f1f1f1;z-index:999;}}
.btn{{flex:1;text-align:center;padding:20px;border-radius:20px;text-decoration:none;font-weight:800;color:#fff;font-size:16px;box-shadow:0 4px 12px rgba(0,0,0,0.1);}}
.btn-call{{background:#1A202C;}}
.btn-line{{background:#00B900;}}
.btn-ext{{display:block;text-align:center;padding:18px;background:#fff;color:var(--sk-navy);text-decoration:none;border-radius:16px;margin-top:15px;font-weight:800;border:2px solid #edf2f7;}}
.advice-box{{background:linear-gradient(135deg,#f0f7ff 0%,#e6f0ff 100%);padding:25px;border-radius:22px;margin:30px 0;border-left:6px solid var(--sk-gold);font-size:15px;color:var(--sk-navy);line-height:1.8;}}
.back-link{{position:absolute;top:30px;left:25px;background:rgba(255,255,255,0.9);padding:12px 22px;border-radius:15px;text-decoration:none;font-weight:800;color:var(--sk-navy);z-index:100;backdrop-filter:blur(10px);box-shadow:0 5px 15px rgba(0,0,0,0.1);}}
</style>
</head>"""

# ============================================================
# 4) Build
# ============================================================
def build():
    out = Path(".")
    for p in out.glob("p*"):
        if p.is_dir() and re.match(r"^p\d+$", p.name):
            shutil.rmtree(p)

    cache = load_cache()

    res = requests.get(SHEET_CSV_URL)
    res.encoding = "utf-8-sig"
    reader = csv.DictReader(res.text.splitlines())

    items, map_data, regions, types = [], [], set(), set()

    for i, row in enumerate(reader):
        d = {str(k).strip(): str(v).strip() for k, v in row.items() if k}

        name = d.get("案名") or next((v for k, v in d.items() if "案名" in k), "")
        if not name or d.get("狀態", "").upper() in ["OFF", "FALSE"]:
            continue

        reg = d.get("區域", "台中")
        use_type = d.get("用途", "住宅")
        p_str = d.get("價格", "面議")
        addr = d.get("地址", "")

        regions.add(reg)
        types.add(use_type)

        img = d.get("圖片網址") or next((v for k, v in d.items() if "圖片" in k), "")
        if img and not img.startswith("http"):
            img = f"{IMG_BASE}{img.lstrip('/')}"

        slug = f"p{i}"
        (out / slug).mkdir(exist_ok=True)

        internal_url = f"./{slug}/"
        search_addr = norm_addr(addr) if addr else norm_addr(f"台中市 {reg} {name}")

        # ✅ build 時轉座標 + 快取
        lat, lng, _st = geocode_address(search_addr, cache)
        time.sleep(GEOCODE_SLEEP_SEC)

        map_data.append({
            "name": name,
            "price": p_str,
            "img": img,
            "url": internal_url,
            "address": search_addr,
            "lat": lat,
            "lng": lng
        })

        ext_link = next(
            (v for v in d.values()
             if str(v).startswith("http") and not any(x in str(v).lower() for x in [".jpg", ".png", ".jpeg", ".webp"])),
            ""
        )

        ext_btn = f'<a href="{ext_link}" target="_blank" class="btn-ext">🌐 前往 591 / 樂屋網 查看原始物件</a>' if ext_link else ""

        detail = f"""<div class="container">
<a href="../" class="back-link">← 返回列表</a>
<img src="{img}" style="width:100%;height:480px;object-fit:cover;display:block;">
<div style="padding:45px 25px;background:#fff;border-radius:45px 45px 0 0;margin-top:-55px;position:relative;">
  <h1 style="font-size:32px;font-weight:900;color:var(--sk-navy);margin:0;line-height:1.3;">{esc(name)}</h1>
  <div class="price" style="margin-top:15px;">{esc(p_str)}</div>
  <div style="line-height:2.2;color:#4a5568;margin:35px 0;font-size:17px;letter-spacing:0.5px;">{esc(d.get("描述","")).replace('、','<br>• ')}</div>

  <div class="advice-box">
    <strong style="font-size:17px;display:block;margin-bottom:10px;">💡 SK-L 專業顧問建議</strong>
    此物件地段具保值性。建議直接點擊下方 LINE 諮詢，我提供最新成交行情與貸款方案建議。
  </div>

  {ext_btn}

  <a href="https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(search_addr)}" target="_blank"
     style="display:block;text-align:center;padding:20px;background:var(--sk-navy);color:#fff;text-decoration:none;border-radius:18px;margin-top:15px;font-weight:800;font-size:15px;letter-spacing:1px;">
     📍 在地圖上開啟導航位置
  </a>

  {LEGAL_FOOTER}
</div>

<div class="action-bar">
  <a href="tel:{MY_PHONE}" class="btn btn-call">致電 SK-L</a>
  <a href="{MY_LINE_URL}" class="btn btn-line">LINE 諮詢</a>
</div>
</div>"""

        (out / slug / "index.html").write_text(
            f"<!doctype html><html lang='zh-TW'>{get_head(name + ' | ' + reg + '房產專家推薦', d.get('描述',''), img)}<body>{detail}</body></html>",
            encoding="utf-8"
        )

        price_val = "".join(filter(str.isdigit, p_str)) or "0"
        items.append(f"""<div class="property-card" data-region="{esc(reg)}" data-type="{esc(use_type)}" data-price="{price_val}">
  <a href="{internal_url}"><img src="{img}" style="width:100%;height:300px;object-fit:cover;display:block;"></a>
  <div class="card-info" style="padding:28px;">
    <h4 style="margin:0 0 10px;font-size:18px;color:var(--sk-navy);">{esc(name)}</h4>
    <div class="price">{esc(p_str)}</div>
    <div style="font-size:13px;color:#94a3b8;margin-top:8px;">{esc(reg)} · {esc(use_type)}</div>
    <a href="{internal_url}" style="display:block;text-align:center;margin-top:20px;padding:16px;background:#f1f5f9;color:var(--sk-navy);text-decoration:none;font-size:14px;font-weight:800;border-radius:14px;">查看 SK-L 置產建議</a>
  </div>
</div>""")

    save_cache(cache)

    # ✅ Actions 安全：用 &quot; 包住 onclick 的參數（不再用 \")
    reg_btns = "".join([
        f"<button class='tag f-reg' data-val='{esc(r)}' onclick='setTag(this, &quot;f-reg&quot;)'>{esc(r)}</button>"
        for r in sorted(regions)
    ])
    type_btns = "".join([
        f"<button class='tag f-type' data-val='{esc(t)}' onclick='setTag(this, &quot;f-type&quot;)'>{esc(t)}</button>"
        for t in sorted(types)
    ])

    map_json = json.dumps(map_data, ensure_ascii=False)

    home_html = f"""<div class="container">
<div class="hero"><div class="hero-content"><h2>{esc(SITE_TITLE)}</h2><p style="letter-spacing:3px;opacity:0.9;">Curated Real Estate · Taichung</p></div></div>
<div class="map-box"><div id="map"></div></div>

<div class="filter-section">
  <div class="filter-group">
    <button class="tag f-reg active" data-val="all" onclick="setTag(this, 'f-reg')">全部區域</button>
    {reg_btns}
  </div>
  <div class="filter-group" style="margin-top:12px;">
    <button class="tag f-type active" data-val="all" onclick="setTag(this, 'f-type')">所有用途</button>
    {type_btns}
  </div>
  <div class="filter-group" style="margin-top:12px; border-top:1px solid #f1f5f9; padding-top:20px;">
    <button class="tag f-sort active" data-val="none" onclick="setTag(this, 'f-sort')">預設排序</button>
    <button class="tag f-sort" data-val="high" onclick="setTag(this, 'f-sort')">價格：高至低</button>
    <button class="tag f-sort" data-val="low" onclick="setTag(this, 'f-sort')">價格：低至高</button>
  </div>
</div>

<div id="list">{''.join(items)}</div>
{LEGAL_FOOTER}

<div class="action-bar">
  <a href="tel:{MY_PHONE}" class="btn btn-call">致電 SK-L</a>
  <a href="{MY_LINE_URL}" class="btn btn-line">LINE 諮詢</a>
</div>
</div>"""

    (out / "index.html").write_text(
        f"<!doctype html><html lang='zh-TW'>{get_head(SITE_TITLE, is_home=True, map_data_json=map_json)}<body>{home_html}</body></html>",
        encoding="utf-8"
    )

if __name__ == "__main__":
    build()
