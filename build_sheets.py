import os, csv, requests, html, shutil
from pathlib import Path
from datetime import datetime

# --- 核心配置 ---
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQShAl0-TbUU0MQdYVe53im2T6lXQgh_7g-bdL6HHpIBFtA2yfIAMbPw4J9RgZUkROb9AAiMhnRC0kH/pub?output=csv"
MY_PHONE = "0938-615-351"
MY_LINE_URL = "https://line.me/ti/p/FDsMyAYDv"
SITE_TITLE = "台中房產雲端看板"
BASE_URL = "https://shihkailin.github.io/taichung-houses" # 用於 SEO Sitemap

def esc(s): return html.escape(str(s or "").strip())

def build():
    out = Path("site")
    if out.exists(): shutil.rmtree(out)
    out.mkdir()

    print("🚀 啟動旗艦版 SEO 建置引擎...")
    res = requests.get(SHEET_CSV_URL)
    res.encoding = 'utf-8-sig'
    lines = [line.strip() for line in res.text.splitlines() if line.strip()]
    reader = csv.DictReader(lines)

    items = []
    sitemap_urls = [f"{BASE_URL}/"]

    for i, row in enumerate(reader):
        clean_row = {str(k).strip().replace('\ufeff', ''): str(v).strip() for k, v in row.items() if k}
        if clean_row.get("狀態") != "ON": continue

        name = clean_row.get("案名", "精選物件")
        area = clean_row.get("區域", "台中")
        price = clean_row.get("價格", "面議")
        desc = clean_row.get("描述", "")
        img_url = clean_row.get("圖片網址", "")
        address = clean_row.get("地址", "")
        
        # SEO 強化：自動組合關鍵字標題
        seo_title = f"[{area}] {name} - {price} | {SITE_TITLE}"
        keywords = f"{area}買屋, {name}, {address}, 台中房地產, 實價登錄, {price}"
        slug = f"p{i}"
        (out/slug).mkdir()
        sitemap_urls.append(f"{BASE_URL}/{slug}/")

        # 物件詳細頁 (旗艦版 UI)
        page_content = f"""
        <div class="card">
            <div class="img-container">
                {f'<img src="{img_url}" alt="{name}">' if "http" in img_url else '<div class="no-img">📸 預覽圖製作中</div>'}
            </div>
            <div class="content">
                <span class="badge">{esc(area)}</span>
                <h1>{esc(name)}</h1>
                <p class="price">{esc(price)}</p>
                <p class="address">📍 {esc(address)}</p>
                <div class="desc-box">
                    <strong>🏠 物件特色：</strong><br>
                    {esc(desc).replace('、', '<br>• ')}
                </div>
                <div class="btn-group">
                    <a href="tel:{MY_PHONE}" class="btn tel">📞 立即撥通</a>
                    <a href="{MY_LINE_URL}" class="btn line">💬 LINE 諮詢</a>
                </div>
                <div class="seo-footer">相關搜尋：{keywords}</div>
            </div>
        </div>
        """
        
        full_page = f"""<!doctype html><html><head>
            <meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
            <title>{seo_title}</title>
            <meta name="description" content="{esc(desc)[:100]}">
            <meta name="keywords" content="{keywords}">
            <style>
                body {{ font-family: -apple-system, sans-serif; background: #f0f2f5; margin: 0; padding: 20px; }}
                .card {{ max-width: 500px; margin: auto; background: white; border-radius: 20px; overflow: hidden; box-shadow: 0 10px 25px rgba(0,0,0,0.1); }}
                .img-container img {{ width: 100%; display: block; }}
                .no-img {{ height: 250px; background: #eee; display: flex; align-items: center; justify-content: center; color: #999; }}
                .content {{ padding: 25px; }}
                .badge {{ background: #e8f0fe; color: #1a73e8; padding: 5px 12px; border-radius: 50px; font-weight: bold; font-size: 14px; }}
                h1 {{ font-size: 22px; margin: 15px 0 10px; color: #1c1e21; }}
                .price {{ color: #d93025; font-size: 28px; font-weight: 800; margin-bottom: 10px; }}
                .address {{ color: #5f6368; font-size: 15px; margin-bottom: 20px; }}
                .desc-box {{ background: #f8f9fa; padding: 15px; border-radius: 12px; line-height: 1.6; color: #4b4b4b; }}
                .btn-group {{ display: flex; gap: 12px; margin-top: 25px; }}
                .btn {{ flex: 1; text-align: center; padding: 16px; border-radius: 50px; text-decoration: none; font-weight: bold; transition: 0.3s; }}
                .tel {{ background: #f2994a; color: white; }}
                .line {{ background: #27ae60; color: white; }}
                .seo-footer {{ margin-top: 30px; font-size: 12px; color: #ccc; }}
            </style>
        </head><body>{page_content}</body></html>"""
        
        (out/slug/"index.html").write_text(full_page, encoding="utf-8")
        items.append(f"""
            <a href="./{slug}/" class="item-card">
                <div class="item-info">
                    <span class="item-area">[{esc(area)}]</span>
                    <div class="item-name">{esc(name)}</div>
                    <div class="item-price">{esc(price)}</div>
                </div>
            </a>
        """)

    # 生成首頁
    home_html = f"""
    <!doctype html><html><head>
    <meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
    <title>{SITE_TITLE} - 台中買屋賣屋推薦</title>
    <style>
        body {{ background: #f8fafc; font-family: sans-serif; padding: 20px; }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .list {{ max-width: 600px; margin: auto; }}
        .item-card {{ display: block; background: white; margin-bottom: 15px; padding: 20px; border-radius: 15px; text-decoration: none; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border-left: 6px solid #f2994a; }}
        .item-area {{ color: #999; font-size: 13px; }}
        .item-name {{ font-size: 18px; color: #333; font-weight: bold; margin: 5px 0; }}
        .item-price {{ color: #d93025; font-size: 20px; font-weight: 800; }}
    </style>
    </head><body>
    <div class="header"><h1>🏠 {SITE_TITLE}</h1><p>世塏精選 · 台中好房</p></div>
    <div class="list">{"".join(items)}</div>
    </body></html>
    """
    (out/"index.html").write_text(home_html, encoding="utf-8")

    # --- 生成自動化 Sitemap ---
    sitemap = f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    for url in sitemap_urls:
        sitemap += f'<url><loc>{url}</loc><lastmod>{datetime.now().strftime("%Y-%m-%d")}</lastmod></url>'
    sitemap += '</urlset>'
    (out/"sitemap.xml").write_text(sitemap, encoding="utf-8")
    
    print(f"✅ 旗艦版建置完成！共生成 {len(items)} 個 SEO 頁面。")

if __name__ == "__main__": build()
