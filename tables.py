"""League tables + top scorers/assists (ESPN public data) -> tables.html, and the team list for "My Teams"."""
import html
import json
import re
import unicodedata

from layout import page

TABLE_LEAGUES = [  # key used for filters, ESPN code, name, flagcdn code
    ("eng", "eng.1", "Premier League", "gb-eng"), ("esp", "esp.1", "LaLiga", "es"), ("ita", "ita.1", "Serie A", "it"),
    ("ger", "ger.1", "Bundesliga", "de"), ("fra", "fra.1", "Ligue 1", "fr"), ("eur", "uefa.champions", "Champions League", "eu"),
    ("ksa", "ksa.1", "Saudi Pro League", "sa"),
]
# extra names fans and video titles use for clubs (lowercase, no accents)
ALIASES = {
    "manchester united": ["man utd", "man united", "manchester utd"], "manchester city": ["man city"],
    "tottenham hotspur": ["spurs", "tottenham"], "wolverhampton wanderers": ["wolves"], "brighton & hove albion": ["brighton"],
    "nottingham forest": ["forest"], "west ham united": ["west ham"], "newcastle united": ["newcastle"],
    "paris saint-germain": ["psg", "paris sg"], "internazionale": ["inter", "inter milan"], "ac milan": ["milan"],
    "bayern munich": ["bayern", "fc bayern"], "borussia dortmund": ["dortmund", "bvb"], "bayer leverkusen": ["leverkusen"],
    "atletico madrid": ["atletico", "atleti"], "barcelona": ["barca", "fc barcelona"], "juventus": ["juve"],
    "rb leipzig": ["leipzig"], "olympique de marseille": ["marseille"], "marseille": ["om marseille"],
    "olympique lyonnais": ["lyon"], "al nassr": ["al-nassr", "nassr"], "al hilal": ["al-hilal", "hilal"],
    "al ittihad": ["al-ittihad", "ittihad"], "al ahli": ["al-ahli"],
}
STOP_FIRST = {"real", "club", "sporting", "athletic", "olympique", "borussia", "manchester", "deportivo", "union",
              "racing", "stade", "inter", "west", "nottingham", "sheffield", "queens", "crystal", "aston", "werder"}


def plain(s):
    return "".join(ch for ch in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(ch) != "Mn")


def keys_for(name, short):
    keys = {plain(name), plain(short)}
    keys |= set(ALIASES.get(plain(name), []))
    first = plain(name).split(" ")[0]
    if len(first) >= 5 and first not in STOP_FIRST:
        keys.add(first)
    return sorted(k for k in keys if len(k) >= 3)


def _num(stats, name):
    for s in stats:
        if s.get("name") == name:
            return s.get("displayValue", "")
    return ""


