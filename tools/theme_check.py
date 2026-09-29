"""Verify the Day/Night/Auto switch in a real browser.

    python tools/theme_check.py

The switch crosses three boundaries at once -- browser storage, a component
message, and a Streamlit rerun -- and every one of them can break without an
exception. The failure is also invisible in a screenshot of a single page: the
page paints correctly from localStorage while the control above it still shows
the default, and nothing looks wrong until somebody tries to change it.

So this drives the real thing and asserts the parts that no unit test can reach:

- a device with no saved choice starts on Night, the default
- pressing Day paints the page, moves the control, and persists to localStorage
- a *fresh page* on that same device starts on Day with the control already on
  Day -- the regression this tool exists for, because that is the case the whole
  component exists to fix
- the Board frame follows, and a change from the Board reaches both documents

It reads and clicks only; it never writes to the database behind the app.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "tools"))

from shoot import free_port, kill, settle, start_app  # noqa: E402

THEME_KEY = "family-task-theme"

STATE = """() => {
  const de = document.documentElement;
  const active = document.querySelector(
    '[data-testid="stBaseButton-segmented_controlActive"]'
  );
  let board = null;
  for (let i = 0; i < window.frames.length; i++) {
    try {
      const d = window.frames[i].document;
      if (d && d.querySelector('.board')) {
        board = d.documentElement.getAttribute('data-theme');
      }
    } catch (e) { /* not the board frame */ }
  }
  let stored = null;
  try { stored = window.localStorage.getItem(%r); } catch (e) { stored = 'ERR'; }
  return {
    mode: de.getAttribute('data-mode'),
    control: active ? active.textContent.trim() : null,
    board: board,
    stored: stored,
  };
}""" % THEME_KEY


def read(page):
    return page.evaluate(STATE)


def click(page, label):
    page.click(f'[data-testid="stButtonGroup"] button:has-text("{label}")')
    settle(page)
    page.wait_for_timeout(1000)


def expect(problems, label, got, **want):
    detail = " ".join(f"{k}={got.get(k)!r}" for k in ("mode", "control", "board", "stored"))
    print(f"    {label:24s} {detail}")
    for key, value in want.items():
        if got.get(key) != value:
            problems.append(f"{label}: {key} is {got.get(key)!r}, want {value!r}")


def main():
    port = free_port()
    proc = None
    try:
        proc = start_app(port, env_overrides={"FAMILY_TASK_CLASSIC": "1"})
        from playwright.sync_api import sync_playwright

        problems = []
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            context = browser.new_context(viewport={"width": 1280, "height": 800})

            page = context.new_page()
            errors = []
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.goto(f"http://127.0.0.1:{port}", wait_until="domcontentloaded")
            settle(page)
            page.wait_for_timeout(1200)
            expect(problems, "fresh device", read(page), mode="night", control="Night")

            click(page, "Day")
            expect(
                problems, "after pressing Day", read(page),
                mode="day", control="Day", stored="day",
            )

            # The point of the whole exercise: a new page on a Day device must
            # show Day in the control on its own, without anybody pressing
            # anything. This is what the localStorage component is for.
            fresh = context.new_page()
            fresh.on("pageerror", lambda e: errors.append(str(e)))
            fresh.goto(f"http://127.0.0.1:{port}", wait_until="domcontentloaded")
            settle(fresh)
            fresh.wait_for_timeout(1500)
            expect(
                problems, "reopened on day", read(fresh),
                mode="day", control="Day", stored="day",
            )

            nav = fresh.query_selector('button:has-text("Board")')
            if nav is None:
                problems.append("no Board button in the nav row")
            else:
                nav.click()
                fresh.wait_for_timeout(2600)
                expect(
                    problems, "Board follows day", read(fresh),
                    mode="day", control="Day", board="day",
                )

                click(fresh, "Night")
                fresh.wait_for_timeout(1200)
                expect(
                    problems, "Board changes to night", read(fresh),
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
