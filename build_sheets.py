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
GA4_ID = "G-B7WP9BTP8X" # 已為您填入 GA4 編號

def esc(s): return html.escape(str(s or "").strip())

def get_final_img_url(url):
    """【最強解析】優先抓 GitHub 本地檔案，支援 Google Drive 自動轉換"""
    url = str(url).strip()
    if not url: return "https://placehold.co/600x400?text=無圖片"
    # 處理 GitHub 內部照片
    if not url.startswith("http"):
        clean_path = url.lstrip("/")
        if not clean_path.startswith("images/"): clean_path = f"images/{clean_path}"
        return f"https://raw.githubusercontent.com/ShihKaiLin/taichung-houses/main/{clean_path}"
    # 處理 Google Drive 轉換
    if "drive.google.com" in url:
        match = re.search(r'[-\w]{25,45}', url)
        if match: return f"https://drive.google.com/uc?export=view&id={match.group()}"
    return url

def get_head(title, desc, img, url):
    """整合 SEO 與 GA4 數據追蹤"""
    ga_script = f"""
    <script async src="https://www.googletagmanager.com/gtag/js?id={GA4_ID}"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){{dataLayer.push(arguments);}}
      gtag('js', new Date());
      gtag('config', '{GA4_ID}');
    </script>
    """ if GA4_ID else ""
    return f"""
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=0">
        <title>{esc(title)}</title>
        <meta name="description" content="{esc(desc)[:150]}">
        {ga_script}
        <style>
            :root {{ --primary: #b08d57; --dark: #1a1a1a; --light: #f8f9fa; --danger: #e63946; }}
            body {{ font-family: 'PingFang TC', 'Microsoft JhengHei', sans-serif; background: var(--light); margin: 0; color: var(--dark); line-height: 1.6; }}
            .container {{ max-width: 500px; margin: auto; background: #fff; min-height: 100vh; padding-bottom: 120px; box-shadow: 0 0 30px rgba(0,0,0,0.05); }}
            .header {{ padding: 60px 25px 30px; background: #fff; text-align: center; border-bottom: 1px solid #f0f0f0; }}
            .card {{ display: flex; text-decoration: none; color: inherit; margin: 15px 20px; background: #fff; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.05); border: 1px solid #eee; transition: 0.3s; }}
            .card img {{ width: 120px; height: 120px; object-fit: cover; background: #f5f5f5; }}
            .card-info {{ padding: 15px; flex: 1; display: flex; flex-direction: column; justify-content: center; }}
            .price {{ color: var(--danger); font-size: 22px; font-weight: 900; }}
            .action-bar {{ position: fixed; bottom: 0; left: 50%; transform: translateX(-50%); width: 100%; max-width: 500px; padding: 15px 20px 35px; display: flex; gap: 12px; background: rgba(255,255,255,0.9); backdrop-filter: blur(10px); z-index: 100; border-top: 1px solid #eee; }}
            .btn {{ flex: 1; text-align: center; padding: 16px; border-radius: 50px; text-decoration: none; font-weight: bold; font-size: 16px; color: #fff; }}
            .btn-call {{ background: var(--dark); }}
            .btn-line {{ background: #06c755; }}
            .btn-map {{ background: #4285F4; display: inline-block; padding: 10px 20px; border-radius: 8px; color: #fff; text-decoration: none; margin-top: 15px; font-weight: bold; font-size: 14px; }}
        </style>
    </head>
    """

def build():
    out = Path("site")
    if out.exists(): shutil.rmtree(out)
    for d in ["area", "sell"]: (out/d).mkdir(parents=True)

    print("🚀 啟動『林世塏』旗艦版建置引擎...")
    res = requests.get(SHEET_CSV_URL); res.encoding = 'utf-8-sig'
    reader = csv.DictReader(res.text.splitlines())

    items, sitemap_urls = [], [f"{BASE_URL}/"]

    for i, row in enumerate(reader):
        row = {str(k).strip().replace('\ufeff', ''): str(v).strip() for k, v in row.items() if k}
        if row.get("狀態") != "ON": continue

        img = get_final_img_url(row.get("圖片網址", ""))
        name, area, price, addr = row.get("案名", ""), row.get("區域", ""), row.get("價格", ""), row.get("地址", "")
        slug = f"p{i}"
        (out/slug).mkdir()
        page_url = f"{BASE_URL}/{slug}/"
        sitemap_urls.append(page_url)
        
        # 產生 Google 地圖搜尋連結
        map_link = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(addr if addr else name)}"

        detail_html = f"""
        <div class="container">
            <img src="{img}" style="width:100%; height:380px; object-fit:cover;" onerror="this.src='https://placehold.co/800x600?text=照片路徑檢查中'">
            <div style="padding:30px 25px; margin-top:-35px; background:#fff; border-radius:30px 30px 0 0; position:relative;">
                <span style="background:var(--light); padding:5px 15px; border-radius:50px; font-size:13px; color:var(--primary); font-weight:bold;">📍 {esc(area)}</span>
                <h1 style="font-size:26px; margin:15px 0 10px; font-weight:900;">{esc(name)}</h1>
                <div class="price" style="font-size:30px; margin-bottom:20px;">{esc(price)}</div>
                
                <a href="{map_link}" target="_blank" class="btn btn-map">📍 在 Google 地圖查看位置</a>
                
                <div style="background:var(--light); padding:20px; border-radius:15px; font-size:16px; line-height:1.8;">
                    🏠 物件描述：<br>{esc(row.get("描述","")).replace('、', '<br>• ')}<br><br>
                    📌 地址：{esc(addr if addr else "請洽經紀人")}
                </div>
            </div>
            <div class="action-bar">
                <a href="tel:{MY_PHONE}" class="btn btn-call">📞 撥打電話</a>
                <a href="{MY_LINE_URL}" class="btn btn-line">💬 LINE 諮詢</a>
            </div>
        </div>
        """
        (out/slug/"index.html").write_text(f"<!doctype html><html lang='zh-tw'>{get_head(name, '', img, page_url)}<body>{detail_html}</body></html>", encoding="utf-8")
        items.append(f"""<a href="./{slug}/" class="card"><img src="{img}"><div class="card-info"><span style="font-size:12px; color:var(--primary);">{esc(area)}</span><b style="font-size:17px; margin:3px 0; display:block;">{esc(name)}</b><div class="price" style="font-size:18px;">{esc(price)}</div></div></a>""")

    # 生成首頁
    (out/"index.html").write_text(f"<!doctype html><html>{get_head(SITE_TITLE, SLOGAN, '', f'{BASE_URL}/')}<body><div class='container'><div class='header'><h1>🏠 {SITE_TITLE}</h1><p style='color:var(--primary); font-weight:600;'>{SLOGAN}</p></div>{''.join(items)}</div></body></html>", encoding="utf-8")

    # 生成 Sitemap.xml
    sitemap = f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    for url in sitemap_urls: sitemap += f'<url><loc>{url}</loc><lastmod>{datetime.now().strftime("%Y-%m-%d")}</lastmod></url>'
    sitemap += '</urlset>'
    (out/"sitemap.xml").write_text(sitemap, encoding="utf-8")
    print("✅ 旗艦版部署成功！")

if __name__ == "__main__": build()
