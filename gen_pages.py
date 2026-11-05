"""Builds the static pages: articles/*.html, articles/index.html, about.html, contact.html.
Run: python gen_pages.py  (after adding a new article to articles_src.py)"""
import html, os
from articles_src import ARTICLES

from layout import FB, CSS, page

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
    open(f"articles/{a['slug']}.html", "w").write(page(a["title"], a["summary"], body, 1, path=f"articles/{a['slug']}.html", jsonld={
        "@context": "https://schema.org", "@type": "Article", "headline": a["title"], "description": a["summary"],
        "datePublished": a["date"], "author": {"@type": "Organization", "name": "Football Arena"},
        "publisher": {"@type": "Organization", "name": "Football Arena", "logo": {"@type": "ImageObject", "url": "https://www.footballarena.net/logo.png"}},
        "mainEntityOfPage": f"https://www.footballarena.net/articles/{a['slug']}.html", "inLanguage": "en"}))
cards = "".join(f'<a class="card" href="{a["slug"]}.html"><span class="pill">{a["tag"]}</span><h3>{html.escape(a["title"])}</h3>'
                f'<p>{html.escape(a["summary"])}</p><div class="meta">{nice(a["date"])}</div></a>' for a in arts)
open("articles/index.html", "w").write(page("Football Articles", "Guides to the rules, tactics and history of football, written by Football Arena.",
     f'<h1>Football Articles</h1><p class="meta">Easy guides to the rules, tactics and history of the beautiful game.</p><div class="list">{cards}</div>', 1, path="articles/index.html"))
open("about.html", "w").write(page("About Football Arena", "About Football Arena: who we are and what we publish.", f"""
<h1>About Football Arena</h1>
<p>Football Arena is an independent football website for fans everywhere. We bring together the latest official highlights and football news from the world's biggest leagues — the Premier League, LaLiga, the Champions League, Serie A, the Bundesliga and more — in one simple place, updated every hour.</p>
<h2>What you'll find here</h2>
<ul><li><strong>Highlights:</strong> the newest official highlight videos, played on each league's own YouTube channel.</li>
<li><strong>News:</strong> headlines from trusted publishers such as BBC Sport, The Guardian and ESPN, always linking to the original story.</li>
<li><strong>Articles:</strong> our own easy-to-read guides about the rules, tactics and history of football.</li></ul>
<h2>Our approach</h2>
<p>We respect the work of clubs, leagues and journalists. We never re-upload other people's videos or copy their articles: we link to the official source so the creators get the credit. Our own articles are written by the Football Arena team.</p>
<p>Follow us on <a href="{FB}" target="_blank" rel="noopener">Facebook</a> for daily match recaps and stories.</p>""", 0, path="about.html"))
open("contact.html", "w").write(page("Contact Football Arena", "How to contact Football Arena.", f"""
<h1>Contact us</h1>
<p>We'd love to hear from you — whether you have a question, a correction, a story idea or a business enquiry.</p>
<p>The fastest way to reach us is to send a message to our <a href="{FB}" target="_blank" rel="noopener">Football Arena Facebook Page</a>. We usually reply within 48 hours.</p>
<p>If you believe any content on this site should be credited differently or removed, please tell us and we will act quickly.</p>""", 0, path="contact.html"))
print("pages built:", len(arts))

