"""
韓式甜點海外市場分析程式（跨店版 v2）
========================================
支援城市：台北、東京、溫哥華
分析邏輯：只統計關鍵字出現在幾間不同的店，排除單店主打品項偏差

用法：
  把所有 JSON 檔案放在同一個資料夾，執行：
  python korean_dessert_analysis.py
"""

import json
import pandas as pd
from collections import Counter
import os

CITIES = [
    {"name": "台北",   "file": "taipei_korean.json"},
    {"name": "東京",   "file": "japan_korean.json"},
    {"name": "溫哥華", "file": "canada_korean.json"},
]

KEYWORDS = {
    "藥果 약과":      ["약과", "yakgwa", "薬菓", "ヤッカ"],
    "刨冰 빙수":      ["빙수", "bingsu", "ビンス", "かき氷", "shaved ice"],
    "糖餅 호떡":      ["호떡", "hotteok", "ホトク", "糖餅", "korean pancake"],
    "年糕 떡":        ["떡", "tteok", "トック", "年糕", "rice cake"],
    "核桃糕 호두과자": ["호두과자", "walnut cake", "walnut cookie"],
    "鯛魚燒 붕어빵":   ["붕어빵", "taiyaki", "fish-shaped"],
    "羊羹 양갱":      ["양갱", "yanggang", "ようかん"],
    "麻花捲 꽈배기":   ["꽈배기", "kkwabaegi"],
    "黑芝麻":         ["흑임자", "black sesame", "黒ごま"],
    "紅豆":           ["팥", "red bean", "あんこ", "azuki"],
    "艾草":           ["쑥", "mugwort", "よもぎ"],
    "南瓜":           ["단호박", "pumpkin", "かぼちゃ"],
    "肉桂":           ["계피", "cinnamon", "シナモン"],
    "堅果":           ["견과류", "nuts", "ナッツ", "walnut", "peanut", "almond"],
    "蜂蜜":           ["꿀", "honey", "はちみつ"],
    "不太甜":         ["甘すぎない", "甘さ控えめ", "not too sweet", "lightly sweet",
                      "subtly sweet", "不太甜", "甜度剛好"],
    "酥脆":           ["サクサク", "カリカリ", "crispy", "crunchy", "酥脆"],
    "軟糯":           ["しっとり", "もちもち", "chewy", "軟Q", "Q彈"],
    "韓國感":         ["韓国", "Korean", "韓國", "authentic"],
    "打卡拍照":       ["映え", "インスタ", "instagram", "cute", "aesthetic", "打卡"],
    "回購推薦":       ["また来たい", "リピート", "recommend", "will be back",
                      "must try", "再來", "推薦", "必吃"],
}

NEGATIVE_KEYWORDS = {
    "太甜":  ["太甜", "甘すぎ", "too sweet", "overly sweet"],
    "太貴":  ["太貴", "高い", "expensive", "overpriced", "pricey"],
    "份量少": ["份量少", "量が少ない", "small portion", "tiny"],
    "等太久": ["等太久", "待ち時間", "long wait", "waited"],
    "態度差": ["態度差", "rude", "unfriendly", "bad service"],
    "失望":  ["失望", "disappointing", "disappointed", "not worth"],
}


