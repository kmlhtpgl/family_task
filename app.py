import json
from datetime import date

import streamlit as st
import streamlit.components.v1 as components
from utils.db_helpers import get_all_data
from utils.styles import apply_custom_styles
from utils.kiosk_helpers import get_kiosk_config
from app_pages.dashboard import dashboard_page
from app_pages.kanban import kanban_page
from app_pages.kids_profiles import kids_profiles_page
from app_pages.parents_profiles import parents_profiles_page
from app_pages.reading_library import reading_library_page
from app_pages.surah_memorization import surah_memorization_page
from app_pages.rewards import rewards_page
from app_pages.admin import admin_page
from app_pages.prayer import prayer_page

st.set_page_config(
    page_title="Family Task Tracker",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dark mode toggle
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

# Apply custom styles based on dark mode
apply_custom_styles(dark_mode=st.session_state.dark_mode)

st.markdown("""
    <style>
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    [data-testid="stHeader"] { display: none !important; }
    [data-testid="stAppViewContainer"] .block-container,
    .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 2rem !important;
    }
    [data-testid="collapsedControl"] { z-index: 100; }

    .family-bg {
        position: fixed;
        bottom: 0;
        right: 0;
        width: 350px;
        height: 350px;
        opacity: 0.04;
        pointer-events: none;
        z-index: -1;
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 400 400'%3E%3Cg fill='%236366F1'%3E%3Ccircle cx='200' cy='80' r='25'/%3E%3Cpath d='M175 130 Q200 110 225 130 L220 180 Q200 170 180 180 Z'/%3E%3Cpath d='M160 180 L145 240 L170 240 L180 190 Z'/%3E%3Cpath d='M240 180 L255 240 L230 240 L220 190 Z'/%3E%3C/g%3E%3Cg fill='%23EC4899'%3E%3Ccircle cx='130' cy='140' r='18'/%3E%3Cpath d='M112 180 Q130 165 148 180 L144 220 Q130 215 116 220 Z'/%3E%3Cpath d='M104 220 L95 270 L115 270 L112 230 Z'/%3E%3Cpath d='M156 220 L165 270 L145 270 L148 230 Z'/%3E%3C/g%3E%3Cg fill='%23EC4899'%3E%3Ccircle cx='270' cy='140' r='18'/%3E%3Cpath d='M252 180 Q270 165 288 180 L284 220 Q270 215 256 220 Z'/%3E%3Cpath d='M244 220 L235 270 L255 270 L252 230 Z'/%3E%3Cpath d='M296 220 L305 270 L285 270 L288 230 Z'/%3E%3C/g%3E%3Cg fill='%2314B8A6'%3E%3Ccircle cx='200' cy='170' r='14'/%3E%3Cpath d='M186 200 Q200 190 214 200 L210 240 Q200 235 190 240 Z'/%3E%3Cpath d='M182 240 L174 280 L190 280 L194 245 Z'/%3E%3Cpath d='M218 240 L226 280 L210 280 L206 245 Z'/%3E%3C/g%3E%3Ccircle cx='100' cy='300' r='30' fill='%236366F1' opacity='0.5'/%3E%3Ccircle cx='300' cy='320' r='25' fill='%2314B8A6' opacity='0.5'/%3E%3C/svg%3E");
        background-size: contain;
        background-repeat: no-repeat;
    }

    .top-navbar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: var(--bg-nav);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid var(--border);
        padding: 14px 28px;
        border-radius: var(--radius-xl);
        margin-bottom: 20px;
        box-shadow: var(--shadow-lg), 0 0 0 1px rgba(99,102,241,0.05);
        height: 76px;
        width: 100%;
        box-sizing: border-box;
        position: relative;
        z-index: 10;
    }

    .navbar-brand {
        display: flex;
        align-items: center;
        gap: 12px;
        text-decoration: none;
        color: inherit;
        cursor: pointer;
    }

    .top-navbar a[href*="nav"] {
        text-decoration: none;
        color: inherit;
        cursor: pointer;
    }

    .navbar-brand h1 {
        font-size: 1.7em;
        margin: 0;
        font-weight: 800;
        letter-spacing: -0.03em;
        white-space: nowrap;
        background: linear-gradient(135deg, var(--primary), var(--secondary));
        -webkit-background-clip: text;
        background-clip: text;
        -webkit-text-fill-color: transparent;
        color: transparent;
    }

    .navbar-brand span {
        color: var(--text-secondary);
        font-size: 0.8em;
        font-weight: 400;
        margin-left: 4px;
    }

    .navbar-actions {
        display: flex;
        align-items: center;
        gap: 12px;
        flex-shrink: 0;
    }

    .navbar-actions .nav-date {
        color: var(--text-secondary);
        font-size: 0.95em;
        font-weight: 600;
    }

    @media (max-width: 768px) {
        .top-navbar {
            padding: 10px 16px;
            border-radius: var(--radius);
            height: auto;
            min-height: 56px;
            flex-wrap: wrap;
        }
        .navbar-brand h1 { font-size: 1.15em; }
        .navbar-brand span { display: none; }
        .navbar-actions .nav-date { display: none; }
        .family-bg { width: 200px; height: 200px; }
    }
    </style>

    <div class="family-bg"></div>
""", unsafe_allow_html=True)

st.markdown(f"""
    <div class="top-navbar">
        <a href="?nav=dashboard" class="navbar-brand">
            <h1>Family Task</h1>
        </a>
        <div class="navbar-actions">
            <div class="nav-date">{date.today().strftime('%a %-d %b %Y')}</div>
        </div>
    </div>
""", unsafe_allow_html=True)

# ── Kiosk Module ──
_kiosk_cfg = get_kiosk_config()
_kiosk_json = json.dumps(_kiosk_cfg)

components.html(f"""
<script>
(function() {{
    var doc = window.parent.document;
    var win = window.parent;

    if (win.__kioskCleared) {{
        clearInterval(win.__kioskInt);
        clearTimeout(win.__kioskIdle);
        clearInterval(win.__kioskSlide);
        clearInterval(win.__kioskFooterInt);
    }}
    win.__kioskCleared = true;

    var CONFIG = {_kiosk_json};

    /* ═══════ WAKE LOCK ═══════ */
    function requestWakeLock() {{
        if (win.__kioskWakeLock) return;
        if (win.navigator && 'wakeLock' in win.navigator) {{
            win.navigator.wakeLock.request('screen').then(function(wl) {{
                win.__kioskWakeLock = wl;
                wl.addEventListener('release', function() {{
                    win.__kioskWakeLock = null;
                }});
            }}).catch(function() {{}});
        }}
    }}
    doc.addEventListener('visibilitychange', function() {{
        if (doc.visibilityState === 'visible') requestWakeLock();
    }});

    /* ═══════ IDLE DETECTION ═══════ */
    var isScreensaverActive = false;
    function resetIdleTimer() {{
        if (isScreensaverActive) hideScreensaver();
        clearTimeout(win.__kioskIdle);
        if (CONFIG.screensaver_enabled && CONFIG.background_images && CONFIG.background_images.length > 0) {{
            win.__kioskIdle = setTimeout(showScreensaver, CONFIG.idle_timeout_ms || 300000);
        }}
    }}

    /* ═══════ NEXT PRAYER HELPER ═══════ */
    function parsePrayerMinute(timeStr) {{
        if (!timeStr) return null;
        var parts = timeStr.split(':');
        if (parts.length < 2) return null;
        return parseInt(parts[0], 10) * 60 + parseInt(parts[1], 10);
    }}

    function computeNextPrayer() {{
        var pt = CONFIG.prayer_times;
        if (!pt) return null;
        var names = ['Fajr', 'Dhuhr', 'Asr', 'Maghrib', 'Isha'];
        var now = new Date();
        var nowMin = now.getHours() * 60 + now.getMinutes();
        var best = Infinity;
        var next = null;
        for (var pi = 0; pi < names.length; pi++) {{
            var prayer = names[pi];
            var time = pt[prayer];
            if (!time) continue;
            if (prayer === 'Fajr' && pt.Sunrise) {{
                var sr = parsePrayerMinute(pt.Sunrise) - 10;
                if (sr !== null) {{
                    var fh = Math.floor(sr / 60);
                    var fm = sr % 60;
                    time = fh + ':' + (fm < 10 ? '0' : '') + fm;
                }}
            }}
            var tMin = parsePrayerMinute(time);
            if (tMin === null) continue;
            var diff = tMin - nowMin;
            if (diff < 0) diff += 24 * 60;
            if (diff < best) {{
                best = diff;
                next = {{ name: prayer, time: time, minutes: diff }};
            }}
        }}
        return next;
    }}

    function formatMinutesLeft(total) {{
        if (total >= 60) {{
            var h = Math.floor(total / 60);
            var m = total % 60;
            return 'in ' + h + 'h' + (m > 0 ? ' ' + m + 'm' : '');
        }}
        return 'in ' + total + ' min';
    }}

    function renderScreensaverFooter() {{
        if (!screensaverEl) return;
        var el = screensaverEl.querySelector('.kiosk-screensaver-footer');
        if (!el) return;
        var now = new Date();
        var hh = now.getHours();
        var mm = now.getMinutes();
        var timeStr = (hh < 10 ? '0' : '') + hh + ':' + (mm < 10 ? '0' : '') + mm;
        var dateStr = now.toLocaleDateString('en-GB', {{ weekday: 'long', day: 'numeric', month: 'long' }});
        var clock = '<span class="kiosk-ss-time">🕐 ' + dateStr + ' · ' + timeStr + '</span>';
        var next = computeNextPrayer();
        var prayer = '';
        if (next) {{
            prayer = '<span class="kiosk-ss-prayer">🕌 Next: ' + next.name + ' at ' + next.time + ' · ' + formatMinutesLeft(next.minutes) + '</span>';
        }}
        el.innerHTML = clock + prayer;
    }}

    /* ═══════ SCREENSAVER ═══════ */
    var screensaverEl = null;
    var slideshowInterval = null;
    var currentImageIndex = 0;
    var shuffledOrder = [];
    var shuffledPos = 0;

    function buildShuffleOrder(length) {{
        var order = [];
        for (var i = 0; i < length; i++) order.push(i);
        for (var i = length - 1; i > 0; i--) {{
            var j = Math.floor(Math.random() * (i + 1));
            var tmp = order[i];
            order[i] = order[j];
            order[j] = tmp;
        }}
        return order;
    }}

    function nextImageIndex() {{
        shuffledPos++;
        if (shuffledPos >= shuffledOrder.length) {{
            shuffledOrder = buildShuffleOrder(shuffledOrder.length);
            shuffledPos = 0;
        }}
        return shuffledOrder[shuffledPos];
    }}

    function showScreensaver() {{
        if (isScreensaverActive) return;
        var imgs = CONFIG.background_images;
        if (!imgs || imgs.length === 0) return;
        isScreensaverActive = true;

        screensaverEl = doc.createElement('div');
        screensaverEl.className = 'kiosk-screensaver';

        var imgContainer = doc.createElement('div');
        imgContainer.className = 'kiosk-screensaver-images';

        shuffledOrder = buildShuffleOrder(imgs.length);
        shuffledPos = 0;
        currentImageIndex = shuffledOrder[shuffledPos];

        var img = doc.createElement('img');
        img.src = imgs[currentImageIndex];
        img.className = 'kiosk-screensaver-img active';
        imgContainer.appendChild(img);
        screensaverEl.appendChild(imgContainer);
        doc.body.appendChild(screensaverEl);

        var footer = doc.createElement('div');
        footer.className = 'kiosk-screensaver-footer';
        screensaverEl.appendChild(footer);
        renderScreensaverFooter();
        win.__kioskFooterInt = setInterval(renderScreensaverFooter, 30000);

        if (imgs.length > 1) {{
            win.__kioskSlide = setInterval(function() {{
                var container = screensaverEl.querySelector('.kiosk-screensaver-images');
                if (!container) return;
                currentImageIndex = nextImageIndex();
                while (container.firstChild) container.removeChild(container.firstChild);
                var newImg = doc.createElement('img');
                newImg.src = imgs[currentImageIndex];
                newImg.className = 'kiosk-screensaver-img active';
                container.appendChild(newImg);
            }}, 10000);
        }}

        function dismissHandler() {{ hideScreensaver(); }}
        screensaverEl.addEventListener('click', dismissHandler);
        screensaverEl.addEventListener('touchend', dismissHandler);
    }}

    function hideScreensaver() {{
        if (!isScreensaverActive) return;
        isScreensaverActive = false;
        clearInterval(win.__kioskSlide);
        clearInterval(win.__kioskFooterInt);
        if (screensaverEl) {{ screensaverEl.remove(); screensaverEl = null; }}
        currentImageIndex = 0;
        shuffledOrder = [];
        shuffledPos = 0;
        resetIdleTimer();
    }}

    /* ═══════ USER ACTIVITY ═══════ */
    var activityEvents = ['mousedown','mousemove','keydown','touchstart','click','scroll','wheel'];
    for (var ei = 0; ei < activityEvents.length; ei++) {{
        doc.addEventListener(activityEvents[ei], resetIdleTimer, {{ passive: true }});
    }}

    /* ═══════ PRAYER TIME CHECKER ═══════ */
    var lastPrayed = {{}};
    function checkPrayerTimes() {{
        if (!CONFIG.adhan_enabled || !CONFIG.prayer_times || !CONFIG.audio_data) return;
        var now = new Date();
        var todayKey = now.getFullYear() + '-' + now.getMonth() + '-' + now.getDate();
        if (lastPrayed._date !== todayKey) {{
            lastPrayed = {{ _date: todayKey }};
        }}
        var prayers = ['Fajr','Dhuhr','Asr','Maghrib','Isha'];
        for (var pi = 0; pi < prayers.length; pi++) {{
            var prayer = prayers[pi];
            var time = CONFIG.prayer_times[prayer];
            if (!time) continue;
            if (prayer === 'Fajr' && CONFIG.prayer_times.Sunrise) {{
                var sr = CONFIG.prayer_times.Sunrise.split(':');
                var srMin = parseInt(sr[0], 10) * 60 + parseInt(sr[1], 10) - 10;
                var fh = Math.floor(srMin / 60);
                var fm = srMin % 60;
                time = fh + ':' + (fm < 10 ? '0' : '') + fm;
            }}
            var parts = time.split(':');
            var h = parseInt(parts[0], 10);
            var m = parseInt(parts[1], 10);
            var prayerDate = new Date(now);
            prayerDate.setHours(h, m, 0, 0);
            var diff = Math.abs(now - prayerDate);
            if (diff < 120000 && !lastPrayed[prayer]) {{
                lastPrayed[prayer] = true;
                playAdhan(prayer.toLowerCase());
                break;
            }}
        }}
    }}

    var audioCtx = null;
    function unlockAudio() {{
        if (!audioCtx) {{
            try {{ audioCtx = new (win.AudioContext || win.webkitAudioContext)(); }} catch(e) {{
                console.error('Kiosk: AudioContext creation failed', e);
            }}
        }}
        if (audioCtx && audioCtx.state === 'suspended') {{
            audioCtx.resume().catch(function(e) {{
                console.error('Kiosk: AudioContext resume failed', e);
            }});
        }}
    }}
    function reattachAudioUnlock() {{
        doc.removeEventListener('touchstart', unlockAudio);
        doc.removeEventListener('click', unlockAudio);
        doc.addEventListener('touchstart', unlockAudio);
        doc.addEventListener('click', unlockAudio);
    }}
    reattachAudioUnlock();

    function base64ToArrayBuffer(dataUri) {{
        var commaIdx = dataUri.indexOf(',');
        var base64 = dataUri.substring(commaIdx + 1);
        var binaryStr = atob(base64);
        var len = binaryStr.length;
        var bytes = new Uint8Array(len);
        for (var i = 0; i < len; i++) {{
            bytes[i] = binaryStr.charCodeAt(i);
        }}
        return bytes.buffer;
    }}

    function playAdhan(prayer) {{
        if (!CONFIG.audio_data || !CONFIG.audio_data[prayer]) return;
        unlockAudio();
        if (!audioCtx) {{
            console.error('Kiosk: No audio context available');
            return;
        }}
        var names = {{ fajr:'Fajr', dhuhr:'Dhuhr', asr:'Asr', maghrib:'Maghrib', isha:'Isha' }};
        var banner = doc.createElement('div');
        banner.className = 'kiosk-adhan-banner';
        banner.innerHTML = '\\u{{1F54C}} Adhan \\u2014 ' + (names[prayer] || prayer) + ' time!';
        doc.body.appendChild(banner);
        setTimeout(function() {{ if (banner.parentNode) banner.remove(); }}, 10000);
        doc.body.classList.add('adhan-playing');
        try {{
            var arrayBuffer = base64ToArrayBuffer(CONFIG.audio_data[prayer]);
            audioCtx.decodeAudioData(arrayBuffer, function(buffer) {{
                var source = audioCtx.createBufferSource();
                source.buffer = buffer;
                source.connect(audioCtx.destination);
                source.start(0);
                source.onended = function() {{
                    doc.body.classList.remove('adhan-playing');
                }};
            }}, function(err) {{
                console.error('Kiosk: Audio decode failed', err);
                doc.body.classList.remove('adhan-playing');
            }});
        }} catch(e) {{
            console.error('Kiosk: Adhan playback error', e);
            doc.body.classList.remove('adhan-playing');
        }}
    }}

    /* ═══════ FAMILY TASK BRAND → HOME (same tab) ═══════ */
    (function makeBrandSameTab() {{
        var tries = 0;
        function tryPatch() {{
            var brand = doc.querySelector('a[href*="nav=dashboard"]');
            if (!brand) {{
                if (tries < 50) {{ tries++; setTimeout(tryPatch, 100); }}
                return;
            }}
            brand.removeAttribute('target');
        }}
        tryPatch();
    }})();

    /* ═══════ INIT ═══════ */
    requestWakeLock();
    resetIdleTimer();
    win.__kioskInt = setInterval(checkPrayerTimes, 15000);
    if (CONFIG.trigger_screensaver) {{
        setTimeout(function() {{ showScreensaver(); }}, 500);
    }}

    win.Kiosk = {{
        testAdhan: playAdhan,
        hideScreensaver: hideScreensaver,
        showScreensaver: showScreensaver,
        updateConfig: function(cfg) {{ win.__kioskConfig = cfg; }},
    }};
}})();
</script>
""", height=0)

# Page navigation bar
if "page" not in st.session_state:
    st.session_state.page = "dashboard"

pages = [
    ("dashboard", "📊", "Dashboard"),
    ("kanban", "🎯", "Daily Board"),
    ("parents", "👨‍👩‍👧", "Parents"),
    ("kids", "🧒", "Kids"),
    ("reading", "📚", "Reading"),
    ("quran", "📖", "Quran"),
    ("prayer", "🕌", "Prayer"),
    ("rewards", "💰", "Rewards"),
    ("admin", "⚙️", "Admin"),
]

# Create navigation buttons
cols = st.columns(len(pages), gap="small")
for col, (page_key, icon, label) in zip(cols, pages):
    is_active = page_key == st.session_state.page
    btn_type = "primary" if is_active else "secondary"

    if col.button(f"{icon} {label}", key=f"nav_{page_key}", use_container_width=True, type=btn_type):
        st.session_state.page = page_key
        st.rerun()

# Handle nav query param (clicking the Family Task header)
if st.query_params.get("nav") == "dashboard":
    st.session_state.page = "dashboard"
    st.query_params.clear()
    st.rerun()

data = get_all_data()

# Determine page from session state
page = st.session_state.get("page", "dashboard")

# Route to pages
if page == "dashboard":
    dashboard_page(data)

elif page == "kanban":
    kanban_page(data)

elif page == "parents":
    parents_profiles_page(data)

elif page == "kids":
    kids_profiles_page(data)

elif page == "reading":
    reading_library_page(data)

elif page == "quran":
    surah_memorization_page(data)

elif page == "prayer":
    prayer_page(data)

elif page == "rewards":
    rewards_page(data)

elif page == "admin":
    if "admin_authenticated" not in st.session_state:
        st.session_state.admin_authenticated = False

    if not st.session_state.admin_authenticated:
        st.warning("🔒 Admin section is password-protected.")
        with st.form("admin_login"):
            pwd = st.text_input("Enter admin password", type="password")
            if st.form_submit_button("Unlock"):
                if pwd == st.secrets["ADMIN_PASSWORD"]:
                    st.session_state.admin_authenticated = True
                    st.rerun()
                else:
                    st.error("Incorrect password.")
    else:
        admin_page(data)
