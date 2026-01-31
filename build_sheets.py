# build_sheets.py — FINAL（GitHub Actions 可過版）
# ✅ 自動地址轉座標（Geocoding）+ geocache.json 快取（同地址下次不再查）
# ✅ 首頁地圖打點用 lat/lng（不再前端 geocode、不燒訪客額度）
# ✅ 修正 GitHub Actions SyntaxError：onclick 內引號改用 &quot;（100% 穩）
#
# 你要做的只有：
# 1) GitHub Repo → Settings → Secrets and variables → Actions → New repository secret
#    - Name: MAPS_API_KEY
#    - Value: 你的 Google API Key
# 2) workflow 裡跑：python build_sheets.py
#
# 產出：./index.html + ./p*/index.html + geocache.json

import os, csv, requests, html, shutil, re, urllib.parse, json, time
from pathlib import Path
from datetime import datetime

# --- 1. 個人品牌配置 ---
SHEET_CSV_URL = os.getenv(
    "SHEET_CSV_URL",
    "https://docs.google.com/spreadsheets/d/e/2PACX-1vQShAl0-TbUU0MQdYVe53im2T6lXQgh_7g-bdL6HHpIBFtA2yfIAMbPw4J9RgZUkROb9AAiMhnRC0kH/pub?output=csv"
).strip()

MY_PHONE = os.getenv("MY_PHONE", "0938-615-351").strip()
MY_LINE_URL = os.getenv("MY_LINE_URL", "https://line.me/ti/p/FDsMyAYDv").strip()
SITE_TITLE = os.getenv("SITE_TITLE", "SK-L 大台中房地產").strip()
GA4_ID = os.getenv("GA4_ID", "G-B7WP9BTP8X").strip()

# ✅ 只從環境變數讀（避免硬寫暴露）
MAPS_API_KEY = os.getenv("MAPS_API_KEY", "").strip()

IMG_BASE = os.getenv("IMG_BASE", "https://raw.githubusercontent.com/ShihKaiLin/taichung-houses/main/images/").strip().rstrip("/") + "/"
BASE_URL = os.getenv("BASE_URL", "https://shihkailin.github.io/taichung-houses").strip().rstrip("/")

# --- 2. 合規資訊 ---
LEGAL_FOOTER = """
<div style="margin: 100px 0 40px; padding: 20px; text-align: center; border-top: 1px solid #f9f9f9;">
    <div style="font-size: 10px; color: #ddd; line-height: 1.6; letter-spacing: 0.5px;">
        英柏國際地產有限公司 | 中市地價二字第 1070029259 號<br>
        王一媖 經紀人 (103) 中市經紀字第 00678 號<br>
        <span style="opacity: 0.5;">© 2026 SK-L Branding</span>
    </div>
</div>
"""

# --- 3. 地理座標快取 ---
GEOCACHE_PATH = Path("geocache.json")
GEOCODE_SLEEP_SEC = float(os.getenv("GEOCODE_SLEEP_SEC", "0.25"))
GEOCODE_RETRY = int(os.getenv("GEOCODE_RETRY", "2"))
GEOCODE_TIMEOUT = int(os.getenv("GEOCODE_TIMEOUT", "20"))
GEOCODE_REGION = os.getenv("GEOCODE_REGION", "tw").strip()
GEOCODE_LANGUAGE = os.getenv("GEOCODE_LANGUAGE", "zh-TW").strip()

def esc(s):
    return html.escape(str(s or "").strip())

def norm_addr(s: str) -> str:
    s = str(s or "").strip()
    s = s.replace("臺中市", "台中市")
    s = re.sub(r"\s+", " ", s)
    return s

