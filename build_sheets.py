import os, csv, requests, html, shutil, re, urllib.parse, json
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup

# ============================================================
# 1. 核心品牌與監督配置
# ============================================================
EVOLUTION_MODE = "MANUAL"
CURRENT_THEME = "GOLD" # 可選: GOLD, SLATE, SNOW

PROJECT_NAME = "taichung-houses"
BASE_URL = f"https://shihkailin.github.io/{PROJECT_NAME}"
SITE_TITLE = "SK-L 大台中房地產"
MY_NAME, MY_PHONE = "林世塏", "0938-615-351"
MY_LINE_URL = "https://line.me/ti/p/FDsMyAYDv_" 
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQShAl0-TbUU0MQdYVe53im2T6lXQgh_7g-bdL6HHpIBFtA2yfIAMbPw4J9RgZUkROb9AAiMhnRC0kH/pub?output=csv"
MAPS_API_KEY = os.getenv("MAPS_API_KEY", "AIzaSyDzgnI2Ucv622CRkWwo2GE5JRrs_Y4HQY0")
IMG_RAW_BASE = f"https://raw.githubusercontent.com/ShihKaiLin/{PROJECT_NAME}/main/images/"
POSTS_DIR, REPORT_DIR = Path("posts"), Path("market_reports")

THEMES = {
    "GOLD": {"p": "#1A1C1E", "a": "#C5A059", "bg": "#FDFDFD", "l": "奢華置產"},
    "SLATE": {"p": "#0F172A", "a": "#64748B", "bg": "#F8FAFC", "l": "專業法規"},
    "SNOW": {"p": "#272727", "a": "#9CA3AF", "bg": "#FFFFFF", "l": "極簡質感"}
}
sel = THEMES.get(CURRENT_THEME, THEMES["GOLD"])

# ============================================================
# 2. 數據與工具函數 (嚴格對齊，解決 IndentationError)
# ============================================================
def esc(s): return html.escape(str(s or "").strip())
def norm(s): return str(s or "").strip().replace("\ufeff", "")
def get_num(s):
    nums = re.findall(r'\d+\.?\d*', str(s).replace(',', ''))
    return float(nums[0]) if nums else 0

def normalize_imgs(img_field):
    if not img_field: return ["https://placehold.co/1200x800?text=SK-L"]
    raw_list = re.split(r'[|｜]+', str(img_field))
    return [i if i.startswith("http") else f"{IMG_RAW_BASE}{i.lstrip('/')}" for i in raw_list if i.strip()]

