import os, csv, requests, html, shutil, re, urllib.parse, json, time
from pathlib import Path
from datetime import datetime, timezone

# ============================================================
# SK-L BUILD.PY (MAP + FILTER + STATUS/STATE/FEATURE/PRICE/LIFE/AGENT)
# ============================================================

# --- Core Config ---
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQShAl0-TbUU0MQdYVe53im2T6lXQgh_7g-bdL6HHpIBFtA2yfIAMbPw4J9RgZUkROb9AAiMhnRC0kH/pub?output=csv"

BASE_URL = "https://shihkailin.github.io/taichung-houses"
SITE_TITLE = "SK-L 大台中房地產"
SITE_SLOGAN = "林世塏｜台中精選房產｜買屋/賣屋/委託"
GA4_ID = "G-B7WP9BTP8X"

MY_NAME = "林世塏"
MY_PHONE = "0938-615-351"
MY_LINE_URL = "https://line.me/ti/p/FDsMyAYDv"

# Maps (Home Map + address geocode cache)
MAPS_API_KEY = os.getenv("MAPS_API_KEY", "").strip()
GEOCACHE_PATH = Path("geocache.json")
GEOCODE_SLEEP_SEC = float(os.getenv("GEOCODE_SLEEP_SEC", "0.2"))

# Images
IMG_RAW_BASE = "https://raw.githubusercontent.com/ShihKaiLin/taichung-houses/main/images/"
DEFAULT_HERO = f"{IMG_RAW_BASE}hero_bg.jpg"

# Posts
POSTS_DIR = Path("posts")

# Clean output dirs
CLEAN_TARGET_DIRS = ["status", "state", "feature", "price", "life", "agent"]


# ============================================================
# Utilities
# ============================================================
def esc(s):
    return html.escape(str(s or "").strip())

def norm_text(s):
    s = str(s or "").strip().replace("\ufeff", "")
    s = re.sub(r"\s+", " ", s)
    return s

def now_ymd():
    return datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d")

def url_join(base, path):
    return f"{base.rstrip('/')}/{path.lstrip('/')}"

def safe_dirname(label: str) -> str:
    label = norm_text(label)
    return urllib.parse.quote(label, safe="") if label else "unknown"

def split_tags(s: str):
    s = norm_text(s)
    if not s:
        return []
    parts = re.split(r"[、,，;；\|\｜/\\\n\r]+", s)
    return [p.strip() for p in parts if p.strip()]

def is_truthy(v):
    v = norm_text(v).upper()
    return v in ["ON", "TRUE", "YES", "Y", "1", "OK"]

def pick_field(d: dict, candidates: list, fallback=""):
    for c in candidates:
        if c in d:
            return d.get(c, fallback)
    for c in candidates:
        for k in d.keys():
            if c in k:
                return d.get(k, fallback)
    return fallback

def first_http_link(d: dict):
    prefer_keys = ["連結", "網址", "外連", "外部連結", "591", "樂屋", "物件連結", "物件網址", "URL", "Link"]
    for want in prefer_keys:
        for k, v in d.items():
            vv = str(v).strip()
            if want in k and vv.startswith("http"):
                if not re.search(r"\.(jpg|jpeg|png|webp)(\?|$)", vv.lower()):
                    return vv
    for v in d.values():
        vv = str(v).strip()
        if vv.startswith("http") and not re.search(r"\.(jpg|jpeg|png|webp)(\?|$)", vv.lower()):
            return vv
    return ""

def normalize_img(img):
    img = norm_text(img)
    if not img:
        return "https://placehold.co/800x600?text=%E7%84%A1%E5%9C%96%E7%89%87"
    if img.startswith("http"):
        return img
    img = img.lstrip("/")
    if img.startswith("images/"):
        img = img.split("images/", 1)[1]
    return f"{IMG_RAW_BASE}{img}"

def parse_price_number(price_str: str):
    s = norm_text(price_str)
    if not s:
        return None
    m = re.search(r"([\d,]+)\s*萬", s)
    if m:
        try:
            return float(m.group(1).replace(",", ""))
        except:
            return None
    m2 = re.search(r"([\d,]{3,})", s)
    if m2:
        try:
            return float(m2.group(1).replace(",", ""))
        except:
            return None
    return None

def auto_price_bucket(price_wan: float):
    if price_wan is None:
        return "面議/未填"
    if price_wan < 800:
        return "800萬以下"
    if price_wan < 1200:
        return "800-1200萬"
    if price_wan < 1600:
        return "1200-1600萬"
    if price_wan < 2000:
        return "1600-2000萬"
    if price_wan < 3000:
        return "2000-3000萬"
    return "3000萬以上"