def load_cache() -> dict:
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
        return None, None, None

    if addr in cache and isinstance(cache[addr], dict):
        v = cache[addr]
        lat = v.get("lat")
        lng = v.get("lng")
        fmt = v.get("formatted_address")
        if lat is not None and lng is not None:
            return lat, lng, fmt

    if not MAPS_API_KEY:
        cache[addr] = {"lat": None, "lng": None, "formatted_address": None, "status": "NO_API_KEY"}
        return None, None, None

    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": addr,
        "key": MAPS_API_KEY,
        "region": GEOCODE_REGION,
        "language": GEOCODE_LANGUAGE
    }

    last_status = None
    for attempt in range(GEOCODE_RETRY + 1):
        try:
            r = requests.get(url, params=params, timeout=GEOCODE_TIMEOUT)
            data = r.json()
            status = data.get("status")
            last_status = status

            if status == "OK" and data.get("results"):
                loc = data["results"][0]["geometry"]["location"]
                lat = float(loc["lat"])
                lng = float(loc["lng"])
                fmt = data["results"][0].get("formatted_address") or None
                cache[addr] = {"lat": lat, "lng": lng, "formatted_address": fmt, "status": "OK"}
                return lat, lng, fmt

            if status in ("OVER_QUERY_LIMIT", "UNKNOWN_ERROR"):
                time.sleep(max(GEOCODE_SLEEP_SEC, 0.6) * (attempt + 1))
                continue

            cache[addr] = {"lat": None, "lng": None, "formatted_address": None, "status": status or "ERROR"}
            return None, None, None

        except Exception:
            time.sleep(max(GEOCODE_SLEEP_SEC, 0.6) * (attempt + 1))
            continue

    cache[addr] = {"lat": None, "lng": None, "formatted_address": None, "status": last_status or "ERROR"}
    return None, None, None

def get_head(title, desc="", is_home=False, map_data_json="[]"):
    seo_desc = esc(desc)[:80] if desc else f"{SITE_TITLE} - 精選台中優質房產，由林世塏提供專業不動產買賣服務。"
    ga = ""
    if GA4_ID:
        ga = f"""<script async src="https://www.googletagmanager.com/gtag/js?id={GA4_ID}"></script><script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','{GA4_ID}');</script>"""

    script = ""
    if is_home and MAPS_API_KEY:
        script = f"""
<script src="https://maps.googleapis.com/maps/api/js?key={MAPS_API_KEY}"></script>
<script>
function filterAndSort() {{
  const reg = document.querySelector('.tag.f-reg.active').dataset.val;
  const type = document.querySelector('.tag.f-type.active').dataset.val;
  const sort = document.querySelector('.tag.f-sort.active').dataset.val;
  let cards = Array.from(document.querySelectorAll('.property-card'));
  cards.forEach(c => {{
    const mReg = (reg === 'all' || c.dataset.region === reg);
    const mType = (type === 'all' || c.dataset.type === type);
    c.style.display = (mReg && mType) ? 'block' : 'none';
  }});
  if (sort !== 'none') {{
    cards.sort((a,b)=> {{
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
    center: {{ lat: 24.162, lng: 120.647 }},
    zoom: 12,
    disableDefaultUI: true,
    zoomControl: true
  }});
  const locations = {map_data_json};
  locations.forEach(loc => {{
    if (!loc.lat || !loc.lng) return;
    const marker = new google.maps.Marker({{
      position: {{ lat: loc.lat, lng: loc.lng }},
      map: map,
      title: loc.name
    }});
    marker.addListener("click", () => {{
      if (loc.url.startsWith('http')) window.open(loc.url, '_blank');
      else window.location.href = loc.url;
    }});
  }});
}}
window.onload = initMap;
</script>
        """

    return f"""<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{seo_desc}">
{ga}
{script}
<style>
:root{{--sk-navy:#1A365D;--sk-gold:#C5A059;}}
body{{font-family:sans-serif;margin:0;background:#fff;-webkit-font-smoothing:antialiased;}}
.container{{max-width:500px;margin:auto;background:#fff;min-height:100vh;position:relative;box-shadow:0 0 40px rgba(0,0,0,0.05);}}
.hero{{height:320px;background:url('{IMG_BASE}hero_bg.jpg') center/cover;display:flex;align-items:center;justify-content:center;color:#fff;position:relative;}}
.hero::after{{content:'';position:absolute;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.3);}}
.hero-content{{position:relative;z-index:2;text-align:center;}}
.hero-content h2{{font-size:32px;margin:0;letter-spacing:5px;font-weight:900;}}
.map-box{{margin:-40px 20px 0;position:relative;z-index:10;}}
#map{{height:280px;border-radius:20px;box-shadow:0 15px 40px rgba(0,0,0,0.1);border:5px solid #fff;}}
.filter-section{{padding:35px 20px 10px;}}
.filter-group{{display:flex;gap:10px;overflow-x:auto;padding-bottom:15px;scrollbar-width:none;}}
.tag{{padding:8px 18px;border-radius:50px;background:#f0f2f5;font-size:13px;color:#666;cursor:pointer;white-space:nowrap;border:none;font-weight:600;}}
.tag.active{{background:var(--sk-navy);color:#fff;}}
.property-card{{margin:30px 20px;border-radius:24px;overflow:hidden;background:#fff;box-shadow:0 10px 30px rgba(0,0,0,0.05);}}
.price{{font-size:22px;color:var(--sk-gold);font-weight:900;}}
.action-bar{{position:fixed;bottom:0;left:50%;transform:translateX(-50%);width:100%;max-width:500px;padding:15px 25px 40px;display:flex;gap:12px;background:rgba(255,255,255,0.85);backdrop-filter:blur(15px);border-top:1px solid #f1f1f1;z-index:999;}}
.btn{{flex:1;text-align:center;padding:18px;border-radius:18px;text-decoration:none;font-weight:800;color:#fff;font-size:15px;}}
.btn-call{{background:#1A202C;}}
.btn-line{{background:#00B900;}}
.back-btn{{position:absolute;top:25px;left:25px;background:#fff;padding:10px 20px;border-radius:14px;text-decoration:none;font-weight:800;color:var(--sk-navy);z-index:100;box-shadow:0 5px 15px rgba(0,0,0,0.1);}}
.btn-ext{{display:block;text-align:center;padding:16px;background:var(--sk-navy);color:#fff;text-decoration:none;border-radius:14px;margin-top:15px;font-weight:700;}}
</style>
</head>"""

