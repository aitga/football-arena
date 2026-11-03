"""Daily Facebook post for the Football Arena Page.
   python daily_post.py prepare  -> writes post.json + a preview in the GitHub run summary
   python daily_post.py publish  -> posts post.json to the Facebook Page"""
import json
import os
import sys

import requests

import build

SITE = "https://aitga.github.io/football-arena/"
GRAPH = "https://graph.facebook.com/v21.0"


def prepare():
    news, vids = build.news(), build.highlights()
    top = news[:4]
    lines = ["⚽ FOOTBALL ARENA – today's top football stories", ""]
    lines += [f"{i}. {n['title']} ({n['source']})" for i, n in enumerate(top, 1)]
    if vids:
        lines += ["", f"🎬 Today's must-watch highlight: {vids[0]['title']}"]
    lines += ["", f"👉 All the latest highlights & news, updated every hour: {SITE}", "",
              "What do you think? Share your view in the comments 👇", "",
              "#football #soccer #footballnews #highlights #PremierLeague #ChampionsLeague #LaLiga"]
    post = {"message": "\n".join(lines), "link": SITE}
    json.dump(post, open("post.json", "w"), ensure_ascii=False, indent=1)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a") as f:
            f.write("## 📝 Today's Football Arena post (preview)\n\n```\n" + post["message"] + "\n```\n\n"
                    "Link card: " + SITE + "\n\nIf it looks good: **Review deployments → approval → Approve and deploy**.\n")
    print(post["message"])


def publish():
    post = json.load(open("post.json"))
    page, token = os.environ["FB_PAGE_ID"].strip(), os.environ["FB_PAGE_TOKEN"].strip()
    r = requests.post(f"{GRAPH}/{page}/feed", data={"message": post["message"], "link": post["link"],
                                                     "access_token": token}, timeout=60)
    out = r.json()
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    result = f"✅ Posted: https://facebook.com/{out['id']}" if "id" in out else f"❌ Facebook said: {out}"
    if summary:
        open(summary, "a").write("## Posting result\n\n" + result + "\n")
    print(result)
    if "id" not in out:
        sys.exit(1)


if __name__ == "__main__":
    {"prepare": prepare, "publish": publish}[sys.argv[1]]()
