/* Football Arena – live match tracker (cartoon pitch + live events). Data: ESPN public scoreboard. */
(function () {
var API = "https://site.api.espn.com/apis/site/v2/sports/soccer/";
var LEAGUES = [["eng.1", "eng"], ["esp.1", "esp"], ["ita.1", "ita"], ["ger.1", "ger"], ["fra.1", "fra"],
               ["uefa.champions", "eur"], ["uefa.europa", "eur"]];
var FLAG = {eng: "gb-eng", esp: "es", ita: "it", ger: "de", fra: "fr", eur: "eu"};
var list = document.getElementById("list"), box = document.getElementById("match");
var games = [], sel = null, last = {}, timer = null, ball = {x: 50, y: 32, tx: 50, ty: 32};

function t(k, v) { return window.FA ? FA.t(k, v) : k; }
function esc(s) { var d = document.createElement("div"); d.textContent = s == null ? "" : s; return d.innerHTML; }
function ymd(d) { return d.toISOString().slice(0, 10).replace(/-/g, ""); }
function flag(l) { return '<img class="flag" src="https://flagcdn.com/w40/' + FLAG[l] + '.png" alt="" width="20" height="14">'; }
function loc() { return window.FA && FA.lang === "ar" ? "ar-MA" : (window.FA ? FA.lang : "en"); }
function kick(d) { var x = new Date(d); return x.toLocaleTimeString(loc(), {hour: "2-digit", minute: "2-digit"}); }
function col(c, fb) { return c && /^[0-9a-f]{6}$/i.test(c) && c.toLowerCase() !== "ffffff" ? "#" + c : fb; }

async function getJSON(u) { var r = await fetch(u, {cache: "no-store"}); if (!r.ok) throw new Error(r.status); return r.json(); }

async function loadList() {
  var now = new Date(), days = [ymd(new Date(now - 864e5)), ymd(now), ymd(new Date(+now + 864e5))], found = [];
  await Promise.all(LEAGUES.map(async function (L) {
    for (var i = 0; i < days.length; i++) {
      try {
        var d = await getJSON(API + L[0] + "/scoreboard?dates=" + days[i]);
        (d.events || []).forEach(function (ev) {
          var c = ev.competitions[0], tm = {};
          c.competitors.forEach(function (x) { tm[x.homeAway] = x; });
          var start = new Date(ev.date), st = ev.status.type.state;
          if (st === "post" && now - start > 6 * 36e5) return;      // finished long ago
          if (st === "pre" && start - now > 30 * 36e5) return;       // more than ~a day away
          found.push({code: L[0], l: L[1], id: ev.id, date: ev.date, state: st, clock: ev.status.displayClock,
                      detail: ev.status.type.shortDetail, comp: (d.leagues[0] || {}).name || "",
                      home: tm.home, away: tm.away});
        });
      } catch (e) {}
    }
  }));
  var seen = {};
  games = found.filter(function (g) { return seen[g.id] ? false : (seen[g.id] = 1); }).sort(function (a, b) {
    var o = {"in": 0, pre: 1, post: 2};
    return o[a.state] - o[b.state] || new Date(a.date) - new Date(b.date);
  });
  drawList();
}

function status(g) {
  if (g.state === "in") return '<span class="lv-live">● ' + esc(t("live")) + " " + esc(g.clock || g.detail) + "</span>";
  if (g.state === "post") return '<span class="lv-ft">' + esc(t("lv_ft")) + "</span>";
  return '<span class="lv-ko">' + esc(kick(g.date)) + "</span>";
}

function drawList() {
  if (!games.length) {
    list.innerHTML = '<p class="meta">' + esc(t("lv_none")) + ' <a href="index.html#matches">' + esc(t("lv_sched")) + "</a></p>";
    box.innerHTML = "";
    return;
  }
  list.innerHTML = games.map(function (g) {
    var on = sel && sel.id === g.id ? " on" : "";
    return '<button class="lv-item' + on + '" data-id="' + g.id + '">' + flag(g.l) + " <b>" +
      esc(g.home.team.shortDisplayName) + " " + (g.state === "pre" ? "–" : esc(g.home.score) + " – " + esc(g.away.score)) + " " +
      esc(g.away.team.shortDisplayName) + "</b> " + status(g) + "</button>";
  }).join("");
  list.querySelectorAll(".lv-item").forEach(function (b) {
    b.onclick = function () { pick(b.dataset.id, true); };
  });
  if (!sel) {
    var h = location.hash.slice(1).split("/")[1];
    pick(h && games.some(function (g) { return g.id === h; }) ? h : games[0].id);
  }
}

function pick(id, scroll) {
  sel = games.filter(function (g) { return g.id === id; })[0];
  if (!sel) return;
  try { history.replaceState(null, "", "#" + sel.code + "/" + sel.id); } catch (e) {}
  last = {};
  drawList();
  loadMatch();
  if (scroll) box.scrollIntoView({behavior: "smooth", block: "start"});
}

function stat(team, name) {
  var s = (team.statistics || []).filter(function (z) { return z.name === name; })[0];
  return s ? parseFloat(s.displayValue) || 0 : 0;
}

// ---- live commentator: reads goals, cards and big moments out loud in English or Arabic
var cm = "off", said = {}, saidMatch = null;
try { cm = localStorage.getItem("fa_cmlive") || "off"; } catch (e) {}
var CM_LANG = {en: "en-GB", ar: "ar-SA"};
var cmStyle = document.createElement("style");
cmStyle.textContent = ".lv-cm{display:flex;flex-wrap:wrap;align-items:center;gap:8px;margin:12px 0 0;font-size:14px;font-weight:700}" +
  ".lv-cm button{background:#10251a;color:#eef6f0;border:1px solid #1f3d2b;border-radius:20px;padding:6px 14px;font:700 14px system-ui,sans-serif;cursor:pointer}" +
  ".lv-cm button.on{background:#ffc83d;border-color:#ffc83d;color:#2a1d00}.lv-cm small{flex-basis:100%;color:#9cb8a6;font-weight:500}";
document.head.appendChild(cmStyle);
function voiceFor(l) {
  if (!window.speechSynthesis) return null;
  var vs = speechSynthesis.getVoices() || [];
  return vs.filter(function (v) { return v.lang && v.lang.toLowerCase().indexOf(l) === 0; })[0] || null;
}
function say(text) {
  if (cm === "off" || !window.speechSynthesis || !text) return;
  var u = new SpeechSynthesisUtterance(text);
  u.lang = CM_LANG[cm]; var v = voiceFor(cm); if (v) u.voice = v;
  u.rate = 1.05; u.pitch = 1.05;
  speechSynthesis.speak(u);
}
function cmBar() {
  var el = document.getElementById("lvcm");
  if (!el) return;
  var b = function (k, label) { return '<button data-cm="' + k + '"' + (cm === k ? ' class="on"' : "") + ">" + label + "</button>"; };
  var note = cm !== "off" && window.speechSynthesis && !voiceFor(cm) && (speechSynthesis.getVoices() || []).length ? t("cm_novoice") : t("cm_note");
  el.innerHTML = "<span>" + esc(t("cm_title")) + "</span>" + b("off", esc(t("cm_off"))) + b("en", "🇬🇧 English") + b("ar", "🇲🇦 العربية") +
    "<small>" + esc(note) + "</small>";
  el.querySelectorAll("button").forEach(function (x) {
    x.onclick = function () {
      cm = x.dataset.cm;
      try { localStorage.setItem("fa_cmlive", cm); } catch (e) {}
      if (window.speechSynthesis) speechSynthesis.cancel();
      saidMatch = null;  // say hello + the latest moment in the new language
      cmBar(); loadMatch();
    };
  });
}
if (window.speechSynthesis) speechSynthesis.onvoiceschanged = cmBar;
function commentate(g, s, h, a, state, teams) {
  if (cm === "off") { saidMatch = g.id; return; }
  var tr = function (k, v) { return window.FA && FA.tl ? FA.tl(cm, k, v) : k; };
  var lines = ((s && s.keyEvents) || []).map(function (k) { return eventLine(k, teams, tr); }).filter(Boolean);
  var key = function (e) { return e[1] + "|" + e[2]; };
  var fresh = saidMatch !== g.id;
  if (fresh) {  // just picked this match: greet, then only the latest moment
    said = {};
    lines.forEach(function (e) { said[key(e)] = 1; });
    var score = state === "pre" ? tr("cm_pre") : tr("cm_score", {h: h.score, a: a.score});
    say(tr("cm_hello", {home: h.team.shortDisplayName || h.team.displayName, away: a.team.shortDisplayName || a.team.displayName, score: score}));
    var lastEv = lines[lines.length - 1];
    if (lastEv) say((lastEv[1] ? tr("cm_min", {min: lastEv[1].replace(/'/g, "")}) + " " : "") + lastEv[2]);
    saidMatch = g.id;
    return;
  }
  lines.forEach(function (e) {
    if (said[key(e)]) return;
    said[key(e)] = 1;
    say((e[1] ? tr("cm_min", {min: e[1].replace(/'/g, "")}) + " " : "") + e[2] + (e[3] === "goal" ? " " + tr("cm_score", {h: h.score, a: a.score}) : ""));
  });
}

function eventLine(k, teams, tr) {
  var t = tr || function (k, v) { return window.FA ? FA.t(k, v) : k; };
  var ty = (k.type && (k.type.type || k.type.text) || "").toLowerCase(), c = (k.clock && k.clock.displayValue) || "";
  var who = (k.participants || []).map(function (p) { return p.athlete && p.athlete.displayName; }).filter(Boolean);
  var team = k.team ? (teams[k.team.id] || {}).name || k.team.displayName : "";
  var v = {team: team, p: who[0] || "", a: who[1] || "", min: c};
  if (k.scoringPlay || /goal|penalty---scored/.test(ty)) {
    var key = /own/.test(ty) ? "ev_og" : /penalty/.test(ty) ? "ev_pen" : who[1] ? "ev_goal_a" : "ev_goal";
    return ["⚽", c, t(key, v), "goal"];
  }
  if (/red/.test(ty)) return ["🟥", c, t("ev_red", v), "card"];
  if (/yellow/.test(ty)) return ["🟨", c, t("ev_yellow", v), "card"];
  if (/substitution/.test(ty)) return ["🔄", c, t("ev_sub", {team: team, p: who.join(" ↔ ")}), "sub"];
  if (/kickoff/.test(ty)) return ["⏱️", c, t("ev_ko"), "info"];
  if (/halftime/.test(ty)) return ["⏸️", c, t("ev_ht"), "info"];
  if (/start-2nd/.test(ty)) return ["▶️", c, t("ev_2h"), "info"];
  if (/end-regular|full/.test(ty)) return ["🏁", c, t("ev_ft"), "info"];
  return null;
}

function pitch(h, a) {
  var hc = col(h.team.color, "#e23b3b"), ac = col(a.team.color, "#2f6fe0");
  if (hc === ac) ac = col(a.team.alternateColor, "#f5d020");
  var dots = "", posH = [[8, 32], [22, 14], [22, 50], [36, 24], [36, 40], [46, 32]];
  posH.forEach(function (p, i) {
    dots += '<circle class="pl p' + (i % 3) + '" cx="' + p[0] + '" cy="' + p[1] + '" r="2.4" fill="' + hc + '" stroke="#fff" stroke-width=".6"/>';
    dots += '<circle class="pl p' + ((i + 1) % 3) + '" cx="' + (100 - p[0]) + '" cy="' + (64 - p[1]) + '" r="2.4" fill="' + ac + '" stroke="#fff" stroke-width=".6"/>';
  });
  var stripes = "";
  for (var i = 0; i < 10; i++) stripes += '<rect x="' + i * 10 + '" y="0" width="10" height="64" fill="' + (i % 2 ? "#2f9b46" : "#35a94e") + '"/>';
  return '<svg class="lv-pitch" viewBox="0 0 100 64" role="img" aria-label="pitch">' + stripes +
    '<g fill="none" stroke="#fff" stroke-width=".5" opacity=".9"><rect x="1" y="1" width="98" height="62"/><line x1="50" y1="1" x2="50" y2="63"/>' +
    '<circle cx="50" cy="32" r="8"/><rect x="1" y="17" width="14" height="30"/><rect x="85" y="17" width="14" height="30"/>' +
    '<rect x="1" y="25" width="5" height="14"/><rect x="94" y="25" width="5" height="14"/></g>' +
    '<rect x="-1.5" y="28" width="2.5" height="8" fill="#fff"/><rect x="99" y="28" width="2.5" height="8" fill="#fff"/>' +
    dots + '<circle id="ball" cx="50" cy="32" r="1.6" fill="#fff" stroke="#222" stroke-width=".4"/></svg>';
}

async function loadMatch() {
  if (!sel) return;
  var g = sel, s;
  try { s = await getJSON(API + g.code + "/summary?event=" + g.id); } catch (e) { s = null; }
  if (!sel || sel.id !== g.id) return;
  var comp = s && s.header && s.header.competitions && s.header.competitions[0];
  var cs = comp ? comp.competitors : [g.home, g.away], tm = {};
  cs.forEach(function (x) { tm[x.homeAway] = x; });
  var h = tm.home || g.home, a = tm.away || g.away;
  var st = comp && comp.status ? comp.status : null, state = st ? st.type.state : g.state;
  var clock = st ? (st.displayClock || st.type.shortDetail) : g.clock;
  g.state = state; g.clock = clock; g.home.score = h.score; g.away.score = a.score;
  var teams = {}; teams[h.id] = {name: h.team.shortDisplayName || h.team.displayName}; teams[a.id] = {name: a.team.shortDisplayName || a.team.displayName};
  var bx = (s && s.boxscore && s.boxscore.teams) || [], bh = {}, ba = {};
  bx.forEach(function (x) { if (x.team.id === h.id) bh = x; else ba = x; });
  var evs = ((s && s.keyEvents) || []).map(function (k) { return eventLine(k, teams); }).filter(Boolean);

  var badge = state === "in" ? '<span class="lv-live big">● ' + esc(t("live")) + " " + esc(clock) + "</span>" :
    state === "post" ? '<span class="lv-ft big">' + esc(t("lv_ft")) + "</span>" :
    '<span class="lv-ko big">' + esc(t("lv_kick", {time: kick(g.date)})) + "</span>";
  var rows = [["possessionPct", "st_pos", "%"], ["totalShots", "st_shots", ""], ["shotsOnTarget", "st_target", ""],
              ["wonCorners", "st_corners", ""], ["foulsCommitted", "st_fouls", ""], ["yellowCards", "st_yellow", ""]];
  var stats = state === "pre" ? "" : rows.map(function (r) {
    var x = stat(bh, r[0]), y = stat(ba, r[0]), tot = x + y || 1;
    return '<div class="st"><span>' + x + r[2] + '</span><b>' + esc(t(r[1])) + '</b><span>' + y + r[2] + '</span>' +
      '<div class="sbar"><i style="width:' + (x / tot * 100) + '%;background:' + col(h.team.color, "#e23b3b") + '"></i><i style="width:' +
      (y / tot * 100) + '%;background:' + col(a.team.color, "#2f6fe0") + '"></i></div></div>';
  }).join("");
  var tl = evs.length ? evs.slice().reverse().map(function (e) {
    return '<li class="ev ' + e[3] + '"><span class="ic">' + e[0] + '</span><span class="mn">' + esc(e[1]) + "</span><span>" + esc(e[2]) + "</span></li>";
  }).join("") : '<li class="ev info"><span class="ic">⏳</span><span></span><span>' + esc(t(state === "pre" ? "lv_wait" : "lv_noev")) + "</span></li>";

  var goals = (+h.score || 0) + (+a.score || 0), scored = last.id === g.id && goals > last.goals;
  var firstDraw = !box.querySelector(".lv-pitch") || last.id !== g.id;
  if (firstDraw) {
    box.innerHTML = '<div class="lv-board"><div class="tm">' + esc(h.team.displayName) + '</div><div class="sc" id="lvsc"></div><div class="tm">' +
      esc(a.team.displayName) + '</div></div><div class="lv-st" id="lvbadge"></div><div class="lv-cm" id="lvcm"></div><div class="lv-wrap">' + pitch(h, a) +
      '<div class="lv-goal" id="lvgoal"></div></div><div class="lv-grid"><div><h3>' + esc(t("lv_stats")) + '</h3><div id="lvstats"></div></div>' +
      '<div><h3>' + esc(t("lv_events")) + '</h3><ul class="tl" id="lvtl"></ul></div></div><p class="meta lv-src">' + esc(t("lv_src")) + "</p>";
  }
  document.getElementById("lvsc").textContent = state === "pre" ? "vs" : h.score + " – " + a.score;
  document.getElementById("lvbadge").innerHTML = badge + " <small>" + esc(g.comp) + "</small>";
  document.getElementById("lvstats").innerHTML = stats || '<p class="meta">' + esc(t("lv_wait")) + "</p>";
  document.getElementById("lvtl").innerHTML = tl;
  if (scored && evs.length) {
    var goalEv = evs.filter(function (e) { return e[3] === "goal"; }).pop();
    var gb = document.getElementById("lvgoal");
    gb.innerHTML = "<b>" + esc(t("lv_goal")) + "</b><span>" + esc(goalEv ? goalEv[2] : "") + "</span>";
    gb.classList.add("show");
    setTimeout(function () { gb.classList.remove("show"); }, 9000);
  }
  if (firstDraw) cmBar();
  commentate(g, s, h, a, state, teams);
  last = {id: g.id, goals: goals, state: state, pos: stat(bh, "possessionPct") || 50};
  drawList();
  clearTimeout(timer);
  timer = setTimeout(loadMatch, state === "in" ? 30000 : 120000);
}

// the ball wanders around the pitch while the match is live (more often in the half of the team with less possession)
setInterval(function () {
  var b = document.getElementById("ball");
  if (!b || last.state !== "in") return;
  if (Math.abs(ball.x - ball.tx) < 1 && Math.abs(ball.y - ball.ty) < 1) {
    var homeAttack = Math.random() * 100 < (last.pos || 50);
    ball.tx = homeAttack ? 52 + Math.random() * 40 : 8 + Math.random() * 40;
    ball.ty = 8 + Math.random() * 48;
  }
  ball.x += (ball.tx - ball.x) * 0.08; ball.y += (ball.ty - ball.y) * 0.08;
  b.setAttribute("cx", ball.x.toFixed(2)); b.setAttribute("cy", ball.y.toFixed(2));
}, 60);

document.addEventListener("fa:lang", function () { drawList(); last = {}; loadMatch(); });
loadList();
setInterval(loadList, 60000);
})();
