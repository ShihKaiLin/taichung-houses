# build.py
# =========================================================
# 平台外搜尋截流器 FINAL+++（旗艦視覺 + 房產 JSON-LD + 關鍵字入口短文 + hashtag 站內連結 + 自動推 GitHub）
# =========================================================
# ✅ 多物件：listings/*.txt
# ✅ 下架：*.OFF.txt 自動跳過
# ✅ 每物件「旗艦卡片頁」（漸層 + 卡片陰影 + CTA）
# ✅ 房產專用 JSON-LD（RealEstateListing / Residence）
# ✅ 首頁清單 + 區域分類頁 + 關鍵字入口頁
# ✅ 關鍵字入口頁：自動生成「短文段落」（避免薄內容）
# ✅ 物件頁：hashtag + 站內連結（點一下到 /k/）
# ✅ sitemap.xml / robots.txt / canonical / 內部連結
# ✅ 自動 Deploy 到 GitHub（AUTO_DEPLOY=1 才會推）
#
# -------------------------
# listings/ 建議標籤（可只貼原始文字，也可加標籤更準）
# 【案名】宏台美術館
# 【區域】台中市西區
# 【地址】台中市西區五權三街
# 【價格】2188萬
# 【格局】3房2廳2衛
# 【坪數】47.36坪
# 【車位】B1平車
# 【連結】https://...
# 【圖片】https://...jpg   (可選)
# 【關鍵字】宏台美術館, 國美特區, 五權三街, 西區三房平車
# 【描述】（可選，自訂 1~3 句，會放在卡片描述區）
# (下方可貼原始分享文字)
#
# ✅ 本機圖片（可選）：與 txt 同名放在 listings/
#   listings/macrotai.txt 對應 listings/macrotai.jpg / .png / .webp
# =========================================================

import os, re, html, shutil, unicodedata, subprocess, json
from pathlib import Path
from datetime import datetime, timezone

# =======================
# 導流資訊（固定顯示）
# =======================
CONTACT_NAME = os.getenv("CONTACT_NAME", "林世塏").strip()
CONTACT_PHONE = os.getenv("CONTACT_PHONE", "0938-615-351").strip()
CONTACT_LINE = os.getenv("CONTACT_LINE", "https://line.me/ti/p/FDsMyAYDv").strip()

SITE_TITLE = os.getenv("SITE_TITLE", "台中房產條件整理（找房比較頁）").strip()

# GitHub Pages 上線後建議填（影響 canonical + sitemap 絕對網址）
# 例：https://yourname.github.io/house-info
BASE_URL = os.getenv("BASE_URL", "").strip().rstrip("/")

# =======================
# 自動部署到 GitHub（可選）
# =======================
AUTO_DEPLOY = os.getenv("AUTO_DEPLOY", "0").strip() == "1"
GITHUB_REPO_URL = os.getenv("GITHUB_REPO_URL", "").strip()      # https://github.com/you/repo.git
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "").strip()            # PAT（環境變數）
GIT_BRANCH = os.getenv("GIT_BRANCH", "main").strip()

# =======================
# 關鍵字入口控制（避免灌水）
# =======================
MAX_KEY_PAGES_PER_LISTING = int(os.getenv("MAX_KEY_PAGES_PER_LISTING", "5"))
MAX_LISTINGS_PER_KEYWORD_PAGE = int(os.getenv("MAX_LISTINGS_PER_KEYWORD_PAGE", "20"))
KEYWORD_INTRO_SENTENCES = int(os.getenv("KEYWORD_INTRO_SENTENCES", "4"))  # 入口短文句數 3~6 建議

# 物件頁 hashtag 連結數量（避免太多）
MAX_HASHTAGS = int(os.getenv("MAX_HASHTAGS", "10"))

# =======================
# 目錄
# =======================
SRC = Path("listings")
OUT = Path("site")
IMG_OUT = OUT / "imgs"

BLACK = ["just a moment", "attention required", "cloudflare", "captcha", "access denied", "checking your browser"]

