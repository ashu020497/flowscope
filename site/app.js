/* Flowscope front end — reads site/data/*.json produced by the daily pipeline. */
(function () {
  'use strict';
  const D = {};
  const ST = { region: 'Global', win: 'Latest', view: 'Returns', cls: 'All', aregion: 'All', q: '', ccy: 'Local', sort: null, sortDir: -1, range: '3Y', aView: 'Returns' };
  const $main = document.getElementById('main');
  const tip = document.getElementById('tip');

  // ---------- formatting ----------
  const esc = (s) => String(s == null ? '' : s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const MINUS = '−';
  const isNum = (v) => typeof v === 'number' && isFinite(v);
  function pct(v, d = 1, signed = true) {
    if (!isNum(v)) return '—';
    const s = (Math.abs(v) * 100).toFixed(d) + '%';
    if (Number(s.slice(0, -1)) === 0) v = 0;
    if (!signed) return (v < 0 ? MINUS : '') + s;
    return (v > 0 ? '+' : v < 0 ? MINUS : '') + s;
  }
  const num = (v, d = 2) => (isNum(v) ? (v < 0 && Number(Math.abs(v).toFixed(d)) !== 0 ? MINUS : '') + Math.abs(v).toFixed(d) : '—');
  const cls = (v) => (isNum(v) ? (v > 0 ? 'in-t' : v < 0 ? 'out-t' : '') : '');
  function big(v) {
    const a = Math.abs(v);
    if (a >= 1e5) return (a / 1e5).toFixed(2) + 'L';
    if (a >= 1e3) return (a / 1e3).toFixed(1) + 'k';
    return a.toFixed(a >= 100 ? 0 : 1);
  }
  function flow(v, unit, signed = true) {
    if (!isNum(v)) return '—';
    const sg = signed ? (v > 0 ? '+' : v < 0 ? MINUS : '') : (v < 0 ? MINUS : '');
    if (unit === 'US$ bn') return sg + '$' + (Math.abs(v) >= 1000 ? (Math.abs(v) / 1000).toFixed(2) + 'tn' : Math.abs(v).toFixed(1) + 'bn');
    if (unit === '₹ cr') return sg + '₹' + big(v) + ' cr';
    if (unit === '¥ bn') return sg + '¥' + big(v) + 'bn';
    return sg + Math.abs(v).toFixed(1) + ' ' + unit;
  }
  const MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  function toDate(s) { return s.length === 7 ? new Date(s + '-28T00:00:00Z') : new Date(s.slice(0, 10) + 'T00:00:00Z'); }
  function fdate(s, withYear = false) {
    if (!s) return '—';
    const d = toDate(s);
    if (s.length === 7) return MON[d.getUTCMonth()] + ' ' + d.getUTCFullYear();
    return d.getUTCDate() + ' ' + MON[d.getUTCMonth()] + (withYear ? ' ' + d.getUTCFullYear() : '');
  }
  const ago = (iso) => { const h = (Date.now() - new Date(iso)) / 36e5; return h < 1 ? 'just now' : h < 48 ? Math.round(h) + ' h ago' : Math.round(h / 24) + ' days ago'; };

  // ---------- data ----------
  async function j(name) {
    const r = await fetch('data/' + name + (D.v ? '?v=' + D.v : ''), { cache: 'no-cache' });
    if (!r.ok) throw new Error(name + ' ' + r.status);
    return r.json();
  }
  async function load() {
    D.meta = await j('meta.json');
    D.v = encodeURIComponent(D.meta.generated || '');
    const [assets, flows, cash, decomp, sources] = await Promise.all(['assets.json', 'flows.json', 'cash.json', 'decomp.json', 'sources.json'].map((n) => j(n).catch(() => ({}))));
    Object.assign(D, { assets: assets.assets || [], rf: assets.rf || {}, flows, cash, decomp, sources: sources.sources || [] });
    D.byId = Object.fromEntries(D.assets.map((a) => [a.id, a]));
    D.srcById = Object.fromEntries(D.sources.map((s) => [s.id, s]));
    if (D.meta.demo) document.getElementById('demo').hidden = false;
    document.getElementById('fresh').textContent = 'Updated ' + ago(D.meta.generated);
  }

  // ---------- flow board helpers ----------
  const WIN_DAYS = { '3M': 91, '6M': 182, '12M': 365 };
  function windowValue(cat, win) {
    const h = cat.history || [];
    if (!h.length) return { v: null };
    const last = h[h.length - 1];
    const lastD = toDate(last[0]);
    if (win === 'Latest') {
      if (cat.freq === 'Daily') {
        const from = lastD - 7 * 864e5;
        const pts = h.filter((p) => toDate(p[0]) > from);
        return { v: pts.reduce((s, p) => s + p[1], 0), label: '7 days to ' + fdate(last[0]), n: pts.length };
      }
      return { v: last[1], label: cat.freq === 'Monthly' ? fdate(last[0]) : 'week to ' + fdate(last[0]), n: 1 };
    }
    const from = lastD - WIN_DAYS[win] * 864e5;
    const pts = h.filter((p) => toDate(p[0]) > from);
    const first = h[0][0];
    const partial = toDate(first) > from + 20 * 864e5;
    return { v: pts.reduce((s, p) => s + p[1], 0), label: (partial ? 'since ' + fdate(first, true) : win), n: pts.length, partial };
  }
  function board(region, win) {
    const cats = ((D.flows || {}).board || {})[region] || [];
    return cats.map((c) => Object.assign({}, c, windowValue(c, win))).filter((c) => isNum(c.v));
  }
  const lc = (s) => s.replace(/^(US|Foreign|Japanese|Foreigners)\b/, (m) => m).replace(/^[A-Z][a-z]/, (m) => m.toLowerCase());

  function headline(region, win) {
    const b = board(region, win);
    const where = region === 'Global' ? '' : region === 'United States' ? 'In the US, ' : 'In ' + region + ', ';
    if (b.length >= 3) {
      const pos = b.filter((c) => c.v > 0).sort((a, z) => z.v - a.v).slice(0, 2);
      const neg = b.filter((c) => c.v < 0).sort((a, z) => a.v - z.v).slice(0, 2);
      const nm = (c) => '<span class="' + (c.v > 0 ? 'in-t' : 'out-t') + '">' + esc(lc(c.name)) + '</span>';
      const join = (xs) => xs.map(nm).join(' and ');
      if (pos.length && neg.length) return (where ? where : '') + (where ? 'money' : 'Money') + ' is leaving ' + join(neg) + ' — and moving into ' + join(pos) + '.';
      if (pos.length) return (where || '') + (where ? 'money' : 'Money') + ' is flowing in, led by ' + join(pos) + '.';
      if (neg.length) return (where || '') + (where ? 'money' : 'Money') + ' is flowing out, led by ' + join(neg) + '.';
    }
    // fallback: relative price strength over 1 month
    const xs = D.assets.filter((a) => a.ret && isNum(a.ret['1M']) && a.cls !== 'Volatility' && a.cls !== 'FX');
    if (!xs.length) return 'Waiting for the first data refresh.';
    xs.sort((a, z) => z.ret['1M'] - a.ret['1M']);
    return 'Over the past month, <span class="in-t">' + esc(xs[0].name) + '</span> led and <span class="out-t">' + esc(xs[xs.length - 1].name) + '</span> fell most.';
  }

  // ---------- charts ----------
  const css = (v) => getComputedStyle(document.documentElement).getPropertyValue(v).trim();
  const observers = [];
  const signColor = (v) => css(v < 0 ? '--out' : '--in');
  function responsive(el, draw) {
    const go = () => { el.innerHTML = ''; draw(el.clientWidth || 600); };
    go();
    if (window.ResizeObserver) { const ro = new ResizeObserver(() => { clearTimeout(el._t); el._t = setTimeout(go, 80); }); ro.observe(el); observers.push(ro); }
  }
  function showTip(e, html) { tip.innerHTML = html; tip.hidden = false; const x = Math.min(e.clientX + 14, window.innerWidth - tip.offsetWidth - 8); tip.style.left = x + 'px'; tip.style.top = (e.clientY - 34) + 'px'; }
  function hideTip() { tip.hidden = true; }
  const NS = 'http://www.w3.org/2000/svg';
  function svgEl(tag, attrs, parent) { const e = document.createElementNS(NS, tag); for (const k in attrs) e.setAttribute(k, attrs[k]); if (parent) parent.appendChild(e); return e; }

  /** Line chart. series: [{pts:[[date,value]], color, name}] */
  function lineChart(el, series, opt = {}) {
    const H = opt.height || 260, fmt = opt.fmt || ((v) => num(v, 2));
    series = series.filter((s) => s.pts && s.pts.length > 1);
    if (!series.length) { el.innerHTML = '<div class="empty">No data yet for this chart.</div>'; return; }
    responsive(el, (W) => {
      const padL = 0, padR = 64, padT = 10, padB = 26;
      const all = series.flatMap((s) => s.pts.map((p) => p[1]));
      let lo = Math.min(...all), hi = Math.max(...all);
      if (opt.zero) { lo = Math.min(lo, 0); hi = Math.max(hi, 0); }
      if (lo === hi) { lo -= 1; hi += 1; }
      const pad = (hi - lo) * 0.06; lo -= pad; hi += pad;
      const t0 = Math.min(...series.map((s) => toDate(s.pts[0][0]).getTime())), t1 = Math.max(...series.map((s) => toDate(s.pts[s.pts.length - 1][0]).getTime()));
      const x = (d) => padL + ((toDate(d).getTime() - t0) / (t1 - t0 || 1)) * (W - padL - padR);
      const y = (v) => padT + (1 - (v - lo) / (hi - lo)) * (H - padT - padB);
      const svg = svgEl('svg', { viewBox: `0 0 ${W} ${H}`, height: H, role: 'img', 'aria-label': opt.label || 'Line chart' }, el);
      for (let i = 0; i <= 3; i++) {
        const v = lo + ((hi - lo) * i) / 3;
        svgEl('line', { x1: 0, x2: W - padR, y1: y(v), y2: y(v), stroke: css('--rule') }, svg);
        const t = svgEl('text', { x: W - padR + 8, y: y(v) + 4, fill: css('--muted'), 'font-size': 11 }, svg); t.textContent = fmt(v);
      }
      if (opt.zero && lo < 0 && hi > 0) svgEl('line', { x1: 0, x2: W - padR, y1: y(0), y2: y(0), stroke: css('--axis') }, svg);
      const t = (s, anchor, xx) => { const e = svgEl('text', { x: xx, y: H - 6, fill: css('--muted'), 'font-size': 11, 'text-anchor': anchor }, svg); e.textContent = s; };
      t(fdate(series[0].pts[0][0], true), 'start', 0); t(fdate(series[0].pts[series[0].pts.length - 1][0], true), 'end', W - padR);
      series.forEach((s) => {
        const d = s.pts.map((p, i) => (i ? 'L' : 'M') + x(p[0]).toFixed(1) + ',' + y(p[1]).toFixed(1)).join('');
        if (s.area) svgEl('path', { d: d + `L${x(s.pts[s.pts.length - 1][0])},${y(opt.zero ? 0 : lo)}L${x(s.pts[0][0])},${y(opt.zero ? 0 : lo)}Z`, fill: s.area }, svg);
        svgEl('path', { d, fill: 'none', stroke: s.color || css('--fg'), 'stroke-width': s.w || 1.5 }, svg);
      });
      const guide = svgEl('line', { y1: padT, y2: H - padB, stroke: css('--axis'), visibility: 'hidden' }, svg);
      const main = series[0].pts;
      svg.addEventListener('mousemove', (e) => {
        const r = svg.getBoundingClientRect(); const mx = ((e.clientX - r.left) / r.width) * W;
        let best = 0, bd = Infinity;
        for (let i = 0; i < main.length; i++) { const dd = Math.abs(x(main[i][0]) - mx); if (dd < bd) { bd = dd; best = i; } }
        const p = main[best]; guide.setAttribute('x1', x(p[0])); guide.setAttribute('x2', x(p[0])); guide.setAttribute('visibility', 'visible');
        const rows = series.map((s) => { const q = s.pts.reduce((a, b) => (Math.abs(toDate(b[0]) - toDate(p[0])) < Math.abs(toDate(a[0]) - toDate(p[0])) ? b : a)); return (series.length > 1 ? esc(s.name) + ' ' : '') + fmt(q[1]); });
        showTip(e, fdate(p[0], true) + ' · ' + rows.join(' · '));
      });
      svg.addEventListener('mouseleave', () => { guide.setAttribute('visibility', 'hidden'); hideTip(); });
    });
  }

  /** Columns around a zero axis. groups: [{label, values:[v1, v2]}], colors per value index */
  function columns(el, groups, colors, opt = {}) {
    if (!groups.length) { el.innerHTML = '<div class="empty">No data yet.</div>'; return; }
    const H = opt.height || 240, fmt = opt.fmt || ((v) => num(v, 0));
    responsive(el, (W) => {
      const padB = 22;
      const all = groups.flatMap((g) => g.values.filter(isNum));
      const m = Math.max(1e-9, ...all.map(Math.abs));
      const hasNeg = all.some((v) => v < 0), hasPos = all.some((v) => v > 0);
      const top = 6, base = hasNeg && hasPos ? (H - padB) / 2 : hasNeg ? top : H - padB;
      const scale = (hasNeg && hasPos ? (H - padB) / 2 - top : H - padB - top) / m;
      const svg = svgEl('svg', { viewBox: `0 0 ${W} ${H}`, height: H, role: 'img', 'aria-label': opt.label || 'Column chart' }, el);
      const gw = W / groups.length, k = groups[0].values.length, bw = Math.max(2, Math.min(28, (gw * 0.72) / k));
      svgEl('line', { x1: 0, x2: W, y1: base, y2: base, stroke: css('--axis') }, svg);
      groups.forEach((g, i) => {
        g.values.forEach((v, jx) => {
          if (!isNum(v)) return;
          const h = Math.abs(v) * scale, x0 = i * gw + (gw - bw * k) / 2 + jx * bw;
          const r = svgEl('rect', { x: x0, y: v >= 0 ? base - h : base, width: bw - 1, height: Math.max(1, h), fill: typeof colors[jx] === 'function' ? colors[jx](v) : colors[jx] }, svg);
          r.addEventListener('mousemove', (e) => showTip(e, esc(g.label) + ' · ' + esc((opt.names || [])[jx] || '') + ' ' + fmt(v)));
          r.addEventListener('mouseleave', hideTip);
        });
        const every = Math.ceil(groups.length / Math.max(1, Math.floor(W / 64)));
        if (i % every === 0) { const t = svgEl('text', { x: i * gw + gw / 2, y: H - 6, fill: css('--muted'), 'font-size': 11, 'text-anchor': 'middle' }, svg); t.textContent = g.label; }
      });
    });
  }

  // ---------- UI pieces ----------
  const tabs = (items, cur, act) => '<div class="tabs" role="group">' + items.map((x) => `<button class="tab${x === cur ? ' on' : ''}" data-act="${act}" data-val="${esc(x)}">${esc(x)}</button>`).join('') + '</div>';
  const seg = (items, cur, act, label) => `<div class="seg" role="group" aria-label="${label}">` + items.map((x) => `<button class="${x === cur ? 'on' : ''}" data-act="${act}" data-val="${esc(x)}">${esc(x)}</button>`).join('') + '</div>';
  const srcLink = (id, extra) => { const s = D.srcById[id]; if (!s) return ''; return `<a href="#sources">${esc(s.publisher)}</a>${s.as_of ? ' · as of ' + fdate(s.as_of, true) : ''}${s.status !== 'ok' ? ' <span class="stale">' + (s.status === 'stale' ? 'last good data' : 'unavailable') + '</span>' : ''}${extra || ''}`; };
  function spark(vals, w = 96, h = 24) {
    if (!vals || vals.length < 2) return '';
    const lo = Math.min(...vals), hi = Math.max(...vals) || 1;
    const p = vals.map((v, i) => ((i / (vals.length - 1)) * w).toFixed(1) + ',' + (h - 2 - ((v - lo) / (hi - lo || 1)) * (h - 4)).toFixed(1)).join(' ');
    const col = vals[vals.length - 1] >= vals[0] ? 'var(--in)' : 'var(--out)';
    return `<svg width="${w}" height="${h}" viewBox="0 0 ${w} ${h}" aria-hidden="true"><polyline points="${p}" fill="none" stroke="${col}" stroke-width="1.4"/></svg>`;
  }

  // ---------- pages ----------
  function pageFlows() {
    const regions = ['Global', 'India', 'United States', 'Japan'];
    const wins = ['Latest', '3M', '6M', '12M'];
    const b = board(ST.region, ST.win).sort((a, z) => z.v - a.v);
    const ok = D.sources.filter((s) => s.status === 'ok').length;
    let html = `<section class="lede" aria-labelledby="lede">
      <div class="meta-line"><span>Refreshed ${esc(new Date(D.meta.generated).toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short', timeZone: 'Asia/Kolkata' }))} IST</span><span>${ok} of ${D.sources.length} sources current</span><span>Daily · weekly · monthly</span></div>
      <h1 id="lede" class="big">${headline(ST.region, ST.win)}</h1>
      <p>A daily read of where capital is going across asset classes and regions, built only from official and issuer-published data. Every figure shows its source and date.</p>
    </section>
    <section class="bar-filters" aria-label="Filters">${tabs(regions, ST.region, 'region')}${seg(wins, ST.win, 'win', 'Time window')}</section>
    <section class="kpis" aria-label="Key signals">${kpis()}</section>`;

    // 01 flows
    const m = Math.max(1e-9, ...b.map((c) => Math.abs(c.v)));
    html += `<section class="sec split" aria-labelledby="s1"><div class="side"><span class="num">01</span><h2 id="s1">Net flows by asset class</h2>
      <p>${ST.region === 'India' ? 'Mutual-fund net inflows by category (AMFI) and foreign portfolio investment (NSDL), ₹ crore.' : ST.region === 'Japan' ? 'Weekly cross-border portfolio flows from Japan’s Ministry of Finance, ¥ bn.' : 'US mutual fund and ETF flows by category (ICI), money-market funds, and spot crypto ETFs. US$ bn.'}
      ${ST.win !== 'Latest' ? ' Summed over the window.' : ''}</p>
      <div class="legend"><span><i class="sw" style="background:var(--in)"></i>Arriving</span><span><i class="sw" style="background:var(--out)"></i>Leaving</span></div></div>
      <div class="body">${b.length ? b.map((c) => `<div class="fbar"><span class="n">${esc(c.name)}<small>${esc(c.source)} · ${esc(c.label || '')}</small></span>
        <span class="track"><span class="ax"></span><span class="b" style="${c.v >= 0 ? 'left' : 'right'}:50%;width:${Math.max(0.6, (Math.abs(c.v) / m) * 50).toFixed(1)}%;background:var(--${c.v >= 0 ? 'in' : 'out'})"></span></span>
        <span class="v ${cls(c.v)}">${flow(c.v, c.unit)}</span></div>`).join('') : '<div class="empty">No flow data for this region yet. Check the Sources page for status.</div>'}</div></section>`;

    // 02 India
    html += `<section class="sec split" aria-labelledby="s2"><div class="side"><span class="num">02</span><h2 id="s2">India: foreign vs domestic money</h2><div id="india-side"></div></div><div class="body"><div id="india-chart" class="chart"></div></div></section>`;
    // 03 positioning
    html += `<section class="sec split" aria-labelledby="s3"><div class="side"><span class="num">03</span><h2 id="s3">Where speculative money is leaning</h2>
      <p>Net position of large speculators (non-commercials) in futures, as a share of open interest. Weekly, CFTC.</p>
      <p class="note">${srcLink('cftc')}</p></div><div class="body" id="pos"></div></section>`;
    // 04 table
    html += `<section class="sec" aria-labelledby="s4"><div class="head-row"><div class="t"><span class="num">04</span><h2 id="s4">Returns and quality</h2></div>
      <div class="tools">${tabs(['Returns', 'Risk', 'Trend'], ST.view, 'view')}<a href="#assets">All ${D.assets.length} assets →</a></div></div>
      <div class="tbl-wrap">${assetTable(homeAssets(), ST.view, false)}</div></section>`;
    $main.innerHTML = html;
    drawIndia();
    drawPositioning(document.getElementById('pos'));
  }

  function kpis() {
    const f = D.flows || {};
    const out = [];
    const cat = (region, name) => (((f.board || {})[region]) || []).find((c) => c.name === name);
    const add = (l, v, s, c) => out.push(`<div class="kpi"><span class="l">${esc(l)}</span><span class="v ${c || ''}">${v}</span><span class="s">${s}</span></div>`);
    const win = (c) => (c ? windowValue(c, ST.win) : { v: null });
    if (ST.region === 'India') {
      const liq = ['Liquid funds', 'Overnight funds', 'Money-market funds'].map((n) => win(cat('India', n))).filter((x) => isNum(x.v));
      const lv = liq.reduce((s, x) => s + x.v, 0);
      if (liq.length) add('Cash-like funds (liquid, overnight, money market)', flow(lv, '₹ cr'), esc(liq[0].label) + ' · AMFI', cls(lv));
      const g = win(cat('India', 'Gold ETFs')); if (isNum(g.v)) add('Gold ETFs', flow(g.v, '₹ cr'), esc(g.label) + ' · AMFI', cls(g.v));
      const fe = win(cat('India', 'Foreign investors: equity')); if (isNum(fe.v)) add('Foreign investors in Indian equity', flow(fe.v, '₹ cr'), esc(fe.label) + ' · NSDL', cls(fe.v));
      const eqNames = ['Large-cap equity', 'Mid-cap equity', 'Small-cap equity', 'Flexi-cap equity', 'Sectoral & thematic', 'Index funds'];
      const eq = eqNames.map((n) => win(cat('India', n))).filter((x) => isNum(x.v)); const ev = eq.reduce((s, x) => s + x.v, 0);
      if (eq.length) add('Domestic equity funds', flow(ev, '₹ cr'), esc(eq[0].label) + ' · AMFI', cls(ev));
    } else if (ST.region === 'Japan') {
      (((f.board || {}).Japan) || []).forEach((c) => { const w = win(c); add(c.name, flow(w.v, c.unit), esc(w.label) + ' · Japan MOF', cls(w.v)); });
    } else {
      const mmf = (f.mmf || []);
      if (mmf.length) { const l = mmf[mmf.length - 1]; const w = win(cat('Global', 'Money-market funds')); add('US money-market fund assets', flow(l.total_bn, 'US$ bn', false), (ST.win === 'Latest' ? 'week to ' + fdate(l.date) : esc(w.label)) + ' ' + flow(w.v, 'US$ bn') + ' · ICI', ''); }
      const rrp = ((D.cash.series || {}).RRPONTSYD || {}).points; if (rrp && rrp.length) add('Fed reverse repo (idle cash)', flow(rrp[rrp.length - 1][1], 'US$ bn', false), fdate(rrp[rrp.length - 1][0], true) + ' · Federal Reserve', '');
      const be = win(cat('Global', 'Bitcoin ETFs')); if (isNum(be.v)) add('Spot Bitcoin ETFs', flow(be.v, 'US$ bn'), esc(be.label) + ' · Farside', cls(be.v));
      const ue = win(cat('Global', 'US equity funds')); if (isNum(ue.v)) add('US equity funds', flow(ue.v, 'US$ bn'), esc(ue.label) + ' · ICI', cls(ue.v));
    }
    return out.join('') || '<div class="kpi"><span class="l">Waiting for data</span><span class="v">—</span><span class="s">See Sources</span></div>';
  }

  function drawIndia() {
    const side = document.getElementById('india-side'), el = document.getElementById('india-chart');
    const f = D.flows || {};
    const nse = (f.nse || []).filter((r) => isNum(r.fii) || isNum(r.dii));
    let groups, names, unitNote, src;
    if (nse.length >= 8) {
      const rows = nse.slice(-30);
      groups = rows.map((r) => ({ label: fdate(r.date), values: [r.dii, r.fii] }));
      names = ['Domestic institutions', 'Foreign investors']; unitNote = 'Daily net buying in the cash market, ₹ crore, last ' + rows.length + ' sessions.'; src = srcLink('nse');
      const sd = rows.reduce((s, r) => s + (r.dii || 0), 0), sf = rows.reduce((s, r) => s + (r.fii || 0), 0);
      side.innerHTML = `<p>${unitNote}</p><div><div class="kv"><span>Domestic institutions</span><span class="v ${cls(sd)}">${flow(sd, '₹ cr')}</span></div><div class="kv"><span>Foreign investors</span><span class="v ${cls(sf)}">${flow(sf, '₹ cr')}</span></div></div><p class="note">${src}</p>`;
    } else {
      const fpi = Object.fromEntries((f.nsdl_monthly || []).map((r) => [r.date, r.equity]));
      const eqNames = ['Large-cap equity', 'Mid-cap equity', 'Small-cap equity', 'Flexi-cap equity', 'Sectoral & thematic', 'Index funds'];
      const mf = {};
      (f.amfi || []).forEach((r) => { mf[r.date] = eqNames.reduce((s, n) => s + (isNum(r[n]) ? r[n] : 0), 0); });
      const keys = [...new Set([...Object.keys(fpi), ...Object.keys(mf)])].sort().slice(-12);
      groups = keys.map((k) => ({ label: fdate(k).split(' ')[0], values: [mf[k], fpi[k]] }));
      names = ['Domestic equity funds', 'Foreign investors (equity)'];
      const sd = keys.reduce((s, k) => s + (mf[k] || 0), 0), sf = keys.reduce((s, k) => s + (fpi[k] || 0), 0);
      side.innerHTML = `<p>Monthly net flows into Indian equities, ₹ crore: domestic equity mutual funds (AMFI) vs foreign portfolio investors (NSDL). ${nse.length ? 'The daily NSE view appears once ' + (8 - nse.length) + ' more sessions are collected.' : ''}</p>
        <div><div class="kv"><span>Domestic equity funds, ${keys.length} months</span><span class="v ${cls(sd)}">${flow(sd, '₹ cr')}</span></div><div class="kv"><span>Foreign investors, ${keys.length} months</span><span class="v ${cls(sf)}">${flow(sf, '₹ cr')}</span></div></div>
        <p class="note">${srcLink('amfi')}<br>${srcLink('nsdl_monthly')}</p>`;
    }
    side.insertAdjacentHTML('afterbegin', `<div class="legend"><span><i class="sw" style="background:var(--in)"></i>${esc(names[0])}</span><span><i class="sw" style="background:var(--out)"></i>${esc(names[1])}</span></div>`);
    columns(el, groups, [css('--in'), css('--out')], { names, fmt: (v) => flow(v, '₹ cr'), height: 260, label: 'Foreign versus domestic flows' });
  }

  function drawPositioning(el, only) {
    let xs = (D.flows || {}).cftc || [];
    if (only) xs = xs.filter((x) => only.includes(x.name));
    if (!xs.length) { el.innerHTML = '<div class="empty">No positioning data yet.</div>'; return; }
    xs = xs.slice().sort((a, z) => z.net_pct_oi - a.net_pct_oi);
    const m = Math.max(0.05, ...xs.map((x) => Math.abs(x.net_pct_oi)));
    el.innerHTML = `<div class="pos-row muted" style="min-height:36px;font-size:12px;border-top:0"><span>Market</span><span>Net long / short, % of open interest</span><span style="text-align:right">4-week change</span><span class="hide-s" style="text-align:right">vs 1-year range</span></div>` +
      xs.map((x) => `<div class="pos-row"><span>${esc(x.name)}</span><span class="track"><span class="ax"></span><span class="b" style="${x.net_pct_oi >= 0 ? 'left' : 'right'}:50%;width:${((Math.abs(x.net_pct_oi) / m) * 50).toFixed(1)}%;background:var(--${x.net_pct_oi >= 0 ? 'in' : 'out'})"></span></span>
      <span style="text-align:right" class="${cls(x.chg4w_pct_oi)}">${pct(x.chg4w_pct_oi, 1)}</span><span class="hide-s muted" style="text-align:right">${isNum(x.pctile_1y) ? Math.round(x.pctile_1y * 100) + 'th pctile' : '—'}</span></div>`).join('');
  }

  const HOME = { Global: ['acwi', 'sp500', 'nifty50', 'semis', 'ust2', 'gold', 'brent', 'btc', 'dxy', 'bdc'], India: ['nifty50', 'niftybank', 'niftyit', 'niftymid', 'indgilt', 'goldinr', 'embassy', 'usdinr'], 'United States': ['sp500', 'nasdaq100', 'semis', 'russell2000', 'tbills', 'ust20', 'usig', 'ushy', 'usreit', 'bdc'], Japan: ['nikkei', 'usdjpy', 'acwi', 'gold'] };
  const homeAssets = () => (HOME[ST.region] || HOME.Global).map((id) => D.byId[id]).filter(Boolean);

  const COLS = {
    Returns: [['1M', '1 month'], ['3M', '3 months'], ['YTD', 'Year to date'], ['1Y', '1 year'], ['3Y', '3 years, ann.'], ['5Y', '5 years, ann.']],
    Risk: [['vol', 'Volatility'], ['max_dd', 'Max drawdown'], ['sharpe', 'Sharpe'], ['sortino', 'Sortino'], ['calmar', 'Calmar'], ['beta', 'Beta to world']],
    Trend: [['vs_200dma', 'vs 200-day avg'], ['current_dd', 'From peak'], ['up_months', 'Positive months'], ['corr', 'Correlation to world'], ['spark', '1 year']],
  };
  function cellVal(a, key, view, usd) {
    const r = usd && a.ret_usd ? a.ret_usd : a.ret || {};
    const k = usd && a.risk_usd ? a.risk_usd : a.risk || {};
    if (view === 'Returns') return r[key];
    if (key === 'spark') return null;
    return k[key];
  }
  function cellHtml(a, key, view, usd) {
    if (key === 'spark') return spark(a.spark);
    const v = cellVal(a, key, view, usd);
    if (view === 'Returns' || ['max_dd', 'current_dd', 'vs_200dma'].includes(key)) return `<span class="${view === 'Returns' || key === 'vs_200dma' ? cls(v) : ''}">${pct(v)}</span>`;
    if (['vol', 'up_months'].includes(key)) return pct(v, 1, false);
    return num(v, 2);
  }
  function assetTable(list, view, sortable) {
    const usd = ST.ccy === 'USD';
    const cols = COLS[view];
    if (sortable && ST.sort && cols.some((c) => c[0] === ST.sort)) {
      list = list.slice().sort((a, z) => { const x = cellVal(a, ST.sort, view, usd), y = cellVal(z, ST.sort, view, usd); return (isNum(y) ? y : -1e9) * ST.sortDir - (isNum(x) ? x : -1e9) * ST.sortDir; });
    }
    if (!list.length) return '<div class="empty">No assets match.</div>';
    const th = (c) => sortable && c[0] !== 'spark' ? `<th><button data-act="sort" data-val="${c[0]}">${esc(c[1])}${ST.sort === c[0] ? (ST.sortDir < 0 ? ' ↓' : ' ↑') : ''}</button></th>` : `<th>${esc(c[1])}</th>`;
    return `<table class="t"><thead><tr><th>Asset</th>${cols.map(th).join('')}</tr></thead><tbody>` +
      list.map((a) => `<tr><td><a href="#asset-${esc(a.id)}">${esc(a.name)} <span class="muted">→</span></a>${a.stale ? '<span class="stale">stale</span>' : ''}<span class="sub">${esc(a.region)} · ${esc(a.cls)}${usd && a.ccy !== 'USD' && a.ret_usd ? ' · in USD' : ''}</span></td>${cols.map((c) => `<td>${cellHtml(a, c[0], view, usd)}</td>`).join('')}</tr>`).join('') + '</tbody></table>';
  }

  function pageAssets() {
    const classes = ['All', ...new Set(D.assets.map((a) => a.cls))];
    const regions = ['All', ...new Set(D.assets.map((a) => a.region))];
    const q = ST.q.toLowerCase();
    const list = D.assets.filter((a) => (ST.cls === 'All' || a.cls === ST.cls) && (ST.aregion === 'All' || a.region === ST.aregion) && (!q || (a.name + ' ' + a.ticker + ' ' + (a.theme || '')).toLowerCase().includes(q)));
    $main.innerHTML = `<section class="lede" style="padding:64px 0 40px"><span class="num">Screener</span><h1 class="big" style="font-size:clamp(32px,4vw,48px)">Every tracked asset, one table.</h1>
      <p>Returns in local currency or US dollars. Risk metrics use three years of daily data. Risk-free rate: US 3-month T-bill ${pct(D.rf.USD, 2, false)}, India T-bill ${pct(D.rf.INR, 2, false)}.</p></section>
      <section class="bar-filters" aria-label="Filters">${tabs(classes, ST.cls, 'cls')}</section>
      <section class="bar-filters" aria-label="More filters"><div class="tools">
        <label class="muted" style="font-size:13px">Region <select class="select" data-act="aregion">${regions.map((r) => `<option${r === ST.aregion ? ' selected' : ''}>${esc(r)}</option>`).join('')}</select></label>
        <label class="muted" style="font-size:13px">Search <input class="search" type="search" data-act="q" value="${esc(ST.q)}" placeholder="Nifty, gold, uranium…"></label></div>
        <div class="tools">${tabs(['Returns', 'Risk', 'Trend'], ST.aView, 'aview')}${seg(['Local', 'USD'], ST.ccy, 'ccy', 'Currency')}</div></section>
      <section class="sec" style="padding-top:32px"><p class="note" style="margin-bottom:16px">${list.length} assets · prices ${srcLink('yahoo')} · click a column to sort</p><div class="tbl-wrap">${assetTable(list, ST.aView, true)}</div></section>`;
    const inp = $main.querySelector('input[data-act="q"]');
    if (inp && ST._focusQ) { inp.focus(); inp.setSelectionRange(inp.value.length, inp.value.length); }
  }

  const RISK_HELP = [
    ['vol', 'Annualised volatility', 'How much it swings in a typical year', (v) => pct(v, 1, false)],
    ['max_dd', 'Maximum drawdown', 'Worst fall from a peak in the last three years', (v) => pct(v)],
    ['current_dd', 'Below its peak today', 'Distance from the three-year high', (v) => pct(v)],
    ['sharpe', 'Sharpe ratio', 'Return above the T-bill rate per unit of volatility. Above 1 is strong', (v) => num(v)],
    ['sortino', 'Sortino ratio', 'Like Sharpe, but only counts downside swings', (v) => num(v)],
    ['calmar', 'Calmar ratio', 'Annual return divided by the maximum drawdown', (v) => num(v)],
    ['beta', 'Beta to world equities', 'How much it moves when MSCI ACWI moves 1% (weekly data)', (v) => num(v)],
    ['corr', 'Correlation to world equities', '1 moves together, 0 unrelated, −1 opposite', (v) => num(v)],
    ['up_months', 'Positive months', 'Share of months that ended higher', (v) => pct(v, 0, false)],
    ['vs_200dma', 'Versus 200-day average', 'Above zero means the long-term trend is up', (v) => pct(v)],
  ];
  const CFTC_MAP = { gold: 'Gold', goldinr: 'Gold', goldminers: 'Gold', silver: 'Silver', silverinr: 'Silver', brent: 'Crude oil (WTI)', copper: 'Copper', sp500: 'S&P 500 e-mini', nasdaq100: 'Nasdaq 100 e-mini', ust20: 'US 10-year note', ust2: 'US 10-year note', dxy: 'US dollar index', btc: 'Bitcoin (CME)', agri: 'Corn' };
  const FLOW_MAP = { btc: ['Global', ['Bitcoin ETFs']], eth: ['Global', ['Ether ETFs']], sp500: ['Global', ['US equity funds']], nasdaq100: ['Global', ['US equity funds']], acwi: ['Global', ['World equity funds', 'US equity funds']], usig: ['Global', ['Taxable bond funds']], ushy: ['Global', ['Taxable bond funds']], tbills: ['Global', ['Money-market funds']], nifty50: ['India', ['Foreign investors: equity', 'Large-cap equity', 'Index funds']], niftymid: ['India', ['Mid-cap equity', 'Small-cap equity']], goldinr: ['India', ['Gold ETFs']], indgilt: ['India', ['Gilt funds', 'Foreign investors: debt']], nikkei: ['Japan', ['Foreigners buying Japanese stocks']] };

  async function pageAsset(id) {
    const a = D.byId[id];
    if (!a) { $main.innerHTML = '<p class="loading">Asset not found. <a href="#assets">Back to all assets</a></p>'; return; }
    let ser = {};
    try { ser = await j('series/' + id + '.json'); } catch (e) { ser = {}; }
    const usd = ST.ccy === 'USD' && a.ccy !== 'USD' && ser.usd;
    const r = usd ? a.ret_usd || {} : a.ret || {};
    const k = usd ? a.risk_usd || {} : a.risk || {};
    const chg = a.last / a.prev - 1;
    const lbls = [['1D', '1 day'], ['1W', '1 week'], ['1M', '1 month'], ['3M', '3 months'], ['6M', '6 months'], ['YTD', 'Year to date'], ['1Y', '1 year'], ['3Y', '3 years, ann.'], ['5Y', '5 years, ann.'], ['10Y', '10 years, ann.']];
    const dec = a.decomp && D.decomp ? D.decomp[a.decomp] : null;
    let html = `<section class="a-head"><a href="#assets" class="muted" style="font-size:13px;text-decoration:none">← ${esc(a.region)} / ${esc(a.cls)}</a>
      <div class="row"><div><h1>${esc(a.name)}</h1><div class="px"><span class="p">${a.last.toLocaleString('en-IN', { maximumFractionDigits: 2 })}</span><span class="${cls(chg)}">${pct(chg, 2)}</span><span class="muted" style="font-size:13px">Close ${fdate(a.last_date, true)} · ${esc(a.ticker)} · ${esc(a.ccy)}${a.stale ? ' · <span class="stale">stale</span>' : ''}</span></div></div>
      ${a.ccy !== 'USD' && a.ret_usd ? seg(['Local', 'USD'], ST.ccy, 'ccy', 'Currency') : ''}</div></section>
      <section class="strip" aria-label="Returns by period">${lbls.filter((l) => r[l[0]] !== undefined).map((l) => `<div><span class="l">${l[1]}</span><span class="v ${cls(r[l[0]])}">${pct(r[l[0]])}</span></div>`).join('')}</section>
      <section class="sec" aria-labelledby="c1"><div class="head-row"><div class="t"><span class="num">01</span><h2 id="c1">Price and drawdown${usd ? ' (in US$)' : ''}</h2></div>${seg(['6M', '1Y', '3Y', '5Y', 'Max'], ST.range, 'range', 'Chart range')}</div>
      <div id="pchart" class="chart"></div><div id="ddchart" class="chart" style="margin-top:8px"></div><p class="note" style="margin-top:12px">Prices ${srcLink('yahoo')}. Since ${fdate(a.start_date, true)}.</p></section>`;
    html += `<div class="sec two"><section aria-labelledby="c2"><div class="t" style="display:flex;flex-direction:column;gap:12px"><span class="num">02</span><h2 id="c2">Risk and quality</h2>
      <span class="muted" style="font-size:14px">Three years of daily data · risk-free: ${usd ? 'US T-bill' : esc(a.rf_note || 'n/a')}</span></div>
      <div>${a.risk ? RISK_HELP.filter((x) => k[x[0]] !== undefined).map((x) => `<div class="kv"><span>${x[1]}</span><span class="v">${x[3](k[x[0]])}</span><span class="h">${x[2]}</span></div>`).join('') : '<div class="empty">Risk metrics are not meaningful for this series.</div>'}</div></section>
      <section aria-labelledby="c3"><div class="t" style="display:flex;flex-direction:column;gap:12px"><span class="num">03</span><h2 id="c3">Was the return earned?</h2>
      <span class="muted" style="font-size:14px;line-height:1.6">Each year's return split into earnings growth, change in valuation (P/E) and dividends. Gains from earnings tend to last longer than gains from re-rating.</span></div>
      ${dec ? decompHtml(dec, a) : `<div class="empty">${a.cls === 'Equities' ? 'A free, regularly published earnings series exists for the Nifty 50 and S&P 500, so the split is shown for those two indices.' : 'Not applicable: this asset has no earnings.'}</div>`}</section></div>`;
    const fm = FLOW_MAP[id], cm = CFTC_MAP[id];
    if (fm || cm) {
      html += `<section class="sec" aria-labelledby="c4"><div class="head-row"><div class="t"><span class="num">04</span><h2 id="c4">Who is buying and selling</h2></div></div><div class="grid-charts">`;
      if (fm) (((D.flows || {}).board || {})[fm[0]] || []).filter((c) => fm[1].includes(c.name)).forEach((c, i) => { html += `<div class="card-c"><h3>${esc(c.name)}</h3><span class="note">${esc(c.freq)} net flow, ${esc(c.unit)} · ${esc(c.source)}</span><div class="chart" id="fl${i}"></div></div>`; });
      if (cm) html += `<div class="card-c"><h3>Speculative positioning: ${esc(cm)}</h3><span class="note">Net non-commercial position, % of open interest · CFTC weekly</span><div class="chart" id="cf"></div></div>`;
      html += '</div></section>';
    }
    $main.innerHTML = html;

    const pts = (usd ? ser.usd : ser.local) || [];
    const days = { '6M': 182, '1Y': 365, '3Y': 1096, '5Y': 1826, Max: 1e6 }[ST.range];
    const lastT = pts.length ? toDate(pts[pts.length - 1][0]) : 0;
    const win = pts.filter((p) => lastT - toDate(p[0]) <= days * 864e5);
    let peak = -Infinity; const dd = win.map((p) => { peak = Math.max(peak, p[1]); return [p[0], p[1] / peak - 1]; });
    lineChart(document.getElementById('pchart'), [{ pts: win, color: css('--fg'), name: a.name }], { height: 280, fmt: (v) => v.toLocaleString('en-IN', { maximumFractionDigits: v > 100 ? 0 : 2 }), label: a.name + ' price' });
    lineChart(document.getElementById('ddchart'), [{ pts: dd, color: css('--out'), area: css('--out-soft'), name: 'Drawdown' }], { height: 110, fmt: (v) => pct(v, 0), zero: true, label: 'Drawdown' });
    if (fm) (((D.flows || {}).board || {})[fm[0]] || []).filter((c) => fm[1].includes(c.name)).forEach((c, i) => {
      const h = c.history.slice(c.freq === 'Daily' ? -60 : -24);
      columns(document.getElementById('fl' + i), h.map((p) => ({ label: fdate(p[0]).split(' ').slice(0, 2).join(' '), values: [p[1]] })), [signColor], { fmt: (v) => flow(v, c.unit), names: [''], height: 180 });
    });
    if (cm) { const x = ((D.flows || {}).cftc || []).find((c) => c.name === cm); lineChart(document.getElementById('cf'), x ? [{ pts: x.history, color: css('--in'), area: css('--in-soft'), name: cm }] : [], { height: 180, fmt: (v) => pct(v, 0), zero: true }); }
  }

  function decompHtml(d, a) {
    const rows = d.rows || [];
    const m = Math.max(0.05, ...rows.flatMap((r) => [Math.abs(r.eps_growth) + Math.abs(r.pe_change) + Math.abs(r.dividend)]));
    const sc = 48 / m;
    const seg = (left, w, color) => `<span style="left:${left.toFixed(1)}%;width:${Math.abs(w).toFixed(1)}%;background:${color}"></span>`;
    const bars = rows.map((r) => {
      const e = r.eps_growth * sc, p = r.pe_change * sc, dv = r.dividend * sc;
      let pos = 50, neg = 50, parts = '';
      const put = (w, color) => { if (w >= 0) { parts += seg(pos, w, color); pos += w; } else { neg += w; parts += seg(neg, w, color); } };
      put(e, 'var(--in)'); put(p, 'var(--out)'); put(dv, 'var(--neutral)');
      return `<div class="dec" title="EPS ${pct(r.eps_growth)} · P/E ${pct(r.pe_change)} · dividends ${pct(r.dividend)}"><span class="muted" style="font-size:14px">${esc(r.year)}</span><div class="tr"><span class="ax" style="left:50%;width:1px;background:var(--axis);top:-12px;height:32px"></span>${parts}</div><span style="text-align:right" class="${cls(r.total)}">${pct(r.total)}</span></div>`;
    }).join('');
    return `<div class="legend"><span><i class="sw" style="background:var(--in);height:8px"></i>EPS growth</span><span><i class="sw" style="background:var(--out);height:8px"></i>P/E change</span><span><i class="sw" style="background:var(--neutral);height:8px"></i>Dividends</span></div>
      <div>${bars}</div>
      <div class="kv" style="border-top:1px solid var(--fg)"><span>Trailing P/E</span><span class="v">${num(d.pe, 1)}×</span><span class="h">5-year range ${num(d.pe_5y_min, 1)}×–${num(d.pe_5y_max, 1)}×, median ${num(d.pe_5y_median, 1)}× · ${esc(d.method)} · ${srcLink(a.decomp === 'nifty50' ? 'nifty_pe' : 'sp500_eps')}</span></div>`;
  }

  function pageCash() {
    const s = D.cash.series || {};
    const cards = [];
    const add = (id, title, pts, fmt, sub, src) => cards.push({ id, title, pts, fmt, sub, src });
    if (D.cash.ici_mmf && D.cash.ici_mmf.length) add('mmf', 'US money-market fund assets', D.cash.ici_mmf, (v) => flow(v, 'US$ bn', false), 'Weekly · history builds from the first refresh', srcLink('ici_mmf'));
    [['WRMFNS', (v) => flow(v, 'US$ bn', false)], ['RRPONTSYD', (v) => flow(v, 'US$ bn', false)], ['DPSACBW027SBOG', (v) => flow(v, 'US$ bn', false)], ['WTREGEN', (v) => flow(v, 'US$ bn', false)], ['WALCL', (v) => flow(v, 'US$ bn', false)], ['WMTSECL1', (v) => flow(v, 'US$ bn', false)],
      ['DTB3', (v) => v.toFixed(2) + '%'], ['DGS10', (v) => v.toFixed(2) + '%'], ['BAMLH0A0HYM2', (v) => v.toFixed(2) + '%'], ['BAMLC0A0CM', (v) => v.toFixed(2) + '%'], ['DTWEXBGS', (v) => v.toFixed(1)], ['INTGSTINM193N', (v) => v.toFixed(2) + '%'], ['INDIRLTLT01STM', (v) => v.toFixed(2) + '%']]
      .forEach(([id, fmt]) => { if (s[id]) add(id, s[id].name, s[id].points.filter((p) => p[0] >= (cutoff(3))), fmt, s[id].freq + ' · ' + s[id].unit + ' · FRED ' + id, srcLink('fred')); });
    const liq = ((D.flows || {}).amfi || []).map((r) => [r.date, ['Liquid funds', 'Overnight funds', 'Money-market funds'].reduce((t, n) => t + (isNum(r[n]) ? r[n] : 0), 0)]);
    $main.innerHTML = `<section class="lede" style="padding:64px 0 48px"><span class="num">Cash &amp; liquidity</span><h1 class="big" style="font-size:clamp(32px,4vw,48px)">Where idle money is waiting.</h1>
      <p>When investors step away from risk, the cash shows up here: money-market funds, bank deposits, the Fed’s reverse-repo facility and short-term government bills.</p></section>
      <section class="sec"><div class="grid-charts">${cards.map((c, i) => `<div class="card-c"><h3>${esc(c.title)}</h3><span class="big">${c.pts.length ? c.fmt(c.pts[c.pts.length - 1][1]) : '—'}</span><span class="note">${esc(c.sub)} · ${c.src}</span><div class="chart" id="cc${i}"></div></div>`).join('')}
      <div class="card-c"><h3>India: net flows into cash-like mutual funds</h3><span class="note">Liquid + overnight + money-market funds, ₹ crore, monthly · ${srcLink('amfi')}</span><div class="chart" id="ccl"></div></div></div></section>`;
    cards.forEach((c, i) => lineChart(document.getElementById('cc' + i), [{ pts: c.pts, color: css('--in'), area: css('--in-soft'), name: c.title }], { height: 170, fmt: c.fmt, label: c.title }));
    columns(document.getElementById('ccl'), liq.map((p) => ({ label: fdate(p[0]).split(' ')[0], values: [p[1]] })), [signColor], { fmt: (v) => flow(v, '₹ cr'), names: [''], height: 170 });
  }
  function cutoff(years) { const d = new Date(); d.setFullYear(d.getFullYear() - years); return d.toISOString().slice(0, 10); }

  function pageSources() {
    $main.innerHTML = `<section class="lede" style="padding:64px 0 48px"><span class="num">Sources</span><h1 class="big" style="font-size:clamp(32px,4vw,48px)">Where every number comes from.</h1>
      <p>Refreshed every day at about 07:00 IST. If a source can’t be reached, the site keeps its last good data and marks it here.</p></section>
      <section class="sec" style="padding-top:24px"><div class="tbl-wrap"><table class="t"><thead><tr><th>Source</th><th>Publisher</th><th>Frequency</th><th>Data as of</th><th>Status</th></tr></thead><tbody>
      ${D.sources.map((s) => `<tr><td><a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.name)} ↗</a>${s.message ? `<span class="sub" style="white-space:normal;max-width:420px">${esc(s.message)}</span>` : ''}</td><td>${esc(s.publisher)}</td><td>${esc(s.freq)}</td><td>${fdate(s.as_of, true)}</td><td><span class="badge ${esc(s.status)}">${s.status === 'ok' ? 'Current' : s.status === 'stale' ? 'Last good data' : 'Unavailable'}</span></td></tr>`).join('')}
      </tbody></table></div></section>
      <section class="sec two"><section><h2>Method</h2><div class="note" style="font-size:14px;line-height:1.7">
        <p><b>Returns</b> use adjusted daily closes where available. Periods over one year are annualised. “USD” converts local prices at daily exchange rates.</p>
        <p><b>Volatility</b> is the standard deviation of daily log returns, annualised by the number of trading days. <b>Sharpe</b> and <b>Sortino</b> use the annualised three-year return minus the local T-bill rate. <b>Beta</b> and <b>correlation</b> use weekly returns against MSCI ACWI.</p>
        <p><b>Earnings split</b>: price return = (1 + EPS growth) × (1 + P/E change) − 1, plus the average dividend yield.</p></div></section>
      <section><h2>Limits</h2><div class="note" style="font-size:14px;line-height:1.7">
        <p>Comprehensive global fund-flow databases (EPFR, LSEG Lipper) are paid, so flows here come from official and issuer-published sources: US (ICI), India (AMFI, NSDL, NSE), Japan (MOF), crypto ETFs (Farside) and futures positioning (CFTC).</p>
        <p>Some sources publish only the latest period. For those, history builds up from the first daily refresh.</p>
        <p>Information only, not investment advice.</p></div></section></section>`;
  }

  // =====================================================================
  // Driver map, shock simulator, watchlist
  // =====================================================================
  const M = { loaded: false, overlay: 'This week', view: 'Map', sel: null, trail: [], center: null, shockF: 'brent', shockV: 10, shockCap: 'Large & mid caps', q: '' };
  const SIGNTXT = { '+': 'Pushes up', '-': 'Pushes down', '~': 'Mixed' };
  const symFile = (s) => s.replace(/&/g, '_and_').replace(/\//g, '_');
  const watch = {
    get() { try { return JSON.parse(localStorage.getItem('fs-watch') || '[]'); } catch (e) { return M._w || []; } },
    set(v) { M._w = v; try { localStorage.setItem('fs-watch', JSON.stringify(v)); } catch (e) { /* in-memory only */ } },
    has(s) { return this.get().includes(s); },
    toggle(s) { const w = this.get(); this.set(w.includes(s) ? w.filter((x) => x !== s) : w.concat([s])); },
  };

  async function loadMap() {
    if (M.loaded) return;
    const [g, idx, ex] = await Promise.all([j('graph.json'), j('stocks/index.json'), j('exposure.json').catch(() => null)]);
    M.g = g; M.idx = idx; M.ex = ex;
    M.st = Object.fromEntries((idx.stocks || []).map((s) => [s.s, s]));
    M.loaded = true;
  }
  const stockCache = {};
  async function stockData(sym) {
    if (!stockCache[sym]) stockCache[sym] = await j('stocks/' + symFile(sym) + '.json').catch(() => null);
    return stockCache[sym];
  }

  function moveTxt(m) {
    if (!m) return null;
    const v = isNum(m.w1) ? m.w1 : isNum(m.m1) ? m.m1 : isNum(m.y1) ? m.y1 : null;
    const per = isNum(m.w1) ? '1W' : isNum(m.m1) ? '1M' : 'YoY';
    if (!isNum(v)) return null;
    return { v, txt: (m.unit === 'pp' ? (v > 0 ? '+' : v < 0 ? MINUS : '') + Math.abs(v * 100).toFixed(0) + ' bp' : pct(v, 1)) + ' ' + per };
  }
  const nodeName = (id) => {
    if (id.startsWith('s:')) { const s = M.st[id.slice(2)]; return s ? s.n : id.slice(2); }
    if (id.startsWith('t:')) { const t = M.g.templates[id.slice(2)]; return t ? t.name + ' industry' : id; }
    if (id.startsWith('i:')) return M.g.indices[id.slice(2)] || id;
    return (M.g.nodes[id] || {}).name || id;
  };
  function nodeMove(id) {
    if (id.startsWith('s:')) { const s = M.st[id.slice(2)]; return s && isNum(s.r1w) ? { v: s.r1w, txt: pct(s.r1w) + ' 1W' } : null; }
    if (id.startsWith('i:')) { const a = D.byId[id.slice(2)]; return a && a.ret ? { v: a.ret['1W'], txt: pct(a.ret['1W']) + ' 1W' } : null; }
    if (id.startsWith('t:')) return null;
    return moveTxt((M.g.nodes[id] || {}).move);
  }
  const fmtBeta = (k, b) => (isNum(b) ? (M.g.factors[k] && (M.ex && M.ex.kinds && M.ex.kinds[k] === 'yld') ? num(b * 100, 1) + '% per 1 pp' : num(b, 2)) : '—');

  // Build {center, drivers[], deps[]} for any node id
  async function neighbours(id) {
    const g = M.g; const out = { id, drivers: [], deps: [] };
    const push = (arr, x) => { if (!arr.some((y) => y.id === x.id)) arr.push(x); };
    if (id.startsWith('s:')) {
      const sym = id.slice(2); const d = await stockData(sym) || {}; const meta = M.st[sym] || {};
      out.stock = d; out.name = d.n || meta.n || sym; out.kind = 'Stock · ' + (meta.i || '') + ' · NSE: ' + sym;
      const tp = g.templates[d.t || meta.t] || g.templates.default;
      const sens = d.sens || {};
      push(out.drivers, { id: 'nifty', sign: '+', str: 3, why: 'Overall market direction. Measured market beta ' + num(d.bm, 2) + ': a 1% Nifty move has typically meant ' + num(d.bm, 2) + '% for this stock.', meas: sens.nifty });
      tp.drivers.forEach(([n, sg, st, why]) => push(out.drivers, { id: n, sign: sg, str: st, why, meas: sens[n] }));
      Object.entries(sens).forEach(([k, v]) => { if (k !== 'nifty' && isNum(v.corr) && Math.abs(v.corr) >= 0.3 && !out.drivers.some((x) => x.id === k)) push(out.drivers, { id: k, sign: v.beta >= 0 ? '+' : '-', str: 1, why: 'Not in the industry template, but the price data shows a consistent link (correlation ' + num(v.corr, 2) + ').', meas: v, measuredOnly: true }); });
      push(out.drivers, { id: 't:' + (d.t || meta.t || 'default'), sign: '+', str: 2, why: 'Industry-wide news (pricing, demand, regulation) moves all ' + tp.name.toLowerCase() + ' stocks together.', template: true });
      const w = d.weights || {};
      (d.idx || meta.idx || []).sort((a, z) => (w[z] || 0) - (w[a] || 0)).slice(0, 4).forEach((k) => push(out.deps, { id: 'i:' + k, sign: '+', str: (w[k] || 0) > 0.02 ? 3 : (w[k] || 0) > 0.005 ? 2 : 1, why: 'Member of ' + (g.indices[k] || k) + (isNum(w[k]) ? ' with an approximate weight of ' + pct(w[k], 2, false) + ' (by market cap)' : '') + '. ' + (g.etfs[k] ? g.etfs[k] + ' must buy or sell it as money flows in or out.' : ''), weight: w[k] }));
      (d.peers || []).slice(0, 4).forEach((p) => push(out.deps, { id: 's:' + p.s, sign: '~', str: isNum(p.c) && p.c > 0.6 ? 3 : 2, why: 'Peer in the same industry' + (isNum(p.c) ? '; weekly returns correlation ' + num(p.c, 2) : '') + '. Company news here often moves the peer group.', meas: isNum(p.c) ? { corr: p.c } : null, peer: true }));
      tp.drives.forEach(([n, sg, st, why]) => push(out.deps, { id: n, sign: sg, str: st, why, qual: (g.nodes[n] || {}).kind === 'Qualitative' }));
      if (d.own) push(out.deps, { id: 'own:' + sym, sign: '~', str: 1, label: 'Ownership mix', why: 'Who owns the shares, and so who would be the marginal buyer or seller.', own: d.own });
    } else if (id.startsWith('t:')) {
      const k = id.slice(2); const tp = g.templates[k] || {}; out.name = (tp.name || k) + ' industry'; out.kind = 'Industry template · ' + (tp.n || 0) + ' stocks';
      tp.drivers.forEach(([n, sg, st, why]) => push(out.drivers, { id: n, sign: sg, str: st, why }));
      tp.drives.forEach(([n, sg, st, why]) => push(out.deps, { id: n, sign: sg, str: st, why, qual: (g.nodes[n] || {}).kind === 'Qualitative' }));
      if (tp.sector) push(out.deps, { id: tp.sector, sign: '+', str: 2, why: 'Part of the ' + g.nodes[tp.sector].name + ' index.' });
      (M.idx.stocks || []).filter((s) => s.t === k).sort((a, z) => (z.mc || 0) - (a.mc || 0)).slice(0, 6).forEach((s) => push(out.deps, { id: 's:' + s.s, sign: '+', str: 2, why: 'Company in this industry (largest by market cap first).', member: true }));
    } else if (id.startsWith('i:')) {
      const k = id.slice(2); out.name = g.indices[k] || k; out.kind = 'Index';
      const mem = (M.idx.memberships || {})[k] || []; const tot = mem.reduce((t, s) => t + ((M.st[s] || {}).mc || 0), 0);
      mem.map((s) => M.st[s]).filter(Boolean).sort((a, z) => (z.mc || 0) - (a.mc || 0)).slice(0, 10).forEach((s) => push(out.drivers, { id: 's:' + s.s, sign: '+', str: 2, why: 'Constituent' + (tot && s.mc ? ' with approximate weight ' + pct(s.mc / tot, 1, false) + ' (by market cap)' : '') + '.', weight: tot && s.mc ? s.mc / tot : null }));
      if (g.etfs[k]) push(out.deps, { id: 'etf:' + k, label: g.etfs[k], sign: '+', str: 2, why: 'Passive funds track this index and must trade its constituents as money flows in or out.' });
      push(out.deps, { id: 'dii', sign: '~', str: 1, why: 'Index funds are part of domestic institutional flows.' });
    } else {
      const n = g.nodes[id]; if (!n) return null;
      out.name = n.name; out.kind = n.kind; out.desc = n.desc;
      g.edges.filter((e) => e[1] === id).forEach(([a, , sg, st, why]) => push(out.drivers, { id: a, sign: sg, str: st, why }));
      g.edges.filter((e) => e[0] === id).forEach(([, b, sg, st, why]) => push(out.deps, { id: b, sign: sg, str: st, why, qual: (g.nodes[b] || {}).kind === 'Qualitative' }));
      Object.entries(g.templates).filter((kv) => kv[0] !== 'default').forEach(([k, tp]) => tp.drivers.filter((d) => d[0] === id).forEach(([, sg, st, why]) => push(out.deps, { id: 't:' + k, sign: sg, str: st, why })));
      const top = (g.top || {})[id];
      if (top) [...top.pos.slice(0, 3), ...top.neg.slice(0, 3)].forEach((x) => push(out.deps, { id: 's:' + x.s, sign: x.b >= 0 ? '+' : '-', str: 2, why: 'Among the most sensitive large/mid-cap stocks in the price data (sensitivity ' + fmtBeta(id, x.b) + ', after removing the overall market move).', meas: { beta: x.b }, measuredOnly: true }));
      Object.entries(g.templates).forEach(([k, tp]) => tp.drives.filter((d) => d[0] === id).forEach(([, sg, st, why]) => push(out.drivers, { id: 't:' + k, sign: sg, str: st, why })));
    }
    const rank = (a, z) => (z.str - a.str) || ((Math.abs((z.meas || {}).corr || 0)) - Math.abs((a.meas || {}).corr || 0));
    out.drivers.sort(rank); out.deps.sort(rank);
    return out;
  }

  function windFor(item, side) {
    const mv = item.move; if (!mv || !isNum(mv.v) || item.sign === '~' || side !== 'drivers') return null;
    const up = mv.v > 0; const good = (item.sign === '+') === up;
    return good ? 'Tailwind' : 'Headwind';
  }
  function itemSub(item, side) {
    if (M.overlay === 'Off') return { t: SIGNTXT[item.sign] || 'Linked', c: 'var(--muted)' };
    if (M.overlay === 'Sensitivity') {
      const m = item.meas; if (item.weight) return { t: 'weight ' + pct(item.weight, 2, false), c: 'var(--muted)' };
      if (m && isNum(m.beta)) return { t: 'β ' + num(m.beta, 2) + (isNum(m.corr) ? ' · corr ' + num(m.corr, 2) : ''), c: 'var(--muted)' };
      if (m && isNum(m.corr)) return { t: 'corr ' + num(m.corr, 2), c: 'var(--muted)' };
      return { t: item.qual ? 'qualitative' : 'curated', c: 'var(--muted)' };
    }
    const mv = item.move; if (!mv) return { t: item.qual ? 'qualitative' : 'no live series', c: 'var(--muted)' };
    const w = windFor(item, side);
    return { t: mv.txt + (w ? ' · ' + w.toLowerCase() : ''), c: w ? (w === 'Tailwind' ? 'var(--in-t)' : 'var(--out-t)') : mv.v > 0 ? 'var(--in-t)' : mv.v < 0 ? 'var(--out-t)' : 'var(--muted)' };
  }
  const label = (it) => it.label || nodeName(it.id);
  const canOpen = (id) => !id.startsWith('own:') && !id.startsWith('etf:');

  async function pageMap(id) {
    await loadMap();
    id = id || 'nifty';
    if (M.center !== id) { M.sel = null; const i = M.trail.indexOf(id); M.trail = i >= 0 ? M.trail.slice(0, i + 1) : M.trail.concat([id]).slice(-8); M.center = id; }
    const nb = await neighbours(id);
    if (!nb) { $main.innerHTML = '<p class="loading">Not found. <a href="#map">Back to the map</a></p>'; return; }
    [...nb.drivers, ...nb.deps].forEach((x) => { x.move = nodeMove(x.id); });
    const cMove = id.startsWith('s:') ? (nb.stock && isNum(nb.stock.r1w) ? { v: nb.stock.r1w, txt: pct(nb.stock.r1w) + ' this week' } : null) : nodeMove(id);
    const isStock = id.startsWith('s:'); const sym = isStock ? id.slice(2) : null;
    const narrow = $main.clientWidth < 760;
    const view = narrow ? 'List' : M.view;
    $main.innerHTML = `<section class="bar-filters" aria-label="Map controls" style="padding-top:28px">
      <nav aria-label="Trail" class="trail">${M.trail.map((t, i) => `<a href="#map-${encodeURIComponent(t)}" class="${i === M.trail.length - 1 ? 'on' : ''}">${esc(nodeName(t))}</a>`).join('<span class="muted">→</span>')}</nav>
      <div class="tools"><div class="srch"><label class="muted" style="font-size:13px">Find <input id="mq" class="search" type="search" autocomplete="off" placeholder="Stock, industry, commodity…" value="${esc(M.q)}"></label><div id="mres" class="mres" hidden></div></div>
      ${seg(['This week', 'Sensitivity', 'Off'], M.overlay, 'mov', 'Overlay')}${narrow ? '' : seg(['Map', 'List'], M.view, 'mview', 'View')}</div></section>
      <div class="map-wrap${view === 'List' ? ' list' : ''}"><section class="map-body" aria-label="Driver map"><div id="mapc"></div>
      <div class="legend" style="margin-top:14px;font-size:12px;color:var(--muted)"><span><i class="sw" style="background:var(--in);height:2px"></i>Pushes up</span><span><i class="sw" style="background:var(--out);height:2px"></i>Pushes down</span><span><i class="sw" style="background:var(--neutral);height:2px"></i>Mixed / peer</span><span>Thicker = stronger · dashed = curated, not measured</span></div></section>
      <aside class="map-side" id="mside" aria-live="polite"></aside></div>`;
    const N = view === 'Map' ? 9 : 99;
    const L = nb.drivers.slice(0, N), R = nb.deps.slice(0, N);
    if (view === 'Map') drawRadial(document.getElementById('mapc'), nb, L, R, cMove);
    else drawChain(document.getElementById('mapc'), nb, cMove);
    renderSide(nb, cMove, sym);
    wireSearch();
  }

  function drawRadial(el, nb, L, R, cMove) {
    responsive(el, (W) => {
      const nodeW = Math.min(180, Math.max(140, W * 0.2)), nodeH = 56;
      const rows = Math.max(L.length, R.length, 5);
      const H = Math.max(500, rows * 78 + 60);
      const cx = W / 2, cy = H / 2;
      const box = document.createElement('div'); box.className = 'radial'; box.style.height = H + 'px'; el.appendChild(box);
      const svg = svgEl('svg', { width: W, height: H, viewBox: `0 0 ${W} ${H}`, 'aria-hidden': 'true' }, box);
      const head = document.createElement('div'); head.className = 'radial-head'; head.innerHTML = `<span>← What drives it${nb.drivers.length > L.length ? ' (top ' + L.length + ' of ' + nb.drivers.length + ')' : ''}</span><span>What it drives${nb.deps.length > R.length ? ' (top ' + R.length + ' of ' + nb.deps.length + ')' : ''} →</span>`; el.insertBefore(head, box);
      const place = (list, side) => list.map((it, i) => {
        const n = list.length; const t = n === 1 ? 0.5 : i / (n - 1);
        const span = Math.min(H - 40 - nodeH, (n - 1) * 78);
        const y = cy - span / 2 + t * span;
        const th = (t - 0.5) * Math.PI * 0.7;
        const rx = cx - nodeW / 2 - 4;
        const x = cx + side * (rx * (0.66 + 0.34 * Math.cos(th)));
        return { it, x, y, side };
      });
      const pts = [...place(L, -1), ...place(R, 1)];
      const cW = 190, cH = 96;
      pts.forEach((p) => {
        const sx = cx + p.side * cW / 2, ex = p.x - p.side * nodeW / 2, mx = (sx + ex) / 2;
        const col = p.it.sign === '+' ? css('--in') : p.it.sign === '-' ? css('--out') : css('--neutral');
        const measured = p.it.meas && (isNum(p.it.meas.beta) || isNum(p.it.meas.corr));
        svgEl('path', { d: `M${sx},${cy} C${mx},${cy} ${mx},${p.y} ${ex},${p.y}`, fill: 'none', stroke: col, 'stroke-width': 0.8 + p.it.str * 0.9, 'stroke-dasharray': measured || p.it.weight ? '' : '5 4', opacity: M.sel && M.sel !== p.it.id ? 0.22 : 0.9, 'data-id': p.it.id }, svg);
        const b = document.createElement('button');
        b.className = 'mnode' + (M.sel === p.it.id ? ' on' : '');
        b.style.cssText = `left:${Math.max(0, Math.min(W - nodeW, p.x - nodeW / 2))}px;top:${Math.max(0, Math.min(H - nodeH, p.y - nodeH / 2))}px;width:${nodeW}px`;
        const sub = itemSub(p.it, p.side < 0 ? 'drivers' : 'deps');
        b.innerHTML = `<span class="mn">${esc(label(p.it))}</span><span class="ms" style="color:${M.sel === p.it.id ? 'inherit' : sub.c}">${esc(sub.t)}</span>`;
        b.dataset.act = 'msel'; b.dataset.val = p.it.id; b.dataset.side = p.side < 0 ? 'drivers' : 'deps';
        box.appendChild(b);
      });
      const c = document.createElement('div'); c.className = 'mcenter';
      c.style.cssText = `left:${cx - cW / 2}px;top:${cy - cH / 2}px;width:${cW}px;min-height:${cH}px`;
      c.innerHTML = `<span class="muted" style="font-size:12px">${esc((nb.kind || '').split(' · ')[0])}</span><span style="font-size:19px;font-weight:500;line-height:1.2">${esc(nb.name)}</span>${cMove ? `<span class="${cls(cMove.v)}" style="font-size:13px">${esc(cMove.txt)}</span>` : ''}`;
      box.appendChild(c);
    });
  }

  function drawChain(el, nb, cMove) {
    const g = M.g;
    const second = (list, dir) => {
      const seen = new Set([nb.id, ...list.map((x) => x.id)]); const out = [];
      list.forEach((x) => {
        if (!g.nodes[x.id]) return;
        g.edges.filter((e) => (dir < 0 ? e[1] === x.id : e[0] === x.id)).forEach((e) => { const o = dir < 0 ? e[0] : e[1]; if (!seen.has(o)) { seen.add(o); out.push({ id: o, via: x.id, sign: e[2] }); } });
      });
      return out.slice(0, 14);
    };
    const row = (it, side) => { const sub = itemSub(it, side); return `<button class="crow" data-act="msel" data-val="${esc(it.id)}" data-side="${side}"><span class="cn">${esc(label(it))}</span><span class="cm" style="color:${sub.c}">${esc(sub.t)}</span><span class="cb"><i style="width:${it.str * 14}px;background:var(--${it.sign === '+' ? 'in' : it.sign === '-' ? 'out' : 'neutral'})"></i>${esc(SIGNTXT[it.sign] || '')}</span></button>`; };
    const row2 = (it, word) => `<a class="crow2" href="#map-${encodeURIComponent(it.id)}">${esc(nodeName(it.id))}<span>${word} ${esc(nodeName(it.via))}</span></a>`;
    el.innerHTML = `<div class="chain"><div><h3 class="ch">Drivers of drivers</h3>${second(nb.drivers, -1).map((x) => row2(x, '→')).join('') || '<p class="note">—</p>'}</div>
      <div><h3 class="ch">What drives it</h3>${nb.drivers.map((x) => row(x, 'drivers')).join('')}</div>
      <div class="ccenter"><span class="muted" style="font-size:12px">${esc((nb.kind || '').split(' · ')[0])}</span><span style="font-size:20px;font-weight:500">${esc(nb.name)}</span>${cMove ? `<span class="${cls(cMove.v)}">${esc(cMove.txt)}</span>` : ''}</div>
      <div><h3 class="ch">What it drives</h3>${nb.deps.map((x) => row(x, 'deps')).join('')}</div>
      <div><h3 class="ch">Knock-on effects</h3>${second(nb.deps, 1).map((x) => row2(x, 'via')).join('') || '<p class="note">—</p>'}</div></div>`;
  }

  function renderSide(nb, cMove, sym) {
    const side = document.getElementById('mside'); if (!side) return;
    const all = [...nb.drivers.map((x) => Object.assign({ side: 'drivers' }, x)), ...nb.deps.map((x) => Object.assign({ side: 'deps' }, x))];
    const it = all.find((x) => x.id === M.sel);
    const fact = (l, v, c) => `<div class="kv" style="grid-template-columns:auto 1fr"><span class="muted" style="font-size:14px">${esc(l)}</span><span style="text-align:right;font-size:14px" class="${c || ''}">${v}</span></div>`;
    if (it) {
      const wind = windFor(it, it.side);
      const m = it.meas || {};
      let facts = fact('Direction', esc(SIGNTXT[it.sign] || '—'), it.sign === '+' ? 'in-t' : it.sign === '-' ? 'out-t' : '') + fact('Stated importance', ['', 'Low', 'Medium', 'High'][it.str] || '—');
      if (isNum(m.beta) || isNum(m.corr)) facts += fact('Measured link (3Y weekly)', (isNum(m.beta) ? 'β ' + esc(fmtBeta(it.id, m.beta)) : '') + (isNum(m.corr) ? (isNum(m.beta) ? ' · ' : '') + 'corr ' + num(m.corr, 2) : ''));
      else if (it.weight) facts += fact('Approx. index weight', pct(it.weight, 2, false));
      else facts += fact('Measured link', it.qual ? 'Qualitative' : 'Not measured');
      if (it.move) facts += fact('Latest move', esc(it.move.txt), cls(it.move.v));
      if (wind) facts += fact('Right now this is a', wind + ' for ' + esc(nb.name), wind === 'Tailwind' ? 'in-t' : 'out-t');
      if (it.side === 'deps' && it.sign !== '~' && it.str) facts += fact('If ' + esc(nb.name) + ' rises', esc(label(it)) + (it.sign === '+' ? ' tends to rise' : ' tends to fall'), it.sign === '+' ? 'in-t' : 'out-t');
      if (it.own) { const h = it.own.hist || []; const a = h[0], b = h[1]; if (a) facts += fact('Promoters', pct(a.promoter / 100, 1, false) + (b ? ' (' + (a.promoter - b.promoter >= 0 ? '+' : MINUS) + Math.abs(a.promoter - b.promoter).toFixed(1) + ' pp q/q)' : '')) + fact('Public (FII, DII, retail)', pct(a.public / 100, 1, false)) + fact('As of', esc(a.date)); }
      side.innerHTML = `<span class="muted" style="font-size:12px">${it.side === 'drivers' ? 'Drives ' : 'Driven by '}${esc(nb.name)}${it.measuredOnly ? ' · found in price data' : ''}</span>
        <h2 style="font-size:28px">${esc(label(it))}</h2><p style="margin:0;font-size:15px;line-height:1.6">${esc(it.why || '')}</p><div>${facts}</div>
        ${canOpen(it.id) ? `<a class="btn-solid" href="#map-${encodeURIComponent(it.id)}">Open ${esc(label(it).split(' (')[0])}'s map →</a>` : ''}
        <p class="note">Mechanism: curated from public filings and industry research. Measured: Flowscope daily price data (market move removed).</p>`;
      return;
    }
    const tw = nb.drivers.filter((x) => windFor(x, 'drivers') === 'Tailwind').length, hw = nb.drivers.filter((x) => windFor(x, 'drivers') === 'Headwind').length;
    let extra = '';
    if (sym && nb.stock) {
      const d = nb.stock;
      extra += fact('Price', d.last ? '₹' + d.last.toLocaleString('en-IN', { maximumFractionDigits: 2 }) + ' · ' + fdate(d.date, true) : '—') + fact('1 month · 1 year', pct(d.r1m) + ' · ' + pct(d.r1y)) + fact('Volatility (1Y)', pct(d.vol, 1, false)) + fact('Market beta', num(d.bm, 2)) + fact('Price explained by tracked factors', isNum(d.r2) ? pct(d.r2, 0, false) : '—') + fact('Market cap (approx.)', d.mc ? '₹' + big(d.mc) + ' cr' : '—');
      const f = (D.flows || {}).board || {}; const ind = f.India || [];
      const fe = ind.find((c) => c.name === 'Foreign investors: equity'), st = ind.find((c) => c.name === 'Sectoral & thematic');
      const wv = (c) => (c ? windowValue(c, 'Latest') : { v: null });
      const a = wv(fe), b = wv(st);
      if (isNum(a.v) || isNum(b.v)) extra += `<h3 class="ch" style="margin-top:12px">Money flows</h3>` + (isNum(a.v) ? fact('Foreign investors, Indian equity (' + esc(a.label) + ')', flow(a.v, '₹ cr'), cls(a.v)) : '') + (isNum(b.v) ? fact('Sectoral & thematic funds (' + esc(b.label) + ')', flow(b.v, '₹ cr'), cls(b.v)) : '');
    }
    const asset = !sym && nb.id && (M.g.nodes[nb.id] || {}).series && String(M.g.nodes[nb.id].series).startsWith('a:') ? M.g.nodes[nb.id].series.slice(2) : null;
    side.innerHTML = `<span class="muted" style="font-size:12px">${esc(nb.kind || '')}</span><h2 style="font-size:30px">${esc(nb.name)}</h2>
      <p style="margin:0;font-size:15px;line-height:1.6">${esc(nb.desc || (sym ? 'Drivers come from its industry template plus links measured in the price data. Click a node for details, then "Open" to make it the centre.' : 'Click any node for details, then "Open" to make it the centre.'))}</p>
      <div>${cMove ? fact('This week', esc(cMove.txt), cls(cMove.v)) : ''}${fact('Drivers', nb.drivers.length + ' tracked')}${fact('Dependants', nb.deps.length + ' tracked')}${tw + hw ? fact('Driver signal now', tw + ' tailwinds · ' + hw + ' headwinds', tw >= hw ? 'in-t' : 'out-t') : ''}${extra}</div>
      ${sym ? `<button class="btn-solid" data-act="watch" data-val="${esc(sym)}">${watch.has(sym) ? '✓ On watchlist' : '+ Add to watchlist'}</button>` : ''}
      ${asset && D.byId[asset] ? `<a class="btn-line" style="display:flex;align-items:center;justify-content:center;text-decoration:none" href="#asset-${esc(asset)}">Returns & risk page →</a>` : ''}
      <a class="btn-line" style="display:flex;align-items:center;justify-content:center;text-decoration:none" href="#shock">Shock simulator →</a>
      <p class="note">${sym ? 'Industry template: ' + esc((M.g.templates[nb.stock.t] || {}).name || '') + '. ' : ''}Sources: curated mechanisms; prices ${srcLink('stock_prices') || srcLink('yahoo')}; indices ${srcLink('nifty_indices')}.</p>`;
  }

  function searchIndex() {
    if (M.sx) return M.sx;
    const g = M.g; const xs = [];
    Object.entries(g.nodes).forEach(([k, n]) => xs.push({ id: k, n: n.name, t: n.kind }));
    Object.entries(g.templates).forEach(([k, t]) => xs.push({ id: 't:' + k, n: t.name + ' industry', t: 'Industry' }));
    Object.entries(g.indices).forEach(([k, n]) => xs.push({ id: 'i:' + k, n, t: 'Index' }));
    (M.idx.stocks || []).forEach((s) => xs.push({ id: 's:' + s.s, n: s.n, t: 'Stock · ' + s.s, sym: s.s, mc: s.mc || 0 }));
    return (M.sx = xs);
  }
  function wireSearch() {
    const inp = document.getElementById('mq'), res = document.getElementById('mres');
    if (!inp) return;
    const go = () => {
      const q = inp.value.trim().toLowerCase(); M.q = inp.value;
      if (q.length < 2) { res.hidden = true; return; }
      const hits = searchIndex().filter((x) => x.n.toLowerCase().includes(q) || (x.sym && x.sym.toLowerCase().startsWith(q))).sort((a, z) => (a.n.toLowerCase().startsWith(q) ? -1 : 0) - (z.n.toLowerCase().startsWith(q) ? -1 : 0) || (z.mc || 0) - (a.mc || 0)).slice(0, 10);
      res.innerHTML = hits.map((h) => `<a href="#map-${encodeURIComponent(h.id)}">${esc(h.n)}<span>${esc(h.t)}</span></a>`).join('') || '<span class="note" style="padding:10px;display:block">No matches</span>';
      res.hidden = false;
    };
    inp.addEventListener('input', go);
    inp.addEventListener('keydown', (e) => { if (e.key === 'Enter') { const a = res.querySelector('a'); if (a) location.hash = a.getAttribute('href').slice(1); } if (e.key === 'Escape') res.hidden = true; });
  }

  // ---------- shock simulator ----------
  async function pageShock() {
    await loadMap();
    const ex = M.ex;
    if (!ex || !ex.stocks || !ex.stocks.length) { $main.innerHTML = '<p class="loading">Sensitivity data is not available yet. It appears after the first successful daily refresh.</p>'; return; }
    if (!ex.factors.includes(M.shockF)) M.shockF = ex.factors[0];
    const fi = ex.factors.indexOf(M.shockF), yld = ex.kinds[M.shockF] === 'yld';
    const sizes = yld ? [-1, -0.5, -0.25, 0.25, 0.5, 1] : [-20, -10, -5, 5, 10, 20];
    if (!sizes.includes(M.shockV)) M.shockV = yld ? 0.5 : 10;
    const shockLbl = (v) => (yld ? (v > 0 ? '+' : MINUS) + Math.abs(v * 100) + ' bp' : (v > 0 ? '+' : MINUS) + Math.abs(v) + '%');
    const capMin = { 'Large & mid caps': 20000, 'All 750': 0 }[M.shockCap];
    const rows = ex.stocks.map((s, i) => ({ s, n: ex.names[i], t: ex.tmpl[i], mc: ex.mc[i] || 0, b: ex.beta[i][fi] })).filter((r) => isNum(r.b) && r.mc >= capMin);
    rows.forEach((r) => { r.v = r.b * (yld ? M.shockV : M.shockV / 100); });
    const up = rows.filter((r) => r.v > 0).sort((a, z) => z.v - a.v).slice(0, 10), dn = rows.filter((r) => r.v < 0).sort((a, z) => a.v - z.v).slice(0, 10);
    const m = Math.max(1e-6, ...[...up, ...dn].map((r) => Math.abs(r.v)));
    const byT = {}; rows.forEach((r) => (byT[r.t] = byT[r.t] || []).push(r.v));
    const med = (a) => { const s = a.slice().sort((x, y) => x - y); return s[Math.floor(s.length / 2)]; };
    const inds = Object.entries(byT).filter(([, a]) => a.length >= 2).map(([t, a]) => ({ t, v: med(a), n: a.length })).sort((a, z) => z.v - a.v);
    const im = Math.max(1e-6, ...inds.map((x) => Math.abs(x.v)));
    const line = (r) => `<a class="fbar" style="grid-template-columns:minmax(150px,1fr) 1fr 72px;text-decoration:none" href="#map-s:${encodeURIComponent(r.s)}"><span class="n">${esc(r.n)}<small>${esc((M.g.templates[r.t] || {}).name || '')} · β ${esc(fmtBeta(M.shockF, r.b))}</small></span><span class="track" style="height:4px"><span class="b" style="left:0;width:${(Math.abs(r.v) / m * 100).toFixed(0)}%;background:var(--${r.v > 0 ? 'in' : 'out'})"></span></span><span class="v ${cls(r.v)}">${pct(r.v)}</span></a>`;
    const wl = watch.get().filter((s) => ex.stocks.includes(s));
    const cell = (b, k) => { if (!isNum(b)) return '<td>—</td>'; const a = Math.min(Math.abs(b) / (k === 'nifty' ? 1.5 : 0.6), 1); return `<td style="background:${b >= 0 ? 'rgba(166,215,240,' : 'rgba(196,127,82,'}${(0.06 + a * 0.5).toFixed(2)});text-align:center">${num(b, 2)}</td>`; };
    const wrows = wl.map((s) => { const i = ex.stocks.indexOf(s); return `<tr><td><a href="#map-s:${encodeURIComponent(s)}">${esc(ex.names[i])}</a> <button class="xbtn" data-act="watch" data-val="${esc(s)}" aria-label="Remove ${esc(ex.names[i])}">×</button></td>${ex.factors.map((k, j) => cell(ex.beta[i][j], k)).join('')}</tr>`; }).join('');
    const avg = ex.factors.map((k, j) => { const v = wl.map((s) => ex.beta[ex.stocks.indexOf(s)][j]).filter(isNum); return v.length ? v.reduce((a, b) => a + b, 0) / v.length : null; });
    $main.innerHTML = `<section class="lede" style="padding:64px 0 40px"><span class="num">Shock simulator</span>
      <h1 class="big" style="font-size:clamp(30px,4vw,46px)">If ${esc(ex.labels[M.shockF])} moves ${shockLbl(M.shockV)}, which stocks are most exposed?</h1>
      <p>Estimated from each stock's measured three-year sensitivity, with the overall market move removed${M.shockF === 'nifty' ? ' (for the Nifty itself, this is market beta)' : ''}. It ranks exposure; it is not a forecast.</p></section>
      <section class="bar-filters">${tabs(ex.factors.map((k) => ex.labels[k]), ex.labels[M.shockF], 'shf')}</section>
      <section class="bar-filters"><div class="tools">${seg(sizes.map(shockLbl), shockLbl(M.shockV), 'shv', 'Shock size')}</div>${seg(['Large & mid caps', 'All 750'], M.shockCap, 'shc', 'Universe')}</section>
      <div class="sec two" style="padding-top:48px"><section><h2 style="font-size:24px">Most helped</h2><div>${up.map(line).join('') || '<div class="empty">None</div>'}</div></section>
      <section><h2 style="font-size:24px">Most hurt</h2><div>${dn.map(line).join('') || '<div class="empty">None</div>'}</div></section></div>
      <section class="sec split"><div class="side"><span class="num">By industry</span><h2>Median impact by industry</h2><p>Typical estimated move for stocks in each industry template.</p></div><div class="body">
      ${inds.map((x) => `<a class="fbar" style="text-decoration:none" href="#map-t:${encodeURIComponent(x.t)}"><span class="n">${esc((M.g.templates[x.t] || {}).name || x.t)}<small>${x.n} stocks</small></span><span class="track"><span class="ax"></span><span class="b" style="${x.v >= 0 ? 'left' : 'right'}:50%;width:${(Math.abs(x.v) / im * 50).toFixed(1)}%;background:var(--${x.v >= 0 ? 'in' : 'out'})"></span></span><span class="v ${cls(x.v)}">${pct(x.v)}</span></a>`).join('')}</div></section>
      <section class="sec"><div class="head-row"><div class="t"><span class="num">Watchlist</span><h2>Your combined exposure</h2></div><span class="note">Sensitivity to each factor (3Y weekly, market removed). Blue gains when the factor rises. Add stocks from any stock map.</span></div>
      ${wl.length ? `<div class="tbl-wrap"><table class="t wl"><thead><tr><th>Stock</th>${ex.factors.map((k) => `<th style="text-align:center">${esc(ex.labels[k])}</th>`).join('')}</tr></thead><tbody>${wrows}<tr style="font-weight:500"><td>Watchlist average</td>${avg.map((b, j) => cell(b, ex.factors[j])).join('')}</tr></tbody></table></div>` : '<div class="empty">Your watchlist is empty. Open any stock in the Driver map and click “Add to watchlist”.</div>'}</section>`;
  }

  // ---------- routing & events ----------
  function route() {
    observers.splice(0).forEach((o) => o.disconnect()); hideTip();
    const h = location.hash.replace('#', '') || 'flows';
    const page = h.startsWith('asset-') ? 'assets' : h.startsWith('map') ? 'map' : h;
    document.querySelectorAll('[data-nav]').forEach((a) => a.classList.toggle('on', a.dataset.nav === page));
    if (h.startsWith('asset-')) return pageAsset(h.slice(6));
    if (h === 'map' || h.startsWith('map-')) return pageMap(h.length > 4 ? decodeURIComponent(h.slice(4)) : null).catch((e) => { $main.innerHTML = '<p class="loading">Driver map data is not available yet (' + esc(e.message) + '). It appears after the first successful refresh.</p>'; });
    if (h === 'shock') return pageShock().catch((e) => { $main.innerHTML = '<p class="loading">Could not load sensitivities (' + esc(e.message) + ').</p>'; });
    ({ assets: pageAssets, cash: pageCash, sources: pageSources }[h] || pageFlows)();
  }
  document.addEventListener('click', (e) => {
    const b = e.target.closest('[data-act]');
    if (!b || b.tagName === 'SELECT' || b.tagName === 'INPUT') return;
    const act = b.dataset.act, val = b.dataset.val;
    if (act === 'sort') { ST.sortDir = ST.sort === val ? -ST.sortDir : -1; ST.sort = val; }
    else if (act === 'msel') { M.sel = M.sel === val ? null : val; }
    else if (act === 'mov') { M.overlay = val; }
    else if (act === 'mview') { M.view = val; }
    else if (act === 'watch') { watch.toggle(val); }
    else if (act === 'shf') { M.shockF = Object.keys(M.ex.labels).find((k) => M.ex.labels[k] === val) || M.shockF; }
    else if (act === 'shv') { const n = parseFloat(val.replace(MINUS, '-').replace('+', '')); M.shockV = /bp/.test(val) ? n / 100 : n; }
    else if (act === 'shc') { M.shockCap = val; }
    else ST[{ region: 'region', win: 'win', view: 'view', cls: 'cls', aview: 'aView', ccy: 'ccy', range: 'range' }[act]] = val;
    const y = window.scrollY; route(); window.scrollTo(0, y);
  });
  document.addEventListener('change', (e) => { if (e.target.dataset.act === 'aregion') { ST.aregion = e.target.value; route(); } });
  document.addEventListener('input', (e) => { if (e.target.dataset.act === 'q') { ST.q = e.target.value; ST._focusQ = true; route(); ST._focusQ = false; } });
  window.addEventListener('hashchange', () => { route(); window.scrollTo(0, 0); });
  const themeBtn = document.getElementById('theme');
  const setThemeLabel = () => { themeBtn.textContent = document.documentElement.dataset.theme === 'light' ? 'Dark' : 'Light'; };
  themeBtn.addEventListener('click', () => {
    const light = document.documentElement.dataset.theme !== 'light';
    if (light) document.documentElement.dataset.theme = 'light'; else delete document.documentElement.dataset.theme;
    try { localStorage.setItem('fs-theme', light ? 'light' : 'dark'); } catch (e) { /* storage unavailable */ }
    setThemeLabel(); route();
  });
  setThemeLabel();
  load().then(route).catch((e) => { $main.innerHTML = '<p class="loading">Could not load data (' + esc(e.message) + '). If this is a new site, the first daily refresh may still be running.</p>'; });
})();
