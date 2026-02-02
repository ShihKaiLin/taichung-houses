import os, csv, requests, html, shutil, re, json
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup

# ============================================================
# 1. 核心品牌配置 (SK-L Agency Branding)
# ============================================================
SITE_TITLE = "SK-L 大台中地產戰略"
PROJECT_NAME = "taichung-houses"
BASE_URL = f"https://shihkailin.github.io/{PROJECT_NAME}"
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQShAl0-TbUU0MQdYVe53im2T6lXQgh_7g-bdL6HHpIBFtA2yfIAMbPw4J9RgZUkROb9AAiMhnRC0kH/pub?output=csv"
MAP_KEY = os.getenv("MAPS_API_KEY", "AIzaSyDzgnI2Ucv622CRkWwo2GE5JRrs_Y4HQY0")

AGENT_INFO = {
    "name": "林世塏", 
    "title": "大台中房產置產顧問",
    "phone": "0938-615-351", 
    "line": "https://line.me/ti/p/FDsMyAYDv_",
    "photo": f"https://raw.githubusercontent.com/ShihKaiLin/{PROJECT_NAME}/main/images/agent_photo.jpg"
}

# ============================================================
# 2. 旗艦級 CSS 視覺系統 (參考 TamsuiHome 質感)
# ============================================================
CSS = f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@300;500;700;900&display=swap');
    :root {{ --navy: #0A192F; --gold: #B59461; --bg: #F8FAFC; }}
    * {{ box-sizing: border-box; transition: all 0.3s ease; }}
    body {{ font-family: 'Noto Sans TC', sans-serif; margin:0; background:var(--bg); color:var(--navy); line-height:1.6; }}
    .navbar {{ position:fixed; top:0; width:100%; z-index:5000; background:rgba(255,255,255,0.95); backdrop-filter:blur(10px); padding:15px 50px; display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid rgba(0,0,0,0.05); }}
    .logo {{ font-weight:900; font-size:20px; letter-spacing:3px; text-decoration:none; color:var(--navy); }}
    .hero {{ height:85vh; background: linear-gradient(rgba(10,25,47,0.4), rgba(10,25,47,0.4)), url('https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=1920&q=80') center/cover; display:flex; align-items:center; justify-content:center; text-align:center; color:#fff; }}
    .hero-content h1 {{ font-size:60px; font-weight:900; margin:0; letter-spacing:8px; }}
    #map {{ height:450px; width:100%; filter: grayscale(100%) contrast(90%); }}
    .search-section {{ width:90%; max-width:1100px; margin:-60px auto 80px; background:#fff; padding:40px; border-radius:15px; box-shadow:0 30px 60px rgba(0,0,0,0.1); position:relative; z-index:1000; display:flex; gap:20px; align-items:flex-end; }}
    .grid {{ display:grid; grid-template-columns:repeat(auto-fill, minmax(380px, 1fr)); gap:50px; padding:0 50px 100px; }}
    .card {{ background:#fff; text-decoration:none; color:inherit; overflow:hidden; }}
    .card-img {{ width:100%; height:300px; object-fit:cover; border-radius:8px; }}
    .about-section {{ background:#fff; padding:100px 50px; display:flex; align-items:center; gap:80px; }}
    .about-img {{ width:450px; height:600px; object-fit:cover; border-radius:15px; box-shadow:30px 30px 0 var(--gold); }}
    .contact-bar {{ position:fixed; bottom:40px; left:50%; transform:translateX(-50%); width:90%; max-width:600px; background:var(--navy); padding:15px; border-radius:20px; display:flex; gap:15px; z-index:10000; box-shadow:0 20px 50px rgba(0,0,0,0.3); }}
    .btn-contact {{ flex:1; text-align:center; padding:18px; border-radius:12px; text-decoration:none; color:#fff; font-weight:900; }}
    .btn-line {{ background:#06C755; }}
    @media (max-width:768px) {{ .navbar {{ padding:15px 20px; }} .about-section {{ flex-direction:column; }} .about-img {{ width:100%; height:400px; }} .hero-content h1 {{ font-size:36px; }} }}
</style>
"""

def esc(s): return html.escape(str(s or "").strip())

class SKL_Agency:
    def __init__(self):
        self.points = []
        self.items = []

    def build_layout(self, title, body, is_home=False):
        map_js = ""
        if is_home:
            data = json.dumps(self.points, ensure_ascii=False)
            map_js = f"""
            <script src="https://maps.googleapis.com/maps/api/js?key={MAP_KEY}&callback=initMap" async defer></script>
            <script>
                function initMap() {{
                    const map = new google.maps.Map(document.getElementById('map'), {{ center: {{lat:24.162, lng:120.647}}, zoom:13, disableDefaultUI:true, styles:[{{"featureType":"all","stylers":[{{"saturation":-100}}]}}] }});
                    const iw = new google.maps.InfoWindow();
                    const pts = {data};
                    pts.forEach(p => {{
                        const m = new google.maps.Marker({{ position:{{lat:parseFloat(p.lat), lng:parseFloat(p.lng)}}, map }});
                        m.addListener('click', () => {{ iw.setContent(`<div style="padding:10px;width:150px;"><img src="${{p.img}}" style="width:100%"><h4 style="margin:5px 0">${{p.name}}</h4><a href="${{p.url}}">查看詳情</a></div>`); iw.open(map, m); }});
                    }});
                }}
            </script>"""
        return f"<!DOCTYPE html><html lang='zh-TW'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>{esc(title)}</title>{CSS}{map_js}</head><body>{body}</body></html>"

    def run(self):
        for f in ["area", "life"]:
            if Path(f).exists(): shutil.rmtree(f)
            Path(f).mkdir(exist_ok=True)
        res = requests.get(SHEET_URL)
        res.encoding = "utf-8-sig"
        rows = list(csv.DictReader(res.text.splitlines()))
        for i, r in enumerate(rows):
            name = r.get("案名", "").strip()
            if not name or r.get("狀態", "").upper() == "OFF": continue
            img = r.get("圖片網址", "").split('|')[0]
            if not img.startswith("http"): img = f"https://raw.githubusercontent.com/ShihKaiLin/{PROJECT_NAME}/main/images/{img.lstrip('/')}"
            slug = f"p{i}"
            Path(slug).mkdir(exist_ok=True)
            url = f"/{PROJECT_NAME}/{slug}/"
            if r.get("lat") and r.get("lng"): self.points.append({"name":name, "price":r.get("價格"), "img":img, "url":url, "lat":r["lat"], "lng":r["lng"]})
            detail = f"""<nav class="navbar"><a href="/{PROJECT_NAME}/" class="logo">SK-L AGENCY</a></nav><div style="height:60vh; background:url('{img}') center/cover;"></div><div style="padding:80px 50px; max-width:900px; margin:auto;"><h1>{esc(name)}</h1><div style="font-size:50px; color:var(--gold);">{esc(r.get('價格'))}萬</div><p style="font-size:20px; line-height:2.2;">{esc(r.get('描述',''))}</p></div>"""
            Path(f"{slug}/index.html").write_text(self.build_layout(name, detail), encoding="utf-8")
            self.items.append(r)
        
        opts = "".join([f"<option value='{a}'>{a}</option>" for a in sorted(set(x.get('區域') for x in self.items if x.get('區域')))])
        cards = "".join([f"<a href='/{PROJECT_NAME}/p{rows.index(x)}/' class='card-anchor' data-area='{x.get('區域')}'><div class='card'><img src='{self.points[self.items.index(x)]['img'] if self.items.index(x) < len(self.points) else ''}' class='card-img'><div class='card-body'><div style='color:var(--gold); font-weight:700;'>{x.get('區域')}</div><h3>{x.get('案名')}</h3><div style='font-size:24px;'>{x.get('價格')}萬</div></div></div></a>" for x in self.items[::-1]])
        home = f"""<nav class="navbar"><a href="#" class="logo">SK-L REAL ESTATE</a></nav><section class="hero"><div class="hero-content"><h1>大台中置產專家</h1><p>{AGENT_INFO['name']} · 深耕台中精華區</p></div></section><div id="map"></div><div class="search-section"><div style="flex:1"><label>行政區域</label><select id="s-area" style="width:100%; padding:10px;"><option value="all">台中全區</option>{opts}</select></div><button class="btn-contact" style="background:var(--navy); padding:10px 40px;">搜尋</button></div><div class="grid">{cards}</div><section class="about-section"><img src="{AGENT_INFO['photo']}" class="about-img"><div class="about-content"><h3>{AGENT_INFO['name']}</h3><p>{AGENT_INFO['title']}<br>我們致力於為每一位客戶提供精準的市場分析。我們不只是仲介，更是您的置產顧問。</p></div></section><div class="contact-bar"><a class="btn-contact btn-line" href="{AGENT_INFO['line']}">💬 LINE 諮詢</a></div>"""
        Path("index.html").write_text(self.build_layout(SITE_TITLE, home, True), encoding="utf-8")

if __name__ == "__main__":
    SKL_Agency().run()
