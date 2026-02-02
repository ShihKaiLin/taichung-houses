import os, csv, requests, html, shutil, re, urllib.parse, json
from pathlib import Path
from datetime import datetime

# ============================================================
# 1. 核心品牌與技術配置 (關鍵：修正 LINE 連結與專案路徑)
# ============================================================
# 雲端試算表發佈連結
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQShAl0-TbUU0MQdYVe53im2T6lXQgh_7g-bdL6HHpIBFtA2yfIAMbPw4J9RgZUkROb9AAiMhnRC0kH/pub?output=csv"
PROJECT_NAME = "taichung-houses"
BASE_URL = f"https://shihkailin.github.io/{PROJECT_NAME}"

# 品牌基礎資訊
SITE_TITLE = "SK-L 大台中房地產"
SITE_SLOGAN = "林世塏｜專業顧問 · 誠信置產 · 台中精選房產"
GA4_ID = "G-B7WP9BTP8X"

# 置產專業顧問資訊 (已修正：確保末尾底線符號正確包含)
MY_NAME = "林世塏"
MY_PHONE = "0938-615-351"
MY_LINE_URL = "https://line.me/ti/p/FDsMyAYDv_" 

# 技術路徑與 API 定義 (防止 Actions 環境報錯)
POSTS_DIR = Path("posts")
GEOCACHE_PATH = Path("geocache.json")
MAPS_API_KEY = os.getenv("MAPS_API_KEY", "AIzaSyDzgnI2Ucv622CRkWwo2GE5JRrs_Y4HQY0")
IMG_RAW_BASE = f"https://raw.githubusercontent.com/ShihKaiLin/{PROJECT_NAME}/main/images/"
DEFAULT_HERO = f"{IMG_RAW_BASE}hero_bg.jpg"

