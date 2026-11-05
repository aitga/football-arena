"""One page per match (matches/<slug>.html) + matches/index.html, for search engines and visitors.
Pages are kept for 30 days after kick-off and get the final score once the match is over."""
import datetime
import html
import os
import re
import unicodedata

from layout import page, SITE

KEEP_DAYS = 30
MENA_TV = {"eng": "beIN SPORTS", "esp": "beIN SPORTS", "ger": "beIN SPORTS", "fra": "beIN SPORTS", "eur": "beIN SPORTS"}


def slugify(s):
    s = "".join(ch for ch in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(ch) != "Mn")
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def slug_of(f):
    return f"{slugify(f['home'])}-vs-{slugify(f['away'])}-{f['date'][:10]}"


def parse(d):
    return datetime.datetime.fromisoformat(d.replace("Z", "+00:00"))


def merge_archive(archive, fixtures):
    """archive: {id: fixture}. Newer data wins; old matches are dropped after KEEP_DAYS."""
    now = datetime.datetime.now(datetime.timezone.utc)
    for f in fixtures:
        archive[f["id"]] = dict(archive.get(f["id"], {}), **f)
    return {k: v for k, v in archive.items() if now - parse(v["date"]) < datetime.timedelta(days=KEEP_DAYS)}


def _team_row(tables, name):
    for lg in tables.get("leagues", []):
        for r in lg.get("rows", []):
            if r["team"] == name:
                return lg["name"], r
    return None, None


def _related(items, f, key):
    words = [slugify(f["home"]).split("-")[0], slugify(f["away"]).split("-")[0]]
    words = [w for w in words if len(w) >= 4]
    out = []
    for it in items:
        t = slugify(it.get(key, ""))
        if any(re.search(r"(^|-)" + re.escape(w) + r"($|-)", t) for w in words):
            out.append(it)
    return out[:4]


