import os, csv, requests, html, shutil, re, json
from pathlib import Path
from datetime import datetime

# ============================================================
# 1. 核心品牌配置 (SK-L Agency Branding)
# ============================================================
CONFIG = {
    "PROJECT": "taichung-houses",
    "SHEET_URL": "https://docs.google.com/spreadsheets/d/e/2PACX-1vQShAl0-TbUU0MQdYVe53im2T6lXQgh_7g-bdL6HHpIBFtA2yfIAMbPw4J9RgZUkROb9AAiMhnRC0kH/pub?output=csv",
    "MAP_KEY": os.getenv("MAPS_API_KEY", "AIzaSyDzgnI2Ucv622CRkWwo2GE5JRrs_Y4HQY0"),
    "AGENT": {
        "name": "林世塏", 
        "title": "大台中房產置產顧問",
        "phone": "0938-615-351", 
        "line": "https://line.me/ti/p/FDsMyAYDv_",
        "photo": "https://raw.githubusercontent.com/ShihKaiLin/taichung-houses/main/images/agent_photo.jpg"
    },
    "THEME": {"navy": "#0A192F", "gold": "#B59461", "light": "#F8FAFC"}
}

# ============================================================
# 2. 旗艦級 CSS 視覺系統 (參考 TamsuiHome 質感)
# ============================================================
CSS = f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@300;500;700;900&display=swap');
    
    :root {{ --navy: {CONFIG['THEME']['navy']}; --gold: {CONFIG['THEME']['gold']}; --bg: {CONFIG['THEME']['light']}; }}
    
    * {{ box-sizing: border-box; transition: all 0.3s ease; }}
    body {{ font-family: 'Noto Sans TC', sans-serif; margin:0; background:var(--bg); color:var(--navy); line-height:1.6; }}
    
    /* 導航欄 */
    .navbar {{ position:fixed; top:0; width:100%; z-index:5000; background:rgba(255,255,255,0.95); backdrop-filter:blur(10px); padding:15px 50px; display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid rgba(0,0,0,0.05); }}
    .logo {{ font-weight:900; font-size:20px; letter-spacing:3px; text-decoration:none; color:var(--navy); }}
    .nav-links {{ display:flex; gap:30px; }}
    .nav-links a {{ text-decoration:none; color:var(--navy); font-weight:700; font-size:14px; opacity:0.7; }}
    .nav-links a:hover {{ opacity:1; color:var(--gold); }}

    /* 首頁大圖 (Hero) */
    .hero {{ height:85vh; background: linear-gradient(rgba(10,25,47,0.4), rgba(10,25,47,0.4)), url('https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=1920&q=80') center/cover; display:flex; align-items:center; justify-content:center; text-align:center; color:#fff; }}
    .hero-content h1 {{ font-size:60px; font-weight:900; margin:0; letter-spacing:8px; }}
    .hero-content p {{ font-size:18px; letter-spacing:4px; opacity:0.9; margin-top:15px; }}

    /* 地圖與搜尋板塊 */
    #map {{ height:450px; width:100%; filter: grayscale(100%) contrast(90%); }}
    .search-section {{ width:90%; max-width:1100px; margin:-60px auto 80px; background:#fff; padding:40px; border-radius:15px; box-shadow:0 30px 60px rgba(0,0,0,0.1); position:relative; z-index:1000; display:flex; gap:20px; align-items:flex-end; }}
    .search-group {{ flex:1; display:flex; flex-direction:column; gap:10px; }}
    .search-group label {{ font-size:11px; font-weight:900; color:var(--gold); letter-spacing:2px; }}
    .search-group select {{ padding:15px; border:1px solid #eee; border-radius:8px; background:#fff; font-size:15px; }}
    .btn-search {{ background:var(--navy); color:#fff; border:none; padding:15px 40px; border-radius:8px; font-weight:900; cursor:pointer; }}
    .btn-search:hover {{ background:var(--gold); }}

    /* 物件展示區 */
    .section-title {{ text-align:center; margin-bottom:60px; }}
    .section-title h2 {{ font-size:32px; font-weight:900; position:relative; display:inline-block; padding-bottom:15px; }}
    .section-title h2::after {{ content:''; position:absolute; bottom:0; left:25%; width:50%; height:3px; background:var(--gold); }}
    
    .grid {{ display:grid; grid-template-columns:repeat(auto-fill, minmax(380px, 1fr)); gap:50px; padding:0 50px 100px; }}
    .card {{ background:#fff; text-decoration:none; color:inherit; overflow:hidden; }}
    .card:hover {{ transform:translateY(-10px); }}
    .card-img {{ width:100%; height:300px; object-fit:cover; border-radius:8px; }}
    .card-body {{ padding:25px 0; }}
    .card-area {{ font-size:12px; font-weight:700; color:var(--gold); letter-spacing:2px; margin-bottom:10px; }}
    .card-name {{ font-size:22px; font-weight:900; margin:0; }}
    .card-price {{ font-size:28px; font-weight:300; margin-top:15px; color:var(--navy); }}
    .card-price span {{ font-size:16px; font-weight:700; margin-left:5px; }}

    /* 顧問介紹區 */
    .about-section {{ background:#fff; padding:100px 50px; display:flex; align-items:center; gap:80px; }}
    .about-img {{ width:450px; height:600px; object-fit:cover; border-radius:15px; box-shadow:30px 30px 0 var(--gold); }}
    .about-content {{ flex:1; }}
    .about-content h3 {{ font-size:40px; font-weight:900; margin-bottom:20px; }}
    .about-content p {{ font-size:18px; color:#555; line-height:2; }}

    /* 懸浮聯絡 */
    .contact-bar {{ position:fixed; bottom:40px; left:50%; transform:translateX(-50%); width:90%; max-width:600px; background:var(--navy); padding:15px; border-radius:20px; display:flex; gap:15px; z-index:10000; box-shadow:0 20px 50px rgba(0,0,0,0.3); }}
    .btn-contact {{ flex:1; text-align:center; padding:18px; border-radius:12px; text-decoration:none; color:#fff; font-weight:900; font-size:16px; }}
    .btn-call {{ border:1px solid rgba(255,255,255,0.2); }}
    .btn-line {{ background:#06C755; }}

    @media (max-width:768px) {{
        .navbar {{ padding:15px 20px; }}
        .nav-links {{ display:none; }}
        .about-section {{ flex-direction:column; padding:60px 20px; }}
        .about-img {{ width:100%; height:400px; box-shadow:15px 15px 0 var(--gold); }}
        .hero-content h1 {{ font-size:36px; }}
        .search-section {{ flex-direction:column; width:94%; padding:25px; }}
        .grid {{ grid-template-columns:1fr; padding:20px; }}
    }}
</style>
"""

# ============================================================
# 3. 核心建置引擎 (Portal Builder)
# ============================================================
class SKL_Agency:
    def __init__(self):
        self.items = []
        self.map_points = []

    def build_layout(self, title, body_content, is_home=False):
        map_js = ""
        if is_home:
            points_json = json.dumps(self.map_points, ensure_ascii=False)
            map_js = f"""
            <script src="https://maps.googleapis.com/maps/api/js?key={CONFIG['MAP_KEY']}&callback=initMap" async defer></script>
            <script>
                function initMap() {{
                    const map = new google.maps.Map(document.getElementById('map'), {{
                        center: {{lat:24.162, lng:120.647}}, zoom:13,
                        disableDefaultUI:true, zoomControl:true,
                        styles: [{{"featureType":"all","stylers":[{{"saturation":-100}}]}}]
                    }});
                    const iw = new google.maps.InfoWindow();
                    const pts = {points_json};
                    pts.forEach(p => {{
                        const m = new google.maps.Marker({{ position:{{lat:parseFloat(p.lat), lng:parseFloat(p.lng)}}, map:map }});
                        m.addListener('click', () => {{
                            iw.setContent(`<div style="padding:15px;width:200px;"><img src="${{p.img}}" style="width:100%;border-radius:5px;"><h4 style="margin:10px 0 5px">${{p.name}}</h4><div style="color:#B59461;font-weight:900;font-size:18px">${{p.price}}萬</div><a href="${{p.url}}" style="display:block;margin-top:10px;text-align:center;background:#0A192F;color:#fff;text-decoration:none;padding:8px;border-radius:4px;font-size:12px">進入案場分析</a></div>`);
                            iw.open(map, m);
                        }});
                    }});
                }}
                function filterItems() {{
                    const area = document.getElementById('s-area').value;
                    document.querySelectorAll('.card-anchor').forEach(c => {{
                        c.style.display = (area === 'all' || c.dataset.area === area) ? 'block' : 'none';
                    }});
                }}
            </script>
            """
        return f"""<!DOCTYPE html><html lang="zh-TW"><head><meta charset="utf-8">
        <meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title>{CSS}{map_js}</head>
        <body>{body_content}</body></html>"""

    def run(self):
        # 初始化環境
        for folder in ["area", "life"]:
            if Path(folder).exists(): shutil.rmtree(folder)
            Path(folder).mkdir(exist_ok=True)

        # 抓取試算表
        res = requests.get(CONFIG["SHEET_URL"])
        res.encoding = "utf-8-sig"
        rows = list(csv.DictReader(res.text.splitlines()))

        for i, r in enumerate(rows):
            name = r.get("案名", "").strip()
            if not name or r.get("狀態", "").upper() == "OFF": continue
            
            slug = f"p{i}"
            Path(slug).mkdir(exist_ok=True)
            img_raw = r.get("圖片網址", "")
            img = img_raw.split('|')[0] if "|" in img_raw else img_raw
            if not img.startswith("http"):
                img = f"https://raw.githubusercontent.com/ShihKaiLin/{CONFIG['PROJECT']}/main/images/{img.lstrip('/')}"
            
            url = f"/{CONFIG['PROJECT']}/{slug}/"
            if r.get("lat") and r.get("lng"):
                self.map_points.append({"name":name, "price":r.get("價格"), "img":img, "url":url, "lat":r["lat"], "lng":r["lng"]})
            
            # 物件詳情頁
            detail = f"""
            <nav class="navbar"><a href="/{CONFIG['PROJECT']}/" class="logo">SK-L AGENCY</a><div class="nav-links"><a href="/{CONFIG['PROJECT']}/#listings">精選物件</a><a href="{CONFIG['AGENT']['line']}">預約看屋</a></div></nav>
            <div style="height:60vh; background:url('{img}') center/cover;"></div>
            <div style="padding:100px 50px; max-width:1000px; margin:auto;">
                <div class="card-area">{r.get('區域')} · 置產推薦</div>
                <h1 style="font-size:50px; font-weight:900; margin:10px 0;">{name}</h1>
                <div style="font-size:60px; font-weight:300; color:var(--navy);">{r.get('價格')}<span>萬</span></div>
                <div style="margin-top:50px; line-height:2.5; font-size:20px; color:#444; border-top:1px solid #eee; padding-top:50px;">
                    <h3 style="color:var(--gold);">顧問深度分析報告</h3>
                    {r.get('描述','').replace('、','<br>• ')}
                </div>
            </div>
            <div class="contact-bar"><a class="btn-contact btn-call" href="tel:{CONFIG['AGENT']['phone']}">服務專線</a><a class="btn-contact btn-line" href="{CONFIG['AGENT']['line']}">💬 LINE 諮詢</a></div>
            """
            Path(f"{slug}/index.html").write_text(self.build_layout(name, detail), encoding="utf-8")
            self.items.append(r)

        # 首頁組裝
        areas = sorted(set(x.get("區域") for x in self.items if x.get("區域")))
        opts = "".join([f'<option value="{a}">{a}</option>' for a in areas])
        cards = "".join([f"""<a href="/{CONFIG['PROJECT']}/p{rows.index(it)}/" class="card-anchor" data-area="{it.get('區域')}">
            <div class="card"><img src="{self.map_points[self.items.index(it)]['img'] if self.items.index(it) < len(self.map_points) else ''}" class="card-img">
            <div class="card-body"><div class="card-area">{it.get('區域')}</div><h3 class="card-name">{it.get('案名')}</h3><div class="card-price">{it.get('價格')}<span>萬</span></div></div></div></a>""" for it in self.items[::-1]])

        home = f"""
        <nav class="navbar"><a href="#" class="logo">SK-L REAL ESTATE</a><div class="nav-links"><a href="#listings">精選物件</a><a href="#about">關於世塏</a><a href="{CONFIG['AGENT']['line']}">委託諮詢</a></div></nav>
        <section class="hero"><div class="hero-content"><h1>大台中置產專家</h1><p>林世塏 · 提供您最具深度的房產決策建議</p></div></section>
        <div id="map"></div>
        <div class="search-section">
            <div class="search-group"><label>行政區域 LOCATION</label><select id="s-area"><option value="all">台中全區</option>{opts}</select></div>
            <button class="btn-search" onclick="filterItems()">🔍 搜尋台中物件</button>
        </div>
        <section id="listings" class="section-title"><h2>精選物件</h2><p>PREMIUM LISTINGS</p></section>
        <div class="grid">{cards}</div>
        <section id="about" class="about-section">
            <img src="{CONFIG['AGENT']['photo']}" class="about-img" onerror="this.src='https://placehold.co/450x600?text=SK-L'">
            <div class="about-content">
                <div class="card-area">ABOUT THE EXPERT</div>
                <h3>{CONFIG['AGENT']['name']}</h3>
                <p>深耕大台中房地產市場，致力於為每一位客戶提供精準的市場分析與置產建議。我們不只是仲介，更是您在資產配置路上的專業顧問。</p>
                <a href="{CONFIG['AGENT']['line']}" style="display:inline-block; margin-top:30px; color:var(--gold); font-weight:900; text-decoration:none; border-bottom:2px solid var(--gold);">更多經營理念 →</a>
            </div>
        </section>
        <div class="contact-bar"><a class="btn-contact btn-call" href="tel:{CONFIG['AGENT']['phone']}">服務專線</a><a class="btn-contact btn-line" href="{CONFIG['AGENT']['line']}">💬 LINE 諮詢</a></div>
        """
        Path("index.html").write_text(self.build_layout(SITE_TITLE, home, True), encoding="utf-8")

if __name__ == "__main__":
    SKL_Agency().run()