def minimal_markdown_to_html(md: str):
    lines = (md or "").replace("\r\n", "\n").replace("\r", "\n").split("\n")
    out = []
    in_list = False

    def close_list():
        nonlocal in_list
        if in_list:
            out.append("</ul>")
            in_list = False

    def linkify(s):
        return re.sub(r"\[([^\]]+)\]\((https?://[^\)]+)\)", r"<a href='\2' target='_blank'>\1</a>", esc(s))

    for line in lines:
        raw = line.strip()
        if not raw:
            close_list()
            continue
        if raw.startswith("#"):
            close_list()
            level = len(raw) - len(raw.lstrip("#"))
            level = max(1, min(level, 3))
            title = raw.lstrip("#").strip()
            out.append(f"<h{level}>{linkify(title)}</h{level}>")
            continue
        if raw.startswith("- "):
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append(f"<li>{linkify(raw[2:].strip())}</li>")
            continue
        close_list()
        out.append(f"<p>{linkify(raw)}</p>")
    close_list()
    return "\n".join(out)


# ============================================================
# Geocode (Address -> lat/lng) with cache
# ============================================================
def load_geocache():
    if GEOCACHE_PATH.exists():
        try:
            return json.loads(GEOCACHE_PATH.read_text(encoding="utf-8"))
        except:
            return {}
    return {}

def save_geocache(cache: dict):
    GEOCACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")

def geocode_address(addr: str, cache: dict):
    addr = norm_text(addr)
    if not addr:
        return None

    key = addr
    if key in cache:
        return cache[key]

    if not MAPS_API_KEY:
        return None

    # Google Geocoding API (server-side, for build time)
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {"address": addr, "key": MAPS_API_KEY, "region": "tw", "language": "zh-TW"}
    try:
        r = requests.get(url, params=params, timeout=15)
        data = r.json()
        if data.get("status") == "OK" and data.get("results"):
            loc = data["results"][0]["geometry"]["location"]
            cache[key] = {"lat": loc["lat"], "lng": loc["lng"], "ts": now_ymd()}
            time.sleep(GEOCODE_SLEEP_SEC)
            return cache[key]
        else:
            cache[key] = None
            time.sleep(GEOCODE_SLEEP_SEC)
            return None
    except:
        cache[key] = None
        return None


# ============================================================
# JSON-LD
# ============================================================
def jsonld_agent():
    return {
        "@context": "https://schema.org",
        "@type": "RealEstateAgent",
        "name": SITE_TITLE,
        "telephone": MY_PHONE,
        "url": url_join(BASE_URL, "/"),
        "areaServed": "Taichung, Taiwan",
        "sameAs": [MY_LINE_URL],
    }

def jsonld_listing(name, desc, img, page_url, address, price_wan, property_type, area):
    offers = None
    if price_wan is not None:
        offers = {
            "@type": "Offer",
            "priceCurrency": "TWD",
            "price": int(round(price_wan * 10000)),
            "availability": "https://schema.org/InStock",
            "url": page_url,
        }
    data = {
        "@context": "https://schema.org",
        "@type": "RealEstateListing",
        "name": name,
        "description": (desc or "")[:600],
        "image": [img] if img else [],
        "url": page_url,
    }
    if offers:
        data["offers"] = offers
    if address:
        data["address"] = {
            "@type": "PostalAddress",
            "streetAddress": address,
            "addressLocality": area or "Taichung",
            "addressCountry": "TW",
        }
    if property_type:
        data["category"] = property_type
    return data