# ---------- quiz.html ----------
import json
from quiz_src import QUIZ
from build import LEAGUES, flag
chips = '<button class="chip on" data-f="all">⚽ <span data-i18n="all">All</span></button>' + "".join(
    f'<button class="chip" data-f="{k}">{flag(k)} <span data-i18n="c_{k}">{html.escape(c)}</span></button>' for k, _f, c, _l, _kw in LEAGUES)
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
.btn.alt{background:none;color:#2ee06f;border:1px solid #2ee06f;margin-inline-start:8px}
.big{font-size:54px;font-weight:800;color:#ffc83d;margin:4px 0}
</style>"""
qbody = QCSS + f"""<h1 data-i18n="qz_title">🧠 Football Quiz</h1>
<p class="meta" data-i18n="qz_intro">Pick a country or league, answer 10 questions, and learn a fun fact with every answer.</p>
<div class="chips">{chips}</div>
<div id="box"></div>
<p class="meta" style="margin-top:22px" data-i18n-html="qz_more">Want to learn more? Read our <a href="articles/index.html">football articles</a> or watch the <a href="index.html#highlights">latest highlights</a>.</p>"""
qscript = f"""<script src="quiz_i18n.js"></script>
<script>
var QUIZ = {json.dumps(QUIZ, ensure_ascii=False)};
var cat = "all", qs = [], i = 0, score = 0, box = document.getElementById("box");
function shuffle(a){{ a = a.slice(); for (var j = a.length - 1; j > 0; j--) {{ var k = Math.floor(Math.random() * (j + 1)), t = a[j]; a[j] = a[k]; a[k] = t; }} return a; }}
function esc(t){{ var d = document.createElement("div"); d.textContent = t; return d.innerHTML; }}
function t(k, v){{ return window.FA ? FA.t(k, v) : k; }}
function tq(q){{ var L = window.FA ? FA.lang : "en", x = (window.FA_QUIZ[L] || [])[QUIZ.indexOf(q)]; return x || [q.q, q.fact]; }}
function to(o){{ var L = window.FA ? FA.lang : "en"; return (window.FA_OPT[L] || {{}})[o] || o; }}
function start(){{
  qs = shuffle(QUIZ.filter(function(q){{ return cat === "all" || q.l === cat; }})).slice(0, 10);
  i = 0; score = 0; show();
}}
function show(){{
  var q = qs[i], tr = tq(q), opts = shuffle(q.o.map(function(o, k){{ return [o, k]; }}));
  box.innerHTML = '<div class="prog"><span>' + esc(t("qz_q", {{i: i + 1, n: qs.length}})) + '</span><span>' + esc(t("qz_score")) + ': ' + score + '</span></div>'
    + '<div class="pbar"><i style="width:' + (i / qs.length * 100) + '%"></i></div><p id="q">' + esc(tr[0]) + '</p>'
    + opts.map(function(o){{ return '<button class="opt" data-k="' + o[1] + '">' + esc(to(o[0])) + '</button>'; }}).join("")
    + '<div id="fact"></div><button class="btn" id="next" style="display:none">' + esc(i + 1 < qs.length ? t("qz_next") : t("qz_see")) + '</button>';
  box.querySelectorAll(".opt").forEach(function(b){{
    b.onclick = function(){{
      var ok = b.dataset.k === "0";
      if (ok) score++;
      box.querySelectorAll(".opt").forEach(function(x){{ x.disabled = true; if (x.dataset.k === "0") x.classList.add("right"); }});
      if (!ok) b.classList.add("wrong");
      var f = document.getElementById("fact");
      f.innerHTML = (ok ? "✅ <b>" + esc(t("qz_ok")) + "</b> " : "❌ " + esc(t("qz_no")) + " <b>" + esc(to(q.o[0])) + "</b>. ") + "<br>💡 " + esc(tr[1]);
      f.style.display = "block"; document.getElementById("next").style.display = "inline-block";
    }};
  }});
  document.getElementById("next").onclick = function(){{ i++; i < qs.length ? show() : end(); }};
}}
function end(){{
  var p = score / qs.length, msg = t(p === 1 ? "qz_m1" : p >= .7 ? "qz_m2" : p >= .4 ? "qz_m3" : "qz_m4");
  var share = "https://www.facebook.com/sharer/sharer.php?u=" + encodeURIComponent("https://www.footballarena.net/quiz.html");
  box.innerHTML = '<p class="meta" style="margin:0">' + esc(t("qz_your")) + '</p><div class="big">' + score + ' / ' + qs.length + '</div><p style="font-size:19px;margin:0">' + msg + '</p>'
    + '<button class="btn" id="again">' + esc(t("qz_again")) + '</button><a class="btn alt" href="' + share + '" target="_blank" rel="noopener">' + esc(t("qz_share")) + '</a>';
  document.getElementById("again").onclick = start;
}}
document.querySelectorAll(".chip").forEach(function(b){{
  b.onclick = function(){{ document.querySelectorAll(".chip").forEach(function(x){{ x.classList.toggle("on", x === b); }}); cat = b.dataset.f; start(); }};
}});
document.addEventListener("fa:lang", start);
start();
</script>"""
open("quiz.html", "w").write(page("Football Quiz – Test Your Knowledge by Country and League",
     "Play a free football quiz about the Premier League, LaLiga, Serie A, Bundesliga, Ligue 1, the Champions League and the World Cup. Learn a fun fact with every answer.", qbody, 0, note=False, extra=qscript, path="quiz.html"))
print("quiz built:", len(QUIZ), "questions")

# ---------- live.html (live match tracker) ----------
LCSS = """<style>
main{max-width:980px}
#list{display:flex;flex-wrap:wrap;gap:8px;margin:16px 0 20px}
.lv-item{display:flex;align-items:center;gap:7px;background:#10251a;color:#eef6f0;border:1px solid #1f3d2b;border-radius:12px;padding:8px 12px;font:600 14px system-ui,sans-serif;cursor:pointer}
.lv-item.on{border-color:#2ee06f;background:#123a22}.lv-item b{font-weight:700}
.flag{width:20px;height:14px;border-radius:2px;object-fit:cover}
.lv-live{color:#ff5b5b;font-weight:800;font-size:12px}.lv-ft{color:#9cb8a6;font-size:12px;font-weight:700}.lv-ko{color:#ffc83d;font-size:12px;font-weight:700}
.lv-live.big,.lv-ft.big,.lv-ko.big{font-size:15px}.lv-live.big{animation:blink 1.4s infinite}@keyframes blink{50%{opacity:.45}}
.lv-board{display:grid;grid-template-columns:1fr auto 1fr;align-items:center;gap:12px;background:#10251a;border:1px solid #1f3d2b;border-radius:16px 16px 0 0;padding:14px 16px}
.lv-board .tm{font-weight:800;font-size:19px;line-height:1.2}.lv-board .tm:last-child{text-align:end}
.lv-board .sc{font-size:40px;font-weight:900;color:#ffc83d;white-space:nowrap}
.lv-st{background:#0b1f13;border:1px solid #1f3d2b;border-top:0;padding:6px 16px;text-align:center}.lv-st small{color:#9cb8a6;margin-inline-start:8px}
.lv-wrap{position:relative;margin:12px 0}.lv-pitch{width:100%;display:block;border-radius:14px;border:3px solid #1f3d2b}
.pl{animation:jig 3s ease-in-out infinite}.p1{animation-duration:3.7s}.p2{animation-duration:2.6s}
@keyframes jig{0%,100%{transform:translate(0,0)}33%{transform:translate(1.5px,-1.2px)}66%{transform:translate(-1.2px,1.4px)}}
.lv-goal{position:absolute;inset:0;display:grid;place-content:center;text-align:center;background:rgba(0,0,0,.55);border-radius:14px;opacity:0;pointer-events:none;transition:opacity .4s}
.lv-goal.show{opacity:1}.lv-goal b{font-size:64px;color:#ffc83d;text-shadow:0 4px 0 #6a3a00;animation:pop .6s}.lv-goal span{font-size:18px;font-weight:700;padding:0 20px}
@keyframes pop{0%{transform:scale(.3)}70%{transform:scale(1.15)}100%{transform:scale(1)}}
.lv-grid{display:grid;grid-template-columns:1fr 1fr;gap:18px}@media(max-width:700px){.lv-grid{grid-template-columns:1fr}}
.lv-grid h3{margin:10px 0}.st{display:grid;grid-template-columns:50px 1fr 50px;align-items:center;font-size:14px;margin:8px 0}
.st b{text-align:center;color:#9cb8a6;font-weight:600}.st span:last-of-type{text-align:end}
.sbar{grid-column:1/4;display:flex;height:7px;border-radius:4px;overflow:hidden;background:#1f3d2b;margin-top:3px}
.tl{list-style:none;margin:0;padding:0;max-height:440px;overflow:auto}
.ev{display:grid;grid-template-columns:28px 58px 1fr;gap:6px;padding:8px 6px;border-bottom:1px solid #1f3d2b;font-size:15px;line-height:1.35}
.ev.goal{background:#123a22;border-radius:8px;font-weight:700}.ev .mn{color:#ffc83d;font-weight:700}.lv-src{margin-top:18px;font-size:13px}
</style>"""
lbody = LCSS + """<h1 data-i18n="lv_title">🔴 Live Match Tracker</h1>
<p class="meta" data-i18n="lv_intro">Follow the big matches live as a cartoon – score, minute, goals, cards and stats update every 30 seconds.</p>
<div id="list"><p class="meta">⏳</p></div><div id="match"></div>"""
open("live.html", "w").write(page("Live Football Match Tracker – Scores, Goals & Stats",
     "Follow today's Premier League, LaLiga, Serie A, Bundesliga, Ligue 1 and Champions League matches live: score, minute, goals, cards and stats, updated every 30 seconds.",
     lbody, 0, note=False, extra='<script src="live.js"></script>', path="live.html"))
print("live page built")
