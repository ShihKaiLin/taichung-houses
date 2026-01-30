import os, csv, requests, html, shutil
from pathlib import Path
from datetime import datetime

# --- 核心配置 ---
# 1. 您的 Google 試算表 CSV 公布連結
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQShAl0-TbUU0MQdYVe53im2T6lXQgh_7g-bdL6HHpIBFtA2yfIAMbPw4J9RgZUkROb9AAiMhnRC0kH/pub?output=csv"
# 2. 聯絡資訊
MY_PHONE = "0938-615-351"
MY_LINE_URL = "https://line.me/ti/p/FDsMyAYDv"
# 3. 網站基本資訊 (影響 SEO)
SITE_TITLE = "台中房產雲端看板"
BASE_URL = "https://shihkailin.github.io/taichung-houses"

def esc(s): return html.escape(str(s or "").strip())

def build():
    out = Path("site")
    if out.exists(): shutil.rmtree(out)
    out.mkdir()

    print("🚀 啟動旗艦版 SEO 建置引擎...")
    try:
        res = requests.get(SHEET_CSV_URL)
        res.encoding = 'utf-8-sig'
        lines = [line.strip() for line in res.text.splitlines() if line.strip()]
        reader = csv.DictReader(lines)
    except Exception as e:
        print(f"❌ 讀取試算表失敗: {e}")
        return

    items = []
    sitemap_urls = [f"{BASE_URL}/"]

    for i, row in enumerate(reader):
        # 整理標題與內容
        clean_row = {str(k).strip().replace('\ufeff', ''): str(v).strip() for k, v in row.items() if k}
        
        # 僅處理狀態為 ON 的物件
        if clean_row.get("狀態") != "ON": continue

        name = clean_row.get("案名", "精選物件")
        area = clean_row.get("區域", "台中")
        price = clean_row.get("價格", "面議")
        desc = clean_row.get("描述", "")
        img_url = clean_row.get("圖片網址", "")
        address = clean_row.get("地址", "")
        
        # --- SEO 關鍵字優化 ---
        seo_title = f"[{area}] {name} - {price} | {SITE_TITLE}"
        keywords = f"{area}買屋, {name}, {address}, 台中房地產, 實價登錄, {price}, {area}仲介"
        slug = f"p{i}"
        (out/slug).mkdir()
        sitemap_urls.append(f"{BASE_URL}/{slug}/")

        # --- 物件詳細頁 (旗艦版視覺) ---
        page_html = f"""<!doctype html>
<html lang="zh-TW">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{seo_title}</title>
    <meta name="description" content="{esc(desc)[:100]}">
    <meta name="keywords" content="{keywords}">
    <style>
        body {{ font-family: 'PingFang TC', 'Microsoft JhengHei', sans-serif; background: #f8fafc; margin: 0; padding: 15px; color: #333; }}
        .container {{ max-width: 600px; margin: auto; }}
        .card {{ background: #fff; border-radius: 25px; overflow: hidden; box-shadow: 0 15px 35px rgba(0,0,0,0.1); border: 1px solid #eee; }}
        .img-box {{ width: 100%; position: relative; background: #eee; min-height: 250px; }}
        .img-box img {{ width: 100%; display: block; }}
        .content {{ padding: 25px; }}
        .area-tag {{ display: inline-block; background: linear-gradient(135deg, #f2994a, #f2c94c); color: #fff; padding: 4px 15px; border-radius: 50px; font-size: 14px; font-weight: bold; }}
        h1 {{ font-size: 22px; margin: 15px 0 10px; line-height: 1.4; }}
        .price-tag {{ color: #e63946; font-size: 30px; font-weight: 900; margin-bottom: 5px; }}
        .address {{ color: #777; font-size: 15px; margin-bottom: 20px; }}
        .features {{ background: #fff8f0; border-left: 5px solid #f2994a; padding: 15px; border-radius: 8px; font-size: 16px; line-height: 1.6; }}
        .btn-group {{ display: flex; gap: 12px; margin-top: 25px; }}
        .btn {{ flex: 1; text-align: center; padding: 16px; border-radius: 50px; text-decoration: none; font-weight: bold; font-size: 17px; transition: 0.2s; }}
        .tel {{ background: #333; color: #fff; }}
        .line {{ background: #06C755; color: #fff; }}
        .footer-seo {{ margin-top: 20px; font-size: 11px; color: #ccc; text-align: center; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <div class="img-box">
                <img src="{img_url}" onerror="this.src='https://placehold.co/600x400?text=圖片載入中...請檢查Google連結'" alt="{name}">
            </div>
            <div class="content">
                <div class="area-tag">{esc(area)}</div>
                <h1>{esc(name)}</h1>
                <div class="price-tag">{esc(price)}</div>
                <p class="address">📍 {esc(address)}</p>
                <div class="features">🏠 物件描述：<br>{esc(desc).replace('、', '<br>• ')}</div>
                <div class="btn-group">
                    <a href="tel:{MY_PHONE}" class="btn tel">📞 撥打電話</a>
                    <a href="{MY_LINE_URL}" class="btn line">💬 LINE 諮詢</a>
                </div>
                <div class="footer-seo">關鍵字：{keywords}</div>
            </div>
        </div>
    </div>
</body>
</html>"""
        (out/slug/"index.html").write_text(page_html, encoding="utf-8")
        
        # 收集首頁列表資料
        items.append(f"""
            <a href="./{slug}/" class="list-item">
                <div class="list-area">[{esc(area)}]</div>
                <div class="list-name">{esc(name)}</div>
                <div class="list-price">{esc(price)}</div>
            </a>
        """)

    # --- 生成首頁 ---
    home_html = f"""<!doctype html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{SITE_TITLE} - 世塏精選台中房產</title>
    <style>
        body {{ background: #f0f2f5; font-family: sans-serif; padding: 20px; }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .list {{ max-width: 600px; margin: auto; }}
        .list-item {{ display: block; background: white; margin-bottom: 12px; padding: 20px; border-radius: 15px; text-decoration: none; color: #333; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border-left: 6px solid #f2994a; }}
        .list-area {{ color: #999; font-size: 13px; }}
        .list-name {{ font-size: 18px; font-weight: bold; margin: 5px 0; }}
        .list-price {{ color: #d93025; font-size: 20px; font-weight: 800; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🏠 {SITE_TITLE}</h1>
        <p>提供最即時、精選的台中房產資訊</p>
    </div>
    <div class="list">{"".join(items)}</div>
</body>
</html>"""
    (out/"index.html").write_text(home_html, encoding="utf-8")

    # --- 生成 Sitemap (SEO 必備) ---
    sitemap = f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    for url in sitemap_urls:
        sitemap += f'<url><loc>{url}</loc><lastmod>{datetime.now().strftime("%Y-%m-%d")}</lastmod></url>'
    sitemap += '</urlset>'
    (out/"sitemap.xml").write_text(sitemap, encoding="utf-8")
    
    print(f"✅ 旗艦版建置完成！共生成 {len(items)} 個物件頁面。")

if __name__ == "__main__":
    build()