# -----------------------
# util
# -----------------------
def esc(s):
    return html.escape(str(s or ""))

def norm(s: str) -> str:
    s = (s or "").replace("臺中市", "台中市")
    s = re.sub(r"\s+", " ", s).strip()
    return s

def pick_tag(raw: str, key: str) -> str:
    m = re.search(rf"^\s*【{re.escape(key)}】\s*(.+?)\s*$", raw, flags=re.M)
    return norm(m.group(1)) if m else ""

def slugify(s: str) -> str:
    s = norm(s)
    s = unicodedata.normalize("NFKD", s)
    s = re.sub(r"[^\w\u4e00-\u9fff]+", "-", s)
    s = re.sub(r"-{2,}", "-", s).strip("-")
    return s[:70] if s else "item"

def now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")

def canonical(url_path: str) -> str:
    if not BASE_URL:
        return ""
    return f"{BASE_URL}/{url_path.lstrip('/')}"

def write(p: Path, s: str):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(s, encoding="utf-8")

def strip_tag_lines(raw: str) -> str:
    lines = [l.rstrip() for l in raw.splitlines() if l.strip()]
    lines = [l for l in lines if not re.match(r"^\s*【[^】]+】", l)]
    return "\n".join(lines[:180])

def safe_int(s: str):
    try:
        return int(str(s).replace(",", "").strip())
    except Exception:
        return None

# -----------------------
# extract
# -----------------------
def extract_area(raw: str) -> str:
    v = pick_tag(raw, "區域")
    if v:
        return v
    m = re.search(r"(台中市|臺中市)\s*([^\s，,]{1,4}區)", raw)
    if m:
        return f"台中市{m.group(2)}"
    return "台中市"

def extract_name(raw: str) -> str:
    v = pick_tag(raw, "案名")
    if v and not any(b in v.lower() for b in BLACK):
        return v
    m = re.search(r"【([^】]{1,30})】", raw)
    if m:
        n = norm(m.group(1))
        if not any(b in n.lower() for b in BLACK):
            return n
    return "住宅物件"

def extract_price(raw: str) -> str:
    v = pick_tag(raw, "價格")
    if v:
        m = re.search(r"(\d{1,3}(?:,\d{3})*|\d+)", v)
        return m.group(1) if m else v
    m = re.search(r"(\d{1,3}(?:,\d{3})*)\s*萬", raw)
    return m.group(1) if m else ""

def extract_layout(raw: str) -> str:
    v = pick_tag(raw, "格局")
    if v:
        return v
    m = re.search(r"(\d)\s*房\s*(\d)\s*廳\s*(\d)\s*衛", raw)
    if m:
        return f"{m.group(1)}房{m.group(2)}廳{m.group(3)}衛"
    m2 = re.search(r"(\d房\d廳\d衛)", raw)
    return m2.group(1) if m2 else ""

def extract_size(raw: str) -> str:
    v = pick_tag(raw, "坪數")
    if v:
        m = re.search(r"([\d\.]+)", v)
        return m.group(1) if m else v
    m = re.search(r"([\d\.]+)\s*坪", raw)
    return m.group(1) if m else ""

def extract_parking(raw: str) -> str:
    v = pick_tag(raw, "車位")
    if v:
        return v
    if any(x in raw for x in ["平車", "坡道平面", "B1平車"]):
        return "平車"
    if "車位" in raw:
        return "車位"
    return ""

def extract_address(raw: str) -> str:
    v = pick_tag(raw, "地址")
    if v:
        return v
    m = re.search(r"(台中市|臺中市)[^，,\n]{0,70}", raw)
    return norm(m.group(0)) if m else ""

def extract_link(raw: str) -> str:
    v = pick_tag(raw, "連結")
    if v.startswith("http"):
        return v
    m = re.search(r"(https?://[^\s]+)", raw)
    return m.group(1) if m else ""

def extract_img_url(raw: str) -> str:
    v = pick_tag(raw, "圖片")
    if v.startswith("http"):
        return v
    return ""