# 經紀法規誠信資訊區塊 (鎖定於詳情頁側邊，建立高端品牌權威)
LEGAL_INFO_HTML = """
<div style="margin-top: 35px; padding-top: 25px; border-top: 1.5px solid #edf2f7; font-size: 11px; color: #94a3b8; line-height: 2.4; font-weight: 500; letter-spacing: 0.5px;">
    📍 英柏國際地產有限公司<br>
    中市地價二字第 1070029259 號<br>
    經紀人：王一媖 (103) 中市經紀字第 00678 號<br>
    © 2026 LIN SHIH KAI PREMIUM REAL ESTATE ANALYSIS
</div>
"""
# ============================================================
# 2. 旗艦級精品美學 CSS (徹底解決版面醜的問題 - 前段佈局)
# ============================================================
# 這裡定義了網頁的整體配色、高階字體以及頂級導航列的視覺效果
CSS_STYLE = """
<style>
    /* 引入國際頂級字體：Inter 與 繁體中文專用的 Noto Sans TC */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&family=Noto+Sans+TC:wght@400;700;900&display=swap');
    
    :root { 
        --navy: #0F172A; /* 深沉午夜藍：代表專業與信任 */
        --gold: #B59461; /* 拉絲質感金：代表價值與高端 */
        --green: #10B981; /* LINE 品牌綠：代表即時與互動 */
        --bg: #F8FAFC; /* 冰原底色：讓內容更具呼吸感 */
        --card-bg: #FFFFFF; 
        --shadow-sm: 0 10px 30px rgba(15, 23, 42, 0.04);
        --shadow-lg: 0 40px 100px rgba(15, 23, 42, 0.12);
        --transition: all 0.6s cubic-bezier(0.16, 1, 0.3, 1);
    }

    /* 基礎樣式重置：優化渲染平滑度 */
    body { 
        font-family: 'Inter', 'Noto Sans TC', sans-serif; 
        margin: 0; background: var(--bg); color: #1E293B; 
        letter-spacing: -0.01em; -webkit-font-smoothing: antialiased; 
    }
    
    /* 旗艦容器：賦予 1200px 經典黃金寬度與軟陰影 */
    .container { 
        width: 100%; max-width: 1200px; margin: auto; 
        background: #fff; min-height: 100vh; position: relative; 
        padding-bottom: 220px; box-shadow: 0 0 120px rgba(0,0,0,0.03); 
    }
    
    /* 高端導航列：固定頂部設計 (Sticky Header) */
    .header { 
        background: var(--navy); color: #fff; padding: 28px 40px; 
        display: flex; justify-content: space-between; align-items: center; 
        position: sticky; top: 0; z-index: 1000; 
        box-shadow: 0 15px 50px rgba(0,0,0,0.18); 
    }
    
    /* 品牌 Logo 樣式：極粗體與字母間距強化 */
    .logo { 
        font-weight: 950; font-size: 26px; letter-spacing: 2px; 
        color: #fff; text-decoration: none; text-transform: uppercase; 
    }

    /* 地圖容器：與導航列無縫銜接，並加入白色邊界質感 */
    #map { 
        height: 500px; background: #E2E8F0; width: 100%; 
        border-bottom: 15px solid #fff; 
    }

    /* 針對行動裝置微調導航列寬度 */
    @media (max-width: 600px) {
        .header { padding: 20px 25px; }
        .logo { font-size: 20px; }
        #map { height: 350px; }
    }
</style>
"""
# 這裡接續定義搜尋列、物件卡片與底部導航的精細樣式
CSS_STYLE_CARDS = """
<style>
    /* 旗艦搜尋面板：核心排版優化 */
    .search-box { 
        background: #fff; padding: 50px; 
        margin: -100px auto 0; /* 關鍵：讓面板向上漂浮，壓在地圖上 */
        border-radius: 50px; 
        box-shadow: var(--shadow-lg); 
        position: relative; z-index: 10;
        width: 94%; display: grid; 
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
        gap: 25px; box-sizing: border-box;
    }
    
    .search-item { display: flex; flex-direction: column; gap: 12px; }
    
    .search-label { 
        font-size: 11px; font-weight: 900; color: var(--navy); 
        text-transform: uppercase; letter-spacing: 2.5px; opacity: 0.4; 
    }
    
    .search-select, .search-input { 
        padding: 20px; border-radius: 22px; border: 1.5px solid #E2E8F0; 
        font-size: 16px; background: #F8FAFC; outline: none; 
        transition: var(--transition);
    }
    
    /* 搜尋按鈕：旗艦級動態效果 */
    .search-btn { 
        background: var(--navy); color: #fff; border: none; padding: 24px; 
        border-radius: 25px; font-weight: 950; font-size: 17px; 
        cursor: pointer; transition: 0.4s; grid-column: 1 / -1; letter-spacing: 3px;
    }
    
    .search-btn:hover { 
        background: var(--gold); transform: translateY(-5px); 
        box-shadow: 0 20px 40px rgba(181, 148, 97, 0.35); 
    }

    /* 旗艦物件網格與卡片設計 */
    .grid { 
        display: grid; grid-template-columns: repeat(2, 1fr); 
        gap: 25px; padding: 80px 30px; 
    }
    
    @media (min-width: 768px) { 
        .grid { grid-template-columns: repeat(3, 1fr); gap: 50px; padding: 120px 50px; } 
    }
    
    .card { 
        border-radius: 55px; overflow: hidden; background: #fff; 
        border: 1.5px solid #F1F5F9; display: flex; flex-direction: column; 
        height: 100%; transition: var(--transition); 
        text-decoration: none; color: inherit;
    }
    
    .card:hover { 
        transform: translateY(-20px); 
        box-shadow: 0 70px 140px rgba(15, 23, 42, 0.15); 
        border-color: var(--gold); 
    }
    
    .card img { 
        width: 100%; height: 320px; object-fit: cover; 
        transition: 0.8s ease; 
    }
    
    .card:hover img { transform: scale(1.1); }
    
    .card-body { padding: 45px; flex-grow: 1; display: flex; flex-direction: column; }
    
    .card-title { 
        font-size: 21px; font-weight: 900; color: var(--navy); 
        line-height: 1.5; margin: 0; 
    }
    
    .card-price { 
        color: var(--gold); font-weight: 950; font-size: 32px; 
        margin-top: 20px; letter-spacing: -1.5px; 
    }
    
    .badge { 
        display: inline-block; padding: 12px 24px; background: #F1F5F9; 
        color: #64748B; border-radius: 20px; font-size: 13px; 
        font-weight: 800; margin: 0 12px 14px 0; 
    }
    
    /* 底部行動 Bar：加入 Glassmorphism 效果 */
    .action-bar { 
        position: fixed; bottom: 0; left: 50%; transform: translateX(-50%); 
        width: 100%; max-width: 1200px; padding: 35px 40px 60px; 
        display: flex; gap: 25px; background: rgba(255,255,255,0.94); 
        backdrop-filter: blur(30px); border-top: 1px solid #F1F5F9; 
        z-index: 10000; box-sizing: border-box; 
    }
</style>
"""# ============================================================
# 3. 互動引擎中心 (地圖資訊小卡復活 + 旗艦篩選 JS)
# ============================================================
def get_head(title, desc="", og_img="", is_home=False, map_data=None):
    # 優化 SEO 描述與社交媒體圖片
    seo_desc = esc(desc)[:120] if desc else esc(SITE_SLOGAN)
    og_img = og_img if (og_img and str(og_img).startswith("http")) else DEFAULT_HERO
    
    # 使用 json.dumps 確保數據結構 100% 正確埋入 JavaScript
    map_json = json.dumps(map_data, ensure_ascii=False) if map_data else "[]"
    
    # --- 核心 JavaScript：賦予網站生命力 ---
    map_js_template = """
    <script src="https://maps.googleapis.com/maps/api/js?key=MAPS_API_KEY&callback=initMap" async defer></script>
    <script>
        let map;
        function initMap() {
            const el = document.getElementById('map'); if(!el) return;
            const data = MAP_DATA_JSON;
            
            // 地圖初始化：設定中心點與極簡風格
            map = new google.maps.Map(el, { 
                center: {lat: 24.162, lng: 120.647}, zoom: 12, 
                disableDefaultUI: true, zoomControl: true,
                styles: [{"featureType":"poi","elementType":"all","stylers":[{"visibility":"off"}]}]
            });
            
            const infoWindow = new google.maps.InfoWindow();
            
            // 遍歷數據點位，生成紅點標記
            data.forEach(loc => {
                if(!loc.lat) return;
                const marker = new google.maps.Marker({ 
                    position: {lat: parseFloat(loc.lat), lng: parseFloat(loc.lng)}, 
                    map: map, title: loc.name
                });
                
                // 【核心亮點】：點擊紅點彈出精品級房屋資訊小卡
                marker.addListener('click', () => {
                    const content = `
                        <div style="padding:15px; width:220px; font-family:'Inter','Noto Sans TC',sans-serif; background:#fff;">
                            <div style="background:url('${loc.img}') center/cover; height:130px; border-radius:22px; margin-bottom:12px; box-shadow:0 12px 30px rgba(0,0,0,0.18);"></div>
                            <h4 style="margin:0; color:#0F172A; font-size:16px; font-weight:900; line-height:1.4;">${loc.name}</h4>
                            <div style="color:#B59461; font-weight:900; font-size:24px; margin:10px 0;">${loc.price}</div>
                            <a href="${loc.url}" style="display:block; text-align:center; background:#0F172A; color:#fff; text-decoration:none; padding:13px; border-radius:15px; font-size:13px; font-weight:900; transition:0.3s; box-shadow:0 5px 15px rgba(15,23,42,0.2);">查看顧問置產分析 →</a>
                        </div>`;
                    infoWindow.setContent(content);
                    infoWindow.open(map, marker);
                });
            });
        }

        // 【核心亮點】：多維度智慧篩選邏輯 (支援區域、類型、價格範圍、坪數範圍)
        function executeSearch() {
            const area = document.getElementById('s-area').value;
            const type = document.getElementById('s-type').value;
            const minP = parseFloat(document.getElementById('s-min-p').value) || 0;
            const maxP = parseFloat(document.getElementById('s-max-p').value) || 999999;
            const minS = parseFloat(document.getElementById('s-min-s').value) || 0;
            const maxS = parseFloat(document.getElementById('s-max-s').value) || 999999;

            document.querySelectorAll('.card-anchor').forEach(card => {
                const d = card.dataset;
                const p = parseFloat(d.priceNum);
                const s = parseFloat(d.sizeNum);
                
                // 執行布林邏輯判斷
                const matchesArea = (area === 'all' || d.area === area);
                const matchesType = (type === 'all' || d.type === type);
                const matchesPrice = (p >= minP && p <= maxP);
                const matchesSize = (s >= minS && s <= maxS);

                // 即時動態切換顯示狀態
                card.style.display = (matchesArea && matchesType && matchesPrice && matchesSize) ? 'block' : 'none';
            });
            
            // 搜尋完成後平滑滾動至結果列表
            document.getElementById('list-start').scrollIntoView({behavior: 'smooth', block: 'start'});
        }
    </script>"""
    
    # 注入 API Key 與 資料，處理 Python/JS 字串跳脫問題
    js_ready = map_js_template.replace("MAPS_API_KEY", MAPS_API_KEY).replace("MAP_DATA_JSON", map_json) if is_home else ""

    return f"""<head>
    <meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=0">
    <title>{esc(title)}</title>
    {CSS_STYLE}{CSS_STYLE_CARDS}
    <script async src="https://www.googletagmanager.com/gtag/js?id={GA4_ID}"></script>
    <script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','{GA4_ID}');</script>
    {js_ready}
    </head>"""

