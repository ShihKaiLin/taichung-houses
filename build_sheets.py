import os, csv, requests, html, shutil, re, urllib.parse
from pathlib import Path
from datetime import datetime

# --- 核心配置 ---
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQShAl0-TbUU0MQdYVe53im2T6lXQgh_7g-bdL6HHpIBFtA2yfIAMbPw4J9RgZUkROb9AAiMhnRC0kH/pub?output=csv"
MY_PHONE = "0938-615-351"
MY_LINE_URL = "https://line.me/ti/p/FDsMyAYDv"
SITE_TITLE = "林世塏｜台中精選房產"
SLOGAN = "石開林｜為您挑選最理想的家"
BASE_URL = "https://shihkailin.github.io/taichung-houses"
GA4_ID = "" # 填入 G-XXXXXX 即可啟用

def esc(s): return html.escape(str(s or "").strip())

def convert_google_drive_url(url):
    """強力解析 Google Drive ID 並轉換為直連網址"""
    if "drive.google.com" in url:
        match = re.search(r'[-\w]{25,45}', url)
        if match:
            return f"https://drive.google.com/uc?export=view&id={match.group()}"
    return url

def get_head(title, desc, img, url):
    ga_script = f"""<script async src="https://www.googletagmanager.com/gtag/js?id={GA4_ID}"></script><script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','{GA4_ID}');</script>""" if GA4_ID else ""
    return f"""
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=0">
        <title>{esc(title)}</title>
        <meta name="description" content="{esc(desc)[:150]}">
        <meta property="og:title" content="{esc(title)}">
        <meta property="og:image" content="{esc(img)}">
        <meta property="og:url" content="{url}">
        {ga_script}
        <style>
            :root {{ --primary: #b08d57; --dark: #1a1a1a; --light: #f8f9fa; --danger: #e63946; }}
            body {{ font-family: 'PingFang TC', sans-serif; background: var(--light); margin: 0; color: var(--dark); line-height: 1.6; }}
            .container {{ max-width: 500px; margin: auto; background: #fff; min-height: 100vh; padding-bottom: 120px; box-shadow: 0 0 20px rgba(0,0,0,0.05); }}
            .header {{ padding: 50px 25px 25px; background: #fff; border-bottom: 1px solid #f0f0f0; text-align: center; }}
            .card {{ display: flex; text-decoration: none; color: inherit; margin: 15px 20px; background: #fff; border-radius: 16px; overflow: hidden; box-shadow: 0 5px 15px rgba(0,0,0,0.05); border: 1px solid #eee; }}
            .card img {{ width: 120px; height: 120px; object-fit: cover; background: #f9f9f9; }}
            .card-info {{ padding: 15px; flex: 1; display: flex; flex-direction: column; justify-content: center; }}
            .price {{ color: var(--primary); font-size: 22px; font-weight: 900; }}
            .insight-box {{ margin: 20px; padding: 25px; background: #fdfaf5; border-left: 5px solid var(--primary); border-radius: 8px; font-size: 15px; }}
            .action-bar {{ position: fixed; bottom: 0; left: 50%; transform: translateX(-50%); width: 100%; max-width: 500px; padding: 15px 20px 30px; display: flex; gap: 10px; background: rgba(255,255,255,0.9); backdrop-filter: blur(10px); box-sizing: border-box; z-index: 100; border-top: 1px solid #eee; }}
            .btn {{ flex: 1; text-align: center; padding: 16px; border-radius: 12px; text-decoration: none; font-weight: bold; color: #fff; }}
            .btn-call {{ background: var(--dark); }}
            .btn-line {{ background: #06c755; }}
        </style>
    </head>
    """