def fetch(get):
    """get(url) -> bytes. Returns {"leagues": [...], "teams": [...]}"""
    out, teams = [], []
    for key, code, name, fl in TABLE_LEAGUES:
        lg = {"key": key, "code": code, "name": name, "flag": fl, "rows": [], "scorers": [], "assists": [], "season": ""}
        try:
            s = json.loads(get(f"https://site.api.espn.com/apis/v2/sports/soccer/{code}/standings"))
            lg["season"] = (s.get("season") or {}).get("displayName", "")
            groups = s.get("children") or [s]
            for gi, grp in enumerate(groups):
                for en in (grp.get("standings") or {}).get("entries", []):
                    t, st = en["team"], en.get("stats", [])
                    note = en.get("note") or {}
                    lg["rows"].append({"group": grp.get("name", "") if len(groups) > 1 else "", "rank": _num(st, "rank"),
                                       "team": t.get("displayName", ""), "short": t.get("shortDisplayName", ""),
                                       "p": _num(st, "gamesPlayed"), "w": _num(st, "wins"), "d": _num(st, "ties"),
                                       "l": _num(st, "losses"), "gd": _num(st, "pointDifferential"), "pts": _num(st, "points"),
                                       "zone": note.get("color", ""), "zone_name": note.get("description", "")})
                    teams.append({"l": key, "name": t.get("displayName", ""), "short": t.get("shortDisplayName", ""),
                                  "keys": keys_for(t.get("displayName", ""), t.get("shortDisplayName", ""))})
        except Exception as ex:
            print("Standings failed:", code, ex)
        try:
            st = json.loads(get(f"https://site.api.espn.com/apis/site/v2/sports/soccer/{code}/statistics"))
            for cat in st.get("stats", []):
                rows = []
                for ld in (cat.get("leaders") or [])[:10]:
                    a = ld.get("athlete") or {}
                    m = re.search(r"Matches:\s*(\d+)", ld.get("displayValue", ""))
                    rows.append({"player": a.get("displayName", ""), "team": (a.get("team") or {}).get("displayName", ""),
                                 "value": int(ld.get("value") or 0), "matches": m.group(1) if m else ""})
                if cat.get("name") == "goalsLeaders":
                    lg["scorers"] = rows
                elif cat.get("name") == "assistsLeaders":
                    lg["assists"] = rows[:5]
        except Exception as ex:
            print("Stats failed:", code, ex)
        out.append(lg)
    seen, uniq = set(), []
    for t in teams:
        if t["name"] not in seen:
            seen.add(t["name"])
            uniq.append(t)
    return {"leagues": out, "teams": uniq}


CSS = """<style>
main{max-width:1000px}
.ltabs{display:flex;gap:8px;flex-wrap:wrap;margin:14px 0 18px}
.ltab{display:flex;align-items:center;gap:6px;background:#10251a;color:#eef6f0;border:1px solid #1f3d2b;border-radius:22px;padding:7px 13px;font:600 14px system-ui,sans-serif;cursor:pointer}
.ltab.on{background:#2ee06f;color:#04210f;border-color:#2ee06f}.flag{width:20px;height:14px;border-radius:2px;object-fit:cover}
.lg{display:none}.lg.on{display:block}
.twrap{overflow-x:auto;background:#10251a;border:1px solid #1f3d2b;border-radius:14px}
table{border-collapse:collapse;width:100%;font-size:15px}
th,td{padding:9px 8px;text-align:center;white-space:nowrap}th{color:#9cb8a6;font-weight:600;font-size:13px;border-bottom:1px solid #1f3d2b}
td.tm,th.tm{text-align:start;white-space:normal;min-width:150px}td.tm{font-weight:700}
tr+tr td{border-top:1px solid #16301f}td.pts{font-weight:800;color:#ffc83d}
td.rk{border-inline-start:4px solid transparent;font-weight:700;color:#9cb8a6}
tr.mine td{background:#173d25}
.legend{display:flex;flex-wrap:wrap;gap:6px 16px;font-size:13px;color:#9cb8a6;margin:10px 4px}
.legend i{display:inline-block;width:10px;height:10px;border-radius:2px;margin-inline-end:6px}
.lead{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:20px}@media(max-width:720px){.lead{grid-template-columns:1fr}}
.lead h3{margin:6px 0 8px}.lead td.v{font-weight:800;color:#2ee06f}
.grp{color:#ffc83d;font-weight:700;text-align:start}
</style>"""