def extract_road_fragment(address: str):
    if not address:
        return ""
    m = re.search(r"([^\s，,]{1,12}(路|街|大道|巷))", address)
    return m.group(1) if m else ""

def extract_keywords(raw: str, area: str, name: str, address: str, layout: str, parking: str):
    tagged = pick_tag(raw, "關鍵字")
    keys = []
    if tagged:
        for part in re.split(r"[，,;；|/]+", tagged):
            p = norm(part)
            if p and p not in keys:
                keys.append(p)

    road = extract_road_fragment(address)

    auto = []
    if name:
        auto += [name, f"{name} 房價", f"{name} 實價", f"{name} 行情", f"{name} 格局", f"{name} 平車"]
    if area:
        auto += [area, f"{area} 買房", f"{area} 房價"]
    if road:
        auto += [road, f"{road} 房價", f"{road} 買房"]
    if layout:
        auto += [f"{area} {layout}", f"{layout} 平車" if parking else layout]
    if parking:
        auto += [f"{area} 平車", f"{area} {layout} 平車" if layout else f"{area} 平車"]

    for a in auto:
        a = norm(a)
        if a and a not in keys:
            keys.append(a)

    # 控制數量
    return keys[:MAX_KEY_PAGES_PER_LISTING]

# -----------------------
# visuals / seo
# -----------------------
def best_placeholder():
    return "https://placehold.co/600x400?text=%E5%9C%96%E7%89%87%E8%BC%89%E5%85%A5%E4%B8%AD...%E8%AB%8B%E6%AA%A2%E6%9F%A5%E9%80%A3%E7%B5%90"

def build_seo_title(meta):
    parts = []
    if meta["area"]: parts.append(meta["area"])
    if meta["name"]: parts.append(meta["name"])
    if meta["layout"]: parts.append(meta["layout"])
    if meta["parking"]: parts.append(meta["parking"])
    if meta["price"]: parts.append(f"{meta['price']}萬")
    road = extract_road_fragment(meta.get("address",""))
    if road: parts.append(road)
    return "｜".join(parts) + "｜條件整理"

def build_seo_desc(meta, desc_text):
    bits = [meta.get("area",""), meta.get("name",""), meta.get("layout","")]
    if meta.get("size"): bits.append(f"{meta['size']}坪")
    if meta.get("parking"): bits.append(meta["parking"])
    if meta.get("price"): bits.append(f"約{meta['price']}萬")
    base = "、".join([b for b in bits if b])
    extra = norm(desc_text)[:95]
    return f"{base}｜{extra}" if extra else f"{base}｜提供找房者快速比較與補充資訊入口。"

def make_hashtags(meta, keywords):
    # 產生 hashtag + 站內連結（連到 /k/<slug>/）
    tags = []
    if meta.get("name"): tags.append(meta["name"])
    if meta.get("area"): tags.append(meta["area"])
    road = extract_road_fragment(meta.get("address",""))
    if road: tags.append(road)
    if meta.get("layout"): tags.append(meta["layout"])
    if meta.get("parking"): tags.append(meta["parking"])
    # 再補一點標籤關鍵字（少量）
    for k in keywords or []:
        k = norm(k)
        if k and k not in tags:
            tags.append(k)
    return tags[:MAX_HASHTAGS]

def keyword_link(tag: str):
    return f"../k/{slugify(tag)}/"

def render_hashtag_links(tags):
    chips = []
    for t in tags:
        chips.append(
            f"<a class='chip' href='{esc(keyword_link(t))}'>#{esc(t)}</a>"
        )
    return "".join(chips)

