import os, csv, requests, html, shutil
from pathlib import Path

# --- 請確認使用您最新的發佈網址 ---
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQShAl0-TbUU0MQdYVe53im2T6lXQgh_7g-bdL6HHpIBFtA2yfIAMbPw4J9RgZUkROb9AAiMhnRC0kH/pub?output=csv"
MY_PHONE = "0938-615-351"
MY_LINE_URL = "https://line.me/ti/p/FDsMyAYDv"
SITE_TITLE = "台中房產雲端看板"

def esc(s): return html.escape(str(s or "").strip())

def build():
    out = Path("site")
    if out.exists(): shutil.rmtree(out)
    out.mkdir()

    print(f"🚀 開始抓取資料...")
    res = requests.get(SHEET_CSV_URL)
    res.encoding = 'utf-8-sig'
    
    # 診斷：如果抓到的內容太短，代表網址發佈可能沒成功
    if len(res.text) < 50:
        print("❌ 錯誤：抓到的資料太短，請確認 Google 表格是否已『發佈到網路』而非只是共用連結。")
        print(f"內容：{res.text}")
        return

    lines = [line.strip() for line in res.text.splitlines() if line.strip()]
    reader = csv.DictReader(lines)
    
    items = []
    for i, row in enumerate(reader):
        # 自動清除欄位名稱的所有隱藏空白
        row = {str(k).strip(): str(v).strip() for k, v in row.items() if k}
        
        # 診斷：印出第一行抓到的標題，讓我們知道機器人看到了什麼
        if i == 0:
            print(f"✅ 機器人讀取到的標題為：{list(row.keys())}")

        if row.get("狀態") != "ON": continue

        name = row.get("案名", "未命名")
        area = row.get("區域", "台中")
        price = row.get("價格", "面議")
        desc = row.get("描述", "")
        img_url = row.get("圖片網址", "")

        slug = f"p{i}"
        (out/slug).mkdir()
        
        # 生成物件網頁
        body = f"<div style='padding:20px;'><h1>{esc(name)}</h1><p style='font-size:24px; color:orange;'>{esc(price)}</p><p>{esc(desc)}</p><a href='tel:{MY_PHONE}' style='display:block; background:orange; color:white; padding:15px; text-align:center; text-decoration:none; border-radius:50px;'>撥打電話</a></div>"
        (out/slug/"index.html").write_text(f"<!doctype html><html><head><meta name='viewport' content='width=device-width,initial-scale=1'></head><body>{body}</body></html>", encoding="utf-8")
        items.append(f"<li><a href='./{slug}/'>[{esc(area)}] {esc(name)}</a></li>")

    # 生成首頁
    home = f"<div style='padding:20px;'><h1>🏠 {SITE_TITLE}</h1><ul>{''.join(items)}</ul></div>"
    (out/"index.html").write_text(f"<!doctype html><html><head><meta name='viewport' content='width=device-width,initial-scale=1'></head><body>{home}</body></html>", encoding="utf-8")
    print(f"✅ 成功處理了 {len(items)} 個物件！")

if __name__ == "__main__":
    build()
