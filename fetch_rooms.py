#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Accolade 房间级抓取（3D Estate 数据）
=====================================
数据源：assets.3destate.cloud 应用配置（公开可访问）
数据：每个具体房间的房间号、房型、面积、楼层、床型、3租期价格、起租日期、状态

用法：
  python3 fetch_rooms.py              # 抓取已配置的公寓房间数据
"""
import json
import re
import time
import urllib.request

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36"
RETRIES = 3

# 公寓 → 3destate app ID（通过 Playwright 从页面点击 Explore in 3D 捕获）
APPS = {
    "On Gibbons": "greystar-sydney-gibbons-29h0833h-co-sm",
    "On Regent": "greystar-sydney-regent-b94icvm3-co-sm",
}

# 租期显示名（3destate 用 76/77/95 作为租期 ID，与页面价格编码一致）
TERM_LABELS = ["全年", "学期", "短学期"]


def fetch(url, retries=RETRIES):
    last_err = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read().decode("utf-8", errors="ignore")
        except Exception as e:
            last_err = e
            time.sleep(2 * (attempt + 1))
    raise last_err


def fetch_rooms(app_id):
    """抓取 3destate 应用配置，提取所有房间"""
    url = f"https://assets.3destate.cloud/assets/apps/{app_id}/r/latest/config.json"
    data = json.loads(fetch(url))
    config = data.get("data", {}).get("config", {})
    units = config.get("units", [])

    rooms = []
    for u in units:
        custom = u.get("custom", {})
        name = u.get("name", "")
        unit_type = custom.get("unitType", "")
        floorplan = custom.get("floorplanName", "") or unit_type
        area = custom.get("areaSqm") or custom.get("area", 0)
        floor = custom.get("floor", 0)
        status = custom.get("status", 0)

        # 租期价格
        terms_map = custom.get("leaseTermsDataMap", {})
        terms = {}
        for i, key in enumerate(sorted(terms_map.keys())[:3]):
            if i < 3:
                terms[TERM_LABELS[i]] = terms_map[key].get("rent", 0)

        # 起租日期
        avail_ts = custom.get("availableDateNumber") or custom.get("tempMoveInDate")
        avail_date = ""
        if avail_ts:
            try:
                import datetime
                avail_date = datetime.datetime.utcfromtimestamp(avail_ts / 1000).strftime("%Y-%m-%d")
            except Exception:
                pass

        # 床型/特征
        features = custom.get("features", [])
        bed = next((f for f in features if "bed" in f.lower() or "king" in f.lower() or "double" in f.lower() or "single" in f.lower()), "")
        shared = custom.get("isShared", False)

        rooms.append({
            "room": name,
            "floorplan": floorplan,
            "area": area,
            "floor": floor,
            "bed": bed,
            "shared": shared,
            "terms": terms,
            "available_date": avail_date,
            "status": "available" if status == 1 else "unavailable",
            "has_price": any(v > 0 for v in terms.values()),
        })

    # 按房型分组统计
    return rooms


def main():
    result = {}
    total = 0
    for prop_name, app_id in APPS.items():
        print(f"抓取 {prop_name} ({app_id})...")
        try:
            rooms = fetch_rooms(app_id)
            result[prop_name] = rooms
            total += len(rooms)
            # 统计
            avail = sum(1 for r in rooms if r["has_price"])
            print(f"  ✅ {len(rooms)} 个房间（{avail} 个可订）")
            # 按房型统计
            by_type = {}
            for r in rooms:
                by_type.setdefault(r["floorplan"], []).append(r)
            for ft, rs in by_type.items():
                print(f"    {ft}: {len(rs)} 间")
        except Exception as e:
            print(f"  ❌ {e}")

    import datetime
    sydney = datetime.datetime.utcnow() + datetime.timedelta(hours=10)
    with open("accolade_rooms.json", "w", encoding="utf-8") as f:
        json.dump({"fetched_at": sydney.strftime("%Y-%m-%d %H:%M:%S"), "properties": result},
                  f, ensure_ascii=False, indent=2)
    print(f"\n✅ 完成！共 {total} 个房间，已保存 accolade_rooms.json")


if __name__ == "__main__":
    main()