def render_all(archive, tables, vids, news):
    e = html.escape
    os.makedirs("matches", exist_ok=True)
    now = datetime.datetime.now(datetime.timezone.utc)
    pages = []
    for f in sorted(archive.values(), key=lambda x: x["date"]):
        d = parse(f["date"])
        slug = slug_of(f)
        state = f.get("state") or ("in" if f.get("live") else "pre")
        date_txt = d.strftime("%A %d %B %Y")
        time_txt = d.strftime("%H:%M UTC")
        tv = []
        if MENA_TV.get(f["l"]):
            tv.append(("tv_mena", "Arab world & North Africa", MENA_TV[f["l"]]))
        if f.get("usa"):
            tv.append(("tv_usa", "USA", ", ".join(f["usa"])))
        if state == "post":
            score = f'<div class="msc">{e(str(f.get("hs", "")))} – {e(str(f.get("as", "")))}</div><div class="mst" data-i18n="lv_ft">FT</div>'
            title = f"{f['home']} {f.get('hs', '')}-{f.get('as', '')} {f['away']} – Result & Match Report ({f['comp']}, {d.strftime('%d %b %Y')})"
            desc = (f"{f['home']} {f.get('hs', '')}-{f.get('as', '')} {f['away']}: final score of the {f['comp']} match played on "
                    f"{date_txt}. Highlights, league table and more on Football Arena.")
            status = "https://schema.org/EventScheduled"
        else:
            live = state == "in"
            score = (f'<div class="msc">{e(str(f.get("hs", "")))} – {e(str(f.get("as", "")))}</div><div class="mst live">● <span data-i18n="live">LIVE</span> {e(f.get("clock", ""))}</div>'
                     if live else '<div class="msc vs">vs</div>')
            chan = (" on " + tv[0][2]) if tv else ""
            title = f"{f['home']} vs {f['away']} – Live Score, Kick-off Time & TV Channel ({d.strftime('%d %b %Y')})"
            desc = (f"{f['home']} vs {f['away']} in the {f['comp']} on {date_txt} at {time_txt}{chan}. "
                    f"Live score, TV channels, stadium and league table on Football Arena.")
            status = "https://schema.org/EventScheduled"
        tv_html = "".join(f'<li>📺 <span data-i18n="{k}">{e(lbl)}</span>: <b>{e(ch)}</b></li>' for k, lbl, ch in tv) or \
            '<li>📺 <span data-i18n="tv_check">Check your local TV listings</span></li>'
        rows = []
        for name in (f["home"], f["away"]):
            lg, r = _team_row(tables, name)
            if r:
                rows.append(f'<tr><td>{e(r["rank"])}</td><td class="tm">{e(r["team"])}</td><td>{e(r["p"])}</td><td>{e(r["gd"])}</td><td class="pts">{e(r["pts"])}</td></tr>')
        table_html = ("<h2 data-i18n=\"m_table\">League table</h2><div class=\"twrap\"><table><tr><th>#</th><th class=\"tm\" data-i18n=\"t_team\">Team</th>"
                      "<th data-i18n=\"t_p\">P</th><th data-i18n=\"t_gd\">GD</th><th data-i18n=\"t_pts\">Pts</th></tr>" + "".join(rows) +
                      "</table></div><p><a href=\"../tables.html\" data-i18n=\"m_all_tables\">See the full league tables →</a></p>") if rows else ""
        rel_v = _related(vids, f, "title")
        rel_n = _related(news, f, "title")
        rel = "".join(f'<li>🎬 <a href="https://www.youtube.com/watch?v={e(v["id"])}" target="_blank" rel="noopener">{e(v["title"])}</a></li>' for v in rel_v)
        rel += "".join(f'<li>📰 <a href="{e(n["link"])}" target="_blank" rel="noopener">{e(n["title"])}</a> <small>({e(n["source"])})</small></li>' for n in rel_n)
        rel_html = f'<h2 data-i18n="m_related">Related highlights & news</h2><ul class="rel">{rel}</ul>' if rel else ""
        live_btn = (f'<p><a class="btn" href="../live.html#{e(f["code"])}/{e(f["id"])}">🔴 <span data-i18n="watch">Live tracker</span></a></p>'
                    if state != "post" else "")
        body = f"""{CSS}
<p class="meta"><a href="index.html" data-i18n="m_all">All matches</a> › {e(f['comp'])}</p>
<h1>{e(f['home'])} vs {e(f['away'])}</h1>
<div class="mbox"><div class="mt">{e(f['home'])}</div><div class="mid">{score}</div><div class="mt r">{e(f['away'])}</div></div>
<ul class="facts">
<li>🏆 <b>{e(f['comp'])}</b></li>
<li>🗓️ <span data-i18n="m_kick">Kick-off</span>: <b class="ftime" data-k="{int(d.timestamp())}">{e(date_txt)} · {e(time_txt)}</b></li>
{f'<li>🏟️ <span data-i18n="m_venue">Stadium</span>: <b>{e(f["venue"])}</b></li>' if f.get("venue") else ''}
</ul>
<h2 data-i18n="m_watch">Where to watch on TV</h2><ul class="facts">{tv_html}</ul>
<p class="meta" data-i18n="fix_note">Times are shown in your local time. TV channels can change – please check your local listings.</p>
{live_btn}{table_html}{rel_html}"""
        jsonld = {"@context": "https://schema.org", "@type": "SportsEvent", "name": f"{f['home']} vs {f['away']}",
                  "startDate": f["date"], "eventStatus": status, "sport": "Soccer",
                  "homeTeam": {"@type": "SportsTeam", "name": f["home"]}, "awayTeam": {"@type": "SportsTeam", "name": f["away"]},
                  "competitor": [{"@type": "SportsTeam", "name": f["home"]}, {"@type": "SportsTeam", "name": f["away"]}],
                  "url": f"{SITE}matches/{slug}.html", "organizer": {"@type": "SportsOrganization", "name": f["comp"]}}
        if f.get("venue"):
            jsonld["location"] = {"@type": "Place", "name": f["venue"]}
        open(f"matches/{slug}.html", "w").write(page(title, desc, body, 1, note=False, path=f"matches/{slug}.html", jsonld=jsonld))
        pages.append((f, slug, d, state))
    # matches/index.html
    def li(f, slug, d, state):
        sc = f"{f.get('hs', '')}–{f.get('as', '')}" if state != "pre" else "vs"
        return (f'<a class="mrow" href="{slug}.html"><span class="ftime" data-k="{int(d.timestamp())}">{d.strftime("%d %b · %H:%M UTC")}</span>'
                f'<b>{e(f["home"])} <span class="sc2">{e(sc)}</span> {e(f["away"])}</b><small>{e(f["comp"])}</small></a>')
    up = [p for p in pages if p[3] != "post" and p[2] > now - datetime.timedelta(hours=3)]
    rec = [p for p in pages if p[3] == "post"][::-1]
    body = (CSS + '<h1 data-i18n="m_h1">Football Matches: Live Scores, Kick-off Times & TV Channels</h1>'
            '<p class="meta" data-i18n="m_intro">Every big match in the Premier League, LaLiga, Serie A, Bundesliga, Ligue 1, Champions League and Europa League.</p>'
            '<h2 data-i18n="m_upcoming">Upcoming & live</h2>' + ("".join(li(*p) for p in up) or "<p class=meta>—</p>") +
            '<h2 data-i18n="m_recent">Recent results</h2>' + ("".join(li(*p) for p in rec[:60]) or "<p class=meta>—</p>"))
    open("matches/index.html", "w").write(page("Football Matches Today – Live Scores, Kick-off Times & TV Channels",
                                               "Today's and upcoming football matches with kick-off times, TV channels (beIN SPORTS and more), "
                                               "live scores and results for the biggest leagues.", body, 1, note=False, path="matches/index.html"))
    return {p[0]["id"]: p[1] for p in pages}, [(f"matches/{p[1]}.html", p[2]) for p in pages]


