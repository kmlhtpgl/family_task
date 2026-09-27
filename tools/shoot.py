"""Screenshot the app so design work can actually be looked at.

    python tools/shoot.py                    # every viewport, every route
    python tools/shoot.py --route board      # one route
    python tools/shoot.py --compare          # also diff against .screens/baseline

Streamlit reruns are triggered by real widget interaction and by nothing else,
so routes are reached by clicking the nav rather than by URL: the app keeps its
page in session state, not in the query string.

Output lands in .screens/<viewport>/<route>.png. A --compare run writes the
difference against .screens/baseline/<viewport>/<route>.png, which is the only
practical way to catch a layout regression that no assertion would notice.
"""

import argparse
import http.client
import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT = REPO_ROOT / ".screens"
BASELINE = OUT / "baseline"

VIEWS = {
    # The wall tablet is the primary device, so it is listed first and shot at
    # the size it actually is on the wall.
    "kiosk": (1280, 800),
    "kiosk-hd": (1920, 1080),
    "tablet": (820, 1180),
    "phone": (390, 844),
    "desktop": (1440, 900),
}

# Classic nav labels, in the order app.py defines them.
ROUTES = {
    "parents": "Parents",
    "kids": "Kids",
    "reading": "Reading",
    "quran": "Quran",
    "prayer": "Prayer",
    "rewards": "Rewards",
    "meeting": "Meeting",
    "admin": "Admin",
}

ADMIN_PASSWORD_HINT = "set FAMILY_TASK_ADMIN_PASSWORD to shoot the admin page"


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def wait_for_health(port, timeout=90):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            conn = http.client.HTTPConnection("127.0.0.1", port, timeout=2)
            conn.request("GET", "/healthz")
            if conn.getresponse().status == 200:
                return True
        except OSError:
            time.sleep(0.5)
    return False


