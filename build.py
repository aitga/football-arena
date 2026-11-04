"""Builds the Football Arena website (index.html) from live football news feeds
and the leagues' official YouTube highlight channels. Runs every hour on GitHub."""
import datetime
import email.utils
import html
import json
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
]
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


def highlights():
    vids = []
    for name, handle in HIGHLIGHT_CHANNELS:
        try:
            cid = handle if handle.startswith("UC") else channel_id(handle)
            root = ET.fromstring(get(f"https://www.youtube.com/feeds/videos.xml?channel_id={cid}"))
        except Exception as e:
            print("Channel failed:", name, e)
            continue
        for en in root.findall("atom:entry", NS)[:8]:
            title = en.findtext("atom:title", "", NS)
            if "#shorts" in title.lower():
                continue
            vids.append({"channel": name, "id": en.findtext("yt:videoId", "", NS), "title": clean(title, 120),
                         "date": parse_date(en.findtext("atom:published", "", NS))})
    hl = [v for v in vids if re.search(r"highlight|resumen|sintesi|goals?\b|résumé", v["title"], re.I)]
    rest = [v for v in vids if v not in hl]
    return sorted(hl, key=lambda v: v["date"], reverse=True)[:18] + sorted(rest, key=lambda v: v["date"], reverse=True)[:6]


def ago(d):
    s = (datetime.datetime.now(datetime.timezone.utc) - d).total_seconds()
    if s < 3600:
        return f"{max(1, int(s // 60))} min ago"
    if s < 86400:
        return f"{int(s // 3600)} h ago"
    return f"{int(s // 86400)} d ago"


def render(news_items, vids):
    e = html.escape
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%d %b %Y, %H:%M UTC")
    vcards = "\n".join(
        f'<a class="vid" href="https://www.youtube.com/watch?v={e(v["id"])}" target="_blank" rel="noopener">'
        f'<div class="thumb" style="background-image:url(https://i.ytimg.com/vi/{e(v["id"])}/hqdefault.jpg)"><span class="play">▶</span></div>'
        f'<div class="vt">{e(v["title"])}</div><div class="meta">{e(v["channel"])} · {ago(v["date"])}</div></a>'
        for v in vids) or '<p class="empty">Highlights are loading – check back soon.</p>'
    ncards = "\n".join(
        f'<a class="news" href="{e(n["link"])}" target="_blank" rel="noopener">'
        + (f'<img src="{e(n["image"])}" alt="" loading="lazy">' if n["image"] else "")
        + f'<div><div class="nt">{e(n["title"])}</div><p>{e(n["summary"])}</p>'
          f'<div class="meta">{e(n["source"])} · {ago(n["date"])}</div></div></a>'
        for n in news_items) or '<p class="empty">News is loading – check back soon.</p>'
    return TEMPLATE.replace("{{VIDEOS}}", vcards).replace("{{NEWS}}", ncards).replace("{{UPDATED}}", now)


TEMPLATE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Football Arena – Football Highlights & News</title>
<meta name="description" content="Latest football highlights and football news from the Premier League, LaLiga, Champions League, Serie A, Bundesliga and more. Updated every hour.">
<meta property="og:title" content="Football Arena – Highlights & News">
<meta property="og:description" content="The latest football highlights and news, updated every hour.">
<link rel="icon" href="logo.png">
<style>
:root{--bg:#07140c;--card:#10251a;--line:#1f3d2b;--txt:#eef6f0;--mut:#9cb8a6;--acc:#2ee06f;--gold:#ffc83d}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--txt);font:16px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
a{color:inherit;text-decoration:none}
header{background:linear-gradient(135deg,#0b3d1f,#07140c 70%);border-bottom:1px solid var(--line);padding:22px 16px 0}
.wrap{max-width:1150px;margin:0 auto}
.brand{display:flex;align-items:center;gap:12px}.brand img{width:52px;height:52px;border-radius:12px}
h1{margin:0;font-size:28px;letter-spacing:.5px}h1 span{color:var(--acc)}
.tag{color:var(--mut);margin:4px 0 14px;font-size:14px}
nav{display:flex;gap:8px;overflow-x:auto}nav a{white-space:nowrap;padding:10px 16px;border-radius:10px 10px 0 0;color:var(--mut);font-weight:600}
nav a.on,nav a:hover{background:var(--bg);color:var(--txt)}
main{padding:20px 16px 40px}h2{font-size:20px;margin:6px 0 14px;display:flex;align-items:center;gap:8px}
h2:before{content:"";width:6px;height:22px;background:var(--acc);border-radius:3px}
.grid{display:grid;gap:14px;grid-template-columns:repeat(auto-fill,minmax(260px,1fr))}
.vid,.news{background:var(--card);border:1px solid var(--line);border-radius:14px;overflow:hidden;transition:transform .15s,border-color .15s}
.vid:hover,.news:hover{transform:translateY(-2px);border-color:var(--acc)}
.thumb{aspect-ratio:16/9;background:#000 center/cover;display:grid;place-items:center}
.play{width:54px;height:54px;border-radius:50%;background:rgba(0,0,0,.6);display:grid;place-items:center;font-size:22px;color:#fff}
.vt,.nt{font-weight:700;padding:10px 12px 2px;line-height:1.3}.meta{color:var(--mut);font-size:13px;padding:2px 12px 12px}
.news{display:flex;flex-direction:column}.news img{width:100%;aspect-ratio:16/9;object-fit:cover;background:#000}
.news p{color:var(--mut);font-size:14px;margin:4px 12px 4px}
section{margin-bottom:34px}.empty{color:var(--mut)}
footer{border-top:1px solid var(--line);color:var(--mut);font-size:13px;padding:18px 16px;text-align:center}
footer a{color:var(--acc)}
</style></head><body>
<header><div class="wrap">
<div class="brand"><img src="logo.png" alt="Football Arena"><div><h1>FOOTBALL <span>ARENA</span></h1>
<div class="tag">Highlights & news from the world's biggest leagues · updated every hour</div></div></div>
<nav><a class="on" href="#highlights">🎬 Highlights</a><a href="#news">📰 Latest News</a><a href="https://www.facebook.com/1429286323597310" target="_blank" rel="noopener" id="fb">👍 Facebook</a></nav>
</div></header>
<main class="wrap">
<section id="highlights"><h2>Latest Highlights</h2><div class="grid">
{{VIDEOS}}
</div></section>
<section id="news"><h2>Latest Football News</h2><div class="grid">
{{NEWS}}
</div></section>
</main>
<footer>Updated {{UPDATED}} · Videos play on the official YouTube channels of each league. News headlines link to the original
publishers (BBC Sport, The Guardian, ESPN). All rights belong to their owners.<br>
<a href="privacy.html">Privacy</a></footer>
</body></html>"""


if __name__ == "__main__":
    n, v = news(), highlights()
    try:
        old = json.load(open("latest.json"))
    except Exception:
        old = {}
    if not v and old.get("videos"):  # YouTube hiccup: keep the last good highlights
        v = [dict(x, date=datetime.datetime.fromisoformat(x["date"])) for x in old["videos"]]
    if not n and old.get("news_all"):
        n = [dict(x, date=datetime.datetime.fromisoformat(x["date"])) for x in old["news_all"]]
    print(f"{len(n)} news, {len(v)} videos")
    open("index.html", "w").write(render(n, v))
    json.dump({"news": [dict(x, date=x["date"].isoformat()) for x in n[:10]],
               "news_all": [dict(x, date=x["date"].isoformat()) for x in n],
               "videos": [dict(x, date=x["date"].isoformat()) for x in v]}, open("latest.json", "w"), indent=1)
