"""Builds the Football Arena website (index.html) from live football news feeds
and the leagues' official YouTube highlight channels. Runs every hour on GitHub."""
import datetime
import email.utils
import html
import json
import os
import re
import xml.etree.ElementTree as ET

import requests

UA = {"User-Agent": "FootballArenaBot/1.0 (+https://github.com)"}

NEWS_FEEDS = [
    ("BBC Sport", "https://feeds.bbci.co.uk/sport/football/rss.xml"),
    ("The Guardian", "https://www.theguardian.com/football/rss"),
    ("ESPN", "https://www.espn.com/espn/rss/soccer/news"),
]
# official league / competition YouTube channels (by @handle)
HIGHLIGHT_CHANNELS = [  # official league / competition YouTube channels (channel IDs)
    ("Premier League", "UCG5qGWdu8nIRZqJ_GgDwQ-w"),
    ("LaLiga", "UCTv-XvfzLX3i4IGWAm4sbmA"),
    ("UEFA", "UCyGa1YEx9ST66rYrJTGIKOw"),
    ("Serie A", "UCBJeMCIeLQos7wacox4hmLQ"),
    ("Bundesliga", "UC6UL29enLNe4mqwTfAyeNuw"),
    ("FIFA", "UCpcTrCXblq78GZrTUTLWeBw"),
    ("Ligue 1", "@Ligue1"),  # handle: looked up to its channel ID automatically
    ("beIN SPORTS", "@beINSPORTS"),  # Arabic commentary (Middle East & North Africa)
]
AR_CHANNELS = {"beIN SPORTS"}  # channels whose videos have Arabic commentary (only their highlight videos are used)
AR_LEAGUE = [("eng", r"الإنجليزي|الانجليزي|البريميرليغ"), ("esp", r"الإسباني|الاسباني|الليغا"), ("ita", r"الإيطالي|الايطالي"),
             ("ger", r"الألماني|الالماني|البوندسليغا"), ("fra", r"الفرنسي"), ("eur", r"أبطال أوروبا|ابطال اوروبا|الدوري الأوروبي|الدوري الاوروبي")]


def commentary_of(v):
    """'ar' for Arabic commentary, 'en' for the official league channels (English)."""
    return "ar" if v["channel"] in AR_CHANNELS or re.search("[\u0600-\u06FF]", v["title"]) else "en"


def league_of_video(v):
    if v["channel"] in CHANNEL_LEAGUE:
        return CHANNEL_LEAGUE[v["channel"]]
    for k, rx in AR_LEAGUE:
        if re.search(rx, v["title"]):
            return k
    return "wld"
NS = {"atom": "http://www.w3.org/2005/Atom", "media": "http://search.yahoo.com/mrss/",
      "yt": "http://www.youtube.com/xml/schemas/2015"}


def get(url):
    r = requests.get(url, headers=UA, timeout=30)
    r.raise_for_status()
    return r.content


def parse_date(text):
    try:
        return email.utils.parsedate_to_datetime(text).astimezone(datetime.timezone.utc)
    except Exception:
        try:
            return datetime.datetime.fromisoformat(text.replace("Z", "+00:00"))
        except Exception:
            return datetime.datetime.now(datetime.timezone.utc)


def clean(text, limit=220):
    text = re.sub(r"<[^>]+>", "", html.unescape(text or "")).strip()
    return text if len(text) <= limit else text[:limit].rsplit(" ", 1)[0] + "…"


def news():
    items = []
    for source, url in NEWS_FEEDS:
        try:
            root = ET.fromstring(get(url))
        except Exception as e:
            print("Feed failed:", source, e)
            continue
        for it in root.iter("item"):
            img = None
            for tag in ("media:thumbnail", "media:content"):
                el = it.find(tag, NS)
                if el is not None and el.get("url"):
                    img = el.get("url")
            enc = it.find("enclosure")
            if not img and enc is not None and "image" in (enc.get("type") or ""):
                img = enc.get("url")
            items.append({"source": source, "title": clean(it.findtext("title"), 160),
                          "link": (it.findtext("link") or "").strip(), "summary": clean(it.findtext("description")),
                          "date": parse_date(it.findtext("pubDate") or ""), "image": img})
    seen, out = set(), []
    for it in sorted(items, key=lambda x: x["date"], reverse=True):
        key = it["title"].lower()[:60]
        if it["link"] and key not in seen:
            seen.add(key)
            out.append(it)
    return out[:60]


def channel_id(handle):
    page = get(f"https://www.youtube.com/{handle}").decode("utf-8", "ignore")
    m = re.search(r'"(?:externalId|channelId)":"(UC[\w-]{22})"', page)
    return m.group(1) if m else None


def channel_videos_api(cid, key):
    """Official YouTube Data API (free key): latest uploads of a channel."""
    if not cid.startswith("UC"):
        ch = requests.get("https://www.googleapis.com/youtube/v3/channels", timeout=30,
                          params={"part": "id", "forHandle": cid, "key": key}).json()
        cid = ch["items"][0]["id"]
    r = requests.get("https://www.googleapis.com/youtube/v3/playlistItems", timeout=30, params={
        "part": "snippet", "playlistId": "UU" + cid[2:], "maxResults": 8, "key": key}).json()
    if "error" in r:
        raise RuntimeError(r["error"].get("message"))
    out = []
    for it in r.get("items", []):
        sn = it["snippet"]
        out.append({"id": sn["resourceId"]["videoId"], "title": sn["title"], "date": sn["publishedAt"]})
    return out