def render(data, path="tables.html"):
    e = html.escape
    tabs, panels = [], []
    for i, lg in enumerate(data["leagues"]):
        if not lg["rows"]:
            continue
        tabs.append(f'<button class="ltab{" on" if not tabs else ""}" data-k="{lg["key"]}-{i}"><img class="flag" src="https://flagcdn.com/w40/{lg["flag"]}.png" alt="" width="20" height="14"> {e(lg["name"])}</button>')
        zones, body, grp = {}, [], None
        for r in lg["rows"]:
            if r["group"] and r["group"] != grp:
                grp = r["group"]
                body.append(f'<tr><td colspan="8" class="grp">{e(grp)}</td></tr>')
            if r["zone"]:
                zones[r["zone"]] = r["zone_name"]
            body.append(f'<tr data-team="{e(r["team"])}"><td class="rk" style="border-inline-start-color:{e(r["zone"] or "transparent")}">{e(r["rank"])}</td>'
                        f'<td class="tm">{e(r["team"])}</td><td>{e(r["p"])}</td><td>{e(r["w"])}</td><td>{e(r["d"])}</td>'
                        f'<td>{e(r["l"])}</td><td>{e(r["gd"])}</td><td class="pts">{e(r["pts"])}</td></tr>')
        legend = "".join(f'<span><i style="background:{e(c)}"></i>{e(n)}</span>' for c, n in zones.items() if n)
        head = ('<tr><th>#</th><th class="tm" data-i18n="t_team">Team</th><th data-i18n="t_p">P</th><th data-i18n="t_w">W</th>'
                '<th data-i18n="t_d">D</th><th data-i18n="t_l">L</th><th data-i18n="t_gd">GD</th><th data-i18n="t_pts">Pts</th></tr>')

        def leaders(rows, title_key, title, col_key, col):
            if not rows:
                return ""
            trs = "".join(f'<tr><td>{n}</td><td class="tm">{e(r["player"])}<br><small style="color:#9cb8a6;font-weight:500">{e(r["team"])}</small></td>'
                          f'<td>{e(r["matches"])}</td><td class="v">{r["value"]}</td></tr>' for n, r in enumerate(rows, 1))
            return (f'<div><h3 data-i18n="{title_key}">{title}</h3><div class="twrap"><table><tr><th>#</th><th class="tm" data-i18n="t_player">Player</th>'
                    f'<th data-i18n="t_p">P</th><th data-i18n="{col_key}">{col}</th></tr>{trs}</table></div></div>')
        panels.append(f'<section class="lg{" on" if len(panels) == 0 else ""}" id="{lg["key"]}-{i}"><h2>{e(lg["name"])} <small style="color:#9cb8a6;font-size:15px">{e(lg["season"])}</small></h2>'
                      f'<div class="twrap"><table>{head}{"".join(body)}</table></div><div class="legend">{legend}</div>'
                      f'<div class="lead">{leaders(lg["scorers"], "t_scorers", "Top scorers", "t_goals", "Goals")}'
                      f'{leaders(lg["assists"], "t_assists", "Top assists", "t_ast", "Assists")}</div></section>')
    script = """<script>
(function(){
  var tabs = document.querySelectorAll('.ltab');
  function show(k){
    tabs.forEach(function(t){ t.classList.toggle('on', t.dataset.k === k); });
    document.querySelectorAll('.lg').forEach(function(p){ p.classList.toggle('on', p.id === k); });
    try { history.replaceState(null, '', '#' + k.split('-')[0]); } catch(e) {}
  }
  tabs.forEach(function(t){ t.onclick = function(){ show(t.dataset.k); }; });
  var h = location.hash.slice(1); tabs.forEach(function(t){ if (h && t.dataset.k.split('-')[0] === h) show(t.dataset.k); });
  var mine = []; try { mine = JSON.parse(localStorage.getItem('fa_teams') || '[]'); } catch(e) {}
  document.querySelectorAll('tr[data-team]').forEach(function(r){ if (mine.indexOf(r.dataset.team) >= 0) r.classList.add('mine'); });
})();
</script>"""
    body = (CSS + '<h1 data-i18n="h_tables">League Tables & Top Scorers</h1>'
            '<p class="meta" data-i18n="tables_intro">Standings, top scorers and top assists for the biggest leagues – updated every hour.</p>'
            f'<div class="ltabs">{"".join(tabs)}</div>{"".join(panels) or "<p class=meta>Tables are loading – check back soon.</p>"}')
    open(path, "w").write(page("Football League Tables & Top Scorers – Premier League, LaLiga, Serie A and more",
                               "Live league tables, top scorers and top assists for the Premier League, LaLiga, Serie A, Bundesliga, "
                               "Ligue 1, the Champions League and the Saudi Pro League, updated every hour.",
                               body, 0, note=False, extra=script))
    return path