def start_app(port, script="app.py", env_overrides=None, script_args=()):
    env = dict(os.environ)
    env["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
    if env_overrides:
        env.update({k: str(v) for k, v in env_overrides.items()})
    log = open("/tmp/shoot-streamlit.log", "w")
    proc = subprocess.Popen(
        [
            str(REPO_ROOT / "path/to/venv/bin/streamlit"),
            "run",
            script,
            *script_args,
            "--server.port",
            str(port),
            "--server.address",
            "127.0.0.1",
            "--server.headless",
            "true",
            "--server.fileWatcherType",
            "none",
            "--browser.gatherUsageStats",
            "false",
        ],
        cwd=REPO_ROOT,
        stdout=log,
        stderr=subprocess.STDOUT,
        env=env,
        preexec_fn=os.setsid,
    )
    if not wait_for_health(port):
        proc.kill()
        raise SystemExit(
            "streamlit never became healthy. See /tmp/shoot-streamlit.log\n"
            + Path("/tmp/shoot-streamlit.log").read_text()[-2000:]
        )
    return proc


def kill(proc):
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        proc.wait(timeout=10)
    except Exception:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except Exception:
            pass


def dom_signature(page):
    """A cheap fingerprint of what is on the page right now.

    Element count, scroll height and text length together change whenever
    Streamlit mounts a different amount of page, which is what we need to know
    about -- not whether a particular selector exists.
    """
    return page.evaluate(
        """() => {
            const main = document.querySelector('[data-testid="stMain"]');
            return [
                document.querySelectorAll('[data-testid="stAppViewContainer"] *').length,
                Math.round(document.documentElement.scrollHeight),
                (main ? main.innerText : '').length,
            ].join(':');
        }"""
    )


def settle(page, timeout=45_000, frames=True):
    """Wait for the current Streamlit run to finish.

    Streamlit shows a status widget while the script is running and removes it
    when the run completes. Screenshotting mid-run catches a half-painted page,
    which is the single most misleading failure mode for this tool.

    `frames` also waits on each child frame's font status. A component iframe
    has its own document, so a page-level `document.fonts.status === 'loaded'`
    says nothing about the type actually being rendered inside it -- which is
    how a fallback face can survive a screenshot unnoticed.

    Then it waits for the page to stop changing. The waits above are all racy in
    the same direction: right after a click, Streamlit has not necessarily
    started its rerun yet, so "no status widget" and "network idle" are both
    still true from the *previous* page and the run is measured mid-swap. That
    is not a cosmetic problem -- a half-mounted page reports fewer font sizes
    than the page has, so the type-scale check fails on whichever page happened
    to be caught in flight. Same failure mode as a screenshot of a half-painted
    page, one level up.
    """
    page.wait_for_selector('[data-testid="stAppViewContainer"]', timeout=timeout)
    page.wait_for_load_state("networkidle")
    try:
        page.wait_for_function(
            "() => !document.querySelector('[data-testid=\"stStatusWidget\"]')",
            timeout=timeout,
        )
    except Exception:
        pass
    # Let webfonts settle; a screenshot taken against a fallback face is
    # useless for judging type.
    page.wait_for_function("() => document.fonts.status === 'loaded'", timeout=15_000)
    if frames:
        for frame in page.frames:
            if frame == page.main_frame:
                continue
            try:
                frame.wait_for_function(
                    "() => document.fonts.status === 'loaded'", timeout=15_000
                )
                frame.wait_for_function(
                    "() => document.fonts.check('400 16px \"Inter\"')",
                    timeout=15_000,
                )
            except Exception:
                # A cross-origin frame cannot be inspected. Nothing to assert.
                pass
    # Now wait for the page to hold still: two identical fingerprints in a row.
    deadline = time.time() + timeout
    previous = None
    while time.time() < deadline:
        current = dom_signature(page)
        if current == previous:
            break
        previous = current
        page.wait_for_timeout(500)
    page.wait_for_timeout(700)


def click_nav(page, label):
    """Click a navbar button and wait for the rerun to land."""
    target = page.locator("button", has_text=label).first
    if target.count() == 0:
        return False
    target.click()
    page.wait_for_load_state("networkidle")
    page.wait_for_function(
        "() => !document.querySelector('[data-testid=\"stStatusWidget\"]')",
        timeout=45_000,
    )
    page.wait_for_timeout(600)
    return True


def unlock_admin(page):
    password = os.environ.get("FAMILY_TASK_ADMIN_PASSWORD")
    if not password:
        print(f"  skipping admin ({ADMIN_PASSWORD_HINT})")
        return False
    field = page.locator('input[type="password"]').first
    if field.count() == 0:
        return True
    field.fill(password)
    page.locator("button", has_text="Unlock").first.click()
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(800)
    return True


def shoot_phase(browser, base, routes, views, args):
    """Shoot one shell's worth of routes. Returns the shots taken."""
    written = []
    for view in views:
        target = OUT / view if not args.baseline else BASELINE / view
        target.mkdir(parents=True, exist_ok=True)

        for route in routes:
            page = browser.new_page(
                viewport={"width": VIEWS[view][0], "height": VIEWS[view][1]},
                device_scale_factor=2 if args.retina else 1,
            )
            errors = []
            page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
            page.on("pageerror", lambda e: errors.append(str(e)))

            page.goto(base, wait_until="domcontentloaded")
            settle(page)

            # The board is the landing page, so it needs no nav click. Every
            # other route is a classic page and has to be clicked to.
            if route != "board":
                if not click_nav(page, ROUTES[route]):
                    print(f"  {view}/{route}: nav button not found, skipping")
                    page.close()
                    continue
                if route == "admin" and not unlock_admin(page):
                    page.close()
                    continue

            out = target / f"{route}.png"
            page.screenshot(path=str(out))
            status = "ok"
            if errors:
                status = f"{len(errors)} console error(s)"
            print(f"  {view}/{route}: {out.relative_to(REPO_ROOT)} [{status}]")
            for e in errors[:3]:
                print(f"      {e[:160]}")
            written.append((view, route, out, errors))
            page.close()
    return written


def shoot(args):
    from playwright.sync_api import sync_playwright

    routes = [args.route] if args.route else ["board", *ROUTES]
    views = [args.view] if args.view else list(VIEWS)

    # The board and the classic pages are two different shells, so they are two
    # different app runs. Screenshotting a classic route against the default
    # board shell would quietly save a picture of the board under a classic
    # page's name.
    phases = [
        ([r for r in routes if r == "board"], None),
        ([r for r in routes if r != "board"], {"FAMILY_TASK_CLASSIC": "1"}),
    ]

    written = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        try:
            for wanted, env in phases:
                if not wanted:
                    continue
                port = free_port()
                proc = start_app(port, env_overrides=env)
                try:
                    written += shoot_phase(
                        browser, f"http://127.0.0.1:{port}", wanted, views, args
                    )
                finally:
                    kill(proc)
        finally:
            browser.close()

    if args.compare:
        diff(written)
    if args.fail_on_console and any(e for _, _, _, errs in written for e in errs):
        return 1
    return 0


def diff(written):
    """Pixel-diff each shot against its baseline, if one exists."""
    try:
        from PIL import Image, ImageChops
    except ImportError:
        print("compare needs Pillow: pip install pillow")
        return

    for view, route, out, _ in written:
        ref = BASELINE / view / f"{route}.png"
        if not ref.is_file():
            print(f"  {view}/{route}: no baseline yet, {out.name} becomes it")
            BASELINE.mkdir(parents=True, exist_ok=True)
            (BASELINE / view).mkdir(parents=True, exist_ok=True)
            out.replace(ref)
            continue
        a, b = Image.open(ref).convert("RGB"), Image.open(out).convert("RGB")
        if a.size != b.size:
            print(f"  {view}/{route}: size changed {a.size} -> {b.size}")
            continue
        bbox = ImageChops.difference(a, b).getbbox()
        if bbox is None:
            print(f"  {view}/{route}: identical")
        else:
            changed = sum(
                1
                for px in ImageChops.difference(a, b).convert("L").getdata()
                if px > 8
            )
            pct = 100.0 * changed / (a.size[0] * a.size[1])
            print(f"  {view}/{route}: {pct:.1f}% of pixels changed, first diff at {bbox}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--route", choices=[*ROUTES, "board"])
    ap.add_argument("--view", choices=list(VIEWS))
    ap.add_argument("--baseline", action="store_true", help="write to .screens/baseline")
    ap.add_argument("--compare", action="store_true", help="diff against .screens/baseline")
    ap.add_argument("--retina", action="store_true")
    ap.add_argument("--fail-on-console", action="store_true")
    args = ap.parse_args()
    raise SystemExit(shoot(args))


if __name__ == "__main__":
    main()
