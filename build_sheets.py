import os, csv, requests, html, shutil, re, urllib.parse
from pathlib import Path
from datetime import datetime

# --- 1. 核心配置 ---
# 這些資訊確保您的 GA4 與聯絡管道運作正常
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQShAl0-TbUU0MQdYVe53im2T6lXQgh_7g-bdL6HHpIBFtA2yfIAMbPw4J9RgZUkROb9AAiMhnRC0kH/pub?output=csv"
MY_PHONE = "0938-615-351"
MY_LINE_URL = "https://line.me/ti/p/FDsMyAYDv"
SITE_TITLE = "林世塏｜台中地圖找房"
BASE_URL = "https://shihkailin.github.io/taichung-houses"
GA4_ID = "G-B7WP9BTP8X"

def esc(s): return html.escape(str(s or "").strip())

def get_final_img_url(url):
    """【自動圖床】支援 GitHub images/ 資料夾，讓您填試算表更輕鬆"""
    url = str(url).strip()
    if not url: return "https://placehold.co/600x400?text=照片整理中"
    if not url.startswith("http"):
        return f"https://raw.githubusercontent.com/ShihKaiLin/taichung-houses/main/images/{url.lstrip('/')}"
    return url

def get_head(title, ga_id, img_url, page_url):
    """【巷導風 CSS】模擬地圖 App 質感，提升客戶留存率"""
    ga = f"""<script async src="https://www.googletagmanager.com/gtag/js?id={ga_id}"></script><script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','{ga_id}');</script>""" if ga_id else ""
    return f"""
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=0">
        <title>{esc(title)}</title>
        <meta property="og:title" content="{esc(title)}">
        <meta property="og:image" content="{img_url}">
        <meta property="og:url" content="{page_url}">
        {ga}
        <style>
            :root {{ --alley-blue: #2A58AD; --alley-gray: #f2f4f7; --alley-dark: #333; }}
            body {{ font-family: 'PingFang TC', 'Noto Sans TC', sans-serif; background: #fff; margin: 0; color: var(--alley-dark); line-height: 1.6; }}
            .container {{ max-width: 480px; margin: auto; min-height: 100vh; padding-bottom: 120px; box-shadow: 0 0 30px rgba(0,0,0,0.05); position: relative; }}
            .header {{ padding: 30px 20px 15px; background: #fff; border-bottom: 1px solid #eee; }}
            .header h1 {{ font-size: 20px; margin: 0; color: var(--alley-blue); }}
            .filter-bar {{ display: flex; gap: 8px; padding: 12px 20px; overflow-x: auto; background: #fff; position: sticky; top: 0; z-index: 100; box-shadow: 0 4px 10px rgba(0,0,0,0.03); }}
            .filter-btn {{ padding: 6px 16px; background: var(--alley-gray); border-radius: 6px; text-decoration: none; color: #666; font-size: 13px; font-weight: 500; white-space: nowrap; border: 1px solid transparent; }}
            .filter-btn.active {{ background: #fff; color: var(--alley-blue); border-color: var(--alley-blue); }}
            .card {{ display: block; text-decoration: none; color: inherit; margin: 15px 20px; background: #fff; border-radius: 12px; overflow: hidden; border: 1px solid #eee; box-shadow: 0 2px 8px rgba(0,0,0,0.03); transition: transform 0.2s; }}
            .card-img-box {{ position: relative; width: 100%; height: 220px; }}
            .card img {{ width: 100%; height: 100%; object-fit: cover; }}
            .area-tag {{ position: absolute; top: 12px; left: 12px; background: rgba(255,255,255,0.9); padding: 4px 10px; border-radius: 4px; font-size: 11px; font-weight: bold; color: var(--alley-blue); }}
            .card-info {{ padding: 16px; }}
            .card-info b {{ font-size: 17px; display: block; margin-bottom: 5px; }}
            .price {{ color: #e53e3e; font-size: 22px; font-weight: 800; }}
            .action-bar {{ position: fixed; bottom: 0; left: 50%; transform: translateX(-50%); width: 100%; max-width: 480px; padding: 12px 15px 30px; display: flex; gap: 8px; background: #fff; border-top: 1px solid #eee; z-index: 200; }}
            .btn {{ flex: 1; text-align: center; padding: 14px; border-radius: 8px; text-decoration: none; font-weight: bold; color: #fff; font-size: 14px; }}
            .btn-call {{ background: var(--alley-dark); }}
            .btn-line {{ background: #00B900; }}
            .back-btn {{ position: absolute; top: 15px; left: 15px; background: #fff; color: #333; padding: 5px 12px; border-radius: 6px; text-decoration: none; font-size: 13px; z-index: 10; border: 1px solid #ddd; }}
        </style>
    </head>
    """