def property_jsonld(meta, img_url, page_url, description):
    # 房產專用 JSON-LD：RealEstateListing + itemOffered (Residence)
    # 注意：資料不足就不硬塞欄位，避免亂填
    price_num = safe_int(meta.get("price",""))
    size_num = None
    try:
        size_num = float(str(meta.get("size","")).replace(",", "").replace("坪","").strip()) if meta.get("size") else None
    except Exception:
        size_num = None

    road = extract_road_fragment(meta.get("address",""))

    data = {
        "@context": "https://schema.org",
        "@type": "RealEstateListing",
        "name": norm(meta.get("name","")) or "住宅物件",
        "url": page_url or "",
        "datePosted": datetime.now().strftime("%Y-%m-%d"),
        "description": norm(description or ""),
        "image": [img_url] if img_url else [],
        "provider": {
            "@type": "RealEstateAgent",
            "name": CONTACT_NAME,
            "telephone": CONTACT_PHONE,
            "url": CONTACT_LINE
        },
        "itemOffered": {
            "@type": "Residence",
            "name": norm(meta.get("name","")) or "住宅物件",
        }
    }

    # address（用 PostalAddress）
    if meta.get("address") or meta.get("area") or road:
        addr = {"@type": "PostalAddress"}
        if meta.get("address"):
            addr["streetAddress"] = meta["address"]
        # 台灣：用 addressLocality/addressRegion 做基本分層
        # area 格式多半是 台中市西區
        if meta.get("area","").startswith("台中市"):
            addr["addressRegion"] = "台中市"
            addr["addressLocality"] = meta.get("area").replace("台中市","").strip() or "台中市"
        else:
            addr["addressRegion"] = meta.get("area","") or "台中市"
        addr["addressCountry"] = "TW"
        data["itemOffered"]["address"] = addr

    # floorSize
    if size_num:
        data["itemOffered"]["floorSize"] = {
            "@type": "QuantitativeValue",
            "value": size_num,
            "unitCode": "MTK"  # 坪不是標準 unitCode，這裡用 MTK(平方公尺)會不準
        }
        # 不亂換算：為避免誤導，改用文字欄位補充
        data["itemOffered"]["floorSize"]["value"] = size_num
        data["itemOffered"]["floorSize"]["unitText"] = "坪"

    # numberOfRooms（從格局粗抓）
    lay = meta.get("layout","")
    m = re.search(r"(\d)\s*房", lay)
    if m:
        data["itemOffered"]["numberOfRooms"] = int(m.group(1))

    # offers
    if price_num:
        data["offers"] = {
            "@type": "Offer",
            "price": price_num * 10000,   # 萬 -> 元
            "priceCurrency": "TWD",
            "availability": "https://schema.org/InStock",
            "url": page_url or ""
        }

    # remove empty url if not known
    if not data["url"]:
        data.pop("url", None)
    if not data["provider"]["url"]:
        data["provider"].pop("url", None)

    return json.dumps(data, ensure_ascii=False)