# ============================================================
# 3. 視覺系統 (解決 SyntaxError: single '}' is not allowed)
# ============================================================
CSS_STYLE = f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;600;800&family=Noto+Sans+TC:wght@300;500;900&display=swap');
    :root {{ --primary: {sel['p']}; --accent: {sel['a']}; --bg: {sel['bg']}; --ease: cubic-bezier(0.2, 1, 0.3, 1); }}
    body {{ font-family: 'Inter', 'Noto Sans TC', sans-serif; margin: 0; background: var(--bg); color: #2C2E30; -webkit-font-smoothing: antialiased; }}
    .container {{ width: 100%; max-width: 1400px; margin: auto; background: #fff; min-height: 100vh; position: relative; padding-bottom: 180px; }}
    .header {{ background: rgba(255,255,255,0.85); backdrop-filter: blur(20px); padding: 30px 60px; display: flex; justify-content: space-between; align-items: center; position: sticky; top: 0; z-index: 1000; border-bottom: 1px solid rgba(0,0,0,0.05); }}
    .logo {{ font-weight: 800; font-size: 22px; letter-spacing: 4px; color: var(--primary); text-decoration: none; text-transform: uppercase; }}
    #map {{ height: 500px; background: #f0f0f0; width: 100%; filter: grayscale(100%) invert(5%) contrast(90%); }}
    .search-box {{ background: #FFFFFF; padding: 35px 50px; margin: -60px auto 0; border-radius: 30px; box-shadow: 0 30px 80px rgba(0,0,0,0.08); position: relative; z-index: 10; width: 88%; display: flex; flex-wrap: wrap; align-items: flex-end; gap: 30px; box-sizing: border-box; }}
    .search-item {{ flex: 1; min-width: 180px; display: flex; flex-direction: column; gap: 10px; }}
    .search-label {{ font-size: 10px; font-weight: 700; color: var(--accent); text-transform: uppercase; letter-spacing: 2px; }}
    .search-select, .search-input {{ padding: 15px 0; border: none; border-bottom: 1.5px solid #E5E7EB; font-size: 16px; background: transparent; outline: none; transition: 0.3s; font-weight: 500; }}
    .search-btn {{ background: var(--primary); color: #fff; border: none; padding: 18px 45px; border-radius: 12px; font-weight: 700; font-size: 15px; cursor: pointer; transition: 0.3s; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(380px, 1fr)); gap: 60px; padding: 100px 60px; }}
    .card {{ overflow: hidden; background: #fff; display: flex; flex-direction: column; transition: var(--ease); text-decoration: none; color: inherit; }}
    .card img {{ width: 100%; height: 320px; object-fit: cover; border-radius: 4px; }}
    .card-body {{ padding: 30px 0; }}
    .card-title {{ font-size: 22px; font-weight: 700; color: var(--primary); margin: 0; }}
    .card-price {{ color: var(--primary); font-weight: 300; font-size: 32px; margin-top: 15px; }}
    .action-bar {{ position: fixed; bottom: 40px; left: 50%; transform: translateX(-50%); width: 90%; max-width: 600px; padding: 15px; display: flex; gap: 15px; background: rgba(26, 28, 30, 0.95); backdrop-filter: blur(15px); border-radius: 20px; z-index: 10000; box-shadow: 0 25px 50px rgba(0,0,0,0.3); }}
    .btn {{ flex: 1; text-align: center; padding: 18px; border-radius: 12px; text-decoration: none; font-weight: 700; color: #fff; font-size: 15px; }}
    .btn-call {{ background: transparent; border: 1px solid rgba(255,255,255,0.2); }}
    .btn-line {{ background: #06C755; }}
    .badge {{ display: inline-block; padding: 6px 14px; border: 1px solid #E5E7EB; color: #9CA3AF; border-radius: 4px; font-size: 11px; font-weight: 600; margin: 0 8px 8px 0; }}
</style>
"""

# ============================================================
# 4. 情報中心與建置流程
# ============================================================
class SKL_Researcher:
    def fetch_latest_intel(self):
        REPORT_DIR.mkdir(exist_ok=True)
        report_file = REPORT_DIR / f"intel_{datetime.now().strftime('%Y%m%d')}.txt"
        print(f"🔍 掃描台中房市新聞...")
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(f"SK-L 地產情報 ({datetime.now().strftime('%Y-%m-%d')})\n\n")
            try:
                headers = {"User-Agent":"Mozilla/5.0"}
                res = requests.get("https://news.591.com.tw/list/taichung", timeout=10, headers=headers)
                soup = BeautifulSoup(res.text, 'html.parser')
                for t in soup.find_all(['h2', 'h3'])[:5]:
                    f.write(f"- {t.get_text().strip()}\n")
            except:
                f.write("- 暫時無法獲取最新新聞。\n")

class SKL_Builder:
    def __init__(self):
        self.items, self.map_data, self.urls = [], [], [f"{BASE_URL}/"]

    def get_head(self, title, is_home=False):
        map_json = json.dumps(self.map_data, ensure_ascii=False) if is_home else "[]"
        map_js = f"""
        <script src="https://maps.googleapis.com/maps/api/js?key={MAPS_API_KEY}&callback=initMap" async defer></script>
        <script>
            function initMap() {{
                const el = document.getElementById('map'); if(!el) return;
                const map = new google.maps.Map(el, {{ center: {{lat:24.16, lng:120.64}}, zoom:12, disableDefaultUI:true }});
                const info = new google.maps.InfoWindow();
                {map_json}.forEach(loc => {{
                    const m = new google.maps.Marker({{ position:{{lat:parseFloat(loc.lat), lng:parseFloat(loc.lng)}}, map }});
                    m.addListener('click', () => {{ 
                        info.setContent(`<div style="padding:10px;"><img src="${{loc.img}}" style="width:100px;"><h4 style="margin:5px 0;">${{loc.name}}</h4><a href="${{loc.url}}">查看詳情</a></div>`);
                        info.open(map, m); 
                    }});
                }});
            }}
            function executeSearch() {{
                const area = document.getElementById('s-area').value;
                document.querySelectorAll('.card-anchor').forEach(c => {{
                    c.style.display = (area === 'all' || c.dataset.area === area) ? 'block' : 'none';
                }});
            }}
        </script>""" if is_home else ""
        return f"<head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>{esc(title)}</title>{CSS_STYLE}{map_js}</head>"

    def run(self):
        for d in ["area", "life"]: 
            if Path(d).exists(): shutil.rmtree(d)
            Path(d).mkdir(exist_ok=True)
        res = requests.get(SHEET_CSV_URL, timeout=30)
        res.encoding = "utf-8-sig"
        reader = list(csv.DictReader(res.text.splitlines()))

        for i, row in enumerate(reader):
            d = {norm(k): norm(v) for k, v in row.items() if k}
            if d.get("狀態", "").upper() == "OFF" or not d.get("案名"): continue
            slug = f"p{i}"
            Path(slug).mkdir(exist_ok=True)
            imgs = normalize_imgs(d.get("圖片網址", ""))
            self.urls.append(f"{BASE_URL}/{slug}/")
            if d.get("lat") and d.get("lng"):
                self.map_data.append({"name":d['案名'], "price":d.get('價格'), "lat":d['lat'], "lng":d['lng'], "img":imgs[0], "url":f"/{PROJECT_NAME}/{slug}/"})
            
            detail_html = f"""<div class='container'><div class='header'><a href='/{PROJECT_NAME}/' class='logo'>SK-L</a></div><img src='{imgs[0]}' style='width:100%;height:500px;object-fit:cover;'><div style='padding:60px;'><h1 style='font-size:48px;'>{esc(d['案名'])}</h1><div style='font-size:60px;color:var(--primary);'>{esc(d.get('價格'))}萬</div><div style='line-height:2.4;font-size:20px;margin-top:40px;'>{esc(d.get('描述',''))}</div></div><div class='action-bar'><a class='btn btn-call' href='tel:{MY_PHONE}'>服務專線</a><a class='btn btn-line' href='{MY_LINE_URL}'>LINE 諮詢</a></div></div>"""
            Path(f"{slug}/index.html").write_text(f"<!doctype html><html>{self.get_head(d['案名'])}<body>{detail_html}</body></html>", encoding="utf-8")
            self.items.append(d)

        # 首頁生成 (修復 SyntaxError)
        area_opts = "".join([f'<option value="{a}">{a}</option>' for a in sorted(set(x.get('區域') for x in self.items if x.get('區域')))])
        home_cards = ""
        for x in self.items[::-1]:
            img_url = normalize_imgs(x.get('圖片網址', ""))[0]
            home_cards += f'<a href="/{PROJECT_NAME}/p{self.items.index(x)}/" class="card-anchor" data-area="{x.get("區域")}"><div class="card"><img src="{img_url}"><div class="card-body"><div class="card-area">{esc(x.get("區域"))}</div><h3 class="card-title">{esc(x.get("案名"))}</h3><div class="card-price">{esc(x.get("價格"))}萬</div></div></div></a>'
        
        home_html = f"""<div class='container'><div class='header'><div class='logo'>{SITE_TITLE}</div></div><div id='map'></div><div class='search-box'><div class='search-item'><label class='search-label'>區域</label><select class='search-select' id='s-area'><option value='all'>全區</option>{area_opts}</select></div><button class='search-btn' onclick='executeSearch()'>搜尋</button></div><div id='list-start' class='grid'>{home_cards}</div><div class='action-bar'><a class='btn btn-call' href='tel:{MY_PHONE}'>預約專線</a><a class='btn btn-line' href='{MY_LINE_URL}'>LINE 諮詢</a></div></div>"""
        Path("index.html").write_text(f"<!doctype html><html>{self.get_head(SITE_TITLE, True)}<body>{home_html}</body></html>", encoding="utf-8")

if __name__ == "__main__":
    SKL_Researcher().fetch_latest_intel()
    SKL_Builder().run()
