"""Original cartoon match recaps for the Football Arena Page.
Uses only match FACTS (teams, score, scorers, minutes) from a public live-scores feed and
draws everything itself: no broadcaster footage, no club crests.

   python recap.py make      -> out/recap_*.mp4 + out/recaps.json + preview in the run summary
   python recap.py publish   -> uploads the recaps to the Facebook Page as Reels"""
import asyncio
import datetime
import json
import math
import os
import random
import subprocess
import sys

import requests
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1080, 1920, 24
OUT = "out"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
LEAGUES = [("eng.1", "Premier League"), ("uefa.champions", "Champions League"), ("esp.1", "LaLiga"),
           ("ita.1", "Serie A"), ("ger.1", "Bundesliga"), ("fra.1", "Ligue 1")]
VOICE = os.environ.get("RECAP_VOICE", "en-GB-RyanNeural")
PITCH = (60, 330, 1020, 1690)  # x0, y0, x1, y1 (home attacks the top goal)
GREEN, DARK = (46, 224, 111), (7, 20, 12)
_fonts = {}


def font(size):
    if size not in _fonts:
        _fonts[size] = ImageFont.truetype(FONT, size)
    return _fonts[size]


# ---------------------------------------------------------------- match data
def fetch_matches(day):
    matches = []
    for code, name in LEAGUES:
        try:
            j = requests.get(f"https://site.api.espn.com/apis/site/v2/sports/soccer/{code}/scoreboard",
                             params={"dates": day.strftime("%Y%m%d")}, timeout=30).json()
        except Exception as e:
            print("Scores feed failed for", name, e)
            continue
        for ev in j.get("events", []):
            c = ev["competitions"][0]
            if c["status"]["type"].get("name") != "STATUS_FULL_TIME":
                continue
            teams = {t["homeAway"]: t for t in c["competitors"]}
            ids = {teams["home"]["team"]["id"]: "home", teams["away"]["team"]["id"]: "away"}
            goals = []
            for d in c.get("details", []):
                if not d.get("scoringPlay"):
                    continue
                side = ids.get((d.get("team") or {}).get("id"))
                who = [a.get("displayName") for a in d.get("athletesInvolved", [])] or ["Unknown"]
                if side:
                    goals.append({"side": side, "minute": (d.get("clock") or {}).get("displayValue", ""),
                                  "scorer": who[0], "pen": bool(d.get("penaltyKick")), "og": bool(d.get("ownGoal"))})
            matches.append({"league": name, "goals": goals,
                            "home": {"name": teams["home"]["team"]["shortDisplayName"],
                                     "color": teams["home"]["team"].get("color") or "1f6feb",
                                     "alt": teams["home"]["team"].get("alternateColor") or "ffffff",
                                     "score": int(teams["home"]["score"])},
                            "away": {"name": teams["away"]["team"]["shortDisplayName"],
                                     "color": teams["away"]["team"].get("color") or "e5534b",
                                     "alt": teams["away"]["team"].get("alternateColor") or "ffffff",
                                     "score": int(teams["away"]["score"])}})
    return matches


def pick_matches(matches, n):
    rank = {name: i for i, (_, name) in enumerate(LEAGUES)}
    good = [m for m in matches if m["goals"] and len(m["goals"]) == m["home"]["score"] + m["away"]["score"]]
    good.sort(key=lambda m: (-min(len(m["goals"]), 5), rank.get(m["league"], 9)))
    return good[:n]


# ---------------------------------------------------------------- colours
def hexrgb(h):
    h = (h or "888888").lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) if len(h) == 6 else (136, 136, 136)


def team_colors(m):
    hc, ac = hexrgb(m["home"]["color"]), hexrgb(m["away"]["color"])
    if sum((a - b) ** 2 for a, b in zip(hc, ac)) < 9000:  # too similar: away wears its 2nd kit
        ac = hexrgb(m["away"]["alt"])
        if sum((a - b) ** 2 for a, b in zip(hc, ac)) < 9000:
            ac = (255, 255, 255) if sum(hc) < 380 else (25, 25, 35)
    return hc, ac


def text_on(c):
    return (20, 20, 20) if sum(c) > 450 else (255, 255, 255)


