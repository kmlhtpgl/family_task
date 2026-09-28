/* Family Task — kiosk runtime (screensaver + adhan)
 *
 * Loaded once by a CONSTANT Streamlit iframe (see app.py). Because the HTML
 * that loads this file never changes, Streamlit reuses the iframe element
 * instead of recreating it, so this script does not re-execute on reruns.
 *
 * Everything with side effects — audio, timers, DOM — lives in the PARENT
 * document realm. That is deliberate and load-bearing:
 *
 *   1. iOS will not play unmuted audio until the page has been interacted
 *      with. WebKit propagates user activation child -> ancestor only, never
 *      parent -> child. Building the Audio element on window.parent means the
 *      taps people make on Streamlit's own nav buttons unlock the adhan, with
 *      no enable-sound button anywhere.
 *   2. State on the parent survives any future iframe reload.
 *
 * Config arrives as JSON in #kiosk-config, which Python re-renders on each
 * rerun. We poll that node instead of receiving it as a script variable, which
 * is what keeps the iframe hash stable.
 */
(function () {
    'use strict';

    var win = window.parent;
    var doc = win.document;
    if (!doc) return;

    /* ── paths ──────────────────────────────────────────────────────────── */

    var pathname = win.location.pathname;
    var BASE = pathname.slice(0, pathname.lastIndexOf('/') + 1) || '/';

    function asset(p) {
        return BASE + 'app/static/' + p;
    }

    /* ── state (on the parent, so it outlives this frame) ───────────────── */

    var K = win.__kiosk;
    if (K) {
        if (K.timer) clearTimeout(K.timer);
        if (K.sync) clearInterval(K.sync);
    }
    K = win.__kiosk = {
        timer: null,
        sync: null,
        cfg: null,
        cfgRaw: null,
        timings: null,
        timingsDay: null,
        timingsPending: false,
        pendingRetry: null,
        fired: {},
        slide: null,
        foot: null,
        ssActive: false,
        ssEl: null,
        order: [],
        pos: 0
    };

    /* ── on-screen diagnostics ──────────────────────────────────────────────
     * A wall tablet gives you nowhere to read a console. When the Admin tab
     * asks for it, render the live runtime state straight onto the page, so a
     * silent adhan can be diagnosed from the device itself. */
    var diagEl = null;

    function dot(ok, warn) {
        var bg = ok ? '#10B981' : (warn ? '#F59E0B' : '#EF4444');
        return '<i style="display:inline-block;width:8px;height:8px;border-radius:50%;' +
               'background:' + bg + ';margin-right:8px;vertical-align:middle"></i>';
    }

    function row(label, value, ok, warn) {
        return '<div style="display:flex;justify-content:space-between;gap:18px;' +
               'padding:3px 0;border-bottom:1px solid rgba(255,255,255,0.07)">' +
               '<span style="opacity:0.75">' + label + '</span>' +
               '<span style="font-weight:600;white-space:nowrap">' +
               dot(ok, warn) + value + '</span></div>';
    }

    function hideDiagnostics() {
        if (diagEl && diagEl.parentNode) diagEl.parentNode.removeChild(diagEl);
        diagEl = null;
    }

    function renderDiagnostics() {
        var c = cfg() || {};
        if (!diagEl) {
            diagEl = doc.createElement('div');
            diagEl.className = 'kiosk-diagnostics';
            doc.body.appendChild(diagEl);
        }
        var np = nextPrayerInfo();
        var mins = np ? Math.round(np.mins / 60 * 10) / 10 : null;
        var idleMin = c.idle_timeout_ms ? Math.round(c.idle_timeout_ms / 6000) / 10 : null;
        var html = '<div style="font-weight:700;font-size:1.05em;margin-bottom:8px;' +
                   'display:flex;align-items:center;gap:8px">Kiosk runtime</div>';
        html += row('Runtime loaded', 'yes', true);
        html += row('Config parsed', c.adhan_enabled !== undefined ? 'yes' : 'no', !!c.adhan_enabled !== undefined);
        html += row('Prayer times', K.timings ? 'loaded' : 'MISSING', !!K.timings, true);
        html += row('Adhan enabled', c.adhan_enabled ? 'on' : 'off', !!c.adhan_enabled, true);
        html += row('Audio files', Object.keys(c.adhan_files || {}).length + ' / 5',
                    Object.keys(c.adhan_files || {}).length >= 5, true);
        html += row('Backgrounds', (c.backgrounds || []).length + ' images',
                    (c.backgrounds || []).length > 0, true);
        html += row('Screensaver', K.ssActive ? 'showing' : 'armed in ' + idleMin + ' min',
                    K.ssActive || !!K.idle, true);
        html += row('Next adhan', np ? np.name + ' ' + np.label + ' · in ' + mins + 'h' : 'unknown',
                    !!np, true);
        html += row('Sound unlocked', K.unlocked ? 'yes' : 'NO — tap the screen',
                    !!K.unlocked);
        html += row('Pending retry', K.pendingRetry || 'none', !K.pendingRetry, true);
        html += row('Wake lock', K.wake ? 'held' : 'not held', !!K.wake, true);
        diagEl.innerHTML = html;
    }

    /* ── config ─────────────────────────────────────────────────────────── */

    function readConfig() {
        var el = doc.getElementById('kiosk-config');
        var raw = el ? (el.textContent || '').trim() : '';
        if (!raw) return null;
        if (raw === K.cfgRaw) return K.cfg;
        try {
            K.cfgRaw = raw;
            K.cfg = JSON.parse(raw);
        } catch (e) {
            console.error('[kiosk] bad config JSON', e);
            K.cfg = null;
        }
        return K.cfg;
    }

    function cfg() {
        return K.cfg || readConfig();
    }

    /* ── small helpers ──────────────────────────────────────────────────── */

    function pad(n) { return n < 10 ? '0' + n : '' + n; }

    function todayKey(d) {
        d = d || new Date();
        return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate());
    }

    function apiDate(d) {
        d = d || new Date();
        return pad(d.getDate()) + '-' + pad(d.getMonth() + 1) + '-' + d.getFullYear();
    }

    /* ── toast ──────────────────────────────────────────────────────────── */

    var toastEl = null;
    function toast(text, cls) {
        if (toastEl && toastEl.parentNode) toastEl.parentNode.removeChild(toastEl);
        var el = doc.createElement('div');
        el.className = 'kiosk-audio-status ' + (cls || 'ok');
        el.textContent = text;
        doc.body.appendChild(el);
        toastEl = el;
        setTimeout(function () {
            if (toastEl === el && el.parentNode) el.parentNode.removeChild(el);
            if (toastEl === el) toastEl = null;
        }, 6000);
    }

    /* ══════════════════════════════════════════════════════════════════════
     * ADHAN
     * ══════════════════════════════════════════════════════════════════════ */

    var PRAYERS = ['Fajr', 'Dhuhr', 'Asr', 'Maghrib', 'Isha'];
    var GRACE_MS = 5 * 60 * 1000;   /* still play if we opened/returned late */
    var LOOKAHEAD_MS = 12 * 60 * 60 * 1000;

    /* Prayer times come straight from the browser. Both providers send
     * Access-Control-Allow-Origin: *, so there is no need to route them
     * through Python — which also means the adhan keeps working when the
     * Streamlit server has cold-cache timings. */
    function fetchTimings(force) {
        var c = cfg();
        if (!c) return;
        var day = todayKey();
        if (!force && K.timings && K.timingsDay === day) return;
        if (K.timingsPending) return;

        K.timingsPending = true;
        var lat = c.lat, lon = c.lon;
        var qs = 'latitude=' + encodeURIComponent(lat) +
                 '&longitude=' + encodeURIComponent(lon) +
                 '&method=' + encodeURIComponent(c.method) +
                 '&school=' + encodeURIComponent(c.school);

        fetch('https://api.aladhan.com/v1/timings/' + apiDate() + '?' + qs, { mode: 'cors' })
            .then(function (r) { return r.ok ? r.json() : Promise.reject(r.status); })
            .then(function (j) { applyTimings(j && j.data && j.data.timings); })
            .catch(function () {
                var qs2 = 'city=Cambridge&country=United%20Kingdom&method=' +
                          encodeURIComponent(c.method) + '&school=' + encodeURIComponent(c.school);
                return fetch('https://api.islamic.app/v1/timings/today?' + qs2, { mode: 'cors' })
                    .then(function (r) { return r.ok ? r.json() : Promise.reject(r.status); })
                    .then(function (j) { applyTimings(j && j.timings); })
                    .catch(function (e) {
                        console.warn('[kiosk] prayer times unavailable', e);
                    });
            })
            .then(function () { K.timingsPending = false; });
    }

    function applyTimings(t) {
        if (!t) return;
        K.timings = t;
        K.timingsDay = todayKey();
        cacheTimings(t);
        arm();
    }

    function cacheTimings(t) {
        try {
            win.localStorage.setItem('adhan.timings.' + K.timingsDay, JSON.stringify(t));
        } catch (e) { /* private mode / quota */ }
    }

    function readCachedTimings() {
        try {
            var raw = win.localStorage.getItem('adhan.timings.' + todayKey());
            if (raw) {
                K.timings = JSON.parse(raw);
                K.timingsDay = todayKey();
                return true;
            }
        } catch (e) { /* ignore */ }
        return false;
    }

    /* Cambridge Central Mosque convention: adhan for Fajr goes at sunrise
     * minus a lead time, not at the reported Fajr time. */
    function effectiveTime(name) {
        var t = K.timings;
        if (!t) return null;
        var raw = t[name];
        if (name === 'Fajr' && t.Sunrise) {
            var p = t.Sunrise.split(':');
            var mins = parseInt(p[0], 10) * 60 + parseInt(p[1], 10) + (cfg().fajr_offset_min || 0);
            if (!isNaN(mins)) {
                var h = Math.floor(mins / 60), m = mins % 60;
                if (h < 0) h += 24;
                return pad(h) + ':' + pad(m);
            }
        }
        return raw || null;
    }

    /* Today's schedule as absolute timestamps. */
    function schedule() {
        var out = [];
        for (var i = 0; i < PRAYERS.length; i++) {
            var time = effectiveTime(PRAYERS[i]);
            if (!time) continue;
            var p = time.split(':');
            var h = parseInt(p[0], 10), m = parseInt(p[1], 10);
            if (isNaN(h) || isNaN(m)) continue;
            var d = new Date();
            d.setHours(h, m, 0, 0);
            out.push({ name: PRAYERS[i], label: time, at: d });
        }
        out.sort(function (a, b) { return a.at - b.at; });
        return out;
    }

    /* ── dedup (localStorage: survives reruns AND full page reloads) ────── */

    function playedKey() { return 'adhan.played.' + todayKey(); }

    function loadPlayed() {
        try {
            var raw = win.localStorage.getItem(playedKey());
            var arr = raw ? JSON.parse(raw) : [];
            K.fired = {};
            for (var i = 0; i < arr.length; i++) K.fired[arr[i]] = true;
        } catch (e) { K.fired = {}; }
    }

    function markPlayed(name) {
        K.fired[name] = true;
        try {
            win.localStorage.setItem(playedKey(), JSON.stringify(Object.keys(K.fired)));
        } catch (e) { /* ignore */ }
    }

    /* Drop stale adhan keys, but keep the last few days of both the played
     * markers and the timings cache — pruning the timings here would leave
     * readCachedTimings() with nothing to show on a cold start. */
    function pruneCache() {
        try {
            var keep = {}, i, k, d, day;
            for (i = 0; i < 4; i++) {
                d = new Date(Date.now() - i * 864e5);
                day = d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate());
                keep['adhan.played.' + day] = 1;
                keep['adhan.timings.' + day] = 1;
            }
            for (i = win.localStorage.length - 1; i >= 0; i--) {
                k = win.localStorage.key(i);
                if (k && k.indexOf('adhan.') === 0 && !keep[k]) win.localStorage.removeItem(k);
            }
        } catch (e) { /* ignore */ }
    }

    /* ── audio ──────────────────────────────────────────────────────────── */

    /* Built in the parent realm: see the file header. */
    function audio() {
        if (!K.el) {
            K.el = new win.Audio();
            K.el.preload = 'auto';
        }
        return K;
    }

    function audioUrl(name) {
        var c = cfg();
        var files = (c && c.adhan_files) || {};
        var f = files[name.toLowerCase()];
        if (!f) return null;
        return asset('adhan/' + encodeURIComponent(f));
    }

    /* A 50 ms silent WAV, built in JS. Used to prime the parent's media
     * session from inside a real gesture — inaudible, and no base64 blob in
     * the Python source. */
    function silentUrl() {
        if (K.silent) return K.silent;
        var sr = 8000, n = Math.floor(sr * 0.05);
        var buf = new win.ArrayBuffer(44 + n * 2);
        var dv = new win.DataView(buf);
        var str = function (o, s) { for (var i = 0; i < s.length; i++) dv.setUint8(o + i, s.charCodeAt(i)); };
        str(0, 'RIFF');
        dv.setUint32(4, 36 + n * 2, true);
        str(8, 'WAVEfmt ');
        dv.setUint32(16, 16, true);
        dv.setUint16(20, 1, true);
        dv.setUint16(22, 1, true);
        dv.setUint32(24, sr, true);
        dv.setUint32(28, sr * 2, true);
        dv.setUint16(32, 2, true);
        dv.setUint16(34, 16, true);
        str(36, 'data');
        dv.setUint32(40, n * 2, true);
        var blob = new win.Blob([buf], { type: 'audio/wav' });
        K.silent = win.URL.createObjectURL(blob);
        return K.silent;
    }

    /* ── audio unlock hint ──────────────────────────────────────────────────
     * iOS refuses unmuted playback until the page has been interacted with.
     * The adhan then sits in pendingRetry waiting for a gesture that, on a
     * wall-mounted tablet, may never come. A 6-second toast is not enough: it
     * expires long before anyone notices. This stays on screen, centred at the
     * bottom, until a gesture actually unlocks the session. */
    var unlockEl = null;

    function unlockHint(on, text) {
        if (!on) {
            if (unlockEl && unlockEl.parentNode) unlockEl.parentNode.removeChild(unlockEl);
            unlockEl = null;
            return;
        }
        if (unlockEl && unlockEl.parentNode) {
            if (unlockEl.textContent !== text) unlockEl.textContent = text;
            return;
        }
        unlockEl = doc.createElement('div');
        unlockEl.className = 'kiosk-unlock-hint';
        unlockEl.textContent = text;
        doc.body.appendChild(unlockEl);
    }

    function prime() {
        var a = audio();
        try {
            a.el.pause();
            a.el.src = silentUrl();
            a.el.volume = 0;
            var p = a.el.play();
            if (p && p.then) {
                p.then(function () {
                    setTimeout(function () {
                        try { a.el.pause(); } catch (e) {}
                        a.el.volume = 1;
                        a.el.removeAttribute('src');
                    }, 90);
                    /* The silent clip played, so the parent's media session is
                     * unlocked and later timer-driven playback will be allowed. */
                    K.unlocked = true;
                    unlockHint(false);
                }).catch(function () {});
            }
        } catch (e) { /* ignore */ }
    }

    function playAdhan(name, isTest) {
        var a = audio();
        var url = audioUrl(name);
        if (!url) {
            toast('No audio file for ' + name, 'err');
            return;
        }
        try {
            a.el.src = url;
            a.el.currentTime = 0;
            a.el.volume = 1;
        } catch (e) {
            toast('Adhan audio error', 'err');
            return;
        }
        var p = a.el.play();
        if (p && p.then) {
            p.then(function () {
                /* A test must not consume the real adhan for that prayer. */
                if (!isTest) markPlayed(name);
                K.pendingRetry = null;
                K.unlocked = true;
                unlockHint(false);
                toast(name + (isTest ? ' adhan (test)' : ' adhan'), 'ok');
            }).catch(function () {
                /* Autoplay refused. Do not latch a false "unlocked" flag —
                 * keep the request and retry on the next real gesture. */
                try { a.el.pause(); } catch (e) {}
                K.pendingRetry = name;
                K.unlocked = false;
                toast('Autoplay blocked', 'warn');
                unlockHint(true, 'Tap anywhere once to let the adhan sound');
            });
        } else if (!isTest) {
            markPlayed(name);
        }
    }

    /* ── the scheduler ──────────────────────────────────────────────────── */

    function arm() {
        if (K.timer) { clearTimeout(K.timer); K.timer = null; }
        var c = cfg();
        if (!c || !c.adhan_enabled) return;
        /* A wall tablet can stay focused across midnight. Refresh the date
         * before trying to schedule yesterday's timings. */
        if (K.timingsDay && K.timingsDay !== todayKey()) {
            K.fired = {};
            fetchTimings(true);
            return;
        }
        if (!K.timings) { fetchTimings(); return; }

        var list = schedule();
        if (!list.length) return;
        var now = Date.now();
        var soonest = null;

        for (var i = 0; i < list.length; i++) {
            var t = list[i].at.getTime();
            var delta = t - now;
            if (delta <= 0 && delta > -GRACE_MS && !K.fired[list[i].name]) {
                playAdhan(list[i].name);
                /* Re-check at the edge of the grace window, so a tab that was
                 * suspended mid-window still gets it exactly once. */
                K.timer = setTimeout(arm, GRACE_MS + 1000);
                return;
            }
            if (delta > 0 && delta < LOOKAHEAD_MS) {
                if (soonest === null || delta < soonest) soonest = delta;
            }
        }

        if (soonest !== null) {
            K.timer = setTimeout(arm, soonest);
        } else {
            /* There are no more prayers today. Wake at the next local
             * midnight so Fajr is not lost when the screen stays on all night. */
            var next = new Date();
            next.setHours(24, 0, 1, 0);
            K.timer = setTimeout(function () {
                K.fired = {};
                fetchTimings(true);
                arm();
            }, Math.max(1000, next.getTime() - Date.now()));
        }
    }

    /* ── wake lock ──────────────────────────────────────────────────────── */

    function wakeLock() {
        if (K.wake || !win.navigator || !('wakeLock' in win.navigator)) return;
        if (doc.visibilityState !== 'visible') return;
        win.navigator.wakeLock.request('screen').then(function (wl) {
            K.wake = wl;
            wl.addEventListener('release', function () { K.wake = null; });
        }).catch(function (e) {
            /* Low battery / power saving — not fatal, and not worth a banner. */
            K.wake = null;
        });
    }

    /* ══════════════════════════════════════════════════════════════════════
     * SCREENSAVER
     * ══════════════════════════════════════════════════════════════════════ */

    function shuffle(n) {
        var a = [], i, j, t;
        for (i = 0; i < n; i++) a.push(i);
        for (i = n - 1; i > 0; i--) {
            j = Math.floor(Math.random() * (i + 1));
            t = a[i]; a[i] = a[j]; a[j] = t;
        }
        return a;
    }

    function nextIndex() {
        K.pos++;
        if (K.pos >= K.order.length) { K.order = shuffle(K.order.length); K.pos = 0; }
        return K.order[K.pos];
    }

    function bgUrls() {
        var c = cfg();
        var names = (c && c.backgrounds) || [];
        var out = [];
        for (var i = 0; i < names.length; i++) {
            out.push(asset('backgrounds/' + encodeURIComponent(names[i])));
        }
        return out;
    }

    function showScreensaver() {
        if (K.ssActive) return;
        var imgs = bgUrls();
        K.ssActive = true;
        doc.documentElement.classList.add('kiosk-active');

        var el = doc.createElement('div');
        el.className = 'kiosk-screensaver';

        var box = doc.createElement('div');
        box.className = 'kiosk-screensaver-images';
        el.appendChild(box);

        var foot = doc.createElement('div');
        foot.className = 'kiosk-screensaver-footer';
        el.appendChild(foot);

        doc.body.appendChild(el);
        K.ssEl = el;

        K.order = shuffle(imgs.length);
        K.pos = 0;
        if (imgs.length) paintImage(imgs);
        else {
            box.classList.add('kiosk-screensaver-images--fallback');
            box.textContent = 'Kiosk mode active';
        }

        var self = this;
        renderFooter();
        K.foot = setInterval(renderFooter, 30000);

        if (imgs.length > 1) {
            K.slide = setInterval(function () { paintImage(imgs); }, 10000);
        }

        var dismiss = function () { hideScreensaver(); };
        el.addEventListener('click', dismiss);
        el.addEventListener('touchend', dismiss);
    }

    function paintImage(imgs) {
        if (!K.ssEl) return;
        var box = K.ssEl.querySelector('.kiosk-screensaver-images');
        if (!box) return;
        if (!imgs.length) return;
        var idx = K.pos === 0 ? K.order[0] : nextIndex();
        while (box.firstChild) box.removeChild(box.firstChild);
        var img = doc.createElement('img');
        img.src = imgs[idx];
        img.className = 'kiosk-screensaver-img active';
        img.addEventListener('error', function () {
            /* A wall display must never turn into an unexplained black page
             * when a CDN/static asset is unavailable. Keep the screensaver
             * layer alive and show a deliberate fallback surface instead. */
            img.style.display = 'none';
            box.classList.add('kiosk-screensaver-images--fallback');
            box.setAttribute('aria-label', 'Kiosk screensaver active');
            box.textContent = 'Kiosk mode active';
        });
        box.appendChild(img);
    }

    function nextPrayerInfo() {
        if (!K.timings) return null;
        var list = schedule();
        var nowMin = new Date().getHours() * 60 + new Date().getMinutes();
        var best = Infinity, found = null;
        for (var i = 0; i < list.length; i++) {
            var p = list[i].label.split(':');
            var m = parseInt(p[0], 10) * 60 + parseInt(p[1], 10);
            var diff = m - nowMin;
            if (diff <= 0) diff += 1440;
            if (diff < best) { best = diff; found = list[i]; }
        }
        return found ? { name: found.name, label: found.label, mins: best } : null;
    }

    function renderFooter() {
        if (!K.ssEl) return;
        var foot = K.ssEl.querySelector('.kiosk-screensaver-footer');
        if (!foot) return;
        var now = new Date();
        var parts = [];
        parts.push('<span class="kiosk-ss-time">' +
            now.toLocaleDateString('en-GB', { weekday: 'long', day: 'numeric', month: 'long' }) +
            ' · ' + pad(now.getHours()) + ':' + pad(now.getMinutes()) + '</span>');

        var np = nextPrayerInfo();
        if (np) {
            var left = np.mins >= 60
                ? 'in ' + Math.floor(np.mins / 60) + 'h' + (np.mins % 60 ? ' ' + (np.mins % 60) + 'm' : '')
                : 'in ' + np.mins + ' min';
            parts.push('<span class="kiosk-ss-prayer">Next: ' + np.name +
                       ' at ' + np.label + ' · ' + left + '</span>');
        }

        var c = cfg();
        if (c && c.weather) {
            parts.push('<span class="kiosk-ss-weather">' + c.weather.icon + ' ' +
                       c.weather.temp + c.weather.unit + ' · ' + c.weather.condition +
                       ' · ' + c.weather.city + '</span>');
        }
        foot.innerHTML = parts.join('');
    }

    function hideScreensaver() {
        if (!K.ssActive) return;
        K.ssActive = false;
        doc.documentElement.classList.remove('kiosk-active');
        if (K.slide) { clearInterval(K.slide); K.slide = null; }
        if (K.foot) { clearInterval(K.foot); K.foot = null; }
        if (K.ssEl && K.ssEl.parentNode) K.ssEl.parentNode.removeChild(K.ssEl);
        K.ssEl = null;
        K.order = [];
        K.pos = 0;
        idle();
    }

    /* ── idle / screensaver timer ───────────────────────────────────────── */

    function idle() {
        if (K.idle) { clearTimeout(K.idle); K.idle = null; }
        var c = cfg();
        if (!c || !c.screensaver_enabled) return;
        if (!bgUrls().length) return;
        K.idle = setTimeout(showScreensaver, c.idle_timeout_ms || 300000);
    }

    function activity() {
        if (K.ssActive) hideScreensaver();
        idle();
    }

    function handleKioskControl(event) {
        var target = event.target && event.target.closest
            ? event.target.closest('[data-kiosk-action]') : null;
        if (!target) return;
        var action = target.getAttribute('data-kiosk-action');
        if (action === 'screensaver') showScreensaver();
        if (action === 'adhan') playAdhan(target.getAttribute('data-kiosk-prayer') || 'Fajr', true);
    }

    /* ══════════════════════════════════════════════════════════════════════
     * WIRING
     * ══════════════════════════════════════════════════════════════════════ */

    var GESTURES = ['pointerdown', 'touchstart', 'mousedown', 'keydown', 'click'];

    function onGesture() {
        audio();                       /* build the element on first touch */
        prime();
        if (K.pendingRetry) {
            var name = K.pendingRetry;
            K.pendingRetry = null;
            playAdhan(name);
        }
    }

    GESTURES.forEach(function (evt) {
        doc.addEventListener(evt, onGesture, { passive: true });
    });
    /* The controls are mounted by Streamlit after this runtime. Capture the
     * click at the parent window so the test remains a real browser gesture. */
    win.addEventListener('pointerdown', handleKioskControl, true);
    win.addEventListener('click', handleKioskControl, true);

    var IDLE_EVENTS = ['mousemove', 'wheel', 'scroll', 'touchstart', 'click'];
    IDLE_EVENTS.forEach(function (evt) {
        doc.addEventListener(evt, activity, { passive: true });
    });

    doc.addEventListener('visibilitychange', function () {
        if (doc.visibilityState === 'visible') {
            wakeLock();
            fetchTimings();
            arm();
            idle();
        }
    });

    win.addEventListener('focus', function () { fetchTimings(); arm(); });
    win.addEventListener('pageshow', function () { fetchTimings(true); arm(); });

    /* Config can change under us (admin toggles, test buttons). Re-arm when
     * it does. Polling a tiny text node is far cheaper than the old design,
     * which rebuilt a multi-megabyte iframe every time the data changed.
     *
     * idle() MUST be re-armed here too. It used to run only at startup, so if
     * the first script pass happened before Streamlit had mounted
     * #kiosk-config, cfg() was null, no timer was ever created, and nothing
     * later re-armed it: on a tablet nobody touches, the screensaver could
     * then never appear at all. */
    /* The Admin test buttons update #kiosk-config after a Streamlit rerun. A
     * four-second poll makes a working test look broken, especially when the
     * page settles or the tablet is being checked by hand. This is a tiny local
     * DOM read, so keep the handoff responsive without touching any API. */
    K.sync = setInterval(function () {
        var c = readConfig();
        if (!c) return;
        var sig = JSON.stringify([
            c.adhan_enabled, c.screensaver_enabled, c.idle_timeout_ms,
            c.trigger_adhan, c.trigger_screensaver, c.fajr_offset_min,
            c.diagnostics,
            c.adhan_files, c.backgrounds && c.backgrounds.length
        ]);
        if (sig !== K.sig) {
            K.sig = sig;
            arm();
            idle();
            if (c.trigger_screensaver) showScreensaver();
        }
        if (K.timingsDay && K.timingsDay !== todayKey()) {
            K.fired = {};
            fetchTimings(true);
        }
        if (c.diagnostics) renderDiagnostics();
        else if (diagEl) hideDiagnostics();
        if (c.trigger_adhan) {
            if (K.triggered !== c.trigger_adhan) {
                K.triggered = c.trigger_adhan;
                playAdhan(c.trigger_adhan, true);
            }
        } else {
            /* Cleared server-side once delivered, so allow the same prayer to
             * be tested again. */
            K.triggered = null;
        }
        /* Surface a blocked media session instead of waiting in silence for a
         * tap that may never arrive. */
        if (!K.unlocked) {
            unlockHint(true, K.pendingRetry
                ? 'Adhan is waiting — tap anywhere once to allow sound'
                : 'Tap anywhere once to enable the adhan');
        }
    }, 500);

    /* ── init ───────────────────────────────────────────────────────────── */

    pruneCache();
    loadPlayed();
    readConfig();
    if (!readCachedTimings()) fetchTimings();
    wakeLock();
    idle();
    arm();

    /* Console handle for manual checks, mirrored by the Admin → Kiosk
     * diagnostics panel so the real state is readable on the device itself
     * instead of having to be guessed at. */
    win.Adhan = {
        play: function (n) { playAdhan(n || 'fajr'); },
        state: function () {
            var list = schedule();
            var now = Date.now();
            var next = null;
            for (var i = 0; i < list.length; i++) {
                var d = list[i].at.getTime() - now;
                if (d > 0 && (next === null || d < next.in)) {
                    next = { name: list[i].name, at: list[i].label, in: d };
                }
            }
            return {
                runtimeLoaded: true,
                configParsed: !!K.cfg,
                screensaverEnabled: !!(K.cfg && K.cfg.screensaver_enabled),
                adhanEnabled: !!(K.cfg && K.cfg.adhan_enabled),
                backgrounds: (K.cfg && K.cfg.backgrounds || []).length,
                adhanFiles: Object.keys((K.cfg && K.cfg.adhan_files) || {}).length,
                idleArmed: !!K.idle,
                idleTimeoutMs: K.cfg ? K.cfg.idle_timeout_ms : null,
                adhanArmed: !!K.timer,
                timingsLoaded: !!K.timings,
                timingsDay: K.timingsDay,
                nextPrayer: next,
                audioUnlocked: !!K.unlocked,
                pendingRetry: K.pendingRetry,
                firedToday: Object.keys(K.fired),
                wakeLock: !!K.wake,
                screensaverActive: K.ssActive,
                audio: audioUrl('fajr')
            };
        }
    };
    win.Kiosk = {
        screensaver: showScreensaver,
        dismiss: hideScreensaver,
        playAdhan: function (name) { playAdhan(name || 'Fajr', true); }
    };
})();
