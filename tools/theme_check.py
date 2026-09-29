"""Verify the Board's Day/Night/Auto control in a real browser.

    python tools/theme_check.py

The control lives inside the Board frame, writes a localStorage key, and the app
document follows that key through the browser's `storage` event. Every boundary
can break without an exception, and a screenshot of one page cannot catch it: the
Board paints correctly while the app chrome around it stays in the other mode, or
the choice is forgotten on the next visit.

So this drives the real thing and asserts the parts no unit test can reach:

- a device with no saved choice starts on Night, the default
- pressing Day on the Board paints the Board, the app document, and persists
- a *fresh page* on that same device starts on Day with the Board's control
  already on Day -- the case that proves the choice is remembered, not just
  applied once
- a classic page follows the saved mode and carries no control of its own
- pressing Night on the Board returns everything to Night

It reads and clicks only; it never writes to the database behind the app.
"""

import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "tools"))

from shoot import free_port, kill, settle, start_app  # noqa: E402

THEME_KEY = "family-task-theme"

STATE = """() => {
  const de = document.documentElement;
  let board = null;
  let control = null;
  for (const f of document.querySelectorAll('iframe')) {
    try {
      const d = f.contentDocument;
      if (d && d.getElementById('board')) {
        board = d.documentElement.getAttribute('data-theme');
        const active = d.querySelector('.head__mode-opt[aria-pressed="true"]');
        control = active ? active.textContent.trim() : null;
      }
    } catch (e) { /* not the board frame */ }
  }
  let stored = null;
  try { stored = window.localStorage.getItem(%r); } catch (e) { stored = 'ERR'; }
  return { mode: de.getAttribute('data-mode'), control: control, board: board, stored: stored };
}""" % THEME_KEY


def read(page):
    return page.evaluate(STATE)


def board_frame(page, timeout=20_000):
    """The board's own frame, not the kiosk iframe that comes first."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        for frame in page.frames:
            if frame == page.main_frame:
                continue
            try:
                if frame.evaluate("() => !!document.getElementById('board')"):
                    return frame
            except Exception:
                pass
        page.wait_for_timeout(250)
    raise SystemExit("no board frame found; is the board shell serving?")


def press(page, preference):
    """Click one of the Board's three mode buttons."""
    frame = board_frame(page)
    frame.locator('.head__mode-opt[data-pref="%s"]' % preference).click()
    page.wait_for_timeout(600)


def expect(problems, label, got, **want):
    detail = " ".join(
        f"{k}={got.get(k)!r}" for k in ("mode", "control", "board", "stored")
    )
    print(f"    {label:24s} {detail}")
    for key, value in want.items():
        if got.get(key) != value:
            problems.append(f"{label}: {key} is {got.get(key)!r}, want {value!r}")


def main():
    port = free_port()
    proc = None
    try:
        proc = start_app(port)
        from playwright.sync_api import sync_playwright

        problems = []
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            context = browser.new_context(viewport={"width": 1280, "height": 800})

            page = context.new_page()
            errors = []
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.goto(f"http://127.0.0.1:{port}", wait_until="domcontentloaded")
            settle(page, timeout=40_000)
            page.wait_for_timeout(1500)
            expect(
                problems, "fresh device", read(page),
                mode="night", control="Night", board="night",
            )

            press(page, "day")
            expect(
                problems, "after pressing Day", read(page),
                mode="day", control="Day", board="day", stored="day",
            )

            # The point of the whole exercise: a new page on a Day device must
            # come up in Day, with the Board's control already showing Day,
            # without anybody pressing anything.
            fresh = context.new_page()
            fresh.on("pageerror", lambda e: errors.append(str(e)))
            fresh.goto(f"http://127.0.0.1:{port}", wait_until="domcontentloaded")
            settle(fresh, timeout=40_000)
            fresh.wait_for_timeout(1500)
            expect(
                problems, "reopened on day", read(fresh),
                mode="day", control="Day", board="day", stored="day",
            )

            # A classic page has no control of its own but still follows the
            # saved mode. This is the "one setting, every page" half.
            parents = fresh.query_selector('button:has-text("Parents")')
            if parents is None:
                problems.append("no Parents button in the nav row")
            else:
                parents.click()
                settle(fresh, timeout=40_000)
                fresh.wait_for_timeout(1200)
                expect(problems, "classic page follows", read(fresh), mode="day")

                back = fresh.query_selector('button:has-text("Board")')
                if back is None:
                    problems.append("no Board button in the nav row")
                else:
                    back.click()
                    fresh.wait_for_timeout(2600)
                    press(fresh, "night")
                    expect(
                        problems, "Board back to night", read(fresh),
                        mode="night", control="Night", board="night", stored="night",
                    )

            if errors:
                problems.append(f"page errors: {errors[:3]}")

            browser.close()
        for problem in problems:
            print(f"  FAIL {problem}")
        print("PASS" if not problems else "FAILED")
        return 0 if not problems else 1
    finally:
        if proc is not None:
            kill(proc)


if __name__ == "__main__":
    raise SystemExit(main())
