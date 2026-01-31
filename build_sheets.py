import os, csv, requests, html, shutil, re, urllib.parse
from pathlib import Path
from datetime import datetime

# --- 1. 核心配置 ---
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQShAl0-TbUU0MQdYVe53im2T6lXQgh_7g-bdL6HHpIBFtA2yfIAMbPw4J9RgZUkROb9AAiMhnRC0kH/pub?output=csv"
MY_PHONE = "0938-615-351"
MY_LINE_URL = "https://line.me/ti/p/FDsMyAYDv"
SITE_TITLE = "林世塏｜台中地圖找房"
BASE_URL = "https://shihkailin.github.io/taichung-houses"
GA4_ID = "G-B7WP9BTP8X"

# --- 2. 品牌合規資訊 (已調小字體，不搶戲) ---
COMPANY_INFO = """
<div style="margin-top:30px; padding:15px; border-top:1px solid #f2f2f2; font-size:11px; color:#bbb; line-height:1.6; text-align:center;">
    英柏國際地產有限公司<br>
    中市地價二字第 1070029259 號<br>
    王一媖 經紀人 (103) 中市經紀字第 00678 號
</div>
"""

def esc(s): return html.escape(str(s or "").strip())

def get_final_img_url(url):
    url = str(url).strip()
    if not url: return "https://placehold.co/600x400?text=照片整理中"
    if not url.startswith("http"):
        return f"https://raw.githubusercontent.com/ShihKaiLin/taichung-houses/main/images/{url.lstrip('/')}"
    return url

def get_head(title, ga_id, is_home=False):
    ga = f"""<script async src="https://www.googletagmanager.com/gtag/js?id={ga_id}"></script><script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','{ga_id}');</script>""" if ga_id else ""
    filter_script = """
    <script>
    function filterArea(area) {
        document.querySelectorAll('.card').forEach(c => {
            c.style.display = (area === 'all' || c.getAttribute('data-area') === area) ? 'block' : 'none';
        });
        document.querySelectorAll('.filter-btn').forEach(b => {
            b.classList.toggle('active', b.getAttribute('onclick').includes(area));
        });
    }
    </script>
    """ if is_home else ""

    return f"""
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=0">
        <title>{esc(title)}</title>
        {ga}{filter_script}
        <style>
            :root {{ --alley-blue: #2A58AD; --alley-gray: #f2f4f7; --alley-dark: #333; }}
            body {{ font-family: 'PingFang TC', sans-serif; background: #fff; margin: 0; color: var(--alley-dark); }}
            .container {{ max-width: 480px; margin: auto; min-height: 100vh; padding-bottom: 120px; position: relative; box-shadow: 0 0 20px rgba(0,0,0,0.05); }}
            .header {{ padding: 25px 20px 10px; }}
            .header h1 {{ font-size: 20px; margin: 0; color: var(--alley-blue); font-weight: 900; }}
            .filter-bar {{ display: flex; gap: 8px; padding: 10px 20px; overflow-x: auto; background: #fff; position: sticky; top: 0; z-index: 100; border-bottom: 1px solid #eee; }}
            .filter-btn {{ padding: 6px 16px; background: var(--alley-gray); border-radius: 20px; color: #666; font-size: 13px; border: none; cursor: pointer; }}
            .filter-btn.active {{ background: var(--alley-blue); color: #fff; }}
            .card {{ display: block; text-decoration: none; color: inherit; margin: 15px 20px; border-radius: 12px; overflow: hidden; border: 1px solid #eee; transition: 0.2s; }}
            .card-img-box {{ position: relative; height: 220px; }}
            .card img {{ width: 100%; height: 100%; object-fit: cover; }}
            .area-tag {{ position: absolute; top: 10px; left: 10px; background: rgba(255,255,255,0.9); padding: 3px 8px; border-radius: 4px; font-size: 11px; color: var(--alley-blue); font-weight: bold; }}
            .card-info {{ padding: 15px; }}
            .card-info b {{ font-size: 18px; display: block; margin-bottom: 5px; }}
            .price {{ color: #e53e3e; font-size: 22px; font-weight: 800; }}
            .action-bar {{ position: fixed; bottom: 0; left: 50%; transform: translateX(-50%); width: 100%; max-width: 480px; padding: 10px 15px 30px; display: flex; gap: 8px; background: #fff; border-top: 1px solid #eee; z-index: 200; }}
            .btn {{ flex: 1; text-align: center; padding: 14px; border-radius: 8px; text-decoration: none; font-weight: bold; color: #fff; font-size: 14px; }}
            .btn-call {{ background: var(--alley-dark); }}
            .btn-line {{ background: #00B900; }}
            .back-btn {{ position: absolute; top: 15px; left: 15px; background: #fff; padding: 5px 12px; border-radius: 5px; text-decoration: none; font-size: 13px; z-index: 10; border: 1px solid #ddd; }}
        </style>
    </head>
    """

