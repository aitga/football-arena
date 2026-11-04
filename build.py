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
                    if "#shorts" not in v["title"].lower():
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


def render(news_items, vids):
    e = html.escape
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%d %b %Y, %H:%M UTC")
    names = {k: f"{country} · {league}" for k, _c, country, league, _kw in LEAGUES}
    vcards = "\n".join(
        f'<a class="vid card" data-l="{lg}" href="https://www.youtube.com/watch?v={e(v["id"])}" target="_blank" rel="noopener">'
        f'<div class="thumb"><img src="https://i.ytimg.com/vi/{e(v["id"])}/hqdefault.jpg" alt="" loading="lazy"><span class="play">▶</span></div>'
        f'<div class="vt">{e(nice_title(v["title"]))}</div>'
        f'<div class="meta">{flag(lg)} {e(names[lg].split(" · ")[1])} · {ago(v["date"])}</div></a>'
        for v in vids for lg in [CHANNEL_LEAGUE.get(v["channel"], "wld")]) \
        or '<p class="empty">Highlights are loading – check back soon.</p>'
    ncards = "\n".join(
        f'<a class="news card" data-l="{lg}" href="{e(n["link"])}" target="_blank" rel="noopener">'
        + (f'<img class="nimg" src="{e(n["image"])}" alt="" loading="lazy">' if n["image"] else "")
        + f'<div><div class="nt">{e(n["title"])}</div><p>{e(n["summary"])}</p>'
          f'<div class="meta">{flag(lg)} {e(n["source"])} · {ago(n["date"])}</div></div></a>'
        for n in news_items for lg in [league_of_news(n)]) \
        or '<p class="empty">News is loading – check back soon.</p>'
    chips = '<button class="chip on" data-f="all">⚽ All</button>' + "".join(
        f'<button class="chip" data-f="{k}">{flag(k)} {e(country)}<small>{e(league)}</small></button>'
        for k, _c, country, league, _kw in LEAGUES)
    try:
        from articles_src import ARTICLES
        arts = sorted(ARTICLES, key=lambda a: a["date"], reverse=True)[:3]
    except Exception:
        arts = []
    acards = "\n".join(
        f'<a class="news card" href="articles/{e(a["slug"])}.html"><div><div class="nt">{e(a["title"])}</div>'
        f'<p>{e(a["summary"])}</p><div class="meta">📝 {e(a["tag"])} · Football Arena</div></div></a>' for a in arts)
    return (TEMPLATE.replace("{{CHIPS}}", chips).replace("{{ARTICLES}}", acards).replace("{{VIDEOS}}", vcards)
            .replace("{{NEWS}}", ncards).replace("{{UPDATED}}", now))


TEMPLATE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Football Arena – Football Highlights & News by League</title>
<meta name="description" content="Latest football highlights and news sorted by country and league: Premier League, LaLiga, Serie A, Bundesliga, Ligue 1, Champions League and the World Cup. Plus football quizzes. Updated every hour.">
<meta property="og:title" content="Football Arena – Highlights, News & Quizzes">
<meta property="og:description" content="The latest football highlights and news by league, updated every hour. Test yourself with our football quiz.">
<meta property="og:image" content="https://www.footballarena.net/logo.png">
<link rel="canonical" href="https://www.footballarena.net/">
<link rel="icon" href="logo.png">
<style>
:root{--bg:#07140c;--card:#10251a;--line:#1f3d2b;--txt:#eef6f0;--mut:#9cb8a6;--acc:#2ee06f;--gold:#ffc83d}
*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:120px}
body{margin:0;background:var(--bg);color:var(--txt);font:16px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
a{color:inherit;text-decoration:none}
header{background:linear-gradient(135deg,#0b3d1f,#07140c 70%);padding:18px 16px 14px}
.wrap{max-width:1150px;margin:0 auto}
.brand{display:flex;align-items:center;gap:12px}.brand img{width:52px;height:52px;border-radius:12px}
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
</style></head><body>
<header><div class="wrap brand"><img src="logo.png" alt="Football Arena" width="52" height="52"><div><h1>FOOTBALL <span>ARENA</span></h1>
<div class="tag">Highlights & news from the world's biggest leagues · updated every hour</div></div></div></header>
<div class="bar"><div class="wrap">
<nav><a href="#highlights">🎬 Highlights</a><a href="#news">📰 News</a><a href="articles/index.html">📝 Articles</a><a class="quiz" href="quiz.html">🧠 Quiz</a><a href="https://www.facebook.com/1429286323597310" target="_blank" rel="noopener">👍 Facebook</a></nav>
<div class="chips">{{CHIPS}}</div>
</div></div>
<main class="wrap">
<section id="highlights"><h2>Latest Highlights <span class="count"></span></h2><div class="grid" data-show="8">
{{VIDEOS}}
</div><button class="more">Show more highlights</button></section>
<section><div class="quizban"><span style="font-size:38px">🧠</span><div><b>How well do you know football?</b>
<p>Play our quiz by country and league – learn a fun fact with every answer.</p></div><a href="quiz.html">Play the quiz</a></div></section>
<section id="news"><h2>Latest Football News <span class="count"></span></h2><div class="grid" data-show="9">
{{NEWS}}
</div><button class="more">Show more news</button></section>
<section id="articles"><h2>Football Articles</h2><div class="grid">
{{ARTICLES}}
</div><p><a href="articles/index.html" style="color:var(--acc)">See all articles →</a></p></section>
</main>
<footer>Updated {{UPDATED}} · Videos play on the official YouTube channels of each league. News headlines link to the original
publishers (BBC Sport, The Guardian, ESPN). All rights belong to their owners.<br>
<a href="about.html">About</a> · <a href="contact.html">Contact</a> · <a href="privacy.html">Privacy</a></footer>
<script>
(function(){
  var filter = "all";
  function apply(){
    document.querySelectorAll(".grid[data-show]").forEach(function(g){
      var lim = +g.dataset.limit || +g.dataset.show, total = 0;
      g.querySelectorAll(".card").forEach(function(c){
        var ok = filter === "all" || c.dataset.l === filter;
        if (!ok) { c.classList.add("hide"); return; }
        total++;
        c.classList.toggle("hide", total > lim);
      });
      var shown = g.querySelectorAll(".card:not(.hide)").length;
      var sec = g.closest("section");
      sec.querySelector(".more").style.display = shown < total ? "" : "none";
      sec.querySelector(".count").textContent = total ? "(" + total + ")" : "";
      var em = g.querySelector(".none");
      if (!total && !em){ em = document.createElement("p"); em.className = "empty none"; em.textContent = "Nothing for this league right now – check back soon."; g.appendChild(em); }
      if (em) em.style.display = total ? "none" : "";
    });
  }
  document.querySelectorAll(".chip").forEach(function(b){
    b.onclick = function(){
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
  var h = location.hash.slice(1), pre = document.querySelector('.chip[data-f="' + h + '"]');
  if (pre) pre.click(); else apply();
})();
</script>
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