CSS = """<style>
main{max-width:860px}
.mbox{display:grid;grid-template-columns:1fr auto 1fr;align-items:center;gap:14px;background:#10251a;border:1px solid #1f3d2b;border-radius:16px;padding:18px;margin:12px 0}
.mt{font-size:22px;font-weight:800;line-height:1.2}.mt.r{text-align:end}.mid{text-align:center}
.msc{font-size:40px;font-weight:900;color:#ffc83d;white-space:nowrap}.msc.vs{font-size:22px;color:#9cb8a6}.mst{font-size:13px;color:#9cb8a6;font-weight:700}.mst.live{color:#ff5b5b}
.facts{list-style:none;padding:0;margin:8px 0}.facts li{padding:6px 0;font-size:16px}
.btn{display:inline-block;background:#ff6b6b;color:#fff;border-radius:22px;padding:9px 20px;font-weight:800;text-decoration:none}
.twrap{background:#10251a;border:1px solid #1f3d2b;border-radius:14px;overflow-x:auto}table{border-collapse:collapse;width:100%}
th,td{padding:9px 8px;text-align:center}th{color:#9cb8a6;font-size:13px}td.tm,th.tm{text-align:start}td.pts{color:#ffc83d;font-weight:800}
.rel{padding-inline-start:18px}.rel li{margin:6px 0}
.mrow{display:grid;grid-template-columns:150px 1fr;gap:2px 12px;align-items:center;background:#10251a;border:1px solid #1f3d2b;border-radius:12px;padding:10px 14px;margin:8px 0;color:#eef6f0;text-decoration:none}
.mrow:hover{border-color:#2ee06f}.mrow .ftime{color:#ffc83d;font-size:13px;font-weight:700;grid-row:span 2}.mrow small{color:#9cb8a6}
.sc2{color:#2ee06f;margin:0 6px}@media(max-width:560px){.mrow{grid-template-columns:1fr}.mrow .ftime{grid-row:auto}}
</style>"""