def build():
    out = Path(".") 
    for p in out.glob("p*"):
        if p.is_dir() and re.match(r'^p\d+$', p.name): shutil.rmtree(p)

    res = requests.get(SHEET_CSV_URL); res.encoding = 'utf-8-sig'
    reader = csv.DictReader(res.text.splitlines())

    items, areas = [], set()

    for i, row in enumerate(reader):
        row = {str(k).strip().replace('\ufeff', ''): str(v).strip() for k, v in row.items() if k}
        status = str(row.get("狀態", "")).upper()
        if status not in ["ON", "TRUE"] or not row.get("案名"): continue

        name, area, price, addr = row.get("案名", ""), row.get("區域", ""), row.get("價格", ""), row.get("地址", "")
        img = get_final_img_url(row.get("圖片網址", ""))
        areas.add(area)
        slug = f"p{i}"
        (out/slug).mkdir(exist_ok=True)
        
        ext_url = row.get("外部網址", "")
        ext_btn = f'<a href="{ext_url}" target="_blank" style="display:block; text-align:center; padding:12px; border:1.5px solid var(--alley-blue); border-radius:8px; color:var(--alley-blue); text-decoration:none; margin-top:15px; font-weight:bold; font-size:14px;">🔗 查看詳細建坪與格局</a>' if ext_url else ""
        map_link = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(addr if addr else name)}"

        detail_html = f"""
        <div class="container">
            <a href="../" class="back-btn">← 返回列表</a>
            <img src="{img}" style="width:100%; height:320px; object-fit:cover;">
            <div style="padding:25px;">
                <span style="color:var(--alley-blue); font-weight:bold; font-size:12px;">{esc(area)}</span>
                <h1 style="font-size:24px; margin:5px 0; font-weight:900;">{esc(name)}</h1>
                <div class="price">{esc(price)}</div>
                <div style="margin-top:18px; background:var(--alley-gray); padding:18px; border-radius:10px; font-size:15px; color:#444;">
                    {esc(row.get("描述","")).replace('、', '<br>• ')}
                </div>
                {ext_btn}
                <a href="{map_link}" target="_blank" style="display:block; text-align:center; padding:12px; background:var(--alley-blue); border-radius:8px; color:#fff; text-decoration:none; margin-top:10px; font-weight:bold; font-size:14px;">📍 開啟 Google 地圖導航</a>
                {COMPANY_INFO}
            </div>
            <div class="action-bar"><a href="tel:{MY_PHONE}" class="btn btn-call">致電聯繫</a><a href="{MY_LINE_URL}" class="btn btn-line">LINE 諮詢</a></div>
        </div>
        """
        (out/slug/"index.html").write_text(f"<!doctype html><html>{get_head(name, GA4_ID)}<body>{detail_html}</body></html>", encoding="utf-8")
        
        items.append(f'<a href="./{slug}/" class="card" data-area="{esc(area)}"><div class="card-img-box"><span class="area-tag">{esc(area)}</span><img src="{img}"></div><div class="card-info"><b>{esc(name)}</b><div class="price">{esc(price)}</div></div></a>')

    filter_html = '<div class="filter-bar"><button class="filter-btn active" onclick="filterArea(\'all\')">全部區域</button>'
    for a in sorted(list(areas)):
        filter_html += f'<button class="filter-btn" onclick="filterArea(\'{esc(a)}\')">{esc(a)}</button>'
    filter_html += '</div>'

    (out/"index.html").write_text(f"<!doctype html><html>{get_head(SITE_TITLE, GA4_ID, True)}<body><div class='container'><div class='header'><h1>{SITE_TITLE}</h1></div>{filter_html}{''.join(items)}{COMPANY_INFO}</div></body></html>", encoding="utf-8")

if __name__ == "__main__": build()