# ============================================================
# Head / CSS / JS (Home Map + Filters)
# ============================================================
def get_head(title, desc="", og_img="", og_url="", extra_jsonld=None, is_home=False):
    seo_desc = esc(desc)[:120] if desc else esc(SITE_SLOGAN)
    og_img = og_img if (og_img and str(og_img).startswith("http")) else DEFAULT_HERO
    og_url = og_url if (og_url and str(og_url).startswith("http")) else url_join(BASE_URL, "/")

    ga = ""
    if GA4_ID:
        ga = (
            f"<script async src='https://www.googletagmanager.com/gtag/js?id={GA4_ID}'></script>"
            f"<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}"
            f"gtag('js',new Date());gtag('config','{GA4_ID}');</script>"
        )

    jsonlds = [jsonld_agent()]
    if extra_jsonld:
        if isinstance(extra_jsonld, list):
            jsonlds.extend(extra_jsonld)
        else:
            jsonlds.append(extra_jsonld)
    jsonld_script = "<script type='application/ld+json'>" + json.dumps(jsonlds, ensure_ascii=False) + "</script>"

    # Home-only scripts: Map + filter
    home_js = ""
    if is_home:
        # Map JS only loads if MAPS_API_KEY exists (client-side)
        # We render markers from precomputed lat/lng; if no lat/lng, marker skipped.
        maps_loader = ""
        if MAPS_API_KEY:
            maps_loader = f"<script src='https://maps.googleapis.com/maps/api/js?key={MAPS_API_KEY}&callback=initMap' async defer></script>"
        home_js = f"""
<script>
let SK_MAP=null, SK_MARKERS=[];
function _qs(sel){{return document.querySelector(sel);}}
function _qsa(sel){{return Array.from(document.querySelectorAll(sel));}}

function filterCards(){{
  const reg = _qs('.tag.f-reg.active')?.dataset.val || 'all';
  const typ = _qs('.tag.f-type.active')?.dataset.val || 'all';
  const sort = _qs('.tag.f-sort.active')?.dataset.val || 'none';

  let cards = _qsa('.property-card');

  cards.forEach(c=>{{
    const mR = (reg==='all' || c.dataset.region===reg);
    const mT = (typ==='all' || c.dataset.type===typ);
    c.style.display = (mR && mT) ? 'block' : 'none';
  }});

  if(sort!=='none'){{
    const list = _qs('#list');
    const visible = cards.filter(c=>c.style.display!=='none');
    visible.sort((a,b)=>{{
      const pA = parseFloat(a.dataset.price)||0;
      const pB = parseFloat(b.dataset.price)||0;
      return sort==='high' ? (pB-pA) : (pA-pB);
    }});
    visible.forEach(c=>list.appendChild(c));
  }}
  syncMarkers();
}}

function setTag(btn, cls){{
  btn.parentElement.querySelectorAll('.'+cls).forEach(b=>b.classList.remove('active'));
  btn.classList.add('active');
  filterCards();
}}

function syncMarkers(){{
  if(!SK_MAP || !SK_MARKERS.length) return;
  const reg = _qs('.tag.f-reg.active')?.dataset.val || 'all';
  const typ = _qs('.tag.f-type.active')?.dataset.val || 'all';
  SK_MARKERS.forEach(m=>{{
    const okR = (reg==='all' || m.__region===reg);
    const okT = (typ==='all' || m.__type===typ);
    m.setVisible(okR && okT);
  }});
}}

function initMap(){{
  const el = document.getElementById('map');
  if(!el) return;
  const data = window.__MAP_DATA__ || [];
  if(typeof google==='undefined' || !google.maps) {{
    el.innerHTML = "<div style='padding:18px;color:#64748b;'>地圖載入失敗（請確認 MAPS_API_KEY 或網路）</div>";
    return;
  }}
  const center = {{lat:24.162, lng:120.647}};
  SK_MAP = new google.maps.Map(el, {{
    center, zoom: 12, disableDefaultUI: true, zoomControl: true,
    styles: [{{"featureType":"poi","stylers":[{{"visibility":"off"}}]}}]
  }});
  const infow = new google.maps.InfoWindow();

  data.forEach(loc=>{{
    if(typeof loc.lat!=='number' || typeof loc.lng!=='number') return;
    const marker = new google.maps.Marker({{
      position: {{lat:loc.lat, lng:loc.lng}},
      map: SK_MAP,
      title: loc.name,
      animation: google.maps.Animation.DROP
    }});
    marker.__region = loc.region || "";
    marker.__type = loc.type || "";
    marker.addListener('click', ()=>{{
      const content = `
        <div style="padding:10px;width:220px;font-family:system-ui, -apple-system, 'PingFang TC', 'Microsoft JhengHei', sans-serif;">
          <div style="background:url('${{loc.img}}') center/cover;height:110px;border-radius:10px;margin-bottom:10px;"></div>
          <div style="font-weight:900;color:#1A365D;font-size:14px;line-height:1.35;">${{loc.name}}</div>
          <div style="color:#C5A059;font-weight:950;font-size:16px;margin:6px 0 10px;">${{loc.price}}</div>
          <a href="${{loc.url}}" style="display:block;text-align:center;background:#1A365D;color:#fff;text-decoration:none;padding:10px;border-radius:10px;font-size:12px;font-weight:900;">查看詳情</a>
        </div>`;
      infow.setContent(content);
      infow.open(SK_MAP, marker);
    }});
    SK_MARKERS.push(marker);
  }});

  syncMarkers();
}}
</script>
{maps_loader}
"""
    return f"""<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=0">
<title>{esc(title)}</title>
<meta name="description" content="{seo_desc}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{seo_desc}">
<meta property="og:image" content="{esc(og_img)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{esc(og_url)}">
{ga}
{jsonld_script}
<style>
:root{{--sk-navy:#1A365D;--sk-gold:#C5A059;--sk-light:#F8FAFC;--sk-shadow:0 15px 45px rgba(0,0,0,0.08);}}
body{{font-family:'PingFang TC','Microsoft JhengHei',sans-serif;margin:0;background:#fff;-webkit-font-smoothing:antialiased;}}
.container{{max-width:520px;margin:auto;background:#fff;min-height:100vh;position:relative;box-shadow:0 0 60px rgba(0,0,0,0.05);}}
.hero{{height:320px;background:url('{DEFAULT_HERO}') center/cover;display:flex;align-items:center;justify-content:center;color:#fff;position:relative;}}
.hero::after{{content:'';position:absolute;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.35);}}
.hero-content{{position:relative;z-index:2;text-align:center;padding:0 18px;}}
.hero-content h1{{font-size:30px;margin:0;letter-spacing:4px;font-weight:900;text-shadow:0 2px 10px rgba(0,0,0,0.3);}}
.hero-content p{{margin:10px 0 0;opacity:.92;letter-spacing:1px;font-weight:600}}

.navbar{{display:flex;gap:10px;overflow:auto;padding:14px 16px;border-bottom:1px solid #eef2f7;background:rgba(255,255,255,.98);position:sticky;top:0;z-index:50}}
.navbtn{{flex:0 0 auto;padding:10px 14px;border-radius:999px;background:var(--sk-light);border:1px solid #e5eaf0;color:#344054;text-decoration:none;font-weight:900;font-size:13px}}
.navbtn.active{{background:var(--sk-navy);border-color:var(--sk-navy);color:#fff}}

.mapWrap{{margin:-42px 16px 0;position:relative;z-index:20}}
#map{{height:300px;border-radius:22px;box-shadow:var(--sk-shadow);border:6px solid #fff;background:#f1f5f9;overflow:hidden}}

.section{{padding:18px 16px}}
.section h2{{margin:0 0 10px;font-size:18px;color:var(--sk-navy);letter-spacing:.5px}}
.badges{{display:flex;gap:8px;flex-wrap:wrap}}
.badge{{font-size:12px;background:#f1f5f9;border:1px solid #e2e8f0;color:#334155;padding:7px 10px;border-radius:999px;text-decoration:none;font-weight:900}}

.filter-section{{padding:18px 16px 0}}
.filter-group{{display:flex;gap:10px;overflow:auto;padding-bottom:10px;scrollbar-width:none}}
.tag{{padding:10px 16px;border-radius:999px;background:var(--sk-light);border:1px solid #e5eaf0;color:#344054;font-weight:900;font-size:13px;cursor:pointer;white-space:nowrap}}
.tag.active{{background:var(--sk-navy);border-color:var(--sk-navy);color:#fff}}

.card{{margin:18px 16px;border-radius:22px;overflow:hidden;background:#fff;box-shadow:var(--sk-shadow);border:1px solid #f1f5f9}}
.card img{{width:100%;height:280px;object-fit:cover;display:block;background:#f3f4f6}}
.cardbody{{padding:18px 16px}}
.title{{margin:0;font-size:17px;font-weight:950;color:var(--sk-navy);line-height:1.35}}
.meta{{margin-top:8px;color:#64748b;font-size:13px;font-weight:800}}
.price{{margin-top:8px;font-size:22px;color:var(--sk-gold);font-weight:950;letter-spacing:-.5px}}
.cta{{display:block;margin-top:14px;text-align:center;padding:14px;border-radius:14px;background:#f1f5f9;color:var(--sk-navy);text-decoration:none;font-weight:950;font-size:14px}}

.detailHero img{{width:100%;height:460px;object-fit:cover;display:block}}
.detailBox{{padding:24px 16px;background:#fff;border-radius:28px 28px 0 0;margin-top:-22px;position:relative}}
.detailBox h1{{margin:0;font-size:26px;font-weight:980;color:var(--sk-navy);line-height:1.25}}
.desc{{margin-top:14px;line-height:2.0;color:#475569;font-size:16px}}
.btnRow{{display:flex;gap:10px;margin-top:16px}}
.btn{{flex:1;text-align:center;padding:14px;border-radius:16px;text-decoration:none;font-weight:980;color:#fff;font-size:14px}}
.btnCall{{background:#111827}}
.btnLine{{background:#00B900}}
.btnExt{{display:block;text-align:center;padding:14px;border-radius:16px;text-decoration:none;font-weight:980;color:var(--sk-navy);border:2px solid #e5eaf0;background:#fff;margin-top:12px}}
.btnMap{{display:block;text-align:center;padding:14px;border-radius:16px;text-decoration:none;font-weight:980;color:#fff;background:var(--sk-navy);margin-top:12px}}

.footer{{margin:80px 0 0;padding:22px 16px;border-top:1px solid #eef2f7;color:#94a3b8;font-size:12px;line-height:1.7;text-align:center}}
.footer strong{{color:#334155}}

.actionbar{{position:fixed;bottom:0;left:50%;transform:translateX(-50%);width:100%;max-width:520px;padding:16px 16px 34px;display:flex;gap:10px;background:rgba(255,255,255,0.96);backdrop-filter:blur(18px);border-top:1px solid #eef2f7;z-index:80}}
.actionbar a{{flex:1;text-align:center;padding:16px;border-radius:18px;text-decoration:none;font-weight:980;color:#fff;font-size:15px;box-shadow:0 4px 12px rgba(0,0,0,.08)}}
.actionbar .call{{background:#111827}}
.actionbar .line{{background:#00B900}}

.postBody{{padding:18px 16px 40px}}
.postBody h1,.postBody h2,.postBody h3{{color:var(--sk-navy)}}
.postBody p{{color:#475569;line-height:2.0;font-size:16px}}
.postBody ul{{padding-left:20px;color:#475569;line-height:2.0;font-size:16px}}
.postBody a{{color:var(--sk-navy);font-weight:950}}
</style>
{home_js}
</head>"""