def build():
    out = Path(".") 
    # 自動清理舊物件，維持系統整潔
    for p in out.glob("p*"):
        if p.is_dir() and re.match(r'^p\d+$', p.name): shutil.rmtree(p)
    if (out/"area").exists(): shutil.rmtree(out/"area")
    (out/"area").mkdir(exist_ok=True)

    print("🚀 啟動『林世塏』純淨導流版更新...")
    res = requests.get(SHEET_CSV_URL); res.encoding = 'utf-8-sig'
    reader = csv.DictReader(res.text.splitlines())

    items, area_map, sitemap_urls = [], {}, [f"{BASE_URL}/"]

    for i, row in enumerate(reader):
        row = {str(k).strip().replace('\ufeff', ''): str(v).strip() for k, v in row.items() if k}
        if row.get("狀態") != "ON" or not row.get("案名"): continue

        img = get_final_img_url(row.get("圖片網址", ""))
        name, area, price, addr = row.get("案名", ""), row.get("區域", ""), row.get("價格", ""), row.get("地址", "")
        ext_url = row.get("外部網址", "")
        slug = f"p{i}"
        (out/slug).mkdir(exist_ok=True)
        page_url = f"{BASE_URL}/{slug}/"
        sitemap_urls.append(page_url)
        
        map_link = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(addr if addr else name)}"
        
        # 外部導流按鈕：解決繁瑣坪數資料，一鍵導向官網
        ext_btn_html = ""
        if ext_url:
            btn_txt = "查看完整建坪與格局圖" if "ychouse" in ext_url else "前往 591 查看詳細數據"
            ext_btn_html = f'<a href="{ext_url}" target="_blank" style="display:block; text-align:center; padding:12px; border:1.5px solid var(--alley-blue); border-radius:8px; color:var(--alley-blue); text-decoration:none; margin-top:15px; font-weight:bold; font-size:14px;">🔗 {btn_txt}</a>'

        detail_html = f"""
        <div class="container">
            <a href="../" class="back-btn">← 返回列表</a>
            <img src="{img}" style="width:100%; height:320px; object-fit:cover;">
            <div style="padding:25px; background:#fff; margin-top:-15px; border-radius:15px 15px 0 0; position:relative;">
                <span style="color:var(--alley-blue); font-size:12px; font-weight:bold;">📍 {esc(area)}</span>
                <h1 style="font-size:22px; margin:8px 0; letter-spacing:-0.5px;">{esc(name)}</h1>
                <div class="price" style="margin-bottom:15px;">{esc(price)}</div>
                <div style="background:var(--alley-gray); padding:15px; border-radius:8px; font-size:14px; color:#555;">
                    {esc(row.get("描述","")).replace('、', '<br>• ')}
                </div>
                {ext_btn_html}
                <a href="{map_link}" target="_blank" style="display:block; text-align:center; padding:12px; background:var(--alley-blue); border-radius:8px; color:#fff; text-decoration:none; margin-top:12px; font-weight:bold; font-size:14px;">📍 開啟 Google 地圖導航</a>
            </div>
            <div class="action-bar"><a href="tel:{MY_PHONE}" class="btn btn-call">致電聯繫</a><a href="{MY_LINE_URL}" class="btn btn-line">LINE 諮詢</a></div>
        </div>
        """
        (out/slug/"index.html").write_text(f"<!doctype html><html>{get_head(name, GA4_ID, img, page_url)}<body>{detail_html}</body></html>", encoding="utf-8")
        
        card_html = f"""<a href="./{slug}/" class="card"><div class="card-img-box"><span class="area-tag">{esc(area)}</span><img src="{img}"></div><div class="card-info"><b>{esc(name)}</b><div class="price">{esc(price)}</div></div></a>"""
        items.append(card_html)
        area_map.setdefault(area, []).append(card_html.replace('./', '../../'))

    # 生成分類導航與首頁
    sorted_areas = sorted(area_map.keys())
    filter_html = f'<div class="filter-bar"><a href="{BASE_URL}/" class="filter-btn active">全部</a>'
    for area in sorted_areas: filter_html += f'<a href="{BASE_URL}/area/{urllib.parse.quote(area)}/" class="filter-btn">{area}</a>'
    filter_html += '</div>'

    (out/"index.html").write_text(f"<!doctype html><html>{get_head(SITE_TITLE, GA4_ID, '', f'{BASE_URL}/')}<body><div class='container'><div class='header'><h1>{SITE_TITLE}</h1></div>{filter_html}{''.join(items)}</div></body></html>", encoding="utf-8")
    
    # Sitemap 提升搜尋引擎收錄率
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for url in sitemap_urls: sitemap += f'  <url><loc>{url}</loc><lastmod>{datetime.now().strftime("%Y-%m-%d")}</lastmod></url>\n'
    sitemap += '</urlset>'
    (out/"sitemap.xml").write_text(sitemap, encoding="utf-8")

if __name__ == "__main__": build()
