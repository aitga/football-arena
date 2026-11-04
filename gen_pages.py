"""Builds the static pages: articles/*.html, articles/index.html, about.html, contact.html.
Run: python gen_pages.py  (after adding a new article to articles_src.py)"""
import html, os
from articles_src import ARTICLES

FB = "https://www.facebook.com/1429286323597310"
CSS = """:root{--bg:#07140c;--card:#10251a;--line:#1f3d2b;--txt:#eef6f0;--mut:#9cb8a6;--acc:#2ee06f}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--txt);font:17px/1.7 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
a{color:var(--acc)}header{background:linear-gradient(135deg,#0b3d1f,#07140c 70%);border-bottom:1px solid var(--line);padding:16px}
.top{max-width:1150px;margin:0 auto;display:flex;align-items:center;gap:12px;flex-wrap:wrap}.top img{width:40px;height:40px;border-radius:10px}
.top b{font-size:20px;color:var(--txt)}.top b span{color:var(--acc)}.top nav{margin-left:auto;display:flex;gap:14px;font-weight:600}
.top nav a{color:var(--mut);text-decoration:none}.top nav a:hover{color:var(--txt)}
main{max-width:760px;margin:0 auto;padding:26px 16px 50px}h1{line-height:1.25;font-size:32px;margin:8px 0}
h2{font-size:22px;margin-top:30px}.meta{color:var(--mut);font-size:14px}.pill{display:inline-block;background:var(--card);border:1px solid var(--line);border-radius:20px;padding:2px 12px;font-size:13px;color:var(--acc)}
.list a.card{display:block;background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px 18px;margin:14px 0;text-decoration:none;color:var(--txt)}
.list a.card:hover{border-color:var(--acc)}.card h3{margin:6px 0 4px;font-size:20px}.card p{margin:0;color:var(--mut);font-size:15px}
footer{border-top:1px solid var(--line);color:var(--mut);font-size:13px;padding:18px 16px;text-align:center}footer a{margin:0 6px}"""

def page(title, desc, body, depth):
    up = "../" * depth
    e = html.escape
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)} – Football Arena</title><meta name="description" content="{e(desc)}">
<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}">
<link rel="icon" href="{up}logo.png"><style>{CSS}</style></head><body>
<header><div class="top"><a href="{up}index.html"><img src="{up}logo.png" alt="Football Arena"></a><b>FOOTBALL <span>ARENA</span></b>
<nav><a href="{up}index.html#highlights">Highlights</a><a href="{up}index.html#news">News</a><a href="{up}articles/index.html">Articles</a><a href="{up}about.html">About</a></nav></div></header>
<main>{body}</main>
<footer>© 2026 Football Arena ·<a href="{up}about.html">About</a>·<a href="{up}contact.html">Contact</a>·<a href="{up}privacy.html">Privacy</a>·<a href="{FB}" target="_blank" rel="noopener">Facebook</a></footer>
</body></html>"""

def nice(d):
    import datetime
    return datetime.date.fromisoformat(d).strftime("%d %B %Y")

os.makedirs("articles", exist_ok=True)
arts = sorted(ARTICLES, key=lambda a: a["date"], reverse=True)
for a in arts:
    others = "".join(f'<li><a href="{o["slug"]}.html">{html.escape(o["title"])}</a></li>' for o in arts if o is not a)[:2000]
    body = (f'<span class="pill">{a["tag"]}</span><h1>{html.escape(a["title"])}</h1>'
            f'<div class="meta">By Football Arena · {nice(a["date"])}</div>{a["body"]}'
            f'<h2>More articles</h2><ul>{others}</ul><p><a href="index.html">← All articles</a></p>')
    open(f"articles/{a['slug']}.html", "w").write(page(a["title"], a["summary"], body, 1))
cards = "".join(f'<a class="card" href="{a["slug"]}.html"><span class="pill">{a["tag"]}</span><h3>{html.escape(a["title"])}</h3>'
                f'<p>{html.escape(a["summary"])}</p><div class="meta">{nice(a["date"])}</div></a>' for a in arts)
open("articles/index.html", "w").write(page("Football Articles", "Guides to the rules, tactics and history of football, written by Football Arena.",
     f'<h1>Football Articles</h1><p class="meta">Easy guides to the rules, tactics and history of the beautiful game.</p><div class="list">{cards}</div>', 1))
open("about.html", "w").write(page("About Football Arena", "About Football Arena: who we are and what we publish.", f"""
<h1>About Football Arena</h1>
<p>Football Arena is an independent football website for fans everywhere. We bring together the latest official highlights and football news from the world's biggest leagues — the Premier League, LaLiga, the Champions League, Serie A, the Bundesliga and more — in one simple place, updated every hour.</p>
<h2>What you'll find here</h2>
<ul><li><strong>Highlights:</strong> the newest official highlight videos, played on each league's own YouTube channel.</li>
<li><strong>News:</strong> headlines from trusted publishers such as BBC Sport, The Guardian and ESPN, always linking to the original story.</li>
<li><strong>Articles:</strong> our own easy-to-read guides about the rules, tactics and history of football.</li></ul>
<h2>Our approach</h2>
<p>We respect the work of clubs, leagues and journalists. We never re-upload other people's videos or copy their articles: we link to the official source so the creators get the credit. Our own articles are written by the Football Arena team.</p>
<p>Follow us on <a href="{FB}" target="_blank" rel="noopener">Facebook</a> for daily match recaps and stories.</p>""", 0))
open("contact.html", "w").write(page("Contact Football Arena", "How to contact Football Arena.", f"""
<h1>Contact us</h1>
<p>We'd love to hear from you — whether you have a question, a correction, a story idea or a business enquiry.</p>
<p>The fastest way to reach us is to send a message to our <a href="{FB}" target="_blank" rel="noopener">Football Arena Facebook Page</a>. We usually reply within 48 hours.</p>
<p>If you believe any content on this site should be credited differently or removed, please tell us and we will act quickly.</p>""", 0))
print("pages built:", len(arts))