# ---------------------------------------------------------------- voice
def speak(text, path):
    try:
        import edge_tts
        asyncio.run(edge_tts.Communicate(text, VOICE, rate="+8%", pitch="+2Hz").save(path))
        if os.path.getsize(path) > 1000:
            return
    except Exception as e:
        print("Voice failed, trying gTTS:", e)
    try:
        from gtts import gTTS
        gTTS(text, lang="en", tld="co.uk").save(path)
        return
    except Exception as e:
        print("Voice failed, silence:", e)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono", "-t", "3", path])


def dur(path):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                                capture_output=True, text=True).stdout.strip() or 3)


def spoken_minute(m):
    base = m.replace("'", "").split("+")[0]
    return f"{base} minutes" if base.isdigit() else "late on"


# ---------------------------------------------------------------- drawing
def pitch_bg():
    im = Image.new("RGB", (W, H), DARK)
    d = ImageDraw.Draw(im)
    x0, y0, x1, y1 = PITCH
    for i in range(10):
        ys = y0 + (y1 - y0) * i / 10
        d.rectangle([x0, ys, x1, ys + (y1 - y0) / 10], fill=(52, 150, 70) if i % 2 else (60, 166, 78))
    line, lw = (235, 255, 240), 6
    d.rectangle(PITCH, outline=line, width=lw)
    cy = (y0 + y1) / 2
    d.line([(x0, cy), (x1, cy)], fill=line, width=lw)
    d.ellipse([W / 2 - 130, cy - 130, W / 2 + 130, cy + 130], outline=line, width=lw)
    for top in (True, False):
        gy = y0 if top else y1
        s = 1 if top else -1
        d.rectangle(sorted_box(W / 2 - 260, gy, W / 2 + 260, gy + s * 210), outline=line, width=lw)
        d.rectangle(sorted_box(W / 2 - 120, gy, W / 2 + 120, gy + s * 80), outline=line, width=lw)
        d.rectangle(sorted_box(W / 2 - 90, gy, W / 2 + 90, gy - s * 45), fill=(240, 240, 240), outline=(200, 200, 200), width=4)
        for k in range(1, 9):  # net
            xx = W / 2 - 90 + k * 20
            d.line([(xx, gy), (xx, gy - s * 45)], fill=(170, 170, 170), width=2)
    return im


def sorted_box(a, b, c, d):
    return [min(a, c), min(b, d), max(a, c), max(b, d)]


def player(d, x, y, color, num, r=34, happy=False):
    d.ellipse([x - r + 5, y - r + 9, x + r + 5, y + r + 9], fill=(30, 90, 40))  # shadow
    d.ellipse([x - r, y - r, x + r, y + r], fill=color, outline=(255, 255, 255), width=5)
    d.text((x, y + 8), str(num), font=font(26), fill=text_on(color), anchor="mm")
    for ex in (-11, 11):  # cartoon eyes
        d.ellipse([x + ex - 7, y - 20, x + ex + 7, y - 6], fill="white")
        d.ellipse([x + ex - 3, y - 15, x + ex + 3, y - 9], fill="black")
    if happy:
        d.arc([x - 14, y - 2, x + 14, y + 16], 0, 180, fill=text_on(color), width=4)


def ball(d, x, y, r=16):
    d.ellipse([x - r + 3, y - r + 6, x + r + 3, y + r + 6], fill=(30, 90, 40))
    d.ellipse([x - r, y - r, x + r, y + r], fill="white", outline=(20, 20, 20), width=3)
    d.regular_polygon((x, y, r * 0.45), 5, fill=(20, 20, 20))


