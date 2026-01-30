import os, csv, requests, html, shutil, re, urllib.parse
from pathlib import Path
from datetime import datetime

# --- 1. 核心配置 ---
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQShAl0-TbUU0MQdYVe53im2T6lXQgh_7g-bdL6HHpIBFtA2yfIAMbPw4J9RgZUkROb9AAiMhnRC0kH/pub?output=csv"
MY_PHONE = "0938-615-351"
MY_LINE_URL = "https://line.me/ti/p/FDsMyAYDv"
SITE_TITLE = "林世塏｜台中精選房產"
SLOGAN = "石開林｜為您挑選最理想的家"
BASE_URL = "https://shihkailin.github.io/taichung-houses"
GA4_ID = "G-B7WP9BTP8X" # 您的 GA4 ID

def esc(s): return html.escape(str(s or "").strip())

def get_final_img_url(url):
    """【解析照片】支援 GitHub images/ 與 Google Drive"""
    url = str(url).strip()
    if not url: return "https://placehold.co/600x400?text=無圖片"
    if not url.startswith("http"):
        clean = url.lstrip("/")
        if not clean.startswith("images/"): clean = f"images/{clean}"
        return f"https://raw.githubusercontent.com/ShihKaiLin/taichung-houses/main/{clean}"
    return url

def get_head(title, ga_id):
    """【整合 SEO 與 GA4】埋入追蹤碼"""
    ga = f"""<script async src="https://www.googletagmanager.com/gtag/js?id={ga_id}"></script><script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','{ga_id}');</script>""" if ga_id else ""
    return f"""
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=0">
        <title>{esc(title)}</title>
        {ga}
        <style>
            :root {{ --primary: #b08d57; --dark: #1a1a1a; --light: #f8f9fa; --danger: #e63946; }}
            body {{ font-family: 'PingFang TC', sans-serif; background: var(--light); margin: 0; color: var(--dark); line-height: 1.6; }}
            .container {{ max-width: 500px; margin: auto; background: #fff; min-height: 100vh; padding-bottom: 120px; box-shadow: 0 0 30px rgba(0,0,0,0.05); position: relative; }}
            .header {{ padding: 60px 25px 30px; background: #fff; text-align: center; border-bottom: 1px solid #f0f0f0; }}
            .card {{ display: flex; text-decoration: none; color: inherit; margin: 15px 20px; background: #fff; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.05); border: 1px solid #eee; }}
            .card img {{ width: 120px; height: 120px; object-fit: cover; background: #f5f5f5; }}
            .card-info {{ padding: 15px; flex: 1; }}
            .price {{ color: var(--danger); font-size: 20px; font-weight: 900; }}
            .action-bar {{ position: fixed; bottom: 0; left: 50%; transform: translateX(-50%); width: 100%; max-width: 500px; padding: 15px 20px 35px; display: flex; gap: 12px; background: rgba(255,255,255,0.95); backdrop-filter: blur(10px); z-index: 100; border-top: 1px solid #eee; }}
            .btn {{ flex: 1; text-align: center; padding: 16px; border-radius: 50px; text-decoration: none; font-weight: bold; color: #fff; font-size: 16px; }}
            .btn-call {{ background: var(--dark); }}
            .btn-line {{ background: #06c755; }}
            .btn-map {{ background: #4285F4; display: inline-block; padding: 10px 20px; border-radius: 8px; color: #fff; text-decoration: none; margin: 15px 0; font-weight: bold; font-size: 14px; }}
            .back-btn {{ position: absolute; top: 15px; left: 15px; background: rgba(0,0,0,0.5); color: #fff; padding: 8px 15px; border-radius: 20px; text-decoration: none; font-size: 14px; z-index: 10; backdrop-filter: blur(5px); }}
        </style>
    </head>
    """

