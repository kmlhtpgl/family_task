import json
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
    .st-emotion-cache-18ni7ap { padding-top: 1rem !important; }
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
        padding: 10px 24px;
        border-radius: var(--radius-xl);
        margin-bottom: 20px;
        box-shadow: var(--shadow-lg), 0 0 0 1px rgba(99,102,241,0.05);
        height: 60px;
        width: 100%;
        box-sizing: border-box;
        position: relative;
        z-index: 10;
    }

    .navbar-brand {
        display: flex;
        align-items: center;
        gap: 12px;
    }

    .navbar-brand .logo {
        font-size: 1.6em;
        background: linear-gradient(135deg, var(--primary), var(--secondary));
        width: 38px;
        height: 38px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 10px;
        flex-shrink: 0;
        color: white;
    }

    .navbar-brand h1 {
        color: var(--text);
        font-size: 1.3em;
        margin: 0;
        font-weight: 700;
        letter-spacing: -0.02em;
        white-space: nowrap;
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
        font-size: 0.85em;
        font-weight: 500;
    }

    .nav-dark-btn {
        background: var(--bg-card-alt);
        border: 1px solid var(--border);
        border-radius: 10px;
        padding: 6px 10px;
        cursor: pointer;
        font-size: 1.1em;
        transition: all var(--transition);
        color: var(--text);
        line-height: 1;
    }

    .nav-dark-btn:hover {
        border-color: var(--primary-light);
        transform: scale(1.1);
    }

    @media (max-width: 768px) {
        .top-navbar {
            padding: 8px 14px;
            border-radius: var(--radius);
            height: auto;
            min-height: 48px;
            flex-wrap: wrap;
        }
        .navbar-brand h1 { font-size: 1em; }
        .navbar-brand span { display: none; }
        .navbar-brand .logo { font-size: 1.3em; width: 32px; height: 32px; }
        .navbar-actions .nav-date { display: none; }
        .family-bg { width: 200px; height: 200px; }
    }
    </style>

    <div class="family-bg"></div>
""", unsafe_allow_html=True)

st.markdown(f"""
    <div class="top-navbar">
        <div id="brand-home" style="cursor:pointer;display:flex;align-items:center;gap:12px;" class="navbar-brand">
            <div class="logo">🏠</div>
            <h1>Family Task</h1>
        </div>
        <div class="navbar-actions">
            <div class="nav-date" id="current-date"></div>
            <button class="nav-dark-btn" onclick="document.getElementById('dark-toggle-input').click()" title="Toggle theme">
                {"🌙" if st.session_state.dark_mode else "☀️"}
            </button>
        </div>
    </div>
    <script>
        document.getElementById('current-date').textContent = new Date().toLocaleDateString('en-GB', {{
            weekday: 'short', day: 'numeric', month: 'short', year: 'numeric'
        }});
        document.getElementById('brand-home').addEventListener('click', function() {{
            window.location.href = '?nav=dashboard';
        }});
    </script>
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
    }}
    win.__kioskCleared = true;

    var CONFIG = {_kiosk_json};

    /* ═══════ WAKE LOCK ═══════ */
    var wakeLock = null;
    function requestWakeLock() {{
        if (win.navigator && 'wakeLock' in win.navigator) {{
            win.navigator.wakeLock.request('screen').then(function(wl) {{
                wakeLock = wl;
                wakeLock.addEventListener('release', function() {{
                    wakeLock = null;
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

    /* ═══════ SCREENSAVER ═══════ */
    var screensaverEl = null;
    var slideshowInterval = null;
    var currentImageIndex = 0;

    function showScreensaver() {{
        if (isScreensaverActive) return;
        var imgs = CONFIG.background_images;
        if (!imgs || imgs.length === 0) return;
        isScreensaverActive = true;

        screensaverEl = doc.createElement('div');
        screensaverEl.className = 'kiosk-screensaver';

        var imgContainer = doc.createElement('div');
        imgContainer.className = 'kiosk-screensaver-images';

        var img = doc.createElement('img');
        img.src = imgs[0];
        img.className = 'kiosk-screensaver-img active';
        imgContainer.appendChild(img);
        screensaverEl.appendChild(imgContainer);
        doc.body.appendChild(screensaverEl);
        currentImageIndex = 0;

        if (imgs.length > 1) {{
            win.__kioskSlide = setInterval(function() {{
                var container = screensaverEl.querySelector('.kiosk-screensaver-images');
                if (!container) return;
                currentImageIndex = (currentImageIndex + 1) % imgs.length;
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
        if (screensaverEl) {{ screensaverEl.remove(); screensaverEl = null; }}
        currentImageIndex = 0;
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

# Hidden toggle for dark mode (triggered by navbar button)
dark_toggle = st.toggle("🌙 Dark mode", value=st.session_state.dark_mode, key="dark-toggle-input", label_visibility="collapsed")

if dark_toggle != st.session_state.dark_mode:
    st.session_state.dark_mode = dark_toggle
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