def outlined(d, xy, t, size, fill, anchor="mm", sw=None):
    d.text(xy, t, font=font(size), fill=fill, anchor=anchor, stroke_width=sw or max(3, size // 12), stroke_fill=DARK)


def scoreboard(d, m, hs, as_, clock, colors):
    hc, ac = colors
    d.rounded_rectangle([40, 40, W - 40, 290], 30, fill=(12, 30, 18), outline=GREEN, width=5)
    outlined(d, (W / 2, 82), f"FOOTBALL ARENA · {m['league'].upper()}", 32, GREEN, sw=2)
    for side, c, x in (("home", hc, 225), ("away", ac, W - 225)):
        name = m[side]["name"]
        size = 42 if len(name) <= 10 else 32 if len(name) <= 14 else 26
        d.rounded_rectangle([x - 165, 120, x + 165, 196], 18, fill=c)
        d.text((x, 158), name.upper(), font=font(size), fill=text_on(c), anchor="mm")
    outlined(d, (W / 2, 170), f"{hs}-{as_}", 84, (255, 255, 255))
    d.text((W / 2, 258), clock, font=font(36), fill=(200, 230, 210), anchor="mm")


def formation(side):
    """5 cartoon players per team, positions as fractions of the pitch (home attacks up)."""
    base = [(0.5, 0.92), (0.25, 0.76), (0.75, 0.76), (0.35, 0.6), (0.65, 0.6)]
    if side == "away":
        base = [(x, 1 - y) for x, y in base]
    return base


def pos(fx, fy):
    x0, y0, x1, y1 = PITCH
    return x0 + (x1 - x0) * fx, y0 + (y1 - y0) * fy


# ---------------------------------------------------------------- video
def make_recap(m, idx):
    os.makedirs(OUT, exist_ok=True)
    work = os.path.join(OUT, f"w{idx}")
    os.makedirs(work, exist_ok=True)
    colors = team_colors(m)
    home, away = m["home"]["name"], m["away"]["name"]
    rnd = random.Random(f"{home}{away}")

    # commentary script
    segs = [("intro", f"Welcome to Football Arena! It's {home} against {away} in the {m['league']}. Here's how it happened!")]
    hs = as_ = 0
    for g in m["goals"]:
        if g["side"] == "home":
            hs += 1
        else:
            as_ += 1
        team = home if g["side"] == "home" else away
        lead = (hs > as_) if g["side"] == "home" else (as_ > hs)
        state = f"{team} lead!" if lead and abs(hs - as_) == 1 else (f"{team} pull level!" if hs == as_ else f"{team} extend the lead!" if lead else f"{team} pull one back!")
        how = "steps up from the penalty spot... and" if g["pen"] else "turns it into his own net... oh no..." if g["og"] else "breaks forward... shoots... and"
        segs.append(("goal", f"{spoken_minute(g['minute'])}... {g['scorer']} {how} it's a GOAL! {state} {hs}, {as_}.", g, hs, as_))
    h_end, a_end = m["home"]["score"], m["away"]["score"]
    result = f"{home} win it!" if h_end > a_end else f"{away} take the win!" if a_end > h_end else "the points are shared!"
    segs.append(("full", f"Full time! {home} {h_end}, {away} {a_end}. {result} Who was your man of the match? Tell us in the comments!"))

    # voice + timeline
    timeline, t = [], 0.0
    for i, s in enumerate(segs):
        path = os.path.join(work, f"v{i}.mp3")
        speak(s[1], path)
        length = max(dur(path) + 0.7, 5.0 if s[0] == "goal" else 3.5)
        timeline.append((t, length, s, path))
        t += length
    total = t + 0.5

    # draw frames straight into ffmpeg
    bg = pitch_bg()
    silent = os.path.join(work, "video.mp4")
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
                           "-pix_fmt", "yuv420p", silent], stdin=subprocess.PIPE)
    confetti = [(rnd.uniform(0, W), rnd.uniform(-400, 0), rnd.uniform(6, 14), rnd.choice(
        [GREEN, (255, 200, 60), (255, 255, 255), colors[0], colors[1]])) for _ in range(90)]
    score = [0, 0]
    for f in range(int(total * FPS)):
        now = f / FPS
        seg = next((x for x in timeline if x[0] <= now < x[0] + x[1]), timeline[-1])
        st, ln, s = seg[0], seg[1], seg[2]
        p = (now - st) / ln
        im = bg.copy()
        d = ImageDraw.Draw(im)
        clock = "KICK-OFF" if s[0] == "intro" else "FULL TIME" if s[0] == "full" else s[2]["minute"]
        if s[0] == "goal" and p > 0.55:
            score = [s[3], s[4]]
        if s[0] == "full":
            score = [h_end, a_end]
        # players jog around their spots
        attack = s[2]["side"] if s[0] == "goal" else None
        if attack and s[2]["og"]:
            attack = "away" if attack == "home" else "home"  # the defending side "scores" the own goal
        bx, by = W / 2, (PITCH[1] + PITCH[3]) / 2
        for si, side in enumerate(("home", "away")):
            for k, (fx, fy) in enumerate(formation(side)):
                shift = 0
                if attack:  # whole teams push toward the goal being attacked
                    shift = (-0.18 if attack == "home" else 0.18) * min(1, p * 1.6)
                x, y = pos(fx + 0.03 * math.sin(now * 2 + k + si), fy + shift + 0.015 * math.cos(now * 2.4 + k))
                happy = s[0] == "goal" and p > 0.55 and side == s[2]["side"]
                player(d, x, y, colors[si], [1, 4, 5, 8, 10][k], happy=happy)
        if attack:
            # the scorer dribbles in and shoots into the net
            top = attack == "home"
            gx, gy = W / 2 + rnd.uniform(-50, 50), PITCH[1] - 22 if top else PITCH[3] + 22
            sx, sy = pos(0.5 + 0.25 * math.sin(len(s[1])), 0.55 if top else 0.45)
            ex, ey = W / 2 + 120 * math.sin(len(s[1]) * 3), (PITCH[1] + 260) if top else (PITCH[3] - 260)
            q = min(1, p / 0.4)
            px, py = sx + (ex - sx) * q, sy + (ey - sy) * q
            player(d, px, py, colors[0 if s[2]["side"] == "home" else 1] if not s[2]["og"] else colors[1 if s[2]["side"] == "home" else 0], 9,
                   r=40, happy=p > 0.55)
            if p < 0.4:
                bx, by = px + 30, py + (-36 if top else 36)
            else:
                k2 = min(1, (p - 0.4) / 0.15)
                bx, by = px + (gx - px) * k2, (py + (-36 if top else 36)) + (gy - py) * k2
        ball(d, bx, by)
        scoreboard(d, m, score[0], score[1], clock, colors)
        # overlays
        if s[0] == "intro":
            a = min(1, p * 3)
            outlined(d, (W / 2, 1000), "MATCH RECAP", int(80 + 30 * a), (255, 255, 255))
            outlined(d, (W / 2, 1110), f"{home}  vs  {away}", 54, (255, 220, 80))
        elif s[0] == "goal" and p > 0.55:
            bounce = 1 + 0.25 * max(0, math.sin((p - 0.55) * 18)) * (1 - (p - 0.55))
            outlined(d, (W / 2, 900), "GOAL!", int(170 * bounce), (255, 220, 60))
            g = s[2]
            tag = " (pen)" if g["pen"] else " (OG)" if g["og"] else ""
            d.rounded_rectangle([110, 1010, W - 110, 1110], 26, fill=(12, 30, 18), outline=GREEN, width=4)
            d.text((W / 2, 1060), f"{g['scorer']}{tag}  {g['minute']}", font=font(46 if len(g['scorer']) < 18 else 36), fill="white", anchor="mm")
            for cx, cy, r, c in confetti:
                yy = (cy + (now - st) * 700) % (H + 400) - 200
                d.ellipse([cx - r, yy - r, cx + r, yy + r], fill=c)
        elif s[0] == "full":
            d.rounded_rectangle([90, 760, W - 90, 1240], 40, fill=(12, 30, 18), outline=GREEN, width=6)
            outlined(d, (W / 2, 830), "FULL TIME", 84, GREEN)
            outlined(d, (W / 2, 960), f"{home} {h_end} - {a_end} {away}", 60 if len(home + away) < 20 else 46, (255, 255, 255))
            d.text((W / 2, 1080), "Who was man of the match?", font=font(44), fill=(255, 220, 80), anchor="mm")
            d.text((W / 2, 1160), "Comment below!", font=font(44), fill=(255, 255, 255), anchor="mm")
        d.rounded_rectangle([0, H - 120, W, H], 0, fill=(12, 30, 18))
        d.text((W / 2, H - 60), "Follow FOOTBALL ARENA for daily recaps", font=font(40), fill=GREEN, anchor="mm")
        ff.stdin.write(im.tobytes())
    ff.stdin.close()
    ff.wait()

    # sound: commentary + crowd + whistles + goal roars
    inputs, filters, n = [], [], 0
    for (st, ln, s, path) in timeline:
        inputs += ["-i", path]
        filters.append(f"[{n}:a]adelay={int(st * 1000 + 150)}:all=1,volume=1.6[s{n}]")
        n += 1
    mix = "".join(f"[s{i}]" for i in range(n))
    crowd = f"anoisesrc=d={total:.2f}:c=pink:a=0.05,lowpass=f=900[crowd]"
    whistle = f"aevalsrc='0.4*sin(2*PI*2900*t)*lt(mod(t,0.35),0.25)':d=0.9:s=44100,asplit=2[w1][w2a];[w2a]adelay={int((total - 3.5) * 1000)}:all=1[w2]"
    roars = []
    for i, (st, ln, s, _) in enumerate(timeline):
        if s[0] == "goal":
            roars.append(f"anoisesrc=d=2.5:c=pink:a=0.35,lowpass=f=1500,afade=t=out:st=0.8:d=1.7,adelay={int((st + ln * 0.55) * 1000)}:all=1[r{i}]")
    graph = ";".join(filters + [crowd, whistle] + roars)
    rlabels = "".join(f"[r{i}]" for i, (_, _, s, _) in enumerate(timeline) if s[0] == "goal")
    graph += f";{mix}[crowd][w1][w2]{rlabels}amix=inputs={n + 3 + len(roars)}:duration=longest:normalize=0[a]"
    video = os.path.join(OUT, f"recap_{idx}.mp4")
    subprocess.run(["ffmpeg", "-y", "-v", "error", *inputs, "-i", silent, "-filter_complex", graph,
                    "-map", f"{n}:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-t", f"{total:.2f}",
                    "-movflags", "+faststart", video], check=True)
    subprocess.run(["rm", "-rf", work])
    return video