def highlights():
    vids = []
    key = os.environ.get("YT_API_KEY", "").strip()
    for name, handle in HIGHLIGHT_CHANNELS:
        if key:
            try:
                for v in channel_videos_api(handle, key):
                    if "shorts" not in v["title"].lower():
                        vids.append({"channel": name, "id": v["id"], "title": clean(v["title"], 120),
                                     "date": parse_date(v["date"])})
                continue
            except Exception as e:
                print("YouTube API failed:", name, e)
        try:
            cid = handle if handle.startswith("UC") else channel_id(handle)
            root = ET.fromstring(get(f"https://www.youtube.com/feeds/videos.xml?channel_id={cid}"))
        except Exception as e:
            print("Channel failed:", name, e)
            continue
        for en in root.findall("atom:entry", NS)[:8]:
            title = en.findtext("atom:title", "", NS)
            if "shorts" in title.lower():
                continue
            vids.append({"channel": name, "id": en.findtext("yt:videoId", "", NS), "title": clean(title, 120),
                         "date": parse_date(en.findtext("atom:published", "", NS))})
    hl = [v for v in vids if re.search(r"highlight|resumen|sintesi|goals?\b|résumé|ملخص|أهداف|اهداف", v["title"], re.I)]
    rest = [v for v in vids if v not in hl and v["channel"] not in AR_CHANNELS]  # Arabic channels: highlights only
    return sorted(hl, key=lambda v: v["date"], reverse=True)[:18] + sorted(rest, key=lambda v: v["date"], reverse=True)[:6]


def ago(d):
    s = (datetime.datetime.now(datetime.timezone.utc) - d).total_seconds()
    if s < 3600:
        return f"{max(1, int(s // 60))} min ago"
    if s < 86400:
        return f"{int(s // 3600)} h ago"
    return f"{int(s // 86400)} d ago"


# country / league groups used for the filter buttons
LEAGUES = [  # key, flag code (flagcdn), country, league, news keywords
    ("eng", "gb-eng", "England", "Premier League",
     r"premier league|arsenal|chelsea|liverpool|man(chester)? (city|utd|united)|tottenham|spurs|newcastle|aston villa|"
     r"everton|west ham|brighton|crystal palace|fulham|wolves|brentford|bournemouth|nottingham forest|leeds|burnley|sunderland|"
     r"fa cup|carabao|efl|championship|amorim|arteta|slot\b|guardiola|maresca|england"),
    ("esp", "es", "Spain", "LaLiga",
     r"la ?liga|real madrid|barcelona|barça|atletico|atlético|sevilla|villarreal|real sociedad|athletic (club|bilbao)|"
     r"betis|valencia|girona|osasuna|celta|mallorca|espanyol|getafe|rayo|alaves|alavés|copa del rey|ancelotti|flick|simeone|xabi alonso|spain"),
    ("ita", "it", "Italy", "Serie A",
     r"serie a|juventus|\binter\b|inter milan|ac milan|\bmilan\b|napoli|roma\b|lazio|atalanta|fiorentina|bologna|torino|"
     r"genoa|udinese|como\b|coppa italia|conte|allegri|italy|italian"),
    ("ger", "de", "Germany", "Bundesliga",
     r"bundesliga|bayern|dortmund|leverkusen|leipzig|frankfurt|stuttgart|wolfsburg|gladbach|freiburg|union berlin|"
     r"werder|hoffenheim|mainz|kompany|germany|german"),
    ("fra", "fr", "France", "Ligue 1",
     r"ligue 1|psg|paris saint|paris st|marseille|lyon|monaco|lille|nice\b|lens\b|rennes|nantes|france|french"),
    ("eur", "eu", "Europe", "Champions League & UEFA",
     r"champions league|europa league|conference league|uefa|euro 20\d\d"),
    ("wld", "", "World", "FIFA & International",
     r"world cup|fifa|international|africa cup|afcon|copa america|nations league|qualifier|morocco|brazil|argentina|usa\b|mexico"),
]
CHANNEL_LEAGUE = {"Premier League": "eng", "LaLiga": "esp", "Serie A": "ita", "Bundesliga": "ger",
                  "Ligue 1": "fra", "UEFA": "eur", "FIFA": "wld"}
SMALL = {"of", "the", "and", "in", "at", "vs", "v", "to", "de", "la", "el", "on", "for", "from", "with"}


FIXED = {"laliga": "LaLiga", "uefa": "UEFA", "fifa": "FIFA", "var": "VAR", "psg": "PSG", "mvp": "MVP",
         "#ucl": "#UCL", "ucl": "UCL", "goals!": "Goals!"}


def nice_title(t):
    """JUVENTUS-NAPOLI 2-0 | EXTENDED HIGHLIGHTS -> Juventus-Napoli 2-0 | Extended Highlights"""
    letters = [c for c in t if c.isalpha()]
    if not letters or sum(c.isupper() for c in letters) / len(letters) < 0.6:
        return t
    out = []
    for i, w in enumerate(t.split(" ")):
        lw = w.lower()
        if lw in FIXED:
            out.append(FIXED[lw])
        elif i and lw in SMALL:
            out.append(lw)
        elif len(w) <= 3 and w.isalpha():
            out.append(w)  # keep short codes: UCL, PSG, AC, FC
        else:
            out.append("-".join(p[:1].upper() + p[1:].lower() for p in w.split("-")))
    return " ".join(out)


def league_of_news(n):
    text = (n["title"] + " " + n["summary"]).lower()
    for key, *_rest, kw in LEAGUES:
        if re.search(kw, text):
            return key
    return "wld"


def flag(key):
    for k, code, country, *_ in LEAGUES:
        if k == key:
            return (f'<img class="flag" src="https://flagcdn.com/w40/{code}.png" alt="{country}" width="20" height="14">'
                    if code else '<span class="flag globe">🌍</span>')
    return ""



# ---------- upcoming matches (ESPN public scoreboard) ----------
FIX_LEAGUES = [("eng", "eng.1"), ("esp", "esp.1"), ("ita", "ita.1"), ("ger", "ger.1"), ("fra", "fra.1"),
               ("eur", "uefa.champions"), ("eur", "uefa.europa")]
