/* Football Arena – Match Centre (programme.html)
   Data: ESPN public site API (no key, called from the browser like live.js).
   Never invents data: anything the provider doesn't return is shown as unavailable. */
(() => {
'use strict';
const API = 'https://site.api.espn.com/apis/site/v2/sports/soccer/';
const ATH = 'https://site.api.espn.com/apis/common/v3/sports/soccer/athletes/';
const LEAGUES = [
  { slug: 'eng.1', name: 'Premier League' },
  { slug: 'esp.1', name: 'LaLiga' },
  { slug: 'ita.1', name: 'Serie A' },
  { slug: 'ger.1', name: 'Bundesliga' },
  { slug: 'fra.1', name: 'Ligue 1' },
  { slug: 'uefa.champions', name: 'Champions League' },
  { slug: 'uefa.europa', name: 'Europa League' },
  { slug: 'uefa.europa.conf', name: 'Conference League' },
  { slug: 'uefa.nations', name: 'Nations League', intl: true },
  { slug: 'fifa.friendly', name: 'International Friendlies', intl: true }
];
const LG = Object.fromEntries(LEAGUES.map(l => [l.slug, l]));
const GK_KIT = '#f2b705';

/* ---------- small helpers ---------- */
const $ = s => document.querySelector(s);
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const ymd = d => d.getFullYear() + String(d.getMonth() + 1).padStart(2, '0') + String(d.getDate()).padStart(2, '0');
const addDays = (d, n) => { const x = new Date(d); x.setDate(x.getDate() + n); return x; };
const fmtTime = iso => new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
const fmtDate = (iso, o) => new Date(iso).toLocaleDateString([], o || { weekday: 'short', day: 'numeric', month: 'short' });
const store = {
  get(k) { try { const v = JSON.parse(localStorage.getItem(k)); return v && v.exp > Date.now() ? v.d : null; } catch (e) { return null; } },
  set(k, d, ttl) { try { localStorage.setItem(k, JSON.stringify({ d, exp: Date.now() + ttl })); } catch (e) { /* storage full or blocked */ } }
};
const mem = new Map();
async function getJSON(url, ttl = 120000) {
  const hit = mem.get(url);
  if (hit && hit.exp > Date.now()) return hit.p;
  const p = fetch(url).then(r => { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); });
  mem.set(url, { p, exp: Date.now() + ttl });
  p.catch(() => mem.delete(url));
  return p;
}
async function pool(items, n, fn) {
  const out = new Array(items.length); let i = 0;
  await Promise.all(Array.from({ length: Math.min(n, items.length) }, async () => {
    while (i < items.length) { const k = i++; try { out[k] = await fn(items[k]); } catch (e) { out[k] = { error: e }; } }
  }));
  return out;
}
const hex = c => (c && /^[0-9a-f]{6}$/i.test(c) ? '#' + c : null);
function lum(h) { const n = parseInt(h.slice(1), 16); const f = v => { v /= 255; return v <= .03928 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4; }; return .2126 * f(n >> 16) + .7152 * f(n >> 8 & 255) + .0722 * f(n & 255); }
const ink = h => (lum(h) > .45 ? '#0b1a10' : '#ffffff');
const initials = n => String(n || '').split(/\s+/).filter(Boolean).map(w => w[0]).slice(0, 2).join('').toUpperCase();
const sk = (n, tall) => `<div class="sk${tall ? ' tall' : ''}">${'<i></i>'.repeat(n)}</div>`;
const errBox = (msg, fn) => { const id = 'r' + Math.random().toString(36).slice(2); setTimeout(() => { const b = document.getElementById(id); if (b) b.onclick = fn; }); return `<div class="err">${esc(msg)} <button id="${id}" type="button">Retry</button></div>`; };

/* ---------- illustrated kit (portrait fallback) ---------- */
function kitSVG(fill, trim, num) {
  const t = ink(fill);
  return `<svg class="kit" viewBox="0 0 64 64" aria-hidden="true"><path d="M22 6 14 9 4 18l6 10 6-4v34h32V24l6 4 6-10-10-9-8-3c-2 5-6 7-10 7s-8-2-10-7Z" fill="${fill}" stroke="${trim}" stroke-width="2.2" stroke-linejoin="round"/><path d="M22 6c2 5 6 7 10 7s8-2 10-7" fill="none" stroke="${trim}" stroke-width="2.2"/><text x="32" y="45" text-anchor="middle" font-family="system-ui,sans-serif" font-size="${String(num).length > 2 ? 14 : 19}" font-weight="900" fill="${t}">${esc(num || '')}</text></svg>`;
}
/* Optional licensed/illustrated portraits: list athlete IDs in portraits/index.json
   and place files as portraits/<athleteId>.webp. Missing → illustrated kit. */
let portraitSet = new Set();
const portraitsReady = fetch('portraits/index.json', { cache: 'no-cache' })
  .then(r => (r.ok ? r.json() : [])).then(a => { portraitSet = new Set((a || []).map(String)); }).catch(() => {});
function portrait(p, kit) {
  return portraitSet.has(String(p.id))
    ? `<img class="ph" src="portraits/${esc(p.id)}.webp" alt="Illustration of ${esc(p.name)}" loading="lazy" onerror="this.replaceWith(document.createRange().createContextualFragment(this.dataset.fb))" data-fb="${esc(kitSVG(kit.fill, kit.trim, p.num))}">`
    : kitSVG(kit.fill, kit.trim, p.num);
}

/* ---------- state ---------- */
const S = {
  league: 'all', upDay: null, resDay: null,
  match: null,           // normalised match model
  team: 'home', view: 'xi', tab: 'before', galTeam: 'all',
  timers: { cd: null, live: null }
};

/* ---------- competitions ---------- */
function renderChips() {
  const el = $('#comp-chips');
  el.innerHTML = [`<button class="chip${S.league === 'all' ? ' on' : ''}" data-lg="all" role="tab">All competitions</button>`]
    .concat(LEAGUES.map(l => `<button class="chip${S.league === l.slug ? ' on' : ''}" data-lg="${l.slug}" role="tab">${esc(l.name)}</button>`)).join('');
  el.onclick = e => {
    const b = e.target.closest('[data-lg]'); if (!b) return;
    S.league = b.dataset.lg; renderChips(); loadDay('up', S.upDay); loadDay('res', S.resDay);
  };
}

/* ---------- fixtures & results by day ---------- */
const dayKey = d => ymd(d);
function normEvent(e, slug) {
  const c = e.competitions?.[0] || {};
  const side = ha => {
    const x = (c.competitors || []).find(k => k.homeAway === ha) || {};
    const t = x.team || {};
    return { id: t.id, name: t.displayName || t.name || '—', short: t.abbreviation || '', logo: t.logo || t.logos?.[0]?.href || '', score: x.score };
  };
  const st = e.status?.type || c.status?.type || {};
  return { id: e.id, slug, date: e.date, state: st.state, detail: st.shortDetail || st.detail || '', clock: e.status?.displayClock, home: side('home'), away: side('away'), venue: c.venue?.fullName || '' };
}
async function fetchDay(date) {
  // The provider groups matches by US calendar day; fetch the two provider days that overlap
  // the visitor's local day, then keep only matches that kick off on that local day.
  const leagues = S.league === 'all' ? LEAGUES : [LG[S.league]];
  const days = new Date().getTimezoneOffset() < 300 ? [addDays(date, -1), date] : [date, addDays(date, 1)];
  const jobs = leagues.flatMap(l => days.map(d => ({ l, d })));
  const res = await pool(jobs, 6, async ({ l, d }) => {
    const j = await getJSON(API + l.slug + '/scoreboard?dates=' + dayKey(d), 180000);
    return (j.events || []).map(e => normEvent(e, l.slug));
  });
  const failed = res.filter(r => r && r.error).length;
  if (failed && failed === jobs.length) throw new Error('all failed');
  const want = dayKey(date), seen = new Set();
  return res.filter(Array.isArray).flat().filter(m => {
    if (seen.has(m.id) || dayKey(new Date(m.date)) !== want) return false;
    seen.add(m.id); return true;
  });
}
function renderDays(kind) {
  const el = $('#' + kind + '-days'); const today = new Date(); today.setHours(12, 0, 0, 0);
  const range = kind === 'up' ? [...Array(10).keys()] : [...Array(10).keys()].map(i => -(i + 1));
  const sel = dayKey(kind === 'up' ? S.upDay : S.resDay);
  el.innerHTML = range.map(o => {
    const d = addDays(today, o);
    const lab = o === 0 ? 'Today' : o === 1 ? 'Tomorrow' : o === -1 ? 'Yesterday' : d.toLocaleDateString([], { weekday: 'short' });
    return `<button class="day${dayKey(d) === sel ? ' on' : ''}" data-o="${o}"><small>${lab}</small>${d.getDate()} ${d.toLocaleDateString([], { month: 'short' })}</button>`;
  }).join('');
  el.onclick = e => { const b = e.target.closest('[data-o]'); if (!b) return; loadDay(kind, addDays(today, +b.dataset.o), false); };
}
function matchRow(m) {
  const mid = m.state === 'pre'
    ? `<b>${fmtTime(m.date)}</b><small>${esc(fmtDate(m.date, { day: 'numeric', month: 'short' }))}</small>`
    : m.state === 'in'
      ? `<b>${esc(m.home.score)} - ${esc(m.away.score)}</b><small class="live-dot">${esc(m.clock || m.detail)}</small>`
      : `<b>${esc(m.home.score)} - ${esc(m.away.score)}</b><small>${esc(m.detail || 'FT')}</small>`;
  const sel = S.match && S.match.id === m.id ? ' sel' : '';
  return `<button class="mrow${sel}" data-m="${m.slug}/${m.id}" aria-label="${esc(m.home.name)} vs ${esc(m.away.name)}">
    <span class="t">${m.home.logo ? `<img src="${esc(m.home.logo)}" alt="" loading="lazy">` : ''}<span>${esc(m.home.name)}</span></span>
    <span class="mid">${mid}</span>
    <span class="t a">${m.away.logo ? `<img src="${esc(m.away.logo)}" alt="" loading="lazy">` : ''}<span>${esc(m.away.name)}</span></span></button>`;
}
function renderList(kind, events) {
  const el = $('#' + kind + '-list');
  if (!events.length) {
    el.innerHTML = `<div class="empty">${kind === 'up' ? 'No upcoming matches on this day' : 'No results on this day'}${S.league === 'all' ? '' : ' in ' + esc(LG[S.league].name)}. Try another day.</div>`;
    return;
  }
  const order = LEAGUES.map(l => l.slug);
  events.sort((a, b) => order.indexOf(a.slug) - order.indexOf(b.slug) || new Date(a.date) - new Date(b.date));
  let html = '', last = '';
  for (const m of events) {
    if (m.slug !== last) { html += `<div class="lgroup">${esc(LG[m.slug].name)}</div>`; last = m.slug; }
    html += matchRow(m);
  }
  el.innerHTML = html;
}
const dayCache = {};
async function loadDay(kind, date, autoSkip = true) {
  const el = $('#' + kind + '-list');
  if (kind === 'up') S.upDay = date; else S.resDay = date;
  renderDays(kind);
  el.innerHTML = sk(4);
  try {
    let evs = await fetchDay(date);
    evs = kind === 'up' ? evs.filter(m => m.state !== 'post' || false) : evs.filter(m => m.state === 'post');
    if (autoSkip && !evs.length) {           // jump to the nearest day that has matches
      for (let i = 1; i <= 6; i++) {
        const d = addDays(date, kind === 'up' ? i : -i);
        let x = await fetchDay(d);
        x = kind === 'up' ? x.filter(m => m.state !== 'post') : x.filter(m => m.state === 'post');
        if (x.length) { return loadDay(kind, d, false); }
      }
    }
    dayCache[kind] = evs;
    renderList(kind, evs);
    if (kind === 'up' && !S.match && !location.hash.startsWith('#match=') && evs.length) {
      const first = evs.find(m => m.state === 'in') || evs.slice().sort((a, b) => new Date(a.date) - new Date(b.date))[0];
      openMatch(first.slug, first.id, false);
    }
  } catch (e) {
    el.innerHTML = errBox("Couldn't load matches right now.", () => loadDay(kind, date, autoSkip));
  }
}
document.addEventListener('click', e => {
  const b = e.target.closest('.mrow[data-m]'); if (!b) return;
  const [slug, id] = b.dataset.m.split('/');
  openMatch(slug, id, true);
});

/* ---------- match model ---------- */
const statMap = arr => Object.fromEntries((arr || []).map(s => [s.name, s.value]));
function normPlayer(r, teamId) {
  const a = r.athlete || {};
  const subMin = (r.plays || []).filter(p => p.substitution).map(p => p.clock?.displayValue).filter(Boolean);
  return {
    id: a.id, teamId, name: a.displayName || a.fullName || '—', short: a.shortName || a.displayName || '', last: a.lastName || a.displayName || '',
    num: r.jersey || '', pos: r.position?.abbreviation || '', posName: r.position?.displayName || '',
    starter: !!r.starter, subbedIn: !!r.subbedIn, subbedOut: !!r.subbedOut, fp: +r.formationPlace || 0,
    subFor: r.subbedInFor?.athlete?.displayName || null, subMin: subMin[0] || null,
    stats: statMap(r.stats), link: (a.links || []).find(l => (l.rel || []).includes('playercard'))?.href || ''
  };
}
function rosterFor(summary, teamId) {
  const r = (summary.rosters || []).find(x => String(x.team?.id) === String(teamId));
  if (!r || !(r.roster || []).length) return null;
  const players = r.roster.map(p => normPlayer(p, teamId));
  if (players.filter(p => p.starter).length < 11) return null;
  return { formation: r.formation || '', players, uniform: hex(r.uniform?.color) };
}
async function expectedRoster(summary, team, kickoff) {
  // Expected XI = this team's most recent official starting XI (real data, clearly labelled as a prediction).
  const lf = (summary.lastFiveGames || []).find(x => String(x.team?.id) === String(team.id));
  const past = (lf?.events || []).filter(e => e.gameDate && new Date(e.gameDate) < new Date(kickoff))
    .sort((a, b) => new Date(b.gameDate) - new Date(a.gameDate));
  for (const ev of past.slice(0, 2)) {
    try {
      const s = await getJSON(API + 'all/summary?event=' + ev.id, 3600000);
      const r = rosterFor(s, team.id);
      if (r) return Object.assign(r, { basis: { date: ev.gameDate, opp: ev.opponent?.displayName || '', comp: ev.competitionName || '', score: ev.score || '' } });
    } catch (e) { /* try the previous game */ }
  }
  return null;
}
function normTeam(c) {
  const t = c.team || {};
  return {
    id: t.id, name: t.displayName || t.name, short: t.abbreviation, logo: t.logos?.[0]?.href || t.logo || '',
    color: hex(t.color) || '#2e7d4f', alt: hex(t.alternateColor) || '#ffffff', score: c.score, form: c.form || '', ha: c.homeAway
  };
}
async function buildMatch(slug, id) {
  const s = await getJSON(API + slug + '/summary?event=' + id, 60000);
  const comp = s.header?.competitions?.[0];
  if (!comp) throw new Error('no match');
  const cs = comp.competitors || [];
  const home = normTeam(cs.find(c => c.homeAway === 'home') || cs[0]);
  const away = normTeam(cs.find(c => c.homeAway === 'away') || cs[1]);
  const st = comp.status?.type || {};
  const m = {
    id, slug, s, date: comp.date, state: st.state, detail: st.shortDetail || st.detail || '', clock: comp.status?.displayClock,
    league: s.header?.league?.name || LG[slug]?.name || '', leagueShort: LG[slug]?.name || s.header?.league?.abbreviation || '',
    venue: s.gameInfo?.venue?.fullName || '', city: [s.gameInfo?.venue?.address?.city, s.gameInfo?.venue?.address?.country].filter(Boolean).join(', '),
    home, away, fetched: new Date()
  };
  // line-ups: official if published, otherwise expected
  const rh = rosterFor(s, home.id), ra = rosterFor(s, away.id);
  if (rh && ra) {
    m.lineupKind = m.state === 'post' ? 'post' : 'conf';
    home.roster = rh; away.roster = ra;
  } else {
    m.lineupKind = 'pred';
    const [eh, ea] = await Promise.all([expectedRoster(s, home, m.date), expectedRoster(s, away, m.date)]);
    home.roster = rh || eh; away.roster = ra || ea;
    if (rh) home.roster.official = true; if (ra) away.roster.official = true;
  }
  for (const t of [home, away]) {
    // Official line-ups carry the kit colour worn in this match; otherwise use the club's primary colour.
    t.kit = { fill: (t.roster && !t.roster.basis && t.roster.uniform) || t.color, trim: t.alt === t.color ? '#ffffff' : t.alt };
    if (t.kit.fill.toLowerCase() === t.kit.trim.toLowerCase()) t.kit.trim = ink(t.kit.fill);
  }
  return m;
}

/* ---------- programme ---------- */
async function openMatch(slug, id, scroll) {
  if (!LG[slug] && slug !== 'all') slug = 'all';
  history.replaceState(null, '', '#match=' + slug + '/' + id);
  document.querySelectorAll('.mrow.sel').forEach(x => x.classList.remove('sel'));
  document.querySelectorAll(`.mrow[data-m="${slug}/${id}"]`).forEach(x => x.classList.add('sel'));
  clearInterval(S.timers.cd); clearTimeout(S.timers.live);
  $('#prog').innerHTML = sk(1, true); $('#lineup').innerHTML = sk(1, true); $('#gal').innerHTML = sk(1, true); $('#gal-ctl').hidden = true;
  if (scroll) $('#programme').scrollIntoView({ behavior: 'smooth', block: 'start' });
  try {
    await portraitsReady;
    const m = await buildMatch(slug, id);
    const sameMatch = S.match && S.match.id === m.id;
    S.match = m;
    if (!sameMatch) { S.team = 'home'; S.view = 'xi'; S.galTeam = 'all'; S.tab = m.state === 'post' ? 'after' : 'before'; }
    renderProgramme(); renderLineup(); renderGallery();
    if (m.state === 'in' || (m.state === 'pre' && new Date(m.date) - Date.now() < 90 * 60000)) {
      S.timers.live = setTimeout(() => { mem.clear(); openMatch(slug, id, false); }, 60000);
    }
  } catch (e) {
    const retry = () => openMatch(slug, id, false);
    $('#prog').innerHTML = errBox("Couldn't load this match programme.", retry);
    $('#lineup').innerHTML = '<div class="empty">Line-ups unavailable.</div>';
    $('#gal').innerHTML = '<div class="empty">Player cards unavailable.</div>';
  }
}
function statusBadge(m) {
  if (m.state === 'in') return `<span class="badge b-live">● Live ${esc(m.clock || '')}</span>`;
  if (m.state === 'post') return `<span class="badge b-post">Full time</span>`;
  return m.lineupKind === 'conf' ? `<span class="badge b-conf">Line-ups confirmed</span>` : `<span class="badge b-pred">Line-ups: expected</span>`;
}
function renderProgramme() {
  const m = S.match;
  const center = m.state === 'pre'
    ? `<div class="v">VS</div>`
    : `<div class="sc">${esc(m.home.score)}<span style="color:var(--mut)"> - </span>${esc(m.away.score)}</div><div class="${m.state === 'in' ? 'live-dot' : ''}" style="font-size:13px;color:var(--mut);font-weight:700">${esc(m.state === 'in' ? m.clock : m.detail)}</div>`;
  const tm = t => `<div class="tm">${t.logo ? `<img src="${esc(t.logo)}" alt="${esc(t.name)} logo">` : ''}<span>${esc(t.name)}</span><small>${t === m.home ? 'Home' : 'Away'}</small></div>`;
  const ko = new Date(m.date);
  $('#prog').innerHTML = `
  <div class="hero">
    <div class="comp">🏆 ${esc(m.league)}</div>
    <div class="vs">${tm(m.home)}<div class="c">${center}</div>${tm(m.away)}</div>
    <div class="info"><span>📅 ${esc(ko.toLocaleDateString([], { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric' }))}</span><span>🕘 ${esc(fmtTime(m.date))} (your time)</span>${m.venue ? `<span>🏟️ ${esc(m.venue)}</span>` : ''}${m.city ? `<span>📍 ${esc(m.city)}</span>` : ''}</div>
    ${m.state === 'pre' ? '<div class="cd" id="cd" aria-live="off"></div>' : ''}
    <div class="st">${statusBadge(m)}</div>
    <div class="upd">Data: ESPN · updated ${esc(m.fetched.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }))}</div>
  </div>
  <div class="tabs" role="tablist">
    <button data-tab="before" class="${S.tab === 'before' ? 'on' : ''}" role="tab">⭐ Before the match</button>
    <button data-tab="after" class="${S.tab === 'after' ? 'on' : ''}" role="tab" ${m.state === 'pre' ? 'disabled title="Available once the match starts"' : ''}>🏁 ${m.state === 'in' ? 'Match so far' : 'After the match'}</button>
  </div>
  <div id="tabbody"></div>`;
  $('#prog .tabs').onclick = e => { const b = e.target.closest('[data-tab]'); if (!b || b.disabled) return; S.tab = b.dataset.tab; renderProgramme(); };
  if (m.state === 'pre') startCountdown(ko);
  $('#tabbody').innerHTML = S.tab === 'after' && m.state !== 'pre' ? afterHTML(m) : beforeHTML(m);
}
function startCountdown(ko) {
  const tick = () => {
    const el = $('#cd'); if (!el) return clearInterval(S.timers.cd);
    let d = Math.max(0, ko - Date.now());
    if (d === 0) { el.innerHTML = '<div style="min-width:auto;padding:6px 14px"><b>Kick-off!</b></div>'; clearInterval(S.timers.cd); return; }
    const u = [[864e5, 'DAYS'], [36e5, 'HOURS'], [6e4, 'MIN'], [1e3, 'SEC']].map(([ms, l]) => { const v = Math.floor(d / ms); d -= v * ms; return `<div><b>${String(v).padStart(2, '0')}</b><small>${l}</small></div>`; });
    el.innerHTML = u.join('');
  };
  tick(); clearInterval(S.timers.cd); S.timers.cd = setInterval(tick, 1000);
}
function formHTML(f) { return f ? `<div class="form">${[...f].map(c => `<i class="${c}">${c}</i>`).join('')}</div>` : '<span class="m">Not available</span>'; }
function beforeHTML(m) {
  const s = m.s;
  const last5 = t => {
    const lf = (s.lastFiveGames || []).find(x => String(x.team?.id) === String(t.id));
    const evs = (lf?.events || []).slice().sort((a, b) => new Date(b.gameDate) - new Date(a.gameDate));
    if (!evs.length) return '<p class="m">Recent results not available.</p>';
    return `<ul class="fl">${evs.map(e => `<li><span>${e.atVs === '@' ? '@ ' : 'vs '}${esc(e.opponent?.displayName || '')}<br><span class="m">${esc(fmtDate(e.gameDate, { day: 'numeric', month: 'short' }))} · ${esc((e.competitionName || '').replace(/^\d{4}(-\d{2})?\s/, ''))}</span></span><b class="${e.gameResult === 'W' ? 'b-conf' : e.gameResult === 'L' ? 'b-live' : ''}">${esc(e.gameResult || '')} ${esc(e.score || '')}</b></li>`).join('')}</ul>`;
  };
  const ss = (s.seasonseries || []).find(x => x.type === 'head-to-head') || (s.seasonseries || [])[0];
  const h2h = ss && (ss.events || []).length
    ? `<p style="margin:0 0 6px;font-weight:700">${esc(ss.summary || '')}</p><ul class="fl">${ss.events.slice(0, 6).map(e => {
      const h = (e.competitors || []).find(c => c.homeAway === 'home'), a = (e.competitors || []).find(c => c.homeAway === 'away');
      return `<li><span>${esc(h?.team?.displayName || h?.team?.abbreviation || '')} – ${esc(a?.team?.displayName || a?.team?.abbreviation || '')}<br><span class="m">${esc(fmtDate(e.date, { day: 'numeric', month: 'short', year: 'numeric' }))}</span></span><b>${esc(h?.score ?? '')} - ${esc(a?.score ?? '')}</b></li>`;
    }).join('')}</ul>`
    : '<p class="m">No head-to-head data from the provider for this fixture.</p>';
  const lu = t => {
    const r = t.roster;
    if (!r) return '<span class="m">Not announced yet</span>';
    return `<b>${esc(r.formation || '—')}</b> ${r.basis ? '<span class="badge b-pred">Expected</span>' : '<span class="badge b-conf">Official</span>'}`;
  };
  return `<div class="grid2">
    <div class="box"><h3>Team form (last 5)</h3>
      <p style="margin:0 0 4px;font-weight:700">${esc(m.home.name)}</p>${formHTML(m.home.form)}
      <p style="margin:10px 0 4px;font-weight:700">${esc(m.away.name)}</p>${formHTML(m.away.form)}
      <h3 style="margin-top:14px">Formations</h3>
      <ul class="fl"><li><span>${esc(m.home.name)}</span>${lu(m.home)}</li><li><span>${esc(m.away.name)}</span>${lu(m.away)}</li></ul>
      <p class="m" style="font-size:12px;margin:6px 0 0">Coach names aren't provided by the data source.</p>
    </div>
    <div class="box"><h3>Head-to-head</h3>${h2h}</div>
    <div class="box"><h3>${esc(m.home.name)} – recent results</h3>${last5(m.home)}</div>
    <div class="box"><h3>${esc(m.away.name)} – recent results</h3>${last5(m.away)}</div>
  </div>`;
}
function afterHTML(m) {
  const s = m.s, ke = s.keyEvents || [];
  const side = tid => (String(tid) === String(m.home.id) ? 'h' : 'a');
  const row = (k, html) => side(k.team?.id) === 'h' ? `<li><span class="h">${html}</span><span class="min">${esc(k.clock?.displayValue || '')}</span><span></span></li>` : `<li><span></span><span class="min">${esc(k.clock?.displayValue || '')}</span><span>${html}</span></li>`;
  const goals = ke.filter(k => k.scoringPlay && !k.shootout).map(k => {
    const t = (k.type?.type || '') + ' ' + (k.type?.text || '');
    const tag = /own/i.test(t) ? ' <small>(OG)</small>' : /penalty/i.test(t) ? ' <small>(pen)</small>' : '';
    const sc = k.participants?.[0]?.athlete?.displayName || '—'; const as = !/own|penalty/i.test(t) ? k.participants?.[1]?.athlete?.displayName : null;
    return row(k, `⚽ <b>${esc(sc)}</b>${tag}${as ? `<br><small>Assist: ${esc(as)}</small>` : ''}`);
  });
  const cards = ke.filter(k => /card/i.test(k.type?.type || '')).map(k => {
    const red = /red/i.test(k.type?.type || '');
    return row(k, `<span class="${red ? 'rc' : 'yc'}"></span>${esc(k.participants?.[0]?.athlete?.displayName || '—')}`);
  });
  const subs = [];
  for (const t of [m.home, m.away]) for (const p of (t.roster?.basis ? [] : t.roster?.players || [])) if (p.subbedIn) subs.push({ t, p });
  subs.sort((a, b) => parseInt(a.p.subMin) - parseInt(b.p.subMin));
  const subRows = subs.map(({ t, p }) => row({ team: { id: t.id }, clock: { displayValue: p.subMin || '' } }, `<span class="b-conf">▲ ${esc(p.name)}</span>${p.subFor ? `<br><small class="b-live">▼ ${esc(p.subFor)}</small>` : ''}`));
  const bs = s.boxscore?.teams || [];
  const tstat = (tid, n) => { const t = bs.find(x => String(x.team?.id) === String(tid)); const v = (t?.statistics || []).find(x => x.name === n); return v ? v.displayValue : null; };
  const STATS = [['possessionPct', 'Possession', '%'], ['totalShots', 'Shots'], ['shotsOnTarget', 'Shots on target'], ['wonCorners', 'Corners'], ['foulsCommitted', 'Fouls'], ['offsides', 'Offsides'], ['saves', 'Saves'], ['yellowCards', 'Yellow cards'], ['redCards', 'Red cards'], ['accuratePasses', 'Accurate passes']];
  const bars = STATS.map(([n, lab, suf]) => {
    const a = tstat(m.home.id, n), b = tstat(m.away.id, n); if (a == null || b == null) return '';
    const x = parseFloat(a) || 0, y = parseFloat(b) || 0, tot = x + y || 1;
    return `<div class="sbar"><div class="lab"><span>${esc(a)}${suf || ''}</span><span>${lab}</span><span>${esc(b)}${suf || ''}</span></div><div class="bar"><i style="width:${x / tot * 100}%;background:${m.home.kit.fill}"></i><i style="width:${y / tot * 100}%;background:${m.away.kit.fill}"></i></div></div>`;
  }).join('');
  const head = `<li style="font-weight:800"><span class="h">${esc(m.home.short || m.home.name)}</span><span class="min"></span><span>${esc(m.away.short || m.away.name)}</span></li>`;
  return `<div class="grid2">
    <div class="box"><h3>Goals</h3>${goals.length ? `<ul class="ev">${head}${goals.join('')}</ul>` : '<p class="m">No goals.</p>'}
      <h3 style="margin-top:14px">Cards</h3>${cards.length ? `<ul class="ev">${cards.join('')}</ul>` : '<p class="m">No cards recorded.</p>'}</div>
    <div class="box"><h3>Match statistics</h3>${bars || '<p class="m">Statistics not available yet.</p>'}</div>
    <div class="box" style="grid-column:1/-1"><h3>Substitutions</h3>${subRows.length ? `<ul class="ev">${head}${subRows.join('')}</ul>` : '<p class="m">No substitutions recorded.</p>'}
      <p class="m" style="font-size:12px;margin:8px 0 0">Player ratings and Man of the Match aren't provided by the data source, so they aren't shown.</p></div>
  </div>`;
}

/* ---------- interactive pitch ---------- */
function depth(abbr) {
  const a = String(abbr).toUpperCase().replace(/-[LR]$/, '');
  if (a === 'G' || a === 'GK') return 0;
  if (/^(CD|CB|D|SW|RB|LB|RCB|LCB)$/.test(a)) return 1;
  if (/WB$/.test(a)) return 1.5;
  if (/^(DM|CDM|LDM|RDM)$/.test(a)) return 2;
  if (/^(AM|CAM|LAM|RAM|LW|RW|W|SS)$/.test(a)) return 4;
  if (/^(F|CF|ST|FW|S|LF|RF)$/.test(a)) return 5;
  return 3;
}
function lateral(abbr) {
  const a = String(abbr).toUpperCase();
  if (/-L$/.test(a)) return -1; if (/-R$/.test(a)) return 1;
  if (/^L/.test(a)) return -2; if (/^R/.test(a)) return 2; return 0;
}
function layout(players, formation) {
  const xi = players.filter(p => p.starter);
  const gk = xi.find(p => depth(p.pos) === 0) || xi.slice().sort((a, b) => a.fp - b.fp)[0];
  const out = xi.filter(p => p !== gk).sort((a, b) => depth(a.pos) - depth(b.pos) || a.fp - b.fp);
  let lines = String(formation || '').split('-').map(Number).filter(n => n > 0);
  if (lines.reduce((a, b) => a + b, 0) !== out.length) {   // fall back to grouping by role
    lines = []; let prev = null;
    for (const p of out) { const d = depth(p.pos); if (d !== prev) { lines.push(0); prev = d; } lines[lines.length - 1]++; }
  }
  const pos = []; let i = 0;
  if (gk) pos.push({ p: gk, x: 50, y: 91 });
  lines.forEach((n, li) => {
    const row = out.slice(i, i + n).sort((a, b) => lateral(a.pos) - lateral(b.pos) || a.fp - b.fp); i += n;
    const y = lines.length === 1 ? 45 : 74 - li * (62 / (lines.length - 1));
    row.forEach((p, j) => pos.push({ p, x: 10 + (j + 1) * 80 / (n + 1), y }));
  });
  return pos;
}
const PITCH_LINES = `<svg class="lines" viewBox="0 0 68 100" preserveAspectRatio="none" aria-hidden="true" fill="none" stroke="rgba(255,255,255,.55)" stroke-width=".35">
<rect x="2" y="2" width="64" height="96"/><line x1="2" y1="50" x2="66" y2="50"/><circle cx="34" cy="50" r="8.5"/><circle cx="34" cy="50" r=".6" fill="rgba(255,255,255,.7)"/>
<rect x="14" y="2" width="40" height="15"/><rect x="24" y="2" width="20" height="5.5"/><rect x="14" y="83" width="40" height="15"/><rect x="24" y="92.5" width="20" height="5.5"/>
<path d="M27 17a8 8 0 0 0 14 0M27 83a8 8 0 0 1 14 0"/></svg>`;
function playerTags(p, m) {
  if (m.lineupKind === 'pred') return '';
  const t = [];
  const g = p.stats.totalGoals || 0, as = p.stats.goalAssists || 0;
  for (let k = 0; k < Math.min(g, 3); k++) t.push('⚽');
  if (as) t.push('🅰');
  if (p.stats.redCards) t.push('<span class="rc" style="margin:0"></span>'); else if (p.stats.yellowCards) t.push('<span class="yc" style="margin:0"></span>');
  if (p.subbedOut) t.push('🔻');
  return t.length ? `<span class="tag">${t.map(x => `<i>${x}</i>`).join('')}</span>` : '';
}
function kitFor(p, team) { return depth(p.pos) === 0 ? { fill: GK_KIT, trim: '#1b1b1b' } : team.kit; }
function lineupBadge(m, t) {
  const r = t.roster;
  if (!r) return '';
  if (r.basis) return `<span class="badge b-pred">Predicted</span><span>Expected XI · based on last official line-up vs ${esc(r.basis.opp)} (${esc(fmtDate(r.basis.date, { day: 'numeric', month: 'short' }))}). Not confirmed.</span>`;
  if (m.lineupKind === 'post') return `<span class="badge b-post">Post-match</span><span>Final line-up and substitutions</span>`;
  return `<span class="badge b-conf">Confirmed</span><span>Official line-up from the data provider</span>`;
}
function renderLineup() {
  const m = S.match, t = m[S.team];
  const r = t.roster;
  const ctl = `<div class="lu-ctl">
    <div class="seg" role="tablist" aria-label="Team">${['home', 'away'].map(k => `<button data-team="${k}" class="${S.team === k ? 'on' : ''}">${m[k].logo ? `<img src="${esc(m[k].logo)}" alt="" style="width:18px;height:18px;object-fit:contain">` : ''}${esc(m[k].name)}</button>`).join('')}</div>
    <div class="seg" role="tablist" aria-label="Players">${[['xi', 'Starting XI'], ['subs', 'Substitutes']].map(([k, l]) => `<button data-view="${k}" class="${S.view === k ? 'on' : ''}">${l}</button>`).join('')}</div></div>`;
  if (!r) {
    $('#lineup').innerHTML = ctl + `<div class="empty">${esc(t.name)} line-up not announced yet. Official line-ups usually appear about 1 hour before kick-off.</div>`;
    bindLineupCtl(); return;
  }
  const meta = `<div class="lu-meta"><span class="fm">${esc(r.formation || '—')}</span>${lineupBadge(m, t)}</div>`;
  const starters = r.players.filter(p => p.starter);
  const bench = r.players.filter(p => !p.starter);
  let main;
  if (S.view === 'xi') {
    main = `<div class="pitch" role="group" aria-label="${esc(t.name)} formation ${esc(r.formation)}">${PITCH_LINES}${layout(r.players, r.formation).map(({ p, x, y }) =>
      `<button class="pl" style="left:${x}%;top:${y}%" data-pid="${esc(p.id)}" aria-label="${esc(p.num)} ${esc(p.name)}, ${esc(p.posName)}">${kitSVG(kitFor(p, t).fill, kitFor(p, t).trim, p.num)}<span class="nm">${esc(p.last || p.short)}</span>${playerTags(p, m)}</button>`).join('')}</div>`;
  } else {
    main = bench.length ? `<div class="bench">${bench.map(p => `<button class="bp" data-pid="${esc(p.id)}">${kitSVG(kitFor(p, t).fill, kitFor(p, t).trim, p.num)}<span>${esc(p.name)}<small>${esc(p.posName || p.pos)}${m.lineupKind !== 'pred' ? (p.subbedIn ? ` · ▲ on ${esc(p.subMin || '')}` : m.state === 'post' ? ' · unused' : '') : ''}</small></span></button>`).join('')}</div>` : '<div class="empty">No substitutes listed.</div>';
  }
  const list = (S.view === 'xi' ? starters : bench);
  const side = `<div class="side box"><h3>${S.view === 'xi' ? 'Starting XI' : 'Substitutes'} · ${esc(t.name)}</h3><ul class="xi-list">${list.map(p => `<li data-pid="${esc(p.id)}" tabindex="0"><span class="n">${esc(p.num)}</span><span>${esc(p.name)}</span><span class="p">${esc(p.pos)}</span></li>`).join('')}</ul></div>`;
  $('#lineup').innerHTML = ctl + meta + `<div class="lu-wrap"><div>${main}</div>${side}</div>`;
  bindLineupCtl();
}
function bindLineupCtl() {
  $('#lineup').onclick = e => {
    const tb = e.target.closest('[data-team]'); if (tb) { S.team = tb.dataset.team; return renderLineup(); }
    const vb = e.target.closest('[data-view]'); if (vb) { S.view = vb.dataset.view; return renderLineup(); }
    const pb = e.target.closest('[data-pid]'); if (pb) openPlayer(pb.dataset.pid);
  };
  $('#lineup').onkeydown = e => { if (e.key === 'Enter') { const li = e.target.closest('li[data-pid]'); if (li) openPlayer(li.dataset.pid); } };
}

/* ---------- player gallery ---------- */
function allPlayers() {
  const m = S.match; const out = [];
  for (const t of [m.home, m.away]) for (const p of (t.roster?.players || [])) out.push({ p, t });
  return out;
}
function cardHTML({ p, t }) {
  const m = S.match;
  const chips = [];
  if (m.lineupKind !== 'pred') {
    if (p.stats.totalGoals) chips.push(`⚽ ${p.stats.totalGoals}`);
    if (p.stats.goalAssists) chips.push(`🅰 ${p.stats.goalAssists}`);
    if (p.stats.redCards) chips.push('<span class="rc" style="margin:0"></span>'); else if (p.stats.yellowCards) chips.push('<span class="yc" style="margin:0"></span>');
  }
  const role = t.roster.basis ? '' : p.starter ? 'Started' : p.subbedIn ? 'Came on' : m.state === 'post' ? 'Unused sub' : 'Substitute';
  const kit = kitFor(p, t);
  return `<button class="card" data-pid="${esc(p.id)}" aria-label="${esc(p.name)}">
    <div class="por" style="background:radial-gradient(circle at 50% 35%,${kit.fill}55,transparent 70%)">${portrait(p, kit)}<span class="num">${esc(p.pos && p.pos !== 'SUB' ? p.pos : '')}</span>${t.logo ? `<img class="tlogo" src="${esc(t.logo)}" alt="">` : ''}${chips.length ? `<span class="stat">${chips.map(c => `<i>${c}</i>`).join('')}</span>` : ''}${role ? `<span class="role badge ${p.starter ? 'b-conf' : 'b-post'}" style="font-size:9px">${role}</span>` : ''}</div>
    <div class="bd"><b>${esc(p.name)}</b><small>${esc(p.posName || p.pos)}</small><small class="nat" data-nat="${esc(p.id)}">&nbsp;</small></div></button>`;
}
function renderGallery() {
  const m = S.match; const ctl = $('#gal-ctl');
  const list = allPlayers();
  if (!list.length) { ctl.hidden = true; $('#gal').innerHTML = '<div class="empty">Player cards will appear once line-ups are available.</div>'; return; }
  ctl.hidden = false;
  ctl.innerHTML = [['all', 'Both teams'], ['home', m.home.name], ['away', m.away.name]].map(([k, l]) => `<button data-g="${k}" class="${S.galTeam === k ? 'on' : ''}">${esc(l)}</button>`).join('');
  ctl.onclick = e => { const b = e.target.closest('[data-g]'); if (!b) return; S.galTeam = b.dataset.g; renderGallery(); };
  const shown = list.filter(({ t }) => S.galTeam === 'all' || t === m[S.galTeam])
    .sort((a, b) => (a.t === b.t ? 0 : a.t === m.home ? -1 : 1) || (b.p.starter - a.p.starter) || depth(a.p.pos) - depth(b.p.pos));
  const pred = m.lineupKind === 'pred' ? `<div class="empty" style="text-align:left;grid-column:1/-1"><span class="badge b-pred">Predicted</span> Squad shown from each team's last official line-up. It will switch to the confirmed line-up automatically when published.</div>` : '';
  $('#gal').innerHTML = pred + shown.map(cardHTML).join('');
  $('#gal').onclick = e => { const c = e.target.closest('[data-pid]'); if (c) openPlayer(c.dataset.pid); };
  lazyNationality();
}
let natObs;
function lazyNationality() {
  natObs && natObs.disconnect();
  const queue = []; let running = 0;
  const run = () => {
    while (running < 4 && queue.length) {
      const el = queue.shift(); running++;
      athlete(el.dataset.nat).then(a => { if (a && a.cit) el.innerHTML = `${a.flag ? `<img src="${esc(a.flag)}" alt="">` : ''}${esc(a.cit)}`; })
        .catch(() => {}).finally(() => { running--; run(); });
    }
  };
  natObs = new IntersectionObserver(es => es.forEach(en => { if (en.isIntersecting) { natObs.unobserve(en.target); queue.push(en.target); run(); } }), { rootMargin: '200px' });
  document.querySelectorAll('[data-nat]').forEach(el => natObs.observe(el));
}
async function athlete(id) {
  const k = 'fa_ath_' + id; const c = store.get(k); if (c) return c;
  const j = await getJSON(ATH + id, 86400000); const a = j.athlete || j;
  const d = {
    cit: a.citizenship || a.citizenshipCountry?.name || '', flag: a.flag?.href || '', age: a.age || null, h: a.displayHeight || '', w: a.displayWeight || '', dob: a.displayDOB || '',
    team: a.team?.displayName || '', season: a.statsSummary?.displayName || '', stats: (a.statsSummary?.statistics || []).map(s => [s.displayName || s.name, s.displayValue])
  };
  store.set(k, d, 7 * 864e5);
  return d;
}

/* ---------- player profile ---------- */
const MATCH_STATS = [['totalGoals', 'Goals'], ['goalAssists', 'Assists'], ['totalShots', 'Shots'], ['shotsOnTarget', 'On target'], ['saves', 'Saves'], ['goalsConceded', 'Conceded'], ['foulsCommitted', 'Fouls'], ['foulsSuffered', 'Fouled'], ['offsides', 'Offsides'], ['yellowCards', 'Yellow'], ['redCards', 'Red']];
async function openPlayer(pid) {
  const found = allPlayers().find(x => String(x.p.id) === String(pid)); if (!found) return;
  const { p, t } = found; const m = S.match; const dlg = $('#pdlg'); const kit = kitFor(p, t);
  const ms = m.lineupKind === 'pred' ? [] : MATCH_STATS.filter(([k]) => p.stats[k] != null && (p.stats[k] !== 0 || ['totalGoals', 'goalAssists', 'totalShots'].includes(k)));
  const draw = a => {
    $('#pdlg-body').innerHTML = `<button class="pd-close" type="button" aria-label="Close">✕</button>
    <div class="pd-top"><div class="por" style="background:radial-gradient(circle,${kit.fill}66,transparent 70%)">${portrait(p, kit)}</div>
      <div><h3>${esc(p.name)}</h3><p>#${esc(p.num)} · ${esc(p.posName || p.pos)}</p><p>${t.logo ? `<img src="${esc(t.logo)}" alt="" style="width:18px;height:18px;object-fit:contain">` : ''}${esc(t.name)}</p>
      <p>${a === undefined ? 'Loading profile…' : a ? `${a.flag ? `<img src="${esc(a.flag)}" alt="">` : ''}${esc(a.cit || 'Nationality n/a')}` : 'Profile details unavailable'}</p></div></div>
    <div class="pd-bd">
      ${a ? `<div class="kv">${[['Age', a.age], ['Height', a.h], ['Weight', a.w], ['Born', a.dob], ['Club', a.team]].filter(x => x[1]).map(([k, v]) => `<div><small>${k}</small><b>${esc(v)}</b></div>`).join('')}</div>` : ''}
      ${ms.length ? `<h4>This match</h4><div class="kv">${ms.map(([k, l]) => `<div><small>${l}</small><b>${esc(p.stats[k])}</b></div>`).join('')}${p.subbedIn ? `<div><small>Came on</small><b>${esc(p.subMin || '✓')}</b></div>` : ''}</div>` : ''}
      ${a && a.stats.length ? `<h4>${esc(a.season || 'Season stats')}</h4><div class="kv">${a.stats.map(([k, v]) => `<div><small>${esc(k)}</small><b>${esc(v)}</b></div>`).join('')}</div>` : ''}
      ${p.link ? `<p style="margin:14px 0 0;font-size:14px"><a href="${esc(p.link)}" target="_blank" rel="noopener">Full profile on ESPN ↗</a></p>` : ''}
      <p class="m" style="font-size:12px;color:var(--mut);margin:8px 0 0">Image: illustration, not an official photograph.</p>
    </div>`;
    $('#pdlg-body .pd-close').onclick = () => dlg.close();
  };
  draw(undefined);
  if (typeof dlg.showModal === 'function') dlg.showModal(); else dlg.setAttribute('open', '');
  try { draw(await athlete(p.id)); } catch (e) { draw(null); }
}
$('#pdlg').addEventListener('click', e => { if (e.target === e.currentTarget) e.currentTarget.close(); });

/* ---------- section nav highlight ---------- */
(() => {
  const links = [...document.querySelectorAll('.mc-nav a[href^="#"]')];
  const io = new IntersectionObserver(es => es.forEach(en => {
    if (en.isIntersecting) links.forEach(a => a.classList.toggle('on', a.getAttribute('href') === '#' + en.target.id));
  }), { rootMargin: '-40% 0px -55% 0px' });
  links.forEach(a => { const s = document.getElementById(a.getAttribute('href').slice(1)); if (s) io.observe(s); });
})();

/* ---------- boot ---------- */
function fromHash() {
  const mt = location.hash.match(/^#match=([a-z0-9._]+)\/(\d+)/i);
  if (mt) { openMatch(mt[1], mt[2], false); return true; }
  return false;
}
window.addEventListener('hashchange', fromHash);
renderChips();
const today = new Date(); today.setHours(12, 0, 0, 0);
fromHash();
loadDay('up', today);
loadDay('res', addDays(today, -1));
})();