# -----------------------
# HTML pages
# -----------------------
def flagship_listing_html(meta, desc, img_url, url_path, back_href, listing_tags):
    title = build_seo_title(meta)
    description = build_seo_desc(meta, desc)

    page_url = canonical(url_path) if BASE_URL else ""
    jsonld = property_jsonld(meta, img_url, page_url, description)

    price_show = f"{meta['price']} 萬" if meta.get("price") else "價格面議"
    feature_bits = []
    if meta.get("layout"): feature_bits.append(f"格局：{meta['layout']}")
    if meta.get("size"): feature_bits.append(f"坪數：約 {meta['size']} 坪")
    if meta.get("parking"): feature_bits.append(f"車位：{meta['parking']}")
    road = extract_road_fragment(meta.get("address",""))
    if road: feature_bits.append(f"路段：{road}")
    feature_line = "｜".join(feature_bits) if feature_bits else "—"

    source_line = ""
    if meta.get("link"):
        source_line = f"<p style='margin:12px 0 0;'><a href='{esc(meta['link'])}' target='_blank' rel='noopener'>👉 來源連結</a></p>"

    hashtag_html = render_hashtag_links(listing_tags)

    canonical_url = canonical(url_path)
    full_page = f"""<!doctype html><html lang="zh-Hant"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)[:155]}">
{f"<link rel='canonical' href='{esc(canonical_url)}'>" if canonical_url else ""}
<meta property="og:type" content="article">
<meta property="og:locale" content="zh_TW">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)[:155]}">
<script type="application/ld+json">{jsonld}</script>
<style>
body {{ font-family: 'PingFang TC', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Noto Sans TC", Arial, sans-serif; background: #fdfdfd; margin: 0; padding: 15px; }}
.container {{ max-width: 640px; margin: auto; }}
.card {{ background: #fff; border-radius: 25px; overflow: hidden; box-shadow: 0 20px 40px rgba(0,0,0,0.08); border: 1px solid #eee; }}
.img-box img {{ width: 100%; height: auto; display: block; }}
.content {{ padding: 26px; }}
.area-tag {{ display: inline-block; background: linear-gradient(135deg, #f2994a, #f2c94c); color: #fff; padding: 5px 16px; border-radius: 50px; font-size: 14px; font-weight: 800; }}
h1 {{ font-size: 24px; color: #333; margin: 14px 0 8px; line-height: 1.4; }}
.meta-line {{ color: #666; font-size: 14px; margin: 0 0 14px; line-height: 1.6; }}
.price-tag {{ color: #e63946; font-size: 32px; font-weight: 900; margin: 6px 0 8px; }}
.address {{ color: #777; font-size: 15px; margin: 0 0 18px; line-height: 1.6; }}
.features {{ background: #fff8f0; border-left: 5px solid #f2994a; padding: 15px; border-radius: 12px; font-size: 16px; color: #444; line-height: 1.7; }}
.small {{ font-size: 12px; color: #888; margin-top: 14px; }}
.btn-group {{ display: flex; gap: 15px; margin-top: 22px; }}
.btn {{ flex: 1; text-align: center; padding: 16px; border-radius: 50px; text-decoration: none; font-weight: 900; font-size: 17px; transition: transform 0.2s; }}
.btn:active {{ transform: scale(0.95); }}
.tel {{ background: #333; color: #fff; box-shadow: 0 10px 20px rgba(0,0,0,0.1); }}
.line {{ background: #06C755; color: #fff; box-shadow: 0 10px 20px rgba(6,199,85,0.2); }}
.topnav {{ margin: 6px 0 10px; }}
.topnav a {{ color:#444; text-decoration:none; font-weight:700; }}
hr.sep {{ border:0; border-top:1px solid #f0f0f0; margin:18px 0; }}
.note {{ background:#fafafa; border:1px solid #eee; border-radius:14px; padding:14px; white-space:pre-wrap; line-height:1.7; color:#333; }}
.chips {{ margin-top: 14px; display:flex; flex-wrap:wrap; gap:10px; }}
.chip {{ display:inline-block; padding:8px 12px; border-radius:999px; border:1px solid #eee; text-decoration:none; color:#333; font-weight:800; font-size:13px; background:#fff; box-shadow:0 8px 18px rgba(0,0,0,0.04); }}
.chip:hover {{ opacity:0.92; }}
</style>
</head><body>
<div class="container">
  <div class="topnav"><a href="{esc(back_href)}">← 回清單</a></div>
  <div class="card">
    <div class="img-box">
      <img src="{esc(img_url)}" onerror="this.src='{best_placeholder()}'" alt="{esc(meta.get('name',''))}">
    </div>
    <div class="content">
      <div class="area-tag">{esc(meta.get('area',''))}</div>
      <h1>{esc(meta.get('name',''))}</h1>
      <p class="meta-line">{esc(feature_line)}</p>
      <div class="price-tag">{esc(price_show)}</div>
      <p class="address">📍 {esc(meta.get('address','')) if meta.get('address') else "—"}</p>

      <div class="features">🏠 物件描述：<br>{esc(norm(desc) if desc else "—")}</div>
      {source_line}

      <div class="btn-group">
        <a href="tel:{esc(CONTACT_PHONE)}" class="btn tel">撥打電話</a>
        <a href="{esc(CONTACT_LINE)}" class="btn line" target="_blank" rel="noopener">LINE 諮詢</a>
      </div>

      <div class="chips">{hashtag_html}</div>

      <hr class="sep">
      <div class="note">{esc(strip_tag_lines(meta.get("_raw","")) if meta.get("_raw","") else "")}</div>

      <div class="small">
        聯絡人：{esc(CONTACT_NAME)}｜更新：{esc(datetime.now().strftime("%Y-%m-%d %H:%M"))}
      </div>
    </div>
  </div>
</div>
</body></html>"""
    return full_page

