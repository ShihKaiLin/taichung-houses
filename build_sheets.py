import os, csv, requests, html, shutil
from pathlib import Path

# --- 核心配置：使用您提供的最新網址 ---
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQShAl0-TbUU0MQdYVe53im2T6lXQgh_7g-bdL6HHpIBFtA2yfIAMbPw4J9RgZUkROb9AAiMhnRC0kH/pub?output=csv"
MY_PHONE = "0938-615-351"
MY_LINE_URL = "https://line.me/ti/p/FDsMyAYDv"
SITE_TITLE = "台中房產雲端看板"

def esc(s): return html.escape(str(s or "").strip())

def build():
    out = Path("site")
    if out.exists(): shutil.rmtree(out)
    out.mkdir()

    print("🚀 正在從雲端抓取房產資料...")
    res = requests.get(SHEET_CSV_URL)
    res.encoding = 'utf-8-sig'
    
    # 過濾掉空白行並清理字元
    lines = [line.strip() for line in res.text.splitlines() if line.strip()]
    reader = csv.DictReader(lines)

    items = []
    for i, row in enumerate(reader):
        # 自動清理欄位名稱的隱藏空白（這是之前出錯的主因）
        clean_row = {str(k).strip(): str(v).strip() for k, v in row.items() if k}
        
        # 只抓取狀態為 ON 的物件
        if clean_row.get("狀態") != "ON":
            continue

        # 根據您的截圖欄位進行對接
        name = clean_row.get("案名", "精選物件")
        area = clean_row.get("區域", "台中")
        price = clean_row.get("價格", "面議")
        desc = clean_row.get("描述", "")
        img_url = clean_row.get("圖片網址", "")
        address = clean_row.get("地址", "")

        slug = f"p{i}"
        (out/slug).mkdir()
        
        # 製作精美的物件頁面
        page_html = f"""
        <div style='padding:20px; font-family:sans-serif; max-width:500px; margin:auto; background:#fff;'>
            {f'<img src="{img_url}" style="width:100%; border-radius:10px;">' if "http" in img_url else '<div style="background:#eee; height:200px; border-radius:10px; text-align:center; line-height:200px; color:#aaa;">暫無圖片</div>'}
            <h1 style='font-size:22px; margin-top:15px;'>{esc(name)}</h1>
            <p style='color:#e67e22; font-size:24px; font-weight:bold;'>{esc(price)}</p>
            <p style='color:#777;'>📍 {esc(area)} | {esc(address)}</p>
            <hr style='border:0; border-top:1px solid #eee;'>
            <div style='line-height:1.6; color:#444;'>{esc(desc)}</div>
            <div style='margin-top:30px; display:flex; gap:10px;'>
                <a href="tel:{MY_PHONE}" style="flex:1; background:#e67e22; color:#fff; text-align:center; padding:15px; text-decoration:none; border-radius:50px; font-weight:bold;">📞 撥打電話</a>
                <a href="{MY_LINE_URL}" style="flex:1; background:#00b900; color:#fff; text-align:center; padding:15px; text-decoration:none; border-radius:50px; font-weight:bold;">💬 LINE 諮詢</a>
            </div>
        </div>
        """
        (out/slug/"index.html").write_text(f"<!doctype html><html><head><meta name='viewport' content='width=device-width,initial-scale=1'></head><body style='margin:0; background:#f5f5f5;'>{page_html}</body></html>", encoding="utf-8")
        items.append(f"<li style='margin-bottom:15px; list-style:none; background:#fff; padding:15px; border-radius:10px; box-shadow:0 2px 5px rgba(0,0,0,0.1);'><a href='./{slug}/' style='text-decoration:none; color:#333; display:block;'><b>[{esc(area)}] {esc(name)}</b><br><span style='color:#e67e22;'>{esc(price)}</span></a></li>")

    # 生成首頁
    home_html = f"<div style='padding:20px; font-family:sans-serif; max-width:500px; margin:auto;'><h2>🏠 {SITE_TITLE}</h2><ul style='padding:0;'>{''.join(items)}</ul></div>"
    (out/"index.html").write_text(f"<!doctype html><html><head><meta name='viewport' content='width=device-width,initial-scale=1'></head><body style='margin:0; background:#f5f5f5;'>{home_html}</body></html>", encoding="utf-8")
    print(f"✅ 成功生成了 {len(items)} 個物件！")

if __name__ == "__main__": build()