# ============================================================
# Page helpers
# ============================================================
LEGAL_FOOTER = """
<div class="footer">
  <strong>英柏國際地產有限公司</strong>｜中市地價二字第 1070029259 號<br>
  經紀人：王一媖（103）中市經紀字第00678號<br>
  © 2026 SK-L Branding
</div>
"""

def wrap_page(title, body_html, desc="", og_img="", og_url="", extra_jsonld=None, is_home=False):
    return f"<!doctype html><html lang='zh-TW'>{get_head(title, desc, og_img, og_url, extra_jsonld, is_home=is_home)}<body>{body_html}</body></html>"

def build_nav(active="home"):
    items = [
        ("home", "首頁", "/"),
        ("status", "精選物件", "/status/精選物件/"),
        ("state", "生活圈", "/state/"),
        ("feature", "特色", "/feature/"),
        ("price", "價格帶", "/price/"),
        ("life", "文章", "/life/"),
        ("agent", "聯絡", "/agent/"),
    ]
    htmls = ["<div class='navbar'>"]
    for key, label, path in items:
        cls = "navbtn" + (" active" if key == active else "")
        htmls.append(f"<a class='{cls}' href='{path}'>{esc(label)}</a>")
    htmls.append("</div>")
    return "".join(htmls)

def build_actionbar():
    return f"""
<div class="actionbar">
  <a class="call" href="tel:{MY_PHONE}">📞 直接致電</a>
  <a class="line" href="{MY_LINE_URL}" target="_blank">💬 LINE 諮詢</a>
</div>
"""