# who shows each league in the Arab world / North Africa (checked Nov 2026; update if rights change)
MENA_TV = {"eng": "beIN SPORTS", "esp": "beIN SPORTS", "ger": "beIN SPORTS", "fra": "beIN SPORTS", "eur": "beIN SPORTS"}


def fixtures(days=7):
    out, seen = [], set()
    today = datetime.datetime.now(datetime.timezone.utc)
    for key, code in FIX_LEAGUES:
        for k in range(-1, days):  # yesterday too, so finished matches get their final score
            day = (today + datetime.timedelta(days=k)).strftime("%Y%m%d")
            try:
                data = json.loads(get(f"https://site.api.espn.com/apis/site/v2/sports/soccer/{code}/scoreboard?dates={day}"))
            except Exception as ex:
                print("Fixtures failed:", code, day, ex)
                continue
            for ev in data.get("events", []):
                st = ev.get("status", {}).get("type", {}).get("state")
                if st not in ("pre", "in", "post") or ev["id"] in seen:
                    continue
                seen.add(ev["id"])
                c = ev["competitions"][0]
                teams = {t.get("homeAway"): t for t in c.get("competitors", [])}
                h, a = teams.get("home", {}), teams.get("away", {})
                tv = []
                for b in c.get("broadcasts", []) or []:
                    tv += b.get("names", [])
                out.append({"id": ev["id"], "code": code, "l": key, "comp": data.get("leagues", [{}])[0].get("name", ""), "date": ev["date"],
                            "home": h.get("team", {}).get("displayName", "?"), "away": a.get("team", {}).get("displayName", "?"),
                            "hs": h.get("score", ""), "as": a.get("score", ""), "live": st == "in", "state": st,
                            "clock": ev.get("status", {}).get("displayClock", ""),
                            "venue": (c.get("venue") or {}).get("fullName", ""), "usa": sorted(set(tv))})
    out.sort(key=lambda f: f["date"])
    return out[:160]


def fixture_cards(fx, slugs=None):
    e = html.escape
    slugs = slugs or {}
    rows = []
    for f in fx:
        if f.get("state") == "post":
            continue
        d = parse_date(f["date"])
        if not f["live"] and d < datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=3):
            continue
        mid = (f'<span class="sc"><b>{e(str(f["hs"]))}</b><b>–</b><b>{e(str(f["as"]))}</b></span>' if f["live"] else '<span class="vs">vs</span>')
        badge = f'<span class="live">● <span data-i18n="live">LIVE</span> {e(f["clock"])}</span>' if f["live"] else ""
        tv = ""
        if MENA_TV.get(f["l"]):
            tv += f'<div>📺 <span data-i18n="tv_mena">Arab world & North Africa</span>: <b>{e(MENA_TV[f["l"]])}</b></div>'
        if f["usa"]:
            tv += f'<div>📺 <span data-i18n="tv_usa">USA</span>: <b>{e(", ".join(f["usa"]))}</b></div>'
        if not tv:
            tv = '<div>📺 <span data-i18n="tv_check">Check your local TV listings</span></div>'
        comp = f'<span data-i18n="lg_{f["l"]}">{e(f["comp"])}</span>' if f["l"] != "eur" else e(f["comp"])
        rows.append(
            f'<div class="card fix" data-l="{f["l"]}" data-s="{e(plain(f["home"] + " " + f["away"]))}"><div class="ftop">{flag(f["l"])} {comp}{badge}</div>'
            f'<div class="ftime" data-k="{int(d.timestamp())}">{d.strftime("%a %d %b · %H:%M UTC")}</div>'
            + (f'<a class="teams" href="matches/{e(slugs[f["id"]])}.html">' if f.get("id") in slugs else '<div class="teams">')
            + f'<span>{e(f["home"])}</span>{mid}<span>{e(f["away"])}</span>' + ('</a>' if f.get("id") in slugs else '</div>')
            + f'<div class="tv">{tv}</div>' + (f'<div class="venue">🏟️ {e(f["venue"])}</div>' if f["venue"] else "")
            + (f'<a class="watch" href="live.html#{e(f["code"])}/{e(f["id"])}">🔴 <span data-i18n="watch">Live tracker</span></a>' if f.get("id") else "")
            + '</div>')
    return "\n".join(rows) or '<p class="empty" data-i18n="no_fix">No matches scheduled in the next few days.</p>'


def gsv_tags():
    """Search-engine ownership tags from seo.json, e.g. {"google": "abc...", "bing": "123..."}"""
    try:
        cfg = json.load(open("seo.json"))
    except Exception:
        return ""
    out = ""
    if cfg.get("google"):
        out += f'<meta name="google-site-verification" content="{html.escape(cfg["google"])}">'
    if cfg.get("bing"):
        out += f'<meta name="msvalidate.01" content="{html.escape(cfg["bing"])}">'
    return out


STATIC_PAGES = ["", "tables.html", "matches/index.html", "live.html", "quiz.html", "articles/index.html", "about.html", "contact.html", "privacy.html"]


def write_sitemap(match_pages):
    import glob
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    urls = [(p, now, "hourly" if p in ("", "tables.html", "matches/index.html") else "weekly") for p in STATIC_PAGES]
    urls += [(p, now, "monthly") for p in sorted(glob.glob("articles/*.html")) if not p.endswith("index.html")]
    urls += [(p, d.strftime("%Y-%m-%d"), "hourly") for p, d in match_pages]
    xml = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for p, mod, freq in urls:
        xml.append(f"  <url><loc>https://www.footballarena.net/{html.escape(p)}</loc><lastmod>{mod}</lastmod><changefreq>{freq}</changefreq></url>")
    xml.append("</urlset>")
    open("sitemap.xml", "w").write("\n".join(xml) + "\n")
    open("robots.txt", "w").write("User-agent: *\nAllow: /\n\nSitemap: https://www.footballarena.net/sitemap.xml\n")
    return len(urls)