# ============================================================
# 4. 數據處理工具函數 (確保輸出的文字與數字安全無誤)
# ============================================================
def esc(s): return html.escape(str(s or "").strip())
def norm(s): return str(s or "").strip().replace("\\ufeff", "")
def get_num(s):
    # 智慧提取純數字：過濾掉「萬」、「,」等干擾字元
    nums = re.findall(r'\\d+\\.?\\d*', str(s).replace(',', ''))
    return float(nums[0]) if nums else 0

def normalize_imgs(img_field):
    if not img_field: return ["https://placehold.co/1200x800?text=SK-L+Branding"]
    # 支援半形或全形分隔符號，讓試算表輸入更隨性
    raw_list = re.split(r'[|｜]+', str(img_field))
    return [i if i.startswith("http") else f"{IMG_RAW_BASE}{i.lstrip('/')}" for i in raw_list if i.strip()]# ============================================================
# 5. 詳情頁生成引擎 (旗艦級精品排版 + 顧問信任模組)
# ============================================================
def build():
    root = Path(".")
    print(f"🚀 開始建置 {SITE_TITLE} 旗艦美學版...")

    # A. 環境初始化：確保目錄結構乾淨，避免 404 或 舊資料殘留
    for d in ["area", "life"]: 
        if (root/d).exists(): shutil.rmtree(root/d)
        (root/d).mkdir(exist_ok=True)
        
    # 清理舊的物件頁面資料夾 (p0, p1, p2...)
    for p in root.glob("p*"):
        if p.is_dir() and re.match(r'^p\d+$', p.name): 
            shutil.rmtree(p)

    # B. 載入座標快取：提升地圖標記的生成速度
    geocache = {}
    if GEOCACHE_PATH.exists():
        try:
            raw_cache = json.loads(GEOCACHE_PATH.read_text(encoding="utf-8"))
            if isinstance(raw_cache, dict): geocache = raw_cache
        except Exception as e:
            print(f"⚠️ 座標快取載入失敗 (將重新查詢): {e}")

    # C. 遠端資料獲取：從 Google 試算表同步最新房訊
    try:
        res = requests.get(SHEET_CSV_URL, timeout=30)
        res.encoding = "utf-8-sig"
        reader = list(csv.DictReader(res.text.splitlines()))
    except Exception as e:
        print(f"❌ 雲端試算表連線失敗: {e}"); return
    
    # 初始化數據池
    all_items, map_data, sitemap_urls = [], [], [f"{BASE_URL}/"]

    # --- D. 核心循環：逐一生成精品的物件詳情網頁 ---
    for i, row in enumerate(reader):
        # 數據清洗：移除空白字元
        d = {norm(k): norm(v) for k, v in row.items() if k}
        
        # 狀態過濾：若設為 OFF 或是案名空白則不顯示
        if d.get("狀態", "").upper() in ["OFF", "FALSE"] or not d.get("案名"): 
            continue
        
        slug = f"p{i}"
        (root / slug).mkdir(exist_ok=True)
        item_path = f"/{PROJECT_NAME}/{slug}/"
        sitemap_urls.append(f"{BASE_URL}/{slug}/")
        
        imgs = normalize_imgs(d.get("圖片網址", ""))
        price_val, size_val = d.get("價格", "面議"), d.get("坪數", "0")
        
        # 地圖座標連動邏輯：優先從快取中提取
        addr = d.get("地址", f"台中市{d.get('區域')}{d.get('案名')}")
        geo = geocache.get(addr)
        if geo and isinstance(geo, dict) and "lat" in geo:
            map_data.append({
                "name": d['案名'], "price": price_val, "url": item_path, 
                "lat": geo["lat"], "lng": geo["lng"], "img": imgs[0]
            })

        # 【旗艦設計】：生成精品級詳情頁內容 (整合大圖漸層、專業顧問模組)
        detail_html = f"""<div class="container">
            <div class="header"><a href="/{PROJECT_NAME}/" class="logo">← {SITE_TITLE}</a></div>
            
            <div style="position:relative; height:520px; overflow:hidden;">
                <img src="{imgs[0]}" style="width:100%; height:100%; object-fit:cover;">
                <div style="position:absolute; bottom:0; left:0; width:100%; height:280px; background:linear-gradient(to top, #fff, transparent);"></div>
            </div>

            <div style="padding:0 50px 100px;">
                <div style="color:var(--gold); font-weight:900; font-size:14px; letter-spacing:4px; margin-bottom:20px; text-transform:uppercase;">Luxury Real Estate Expert Analysis</div>
                <h1 style="font-size:48px; font-weight:900; color:var(--navy); margin:0 0 15px; letter-spacing:-2px;">{esc(d['案名'])}</h1>
                <div style="font-size:60px; color:var(--gold); font-weight:950; margin-bottom:50px; letter-spacing:-3px;">{esc(price_val)}</div>
                
                <div style="margin-bottom:55px;">
                    <span class="badge">📍 {esc(d.get('區域'))}精選</span>
                    <span class="badge">🏠 {esc(d.get('用途'))}性質</span>
                    <span class="badge">📐 {esc(size_val)}坪寬闊空間</span>
                    <span class="badge">🛋️ {esc(d.get('格局','實地現況'))}</span>
                </div>
                
                <div style="line-height:2.5; font-size:20px; color:#475569; background:#F8FAFC; padding:55px; border-radius:55px; border:1.5px solid #F1F5F9; margin-bottom:70px; box-shadow:inset 0 2px 10px rgba(0,0,0,0.02);">
                    <div style="font-weight:900; color:var(--navy); margin-bottom:25px; font-size:24px; border-left:7px solid var(--gold); padding-left:20px; letter-spacing:1px;">專業置產分析與物件特色</div>
                    {esc(d.get('描述','')).replace('、','<br>• ')}
                </div>

                <div style="background:#fff; border-radius:55px; padding:50px; border:1.5px solid #F1F5F9; box-shadow:var(--shadow-lg);">
                    <div style="display:flex; align-items:center; gap:30px; margin-bottom:20px;">
                        <img src="{IMG_RAW_BASE}agent_photo.jpg" style="width:110px; height:110px; border-radius:50%; object-fit:cover; border:6px solid #F8FAFC; box-shadow:0 10px 30px rgba(0,0,0,0.1);" onerror="this.src='https://placehold.co/150x150?text=SK-L'">
                        <div>
                            <div style="font-size:30px; font-weight:950; color:var(--navy);">{esc(MY_NAME)}</div>
                            <div style="font-size:16px; color:#94a3b8; font-weight:800; letter-spacing:1px;">大台中房地產專屬顧問</div>
                        </div>
                    </div>
                    {LEGAL_INFO_HTML}
                    <a href="{MY_LINE_URL}" target="_blank" style="display:block; background:var(--green); color:#fff; text-decoration:none; text-align:center; padding:28px; border-radius:28px; font-weight:950; margin-top:50px; font-size:21px; box-shadow:0 15px 45px rgba(16,185,129,0.4); transition:0.3s;" onmouseover="this.style.transform='scale(1.02)'" onmouseout="this.style.transform='scale(1)'">💬 立即聯繫，索取完整物件分析報告</a>
                </div>
                
                <a href="https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(addr)}" target="_blank" style="display:block; text-align:center; padding:25px; border:2.5px solid var(--navy); color:var(--navy); text-decoration:none; border-radius:28px; font-weight:950; margin-top:55px; font-size:17px; transition:0.3s;" onmouseover="this.style.background='#0F172A'; this.style.color='#fff';">📍 在 Google 地圖上查看案場位置</a>
            </div>
            
            <div class="action-bar"><a class="btn btn-call" href="tel:{MY_PHONE}">📞 服務專線</a><a class="btn btn-line" href="{MY_LINE_URL}" target="_blank">💬 LINE 諮詢</a></div>
        </div>"""
        
        # 寫入單一物件頁面 (SEO 友好的結構)
        (root / slug / "index.html").write_text(f"<!doctype html><html lang='zh-TW'>{get_head(d['案名'], d.get('描述',''), imgs[0])}<body>{detail_html}</body></html>", encoding="utf-8")
        
        # 將物件存入列表供首頁使用
        all_items.append({
            "name": d['案名'], "area": d.get('區域'), "type": d.get('用途'), 
            "price": price_val, "price_num": get_num(price_val), 
            "size_num": get_num(size_val), "img": imgs[0], "url": item_path
        })# ============================================================
    # 6. SEO 置產專欄系統 (Life Posts：收割長尾搜尋流量)
    # ============================================================
    if POSTS_DIR.exists():
        # 掃描所有 Markdown 專業文章
        for md_file in POSTS_DIR.glob("*.md"):
            post_title = md_file.stem
            # 檔案名稱即為網址，進行 URL 編碼以支援中文
            slug = urllib.parse.quote(post_title)
            (root / "life" / slug).mkdir(parents=True, exist_ok=True)
            
            # 讀取內容並將換行轉為 HTML 標籤
            raw_content = md_file.read_text(encoding="utf-8")
            html_content = raw_content.replace('\n', '<br>')
            
            # 【設計亮點】：打造如精品雜誌般的閱讀體驗
            post_html = f"""<div class="container">
                <div class="header"><a href="/{PROJECT_NAME}/" class="logo">← {SITE_TITLE}</a></div>
                <div style="padding:120px 60px; max-width:900px; margin:auto; line-height:2.6; font-size:21px;">
                    <div style="color:var(--gold); font-weight:900; font-size:15px; letter-spacing:5px; margin-bottom:25px; text-transform:uppercase;"> 專業置產專欄 ANALYSIS </div>
                    <h1 style="color:var(--navy); font-size:52px; margin-bottom:60px; font-weight:950; letter-spacing:-2px; line-height:1.2;">{esc(post_title)}</h1>
                    <div style="color:#475569; letter-spacing:0.5px;">
                        {html_content}
                    </div>
                    
                    <div style="margin-top:100px; padding:60px; border-radius:45px; background:#F8FAFC; text-align:center; border:1px solid #E2E8F0;">
                        <h3 style="color:var(--navy); font-size:28px; margin-bottom:20px; font-weight:900;">對台中置產有更多疑問？</h3>
                        <p style="font-size:18px; color:#64748B; margin-bottom:40px;">世塏為您提供一對一的市場數據分析與深度物件評估。</p>
                        <a href="{MY_LINE_URL}" target="_blank" style="display:inline-block; background:var(--green); color:#fff; padding:22px 50px; border-radius:20px; text-decoration:none; font-weight:950; font-size:18px; box-shadow:0 15px 35px rgba(16,185,129,0.3);">💬 立即透過 LINE 諮詢</a>
                    </div>
                </div>
            </div>"""
            
            # 生成文章獨立頁面
            (root / "life" / slug / "index.html").write_text(f"<!doctype html><html lang='zh-TW'>{get_head(post_title)}<body>{post_html}</body></html>", encoding="utf-8")
            sitemap_urls.append(f"{BASE_URL}/life/{slug}/")

    # ============================================================
    # 7. 旗艦首頁組裝：頂級搜尋面板與網格結構
    # ============================================================
    # 自動提取試算表中的區域，動態生成下拉選單選項
    unique_areas = sorted(set(x['area'] for x in all_items if x['area']))
    area_opts = "".join([f'<option value="{a}">{a}</option>' for a in unique_areas])
    
    # 這裡開始定義首頁的 HTML 骨架
    home_html_start = f"""<div class="container">
        <div class="header"><div class="logo">{SITE_TITLE}</div></div>
        
        <div id="map"></div>
        
        <div class="search-box">
            <div class="search-item">
                <label class="search-label">行政區域</label>
                <select class="search-select" id="s-area">
                    <option value="all">不限區域 (台中全區)</option>
                    {area_opts}
                </select>
            </div>
            <div class="search-item">
                <label class="search-label">房屋類型</label>
                <select class="search-select" id="s-type">
                    <option value="all">不限物件類型</option>
                    <option value="透天">透天/別墅</option>
                    <option value="大樓">電梯大樓/華廈</option>
                    <option value="土地">土地/農地/工業地</option>
                    <option value="店面">店面/辦公/其他</option>
                </select>
            </div>
            <div class="search-item">
                <label class="search-label">預算範圍 (萬元)</label>
                <div style="display:flex; gap:12px;">
                    <input class="search-input" id="s-min-p" placeholder="最低" style="width:50%;">
                    <input class="search-input" id="s-max-p" placeholder="最高" style="width:50%;">
                </div>
            </div>
            <button class="search-btn" onclick="executeSearch()">🔍 立即搜尋大台中精選房產</button>
        </div>
        
        <div id="list-start"></div>
"""# --- G. 首頁物件網格組裝 (具備動態過濾數據屬性) ---
        # 將資料庫中的物件轉化為具備「數據指紋」的精品卡片
        home_cards = "".join([f'''
            <a href="{it["url"]}" class="card-anchor" 
               data-area="{it["area"]}" 
               data-type="{it["type"]}" 
               data-price-num="{it["price_num"]}" 
               data-size-num="{it["size_num"]}">
                <div class="card">
                    <div style="overflow:hidden;">
                        <img src="{it["img"]}" loading="lazy" alt="{esc(it["name"])}">
                    </div>
                    <div class="card-body">
                        <div style="color:var(--gold); font-size:12px; font-weight:900; margin-bottom:10px; letter-spacing:1px;">
                            台中精選 · {esc(it["area"])}
                        </div>
                        <h3 class="card-title">{esc(it["name"])}</h3>
                        <div class="card-price">{esc(it["price"])}</div>
                        <div style="margin-top:25px; font-size:11px; color:var(--navy); font-weight:900; opacity:0.3; text-align:right; letter-spacing:2px; text-transform:uppercase;">
                            Explore Details →
                        </div>
                    </div>
                </div>
            </a>''' for it in all_items[::-1]]) # 最新上架的排在最前面

        # 組合首頁最終 HTML
        home_html_end = f"""
        <div class="grid">
            {home_cards}
        </div>
        
        <div style="text-align:center; padding:80px 20px; color:#cbd5e0; font-size:12px; letter-spacing:1.5px; font-family:'Inter';">
            <div style="margin-bottom:15px; color:#94a3b8; font-weight:700;">{SITE_TITLE} PREMIUM SELECTION</div>
            © 2026 {MY_NAME}｜台中置產顧問 · 專業誠信 · 卓越品質
        </div>

        <div class="action-bar">
            <a class="btn btn-call" href="tel:{MY_PHONE}">📞 立即通話</a>
            <a class="btn btn-line" href="{MY_LINE_URL}" target="_blank">💬 LINE 諮詢</a>
        </div>
    </div>"""

        # 寫入首頁檔案 (帶有地圖數據與 JS 互動)
        (root / "index.html").write_text(f"<!doctype html><html lang='zh-TW'>{get_head(SITE_TITLE, is_home=True, map_data=map_data)}<body>{home_html_start}{home_html_end}</body></html>", encoding="utf-8")

    # --- H. 旗艦版 Sitemap 索引生成 (SEO 戰力的保證) ---
    # 自動掃描所有生成的頁面網址，並生成標準 XML 格式供 Google 爬蟲抓取
    xml_header = '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    xml_body = "".join([f'''
    <url>
        <loc>{u}</loc>
        <lastmod>{datetime.now().strftime("%Y-%m-%d")}</lastmod>
        <changefreq>daily</changefreq>
        <priority>{"1.0" if u.endswith("/") else "0.8"}</priority>
    </url>''' for u in sorted(set(sitemap_urls))])
    
    # 寫入 Sitemap 檔案
    (root / "sitemap.xml").write_text(xml_header + xml_body + '</urlset>', encoding="utf-8")

    print("--------------------------------------------------")
    print(f"✅ 【SK-L 21.0 旗艦美學版】建置成功！")
    print(f"📊 物件點位：{len(map_data)} 處")
    print(f"📝 專業文章：{len(list(POSTS_DIR.glob('*.md'))) if POSTS_DIR.exists() else 0} 篇")
    print(f"🌐 網址目錄：{BASE_URL}/")
    print("--------------------------------------------------")

# ============================================================
# 8. 程式進入點 (確保 Actions 執行時啟動建置)
# ============================================================
if __name__ == "__main__":
    try:
        build()
    except Exception as e:
        print(f"❌ 建置過程中發生錯誤: {e}")
