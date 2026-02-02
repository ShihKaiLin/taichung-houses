import os, csv, requests, html, shutil, re, json
from pathlib import Path
from datetime import datetime

# ============================================================
# 核心配置 (世塏僅需檢查這區)
# ============================================================
CONFIG = {
    "PROJECT": "taichung-houses",
    "SHEET_URL": "https://docs.google.com/spreadsheets/d/e/2PACX-1vQShAl0-TbUU0MQdYVe53im2T6lXQgh_7g-bdL6HHpIBFtA2yfIAMbPw4J9RgZUkROb9AAiMhnRC0kH/pub?output=csv",
    "MAP_KEY": os.getenv("MAPS_API_KEY", "AIzaSyDzgnI2Ucv622CRkWwo2GE5JRrs_Y4HQY0"),
    "AGENT": {"name": "林世塏", "phone": "0938-615-351", "line": "https://line.me/ti/p/FDsMyAYDv_"},
    "THEME": {"dark": "#0F172A", "gold": "#B59461", "bg": "#F8FAFC"}
}

# ============================================================
# 視覺系統 (CSS) - 已優化轉義邏輯，防止地圖失效
# ============================================================
CSS = f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;600;900&family=Noto+Sans+TC:wght@300;500;900&display=swap');
    :root {{ --p: {CONFIG['THEME']['dark']}; --a: {CONFIG['THEME']['gold']}; --bg: {CONFIG['THEME']['bg']}; }}
    body {{ font-family: 'Inter', 'Noto Sans TC', sans-serif; margin:0; background:var(--bg); color:var(--p); }}
    .header {{ position:sticky; top:0; z-index:2000; background:rgba(255,255,255,0.9); backdrop-filter:blur(15px); padding:20px 50px; display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid rgba(0,0,0,0.05); }}
    .logo {{ font-weight:900; font-size:22px; letter-spacing:4px; color:var(--p); text-decoration:none; }}
    #map {{ height:500px; width:100%; filter: grayscale(30%); }}
    .search-bar {{ width:90%; max-width:1000px; margin:-40px auto 0; position:relative; z-index:1500; background:#fff; padding:30px; border-radius:20px; box-shadow:0 20px 50px rgba(0,0,0,0.1); display:flex; gap:20px; align-items:flex-end; }}
    .grid {{ display:grid; grid-template-columns:repeat(auto-fill, minmax(350px, 1fr)); gap:40px; padding:80px 50px; }}
    .card {{ background:#fff; border-radius:12px; overflow:hidden; transition:0.4s; text-decoration:none; color:inherit; box-shadow:0 10px 30px rgba(0,0,0,0.05); }}
    .card:hover {{ transform:translateY(-10px); box-shadow:0 20px 40px rgba(0,0,0,0.1); }}
    .card img {{ width:100%; height:280px; object-fit:cover; }}
    .card-body {{ padding:20px; }}
    .card-title {{ font-size:20px; font-weight:900; margin:10px 0; }}
    .card-price {{ font-size:28px; color:var(--a); font-weight:300; }}
    .action-bar {{ position:fixed; bottom:30px; left:50%; transform:translateX(-50%); width:90%; max-width:500px; padding:10px; display:flex; gap:10px; background:var(--p); border-radius:15px; z-index:3000; box-shadow:0 20px 40px rgba(0,0,0,0.3); }}
    .btn {{ flex:1; text-align:center; padding:15px; border-radius:10px; text-decoration:none; font-weight:900; font-size:14px; color:#fff; }}
    .btn-line {{ background:#06C755; }}
</style>
"""

# ============================================================
# 核心引擎 (Engine)
# ============================================================
class SKL_Portal:
    def __init__(self):
        self.points = []
        self.items = []

    def build_page(self, title, content, is_home=False):
        # 解決地圖消失的關鍵：JS 中的大括號必須與 Python f-string 隔離
        map_html = ""
        if is_home:
            map_data = json.dumps(self.points, ensure_ascii=False)
            map_html = f"""
            <script src="https://maps.googleapis.com/maps/api/js?key={CONFIG['MAP_KEY']}&callback=initMap" async defer></script>
            <script>
                function initMap() {{
                    const map = new google.maps.Map(document.getElementById('map'), {{
                        center: {{lat: 24.162, lng: 120.647}}, zoom: 13,
                        styles: [{{"featureType":"all","stylers":[{{"saturation":-80}}]}}]
                    }});
                    const iw = new google.maps.InfoWindow();
                    const pts = {map_data};
                    pts.forEach(p => {{
                        if(!p.lat) return;
                        const m = new google.maps.Marker({{ position:{{lat:parseFloat(p.lat), lng:parseFloat(p.lng)}}, map:map }});
                        m.addListener('click', () => {{
                            iw.setContent(`<div style="padding:10px;width:150px;"><img src="${{p.img}}" style="width:100%"><h4 style="margin:5px 0">${{p.name}}</h4><div style="color:#B59461;font-weight:900">${{p.price}}萬</div><a href="${{p.url}}" style="font-size:12px">點擊查看</a></div>`);
                            iw.open(map, m);
                        }});
                    }});
                }}
                function doSearch() {{
                    const a = document.getElementById('s-area').value;
                    document.querySelectorAll('.card-anchor').forEach(c => {{
                        c.style.display = (a === 'all' || c.dataset.area === a) ? 'block' : 'none';
                    }});
                }}
            </script>"""
        
        return f"""<!DOCTYPE html><html lang="zh-TW"><head><meta charset="utf-8">
        <meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title>{CSS}{map_html}</head>
        <body>{content}</body></html>"""

    def run(self):
        # 清理舊資料
        for folder in ["area", "life"]:
            if Path(folder).exists(): shutil.rmtree(folder)
            Path(folder).mkdir(exist_ok=True)
            
        # 讀取試算表
        res = requests.get(CONFIG["SHEET_URL"])
        res.encoding = "utf-8-sig"
        rows = list(csv.DictReader(res.text.splitlines()))

        for i, row in enumerate(rows):
            name = row.get("案名", "").strip()
            if not name or row.get("狀態", "").upper() == "OFF": continue
            
            slug = f"p{i}"
            Path(slug).mkdir(exist_ok=True)
            img_raw = row.get("圖片網址", "")
            img = img_raw.split('|')[0] if "|" in img_raw else img_raw
            if not img.startswith("http"):
                img = f"https://raw.githubusercontent.com/ShihKaiLin/{CONFIG['PROJECT']}/main/images/{img.lstrip('/')}"
            
            url = f"/{CONFIG['PROJECT']}/{slug}/"
            if row.get("lat") and row.get("lng"):
                self.points.append({"name":name, "price":row.get("價格"), "img":img, "url":url, "lat":row["lat"], "lng":row["lng"]})
            
            # 詳情頁內容
            detail_body = f"""
            <div class="header"><a href="/{CONFIG['PROJECT']}/" class="logo">SK-L</a></div>
            <img src="{img}" style="width:100%;height:450px;object-fit:cover;">
            <div style="padding:50px 30px;max-width:800px;margin:auto;">
                <h1 style="font-size:40px;">{name}</h1>
                <div style="font-size:50px;color:var(--a);">{row.get('價格')}萬</div>
                <p style="font-size:18px;line-height:2;margin-top:30px;">{row.get('描述','')}</p>
            </div>
            <div class="action-bar"><a class="btn" href="tel:{CONFIG['AGENT']['phone']}">📞 聯絡諮詢</a><a class="btn btn-line" href="{CONFIG['AGENT']['line']}">💬 LINE 詢問</a></div>
            """
            Path(f"{slug}/index.html").write_text(self.build_page(name, detail_body), encoding="utf-8")
            self.items.append(row)

        # 首頁生成
        areas = sorted(set(r.get("區域") for r in self.items if r.get("區域")))
        opts = "".join([f'<option value="{a}">{a}</option>' for a in areas])
        cards = ""
        for it in self.items[::-1]:
            img_raw = it.get("圖片網址", "")
            img = img_raw.split('|')[0] if "|" in img_raw else img_raw
            if not img.startswith("http"):
                img = f"https://raw.githubusercontent.com/ShihKaiLin/{CONFIG['PROJECT']}/main/images/{img.lstrip('/')}"
            
            idx = rows.index(it)
            cards += f"""<a href="/{CONFIG['PROJECT']}/p{idx}/" class="card-anchor" data-area="{it.get('區域')}">
                <div class="card"><img src="{img}"><div class="card-body">
                <div style="font-size:12px;color:var(--a);font-weight:900">{it.get('區域')}</div>
                <div class="card-title">{it.get('案名')}</div>
                <div class="card-price">{it.get('價格')}萬</div>
                </div></div></a>"""
        
        home_body = f"""
        <div class="header"><div class="logo">SK-L 大台中地產戰略</div></div>
        <div id="map"></div>
        <div class="search-bar">
            <div style="flex:1"><label style="font-size:11px;font-weight:900">區域</label>
            <select id="s-area" style="width:100%;padding:10px;border:none;border-bottom:1px solid #ddd"><option value="all">台中全區</option>{opts}</select></div>
            <button onclick="doSearch()" style="background:var(--p);color:#fff;border:none;padding:12px 30px;border-radius:8px;cursor:pointer">搜尋</button>
        </div>
        <div class="grid">{cards}</div>
        <div class="action-bar"><a class="btn" href="tel:{CONFIG['AGENT']['phone']}">📞 立即撥打</a><a class="btn btn-line" href="{CONFIG['AGENT']['line']}">💬 LINE 諮詢</a></div>
        """
        Path("index.html").write_text(self.build_page("SK-L 大台中地產", home_body, True), encoding="utf-8")

if __name__ == "__main__":
    SKL_Portal().run()

