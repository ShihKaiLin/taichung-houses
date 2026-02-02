import os, csv, requests, html, shutil, re, urllib.parse, json
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup

# ============================================================
# 1. 核心品牌與技術配置
# ============================================================
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQShAl0-TbUU0MQdYVe53im2T6lXQgh_7g-bdL6HHpIBFtA2yfIAMbPw4J9RgZUkROb9AAiMhnRC0kH/pub?output=csv"
PROJECT_NAME = "taichung-houses"
BASE_URL = f"https://shihkailin.github.io/{PROJECT_NAME}"

SITE_TITLE = "SK-L 大台中房地產"
SITE_SLOGAN = "林世塏｜專業顧問 · 誠信置產 · 台中精選房產"
GA4_ID = "G-B7WP9BTP8X"

MY_NAME = "林世塏"
MY_PHONE = "0938-615-351"
MY_LINE_URL = "https://line.me/ti/p/FDsMyAYDv_" 

POSTS_DIR = Path("posts")
REPORT_DIR = Path("market_reports")
GEOCACHE_PATH = Path("geocache.json")
MAPS_API_KEY = os.getenv("MAPS_API_KEY", "AIzaSyDzgnI2Ucv622CRkWwo2GE5JRrs_Y4HQY0")
IMG_RAW_BASE = f"https://raw.githubusercontent.com/ShihKaiLin/{PROJECT_NAME}/main/images/"
DEFAULT_HERO = f"{IMG_RAW_BASE}hero_bg.jpg"

LEGAL_INFO_HTML = """
<div style="margin-top: 35px; padding-top: 25px; border-top: 1.5px solid #edf2f7; font-size: 11px; color: #94a3b8; line-height: 2.4; font-weight: 500;">
    📍 英柏國際地產有限公司<br>
    中市地價二字第 1070029259 號<br>
    經紀人：王一媖 (103) 中市經紀字第 00678 號
</div>
"""

