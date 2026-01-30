import os, csv, requests, html, shutil
from pathlib import Path

# =========================================================
# 配置區：請填入你的資料
# =========================================================
# 填入你從 Google Sheets 發佈後取得的 CSV 網址
SHEET_CSV_URL ="https://docs.google.com/spreadsheets/d/e/2PACX-1vQne8IK7y_pwL0rqXJ0zZIa5qZyj1fly4SZu13FmSipcVORrdBP9at1tQQY18-v290vN6mUhy_TizCS/pub?output=csv"
# 聯絡資訊
MY_PHONE = "0938-615-351" 
MY_LINE_URL = "https://line.me/ti/p/FDsMyAYDv"
SITE_TITLE = "台中房產雲端看板"

# GA4 衡量 ID (選填，填入後可在手機看流量)
GA4_ID = "" 

def esc(s): return html.escape(str(s or ""))

def render_base(title, desc, body_html):
    ga_code = ""
    if GA4_ID:
        ga_code = f"""
        <script async src="https://www.googletagmanager.com/gtag/js?id={GA4_ID}"></script>
        <script>
          window.dataLayer = window.dataLayer || [];
          function gtag(){{dataLayer.push(arguments);}}
          gtag('js', new Date()); gtag('config', '{GA4_ID}');
        </script>
        """
    return f"""<!doctype html><html lang="zh-Hant"><head>
    {ga_code}
    <meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
    <title>{esc(title)}</title><meta name="description" content="{esc(desc[:150])}">
    <style>
        body{{font-family:-apple-system,sans-serif; background:#f0f2f5; margin:0; padding-bottom:100px; color:#333;}}
        .wrap{{max-width:600px; margin:0 auto; background:#fff; min-height:100vh; box-shadow:0 0 10px rgba(0,0,0,0.1);}}
        img{{width:100%; display:block;}}
        .info{{padding:20px;}}
        .tag{{background:#e67e22; color:#fff; padding:4px 10px; border-radius:4px; font-size:13px;}}
        .price{{color:#e67e22; font-size:24px; font-weight:bold; margin:10px 0;}}
        .note{{white-space:pre-wrap; background:#f9f9f9; padding:15px; border-radius:8px; line-height:1.7;}}
        .fab{{position:fixed; bottom:20px; left:50%; transform:translateX(-50%); width:90%; max-width:400px; display:flex; gap:10px; z-index:100;}}
        .btn{{flex:1; text-align:center; padding:15px; border-radius:50px; color:#fff; font-weight:bold; text-decoration:none; box-shadow:0 4px 10px rgba(0,0,0,0.2);}}
    </style></head><body><div class="wrap">{body_html}</div></body></html>"""

def build():
    out = Path("site")
    if out.exists(): shutil.rmtree(out)
    out.mkdir(); (out/"imgs").mkdir()

    # 抓取 Google Sheets 資料
    try:
        response = requests.get(SHEET_CSV_URL)
        response.encoding = 'utf-8'
        reader = csv.DictReader(response.text.splitlines())
    except Exception as e:
        print(f"抓取失敗: {e}"); return

    items = []
    for i, row in enumerate(reader):
        if row.get("狀態") == "OFF": continue

        name = row.get("案名", "未命名物件")
        area = row.get("區域", "台中市")
        price = row.get("價格", "面議")
        img_url = row.get("圖片網址", "")
        desc = row.get("描述", "")
        addr = row.get("地址", "")

        slug = f"p{i}"
        (out/slug).mkdir()
        
        map_btn = f'<a href="https://www.google.com/maps/search/?api=1&query={addr}" class="btn" style="background:#4285F4;">導航</a>' if addr else ""
        
        body = f"""
        {f'<img src="{img_url}">' if img_url else ''}
        <div class="info">
            <span class="tag">{esc(area)}</span>
            <h1>{esc(name)}</h1>
            <div class="price">{esc(price)} 萬</div>
            <hr>
            <h3>物件描述</h3>
            <div class="note">{esc(desc)}</div>
        </div>
        <div class="fab">
            <a href="tel:{MY_PHONE}" class="btn" style="background:#e67e22;">撥打電話</a>
            {map_btn}
            <a href="{MY_LINE_URL}" class="btn" style="background:#00b900;">LINE 諮詢</a>
        </div>
        """
        (out/slug/"index.html").write_text(render_base(name, desc, body), encoding="utf-8")
        items.append(f'<li><a href="./{slug}/"><b>[{esc(area)}] {esc(name)}</b> - {esc(price)}萬</a></li>')

    home_body = f"<h1>🏠 {SITE_TITLE}</h1><ul>{''.join(items)}</ul>"
    (out/"index.html").write_text(render_base(SITE_TITLE, "台中物件清單", home_body), encoding="utf-8")
    print("✅ 雲端網站更新完成！")


if __name__ == "__main__": build()