def card_html(item):
    return f"""
<div class="property-card card" data-region="{esc(item['area'])}" data-type="{esc(item['type'])}" data-price="{esc(item['price_num'])}">
  <a href="{esc(item['url'])}">
    <img src="{esc(item['img'])}" alt="{esc(item['name'])}">
  </a>
  <div class="cardbody">
    <h3 class="title">{esc(item['name'])}</h3>
    <div class="meta">{esc(item['area'])} · {esc(item['type'])}</div>
    <div class="price">{esc(item['price'])}</div>
    <a class="cta" href="{esc(item['url'])}">查看詳情</a>
  </div>
</div>
"""


# ============================================================
# Build core
# ============================================================
def clean_output(root: Path):
    for p in root.glob("p*"):
        if p.is_dir() and re.match(r"^p\d+$", p.name):
            shutil.rmtree(p)
    for d in CLEAN_TARGET_DIRS:
        if (root / d).exists():
            shutil.rmtree(root / d)
    for f in ["index.html", "sitemap.xml"]:
        fp = root / f
        if fp.exists():
            fp.unlink()

def build_sitemap(root: Path, urls: list):
    seen, uniq = set(), []
    for u in urls:
        if u not in seen:
            seen.add(u)
            uniq.append(u)
    lastmod = now_ymd()
    xml = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in uniq:
        xml += ["  <url>", f"    <loc>{html.escape(u)}</loc>", f"    <lastmod>{lastmod}</lastmod>", "  </url>"]
    xml.append("</urlset>")
    (root / "sitemap.xml").write_text("\n".join(xml), encoding="utf-8")

def build_agent_page(root: Path, urls: list):
    (root / "agent").mkdir(parents=True, exist_ok=True)
    page_url = url_join(BASE_URL, "/agent/")
    urls.append(page_url)
    body = f"""
<div class="container">
  {build_nav("agent")}
  <div class="section">
    <h2>聯絡 {esc(MY_NAME)}</h2>
    <div class="badges">
      <a class="badge" href="tel:{MY_PHONE}">📞 {esc(MY_PHONE)}</a>
      <a class="badge" href="{MY_LINE_URL}" target="_blank">💬 LINE 立即諮詢</a>
      <a class="badge" href="/">🏠 回到首頁</a>
    </div>
  </div>
  <div class="section">
    <h2>服務項目</h2>
    <div style="color:#475569;line-height:2.0;font-size:16px;">
      ・台中買屋／賣屋／委託<br>
      ・社區行情／成交分析／貸款試算<br>
      ・專任委託／快速曝光策略（不亂報、重誠信）<br>
    </div>
  </div>
  {LEGAL_FOOTER}
  {build_actionbar()}
</div>
"""
    (root / "agent" / "index.html").write_text(
        wrap_page(f"{SITE_TITLE}｜聯絡", body, desc="台中房產買賣諮詢、委託、看屋安排", og_img=DEFAULT_HERO, og_url=page_url),
        encoding="utf-8"
    )