def build():
    # --- 2. 結構修正：檔案產出於根目錄，確保 Google 擷取 ---
    out = Path(".") 
    # 清理舊物件目錄
    for p in out.glob("p*"):
        if p.is_dir() and re.match(r'^p\d+$', p.name): shutil.rmtree(p)
    for d in ["area", "sell"]: (out/d).mkdir(parents=True, exist_ok=True)

    print("🚀 啟動『林世塏』SEO 終極加強版建置...")
    res = requests.get(SHEET_CSV_URL); res.encoding = 'utf-8-sig'
    reader = csv.DictReader(res.text.splitlines())

    items, area_map, sitemap_urls = [], {}, [f"{BASE_URL}/"]

    for i, row in enumerate(reader):
        row = {str(k).strip().replace('\ufeff', ''): str(v).strip() for k, v in row.items() if k}
        if row.get("狀態") != "ON": continue

        img = get_final_img_url(row.get("圖片網址", ""))
        name, area, price, addr = row.get("案名", ""), row.get("區域", ""), row.get("價格", ""), row.get("地址", "")
        slug = f"p{i}"
        (out/slug).mkdir(exist_ok=True)
        page_url = f"{BASE_URL}/{slug}/"
        sitemap_urls.append(page_url)
        
        # --- 3. 自動生成地圖導航 ---
        map_link = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(addr if addr else name)}"

        # --- 4. 詳情頁：加入圖片 Alt 標籤以提升圖片 SEO ---
        detail_html = f"""
        <div class="container">
            <a href="../" class="back-btn">🏠 回首頁</a>
            <img src="{img}" alt="{esc(name)} - {esc(area)}房產推薦" style="width:100%; height:380px; object-fit:cover;">
            <div style="padding:30px 25px; margin-top:-35px; background:#fff; border-radius:30px 30px 0 0; position:relative;">
                <span style="color:var(--primary); font-weight:bold;">📍 {esc(area)}</span>
                <h1 style="font-size:24px; margin:10px 0;">{esc(name)}</h1>
                <div class="price">{esc(price)}</div>
                <a href="{map_link}" target="_blank" class="btn btn-map">📍 開啟 Google 地圖導航</a>
                <div style="background:var(--light); padding:15px; border-radius:10px; font-size:15px; margin-top:15px;">
                    {esc(row.get("描述","")).replace('、', '<br>• ')}
                </div>
            </div>
            <div class="action-bar"><a href="tel:{MY_PHONE}" class="btn btn-call">📞 撥打電話</a><a href="{MY_LINE_URL}" class="btn btn-line">💬 LINE 諮詢</a></div>
        </div>
        """
        (out/slug/"index.html").write_text(f"<!doctype html><html lang='zh-tw'>{get_head(name, GA4_ID)}<body>{detail_html}</body></html>", encoding="utf-8")
        
        card_html = f"""<a href="./{slug}/" class="card"><img src="{img}" alt="{esc(name)}"><div class="card-info"><b>{esc(name)}</b><div class="price" style="font-size:16px;">{esc(price)}</div></div></a>"""
        items.append(card_html)
        area_map.setdefault(area, []).append(card_html.replace('./', '../../'))

    # --- 5. 生成區域分頁 (/area/ & /sell/) ---
    for area, cards in area_map.items():
        a_slug = urllib.parse.quote(area)
        for d_path, title_suffix in [("area", "買房推薦"), ("sell", "委託賣房")]:
            (out/d_path/a_slug).mkdir(exist_ok=True)
            page_body = f"""<div class="container"><a href="../../" class="back-btn">🏠 回首頁</a><div class="header"><h1>{area}{title_suffix}</h1></div>{''.join(cards)}</div>"""
            (out/d_path/a_slug/"index.html").write_text(f"<!doctype html><html>{get_head(area+title_suffix, GA4_ID)}<body>{page_body}</body></html>", encoding="utf-8")

    # --- 6. 生成首頁與標準 Sitemap.xml ---
    (out/"index.html").write_text(f"<!doctype html><html>{get_head(SITE_TITLE, GA4_ID)}<body><div class='container'><div class='header'><h1>🏠 {SITE_TITLE}</h1><p>{SLOGAN}</p></div>{''.join(items)}</div></body></html>", encoding="utf-8")
    
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for url in sitemap_urls:
        sitemap += f'  <url><loc>{url}</loc><lastmod>{datetime.now().strftime("%Y-%m-%d")}</lastmod></url>\n'
    sitemap += '</urlset>'
    (out/"sitemap.xml").write_text(sitemap, encoding="utf-8")
    print("✅ SEO 終極加強旗艦版建置成功！")

if __name__ == "__main__": build()