# ============================================================
# 2. SK-L 3.0 極簡精品視覺系統
# ============================================================
CSS_STYLE = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&family=Noto+Sans+TC:wght@300;500;700;900&display=swap');
    
    :root { 
        --primary: #1A1C1E; --accent: #C5A059; --bg: #FDFDFD;
        --text-main: #2C2E30; --ease: cubic-bezier(0.2, 1, 0.3, 1);
    }

    body { font-family: 'Inter', 'Noto Sans TC', sans-serif; margin: 0; background: var(--bg); color: var(--text-main); -webkit-font-smoothing: antialiased; }
    
    .container { width: 100%; max-width: 1400px; margin: auto; background: #fff; min-height: 100vh; position: relative; padding-bottom: 180px; }
    
    .header { background: rgba(255,255,255,0.85); backdrop-filter: blur(20px); padding: 30px 60px; display: flex; justify-content: space-between; align-items: center; position: sticky; top: 0; z-index: 1000; border-bottom: 1px solid rgba(0,0,0,0.05); }
    .logo { font-weight: 800; font-size: 22px; letter-spacing: 4px; color: var(--primary); text-decoration: none; text-transform: uppercase; }

    #map { height: 500px; background: #f0f0f0; width: 100%; filter: grayscale(15%); border-bottom: 1px solid #eee; }
    
    .search-box { 
        background: #FFFFFF; padding: 35px 50px; margin: -60px auto 0; border-radius: 30px; 
        box-shadow: 0 30px 80px rgba(0,0,0,0.08); position: relative; z-index: 10;
        width: 88%; display: flex; flex-wrap: wrap; align-items: flex-end; gap: 30px; box-sizing: border-box;
    }
    .search-item { flex: 1; min-width: 180px; display: flex; flex-direction: column; gap: 10px; }
    .search-label { font-size: 10px; font-weight: 700; color: var(--accent); text-transform: uppercase; letter-spacing: 2px; }
    .search-select, .search-input { padding: 15px 0; border: none; border-bottom: 1.5px solid #E5E7EB; font-size: 16px; background: transparent; outline: none; transition: 0.3s; font-weight: 500; }
    .search-btn { background: var(--primary); color: #fff; border: none; padding: 18px 45px; border-radius: 12px; font-weight: 700; font-size: 15px; cursor: pointer; transition: 0.3s; }
    .search-btn:hover { background: var(--accent); transform: translateY(-2px); box-shadow: 0 10px 30px rgba(197, 160, 89, 0.3); }

    .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(380px, 1fr)); gap: 60px; padding: 100px 60px; }
    
    .card { overflow: hidden; background: #fff; display: flex; flex-direction: column; transition: var(--ease); text-decoration: none; color: inherit; }
    .card:hover { transform: translateY(-10px); }
    .card img { width: 100%; height: 300px; object-fit: cover; border-radius: 4px; transition: 1.2s var(--ease); }
    .card-body { padding: 30px 0; }
    .card-area { font-size: 11px; font-weight: 700; color: var(--accent); letter-spacing: 2.5px; margin-bottom: 12px; text-transform: uppercase; }
    .card-title { font-size: 22px; font-weight: 700; color: var(--primary); line-height: 1.4; margin: 0; }
    .card-price { color: var(--primary); font-weight: 300; font-size: 32px; margin-top: 15px; }
    .card-price::after { content: '萬'; font-size: 14px; font-weight: 600; margin-left: 4px; }
    
    .action-bar { position: fixed; bottom: 40px; left: 50%; transform: translateX(-50%); width: 90%; max-width: 600px; padding: 15px; display: flex; gap: 15px; background: rgba(26, 28, 30, 0.95); backdrop-filter: blur(15px); border-radius: 20px; z-index: 10000; box-shadow: 0 25px 50px rgba(0,0,0,0.3); }
    .btn { flex: 1; text-align: center; padding: 18px; border-radius: 12px; text-decoration: none; font-weight: 700; color: #fff; font-size: 15px; transition: 0.3s; }
    .btn-call { background: transparent; border: 1px solid rgba(255,255,255,0.2); }
    .btn-line { background: #06C755; }
</style>
"""# ============================================================
# 3. 功能模組 A：地產情報研究中心 (Researcher)
# ============================================================
class SKL_Researcher:
    """
    專業研究模組：自動收集競爭對手資訊與市場新聞
    """
    def __init__(self):
        self.targets = {
            "大橘團隊專欄分析": "https://www.dajuteam.com.tw/tw/blog",
            "591 台中房市新聞": "https://news.591.com.tw/list/taichung"
        }
    
    def fetch_latest_intel(self):
        # 建立報告目錄
        REPORT_DIR.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        report_file = REPORT_DIR / f"market_intel_{timestamp}.txt"
        
        print(f"🔍 正在掃描台中房產市場動態...")
        
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(f"=== SK-L 大台中地產戰略報告 ({datetime.now().strftime('%Y-%m-%d')}) ===\n")
            f.write(f"備註：本報告僅供內部研究使用，嚴禁直接轉載。\\n\\n")
            
            for name, url in self.targets.items():
                f.write(f"【對手/來源：{name}】\n")
                try:
                    headers = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
                    res = requests.get(url, timeout=10, headers=headers)
                    res.encoding = "utf-8"
                    soup = BeautifulSoup(res.text, 'html.parser')
                    
                    # 抓取標題
                    titles = [t.get_text().strip() for t in soup.find_all(['h2', 'h3']) if t.get_text().strip()][:5]
                    if titles:
                        for i, t in enumerate(titles, 1):
                            f.write(f"{i}. {t}\n")
                    else:
                        f.write("- 偵測到結構變動，需更新規則。\n")
                except Exception as e:
                    f.write(f"- 獲取失敗: {str(e)}\n")
                f.write("-" * 30 + "\n")
            
            f.write("\n=== 世塏的戰略建議 ===\n")
            f.write("1. 針對對手近期關注的重劃區，建議在專欄撰寫更深度的稅務或法規文章。\\n")
            f.write("2. 目前搜尋熱度集中於特定區塊，請確保試算表中有對應物件。\\n")
            
        print(f"✅ 情報收集完成！報告已存放至：{report_file}")

# ============================================================
# 4. 數據處理工具函數 (嚴格對齊，防止 IndentationError)
# ============================================================
def esc(s): return html.escape(str(s or "").strip())
def norm(s): return str(s or "").strip().replace("\ufeff", "")
def get_num(s):
    nums = re.findall(r'\d+\.?\d*', str(s).replace(',', ''))
    return float(nums[0]) if nums else 0

def normalize_imgs(img_field):
    if not img_field: return ["https://placehold.co/1200x800?text=SK-L+Premium"]
    raw_list = re.split(r'[|｜]+', str(img_field))
    return [i if i.startswith("http") else f"{IMG_RAW_BASE}{i.lstrip('/')}" for i in raw_list if i.strip()]

# ============================================================
# 5. 互動引擎：地圖彈窗與篩選邏輯 (JS)
# ============================================================
def get_head(title, desc="", og_img="", is_home=False, map_data=None):
    map_json = json.dumps(map_data, ensure_ascii=False) if map_data else "[]"
    
    # --- 精品級 JavaScript 引擎 ---
    map_js = f"""
    <script src="https://maps.googleapis.com/maps/api/js?key={MAPS_API_KEY}&callback=initMap" async defer></script>
    <script>
        let map;
        function initMap() {{
            const el = document.getElementById('map'); if(!el) return;
            const data = {map_json};
            map = new google.maps.Map(el, {{ 
                center: {{lat: 24.162, lng: 120.647}}, zoom: 12, 
                disableDefaultUI: true, zoomControl: true,
                styles: [{{"featureType":"poi","elementType":"all","stylers":[{{"visibility":"off"}}]}},{{"featureType":"water","stylers":[{{"color":"#f0f0f0"}}]}}]
            }});
            const infoWindow = new google.maps.InfoWindow();
            data.forEach(loc => {{
                if(!loc.lat) return;
                const marker = new google.maps.Marker({{ position: {{lat: parseFloat(loc.lat), lng: parseFloat(loc.lng)}}, map: map }});
                marker.addListener('click', () => {{
                    const content = `
                        <div style="padding:15px; width:200px; font-family:sans-serif;">
                            <img src="${{loc.img}}" style="width:100%; border-radius:4px; margin-bottom:10px;">
                            <h4 style="margin:0; font-size:15px; color:#1A1C1E;">${{loc.name}}</h4>
                            <div style="color:#C5A059; font-weight:700; font-size:18px; margin:5px 0;">${{loc.price}}</div>
                            <a href="${{loc.url}}" style="display:block; text-align:center; background:#1A1C1E; color:#fff; text-decoration:none; padding:10px; border-radius:4px; font-size:12px;">查看顧問建議 →</a>
                        </div>`;
                    infoWindow.setContent(content);
                    infoWindow.open(map, marker);
                }});
            }});
        }}
        function executeSearch() {{
            const area = document.getElementById('s-area').value;
            const minP = parseFloat(document.getElementById('s-min-p').value) || 0;
            const maxP = parseFloat(document.getElementById('s-max-p').value) || 999999;
            document.querySelectorAll('.card-anchor').forEach(card => {{
                const d = card.dataset;
                const p = parseFloat(d.priceNum);
                card.style.display = (area === 'all' || d.area === area) && (p >= minP && p <= maxP) ? 'block' : 'none';
            }});
            document.getElementById('list-start').scrollIntoView({{behavior: 'smooth', block: 'start'}});
        }}
    </script>""" if is_home else ""
    
    return f"""<head>
    <meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=0">
    <title>{{esc(title)}}</title>
    {{CSS_STYLE}}
    {{map_js}}
    </head>"""# ============================================================
# 6. 功能模組 B：旗艦網站建置引擎 (Builder)
# ============================================================
class SKL_Builder:
    def __init__(self):
        self.root = Path(".")
        self.all_items = []
        self.map_data = []
        self.sitemap_urls = [f"{BASE_URL}/"]

    def run(self):
        print(f"🏗️  正在啟動 SK-L 3.0 旗艦建置流程...")

        # A. 目錄初始化：清理舊檔案，確保 404 不會發生
        for d in ["area", "life"]: 
            if (self.root/d).exists(): shutil.rmtree(self.root/d)
            (self.root/d).mkdir(exist_ok=True)
        for p in self.root.glob("p*"):
            if p.is_dir() and re.match(r'^p\d+$', p.name): shutil.rmtree(p)

        # B. 獲取雲端資料
        try:
            res = requests.get(SHEET_CSV_URL, timeout=30)
            res.encoding = "utf-8-sig"
            reader = list(csv.DictReader(res.text.splitlines()))
        except Exception as e:
            print(f"❌ 雲端試算表連線失敗: {e}"); return

        # C. 逐一生成物件詳情頁面
        for i, row in enumerate(reader):
            d = {norm(k): norm(v) for k, v in row.items() if k}
            if d.get("狀態", "").upper() == "OFF" or not d.get("案名"): continue
            
            slug = f"p{i}"
            (self.root/slug).mkdir(exist_ok=True)
            item_path = f"/{PROJECT_NAME}/{slug}/"
            self.sitemap_urls.append(f"{BASE_URL}/{slug}/")
            
            imgs = normalize_imgs(d.get("圖片網址", ""))
            price_val, size_val = d.get("價格", "面議"), d.get("坪數", "0")
            
            # 地圖點位收集 (修正：確保 lat/lng 存在才加入地圖)
            if d.get("lat") and d.get("lng"):
                self.map_data.append({
                    "name": d['案名'], "price": price_val, "url": item_path, 
                    "lat": d["lat"], "lng": d["lng"], "img": imgs[0]
                })

            # 生成精品詳情頁內容 (3.0 極簡版)
            detail_html = f"""<div class="container">
                <div class="header"><a href="/{PROJECT_NAME}/" class="logo">SK-L</a></div>
                <div style="height:600px; overflow:hidden;"><img src="{imgs[0]}" style="width:100%; height:100%; object-fit:cover;"></div>
                <div style="padding:100px 60px;">
                    <div class="card-area">LUXURY RESIDENCE</div>
                    <h1 style="font-size:52px; font-weight:800; color:var(--primary); margin:0 0 20px; letter-spacing:-2px;">{esc(d['案名'])}</h1>
                    <div style="font-size:64px; color:var(--primary); font-weight:300; margin-bottom:60px;">{esc(price_val)}<span style="font-size:18px; font-weight:600; margin-left:8px;">萬</span></div>
                    
                    <div style="margin-bottom:60px; display:flex; gap:15px; flex-wrap:wrap;">
                        <span class="badge">📍 {esc(d.get('區域'))}</span>
                        <span class="badge">📐 {esc(size_val)}坪</span>
                    </div>

                    <div style="line-height:2.6; font-size:20px; color:#4B5563; border-top:1px solid #EEE; padding-top:60px; margin-bottom:80px;">
                        <div style="font-weight:700; color:var(--primary); margin-bottom:30px; font-size:24px; letter-spacing:1px;">顧問置產分析 Report</div>
                        {esc(d.get('描述','')).replace('、','<br>• ')}
                    </div>

                    <div style="padding:60px; border-radius:24px; background:#F9FAFB; border:1px solid #F3F4F6;">
                        <div style="display:flex; align-items:center; gap:30px; margin-bottom:30px;">
                            <img src="{IMG_RAW_BASE}agent_photo.jpg" style="width:90px; height:90px; border-radius:50%; object-fit:cover;" onerror="this.src='https://placehold.co/150x150?text=SK-L'">
                            <div>
                                <div style="font-size:28px; font-weight:800; color:var(--primary);">{esc(MY_NAME)}</div>
                                <div style="font-size:15px; color:var(--accent); font-weight:700; letter-spacing:1px;">大台中地產置產顧問</div>
                            </div>
                        </div>
                        {LEGAL_INFO_HTML}
                        <a href="{MY_LINE_URL}" target="_blank" style="display:block; background:#06C755; color:#fff; text-decoration:none; text-align:center; padding:22px; border-radius:12px; font-weight:700; margin-top:40px; font-size:18px; transition:0.3s;">💬 索取完整物件分析報告</a>
                    </div>
                </div>
                <div class="action-bar"><a class="btn btn-call" href="tel:{MY_PHONE}">📞 服務專線</a><a class="btn btn-line" href="{MY_LINE_URL}" target="_blank">💬 LINE 諮詢</a></div>
            </div>"""
            (self.root/slug/"index.html").write_text(f"<!doctype html><html lang='zh-TW'>{get_head(d['案名'])}<body>{detail_html}</body></html>", encoding="utf-8")
            
            self.all_items.append({
                "name": d['案名'], "area": d.get('區域'), "price": price_val, 
                "price_num": get_num(price_val), "img": imgs[0], "url": item_path
            })

        # D. SEO 置產專欄處理 (Life Posts)
        if POSTS_DIR.exists():
            for md in POSTS_DIR.glob("*.md"):
                slug = urllib.parse.quote(md.stem)
                (self.root/"life"/slug).mkdir(parents=True, exist_ok=True)
                content = md.read_text(encoding="utf-8").replace('\n', '<br>')
                post_html = f"""<div class="container"><div class="header"><a href="/{PROJECT_NAME}/" class="logo">SK-L</a></div><div style="padding:120px 60px; max-width:900px; margin:auto; line-height:2.8; font-size:21px;"><h1>{esc(md.stem)}</h1>{content}</div></div>"""
                (self.root/"life"/slug/"index.html").write_text(f"<!doctype html><html lang='zh-TW'>{get_head(md.stem)}<body>{post_html}</body></html>", encoding="utf-8")
                self.sitemap_urls.append(f"{BASE_URL}/life/{slug}/")

        # E. 首頁網格組裝與搜尋面板 (此處已修正 501 行縮進問題)
        unique_areas = sorted(set(x['area'] for x in self.all_items if x['area']))
        area_opts = "".join([f'<option value="{a}">{a}</option>' for a in unique_areas])
        
        home_cards = "".join([f'''
        <a href="{it["url"]}" class="card-anchor" data-area="{it["area"]}" data-price-num="{it["price_num"]}">
            <div class="card">
                <div class="card-img-wrapper"><img src="{it["img"]}" loading="lazy" alt="{esc(it["name"])}"></div>
                <div class="card-body">
                    <div class="card-area">{esc(it["area"])}</div>
                    <h3 class="card-title">{esc(it["name"])}</h3>
                    <div class="card-price">{esc(it["price"])}</div>
                </div>
            </div>
        </a>''' for it in self.all_items[::-1]])
        
        home_html = f"""<div class="container">
            <div class="header"><div class="logo">{SITE_TITLE}</div></div>
            <div id="map"></div>
            <div class="search-box">
                <div class="search-item">
                    <label class="search-label">行政區域 Location</label>
                    <select class="search-select" id="s-area"><option value="all">台中全區</option>{area_opts}</select>
                </div>
                <div class="search-item">
                    <label class="search-label">預算範圍 Budget (萬)</label>
                    <div style="display:flex;gap:15px;"><input class="search-input" id="s-min-p" placeholder="最低"><input class="search-input" id="s-max-p" placeholder="最高"></div>
                </div>
                <button class="search-btn" onclick="executeSearch()">🔍 搜尋物件</button>
            </div>
            <div id="list-start"></div>
            <div class="grid">{home_cards}</div>
            <div class="action-bar"><a class="btn btn-call" href="tel:{MY_PHONE}">📞 立即撥打</a><a class="btn btn-line" href="{MY_LINE_URL}" target="_blank">💬 LINE 諮詢</a></div>
        </div>"""
        
        (self.root/"index.html").write_text(f"<!doctype html><html lang='zh-TW'>{get_head(SITE_TITLE, is_home=True, map_data=self.map_data)}<body>{home_html}</body></html>", encoding="utf-8")

        # F. Sitemap 生成
        xml = '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + "".join([f'<url><loc>{u}</loc><lastmod>{datetime.now().strftime("%Y-%m-%d")}</lastmod></url>' for u in sorted(set(self.sitemap_urls))]) + '</urlset>'
        (self.root/"sitemap.xml").write_text(xml, encoding="utf-8")
        print(f"✅ SK-L 3.0 旗艦版建置成功！")

# ============================================================
# 7. 主控制中心執行入口
# ============================================================
if __name__ == "__main__":
    researcher = SKL_Researcher()
    builder = SKL_Builder()
    researcher.fetch_latest_intel() # 先收情報
    builder.run() # 再建網站