def build_life_posts(root: Path, urls: list):
    (root / "life").mkdir(parents=True, exist_ok=True)
    life_index_url = url_join(BASE_URL, "/life/")
    urls.append(life_index_url)

    posts = []
    if POSTS_DIR.exists() and POSTS_DIR.is_dir():
        for md_file in sorted(POSTS_DIR.glob("*.md")):
            md = md_file.read_text(encoding="utf-8", errors="ignore")
            title = md_file.stem
            first_line = (md.strip().split("\n", 1)[0] if md.strip() else "")
            if first_line.startswith("#"):
                t = first_line.lstrip("#").strip()
                if t:
                    title = t
            slug = safe_dirname(md_file.stem)
            post_url = url_join(BASE_URL, f"/life/{slug}/")
            urls.append(post_url)

            body_html = minimal_markdown_to_html(md)
            body = f"""
<div class="container">
  {build_nav("life")}
  <div class="postBody">
    {body_html}
    <div style="margin-top:24px">
      <a class="btnExt" href="/">🏠 回到物件列表</a>
      <a class="btnExt" href="/agent/">☎️ 聯絡 {esc(MY_NAME)}</a>
    </div>
  </div>
  {LEGAL_FOOTER}
  {build_actionbar()}
</div>
"""
            (root / "life" / slug).mkdir(parents=True, exist_ok=True)
            (root / "life" / slug / "index.html").write_text(
                wrap_page(f"{SITE_TITLE}｜{title}", body, desc=title, og_img=DEFAULT_HERO, og_url=post_url),
                encoding="utf-8"
            )
            posts.append({"title": title, "url": f"/life/{slug}/"})

    links = ""
    if posts:
        links = "<div class='section'><h2>文章列表</h2><div class='badges'>" + "".join(
            [f"<a class='badge' href='{p['url']}'>{esc(p['title'])}</a>" for p in posts]
        ) + "</div></div>"
    else:
        links = "<div class='section'><h2>文章列表</h2><div style='color:#94a3b8;'>尚未新增文章（把 .md 放到 posts/）</div></div>"

    body = f"""
<div class="container">
  {build_nav("life")}
  <div class="section">
    <h2>📝 區域文章 / 買屋指南</h2>
    <div style="color:#475569;line-height:2.0;font-size:16px;">
      放生活圈介紹、學區/交通/機能整理，讓搜尋更容易找到你，也讓客戶更快理解區域價值。
    </div>
  </div>
  {links}
  {LEGAL_FOOTER}
  {build_actionbar()}
</div>
"""
    (root / "life" / "index.html").write_text(
        wrap_page(f"{SITE_TITLE}｜文章", body, desc="台中生活圈文章與買屋指南", og_img=DEFAULT_HERO, og_url=life_index_url),
        encoding="utf-8"
    )

