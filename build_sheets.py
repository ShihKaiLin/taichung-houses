import os, csv, requests, html, shutil
from pathlib import Path

# --- 核心配置 ---
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQne8IK7y_pwL0rqXJ0zZIa5qZyj1fly4SZu13FmSipcVORrdBP9at1tQQY18-v290vN6mUhy_TizCS/pub?output=csv"
MY_PHONE = "0938-615-351"
MY_LINE_URL = "https://line.me/ti/p/FDsMyAYDv"
SITE_TITLE = "台中房產雲端看板"

def esc(s): return html.escape(str(s or "").strip())

def build():
    out = Path("site")
    if out.exists(): shutil.rmtree(out)
    out.mkdir()

    # 抓取並解碼資料
    res = requests.get(SHEET_CSV_URL)
    res.encoding = 'utf-8'
    
    # 強力過濾：移除所有空白行，並清除每行兩端的隱藏字元
    lines = [line.strip() for line in res.text.splitlines() if line.strip()]
    
    # 讀取 CSV
    reader = csv.DictReader(lines)

    items = []
    for i, row in enumerate(reader):
        # 終極過濾：清除標題與內容的所有隱藏空格
        clean_row = {str(k).strip(): str(v).strip() for k, v in row.items() if k}
        
        # 只抓取狀態為 ON 的物件 (您的表格目前已統一為 ON)
        if clean_row.get("狀態") != "ON": continue

        name = clean_row.get("案名", "未命名物件")
        area = clean_row.get("區域", "台中")
        price = clean_row.get("價格", "面議")
        desc = clean_row.get("描述", "")
        img_url = clean_row.get("圖片網址", "")

        slug = f"p{i}"
        (out/slug).mkdir()
        
        # 房仲專用物件頁樣板
        body_content = f"""
        <div style='padding:20px; font-family:sans-serif; max-width:600px; margin:auto; background:#fff;'>
            {f'<img src="{img_url}" style="width:100%; border-radius:10px;">' if "http" in img_url else ""}
            <h1 style='color:#333; font-size:22px;'>{esc(name)}</h1>
            <p style='color:#e67e22; font-size:24px; font-weight:bold;'>{esc(price)}</p>
            <div style='background:#f9f9f9; padding:15px; border-radius:8px; line-height:1.7; color:#555;'>{esc(desc)}</div>
            <div style='margin-top:30px; display:flex; gap:10px;'>
                <a href="tel:{MY_PHONE}" style="flex:1; background:#e67e22; color:#fff; text-align:center; padding:15px; text-decoration:none; border-radius:50px; font-weight:bold;">撥打電話</a>
                <a href="{MY_LINE_URL}" style="flex:1; background:#00b900; color:#fff; text-align:center; padding:15px; text-decoration:none; border-radius:50px; font-weight:bold;">LINE 諮詢</a>
            </div>
        </div>
        """
        (out/slug/"index.html").write_text(f"<!doctype html><html><head><meta name='viewport' content='width=device-width,initial-scale=1'></head><body style='margin:0; background:#f0f2f5;'>{body_content}</body></html>", encoding="utf-8")
        items.append(f"<li style='margin-bottom:15px; list-style:none; background:#fff; padding:15px; border-radius:10px; box-shadow:0 2px 5px rgba(0,0,0,0.05);'><a href='./{slug}/' style='text-decoration:none; color:#333; display:block;'><b>[{esc(area)}] {esc(name)}</b><br><span style='color:#e67e22;'>{esc(price)}</span></a></li>")

    # 生成列表首頁
    home_content = f"<div style='padding:20px; font-family:sans-serif; max-width:600px; margin:auto;'><h2>🏠 {SITE_TITLE}</h2><ul style='padding:0;'>{''.join(items)}</ul></div>"
    (out/"index.html").write_text(f"<!doctype html><html><head><meta name='viewport' content='width=device-width,initial-scale=1'></head><body style='margin:0; background:#f0f2f5;'>{home_content}</body></html>", encoding="utf-8")
    print("✅ 網站更新成功！")

if __name__ == "__main__": build()
