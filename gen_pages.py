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
<nav><a href="{up}index.html#highlights">Highlights</a><a href="{up}index.html#news">News</a><a href="{up}articles/index.html">Articles</a><a href="{up}quiz.html" style="color:#ffc83d">Quiz</a><a href="{up}about.html">About</a></nav></div></header>
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

# ---------- quiz.html ----------
import json
from quiz_src import QUIZ
from build import LEAGUES, flag
chips = '<button class="chip on" data-f="all">⚽ All</button>' + "".join(
    f'<button class="chip" data-f="{k}">{flag(k)} {html.escape(c)}</button>' for k, _f, c, _l, _kw in LEAGUES)
QCSS = """<style>
.chips{display:flex;gap:8px;flex-wrap:wrap;margin:14px 0 20px}
.chip{display:flex;align-items:center;gap:6px;background:#10251a;color:#eef6f0;border:1px solid #1f3d2b;border-radius:22px;padding:7px 13px;font:600 14px system-ui,sans-serif;cursor:pointer}
.chip.on{background:#2ee06f;color:#04210f;border-color:#2ee06f}.flag{width:20px;height:14px;border-radius:2px;object-fit:cover}
#box{background:#10251a;border:1px solid #1f3d2b;border-radius:16px;padding:22px}
.prog{display:flex;justify-content:space-between;color:#9cb8a6;font-size:14px}.pbar{height:6px;background:#1f3d2b;border-radius:3px;margin:8px 0 18px}
.pbar i{display:block;height:100%;background:#2ee06f;border-radius:3px;transition:width .3s}
#q{font-size:22px;font-weight:700;line-height:1.35;margin:0 0 16px}
.opt{display:block;width:100%;text-align:left;background:#07140c;color:#eef6f0;border:2px solid #1f3d2b;border-radius:12px;padding:13px 16px;margin:9px 0;font:600 17px system-ui,sans-serif;cursor:pointer}
.opt:hover:not(:disabled){border-color:#2ee06f}.opt.right{border-color:#2ee06f;background:#0f3a20}.opt.wrong{border-color:#ff5b5b;background:#3a1212}
.opt:disabled{cursor:default}
#fact{display:none;margin-top:14px;background:#0b2e18;border-left:4px solid #ffc83d;border-radius:8px;padding:12px 14px;font-size:16px}
.btn{display:inline-block;margin-top:16px;background:#2ee06f;color:#04210f;border:0;border-radius:22px;padding:11px 26px;font:800 16px system-ui,sans-serif;cursor:pointer;text-decoration:none}
.btn.alt{background:none;color:#2ee06f;border:1px solid #2ee06f;margin-left:8px}
.big{font-size:54px;font-weight:800;color:#ffc83d;margin:4px 0}
</style>"""
qbody = QCSS + f"""<h1>🧠 Football Quiz</h1>
<p class="meta">Pick a country or league, answer 10 questions, and learn a fun fact with every answer.</p>
<div class="chips">{chips}</div>
<div id="box"></div>
<p class="meta" style="margin-top:22px">Want to learn more? Read our <a href="articles/index.html">football articles</a> or watch the <a href="index.html#highlights">latest highlights</a>.</p>
<script>
var QUIZ = {json.dumps(QUIZ, ensure_ascii=False)};
var cat = "all", qs = [], i = 0, score = 0, box = document.getElementById("box");
function shuffle(a){{ a = a.slice(); for (var j = a.length - 1; j > 0; j--) {{ var k = Math.floor(Math.random() * (j + 1)), t = a[j]; a[j] = a[k]; a[k] = t; }} return a; }}
function esc(t){{ var d = document.createElement("div"); d.textContent = t; return d.innerHTML; }}
function start(){{
  qs = shuffle(QUIZ.filter(function(q){{ return cat === "all" || q.l === cat; }})).slice(0, 10);
  i = 0; score = 0; show();
}}
function show(){{
  var q = qs[i], opts = shuffle(q.o);
  box.innerHTML = '<div class="prog"><span>Question ' + (i + 1) + ' of ' + qs.length + '</span><span>Score: ' + score + '</span></div>'
    + '<div class="pbar"><i style="width:' + (i / qs.length * 100) + '%"></i></div><p id="q">' + esc(q.q) + '</p>'
    + opts.map(function(o){{ return '<button class="opt">' + esc(o) + '</button>'; }}).join("")
    + '<div id="fact"></div><button class="btn" id="next" style="display:none">' + (i + 1 < qs.length ? "Next question →" : "See my score") + '</button>';
  box.querySelectorAll(".opt").forEach(function(b){{
    b.onclick = function(){{
      var ok = b.textContent === q.o[0];
      if (ok) score++;
      box.querySelectorAll(".opt").forEach(function(x){{ x.disabled = true; if (x.textContent === q.o[0]) x.classList.add("right"); }});
      if (!ok) b.classList.add("wrong");
      var f = document.getElementById("fact");
      f.innerHTML = (ok ? "✅ <b>Correct!</b> " : "❌ <b>Not quite.</b> The answer is <b>" + esc(q.o[0]) + "</b>. ") + "<br>💡 " + esc(q.fact);
      f.style.display = "block"; document.getElementById("next").style.display = "inline-block";
    }};
  }});
  document.getElementById("next").onclick = function(){{ i++; i < qs.length ? show() : end(); }};
}}
function end(){{
  var p = score / qs.length, msg = p === 1 ? "Perfect! You are a football genius 🏆" : p >= .7 ? "Great job – you really know your football! ⚽" : p >= .4 ? "Not bad! Play again to learn more 💪" : "Keep watching and reading – you'll get there! 📚";
  var share = "https://www.facebook.com/sharer/sharer.php?u=" + encodeURIComponent("https://www.footballarena.net/quiz.html");
  box.innerHTML = '<p class="meta" style="margin:0">Your score</p><div class="big">' + score + ' / ' + qs.length + '</div><p style="font-size:19px;margin:0">' + msg + '</p>'
    + '<button class="btn" id="again">Play again</button><a class="btn alt" href="' + share + '" target="_blank" rel="noopener">Share on Facebook</a>';
  document.getElementById("again").onclick = start;
}}
document.querySelectorAll(".chip").forEach(function(b){{
  b.onclick = function(){{ document.querySelectorAll(".chip").forEach(function(x){{ x.classList.toggle("on", x === b); }}); cat = b.dataset.f; start(); }};
}});
start();
</script>"""
open("quiz.html", "w").write(page("Football Quiz – Test Your Knowledge by Country and League",
     "Play a free football quiz about the Premier League, LaLiga, Serie A, Bundesliga, Ligue 1, the Champions League and the World Cup. Learn a fun fact with every answer.", qbody, 0))
print("quiz built:", len(QUIZ), "questions")
