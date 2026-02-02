import os, csv, requests, html, shutil, re, urllib.parse, json
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup

# ============================================================
# 1. 核心品牌與技術配置 (已修正 LINE 與 專案路徑)
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
# 2. 旗艦級精品 CSS 樣式系統 (徹底解決版面醜的問題)
# ============================================================
CSS_STYLE = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&family=Noto+Sans+TC:wght@400;700;900&display=swap');
    
    :root { 
        --navy: #0F172A; --gold: #B59461; --green: #10B981; 
        --bg: #F8FAFC; --card-bg: #FFFFFF; 
        --shadow-sm: 0 10px 30px rgba(15, 23, 42, 0.04);
        --shadow-lg: 0 40px 100px rgba(15, 23, 42, 0.12);
        --transition: all 0.6s cubic-bezier(0.16, 1, 0.3, 1);
    }

    body { font-family: 'Inter', 'Noto Sans TC', sans-serif; margin: 0; background: var(--bg); color: #1E293B; letter-spacing: -0.01em; -webkit-font-smoothing: antialiased; }
    
    .container { width: 100%; max-width: 1200px; margin: auto; background: #fff; min-height: 100vh; position: relative; padding-bottom: 220px; box-shadow: 0 0 120px rgba(0,0,0,0.03); }
    
    .header { background: var(--navy); color: #fff; padding: 28px 40px; display: flex; justify-content: space-between; align-items: center; position: sticky; top: 0; z-index: 1000; box-shadow: 0 15px 50px rgba(0,0,0,0.18); }
    .logo { font-weight: 950; font-size: 26px; letter-spacing: 2px; color: #fff; text-decoration: none; text-transform: uppercase; }

    #map { height: 480px; background: #E2E8F0; width: 100%; border-bottom: 12px solid #fff; }
    
    .search-box { 
        background: #fff; padding: 45px; margin: -85px auto 0; border-radius: 45px; 
        box-shadow: var(--shadow-lg); position: relative; z-index: 10;
        width: 94%; display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; box-sizing: border-box;
    }
    .search-item { display: flex; flex-direction: column; gap: 10px; }
    .search-label { font-size: 11px; font-weight: 900; color: var(--navy); text-transform: uppercase; letter-spacing: 2px; opacity: 0.4; }
    .search-select, .search-input { 
        padding: 18px; border-radius: 20px; border: 1.5px solid #E2E8F0; font-size: 15px; 
        background: #F8FAFC; outline: none; transition: var(--transition);
    }
    .search-select:focus, .search-input:focus { border-color: var(--gold); background: #fff; box-shadow: 0 0 0 6px rgba(181, 148, 97, 0.08); }
    .search-btn { 
        background: var(--navy); color: #fff; border: none; padding: 22px; border-radius: 22px; 
        font-weight: 900; font-size: 16px; cursor: pointer; transition: 0.4s; grid-column: 1 / -1; letter-spacing: 2px;
    }
    .search-btn:hover { background: var(--gold); transform: translateY(-4px); box-shadow: 0 15px 35px rgba(181, 148, 97, 0.3); }

    .grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 25px; padding: 60px 25px; }
    @media (min-width: 768px) { .grid { grid-template-columns: repeat(3, 1fr); gap: 45px; padding: 90px 45px; } }
    
    .card { 
        border-radius: 50px; overflow: hidden; background: #fff; border: 1.5px solid #F1F5F9; 
        display: flex; flex-direction: column; height: 100%; transition: var(--transition); text-decoration: none; color: inherit;
    }
    .card:hover { transform: translateY(-18px); box-shadow: 0 60px 120px rgba(15, 23, 42, 0.12); border-color: var(--gold); }
    .card img { width: 100%; height: 280px; object-fit: cover; transition: 0.7s ease; }
    .card-body { padding: 35px; flex-grow: 1; display: flex; flex-direction: column; }
    .card-title { font-size: 20px; font-weight: 900; color: var(--navy); line-height: 1.5; margin: 0; }
    .card-price { color: var(--gold); font-weight: 950; font-size: 28px; margin-top: 15px; letter-spacing: -1.5px; }
    
    .badge { display: inline-block; padding: 10px 20px; background: #F1F5F9; color: #64748B; border-radius: 16px; font-size: 12px; font-weight: 800; margin: 0 10px 12px 0; }
    
    .action-bar { 
        position: fixed; bottom: 0; left: 50%; transform: translateX(-50%); width: 100%; max-width: 1200px; 
        padding: 30px 35px 55px; display: flex; gap: 20px; background: rgba(255,255,255,0.92); backdrop-filter: blur(25px); 
        border-top: 1px solid #F1F5F9; z-index: 10000; box-sizing: border-box; 
    }
    .btn { flex: 1; text-align: center; padding: 25px; border-radius: 25px; text-decoration: none; font-weight: 950; color: #fff; font-size: 18px; transition: 0.3s; }
    .btn-call { background: var(--navy); } .btn-line { background: var(--green); }
    .btn:hover { transform: scale(0.97); opacity: 0.9; }
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
        
        print(f"🔍 正在掃描台中房產市場動向...")
        
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(f"=== SK-L 大台中地產戰略報告 ({datetime.now().strftime('%Y-%m-%d')}) ===\\n")
            f.write(f"備註：本報告僅供內部研究使用，嚴禁直接轉載以免侵權。\\n\\n")
            
            for name, url in self.targets.items():
                f.write(f"【對手/來源：{name}】\\n")
                try:
                    # 模擬瀏覽器行為，防止被封鎖
                    headers = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
                    res = requests.get(url, timeout=10, headers=headers)
                    res.encoding = "utf-8"
                    soup = BeautifulSoup(res.text, 'html.parser')
                    
                    # 抓取最新的 5 個標題作為情報參考
                    titles = [t.get_text().strip() for t in soup.find_all(['h2', 'h3']) if t.get_text().strip()][:5]
                    if titles:
                        for i, t in enumerate(titles, 1):
                            f.write(f"{i}. {t}\\n")
                    else:
                        f.write("- 偵測到結構變動，需更新掃描規則。\\n")
                except Exception as e:
                    f.write(f"- 獲取失敗: {str(e)}\\n")
                f.write("-" * 30 + "\\n")
            
            f.write("\\n=== 世塏的戰略建議 ===\\n")
            f.write("1. 針對對手近期關注的重劃區，建議在 posts/ 撰寫更深度的稅務或法規面文章以達成差異化。\\n")
            f.write("2. 數據觀察顯示目前搜尋熱度集中於特定行政區，請確保試算表中有對應物件。\\n")
            
        print(f"✅ 情報收集完成！報告已存放至：{report_file}")

# ============================================================
# 4. 數據處理工具函數 (確保輸出的文字與數字安全無誤)
# ============================================================
def esc(s): return html.escape(str(s or "").strip())
def norm(s): return str(s or "").strip().replace("\\ufeff", "")
def get_num(s):
    # 精確提取純數字，過濾掉「萬」、「,」等字元
    nums = re.findall(r'\\d+\\.?\\d*', str(s).replace(',', ''))
    return float(nums[0]) if nums else 0

def normalize_imgs(img_field):
    if not img_field: return ["https://placehold.co/1200x800?text=SK-L+Premium"]
    raw_list = re.split(r'[|｜]+', str(img_field))
    return [i if i.startswith("http") else f"{IMG_RAW_BASE}{i.lstrip('/')}" for i in raw_list if i.strip()]

# ============================================================
# 5. 旗艦級互動引擎 (解決紅點點不開的問題)
# ============================================================
def get_head(title, desc="", og_img="", is_home=False, map_data=None):
    map_json = json.dumps(map_data, ensure_ascii=False) if map_data else "[]"
    
    # --- JavaScript 注入：整合地圖小視窗與搜尋過濾 ---
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
                styles: [{{"featureType":"poi","elementType":"all","stylers":[{{"visibility":"off"}}]}}]
            }});
            
            const infoWindow = new google.maps.InfoWindow();
            data.forEach(loc => {{
                if(!loc.lat) return;
                const marker = new google.maps.Marker({{ 
                    position: {{lat: parseFloat(loc.lat), lng: parseFloat(loc.lng)}}, 
                    map: map 
                }});
                
                marker.addListener('click', () => {{
                    const content = `
                        <div style="padding:15px; width:220px; font-family:sans-serif;">
                            <div style="background:url('${{loc.img}}') center/cover; height:120px; border-radius:18px; margin-bottom:12px; box-shadow:0 8px 25px rgba(0,0,0,0.15);"></div>
                            <h4 style="margin:0; color:#0F172A; font-size:16px; font-weight:900;">${{loc.name}}</h4>
                            <div style="color:#B59461; font-weight:900; font-size:22px; margin:10px 0;">${{loc.price}}</div>
                            <a href="${{loc.url}}" style="display:block; text-align:center; background:#0F172A; color:#fff; text-decoration:none; padding:12px; border-radius:12px; font-size:13px; font-weight:900;">查看專家分析 →</a>
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
                const matches = (area === 'all' || d.area === area) && (p >= minP && p <= maxP);
                card.style.display = matches ? 'block' : 'none';
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
        print(f"🏗️  正在啟動 SK-L 旗艦建置流程...")

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

            # 生成精品詳情頁內容
            detail_html = f"""<div class="container">
                <div class="header"><a href="/{PROJECT_NAME}/" class="logo">← {SITE_TITLE}</a></div>
                <div style="height:500px; overflow:hidden;"><img src="{imgs[0]}" style="width:100%; height:100%; object-fit:cover;"></div>
                <div style="padding:60px 50px 100px;">
                    <div style="color:var(--gold); font-weight:900; font-size:14px; letter-spacing:4px; margin-bottom:20px; text-transform:uppercase;">Luxury Real Estate Analyst</div>
                    <h1 style="font-size:48px; font-weight:950; color:var(--navy); margin-bottom:15px; letter-spacing:-2px;">{esc(d['案名'])}</h1>
                    <div style="font-size:60px; color:var(--gold); font-weight:950; margin-bottom:50px; letter-spacing:-3px;">{esc(price_val)}</div>
                    <div style="margin-bottom:45px;">
                        <span class="badge">📍 {esc(d.get('區域'))}精選</span>
                        <span class="badge">📐 {esc(size_val)}坪寬闊空間</span>
                    </div>
                    <div style="line-height:2.5; font-size:20px; color:#475569; background:#F8FAFC; padding:50px; border-radius:50px; border:1px solid #F1F5F9; margin-bottom:70px;">
                        <div style="font-weight:900; color:var(--navy); margin-bottom:25px; font-size:24px; border-left:6px solid var(--gold); padding-left:20px;">置產專家建議分析</div>
                        {esc(d.get('描述','')).replace('、','<br>• ')}
                    </div>
                    <div style="background:#fff; border-radius:50px; padding:50px; border:1.5px solid #F1F5F9; box-shadow:var(--shadow-lg);">
                        <div style="display:flex; align-items:center; gap:30px; margin-bottom:20px;">
                            <img src="{IMG_RAW_BASE}agent_photo.jpg" style="width:100px; height:100px; border-radius:50%; object-fit:cover; border:6px solid #F8FAFC;" onerror="this.src='https://placehold.co/150x150?text=SK-L'">
                            <div>
                                <div style="font-size:30px; font-weight:950; color:var(--navy);">{esc(MY_NAME)}</div>
                                <div style="font-size:16px; color:#94a3b8; font-weight:800;">大台中房產置產顧問</div>
                            </div>
                        </div>
                        {LEGAL_INFO_HTML}
                        <a href="{MY_LINE_URL}" target="_blank" style="display:block; background:var(--green); color:#fff; text-decoration:none; text-align:center; padding:25px; border-radius:25px; font-weight:950; margin-top:45px; font-size:21px; box-shadow:0 15px 40px rgba(16,185,129,0.35);">💬 立即聯繫，獲取專業置產報告</a>
                    </div>
                </div>
                <div class="action-bar"><a class="btn btn-call" href="tel:{MY_PHONE}">📞 立即撥打</a><a class="btn btn-line" href="{MY_LINE_URL}" target="_blank">💬 LINE 諮詢</a></div>
            </div>"""
            (self.root/slug/"index.html").write_text(f"<!doctype html><html lang='zh-TW'>{get_head(d['案名'])}<body>{detail_html}</body></html>", encoding="utf-8")
            
            self.all_items.append({
                "name": d['案名'], "area": d.get('區域'), "price": price_val, 
                "price_num": get_num(price_val), "img": imgs[0], "url": item_path
            })

        # D. SEO 置產文章處理 (Life Posts)
        if POSTS_DIR.exists():
            for md in POSTS_DIR.glob("*.md"):
                slug = urllib.parse.quote(md.stem)
                (self.root/"life"/slug).mkdir(parents=True, exist_ok=True)
                content = md.read_text(encoding="utf-8").replace('\n', '<br>')
                post_html = f"""<div class="container"><div class="header"><a href="/{PROJECT_NAME}/" class="logo">← {SITE_TITLE}</a></div><div style="padding:100px 60px; max-width:900px; margin:auto; line-height:2.6; font-size:21px;"><h1>{esc(md.stem)}</h1>{content}</div></div>"""
                (self.root/"life"/slug/"index.html").write_text(f"<!doctype html><html lang='zh-TW'>{get_head(md.stem)}<body>{post_html}</body></html>", encoding="utf-8")
                self.sitemap_urls.append(f"{BASE_URL}/life/{slug}/")

        # E. 首頁網格組裝與搜尋面板 (此處已修正 501 行縮進)
        area_opts = "".join([f'<option value="{a}">{a}</option>' for a in sorted(set(x['area'] for x in self.all_items if x['area']))])
        
        home_cards_list = []
        for it in self.all_items[::-1]:
            card_html = f'''<a href="{it["url"]}" class="card-anchor" data-area="{it["area"]}" data-price-num="{it["price_num"]}"><div class="card"><img src="{it["img"]}" loading="lazy"><div class="card-body"><h3 class="card-title">{esc(it["name"])}</h3><div class="card-price">{esc(it["price"])}</div><div style="margin-top:25px; font-size:12px; color:var(--navy); font-weight:900; opacity:0.3; text-align:right; letter-spacing:2px;">EXPLORE PROPERTY →</div></div></div></a>'''
            home_cards_list.append(card_html)
        
        home_cards = "".join(home_cards_list)
        
        home_html = f"""<div class="container"><div class="header"><div class="logo">{SITE_TITLE}</div></div><div id="map"></div>
        <div class="search-box">
            <div class="search-item"><label class="search-label">行政區域</label><select class="search-select" id="s-area"><option value="all">台中全區</option>{area_opts}</select></div>
            <div class="search-item"><label class="search-label">預算(萬)</label><div style="display:flex;gap:12px;"><input class="search-input" id="s-min-p" placeholder="最低"><input class="search-input" id="s-max-p" placeholder="最高"></div></div>
            <button class="search-btn" onclick="executeSearch()">🔍 搜尋台中精選房產</button>
        </div>
        <div id="list-start"></div><div class="grid">{home_cards}</div>
        <div class="action-bar"><a class="btn btn-call" href="tel:{MY_PHONE}">📞 立即撥打</a><a class="btn btn-line" href="{MY_LINE_URL}" target="_blank">💬 LINE 諮詢</a></div></div>"""
        
        (self.root/"index.html").write_text(f"<!doctype html><html lang='zh-TW'>{get_head(SITE_TITLE, is_home=True, map_data=self.map_data)}<body>{home_html}</body></html>", encoding="utf-8")

        # F. Sitemap 生成
        xml = '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + "".join([f'<url><loc>{u}</loc><lastmod>{datetime.now().strftime("%Y-%m-%d")}</lastmod></url>' for u in sorted(set(self.sitemap_urls))]) + '</urlset>'
        (self.root/"sitemap.xml").write_text(xml, encoding="utf-8")
        print(f"✅ SK-L 旗艦版建置完成！(共 {len(self.all_items)} 個物件)")

# ============================================================
# 7. 主程式控制中樞 (程式執行進入點)
# ============================================================
if __name__ == "__main__":
    # 初始化模組
    researcher = SKL_Researcher()
    builder = SKL_Builder()

    # 完整戰略流程：先收集情報分析市場，再自動建置精品網站
    researcher.fetch_latest_intel()
    builder.run()
