#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Accolade 房间级查房页面渲染（城市→公寓→房型→具体房间表格）"""
import json

CSS = """
:root {
  --bg: #fafaf9; --card-bg: #fff;
  --text: #1a1a1a; --text-muted: #6b7280; --border: #e5e4e1;
  --green: #059669; --green-bg: #ecfdf5;
  --amber: #d97706; --amber-bg: #fffbeb;
  --red: #dc2626; --red-bg: #fef2f2;
  --radius: 8px;
  --font: 'Satoshi', system-ui, -apple-system, sans-serif;
}
@media (prefers-color-scheme: dark) {
  :root { --bg: #0c0c0c; --card-bg: #161616; --text: #e5e5e5; --text-muted: #8b8b8b; --border: #262626; }
}
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html { font-family: var(--font); -webkit-font-smoothing: antialiased; background: var(--bg); color: var(--text); }
body { max-width: 1180px; margin: 0 auto; padding: 32px 20px 60px; line-height: 1.5; }
.header { margin-bottom: 24px; }
.header-top { display: flex; align-items: baseline; justify-content: space-between; flex-wrap: wrap; gap: 12px; margin-bottom: 4px; }
.header h1 { font-size: clamp(1.3rem, 3vw, 1.6rem); font-weight: 700; letter-spacing: -0.025em; }
.header .meta { color: var(--text-muted); font-size: 0.8rem; }
.city-nav { display: flex; gap: 6px; margin-bottom: 12px; }
.city-btn { padding: 8px 18px; border-radius: 8px; cursor: pointer; font-size: 0.85rem; font-weight: 700; color: var(--text); border: 1px solid var(--border); background: var(--card-bg); font-family: var(--font); transition: all 200ms cubic-bezier(0.32,0.72,0,1); }
.city-btn:hover { border-color: var(--text-muted); }
.city-btn.active { background: var(--text); color: var(--bg); border-color: var(--text); }
.city-btn .count { font-size: 0.68rem; opacity: 0.5; margin-left: 3px; font-weight: 400; }
.prop-nav { display: flex; gap: 6px; margin-bottom: 20px; overflow-x: auto; -webkit-overflow-scrolling: touch; scrollbar-width: none; }
.prop-nav::-webkit-scrollbar { display: none; }
.prop-btn { flex-shrink: 0; padding: 6px 14px; border-radius: 7px; cursor: pointer; font-size: 0.82rem; font-weight: 600; color: var(--text-muted); border: 1px solid var(--border); background: var(--card-bg); font-family: var(--font); transition: all 200ms cubic-bezier(0.32,0.72,0,1); white-space: nowrap; }
.prop-btn:hover { color: var(--text); border-color: var(--text-muted); }
.prop-btn.active { background: var(--text); color: var(--bg); border-color: var(--text); }
.prop-btn .count { font-size: 0.66rem; opacity: 0.5; margin-left: 3px; font-weight: 400; }
.group-title { display: flex; align-items: center; gap: 8px; margin: 16px 0 8px; font-size: 0.9rem; font-weight: 700; }
.group-title::after { content: ''; flex: 1; height: 1px; background: var(--border); }
.group-title .gcount { font-size: 0.7rem; color: var(--text-muted); font-weight: 500; }
.table-wrap { background: var(--card-bg); border: 1px solid var(--border); border-radius: var(--radius); overflow: hidden; }
.table-wrap table { width: 100%; border-collapse: collapse; font-size: 0.82rem; }
.table-wrap th { text-align: left; padding: 12px 12px; font-weight: 600; font-size: 0.68rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-muted); background: var(--bg); border-bottom: 1px solid var(--border); white-space: nowrap; }
.table-wrap td { padding: 13px 12px; border-bottom: 1px solid var(--border); font-variant-numeric: tabular-nums; white-space: nowrap; }
.table-wrap tr:last-child td { border-bottom: none; }
.table-wrap tbody tr { transition: background 200ms cubic-bezier(0.32,0.72,0,1); }
.table-wrap tbody tr:hover { background: var(--bg); }
.row-ok { box-shadow: inset 3px 0 0 var(--green); }
.row-bad { box-shadow: inset 3px 0 0 var(--red); }
.tag { display: inline-flex; align-items: center; gap: 5px; padding: 3px 10px; border-radius: 99px; font-size: 0.75rem; font-weight: 650; }
.tag::before { content: ''; width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }
.tag-ok { background: var(--green-bg); color: var(--green); }
.tag-ok::before { background: var(--green); }
.tag-bad { background: var(--red-bg); color: var(--red); }
.tag-bad::before { background: var(--red); }
.price { font-weight: 600; }
.room-no { font-weight: 700; font-size: 0.9rem; }
.group-tabs { display: flex; gap: 6px; margin-bottom: 14px; }
.group-tab { padding: 9px 22px; border-radius: 8px; cursor: pointer; font-size: 0.85rem; font-weight: 700; color: var(--text-muted); border: 1px solid var(--border); background: var(--card-bg); font-family: var(--font); transition: all 200ms cubic-bezier(0.32,0.72,0,1); }
.group-tab:hover { color: var(--text); border-color: var(--text-muted); }
.group-tab.active { background: var(--text); color: var(--bg); border-color: var(--text); }
.group-tab .count { font-size: 0.68rem; opacity: 0.5; margin-left: 3px; font-weight: 400; }
.group-panel { display: none; }
.group-panel.active { display: block; }
.type-tabs { display: flex; gap: 4px; margin-bottom: 16px; background: var(--card-bg); border: 1px solid var(--border); border-radius: var(--radius); padding: 4px; width: fit-content; max-width: 100%; overflow-x: auto; scrollbar-width: none; }
.type-tabs::-webkit-scrollbar { display: none; }
.type-tab { padding: 6px 14px; border-radius: 7px; cursor: pointer; font-size: 0.8rem; font-weight: 600; color: var(--text-muted); border: none; background: none; font-family: var(--font); transition: all 200ms cubic-bezier(0.32,0.72,0,1); white-space: nowrap; }
.type-tab:hover { color: var(--text); }
.type-tab.active { background: var(--text); color: var(--bg); box-shadow: 0 1px 3px rgba(0,0,0,0.06); }
.type-tab .count { font-size: 0.66rem; opacity: 0.5; margin-left: 3px; font-weight: 400; }
.type-panel { display: none; }
.type-panel.active { display: block; }
.city-group { display: none; }
.city-group.active { display: block; }
.prop-panel { display: none; }
.prop-panel.active { display: block; }
.footer { margin-top: 40px; padding-top: 24px; border-top: 1px solid var(--border); }
.footer-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px,1fr)); gap: 14px; margin-bottom: 24px; }
.footer-card { background: var(--card-bg); border: 1px solid var(--border); border-radius: var(--radius); padding: 16px 18px; }
.footer-card h3 { font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.07em; color: var(--text-muted); margin-bottom: 8px; font-weight: 600; }
.footer-card p, .footer-card li { font-size: 0.82rem; line-height: 1.7; }
.footer-card ul { list-style: none; padding: 0; }
.footer-card li::before { content: "— "; color: var(--text-muted); }
.footer-sign { text-align: center; }
.footer-sign p { color: var(--text-muted); font-size: 0.75rem; }
.fade-in { opacity: 0; transform: translateY(8px); animation: fadeIn 550ms cubic-bezier(0.32,0.72,0,1) forwards; }
@keyframes fadeIn { to { opacity: 1; transform: translateY(0); } }
@media (max-width:768px) {
  body { padding: 20px 12px 50px; }
  .table-wrap { overflow-x: auto; }
  .table-wrap table { min-width: 800px; }
  .header-top { flex-direction: column; align-items: flex-start; }
}
"""