def caption(m):
    h, a = m["home"], m["away"]
    scorers = ", ".join(f"{g['scorer']} {g['minute']}" for g in m["goals"][:6])
    return (f"⚽ {h['name']} {h['score']}-{a['score']} {a['name']} | {m['league']} cartoon recap\n\n"
            f"Goals: {scorers}\n\nWho was your man of the match? 👇\n"
            "Follow Football Arena for daily recaps!\n\n#football #soccer #matchrecap #footballarena")


def make():
    day = datetime.datetime.now(datetime.timezone.utc).date() - datetime.timedelta(days=1)
    cfg = {}
    try:
        cfg = json.load(open("post_plan.json"))
    except Exception:
        pass
    picked = pick_matches(fetch_matches(day), int(cfg.get("recaps", 2)))
    os.makedirs(OUT, exist_ok=True)
    made = []
    for i, m in enumerate(picked):
        print("Recap:", m["home"]["name"], m["away"]["name"], m["league"])
        made.append({"video": make_recap(m, i), "caption": caption(m)})
    json.dump(made, open(os.path.join(OUT, "recaps.json"), "w"), ensure_ascii=False, indent=1)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a") as f:
            f.write(f"## 🎬 Cartoon match recaps – {len(made)} videos\n\n")
            for r in made:
                f.write("```\n" + r["caption"] + "\n```\n\n")
            if not made:
                f.write("No finished big-league matches with goals yesterday.\n")