def list_page(title, subtitle, cards_html, back_href, url_path):
    canonical_url = canonical(url_path)
    return f"""<!doctype html><html lang="zh-Hant"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(subtitle)[:155]}">
{f"<link rel='canonical' href='{esc(canonical_url)}'>" if canonical_url else ""}
<style>
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Noto Sans TC",Arial;margin:0;background:#fafafa;color:#111}}
.wrap{{max-width:920px;margin:0 auto;padding:22px 16px 64px}}
a{{word-break:break-all;color:#222}}
h1{{font-size:22px;margin:0 0 8px}}
.sub{{opacity:.75;margin:0 0 14px;line-height:1.6}}
.card{{background:#fff;border:1px solid #eee;border-radius:16px;padding:14px 16px;margin:10px 0;box-shadow:0 10px 20px rgba(0,0,0,0.04)}}
.badge{{display:inline-block;background:linear-gradient(135deg,#f2994a,#f2c94c);color:#fff;padding:4px 12px;border-radius:999px;font-weight:800;font-size:12px}}
.small{{font-size:12px;color:#777;margin-top:18px}}
</style></head><body>
<div class="wrap">
  {f"<p><a href='{esc(back_href)}'>← 回清單</a></p>" if back_href else ""}
  <span class="badge">整理頁</span>
  <h1>{esc(title)}</h1>
  <p class="sub">{esc(subtitle)}</p>
  {cards_html}
  <div class="small">聯絡：{esc(CONTACT_NAME)}｜{esc(CONTACT_PHONE)}｜<a href="{esc(CONTACT_LINE)}" target="_blank" rel="noopener">LINE</a></div>
</div>
</body></html>"""

def keyword_intro(keyword, area_hint="", count=0):
    # 關鍵字入口短文（3~6 句），避免薄內容
    kw = norm(keyword)
    bits = []
    bits.append(f"你正在搜尋「{kw}」相關資訊，通常代表你已經在比價或鎖定特定社區/路段。")
    if area_hint:
        bits.append(f"這裡先用「{area_hint}」作為範圍整理，讓你快速對照條件與價位帶。")
    if count:
        bits.append(f"目前整理到 {count} 筆相關條件頁，你可以先點進去看格局、車位、坪數與大致價格。")
    bits.append("如果你是屋主，也能用同樣關鍵字看到這頁，快速確認市場行情與同類型釋出狀況。")
    bits.append("想確認細節或補充條件（例如樓層/採光/管理費/車位型式），可直接用下方方式聯絡。")
    # 控制句數
    return " ".join(bits[:max(3, min(KEYWORD_INTRO_SENTENCES, 6))])

# -----------------------
# Image resolution
# -----------------------
def resolve_image_for_listing(txt_path: Path, raw: str):
    url = extract_img_url(raw)
    if url:
        return url
    for ext in [".jpg", ".jpeg", ".png", ".webp"]:
        p = txt_path.with_suffix(ext)
        if p.exists():
            IMG_OUT.mkdir(parents=True, exist_ok=True)
            dst = IMG_OUT / p.name
            shutil.copy2(p, dst)
            return f"../imgs/{p.name}"
    return best_placeholder()