def build():
    out = Path("site")
    if out.exists(): shutil.rmtree(out)
    for d in ["area", "sell"]: (out/d).mkdir(parents=True)

    print("🚀 正在建置『林世塏』全功能截流版...")
    res = requests.get(SHEET_CSV_URL); res.encoding = 'utf-8-sig'
    reader = csv.DictReader(res.text.splitlines())

    items, area_map, sitemap_urls = [], {}, [f"{BASE_URL}/"]

    for i, row in enumerate(reader):
        row = {str(k).strip().replace('\ufeff', ''): str(v).strip() for k, v in row.items() if k}
        if row.get("狀態") != "ON": continue

        name, area, price = row.get("案名", ""), row.get("區域", "台中"), row.get("價格", "")
        img = convert_google_drive_url(row.get("圖片網址", ""))
        desc_raw = row.get("描述", "")
        addr = row.get("地址", "台中市")
        slug = f"p{i}"
        (out/slug).mkdir()
        page_url = f"{BASE_URL}/{slug}/"
        sitemap_urls.append(page_url)

        # 1. 物件詳細頁
        detail_html = f"""
        <div class="container">
            <img src="{img}" style="width:100%; height:350px; object-fit:cover;" onerror="this.src='https://via.placeholder.com/800?text=圖片載入中'">
            <div style="padding:30px 25px; margin-top:-30px; background:#fff; border-radius:30px 30px 0 0; position:relative;">
                <span style="color:var(--primary); font-weight:bold; font-size:14px;">📍 {esc(area)}</span>
                <h1 style="font-size:26px; margin:10px 0; font-weight:900;">{esc(name)}</h1>
                <div class="price" style="font-size:28px; margin-bottom:20px;">{esc(price)}</div>
                <div style="background:var(--light); padding:20px; border-radius:12px; line-height:1.8;">{esc(desc_raw).replace('、', '<br>• ')}</div>
            </div>
            <div class="action-bar">
                <a href="tel:{MY_PHONE}" class="btn btn-call">📞 立即致電</a>
                <a href="{MY_LINE_URL}" class="btn btn-line">💬 LINE 諮詢</a>
            </div>
        </div>
        """
        (out/slug/"index.html").write_text(f"<!doctype html><html lang='zh-tw'>{get_head(name, desc_raw, img, page_url)}<body>{detail_html}</body></html>", encoding="utf-8")
        
        # 準備卡片 HTML
        card_html = f"""
        <a href="../../{slug}/" class="card">
            <img src="{img}" loading="lazy">
            <div class="card-info">
                <span style="font-size:12px; color:#999;">{esc(area)}</span>
                <b style="font-size:17px; margin:4px 0; display:block;">{esc(name)}</b>
                <div class="price">{esc(price)}</div>
            </div>
        </a>
        """
        items.append(card_html.replace('../../', './'))
        area_map.setdefault(area, []).append(card_html)

    # 2. 生成區域 (area/) 與 委託 (sell/) 截流頁面
    for area, cards in area_map.items():
        a_slug = urllib.parse.quote(area)
        sitemap_urls.append(f"{BASE_URL}/area/{a_slug}/")
        sitemap_urls.append(f"{BASE_URL}/sell/{a_slug}/")
        
        for d_path, title_prefix, insight in [
            ("area", f"{area}買房推薦", f"📍 {area} 區域專家分析：本區生活機能完善，是台中交易指標。"),
            ("sell", f"{area}委託賣房", f"🏠 為什麼選擇林世塏？我們透過 AI 與 SEO 技術，讓您的物件獲得最高曝光。")
        ]:
            (out/d_path/a_slug).mkdir(exist_ok=True)
            page_body = f"""<div class="container"><div class="header"><h1>{area}{title_prefix}</h1></div><div class="insight-box"><h3>{insight[:2]} 分析</h3><p>{insight}</p></div>{''.join(cards)}</div>"""
            (out/d_path/a_slug/"index.html").write_text(f"<!doctype html><html>{get_head(f'{area}{title_prefix}', area, '', '')}<body>{page_body}</body></html>", encoding="utf-8")

    # 3. 首頁
    (out/"index.html").write_text(f"<!doctype html><html>{get_head(SITE_TITLE, SLOGAN, '', f'{BASE_URL}/')}<body><div class='container'><div class='header'><h1>{SITE_TITLE}</h1><p style='color:var(--primary); font-weight:600;'>{SLOGAN}</p></div>{''.join(items)}</div></body></html>", encoding="utf-8")

    # 4. 自動 Sitemap.xml (SEO 用)
    sitemap = f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    for url in sitemap_urls:
        sitemap += f'<url><loc>{url}</loc><lastmod>{datetime.now().strftime("%Y-%m-%d")}</lastmod></url>'
    sitemap += '</urlset>'
    (out/"sitemap.xml").write_text(sitemap, encoding="utf-8")
    
    print(f"✅ 旗艦截流版部署成功！共建置 {len(items)} 個物件與 {len(area_map)*2} 個行銷分頁。")

if __name__ == "__main__": build()
