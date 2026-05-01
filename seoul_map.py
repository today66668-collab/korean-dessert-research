"""
서울 개성주악 가게 지도 + 열지도
首爾開城油蜜果店家地圖 + 熱力圖
====================================
執行後會產生兩個 HTML 檔案：
- seoul_map.html：互動式地圖（點擊每個標記可看店家詳情）
- seoul_heatmap.html：熱力圖（競爭密度視覺化）
"""

import json
import re
import folium
from folium.plugins import HeatMap, MarkerCluster

# ── 載入數據 ───────────────────────────────────────
with open("gaeseong_guak.json", "r", encoding="utf-8") as f:
    data1 = json.load(f)
with open("g2.json", "r", encoding="utf-8") as f:
    data2 = json.load(f)

all_data = data1 + data2

def extract_gu(address):
    if not address: return None
    m = re.search(r'서울\s+(\S+구)', str(address))
    return m.group(1) if m else None

def clean_name(name):
    return name.replace('네이버페이', '').replace('쿠폰', '').strip()

# 手動補充的 2 間（有座標）
manual_shops = [
    {
        'name': '담장옆에국화꽃 안녕인사동점',
        'x': 126.9851,  # 인사동 좌표
        'y': 37.5739,
        'address': '서울 종로구 인사동길 49',
        'gu': '종로구',
        'reviews': 0,
        'score': 0,
        'has_juak': True,
    },
    {
        'name': '아진당 떡상점',
        'x': 126.9930,
        'y': 37.5745,
        'address': '서울 종로구 돈화문로11길 34-6',
        'gu': '종로구',
        'reviews': 0,
        'score': 0,
        'has_juak': True,
    },
]

# ── 整理店家資料 ───────────────────────────────────
shops = []
seen = set()

for d in all_data:
    name = clean_name(d.get('name', ''))
    if not name or name in seen:
        continue

    addr = d.get('roadAddress', '') or d.get('address', '')
    gu = extract_gu(addr)
    if not gu:
        continue  # 只保留首爾店家

    x = d.get('x')  # 經度 longitude
    y = d.get('y')  # 緯度 latitude
    if not x or not y:
        continue

    review_stats = d.get('reviewStats', {}) or {}
    menus = d.get('menus', []) or []
    menu_names = [m.get('name', '') for m in menus]
    has_juak = any('개성주악' in m for m in menu_names)

    seen.add(name)
    shops.append({
        'name': name,
        'x': float(x),
        'y': float(y),
        'address': addr,
        'gu': gu,
        'reviews': review_stats.get('totalCount', 0) or 0,
        'score': review_stats.get('avgRating', 0) or 0,
        'has_juak': has_juak,
    })

# 加入手動補充的店
for m in manual_shops:
    if m['name'] not in seen:
        shops.append(m)
        seen.add(m['name'])

print(f"總計 {len(shops)} 間首爾店家")

# ── 競爭強度判斷 ──────────────────────────────────
gu_max_reviews = {}
for s in shops:
    gu = s['gu']
    gu_max_reviews[gu] = max(gu_max_reviews.get(gu, 0), s['reviews'])

def get_level(gu):
    max_rev = gu_max_reviews.get(gu, 0)
    if max_rev >= 3000: return '강함 強', '#E74C3C'
    elif max_rev >= 500: return '보통 中', '#E67E22'
    else: return '약함 弱', '#27AE60'

# ── 中文店名對照 ──────────────────────────────────
name_zh = {
    '한과와락': '韓果與樂',
    '온당디저트': '溫堂甜點',
    '시에나블루': 'Siena Blue',
    '서울버터샌드': '首爾奶油三明治',
    '쓰임': '用途',
    '편': '篇',
    '가밀148': '가밀148',
    '연우연': '緣遇緣',
    '명과정 합정점': '名果亭合井店',
    '믜요': 'Mwyo',
    '감과당': '甘果堂',
    '김씨부인': '金夫人',
    '예빈당 성수본점': '禮賓堂聖水本店',
    '고호재 롯데월드몰점': '古好齋樂天世界Mall店',
    '묘방': '妙房',
    '지선정담': '知善情談',
    '연경당': '燕慶堂',
    '쭈악쭈악 서순라길': '주악주악西巡羅街',
    '오드투디저트': 'Ode to Dessert',
    '담장옆에국화꽃 안녕인사동점': '牆邊菊花花仁寺洞店',
    '아진당 떡상점': '雅眞堂年糕店',
    '밀과방': '蜜果房',
    '이끼 신당': '이끼新堂',
    '래쉬': 'Lash',
    '화양연화': '花樣年華',
    '한과와락톡톡': '韓果與樂톡톡',
}

# ════════════════════════════════════════════════
# 地圖一：互動式標記地圖
# ════════════════════════════════════════════════
m1 = folium.Map(
    location=[37.555, 126.977],
    zoom_start=12,
    tiles='CartoDB positron'
)

# 圖例 HTML
legend_html = """
<div style="position:fixed; bottom:30px; left:30px; z-index:1000;
     background:white; padding:12px 16px; border-radius:8px;
     border:1px solid #ddd; font-family:Arial; font-size:12px;
     box-shadow:2px 2px 6px rgba(0,0,0,0.2);">
  <b>경쟁 강도 | 競爭強度</b><br>
  <span style="color:#E74C3C">●</span> 강함 強（리뷰 3,000+）<br>
  <span style="color:#E67E22">●</span> 보통 中（리뷰 500+）<br>
  <span style="color:#27AE60">●</span> 약함 弱（리뷰 500 미만）<br>
  <hr style="margin:6px 0">
  <span style="font-size:10px; color:#888">마커 클릭 시 상세 정보 표시<br>點擊標記查看詳情</span>
</div>
"""
m1.get_root().html.add_child(folium.Element(legend_html))