# -----------------------
# Build
# -----------------------
def build_site():
    if not SRC.exists():
        SRC.mkdir(parents=True, exist_ok=True)
        print("⚠️ 已建立 listings/，請放入 .txt 後再執行")
        return False

    files = sorted([p for p in SRC.iterdir() if p.suffix.lower()==".txt" and not p.name.endswith(".OFF.txt")])
    if not files:
        print("⚠️ listings/ 沒有可用 .txt（*.OFF.txt 會被跳過）")
        return False

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True, exist_ok=True)
    IMG_OUT.mkdir(parents=True, exist_ok=True)

    all_cards = []
    area_map = {}
    keyword_map = {}  # keyword -> list(target)
    keyword_area_hint = {}  # keyword -> area (first seen)
    sitemap_locs = []

    # 保存每物件的 hashtag tags（用於頁面）
    listing_tags_map = {}

    for fp in files:
        raw = fp.read_text(encoding="utf-8", errors="ignore").strip()
        if not raw:
            continue

        meta = {
            "area": extract_area(raw),
            "name": extract_name(raw),
            "address": extract_address(raw),
            "price": extract_price(raw),
            "layout": extract_layout(raw),
            "size": extract_size(raw),
            "parking": extract_parking(raw),
            "link": extract_link(raw),
            "_raw": raw,
        }

        # 描述：優先【描述】，否則抓原始前段
        desc = pick_tag(raw, "描述")
        if not desc:
            desc = norm(strip_tag_lines(raw)[:260])

        slug = slugify(f"{meta['area']}-{meta['name']}-{meta['layout']}-{meta['price']}")
        listing_dir = OUT / slug
        listing_dir.mkdir(parents=True, exist_ok=True)

        img_url = resolve_image_for_listing(fp, raw)
        url_path = f"{slug}/"

        # keywords
        keys = extract_keywords(raw, meta["area"], meta["name"], meta["address"], meta["layout"], meta["parking"])
        tags = make_hashtags(meta, keys)
        listing_tags_map[slug] = tags

        listing_html = flagship_listing_html(meta, desc, img_url, url_path, "../index.html", tags)
        write(listing_dir / "index.html", listing_html)

        # cards for lists
        title = f"{meta['area']}｜{meta['name']}{('｜'+meta['layout']) if meta['layout'] else ''}"
        meta_line = " ".join([x for x in [
            meta["layout"],
            (meta["size"]+"坪") if meta["size"] else "",
            meta["parking"],
            (meta["price"]+"萬") if meta["price"] else ""
        ] if x])

        all_cards.append(f"<div class='card'><a href='./{esc(slug)}/'><b>{esc(title)}</b></a><div class='sub'>{esc(meta_line)}</div></div>")

        area_map.setdefault(meta["area"], []).append({
            "href": f"../../{slug}/",
            "title": f"{meta['name']}{('｜'+meta['layout']) if meta['layout'] else ''}",
            "meta": meta_line
        })

        sitemap_locs.append(canonical(f"{slug}/") if BASE_URL else f"{slug}/index.html")

        for k in keys:
            keyword_map.setdefault(k, []).append({
                "href": f"../{slug}/",
                "title": title,
                "meta": meta_line
            })
            if k not in keyword_area_hint:
                keyword_area_hint[k] = meta["area"]

    # home
    home_html = list_page(SITE_TITLE, "本清單為條件整理/比較用，提供找房者快速瀏覽。", "".join(all_cards), None, "/")
    write(OUT / "index.html", home_html)
    sitemap_locs.insert(0, canonical("/") if BASE_URL else "index.html")

    # area pages
    for area_name, items in area_map.items():
        area_slug = slugify(area_name)
        cards = []
        for it in items:
            cards.append(f"<div class='card'><a href='{esc(it['href'])}'><b>{esc(it['title'])}</b></a><div class='sub'>{esc(it['meta'])}</div></div>")
        area_html = list_page(f"{area_name}｜物件整理", f"{area_name} 物件條件整理與比較清單。", "".join(cards), "../../index.html", f"area/{area_slug}/")
        write(OUT / "area" / area_slug / "index.html", area_html)
        sitemap_locs.append(canonical(f"area/{area_slug}/") if BASE_URL else f"area/{area_slug}/index.html")

    # keyword pages
    kroot = OUT / "k"
    kroot.mkdir(parents=True, exist_ok=True)
    for kw, targets in keyword_map.items():
        # 去重
        seen = set()
        uniq = []
        for t in targets:
            if t["href"] not in seen:
                seen.add(t["href"])
                uniq.append(t)

        kw_slug = slugify(kw)
        cards = []
        for t in uniq[:MAX_LISTINGS_PER_KEYWORD_PAGE]:
            cards.append(f"<div class='card'><a href='{esc(t['href'])}'><b>{esc(t['title'])}</b></a><div class='sub'>{esc(t['meta'])}</div></div>")

        intro = keyword_intro(kw, keyword_area_hint.get(kw,""), count=len(uniq))
        kw_html = list_page(f"{kw}｜整理與比較", intro, "".join(cards), "../index.html", f"k/{kw_slug}/")
        write(kroot / kw_slug / "index.html", kw_html)
        sitemap_locs.append(canonical(f"k/{kw_slug}/") if BASE_URL else f"k/{kw_slug}/index.html")

    # robots
    robots = "User-agent: *\nAllow: /\n"
    if BASE_URL:
        robots += f"Sitemap: {BASE_URL}/sitemap.xml\n"
    write(OUT / "robots.txt", robots)

    # sitemap
    lastmod = now_iso()
    sm = ["<?xml version='1.0' encoding='UTF-8'?>",
          "<urlset xmlns='http://www.sitemaps.org/schemas/sitemap/0.9'>"]
    for loc in sitemap_locs:
        loc2 = loc if isinstance(loc, str) else str(loc)
        sm += [
            "<url>",
            f"<loc>{html.escape(loc2)}</loc>",
            f"<lastmod>{html.escape(lastmod)}</lastmod>",
            "<changefreq>weekly</changefreq>",
            "<priority>0.6</priority>",
            "</url>"
        ]
    sm.append("</urlset>")
    write(OUT / "sitemap.xml", "\n".join(sm))

    print("✅ build 完成：site/（含房產 JSON-LD + 入口短文 + hashtag 連結）")
    return True

