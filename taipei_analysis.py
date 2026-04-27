import json
import pandas as pd
from collections import Counter, defaultdict

# ── 載入資料 ──────────────────────────────────────
with open("taipei_korean.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"總評論筆數：{len(data)}")

# ── 整理成 DataFrame ───────────────────────────────
rows = []
for d in data:
    rows.append({
        "店名":     d.get("title", ""),
        "評分":     d.get("stars", ""),
        "評論":     d.get("text", "") or "",
        "評論英文": d.get("textTranslated", "") or "",
        "日期":     d.get("publishedAtDate", ""),
        "語言":     d.get("originalLanguage", ""),
        "食物評分": (d.get("reviewDetailedRating") or {}).get("Food", ""),
        "服務評分": (d.get("reviewDetailedRating") or {}).get("Service", ""),
        "環境評分": (d.get("reviewDetailedRating") or {}).get("Atmosphere", ""),
    })

df = pd.DataFrame(rows)

# ── 分析一：各店基本資料 ───────────────────────────
print("\n=== 各店評論統計 ===")
shop_stats = df.groupby("店名").agg(
    評論數=("評分", "count"),
    平均評分=("評分", lambda x: round(pd.to_numeric(x, errors="coerce").mean(), 2)),
    五星比例=("評分", lambda x: round((pd.to_numeric(x, errors="coerce") == 5).sum() / len(x) * 100, 1)),
).reset_index()

print(shop_stats.to_string(index=False))

# ── 分析二：韓式甜點關鍵字頻率 ────────────────────
keywords = {
    # 傳統韓式甜點
    "糖餅":    ["糖餅", "호떡", "hotteok"],
    "藥果":    ["藥果", "약과", "yakgwa"],
    "年糕":    ["年糕", "떡", "rice cake", "mochi"],
    "刨冰":    ["刨冰", "빙수", "bingsu", "shaved ice"],
    "紅豆":    ["紅豆", "팥", "red bean", "azuki"],
    "黑芝麻":  ["黑芝麻", "흑임자", "black sesame"],
    "艾草":    ["艾草", "쑥", "mugwort"],
    "南瓜":    ["南瓜", "단호박", "pumpkin", "squash"],
    "麻花捲":  ["麻花捲", "꽈배기", "kkwabaegi"],
    "羊羹":    ["羊羹", "양갱", "yanggang"],
    "甜米露":  ["甜米露", "식혜", "sikhye"],
    "柿子飲":  ["柿子飲", "수정과", "sujeonggwa"],
    "雙和茶":  ["雙和茶", "쌍화차"],
    "肉桂":    ["肉桂", "계피", "cinnamon"],
    "堅果":    ["堅果", "nuts", "견과류", "peanut", "花生"],
    # 口感描述
    "不太甜":  ["不太甜", "不甜", "微甜", "低甜", "減糖", "甜度剛好", "不會太甜"],
    "酥脆":    ["酥脆", "crispy", "脆", "crisp"],
    "軟糯":    ["軟糯", "chewy", "Q彈", "彈牙", "軟Q"],
    # 體驗描述
    "韓國感":  ["韓國", "韓式", "Korean", "首爾", "釜山"],
    "打卡":    ["打卡", "拍照", "IG", "instagram", "網美"],
    "回購":    ["再來", "再訪", "推薦", "必吃", "必點", "會再"],
}

# 合併所有評論（中文+英文）
all_text = " ".join([
    (d.get("text", "") or "") + " " + (d.get("textTranslated", "") or "")
    for d in data
]).lower()

print("\n=== 關鍵字出現次數 ===")
kw_results = []
for label, words in keywords.items():
    count = sum(all_text.count(w.lower()) for w in words)
    kw_results.append((label, count))

kw_results.sort(key=lambda x: -x[1])
for label, count in kw_results:
    if count > 0:
        bar = "█" * count
        print(f"  {label:8s} {count:3d}次  {bar}")

# ── 分析三：按店家統計關鍵字 ──────────────────────
print("\n=== 各店關鍵字分布 ===")
for shop in df["店名"].unique():
    shop_reviews = df[df["店名"] == shop]
    shop_text = " ".join([
        (r or "") for r in shop_reviews["評論"].tolist()
    ]).lower()

    found = []
    for label, words in keywords.items():
        count = sum(shop_text.count(w.lower()) for w in words)
        if count > 0:
            found.append(f"{label}({count})")

    avg = pd.to_numeric(shop_reviews["評分"], errors="coerce").mean()
    print(f"\n  【{shop}】平均{avg:.1f}分")
    print(f"  {' / '.join(found) if found else '無明顯關鍵字'}")

# ── 分析四：負評分析 ──────────────────────────────
negative_keywords = ["失望", "難吃", "太甜", "太貴", "份量少", "等很久",
                     "態度差", "disappointing", "overpriced", "too sweet"]

print("\n=== 負評關鍵字 ===")
neg_text = " ".join([
    (d.get("text", "") or "") for d in data
    if str(d.get("stars", "5")) in ["1", "2", "3"]
]).lower()

for kw in negative_keywords:
    count = neg_text.count(kw.lower())
    if count > 0:
        print(f"  {kw:12s} {count}次")

# ── 儲存結果 ──────────────────────────────────────
df.to_csv("taipei_reviews_clean.csv", index=False, encoding="utf-8-sig")
shop_stats.to_csv("taipei_shop_stats.csv", index=False, encoding="utf-8-sig")

print("\n\n已儲存：")
print("  taipei_reviews_clean.csv（清理後的評論資料）")
print("  taipei_shop_stats.csv（各店統計）")