def plain(t):
    import unicodedata
    return "".join(ch for ch in unicodedata.normalize("NFD", (t or "").lower()) if unicodedata.category(ch) != "Mn")


def ago_span(d):
    return f'<span class="ago" data-t="{int(d.timestamp())}">{ago(d)}</span>'


def render(news_items, vids, fx=(), teams=(), slugs=None):
    e = html.escape
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%d %b %Y, %H:%M UTC")
    names = {k: f"{country} · {league}" for k, _c, country, league, _kw in LEAGUES}
    vcards = "\n".join(
        f'<a class="vid card" data-l="{lg}" data-c="{cm}" data-s="{e(plain(v["title"]))}" href="https://www.youtube.com/watch?v={e(v["id"])}" target="_blank" rel="noopener">'
        f'<div class="thumb"><img src="https://i.ytimg.com/vi/{e(v["id"])}/hqdefault.jpg" alt="" loading="lazy"><span class="play">▶</span></div>'
        f'<div class="vt">{e(nice_title(v["title"]))}</div>'
        f'<div class="meta">{flag(lg)} <span data-i18n="lg_{lg}">{e(names[lg].split(" · ")[1])}</span> · {ago_span(v["date"])} · <span class="cmtag">🎙️ {"عربي" if cm == "ar" else "EN"}</span></div></a>'
        for v in vids for lg in [league_of_video(v)] for cm in [commentary_of(v)]) \
        or '<p class="empty">Highlights are loading – check back soon.</p>'
    ncards = "\n".join(
        f'<a class="news card" data-l="{lg}" data-s="{e(plain(n["title"] + " " + n["summary"]))}" href="{e(n["link"])}" target="_blank" rel="noopener">'
        + (f'<img class="nimg" src="{e(n["image"])}" alt="" loading="lazy">' if n["image"] else "")
        + f'<div><div class="nt">{e(n["title"])}</div><p>{e(n["summary"])}</p>'
          f'<div class="meta">{flag(lg)} {e(n["source"])} · {ago_span(n["date"])}</div></div></a>'
        for n in news_items for lg in [league_of_news(n)]) \
        or '<p class="empty">News is loading – check back soon.</p>'
    chips = ('<button class="chip on" data-f="all">⚽ <span data-i18n="all">All</span></button>'
             '<button class="chip mychip" data-f="my">⭐ <span data-i18n="my_teams">My Teams</span></button>') + "".join(
        f'<button class="chip" data-f="{k}">{flag(k)} <span data-i18n="c_{k}">{e(country)}</span><small data-i18n="lg_{k}">{e(league)}</small></button>'
        for k, _c, country, league, _kw in LEAGUES)
    try:
        from articles_src import ARTICLES
        arts = sorted(ARTICLES, key=lambda a: a["date"], reverse=True)[:3]
    except Exception:
        arts = []
    acards = "\n".join(
        f'<a class="news card" href="articles/{e(a["slug"])}.html"><div><div class="nt">{e(a["title"])}</div>'
        f'<p>{e(a["summary"])}</p><div class="meta">📝 {e(a["tag"])} · Football Arena</div></div></a>' for a in arts)
    return (TEMPLATE.replace("{{FIXTURES}}", fixture_cards(fx, slugs)).replace("{{CHIPS}}", chips).replace("{{ARTICLES}}", acards).replace("{{VIDEOS}}", vcards)
            .replace("{{NEWS}}", ncards).replace("{{UPDATED}}", now)
            .replace("{{GSV}}", gsv_tags()).replace("{{TEAMS}}", json.dumps(list(teams), ensure_ascii=False).replace("</", "<\\/")))