def build():
    out = Path(".")

    # 清掉舊 p*
    for p in out.glob("p*"):
        if p.is_dir() and re.match(r"^p\d+$", p.name):
            shutil.rmtree(p)

    cache = load_cache()

    # 拉 CSV
    res = requests.get(SHEET_CSV_URL, timeout=25)
    res.raise_for_status()
    res.encoding = "utf-8-sig"
    reader = csv.DictReader(res.text.splitlines())

    items, map_data, regions, types = [], [], set(), set()
    num_re = re.compile(r"[^\d.]")
    sitemap_urls = [f"{BASE_URL}/"]

    for i, row in enumerate(reader):
        d = {str(k).strip(): str(v).strip() for k, v in row.items() if k}

        name = d.get("案名") or next((v for k, v in d.items() if "案名" in k), "")
        if not name:
            continue
        if str(d.get("狀態", "")).upper() in ["OFF", "FALSE", "0"]:
            continue

        ext_url = next(
            (
                v for v in d.values()
                if isinstance(v, str) and v.startswith("http")
                and not any(x in v.lower() for x in [".jpg", ".png", ".jpeg", ".webp"])
            ),
            ""
        )

        reg = d.get("區域", "台中")
        use_type = d.get("用途", "住宅")
        p_str = d.get("價格", "面議")
        addr = d.get("地址", name)
        slug = f"p{i}"

        regions.add(reg)
        types.add(use_type)

        img = d.get("圖片網址") or next((v for k, v in d.items() if "圖片" in k), "")
        img = (img or "").strip()
        if img and not img.startswith("http"):
            img = f"{IMG_BASE}{img.lstrip('/')}"
        if not img:
            img = "https://placehold.co/900x700?text=No+Image"

        (out / slug).mkdir(exist_ok=True)

        # ✅ build 時地址轉座標 + 快取
        lat, lng, fmt = geocode_address(addr, cache)
        time.sleep(GEOCODE_SLEEP_SEC)

        f_url = ext_url if ext_url.startswith("http") else f"./{slug}/"
        map_data.append({
            "name": name,
            "address": fmt or norm_addr(addr),
            "url": f_url,
            "lat": lat,
            "lng": lng
        })

        page_url = f"{BASE_URL}/{slug}/"
        sitemap_urls.append(page_url)

        ext_btn = f'<a href="{ext_url}" target="_blank" class="btn-ext">🌐 查看完整物件網頁 (591/樂屋)</a>' if ext_url else ""
        desc_html = esc(d.get("描述", "")).replace("、", "<br>• ")

        detail = f"""
<div class="container">
  <a href="../" class="back-btn">← 返回</a>
  <img src="{img}" style="width:100%;height:450px;object-fit:cover;display:block;">
  <div style="padding:40px 25px;background:#fff;border-radius:40px 40px 0 0;margin-top:-50px;position:relative;">
    <h1 style="font-size:28px;font-weight:800;color:var(--sk-navy);margin:0;">{esc(name)}</h1>
    <div class="price">{esc(p_str)}</div>
    <div style="line-height:2.1;color:#4a5568;margin:25px 0;font-size:16px;">{desc_html}</div>
    {ext_btn}
    <a href="https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(norm_addr(addr))}" target="_blank"
       style="display:block;text-align:center;padding:18px;background:var(--sk-navy);color:#fff;text-decoration:none;border-radius:15px;margin-top:15px;font-weight:700;">📍 前往地圖導航</a>
    {LEGAL_FOOTER}
  </div>
  <div class="action-bar">
    <a href="tel:{MY_PHONE}" class="btn btn-call">致電 SK-L</a>
    <a href="{MY_LINE_URL}" class="btn btn-line">LINE 諮詢</a>
  </div>
</div>
"""
        (out / slug / "index.html").write_text(
            f"<!doctype html><html lang='zh-TW'>{get_head(name + ' | ' + reg + '買屋推薦', d.get('描述',''))}<body>{detail}</body></html>",
            encoding="utf-8"
        )

        is_ext = ext_url.startswith("http")
        target = 'target="_blank"' if is_ext else ""
        price_num = num_re.sub("", p_str or "")
        items.append(f"""
<div class="property-card" data-region="{esc(reg)}" data-type="{esc(use_type)}" data-price="{price_num}">
  <a href="{f_url}" {target}>
    <img src="{img}" style="width:100%;height:280px;object-fit:cover;display:block;">
  </a>
  <div class="card-info" style="padding:25px;">
    <h4 style="margin:0 0 8px;">{esc(name)}</h4>
    <div class="price">{esc(p_str)}</div>
    <div style="font-size:12px;color:#999;">{esc(reg)} • {esc(use_type)}</div>
    <a href="{f_url}" {target}
       style="display:block;text-align:center;margin-top:15px;padding:14px;background:#f8fafc;color:var(--sk-navy);text-decoration:none;font-size:13px;font-weight:700;border-radius:12px;">
       {"立即前往物件網頁" if is_ext else "查看詳情"}
    </a>
  </div>
</div>
""")

    save_cache(cache)

    # ✅ 關鍵：onclick 內引號用 &quot;，避免 GitHub Actions f-string 逃脫炸掉
    reg_btns = "".join([
        f'<button class="tag f-reg" data-val="{esc(r)}" onclick="setTag(this, &quot;f-reg&quot;)">{esc(r)}</button>'
        for r in sorted(regions)
    ])
    type_btns = "".join([
        f'<button class="tag f-type" data-val="{esc(t)}" onclick="setTag(this, &quot;f-type&quot;)">{esc(t)}</button>'
        for t in sorted(types)
    ])

    map_data_json = json.dumps(map_data, ensure_ascii=False)

    map_block = '<div class="map-box"><div id="map"></div></div>' if MAPS_API_KEY else (
        '<div style="margin:-20px 20px 0; padding:16px; background:#fff; border-radius:16px; '
        'box-shadow:0 10px 30px rgba(0,0,0,0.05); color:#666; font-size:13px;">'
        '⚠️ 尚未設定 MAPS_API_KEY（地圖功能已自動關閉）</div>'
    )

    home_html = f"""
<div class="container">
  <div class="hero">
    <div class="hero-content">
      <h2>{esc(SITE_TITLE)}</h2>
      <p>Curated Real Estate • Taichung</p>
    </div>
  </div>

  {map_block}

  <div class="filter-section">
    <div class="filter-group">
      <button class="tag f-reg active" data-val="all" onclick="setTag(this, 'f-reg')">全部地區</button>
      {reg_btns}
    </div>
    <div class="filter-group" style="margin-top:10px;">
      <button class="tag f-type active" data-val="all" onclick="setTag(this, 'f-type')">所有用途</button>
      {type_btns}
    </div>
    <div class="filter-group" style="margin-top:10px; border-top:1px solid #f0f0f0; padding-top:15px;">
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
</div>
"""

    (out / "index.html").write_text(
        f"<!doctype html><html lang='zh-TW'>{get_head(SITE_TITLE, is_home=True, map_data_json=map_data_json)}<body>{home_html}</body></html>",
        encoding="utf-8"
    )

    # sitemap（可選，但建議有）
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    today = datetime.now().strftime("%Y-%m-%d")
    for u in sitemap_urls:
        sitemap += f'  <url><loc>{u}</loc><lastmod>{today}</lastmod></url>\n'
    sitemap += "</urlset>"
    (out / "sitemap.xml").write_text(sitemap, encoding="utf-8")

    print("✅ build 完成：index.html + p* 物件頁 + geocache.json + sitemap.xml")

if __name__ == "__main__":
    build()