# -----------------------
# Deploy (git push)
# -----------------------
def run(cmd, cwd=None):
    subprocess.run(cmd, cwd=cwd, shell=True, check=True)

def deploy_to_github():
    if not AUTO_DEPLOY:
        print("ℹ️ AUTO_DEPLOY=0，略過自動部署")
        return

    if not GITHUB_REPO_URL:
        raise SystemExit("❌ 缺少環境變數 GITHUB_REPO_URL（例如：https://github.com/you/house-info.git）")
    if not GITHUB_TOKEN:
        raise SystemExit("❌ 缺少環境變數 GITHUB_TOKEN（GitHub PAT）")

    if not shutil.which("git"):
        raise SystemExit("❌ 找不到 git，請先安裝 Git for Windows")

    if not (OUT / ".git").exists():
        run("git init", cwd=str(OUT))
        run(f"git checkout -b {GIT_BRANCH}", cwd=str(OUT))

    if not GITHUB_REPO_URL.startswith("https://"):
        raise SystemExit("❌ GITHUB_REPO_URL 請用 https://... 形式")
    push_url = GITHUB_REPO_URL.replace("https://", f"https://x-access-token:{GITHUB_TOKEN}@")

    try:
        run("git remote remove origin", cwd=str(OUT))
    except Exception:
        pass
    run(f"git remote add origin {push_url}", cwd=str(OUT))

    run("git add -A", cwd=str(OUT))
    msg = f"deploy: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    try:
        run(f'git commit -m "{msg}"', cwd=str(OUT))
    except Exception:
        pass

    run(f"git push -u origin {GIT_BRANCH} --force", cwd=str(OUT))
    print("✅ 已自動推送到 GitHub（site/）")

def main():
    ok = build_site()
    if not ok:
        return
    deploy_to_github()

if __name__ == "__main__":
    main()