# 標題
title_html = """
<div style="position:fixed; top:15px; left:50%; transform:translateX(-50%);
     z-index:1000; background:white; padding:8px 20px; border-radius:8px;
     border:2px solid #C0392B; font-family:Arial;
     box-shadow:2px 2px 6px rgba(0,0,0,0.2);">
  <b style="color:#C0392B; font-size:14px">서울 개성주악 가게 지도</b>
  <span style="color:#888; font-size:11px; margin-left:8px">| 首爾開城油蜜果店家地圖</span>
</div>
"""
m1.get_root().html.add_child(folium.Element(title_html))

# 添加標記
for s in shops:
    level, color = get_level(s['gu'])
    zh = name_zh.get(s['name'], '')
    reviews = s['reviews']
    score = s['score']
    has_juak = s['has_juak']

    # 彈出視窗內容
    popup_html = f"""
    <div style="font-family:Arial; min-width:220px; font-size:12px;">
        <b style="font-size:14px; color:#2C3E50">{s['name']}</b><br>
        <span style="color:#888">{zh}</span><br>
        <hr style="margin:4px 0">
        <b>구 | 區：</b>{s['gu']}<br>
        <b>경쟁 강도 | 競爭強度：</b>
        <span style="color:{color}">{level}</span><br>
        <b>리뷰 | 評論：</b>{reviews:,} 건<br>
        {"<b>평점 | 評分：</b>★" + str(score) + "<br>" if score else ""}
        <b>메뉴에 개성주악：</b>{"✅ 있음" if has_juak else "❓ 미확인"}<br>
        <hr style="margin:4px 0">
        <span style="color:#888; font-size:10px">{s['address']}</span>
    </div>
    """

    folium.CircleMarker(
        location=[s['y'], s['x']],
        radius=8 + min(s['reviews'] / 500, 8),  # 大小依評論數
        color=color,
        fill=True,
        fill_color=color,
        fill_opacity=0.7,
        popup=folium.Popup(popup_html, max_width=280),
        tooltip=f"{s['name']} | {zh}",
    ).add_to(m1)

m1.save("seoul_map.html")
print("✅ seoul_map.html 儲存完成")


# ════════════════════════════════════════════════
# 地圖二：熱力圖（競爭密度）
# ════════════════════════════════════════════════
m2 = folium.Map(
    location=[37.555, 126.977],
    zoom_start=12,
    tiles='CartoDB dark_matter'  # 深色底圖讓熱力圖更明顯
)

# 熱力圖數據（用評論數作為權重）
heat_data = []
for s in shops:
    weight = max(s['reviews'] / 1000, 0.3)  # 最小權重 0.3，最大不限
    heat_data.append([s['y'], s['x'], weight])

HeatMap(
    heat_data,
    min_opacity=0.3,
    max_zoom=13,
    radius=35,
    blur=25,
    gradient={
        '0.2': '#27AE60',
        '0.5': '#F1C40F',
        '0.8': '#E67E22',
        '1.0': '#E74C3C',
    }
).add_to(m2)

# 熱力圖標題
title2_html = """
<div style="position:fixed; top:15px; left:50%; transform:translateX(-50%);
     z-index:1000; background:rgba(0,0,0,0.7); padding:8px 20px;
     border-radius:8px; border:2px solid #E74C3C; font-family:Arial;
     color:white;">
  <b style="color:#E74C3C; font-size:14px">개성주악 경쟁 밀도 열지도</b>
  <span style="color:#aaa; font-size:11px; margin-left:8px">| 競爭密度熱力圖</span>
</div>
"""
m2.get_root().html.add_child(folium.Element(title2_html))

# 熱力圖圖例
legend2_html = """
<div style="position:fixed; bottom:30px; left:30px; z-index:1000;
     background:rgba(0,0,0,0.7); padding:12px 16px; border-radius:8px;
     border:1px solid #555; font-family:Arial; font-size:12px; color:white;">
  <b>경쟁 밀도 | 競爭密度</b><br>
  <span style="color:#E74C3C">■</span> 매우 높음 | 極高<br>
  <span style="color:#E67E22">■</span> 높음 | 高<br>
  <span style="color:#F1C40F">■</span> 보통 | 中<br>
  <span style="color:#27AE60">■</span> 낮음 | 低<br>
  <hr style="margin:6px 0; border-color:#555">
  <span style="font-size:10px; color:#aaa">
  열 강도 = 리뷰 수 기준<br>
  熱度 = 以評論數為權重
  </span>
</div>
"""
m2.get_root().html.add_child(folium.Element(legend2_html))

m2.save("seoul_heatmap.html")
print("✅ seoul_heatmap.html 儲存完成")

print()
print("두 파일을 브라우저에서 열어주세요！")
print("請用瀏覽器開啟以下兩個檔案：")
print("  📍 seoul_map.html — 互動式地圖")
print("  🔥 seoul_heatmap.html — 熱力圖")
