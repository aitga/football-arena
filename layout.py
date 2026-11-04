"""Shared page layout (header, menu, footer, language picker) for the static pages."""
import html

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
footer{border-top:1px solid var(--line);color:var(--mut);font-size:13px;padding:18px 16px;text-align:center}footer a{margin:0 6px}
.top nav{align-items:center;flex-wrap:wrap}.langpick{background:#10251a;color:#eef6f0;border:1px solid #1f3d2b;border-radius:10px;padding:6px 8px;font:600 14px system-ui,sans-serif}
.note{background:#10251a;border:1px solid #1f3d2b;border-radius:10px;padding:10px 14px;color:#ffc83d;font-size:15px}
[dir=rtl] .top nav{margin-left:0;margin-right:auto}
:lang(ar) body{font-family:"Segoe UI",Tahoma,"Noto Sans Arabic",system-ui,sans-serif}"""

def page(title, desc, body, depth, note=True, extra=""):
    up = "../" * depth
    e = html.escape
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)} – Football Arena</title><meta name="description" content="{e(desc)}">
<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}">
<link rel="icon" href="{up}logo.png"><style>{CSS}</style></head><body>
<header><div class="top"><a href="{up}index.html"><img src="{up}logo.png" alt="Football Arena"></a><b>FOOTBALL <span>ARENA</span></b>
<nav><a href="{up}index.html#highlights" data-i18n="nav_hl">Highlights</a><a href="{up}index.html#news" data-i18n="nav_news">News</a><a href="{up}articles/index.html" data-i18n="nav_art">Articles</a><a href="{up}live.html" style="color:#ff6b6b" data-i18n="nav_live">Live</a><a href="{up}tables.html" data-i18n="nav_tables">Tables</a><a href="{up}quiz.html" style="color:#ffc83d" data-i18n="nav_quiz">Quiz</a><a href="{up}about.html" data-i18n="nav_about">About</a>
<select class="langpick" aria-label="Language"></select></nav></div></header>
<main>{'<p class="note" data-i18n-note style="display:none"></p>' if note else ''}{body}</main>
<footer>© 2026 Football Arena ·<a href="{up}about.html" data-i18n="about">About</a>·<a href="{up}contact.html" data-i18n="contact">Contact</a>·<a href="{up}privacy.html" data-i18n="privacy">Privacy</a>·<a href="{FB}" target="_blank" rel="noopener" data-i18n="nav_fb">Facebook</a></footer>
<script src="{up}i18n.js"></script>{extra}
</body></html>"""

