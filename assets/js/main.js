/* RAMO press kit. No dependencies. */
(() => {
  'use strict';

  /* ================= CONFIG: the three things you will edit ================= */
  const TRACK_URL = 'https://api.soundcloud.com/tracks/1806593451'; // the 2024 house mix
  const BEST_PART_MS = 16 * 60 * 1000;   // best part starts at 16:00. Change this number (milliseconds) to move it.
                                         // Set to null to jump to 35% of the mix instead.
  const BEST_PART_FALLBACK = 0.35;
  /* ======================================================================== */

  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));
  const root = document.documentElement;
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const fmt = (ms) => {
    const s = Math.max(0, Math.round(ms / 1000));
    return Math.floor(s / 60) + ':' + String(s % 60).padStart(2, '0');
  };

  /* ---------- language ---------- */
  const TITLES = {
    en: 'RAMO | DJ, NYC → Tokyo | Press kit',
    ja: 'RAMO | DJ（NYC → 東京）| プレスキット'
  };
  function setLang(l, persist) {
    root.dataset.lang = l;
    root.lang = l;
    document.title = TITLES[l];
    $$('[data-set-lang]').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.setLang === l)));
    if (persist) { try { localStorage.setItem('ramo-lang', l); } catch (e) {} }
  }
  setLang(root.dataset.lang || 'en', false);
  $$('[data-set-lang]').forEach((b) => b.addEventListener('click', () => setLang(b.dataset.setLang, true)));

  /* ---------- top bar ---------- */
  const bar = $('#bar');
  const onScroll = () => bar.classList.toggle('solid', scrollY > innerHeight * 0.55);
  addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  /* ---------- reveal ---------- */
  const rvTargets = $$('.sh, .gig, .player, .reels, .bio, .dl-row, .rider, .book-lead, .mail, .book-links');
  if ('IntersectionObserver' in window && !reduce) {
    const io = new IntersectionObserver((es) => es.forEach((e) => {
      if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); }
    }), { rootMargin: '0px 0px -8% 0px', threshold: 0.06 });
    rvTargets.forEach((el) => { el.classList.add('rv'); io.observe(el); });
    // failsafe: if observers never fire (hidden frame, odd embed), show everything after 3 s
    setTimeout(() => rvTargets.forEach((el) => el.classList.add('in')), 3000);
  }

  /* ---------- waveform (decorative; SoundCloud does not expose the real one) ---------- */
  const wave = $('#wave'), barsEl = $('#waveBars'), onEl = $('#waveOn');
  (function buildWave() {
    const N = 96;
    let a = 2024;
    const rnd = () => { a |= 0; a = (a + 0x6D2B79F5) | 0; let t = Math.imul(a ^ (a >>> 15), 1 | a); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
    let v = 0.5, html = '';
    for (let i = 0; i < N; i++) {
      v += (rnd() - 0.5) * 0.6; v = Math.min(1, Math.max(0.2, v));
      const env = 0.5 + 0.5 * Math.sin(Math.PI * Math.pow(i / N, 0.75));
      html += '<i style="height:' + Math.round(100 * Math.min(1, Math.max(0.12, v * env))) + '%"></i>';
    }
    barsEl.innerHTML = html;
    onEl.innerHTML = html;
  })();

  /* ---------- player (SoundCloud Widget API, custom controls) ---------- */
  const player = $('#player');
  const tCur = $('#tCur'), tDur = $('#tDur'), bestT = $('#bestT'), mini = $('#mini'), mCur = $('#mCur');
  let playerOnScreen = true, everPlayed = false;
  const syncMini = () => mini.classList.toggle('on', everPlayed && !playerOnScreen);
  let widget = null, ready = false, dur = 0, pos = 0, playing = false, wantPlay = false, pendingSeek = null;

  const bestMs = () => (BEST_PART_MS != null ? BEST_PART_MS : dur * BEST_PART_FALLBACK);

  function paint(ms) {
    pos = ms;
    const p = dur ? Math.min(100, (ms / dur) * 100) : 0;
    wave.style.setProperty('--p', p + '%');
    wave.setAttribute('aria-valuenow', String(Math.round(p)));
    tCur.textContent = fmt(ms);
    mini.style.setProperty('--p', p + '%');
    mCur.textContent = fmt(ms) + (dur ? ' / ' + fmt(dur) : '');
  }
  function setPlaying(on) {
    playing = on;
    if (on) everPlayed = true;
    syncMini();
    player.dataset.state = on ? 'playing' : 'paused';
    $$('[data-play]').forEach((b) => {
      b.setAttribute('aria-pressed', String(on));
      b.setAttribute('aria-label', on ? 'Pause' : 'Play');
    });
  }

  if ('IntersectionObserver' in window) new IntersectionObserver((es) => { playerOnScreen = es[0].isIntersecting; syncMini(); }).observe(player);

  function loadSC() {
    if (loadSC.done) return;
    loadSC.done = true;
    const f = document.createElement('iframe');
    f.title = 'SoundCloud player (hidden, controlled by the buttons on this page)';
    f.allow = 'autoplay';
    f.tabIndex = -1;
    f.setAttribute('aria-hidden', 'true');
    f.src = 'https://w.soundcloud.com/player/?url=' + encodeURIComponent(TRACK_URL) +
      '&auto_play=false&hide_related=true&show_comments=false&show_user=false&show_reposts=false&show_teaser=false&visual=false';
    $('#scHost').appendChild(f);
    const s = document.createElement('script');
    s.src = 'https://w.soundcloud.com/player/api.js';
    s.onload = () => {
      widget = SC.Widget(f);
      const E = SC.Widget.Events;
      widget.bind(E.READY, () => {
        ready = true;
        widget.getDuration((d) => {
          dur = d;
          tDur.textContent = fmt(d);
          bestT.textContent = fmt(bestMs());
          if (pendingSeek === -1) pendingSeek = bestMs();   // "best part" was tapped before the player was ready
          if (wantPlay) { wantPlay = false; widget.play(); }
        });
      });
      widget.bind(E.PLAY, () => { setPlaying(true); if (pendingSeek != null) { widget.seekTo(pendingSeek); pendingSeek = null; } });
      widget.bind(E.PAUSE, () => setPlaying(false));
      widget.bind(E.FINISH, () => { setPlaying(false); paint(0); });
      widget.bind(E.PLAY_PROGRESS, (e) => paint(e.currentPosition));
    };
    document.head.appendChild(s);
    setTimeout(() => { if (!ready) $('#plNote').hidden = false; }, 9000);
  }

  function toggle(fromHero) {
    loadSC();
    if (!ready) { wantPlay = true; if (fromHero) goListen(); return; }
    if (playing) { widget.pause(); return; }
    widget.play();
    if (fromHero) goListen();
  }
  function goListen() { $('#listen').scrollIntoView({ behavior: reduce ? 'auto' : 'smooth', block: 'center' }); }

  $$('[data-play]').forEach((b) => b.addEventListener('click', () => toggle(b.classList.contains('play-big'))));

  $('#bestPart').addEventListener('click', () => {
    loadSC();
    if (!ready) { wantPlay = true; pendingSeek = -1; return; }
    const ms = bestMs();
    if (playing) widget.seekTo(ms); else { pendingSeek = ms; widget.play(); }
  });

  /* scrub: click, tap, drag, keys */
  function seekFromEvent(e) {
    if (!ready || !dur) return;
    const r = wave.getBoundingClientRect();
    const ratio = Math.min(1, Math.max(0, (e.clientX - r.left) / r.width));
    paint(ratio * dur);
    widget.seekTo(ratio * dur);
    if (!playing) widget.play();
  }
  let dragging = false;
  wave.addEventListener('pointerdown', (e) => { loadSC(); dragging = true; wave.setPointerCapture(e.pointerId); seekFromEvent(e); });
  wave.addEventListener('pointermove', (e) => { if (dragging) seekFromEvent(e); });
  wave.addEventListener('pointerup', () => { dragging = false; });
  wave.addEventListener('pointercancel', () => { dragging = false; });
  wave.addEventListener('keydown', (e) => {
    if (!ready || !dur) return;
    const step = { ArrowLeft: -5000, ArrowRight: 5000, PageDown: -30000, PageUp: 30000 }[e.key];
    if (step) { e.preventDefault(); const t = Math.min(dur, Math.max(0, pos + step)); paint(t); widget.seekTo(t); }
    if (e.key === 'Home') { e.preventDefault(); paint(0); widget.seekTo(0); }
    if (e.key === ' ' || e.key === 'Enter') { e.preventDefault(); toggle(false); }
  });

  /* warm the player after the page has settled so the first tap works on iOS */
  const warm = () => (window.requestIdleCallback ? requestIdleCallback(loadSC, { timeout: 4000 }) : setTimeout(loadSC, 2500));
  if (document.readyState === 'complete') warm(); else addEventListener('load', warm);
  addEventListener('pointerdown', loadSC, { once: true, passive: true });

  /* ---------- clips ---------- */
  const vids = $$('#reels video');
  function attach(v) {
    if (v.dataset.ok) return;
    v.dataset.ok = '1';
    ['webm', 'mp4'].forEach((t) => {
      const s = document.createElement('source');
      s.src = 'assets/video/' + v.dataset.clip + '.' + t;
      s.type = 'video/' + t;
      v.appendChild(s);
    });
    v.load();
  }
  // share of the clip that is on screen right now (0 to 1), from its real position
  const onScreen = (v) => {
    const r = v.getBoundingClientRect();
    const w = Math.max(0, Math.min(r.right, innerWidth) - Math.max(r.left, 0));
    const h = Math.max(0, Math.min(r.bottom, innerHeight) - Math.max(r.top, 0));
    return (w * h) / Math.max(1, r.width * r.height);
  };
  const tryPlay = (v) => { if (reduce || onScreen(v) < 0.3) return; const p = v.play(); if (p && p.catch) p.catch(() => {}); };
  vids.forEach((v) => v.addEventListener('canplay', () => tryPlay(v)));
  const setPoster = (v) => { if (v.dataset.poster) { v.poster = v.dataset.poster; delete v.dataset.poster; } };
  if ('IntersectionObserver' in window) {
    const pio = new IntersectionObserver((es) => es.forEach((e) => { if (e.isIntersecting) { setPoster(e.target); pio.unobserve(e.target); } }), { rootMargin: '900px' });
    vids.forEach((v) => pio.observe(v));
    // play what is on screen, pause the rest; run on scroll, resize and when the observer fires
    let tick = 0;
    const check = () => {
      tick = 0;
      vids.forEach((v) => {
        const r = v.getBoundingClientRect();
        if (r.bottom > -120 && r.top < innerHeight + 120) attach(v);
        if (onScreen(v) >= 0.3) tryPlay(v); else v.pause();
      });
    };
    const soon = () => { if (!tick) tick = setTimeout(check, 120); };
    addEventListener('scroll', soon, { passive: true });
    addEventListener('resize', soon);
    new IntersectionObserver(soon, { rootMargin: '120px', threshold: [0, 0.3, 0.6] }).observe($('#reels'));
    vids.forEach((v) => v.addEventListener('canplay', soon));
    check();
  }
  else vids.forEach((v) => { setPoster(v); attach(v); });
  vids.forEach((v) => v.addEventListener('click', () => (v.paused ? v.play().catch(() => {}) : v.pause())));

  /* ---------- copy buttons ---------- */
  async function copy(text, btn) {
    try { await navigator.clipboard.writeText(text); }
    catch (e) {
      const ta = document.createElement('textarea'); ta.value = text; ta.style.position = 'fixed'; ta.style.opacity = '0';
      document.body.appendChild(ta); ta.select(); try { document.execCommand('copy'); } catch (_) {} ta.remove();
    }
    const spans = $$('span', btn).filter((s) => s.classList.contains('en') || s.classList.contains('ja'));
    const old = spans.map((s) => s.textContent);
    spans.forEach((s) => { s.textContent = s.classList.contains('ja') ? 'コピーしました' : 'Copied'; });
    setTimeout(() => spans.forEach((s, i) => { s.textContent = old[i]; }), 1600);
  }
  const bioBtn = $('[data-copy-bio]');
  if (bioBtn) bioBtn.addEventListener('click', () => {
    const l = root.dataset.lang === 'ja' ? 'ja' : 'en';
    copy($('.bio-t > .' + l).innerText.replace(/\n{2,}/g, '\n\n').trim(), bioBtn);
  });
  const mailBtn = $('[data-copy-mail]');
  if (mailBtn) mailBtn.addEventListener('click', () => copy($('#mail').textContent.trim(), mailBtn));
})();