TERM_LABELS = ["全年", "学期", "短学期"]


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;"))


def term_cell(label, room):
    price = (room.get("terms") or {}).get(label)
    if not price:
        return "<td>—</td>"
    return f'<td><span class="price">${price:,}</span></td>'


# 公寓 → 官网页面（房间链接目标）
PROP_PAGES = {
    "On Gibbons": "https://www.accolade-student.com/en/locations/sydney/on-gibbons",
    "On Regent": "https://www.accolade-student.com/en/locations/sydney/on-regent",
    "On A'Beckett": "https://www.accolade-student.com/en/locations/melbourne/on-abeckett",
    "On Gray": "https://www.accolade-student.com/en/locations/adelaide/on-gray",
    "On Waymouth": "https://www.accolade-student.com/en/locations/adelaide/on-waymouth",
    "On Moore": "https://www.accolade-student.com/en/locations/canberra/on-moore",
}


def render_room_table(rooms, prop_name=""):
    rows = ""
    prop_url = PROP_PAGES.get(prop_name, "")
    for r in rooms:
        ok = r.get("has_price")
        cls = "ok" if ok else "bad"
        label = "可订" if ok else "售罄"
        floor = esc(f"{r.get('floor')}层") if r.get("floor") else "—"
        terms = "".join(term_cell(t, r) for t in TERM_LABELS)
        # 房间号超链接（带 ↗ 提示，新窗口打开）
        room_html = (f'<a href="{prop_url}" target="_blank" '
                     f'style="color:inherit;text-decoration:none;" class="room-link">'
                     f'<span class="room-no">{esc(r["room"])}</span> '
                     f'<span style="font-size:0.7rem;opacity:0.45;">↗</span></a>'
                     if prop_url else f'<span class="room-no">{esc(r["room"])}</span>')
        rows += (
            f'<tr class="row-{cls}">'
            f'<td>{room_html}</td>'
            f'<td>{floor}</td>'
            f'{terms}'
            f'<td><span class="tag tag-{cls}">{label}</span></td>'
            f'<td>{esc(r.get("available_date") or "—")}</td>'
            f"</tr>"
        )
    if not rows:
        return ""
    head = ("<thead><tr><th>房间号</th><th>楼层</th>"
            + "".join(f"<th>{t}</th>" for t in TERM_LABELS)
            + "<th>状态</th><th>起租日期</th></tr></thead>")
    return f'<div class="table-wrap"><table>{head}<tbody>{rows}</tbody></table></div>'