def load_data(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    rows = []
    for d in data:
        rows.append({
            "店名": d.get("title", "") or "",
            "評分": d.get("stars", "") or "",
            "評論": d.get("text", "") or "",
            "翻譯": d.get("textTranslated", "") or "",
            "語言": d.get("originalLanguage", "") or "",
            "日期": d.get("publishedAtDate", "") or "",
        })
    return pd.DataFrame(rows), data


def cross_shop_analysis(df, keywords):
    results = []
    for label, words in keywords.items():
        shop_counts = {}
        for shop in df["店名"].unique():
            s = df[df["店名"] == shop]
            txt = " ".join([
                (r or "") + " " + (t or "")
                for r, t in zip(s["評論"], s["翻譯"])
            ]).lower()
            count = sum(txt.count(w.lower()) for w in words)
            if count > 0:
                shop_counts[shop] = count
        shop_num = len(shop_counts)
        total = sum(shop_counts.values())
        if shop_num > 0:
            results.append((label, shop_num, total, shop_counts))
    results.sort(key=lambda x: (-x[1], -x[2]))
    return results


def shop_stats(df):
    stats = []
    for shop in df["店名"].unique():
        s = df[df["店名"] == shop]
        scores = pd.to_numeric(s["評分"], errors="coerce")
        avg = round(scores.mean(), 2)
        five_star = int((scores == 5).sum())
        stats.append({
            "店名": shop,
            "評論數": len(s),
            "平均評分": avg,
            "五星比例": f"{round(five_star / len(s) * 100, 1)}%",
        })
    return pd.DataFrame(stats)


def negative_analysis(df, neg_keywords):
    neg = df[pd.to_numeric(df["評分"], errors="coerce") <= 3]
    if neg.empty:
        return {}
    neg_txt = " ".join([
        (r or "") + " " + (t or "")
        for r, t in zip(neg["評論"], neg["翻譯"])
    ]).lower()
    return {
        label: sum(neg_txt.count(w.lower()) for w in words)
        for label, words in neg_keywords.items()
        if sum(neg_txt.count(w.lower()) for w in words) > 0
    }


def lang_distribution(data):
    lang_map = {
        "ja": "日文", "ko": "韓文", "en": "英文",
        "zh-Hant": "繁中", "zh-Hans": "簡中",
    }
    counts = Counter(d.get("originalLanguage", "") or "不明" for d in data)
    return {lang_map.get(k, k) or "不明": v for k, v in counts.most_common()}


def print_city_report(city_name, df, data):
    total_shops = len(df["店名"].unique())
    sep = "=" * 65
    print(f"\n{sep}")
    print(f"  {city_name} 韓式甜點市場分析報告")
    print(f"  共 {total_shops} 間店、{len(df)} 則評論")
    print(sep)

    print("\n【一】各店基本統計")
    print("-" * 65)
    for _, r in shop_stats(df).iterrows():
        stars = "★" * int(r["平均評分"])
        print(f"  {r['店名']:35s} {stars} {r['平均評分']:.1f}分")
        print(f"  {'':35s} 評論{r['評論數']}則 / 五星{r['五星比例']}")

    print("\n【二】評論語言分布")
    print("-" * 65)
    langs = lang_distribution(data)
    total = sum(langs.values())
    for lang, cnt in langs.items():
        pct = round(cnt / total * 100, 1)
        bar = "█" * int(pct / 3)
        print(f"  {lang:6s} {cnt:4d}則 ({pct:5.1f}%)  {bar}")

    print("\n【三】跨店品項分析（排除單店偏差）")
    print("-" * 65)
    print(f"  {'品項':16s} {'出現店數':>6} {'總次數':>6}  熱度（●有出現 ○未出現）")
    print(f"  {'-'*16} {'-'*6} {'-'*6}  {'-'*20}")
    cross = cross_shop_analysis(df, KEYWORDS)
    for label, shop_num, total, _ in cross:
        dots = "●" * shop_num + "○" * (total_shops - shop_num)
        print(f"  {label:16s} {shop_num:>4}間店  {total:>4}次  {dots}")

    print("\n【四】跨2間店以上品項明細")
    print("-" * 65)
    for label, shop_num, total, shop_counts in cross:
        if shop_num >= 2:
            detail = " / ".join([f"{s[:15]}({c}次)" for s, c in shop_counts.items()])
            print(f"  {label}: {detail}")

    print("\n【五】各店最高分代表評論")
    print("-" * 65)
    for shop in df["店名"].unique():
        s = df[df["店名"] == shop]
        top = s[pd.to_numeric(s["評分"], errors="coerce") == 5]
        if not top.empty:
            rev = str(top.iloc[0]["翻譯"]) or str(top.iloc[0]["評論"])
            if rev and rev != "nan":
                print(f"\n  【{shop}】")
                print(f"  「{rev[:160]}」")

    print("\n【六】負評痛點（1-3星）")
    print("-" * 65)
    neg = negative_analysis(df, NEGATIVE_KEYWORDS)
    if neg:
        for label, cnt in sorted(neg.items(), key=lambda x: -x[1]):
            print(f"  {label:8s} {cnt}次")
    else:
        print("  負評極少，整體口碑良好")

    return cross


# ══════════════════════════════════════════════════
# 主程式
# ══════════════════════════════════════════════════
city_results = {}

for city in CITIES:
    if not os.path.exists(city["file"]):
        print(f"\n⚠️  找不到檔案：{city['file']}，跳過 {city['name']}")
        continue
    df, data = load_data(city["file"])
    cross = print_city_report(city["name"], df, data)
    city_results[city["name"]] = {kw: (sn, total) for kw, sn, total, _ in cross}
    out = city["name"] + "_reviews_clean.csv"
    df.to_csv(out, index=False, encoding="utf-8-sig")
    print(f"\n  ✓ 已儲存：{out}")


# ══════════════════════════════════════════════════
# 三城市比較報告
# ══════════════════════════════════════════════════
if len(city_results) >= 2:
    cities = list(city_results.keys())
    print("\n\n" + "=" * 75)
    print("  跨城市比較報告")
    print("  判讀：出現店數越多 = 消費者自發需求越強，不受單店供給影響")
    print("=" * 75)

    header = f"  {'品項':16s}"
    for c in cities:
        header += f"  {c:>13s}"
    print(header)
    print("  " + "-" * (18 + 16 * len(cities)))

    for label in KEYWORDS.keys():
        if not any(label in city_results.get(c, {}) for c in cities):
            continue
        row = f"  {label:16s}"
        for c in cities:
            res = city_results.get(c, {})
            if label in res:
                sn, total = res[label]
                row += f"  {sn}間/{total:>3d}次    "
            else:
                row += f"  {'－':>11s}    "
        print(row)

    print("\n\n  ★ 跨城市強需求品項（在2個以上城市、各有2間以上店提及）")
    print("  " + "-" * 55)
    found_any = False
    for label in KEYWORDS.keys():
        strong = [c for c in cities if label in city_results.get(c, {}) and city_results[c][label][0] >= 2]
        if len(strong) >= 2:
            print(f"  ✓ {label:16s} → {' + '.join(strong)}")
            found_any = True
    if not found_any:
        print("  （目前各城市市場仍在各自發展，尚無跨城市強需求品項）")

print("\n\n分析完成！")
