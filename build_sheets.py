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
GA4_ID = "" # 若有 GA4 ID (如 G-XXXXX) 請填入即可啟用追蹤

def esc(s): return html.escape(str(s or "").strip())

def convert_google_drive_url(url):
    """自動將 Google Drive 分享連結轉換為直接圖片連結"""
    if "drive.google.com" in url:
        file_id = ""
        if "id=" in url:
            file_id = url.split("id=")[1].split("&")[0]
        elif "/d/" in url:
            file_id = url.split("/d/")[1].split("/")[0]
        if file_id:
            return f"https://drive.google.com/uc?export=view&id={file_id}"
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
            body {{ font-family: 'PingFang TC', 'Microsoft JhengHei', sans-serif; background: var(--light); margin: 0; color: var(--dark); line-height: 1.6; }}
            .container {{ max-width: 500px; margin: auto; background: #fff; min-height: 100vh; padding-bottom: 120px; position: relative; box-shadow: 0 0 30px rgba(0,0,0,0.05); }}
            .header {{ padding: 60px 25px 30px; background: #fff; text-align: center; }}
            .header h1 {{ font-size: 26px; font-weight: 900; margin: 0; letter-spacing: 1px; }}
            
            /* 列表卡片美化 */
            .card {{ display: flex; text-decoration: none; color: inherit; margin: 15px 20px; background: #fff; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.05); transition: 0.3s; border: 1px solid #f0f0f0; }}
            .card:hover {{ transform: translateY(-3px); box-shadow: 0 8px 25px rgba(0,0,0,0.1); }}
            .card img {{ width: 120px; height: 120px; object-fit: cover; background: #f5f5f5; }}
            .card-info {{ padding: 15px; flex: 1; display: flex; flex-direction: column; justify-content: center; }}
            .card-area {{ font-size: 12px; color: var(--primary); font-weight: bold; text-transform: uppercase; }}
            .card-name {{ font-size: 16px; margin: 4px 0; font-weight: 700; color: #333; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }}
            .price {{ color: var(--danger); font-size: 20px; font-weight: 900; }}
            
            /* 專業分析區塊 */
            .insight-box {{ margin: 20px; padding: 25px; background: #fdfaf5; border-left: 5px solid var(--primary); border-radius: 8px; font-size: 15px; color: #444; }}
            .insight-box h3 {{ margin: 0 0 10px; color: var(--dark); font-size: 18px; font-weight: 900; }}
            
            /* 底部動作列 */
            .action-bar {{ position: fixed; bottom: 0; left: 50%; transform: translateX(-50%); width: 100%; max-width: 500px; padding: 15px 20px 30px; display: flex; gap: 10px; background: rgba(255,255,255,0.9); backdrop-filter: blur(10px); box-sizing: border-box; z-index: 100; border-top: 1px solid #eee; }}
            .btn {{ flex: 1; text-align: center; padding: 15px; border-radius: 50px; text-decoration: none; font-weight: bold; font-size: 15px; color: #fff; transition: 0.2s; }}
            .btn-call {{ background: var(--dark); }}
            .btn-line {{ background: #06c755; }}
        </style>
    </head>
    """

def build():
    out = Path("site")
    if out.exists(): shutil.rmtree(out)
    for d in ["area", "sell"]: (out/d).mkdir(parents=True)

    print("🚀 啟動『林世塏 x 石開林』旗艦版部署...")
    res = requests.get(SHEET_CSV_URL); res.encoding = 'utf-8-sig'
    reader = csv.DictReader(res.text.splitlines())

    items, area_map = [], {}
    for i, row in enumerate(reader):
        row = {str(k).strip().replace('\ufeff', ''): str(v).strip() for k, v in row.items() if k}
        if row.get("狀態") != "ON": continue

        name, area, price = row.get("案名", "精選物件"), row.get("區域", "台中"), row.get("價格", "面議")
        desc_raw = row.get("描述", "")
        desc_html = desc_raw.replace('\\n', '<br>').replace('、', '<br>• ')
        img = convert_google_drive_url(row.get("圖片網址", "")) or "https://via.placeholder.com/800x600?text=House"
        addr = row.get("地址", "台中市")
        
        slug = f"p{i}"
        (out/slug).mkdir()
        page_url = f"{BASE_URL}/{slug}/"
        
        # 物件詳細頁 (旗艦視覺)
        detail_html = f"""
        <div class="container">
            <img src="{img}" style="width:100%; height:350px; object-fit:cover;" onerror="this.src='https://via.placeholder.com/800x600?text=圖片載入中'">
            <div style="padding:30px 25px; margin-top:-35px; background:#fff; border-radius:30px 30px 0 0; position:relative;">
                <span style="background:var(--light); padding:5px 15px; border-radius:50px; font-size:13px; color:var(--primary); font-weight:bold;">📍 {esc(area)}</span>
                <h1 style="font-size:26px; margin:15px 0 10px; font-weight:900; line-height:1.3;">{esc(name)}</h1>
                <div class="price" style="font-size:28px; margin-bottom:20px;">{esc(price)}</div>
                <div style="padding:20px; background:var(--light); border-radius:15px; font-size:16px; color:#444;">
                    <b style="color:var(--dark);">🏠 物件特色：</b><br>
                    <div style="margin-top:10px; line-height:1.8;">• {desc_html}</div>
                </div>
                <p style="margin-top:20px; color:#999; font-size:14px;">📍 地址：{esc(addr)}</p>
            </div>
            <div class="action-bar">
                <a href="tel:{MY_PHONE}" class="btn btn-call">📞 撥打電話</a>
                <a href="{MY_LINE_URL}" class="btn btn-line">💬 LINE 諮詢</a>
            </div>
        </div>
        """
        (out/slug/"index.html").write_text(f"<!doctype html><html lang='zh-tw'>{get_head(name, desc_raw, img, page_url)}<body>{detail_html}</body></html>", encoding="utf-8")
        
        card = f"""
        <a href="../../{slug}/" class="card">
            <img src="{img}" loading="lazy" onerror="this.src='https://via.placeholder.com/150?text=House'">
            <div class="card-info">
                <span class="card-area">{esc(area)}</span>
                <b class="card-name">{esc(name)}</b>
                <div class="price">{esc(price)}</div>
            </div>
        </a>
        """
        items.append(card.replace('../../', './'))
        area_map.setdefault(area, []).append(card)

    # 區域與成交分析頁面 (SEO 截流)
    for area, cards in area_map.items():
        area_slug = urllib.parse.quote(area)
        (out/"area"/area_slug).mkdir(exist_ok=True)
        (out/"area"/area_slug/"index.html").write_text(f"<!doctype html><html>{get_head(f'{area}買房推薦-林世塏', f'正在找{area}的優質房產嗎？', '', '')}<body><div class='container'><div class='header'><h1>{area}熱門物件</h1></div><div class='insight-box'><h3>📍 {area} 區域分析</h3><p>林世塏深耕{area}，為您精選最高 CP 值物件。</p></div>{''.join(cards)}</div></body></html>", encoding="utf-8")

    # 旗艦版首頁
    (out/"index.html").write_text(f"<!doctype html><html>{get_head(SITE_TITLE, SLOGAN, '', f'{BASE_URL}/')}<body><div class='container'><div class='header'><h1>{SITE_TITLE}</h1><p style='color:var(--primary); font-weight:600;'>{SLOGAN}</p></div>{''.join(items)}</div></body></html>", encoding="utf-8")
    print(f"✅ 部署完成！共生成 {len(items)} 個旗艦頁面。")

if __name__ == "__main__": build()