TEMPLATE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Football Arena – Football Highlights & News by League</title>
<meta name="description" content="Latest football highlights and news sorted by country and league: Premier League, LaLiga, Serie A, Bundesliga, Ligue 1, Champions League and the World Cup. Plus football quizzes. Updated every hour.">
<meta property="og:title" content="Football Arena – Highlights, News & Quizzes">
<meta property="og:description" content="The latest football highlights and news by league, updated every hour. Test yourself with our football quiz.">
<meta property="og:image" content="https://www.footballarena.net/logo.png">
<link rel="canonical" href="https://www.footballarena.net/">
<meta property="og:url" content="https://www.footballarena.net/"><meta property="og:type" content="website"><meta property="og:site_name" content="Football Arena">
{{GSV}}
<script type="application/ld+json">{"@context":"https://schema.org","@graph":[{"@type":"WebSite","@id":"https://www.footballarena.net/#website","name":"Football Arena","alternateName":"FootballArena.net","url":"https://www.footballarena.net/","inLanguage":["en","ar","fr","es","pt","de","it"]},{"@type":"Organization","@id":"https://www.footballarena.net/#org","name":"Football Arena","url":"https://www.footballarena.net/","logo":"https://www.footballarena.net/logo.png","sameAs":["https://www.facebook.com/1429286323597310"]}]}</script>
<link rel="icon" href="logo.png">
<style>
:root{--bg:#07140c;--card:#10251a;--line:#1f3d2b;--txt:#eef6f0;--mut:#9cb8a6;--acc:#2ee06f;--gold:#ffc83d}
*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:120px}
body{margin:0;background:var(--bg);color:var(--txt);font:16px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
a{color:inherit;text-decoration:none}
header{background:linear-gradient(135deg,#0b3d1f,#07140c 70%);padding:18px 16px 14px}
.wrap{max-width:1150px;margin:0 auto}
.brand{display:flex;align-items:center;gap:12px;flex-wrap:wrap}.brand img{width:52px;height:52px;border-radius:12px}
h1{margin:0;font-size:28px;letter-spacing:.5px}h1 span{color:var(--acc)}
.tag{color:var(--mut);margin:2px 0 0;font-size:14px}
.bar{position:sticky;top:0;z-index:5;background:rgba(7,20,12,.95);backdrop-filter:blur(6px);border-bottom:1px solid var(--line)}
nav{display:flex;gap:4px;overflow-x:auto;padding:6px 16px 0;scrollbar-width:none}
nav a{white-space:nowrap;padding:8px 14px;border-radius:10px;color:var(--mut);font-weight:600;font-size:15px}
nav a:hover{background:var(--card);color:var(--txt)}nav a.quiz{color:var(--gold)}
.chips{display:flex;gap:8px;overflow-x:auto;padding:8px 16px 10px;scrollbar-width:none}
.chip{flex:none;display:flex;align-items:center;gap:6px;background:var(--card);color:var(--txt);border:1px solid var(--line);
border-radius:22px;padding:6px 12px;font:600 14px system-ui,sans-serif;cursor:pointer}
.chip small{color:var(--mut);font-weight:500;font-size:12px}.chip.on{background:var(--acc);color:#04210f;border-color:var(--acc)}.chip.on small{color:#0b3d1f}
.flag{width:20px;height:14px;border-radius:2px;object-fit:cover;vertical-align:-2px}.globe{width:auto;height:auto;font-size:14px}
main{padding:22px 16px 40px}
h2{font-size:21px;margin:4px 0 14px;display:flex;align-items:center;gap:8px}
h2:before{content:"";width:6px;height:22px;background:var(--acc);border-radius:3px}
h2 .count{color:var(--mut);font-size:14px;font-weight:500}
.grid{display:grid;gap:14px;grid-template-columns:repeat(auto-fill,minmax(260px,1fr))}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;overflow:hidden;transition:transform .15s,border-color .15s}
.card:hover{transform:translateY(-2px);border-color:var(--acc)}.card.hide{display:none}
.thumb{position:relative;aspect-ratio:16/9;background:#000;display:grid;place-items:center}
.thumb img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
.play{position:relative;width:50px;height:50px;border-radius:50%;background:rgba(0,0,0,.6);display:grid;place-items:center;font-size:20px;color:#fff}
.vt,.nt{font-weight:700;padding:10px 12px 2px;line-height:1.3}.meta{color:var(--mut);font-size:13px;padding:2px 12px 12px}
.news{display:flex;flex-direction:column}.nimg{width:100%;aspect-ratio:16/9;object-fit:cover;background:#000}
.news p{color:var(--mut);font-size:14px;margin:4px 12px 4px}
.more{display:block;margin:16px auto 0;background:none;border:1px solid var(--acc);color:var(--acc);border-radius:22px;padding:9px 22px;font:600 15px system-ui,sans-serif;cursor:pointer}
.more:hover{background:var(--acc);color:#04210f}
section{margin-bottom:38px}.empty{color:var(--mut)}
.quizban{display:flex;align-items:center;gap:16px;flex-wrap:wrap;background:linear-gradient(120deg,#183d22,#2a2a0c);border:1px solid #4b5a1f;border-radius:16px;padding:18px 20px}
.quizban b{font-size:20px}.quizban p{margin:4px 0 0;color:var(--mut)}
.quizban a{margin-left:auto;background:var(--gold);color:#2a1d00;font-weight:800;border-radius:22px;padding:10px 22px}
footer{border-top:1px solid var(--line);color:var(--mut);font-size:13px;padding:18px 16px;text-align:center}
footer a{color:var(--acc)}
.cmrow{display:flex;flex-wrap:wrap;align-items:center;gap:8px;margin:-4px 0 14px;color:var(--mut);font-size:14px;font-weight:600}
.cmb{background:var(--card);color:var(--txt);border:1px solid var(--line);border-radius:20px;padding:5px 12px;font:600 14px system-ui,sans-serif;cursor:pointer}
.cmb.on{background:#ffc83d;border-color:#ffc83d;color:#2a1d00}.cmtag{white-space:nowrap}
.chip.mychip{border-color:#ffc83d}.chip.mychip.on{background:#ffc83d;border-color:#ffc83d;color:#2a1d00}
.modal{position:fixed;inset:0;z-index:50;background:rgba(0,0,0,.72);display:grid;place-items:center;padding:16px}.modal[hidden]{display:none}
.mbox{background:var(--card);border:1px solid var(--line);border-radius:18px;width:min(640px,100%);max-height:88vh;display:flex;flex-direction:column;overflow:hidden}
.mbox.wide{width:min(980px,100%)}.mhead{display:flex;align-items:center;gap:10px;padding:14px 16px;border-bottom:1px solid var(--line)}
.mhead b{flex:1;font-size:17px;line-height:1.3}.x{background:none;border:0;color:var(--txt);font-size:22px;cursor:pointer}
.ptabs{display:flex;gap:6px;overflow-x:auto;padding:12px 16px 4px;scrollbar-width:none}
.ptab{flex:none;background:var(--bg);color:var(--mut);border:1px solid var(--line);border-radius:18px;padding:6px 12px;font:600 13px system-ui,sans-serif;cursor:pointer}
.ptab.on{background:var(--acc);color:#04210f;border-color:var(--acc)}
.pteams{display:grid;grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:8px;padding:12px 16px;overflow:auto}
.pteam{text-align:start;background:var(--bg);color:var(--txt);border:1px solid var(--line);border-radius:12px;padding:10px 12px;font:600 14px system-ui,sans-serif;cursor:pointer}
.pteam.on{border-color:#ffc83d;background:#2a2a0c}
.mfoot{display:flex;align-items:center;justify-content:space-between;padding:12px 16px;border-top:1px solid var(--line)}
.done{background:var(--acc);color:#04210f;border:0;border-radius:20px;padding:9px 24px;font:800 15px system-ui,sans-serif;cursor:pointer}
.vwrap{position:relative;aspect-ratio:16/9;background:#000}.vwrap iframe,.vwrap #ytp{position:absolute;inset:0;width:100%;height:100%;border:0}
.ytbig{position:absolute;inset:0;display:grid;place-content:center;gap:12px;text-align:center;color:#fff;font-size:52px;background:radial-gradient(#3a0d0d,#000)}
.ytbig span{font-size:18px;font-weight:700;background:#e62117;border-radius:24px;padding:10px 22px}
.yt{margin:0;padding:10px 16px;font-size:14px}.yt a{color:var(--acc)}
.fix{padding:12px 14px}.ftop{display:flex;align-items:center;gap:6px;color:var(--mut);font-size:13px;font-weight:600}
.ftime{color:var(--gold);font-weight:700;font-size:14px;margin:6px 0 4px}
.teams{display:grid;grid-template-columns:1fr auto 1fr;gap:8px;align-items:center;font-weight:700;font-size:16px;line-height:1.25;margin:6px 0 10px}
.teams span:last-child{text-align:end}.vs{color:var(--mut);font-size:13px}.sc{display:inline-flex;gap:5px;background:var(--acc);color:#04210f;border-radius:8px;padding:2px 8px}
.live{margin-inline-start:auto;color:#ff5b5b;font-weight:800;font-size:12px}
.tv{font-size:13px;color:var(--mut);border-top:1px solid var(--line);padding-top:8px}.tv b{color:var(--txt)}
.venue{font-size:12px;color:var(--mut);margin-top:6px}
a.teams{color:inherit;text-decoration:none}a.teams:hover span{text-decoration:underline}
.watch{display:inline-block;margin-top:9px;font-size:13px;font-weight:700;color:#ff6b6b;border:1px solid #ff6b6b;border-radius:16px;padding:4px 12px}.watch:hover{background:#ff6b6b;color:#fff}
nav a.livelink{color:#ff6b6b}.fnote{color:var(--mut);font-size:13px;margin:-6px 0 12px}
.langpick{margin-inline-start:auto;background:var(--card);color:var(--txt);border:1px solid var(--line);border-radius:10px;padding:7px 10px;font:600 14px system-ui,sans-serif}
[dir=rtl] .quizban a{margin-left:0;margin-right:auto}
:lang(ar) body,:lang(ar) .chip,:lang(ar) .more{font-family:"Segoe UI",Tahoma,"Noto Sans Arabic",system-ui,sans-serif}
</style></head><body>
<header><div class="wrap brand"><img src="logo.png" alt="Football Arena" width="52" height="52"><div><h1>FOOTBALL <span>ARENA</span></h1>
<div class="tag" data-i18n="tagline">Highlights & news from the world's biggest leagues · updated every hour</div></div>
<select class="langpick" aria-label="Language"></select></div></header>
<div class="bar"><div class="wrap">
<nav><a href="#highlights">🎬 <span data-i18n="nav_hl">Highlights</span></a><a class="livelink" href="live.html">🔴 <span data-i18n="nav_live">Live</span></a><a href="#matches">📅 <span data-i18n="nav_fix">Matches</span></a><a href="tables.html">📊 <span data-i18n="nav_tables">Tables</span></a><a href="#news">📰 <span data-i18n="nav_news">News</span></a><a href="articles/index.html">📝 <span data-i18n="nav_art">Articles</span></a><a class="quiz" href="quiz.html">🧠 <span data-i18n="nav_quiz">Quiz</span></a><a href="https://www.facebook.com/1429286323597310" target="_blank" rel="noopener">👍 <span data-i18n="nav_fb">Facebook</span></a></nav>
<div class="chips">{{CHIPS}}</div>
</div></div>
<main class="wrap">
<section id="highlights"><h2><span data-i18n="h_hl">Latest Highlights</span> <span class="count"></span></h2>
<div class="cmrow"><span data-i18n="cm_hl">🎙️ Commentary:</span> <button class="cmb on" data-c="all" data-i18n="all">All</button><button class="cmb" data-c="en">🇬🇧 English</button><button class="cmb" data-c="ar">🇲🇦 العربية</button></div><div class="grid" data-show="8">
{{VIDEOS}}
</div><button class="more" data-i18n="more_hl">Show more highlights</button></section>
<section id="matches"><h2><span data-i18n="h_fix">Upcoming Matches & TV Channels</span> <span class="count"></span></h2>
<p class="fnote" data-i18n="fix_note">Times are shown in your local time. TV channels can change – please check your local listings.</p>
<div class="grid" data-show="9">
{{FIXTURES}}
</div><button class="more" data-i18n="more_fix">Show more matches</button>
<p><a href="matches/index.html" style="color:var(--acc)" data-i18n="m_all">All matches</a> →</p></section>
<section><div class="quizban"><span style="font-size:38px">🧠</span><div><b data-i18n="qb_t">How well do you know football?</b>
<p data-i18n="qb_p">Play our quiz by country and league – learn a fun fact with every answer.</p></div><a href="quiz.html" data-i18n="qb_btn">Play the quiz</a></div></section>
<section id="news"><h2><span data-i18n="h_news">Latest Football News</span> <span class="count"></span></h2><div class="grid" data-show="9">
{{NEWS}}
</div><button class="more" data-i18n="more_news">Show more news</button></section>
<section id="articles"><h2 data-i18n="h_art">Football Articles</h2><div class="grid">
{{ARTICLES}}
</div><p><a href="articles/index.html" style="color:var(--acc)" data-i18n="see_art">See all articles →</a></p></section>
</main>
<footer><span data-i18n="updated">Updated</span> {{UPDATED}} · <span data-i18n="foot">Videos play on the official YouTube channels of each league. News headlines link to the original
publishers (BBC Sport, The Guardian, ESPN). All rights belong to their owners.</span><br>
<a href="about.html" data-i18n="about">About</a> · <a href="contact.html" data-i18n="contact">Contact</a> · <a href="privacy.html" data-i18n="privacy">Privacy</a></footer>
<div class="modal" id="picker" hidden><div class="mbox"><div class="mhead"><b data-i18n="pick_teams">Pick your favourite teams</b>
<button class="x" data-close aria-label="Close">✕</button></div><div class="ptabs" id="ptabs"></div><div class="pteams" id="pteams"></div>
<div class="mfoot"><span class="meta" id="pcount"></span><button class="done" id="pdone" data-i18n="done">Done</button></div></div></div>
<div class="modal" id="player" hidden><div class="mbox wide"><div class="mhead"><b id="ptitle"></b><button class="x" data-close aria-label="Close">✕</button></div>
<div class="vwrap" id="vwrap"></div><p class="yt"><a id="ytlink" href="#" target="_blank" rel="noopener" data-i18n="yt_fallback">Video not playing? Watch it on YouTube</a></p></div></div>
<script id="teams-data" type="application/json">{{TEAMS}}</script>
<script src="i18n.js"></script>
<script>
(function(){
  var filter = "all";
  var TEAMS = []; try { TEAMS = JSON.parse(document.getElementById("teams-data").textContent); } catch(e) {}
  function getMine(){ try { return JSON.parse(localStorage.getItem("fa_teams") || "[]"); } catch(e) { return []; } }
  function setMine(a){ try { localStorage.setItem("fa_teams", JSON.stringify(a)); } catch(e) {} }
  function esc(x){ return x.replace(/[^a-z0-9 &'-]/g, ""); }
  var mineRe = null;
  function buildRe(){
    var keys = [];
    getMine().forEach(function(n){ TEAMS.forEach(function(t){ if (t.name === n) keys = keys.concat(t.keys); }); });
    mineRe = keys.length ? new RegExp("(^|[^a-z0-9])(" + keys.map(esc).join("|") + ")($|[^a-z0-9])") : null;
  }
  buildRe();
  var cmf = "all";  // commentary language filter for highlights
  try { cmf = localStorage.getItem("fa_cm") || "all"; } catch (e) {}
  document.querySelectorAll(".cmb").forEach(function(b){
    b.classList.toggle("on", b.dataset.c === cmf);
    b.onclick = function(){
      cmf = b.dataset.c;
      try { localStorage.setItem("fa_cm", cmf); } catch (e) {}
      document.querySelectorAll(".cmb").forEach(function(x){ x.classList.toggle("on", x === b); });
      document.querySelectorAll(".grid[data-show]").forEach(function(g){ g.dataset.limit = ""; });
      apply();
    };
  });
  function apply(){
    document.querySelectorAll(".grid[data-show]").forEach(function(g){
      var lim = +g.dataset.limit || +g.dataset.show, total = 0;
      g.querySelectorAll(".card").forEach(function(c){
        var ok = filter === "all" || (filter === "my" ? !!(mineRe && mineRe.test(c.dataset.s || "")) : c.dataset.l === filter);
        if (cmf !== "all" && c.dataset.c && c.dataset.c !== cmf) ok = false;
        if (!ok) { c.classList.add("hide"); return; }
        total++;
        c.classList.toggle("hide", total > lim);
      });
      var shown = g.querySelectorAll(".card:not(.hide)").length;
      var sec = g.closest("section");
      sec.querySelector(".more").style.display = shown < total ? "" : "none";
      sec.querySelector(".count").textContent = total ? "(" + total + ")" : "";
      var em = g.querySelector(".none");
      if (!total && !em){ em = document.createElement("p"); em.className = "empty none"; g.appendChild(em); }
      if (em){ var k = filter === "my" ? "no_my" : "none"; em.setAttribute("data-i18n", k); em.textContent = window.FA ? FA.t(k) : ""; }
      if (em) em.style.display = total ? "none" : "";
    });
  }
  document.querySelectorAll(".chip").forEach(function(b){
    b.onclick = function(){
      if (b.dataset.f === "my" && (!getMine().length || filter === "my")) { openPicker(); return; }
      document.querySelectorAll(".chip").forEach(function(x){ x.classList.toggle("on", x === b); });
      filter = b.dataset.f;
      document.querySelectorAll(".grid[data-show]").forEach(function(g){ g.dataset.limit = ""; });
      try { history.replaceState(null, "", filter === "all" ? location.pathname : "#" + filter); } catch(e) {}
      apply();
    };
  });
  document.querySelectorAll(".more").forEach(function(m){
    m.onclick = function(){ var g = m.previousElementSibling; g.dataset.limit = (+g.dataset.limit || +g.dataset.show) + 12; apply(); };
  });
  // ---- My Teams picker
  var picker = document.getElementById("picker"), ptabs = document.getElementById("ptabs"), pteams = document.getElementById("pteams");
  var LG = [["eng","Premier League"],["esp","LaLiga"],["ita","Serie A"],["ger","Bundesliga"],["fra","Ligue 1"],["ksa","Saudi Pro League"],["eur","Europe"]];
  var cur = "eng";
  function drawPicker(){
    var mine = getMine();
    ptabs.innerHTML = LG.filter(function(l){ return TEAMS.some(function(t){ return t.l === l[0]; }); }).map(function(l){
      return '<button class="ptab' + (l[0] === cur ? ' on' : '') + '" data-l="' + l[0] + '">' + l[1] + '</button>'; }).join("");
    pteams.innerHTML = TEAMS.filter(function(t){ return t.l === cur; }).map(function(t){
      var on = mine.indexOf(t.name) >= 0;
      return '<button class="pteam' + (on ? ' on' : '') + '" data-n="' + t.name.replace(/"/g, "&quot;") + '">' + (on ? "⭐ " : "☆ ") + t.name + '</button>'; }).join("")
      || '<p class="meta">⏳</p>';
    document.getElementById("pcount").textContent = mine.length ? "⭐ " + mine.length : "";
    ptabs.querySelectorAll(".ptab").forEach(function(b){ b.onclick = function(){ cur = b.dataset.l; drawPicker(); }; });
    pteams.querySelectorAll(".pteam").forEach(function(b){ b.onclick = function(){
      var m = getMine(), i = m.indexOf(b.dataset.n); if (i >= 0) m.splice(i, 1); else m.push(b.dataset.n); setMine(m); drawPicker(); }; });
  }
  function openPicker(){ drawPicker(); picker.hidden = false; }
  document.getElementById("pdone").onclick = function(){
    picker.hidden = true; buildRe();
    var my = document.querySelector('.chip[data-f="my"]');
    if (getMine().length) { filter = ""; my.onclick(); } else { document.querySelector('.chip[data-f="all"]').onclick(); }
  };
  // ---- highlights play on this page
  var player = document.getElementById("player"), vwrap = document.getElementById("vwrap");
  function closeAll(){ picker.hidden = true; player.hidden = true; vwrap.innerHTML = ""; }
  document.querySelectorAll("[data-close]").forEach(function(b){ b.onclick = closeAll; });
  [picker, player].forEach(function(m){ m.addEventListener("click", function(ev){ if (ev.target === m) closeAll(); }); });
  document.addEventListener("keydown", function(ev){ if (ev.key === "Escape") closeAll(); });
  // YouTube player; if the owner blocks playing on other sites (or it fails), show a big "watch on YouTube" button
  var ytReady = null;
  function loadYT(){
    if (ytReady) return ytReady;
    ytReady = new Promise(function(res, rej){
      if (window.YT && window.YT.Player) return res();
      window.onYouTubeIframeAPIReady = res;
      var sc = document.createElement("script"); sc.src = "https://www.youtube.com/iframe_api"; sc.onerror = rej;
      document.head.appendChild(sc);
      setTimeout(rej, 5000);
    });
    return ytReady;
  }
  function fallback(url){
    vwrap.innerHTML = '<a class="ytbig" href="' + url + '" target="_blank" rel="noopener">▶ <span>' +
      (window.FA ? FA.t("yt_watch") : "Watch on YouTube") + '</span></a>';
  }
  function playVideo(id, url){
    vwrap.innerHTML = '<div id="ytp"></div>';
    loadYT().then(function(){
      new YT.Player("ytp", {videoId: id, host: "https://www.youtube-nocookie.com",
        playerVars: {autoplay: 1, rel: 0, playsinline: 1},
        events: {onError: function(){ fallback(url); }}});
    }).catch(function(){
      vwrap.innerHTML = '<iframe src="https://www.youtube-nocookie.com/embed/' + id + '?autoplay=1&rel=0" title="Highlights" allow="autoplay; encrypted-media; picture-in-picture; fullscreen" allowfullscreen></iframe>';
    });
  }
  document.querySelectorAll("a.vid").forEach(function(a){
    a.addEventListener("click", function(ev){
      var m = a.href.match(/[?&]v=([A-Za-z0-9_-]{6,})/); if (!m) return;
      ev.preventDefault();
      document.getElementById("ptitle").textContent = a.querySelector(".vt").textContent;
      document.getElementById("ytlink").href = a.href;
      player.hidden = false;
      playVideo(m[1], a.href);
    });
  });
  var h = location.hash.slice(1), pre = document.querySelector('.chip[data-f="' + h + '"]');
  if (pre) pre.click(); else apply();
})();
</script>
</body></html>"""


if __name__ == "__main__":
    n, v = news(), highlights()
    try:
        fx = fixtures()
    except Exception as ex:
        print("Fixtures failed:", ex)
        fx = []
    try:
        old = json.load(open("latest.json"))
    except Exception:
        old = {}
    if not v and old.get("videos"):  # YouTube hiccup: keep the last good highlights
        v = [dict(x, date=datetime.datetime.fromisoformat(x["date"])) for x in old["videos"]]
    if not n and old.get("news_all"):
        n = [dict(x, date=datetime.datetime.fromisoformat(x["date"])) for x in old["news_all"]]
    if not fx and old.get("fixtures"):
        fx = old["fixtures"]
    import tables
    try:
        tb = tables.fetch(get)
    except Exception as ex:
        print("Tables failed:", ex)
        tb = {"leagues": [], "teams": []}
    if not any(lg["rows"] for lg in tb["leagues"]) and old.get("tables"):
        tb = old["tables"]
    tables.render(tb)
    import matchpages
    archive = matchpages.merge_archive(old.get("match_archive", {}), fx)
    slugs, mpages = matchpages.render_all(archive, tb, v, n)
    print(f"{len(n)} news, {len(v)} videos, {len(fx)} fixtures, {len(tb['teams'])} teams, {len(mpages)} match pages, "
          f"{write_sitemap(mpages)} sitemap URLs")
    open("index.html", "w").write(render(n, v, fx, tb["teams"], slugs))
    json.dump({"news": [dict(x, date=x["date"].isoformat()) for x in n[:10]],
               "news_all": [dict(x, date=x["date"].isoformat()) for x in n],
               "videos": [dict(x, date=x["date"].isoformat()) for x in v],
               "fixtures": fx, "tables": tb, "match_archive": archive}, open("latest.json", "w"), indent=1)