def classify_type(name):
    """房型分类：Studio（不含 Twin）→ studio 组；Twin/Ensuite/Share → 合租组"""
    n = name.lower()
    if "studio" in n and "twin" not in n:
        return "studio"
    return "share"


def render_type_tabs(pi, group, types, offset):
    """生成一组户型 Tab + 面板（offset 保证全局唯一索引）"""
    tabs = ""
    panels = ""
    for j, ft in enumerate(types):
        ti = offset + j
        rs = group[ft]
        avail = sum(1 for r in rs if r["has_price"])
        tact = " active" if ti == offset else ""
        tabs += (f'<button class="type-tab{tact}" id="type-btn-{pi}-{ti}" onclick="switchType({pi},{ti})">'
                 f'{esc(ft)}<span class="count">{avail}/{len(rs)}</span></button>')
        panels += (f'<div class="type-panel{tact}" id="type-panel-{pi}-{ti}">'
                   f'{render_room_table(rs)}</div>')
    if not tabs:
        return ""
    return f'<div class="type-tabs">{tabs}</div>{panels}'


def render_property(ci, pi, prop_name, rooms):
    """公寓内：分组 Tab（Studio/合租）→ 组内户型 Tab → 房间表格"""
    by_type = {}
    for r in rooms:
        by_type.setdefault(r["floorplan"], []).append(r)

    # 分组
    groups = []
    studios = {k: v for k, v in by_type.items() if classify_type(k) == "studio"}
    shares = {k: v for k, v in by_type.items() if classify_type(k) == "share"}
    if studios:
        groups.append(("studio", "🏠 Studio", studios))
    if shares:
        groups.append(("share", "👥 合租", shares))

    if not groups:
        return '<div style="padding:24px;color:var(--text-muted);">暂无房间数据</div>'

    group_tabs = ""
    group_panels = ""
    for gi, (gkey, glabel, gtypes) in enumerate(groups):
        gact = " active" if gi == 0 else ""
        total = sum(len(v) for v in gtypes.values())
        group_tabs += (f'<button class="group-tab{gact}" id="group-btn-{ci}-{pi}-{gi}" '
                       f'onclick="switchGroup({ci},{pi},{gi})">{glabel}<span class="count">{total}间</span></button>')

        # 组内户型 Tab
        type_tabs = ""
        type_panels = ""
        for ti, ft in enumerate(sorted(gtypes.keys())):
            rs = gtypes[ft]
            avail = sum(1 for r in rs if r["has_price"])
            tact = " active" if ti == 0 else ""
            type_tabs += (f'<button class="type-tab{tact}" id="type-btn-{ci}-{pi}-{gi}-{ti}" '
                          f'onclick="switchType({ci},{pi},{gi},{ti})">{esc(ft)}'
                          f'<span class="count">{avail}/{len(rs)}</span></button>')
            type_panels += (f'<div class="type-panel{tact}" id="type-panel-{ci}-{pi}-{gi}-{ti}">'
                            f'{render_room_table(rs, prop_name)}</div>')

        group_panels += (f'<div class="group-panel{gact}" id="group-panel-{ci}-{pi}-{gi}">'
                         f'<div class="type-tabs">{type_tabs}</div>{type_panels}</div>')

    return f'<div class="group-tabs">{group_tabs}</div>{group_panels}'


CITY_MAP = {
    "On Gibbons": "悉尼 Sydney", "On Regent": "悉尼 Sydney",
    "On A'Beckett": "墨尔本 Melbourne",
    "On Gray": "阿德莱德 Adelaide", "On Waymouth": "阿德莱德 Adelaide",
    "On Moore": "堪培拉 Canberra",
}