def publish():
    page, token = os.environ["FB_PAGE_ID"].strip(), os.environ["FB_PAGE_TOKEN"].strip()
    g = "https://graph.facebook.com/v21.0"
    results = []
    for r in json.load(open(os.path.join(OUT, "recaps.json"))):
        try:
            start = requests.post(f"{g}/{page}/video_reels", data={"upload_phase": "start", "access_token": token}).json()
            vid = start["video_id"]
            size = os.path.getsize(r["video"])
            with open(r["video"], "rb") as fh:
                up = requests.post(f"https://rupload.facebook.com/video-upload/v21.0/{vid}", data=fh, headers={
                    "Authorization": f"OAuth {token}", "offset": "0", "file_size": str(size)}, timeout=600).json()
            if not up.get("success"):
                raise RuntimeError(f"upload: {up}")
            fin = requests.post(f"{g}/{page}/video_reels", data={"upload_phase": "finish", "video_id": vid,
                                                                  "video_state": "PUBLISHED", "description": r["caption"],
                                                                  "access_token": token}).json()
            if not fin.get("success"):
                raise RuntimeError(f"finish: {fin}")
            results.append(f"✅ Reel posted (video id {vid})")
        except Exception as e:  # fall back to a normal Page video
            try:
                with open(r["video"], "rb") as fh:
                    out = requests.post(f"https://graph-video.facebook.com/v21.0/{page}/videos",
                                        data={"description": r["caption"], "access_token": token},
                                        files={"source": ("recap.mp4", fh, "video/mp4")}, timeout=600).json()
                results.append(f"✅ Video posted: https://facebook.com/{out['id']}" if "id" in out else f"❌ {e} / {out}")
            except Exception as e2:
                results.append(f"❌ {e} / {e2}")
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        open(summary, "a").write("## Recap posting results\n\n" + "\n\n".join(results) + "\n")
    print("\n".join(results))
    if any(x.startswith("❌") for x in results):
        sys.exit(1)


if __name__ == "__main__":
    {"make": make, "publish": publish}[sys.argv[1]]()
