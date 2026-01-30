import os, csv, requests, html, shutil
from pathlib import Path

# --- 核心配置 ---
# 請確認這是您「發佈到網路」後取得的 CSV 網址
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQne8IK7y_pwL0rqXJ0zZIa5qZyj1fly4SZu13FmSipcVORrdBP9at1tQQY18-v290vN6mUhy_TizCS/pub?output=csv"
MY_PHONE = "0938-615-351"
MY_LINE_URL = "https://line.me/ti/p/FDsMyAYDv"
SITE_TITLE = "台中房產雲端看板"

def esc(s): return html.escape(str(s or "").strip())

def build():
    out = Path("site")
    if out.exists(): shutil.rmtree(out)
    out.mkdir()

    # 抓取資料
    res = requests.get(SHEET_CSV_URL)
    res.encoding = 'utf-8'
    
    # 確保抓到標題列並過濾空行
    lines = [line for line in res.text.splitlines() if line.strip()]
    reader = csv.DictReader(lines)

    items = []
    for i, row in enumerate(reader):
        # 清除欄位名稱兩端的空格
        row = {k.strip(): v for k, v in row.items() if k}
        
        # 只抓取狀態為 ON 的物件
        if row.get("狀態") != "ON": continue

        name = row.get("案名", "未命名物件")
        area = row.get("區域", "台中")
        price = row.get("價格", "面議")
        desc = row.get("描述", "")
        img_url = row.get("圖片網址", "")

        slug = f"p{i}"
        (out/slug).mkdir()
        
        # 簡單好看的物件頁面樣板
        body_html = f"""
        <div style='padding:20px; font-family:sans-serif;'>
            {f'<img src="{img_url}" style="width:100%; border-radius:10px;">' if "http" in img_url else ""}
            <h1 style='color:#333;'>{esc(name)}</h1>
            <p style='color:#e67e22; font-size:24px; font-weight:bold;'>{esc(price)}</p>
            <p style='background:#f9f9f9; padding:15px; line-height:1.6;'>{esc(desc)}</p>
            <div style='margin-top:30px;'>
                <a href="tel:{MY_PHONE}" style="display:block; background:#e67e22; color:#fff; text-align:center; padding:15px; text-decoration:none; border-radius:50px; margin-bottom:10px;">撥打電話</a>
                <a href="{MY_LINE_URL}" style="display:block; background:#00b900; color:#fff; text-align:center; padding:15px; text-decoration:none; border-radius:50px;">LINE 諮詢</a>
            </div>
        </div>
        """
        (out/slug/"index.html").write_text(f"<!doctype html><html><head><meta name='viewport' content='width=device-width,initial-scale=1'></head><body style='margin:0; background:#f0f2f5;'>{body_html}</body></html>", encoding="utf-8")
        items.append(f"<li style='margin-bottom:15px; list-style:none; background:#fff; padding:15px; border-radius:10px;'><a href='./{slug}/' style='text-decoration:none; color:#333; font-weight:bold;'>[{esc(area)}] {esc(name)} - {esc(price)}</a></li>")

    # 生成首頁
    home_html = f"<div style='padding:20px; font-family:sans-serif;'><h1>🏠 {SITE_TITLE}</h1><ul style='padding:0;'>{''.join(items)}</ul></div>"
    (out/"index.html").write_text(f"<!doctype html><html><head><meta name='viewport' content='width=device-width,initial-scale=1'></head><body style='margin:0; background:#f0f2f5;'>{home_html}</body></html>", encoding="utf-8")
    print("✅ 網頁生成完畢")

if __name__ == "__main__": build()