def main():
    # 优先用 Sitecore 全城市数据，回退 3destate 数据
    try:
        with open("accolade_sitecore.json", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        with open("accolade_rooms.json", encoding="utf-8") as f:
            data = json.load(f)
    fetched = data.get("fetched_at", "")
    properties = data.get("properties", {})

    # 按城市分组
    cities = {}
    for pname in properties.keys():
        city = CITY_MAP.get(pname, "悉尼 Sydney")
        cities.setdefault(city, []).append(pname)

    city_nav = ""
    city_groups = ""
    for ci, (city, prop_list) in enumerate(cities.items()):
        active = " active" if ci == 0 else ""
        city_nav += (f'<button class="city-btn{active}" id="btn-city-{ci}" onclick="switchCity({ci})">'
                     f'{esc(city)}<span class="count">{len(prop_list)}</span></button>')

        prop_nav = panels = ""
        for pi, pname in enumerate(prop_list):
            rooms = properties.get(pname, [])
            pact = " active" if pi == 0 else ""
            total = len(rooms)
            avail = sum(1 for r in rooms if r.get("has_price"))
            prop_nav += (f'<button class="prop-btn{pact}" id="btn-p{ci}-{pi}" onclick="switchProp({ci},{pi})">'
                         f'{esc(pname)}<span class="count">{avail}/{total}</span></button>')
            panels += (f'<div class="prop-panel{pact}" id="panel-p{ci}-{pi}">'
                       f'{render_property(ci, pi, pname, rooms)}</div>')
        city_groups += (f'<div class="city-group{active}" id="group-city-{ci}">'
                        f'<nav class="prop-nav fade-in">{prop_nav}</nav>{panels}</div>')

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Accolade 房态查房 — 异乡好居</title>
<link href="https://api.fontshare.com/v2/css?f[]=satoshi@400,500,600,700&display=swap" rel="stylesheet">
<style>{CSS}</style>
</head>
<body>
<div class="header fade-in">
  <div class="header-top"><h1>Accolade 房态查房</h1></div>
  <p class="meta">📍 悉尼 · 墨尔本 · 阿德莱德 · 堪培拉 &ensp;|&ensp; 更新于 {fetched} &ensp;|&ensp; 优惠信息请查看「供应商信息同步群」</p>
  <p class="meta" style="margin-top:4px;">⚠️ 此页面仅供一键查房参考，实际信息以官网显示为准</p>
</div>
<nav class="city-nav fade-in">{city_nav}</nav>
{city_groups}
<div class="footer fade-in">
  <div class="footer-grid">
    <div class="footer-card">
      <h3>租金包含</h3>
      <p>水电网全包、健身房、自习室、公共空间、24/7 支持团队</p>
    </div>
    <div class="footer-card">
      <h3>注意事项</h3>
      <ul>
        <li>房间号来自官网房态系统</li>
        <li>价格按周计算（AUD）</li>
        <li>可订状态实时变化，以官网为准</li>
      </ul>
    </div>
    <div class="footer-card">
      <h3>数据来源</h3>
      <ul>
        <li>accolade-student.com 房态系统</li>
        <li>GitHub Actions 自动抓取</li>
      </ul>
    </div>
  </div>
  <div class="footer-sign"><p>异乡好居 · 徐照国 · 仅供内部参考</p></div>
</div>
<script>
function switchCity(ci){{
  document.querySelectorAll('.city-btn').forEach((b,i)=>b.classList.toggle('active',i===ci));
  document.querySelectorAll('.city-group').forEach((g,i)=>g.classList.toggle('active',i===ci));
}}
function switchProp(ci,pi){{
  var g=document.getElementById('group-city-'+ci);
  g.querySelectorAll('.prop-btn').forEach((b,i)=>b.classList.toggle('active',i===pi));
  g.querySelectorAll('.prop-panel').forEach((p,i)=>p.classList.toggle('active',i===pi));
}}
function switchGroup(ci,pi,gi){{
  var panel=document.getElementById('panel-p'+ci+'-'+pi);
  panel.querySelectorAll('.group-tab').forEach((b,i)=>b.classList.toggle('active',i===gi));
  panel.querySelectorAll('.group-panel').forEach((p,i)=>p.classList.toggle('active',i===gi));
}}
function switchType(ci,pi,gi,ti){{
  var gp=document.getElementById('group-panel-'+ci+'-'+pi+'-'+gi);
  gp.querySelectorAll('.type-tab').forEach((b,i)=>b.classList.toggle('active',i===ti));
  gp.querySelectorAll('.type-panel').forEach((p,i)=>p.classList.toggle('active',i===ti));
}}
</script>
</body>
</html>"""

    with open("rooms.html", "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ 已生成 rooms.html（更新于 {fetched}）")