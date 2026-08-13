#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Accolade 房间级抓取（Sitecore GraphQL 统一方式）
=================================================
适用于所有城市（墨尔本/阿德莱德/堪培拉/悉尼备用）
数据源：edge-platform.sitecorecloud.io GraphQL（公开，sitecoreContextId 参数认证）

用法：
  python3 fetch_sitecore.py              # 抓取全部 6 个公寓的房间数据
"""
import json
import re
import sys
import time
import urllib.request

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36"
GQL = "https://edge-platform.sitecorecloud.io/v1/content/api/graphql/v1?sitecoreContextId=2MW3HMz250p2fBoiJ0iNVl"

# 全部 6 个公寓
PROPERTIES = {
    "On Gibbons": "https://www.accolade-student.com/en/locations/sydney/on-gibbons",
    "On Regent": "https://www.accolade-student.com/en/locations/sydney/on-regent",
    "On A'Beckett": "https://www.accolade-student.com/en/locations/melbourne/on-abeckett",
    "On Gray": "https://www.accolade-student.com/en/locations/adelaide/on-gray",
    "On Waymouth": "https://www.accolade-student.com/en/locations/adelaide/on-waymouth",
    "On Moore": "https://www.accolade-student.com/en/locations/canberra/on-moore",
}

# 租期键 → 显示名（各公寓键不同，按价格从低到高映射为 全年/学期/短学期）
TERM_LABELS = ["全年", "学期", "短学期"]

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


def gql(query, variables=None):
    body = json.dumps({"query": query, "variables": variables or {}}).encode()
    req = urllib.request.Request(GQL, data=body, method="POST",
                                 headers={"User-Agent": UA, "Content-Type": "application/json"})
    resp = json.loads(urllib.request.urlopen(req, timeout=30).read().decode())
    if resp.get("errors"):
        raise Exception(resp["errors"][0]["message"])
    return resp.get("data", {}).get("data", {})


def get_floorplans(page_url):
    """从公寓页面提取户型 GUID（通用搜索）"""
    html = fetch(page_url)
    m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.S)
    if not m:
        return []
    data = json.loads(m.group(1))
    s = json.dumps(data)

    # 优先用 integratedCardsResult（带户型名）
    cp = data.get("props", {}).get("pageProps", {}).get("componentProps", {})
    plans = []
    for comp in cp.values():
        cards = comp.get("integratedCardsResult", {}).get("item", {}).get("children", {}).get("results", [])
        for card in cards:
            for f in card.get("children", {}).get("results", []):
                name, fid = f.get("name", ""), f.get("FloorPlanSitecoreID", "")
                if name and name != "Floor Plan" and fid:
                    g = f"{fid[:8]}-{fid[8:12]}-{fid[12:16]}-{fid[16:20]}-{fid[20:]}"
                    plans.append({"name": name, "id": g})
        if plans:
            break
    if plans:
        return plans

    # 通用搜索：全 JSON 找 FloorPlanSitecoreID（名字取附近 displayName/name）
    seen = set()
    for mm in re.finditer(r'"FloorPlanSitecoreID":\s*"([A-F0-9]{32})"', s):
        fid = mm.group(1)
        if fid in seen:
            continue
        seen.add(fid)
        ctx = s[max(0, mm.start()-800):mm.start()]
        # 优先 displayName，其次 name
        dm = re.findall(r'"displayName":\s*"([^"]+)"', ctx)
        nm = re.findall(r'"name":\s*"([^"]+)"', ctx)
        name = dm[-1] if dm else (nm[-1] if nm else "?")
        if name and name != "Floor Plan":
            g = f"{fid[:8]}-{fid[8:12]}-{fid[12:16]}-{fid[16:20]}-{fid[20:]}"
            plans.append({"name": name, "id": g})
    return plans


def query_units(plan_guid):
    """按户型查询房间（含 UnitSpace 价格/起租）"""
    query = """query T($language: String = "en") {
      data: search(
        where: {AND: [{name: "_templates", value: "{6B9AD54E-38FB-4F1C-88F3-99B04EF4FEA5}"}, {name: "_path", value: "%s", operator: CONTAINS}, {name: "_language", value: $language}]}
        first: 200
      ) {
        total
        results {
          ... on Unit {
            unitNumber { value }
            floorNumber { value }
            children(first: 20) { results { ... on UnitSpace { unitNumber { value } price { value } availableDate { value } } } }
          }
        }
      }
    }""" % plan_guid
    resp = gql(query, {"language": "en"})
    return resp.get("results", [])


def parse_price(price_str):
    """价格编码 74=539&75=569&96=599 → 按价格排序映射 全年/学期/短学期"""
    pairs = []
    if not price_str:
        return {}
    for pair in price_str.split("&"):
        if "=" in pair:
            k, v = pair.split("=")
            try:
                pairs.append((int(v), v))
            except ValueError:
                pairs.append((0, v))
    pairs.sort()  # 价格从低到高
    terms = {}
    for i, (price, _) in enumerate(pairs[:3]):
        terms[TERM_LABELS[i]] = price
    return terms


def parse_date(s):
    """6/6/2025 12:00:00 AM → 2025-06-06"""
    if not s:
        return ""
    m = re.match(r"(\d{1,2})/(\d{1,2})/(\d{4})", s)
    if m:
        return f"{m.group(3)}-{int(m.group(1)):02d}-{int(m.group(2)):02d}"
    return ""


def fetch_property(pname, page_url):
    """抓取一个公寓的全部房间"""
    plans = get_floorplans(page_url)
    all_rooms = []
    for plan in plans:
        try:
            units = query_units(plan["id"])
        except Exception as e:
            print(f"    ⚠️ {plan['name']}: {e}")
            continue
        for u in units:
            un = u.get("unitNumber", {}).get("value", "")
            fl = u.get("floorNumber", {}).get("value", "")
            # 取第一个有价格的 UnitSpace
            space = None
            for c in u.get("children", {}).get("results", []):
                if c.get("price", {}).get("value"):
                    space = c
                    break
            if not space and u.get("children", {}).get("results"):
                space = u["children"]["results"][0]
            if not space:
                continue
            price_str = space.get("price", {}).get("value", "")
            terms = parse_price(price_str)
            all_rooms.append({
                "room": un,
                "floorplan": plan["name"],
                "floor": fl,
                "terms": terms,
                "available_date": parse_date(space.get("availableDate", {}).get("value", "")),
                "has_price": any(v > 0 for v in terms.values()),
            })
        time.sleep(0.4)

    # 楼层从高到低排序（同一楼层按房间号）
    all_rooms.sort(key=lambda r: (int(r["floor"] or 0), r["room"]), reverse=True)
    return all_rooms


def main():
    result = {}
    total = 0
    for pname, purl in PROPERTIES.items():
        print(f"抓取 {pname}...")
        try:
            rooms = fetch_property(pname, purl)
            result[pname] = rooms
            avail = sum(1 for r in rooms if r["has_price"])
            print(f"  ✅ {len(rooms)} 个房间（{avail} 可订）")
            total += len(rooms)
        except Exception as e:
            print(f"  ❌ {e}")
    with open("accolade_sitecore.json", "w", encoding="utf-8") as f:
        json.dump({"fetched_at": time.strftime("%Y-%m-%d %H:%M:%S"), "properties": result},
                  f, ensure_ascii=False, indent=2)
    print(f"\n✅ 完成！共 {total} 个房间")


if __name__ == "__main__":
    main()