def build_indexes_and_groups(root: Path, all_items: list, groups: dict, urls: list, map_data: list):
    # Home
    home_url = url_join(BASE_URL, "/")
    urls.append(home_url)

    # filters
    regions = sorted({x["area"] for x in all_items})
    types = sorted({x["type"] for x in all_items})

    reg_btns = "".join([f"<button class='tag f-reg' data-val='{esc(r)}' onclick='setTag(this, \"f-reg\")'>{esc(r)}</button>" for r in regions])
    type_btns = "".join([f"<button class='tag f-type' data-val='{esc(t)}' onclick='setTag(this, \"f-type\")'>{esc(t)}</button>" for t in types])

    featured = [x for x in all_items if x.get("featured")]

    # Inject map data into page
    map_data_js = f"<script>window.__MAP_DATA__ = {json.dumps(map_data, ensure_ascii=False)};</script>"

    body = f"""
<div class="container">
  <div class="hero">
    <div class="hero-content">
      <h1>{esc(SITE_TITLE)}</h1>
      <p>{esc(SITE_SLOGAN)}</p>
    </div>
  </div>

  {build_nav("home")}

  <div class="mapWrap">
    <div id="map"></div>
  </div>

  {map_data_js}

  <div class="filter-section">
    <div class="filter-group">
      <button class="tag f-reg active" data-val="all" onclick="setTag(this, 'f-reg')">全部區域</button>
      {reg_btns}
    </div>
    <div class="filter-group">
      <button class="tag f-type active" data-val="all" onclick="setTag(this, 'f-type')">所有用途</button>
      {type_btns}
    </div>
    <div class="filter-group">
      <button class="tag f-sort active" data-val="none" onclick="setTag(this, 'f-sort')">預設排序</button>
      <button class="tag f-sort" data-val="high" onclick="setTag(this, 'f-sort')">價格：高→低</button>
      <button class="tag f-sort" data-val="low" onclick="setTag(this, 'f-sort')">價格：低→高</button>
    </div>
  </div>

  <div class="section">
    <h2>⭐ 精選物件</h2>
  </div>
  {''.join(card_html(x) for x in (featured[:6] if featured else all_items[:6]))}

  <div class="section">
    <h2>最新物件</h2>
  </div>
  <div id="list">
    {''.join(card_html(x) for x in all_items)}
  </div>

  {LEGAL_FOOTER}
  {build_actionbar()}
</div>
"""
    (root / "index.html").write_text(
        wrap_page(SITE_TITLE, body, desc=SITE_SLOGAN, og_img=DEFAULT_HERO, og_url=home_url, is_home=True),
        encoding="utf-8"
    )

    # status/精選物件
    (root / "status" / safe_dirname("精選物件")).mkdir(parents=True, exist_ok=True)
    status_url = url_join(BASE_URL, "/status/精選物件/")
    urls.append(status_url)
    body = f"""
<div class="container">
  {build_nav("status")}
  <div class="section">
    <h2>⭐ 精選物件</h2>
    <div style="color:#475569;line-height:2.0;font-size:16px;">
      條件漂亮、地段有優勢、詢問度高的物件整理在這裡。
    </div>
  </div>
  {''.join(card_html(x) for x in featured)}
  {LEGAL_FOOTER}
  {build_actionbar()}
</div>
"""
    (root / "status" / safe_dirname("精選物件") / "index.html").write_text(
        wrap_page(f"{SITE_TITLE}｜精選物件", body, desc="台中精選房產物件清單", og_img=DEFAULT_HERO, og_url=status_url),
        encoding="utf-8"
    )

    # index pages for state/feature/price
    for key, active, title, intro in [
        ("state", "state", "生活圈入口", "用生活圈找房：通勤、機能、學區一次對焦。"),
        ("feature", "feature", "特色入口", "用特色找房：學區、捷運、屋齡、電梯、車位等。"),
        ("price", "price", "價格帶入口", "用預算找房：先鎖定價格帶，再看條件。"),
    ]:
        (root / key).mkdir(parents=True, exist_ok=True)
        page_url = url_join(BASE_URL, f"/{key}/")
        urls.append(page_url)
        tags = sorted(groups.get(key, {}).keys())
        tag_links = "".join([f"<a class='badge' href='/{key}/{safe_dirname(t)}/'>{esc(t)}</a>" for t in tags])
        body = f"""
<div class="container">
  {build_nav(active)}
  <div class="section">
    <h2>{esc(title)}</h2>
    <div style="color:#475569;line-height:2.0;font-size:16px;">{esc(intro)}</div>
  </div>
  <div class="section">
    <h2>分類</h2>
    <div class="badges">{tag_links if tag_links else "<div style='color:#94a3b8;'>尚未設定</div>"}</div>
  </div>
  {LEGAL_FOOTER}
  {build_actionbar()}
</div>
"""
        (root / key / "index.html").write_text(
            wrap_page(f"{SITE_TITLE}｜{title}", body, desc=title, og_img=DEFAULT_HERO, og_url=page_url),
            encoding="utf-8"
        )

    # tag pages
    for key, active, title_prefix in [
        ("state", "state", "生活圈"),
        ("feature", "feature", "特色"),
        ("price", "price", "價格帶"),
    ]:
        for tag, items in groups.get(key, {}).items():
            dn = safe_dirname(tag)
            (root / key / dn).mkdir(parents=True, exist_ok=True)
            page_url = url_join(BASE_URL, f"/{key}/{dn}/")
            urls.append(page_url)

            intro = f"「{tag}」相關物件整理。"
            body = f"""
<div class="container">
  {build_nav(active)}
  <div class="section">
    <h2>{esc(title_prefix)}｜{esc(tag)}</h2>
    <div style="color:#475569;line-height:2.0;font-size:16px;">{esc(intro)}</div>
  </div>
  {''.join(card_html(x) for x in items)}
  {LEGAL_FOOTER}
  {build_actionbar()}
</div>
"""
            (root / key / dn / "index.html").write_text(
                wrap_page(f"{SITE_TITLE}｜{title_prefix}｜{tag}", body, desc=intro, og_img=DEFAULT_HERO, og_url=page_url),
                encoding="utf-8"
            )

