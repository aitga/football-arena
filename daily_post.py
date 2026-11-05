"""Daily Facebook post for the Football Arena Page.
   python daily_post.py prepare  -> writes post.json + a preview in the GitHub run summary
   python daily_post.py publish  -> posts post.json to the Facebook Page"""
import json
import os
import sys

import requests

import build

SITE = "https://www.footballarena.net/"
GRAPH = "https://graph.facebook.com/v21.0"


def plan():
    try:
        return json.load(open("post_plan.json"))
    except Exception:
        return {"news_roundup": True, "highlights": 2}


def prepare():
    cfg = plan()
    news, vids = build.news(), build.highlights()
    if not vids:  # use the highlights the website already saved this hour
        try:
            vids = [dict(v, date=build.parse_date(v["date"])) for v in json.load(open("latest.json")).get("videos", [])]
        except Exception:
            vids = []
    posts = []
    if cfg.get("news_roundup", True) and news:
        lines = ["⚽ FOOTBALL ARENA – today's top football stories", "⚽ فوتبول أرينا – أبرز أخبار كرة القدم اليوم", ""]
        lines += [f"{i}. {n['title']} ({n['source']})" for i, n in enumerate(news[:4], 1)]
        lines += ["", f"👉 All the latest highlights & news, updated every hour: {SITE}",
                  f"👉 كل الملخصات والأخبار بالعربية والإنجليزية، تحديث كل ساعة: {SITE}", "",
                  "What do you think? Share your view in the comments 👇",
                  "ما رأيكم؟ شاركونا في التعليقات 👇", "",
                  "#football #soccer #footballnews #highlights #PremierLeague #ChampionsLeague #LaLiga #كرة_القدم"]
        posts.append({"message": "\n".join(lines), "link": SITE})
    # official highlight videos, shared as YouTube links (no re-uploading)
    for v in [v for v in vids if build.re.search(r"highlight|resumen|sintesi|goals?\b", v["title"], build.re.I)][:int(cfg.get("highlights", 2))]:
        posts.append({"message": f"🎬 HIGHLIGHTS | ملخص المباراة\n{v['title']}\n\nOfficial video from {v['channel']}.\n"
                                 f"More highlights every day 👉 {SITE}\nملخصات جديدة كل يوم 👉 {SITE}\n\n"
                                 "Who was the best player? Tell us below 👇\nمن هو أفضل لاعب؟ اكتبوا لنا 👇\n\n"
                                 "#football #highlights #goals #soccer #ملخص #أهداف",
                      "link": f"https://www.youtube.com/watch?v={v['id']}"})
    json.dump({"posts": posts}, open("post.json", "w"), ensure_ascii=False, indent=1)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a") as f:
            f.write(f"## 📝 Today's Football Arena posts (preview) – {len(posts)} posts\n\n")
            for i, p in enumerate(posts, 1):
                f.write(f"### Post {i}\n```\n{p['message']}\n```\nLink: {p['link']}\n\n")
            f.write("If they look good: **Review deployments → approval → Approve and deploy**.\n")
    for p in posts:
        print(p["message"], "\n->", p["link"], "\n")


def publish():
    data = json.load(open("post.json"))
    posts = data.get("posts") or [data]
    page, token = os.environ["FB_PAGE_ID"].strip(), os.environ["FB_PAGE_TOKEN"].strip()
    results, ok = [], True
    for p in posts:
        r = requests.post(f"{GRAPH}/{page}/feed", data={"message": p["message"], "link": p["link"],
                                                         "access_token": token}, timeout=60)
        out = r.json()
        if "id" in out:
            results.append(f"✅ Posted: https://facebook.com/{out['id']}")
        else:
            ok = False
            results.append(f"❌ Facebook said: {out}")
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        open(summary, "a").write("## Posting results\n\n" + "\n\n".join(results) + "\n")
    print("\n".join(results))
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    {"prepare": prepare, "publish": publish}[sys.argv[1]]()
