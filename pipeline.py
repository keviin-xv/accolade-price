#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Accolade 房态流水线（双数据源 + 回退）
=======================================
主数据源：3destate 房间级（公开静态 JSON）
备用数据源：官网房型级（SSG 页面）
复检：数量骤减/失败 → 回退上次成功数据

用法：
  python3 pipeline.py            # 完整流水线（抓取+复检+渲染）
  python3 pipeline.py --rooms    # 只抓房间级
  python3 pipeline.py --render   # 只渲染
"""
import argparse
import json
import re
import sys
import time
import urllib.request

# ═══════════════════ 配置 ═══════════════════

# 公寓 → 3destate app ID（房间级）
APPS = {
    "On Gibbons": "greystar-sydney-gibbons-29h0833h-co-sm",
    "On Regent": "greystar-sydney-regent-b94icvm3-co-sm",
}

# 公寓 → 官网页面（房型级备用）
PROP_URLS = {
    "On Gibbons": "https://www.accolade-student.com/en/locations/sydney/on-gibbons",
    "On Regent": "https://www.accolade-student.com/en/locations/sydney/on-regent",
}

TERM_LABELS = ["全年", "学期", "短学期"]

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36"
RETRIES = 3


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


def load_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ═══════════════════ 房间级抓取（3destate） ═══════════════════


def fetch_rooms(app_id):
    """抓取 3destate 房间级数据"""
    url = f"https://assets.3destate.cloud/assets/apps/{app_id}/r/latest/config.json"
    data = json.loads(fetch(url))
    config = data.get("data", {}).get("config", {})
    units = config.get("units", [])
    rooms = []
    for u in units:
        custom = u.get("custom", {})
        terms_map = custom.get("leaseTermsDataMap", {})
        terms = {}
        for i, key in enumerate(sorted(terms_map.keys())[:3]):
            if i < 3:
                terms[TERM_LABELS[i]] = terms_map[key].get("rent", 0)
        avail_ts = custom.get("availableDateNumber") or custom.get("tempMoveInDate")
        avail_date = ""
        if avail_ts:
            try:
                import datetime
                avail_date = datetime.datetime.utcfromtimestamp(avail_ts / 1000).strftime("%Y-%m-%d")
            except Exception:
                pass
        rooms.append({
            "room": u.get("name", ""),
            "floorplan": custom.get("floorplanName", "") or custom.get("unitType", ""),
            "floor": custom.get("floor", 0),
            "terms": terms,
            "available_date": avail_date,
            "has_price": any(v > 0 for v in terms.values()),
        })
    return rooms


# ═══════════════════ 房型级抓取（官网，备用） ═══════════════════


def fetch_floorplans(url):
    """抓取官网房型级数据（备用）"""
    page = fetch(url)
    m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', page, re.S)
    if not m:
        return []
    data = json.loads(m.group(1))
    cp = data.get("props", {}).get("pageProps", {}).get("componentProps", {})
    plans = []
    for comp in cp.values():
        cards = comp.get("integratedCardsResult", {}).get("item", {}).get("children", {}).get("results", [])
        if not cards:
            continue
        for card in cards:
            for f in card.get("children", {}).get("results", []):
                rname = f.get("name", "")
                if not rname or rname == "Floor Plan":
                    continue
                prices = {}
                price_str = (f.get("price") or {}).get("value", "")
                for i, pair in enumerate(price_str.split("&")[:3]):
                    if "=" in pair:
                        k, v = pair.split("=")
                        try:
                            prices[TERM_LABELS[i]] = int(v)
                        except ValueError:
                            prices[TERM_LABELS[i]] = 0
                plans.append({
                    "floorplan": rname,
                    "terms": prices,
                    "available_date": (f.get("earliestUnitAvailableDate") or {}).get("value", ""),
                    "has_price": any(v > 0 for v in prices.values()),
                })
        break
    return plans


# ═══════════════════ 复检 ═══════════════════


def validate(data, old_data, source):
    new_n = sum(len(v) for v in data.values())
    old_n = sum(len(v) for v in old_data.values()) if old_data else 0
    if old_n > 0 and new_n < old_n * 0.7:
        print(f"⚠️ [{source}] 数量骤减 {old_n} → {new_n}，回退上次数据")
        return False, old_data
    print(f"✅ [{source}] 复检通过: {new_n} 条")
    return True, data


# ═══════════════════ 主流程 ═══════════════════


def run_rooms():
    print("── 房间级抓取（3destate）──")
    result = {}
    for pname, app_id in APPS.items():
        print(f"  {pname}...")
        try:
            rooms = fetch_rooms(app_id)
            result[pname] = rooms
            avail = sum(1 for r in rooms if r["has_price"])
            print(f"    ✅ {len(rooms)} 间（{avail} 可订）")
        except Exception as e:
            print(f"    ❌ {e}")
            return False

    old = load_json("accolade_rooms.json", {}).get("properties", {})
    ok, final = validate(result, old, "房间级")
    if ok:
        save_json("accolade_rooms.json",
                  {"fetched_at": time.strftime("%Y-%m-%d %H:%M:%S"), "properties": result})
    return ok


def run_floorplans():
    print("── 房型级抓取（官网，备用）──")
    result = {}
    for pname, url in PROP_URLS.items():
        print(f"  {pname}...")
        try:
            plans = fetch_floorplans(url)
            result[pname] = plans
            avail = sum(1 for p in plans if p["has_price"])
            print(f"    ✅ {len(plans)} 户型（{avail} 可订）")
        except Exception as e:
            print(f"    ❌ {e}")
            return False

    old = load_json("accolade_plans.json", {}).get("properties", {})
    ok, final = validate(result, old, "房型级")
    if ok:
        save_json("accolade_plans.json",
                  {"fetched_at": time.strftime("%Y-%m-%d %H:%M:%S"), "properties": result})
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rooms", action="store_true")
    ap.add_argument("--render", action="store_true")
    args = ap.parse_args()

    if args.render:
        import render_rooms
        render_rooms.main()
        print("🎉 渲染完成")
        return

    if args.rooms:
        run_rooms()
        import render_rooms
        render_rooms.main()
        print("🎉 房间级更新完成")
        return

    # 完整流程：双数据源
    rooms_ok = run_rooms()
    plans_ok = run_floorplans()
    if rooms_ok:
        import render_rooms
        render_rooms.main()
    print("🎉 流水线完成")


if __name__ == "__main__":
    main()