def build_property_pages(root: Path, urls: list, geocache: dict):
    res = requests.get(SHEET_CSV_URL)
    res.encoding = "utf-8-sig"
    reader = csv.DictReader(res.text.splitlines())

    all_items = []
    groups = {"state": {}, "feature": {}, "price": {}}
    map_data = []

    for i, row in enumerate(reader):
        d = {norm_text(k): norm_text(v) for k, v in row.items() if k}

        status = pick_field(d, ["狀態", "Status"], fallback="ON")
        if norm_text(status).upper() in ["OFF", "FALSE", "0", "NO"]:
            continue

        name = pick_field(d, ["案名", "物件名稱", "名稱", "標題", "Title"], fallback="")
        if not name:
            continue

        area = pick_field(d, ["區域", "行政區", "區", "Area"], fallback="台中")
        price = pick_field(d, ["價格", "總價", "售價", "Price"], fallback="面議")
        addr = pick_field(d, ["地址", "地點", "Address"], fallback="")
        prop_type = pick_field(d, ["用途", "類型", "型態", "Type"], fallback="住宅")
        desc = pick_field(d, ["描述", "簡介", "說明", "內容", "Description"], fallback="")
        img = pick_field(d, ["圖片網址", "圖片", "照片", "Image"], fallback="")
        img_url = normalize_img(img)

        featured_flag = pick_field(d, ["精選", "Featured", "主打"], fallback="")
        featured = is_truthy(featured_flag) or ("精選" in desc)

        state_tags = split_tags(pick_field(d, ["生活圈", "商圈", "生活圈/商圈", "State"], fallback=""))
        feature_tags = split_tags(pick_field(d, ["特色", "標籤", "Feature"], fallback=""))

        price_wan = parse_price_number(price)
        price_bucket = pick_field(d, ["價格帶", "預算", "Budget"], fallback="") or auto_price_bucket(price_wan)

        ext_link = first_http_link(d)

        slug = f"p{i}"
        (root / slug).mkdir(parents=True, exist_ok=True)
        page_path = f"/{slug}/"
        page_url = url_join(BASE_URL, page_path)
        urls.append(page_url)

        # Build map address (address-only is allowed)
        map_query = addr if addr else f"台中市 {area} {name}"
        geo = geocode_address(map_query, geocache)  # cache + api
        if geo and isinstance(geo, dict) and "lat" in geo and "lng" in geo:
            map_data.append({
                "name": name,
                "price": price,
                "img": img_url,
                "url": page_path,
                "address": map_query,
                "lat": float(geo["lat"]),
                "lng": float(geo["lng"]),
                "region": area,
                "type": prop_type
            })

        # Listing JSON-LD
        listing_ld = jsonld_listing(name, desc, img_url, page_url, addr, price_wan, prop_type, area)

        # Detail page
        ext_btn = f"<a class='btnExt' href='{esc(ext_link)}' target='_blank'>🌐 前往 591 / 樂屋 查看原始物件</a>" if ext_link else ""
        map_url = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(map_query)}"

        # internal tag badges
        tag_badges = []
        for t in state_tags[:6]:
            tag_badges.append(f"<a class='badge' href='/state/{safe_dirname(t)}/'>📍 {esc(t)}</a>")
        for t in feature_tags[:6]:
            tag_badges.append(f"<a class='badge' href='/feature/{safe_dirname(t)}/'>✨ {esc(t)}</a>")
        tag_badges.append(f"<a class='badge' href='/price/{safe_dirname(price_bucket)}/'>💰 {esc(price_bucket)}</a>")

        badge_html = f"<div class='section'><h2>快速入口</h2><div class='badges'>{''.join(tag_badges)}</div></div>"

        detail_body = f"""
<div class="container">
  {build_nav("home")}
  <div class="detailHero"><img src="{esc(img_url)}" alt="{esc(name)}"></div>
  <div class="detailBox">
    <h1>{esc(name)}</h1>
    <div class="meta" style="margin-top:10px">{esc(area)} · {esc(prop_type)}</div>
    <div class="price">{esc(price)}</div>

    {badge_html}

    <div class="desc">{esc(desc).replace("、", "<br>• ")}</div>

    {ext_btn}
    <a class="btnMap" href="{esc(map_url)}" target="_blank">📍 地圖導航</a>

    <div class="btnRow">
      <a class="btn btnCall" href="tel:{MY_PHONE}">📞 直接致電</a>
      <a class="btn btnLine" href="{MY_LINE_URL}" target="_blank">💬 LINE 諮詢</a>
    </div>

    {LEGAL_FOOTER}
  </div>

  {build_actionbar()}
</div>
"""
        (root / slug / "index.html").write_text(
            wrap_page(
                f"{SITE_TITLE}｜{name}",
                detail_body,
                desc=desc or f"{area} {prop_type} {price}",
                og_img=img_url,
                og_url=page_url,
                extra_jsonld=[listing_ld],
            ),
            encoding="utf-8"
        )

        price_num = parse_price_number(price) or 0
        item = {
            "name": name,
            "area": area,
            "type": prop_type,
            "price": price,
            "price_num": price_num,
            "price_bucket": price_bucket,
            "img": img_url,
            "url": page_path,
            "featured": featured,
            "state_tags": state_tags,
            "feature_tags": feature_tags,
        }
        all_items.append(item)

        # Group collect
        for t in state_tags:
            groups["state"].setdefault(t, []).append(item)
        for t in feature_tags:
            groups["feature"].setdefault(t, []).append(item)
        groups["price"].setdefault(price_bucket, []).append(item)

    # newest first
    all_items.reverse()
    for k in groups:
        for tag in groups[k]:
            groups[k][tag] = list(reversed(groups[k][tag]))

    return all_items, groups, map_data

def build():
    root = Path(".")
    clean_output(root)

    urls = []
    geocache = load_geocache()

    all_items, groups, map_data = build_property_pages(root, urls, geocache)

    # save cache
    save_geocache(geocache)

    build_indexes_and_groups(root, all_items, groups, urls, map_data)
    build_life_posts(root, urls)
    build_agent_page(root, urls)
    build_sitemap(root, urls)

    print("✅ build.py 完成：保留地圖＋篩選＋分類入口＋文章＋agent＋JSON-LD＋sitemap")

if __name__ == "__main__":
    build()
