"""Prove the board actually writes, end to end, against the real app.

    path/to/venv/bin/python tools/spike_check.py

The bridge is the one place where a bug is invisible to every other test. The
component test in tests/test_board_payload.py proves Python builds a payload;
the shell test proves Python hands it over. Neither proves that a tap on a
task in a browser reaches the data layer and comes back as a painted change.
So this drives the real app.py -- served by tools/preview.py against the
committed fixtures -- in a real browser, and checks the round trip.

1. the component frame fills the host viewport
2. the webfont loads and applies inside the frame
3. tapping a task writes exactly once and paints the task into Done today
4. tapping it again reopens it and takes it back out
5. a task Python will not let you complete does not pretend otherwise
6. the round trip is fast enough that no optimistic UI is needed

Exits non-zero if any of them fails, with the measurement that failed. Writes go
to the in-memory store in tools/preview.py; the real family database is never
touched.
"""

import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
sys.path.insert(0, str(REPO))
from shoot import free_port, kill, settle, start_app  # noqa: E402

WRITES = Path("/tmp/spike-writes.json")

# Fixture task ids from tests/fixtures.py. Task 1 is due today and not yet
# done, so it is the one the board must offer to complete; task 4 is already
# done today and must be left alone, which is what proves a tap did not just
# repaint the fixture.
TABLE = 1
DONE_TODAY = 4
DONE_TITLE = "Read 20 pages"
# Lanes picked for the two rules being checked: Maryam owes a task due tomorrow,
# which Python refuses, and Zayd owes one due today, which it allows.
LOCKED_LANE = "Maryam"
TAPPABLE_LANE = "Zayd"


def writes():
    return json.loads(WRITES.read_text()) if WRITES.exists() else []


def writes_for(task_id):
    return [w for w in writes() if w.get("task_id") == task_id]


def titles(frame):
    return frame.locator(".task__title").all_inner_texts()


def placement(frame):
    """Where every task currently sits, as "group :: title".

    Titles alone cannot tell a completed task from an open one -- the label is
    the same word either way -- so a check that waits for the title list to
    change would wait forever after a successful completion. Pairing each title
    with its group makes the move out of the open groups and into Done today
    observable from the DOM.
    """
    return frame.evaluate(
        "() => [...document.querySelectorAll('.group')].flatMap(g =>"
        "  (g.querySelector('.group__label')?.textContent.trim() || '?') + ' :: ' +"
        "  [...g.querySelectorAll('.task__title')].map(t => t.textContent.trim()).join(' | ')"
        ")"
    )


def board_frame(page, timeout=20_000):
    """Return the board's child frame, not the Adhan kiosk's.

    The real app mounts two iframes -- the adhan player and the board -- and the
    kiosk one comes first. Selecting `iframe` by position silently targets the
    empty adhan document and every later step times out on a locator that will
    never appear, which reads exactly like a board that failed to render.
    """
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


def select_lane(page, name):
    """Select a person's lane by name and return a freshly acquired board frame.

    Two things make this fiddly enough to be worth a helper. Lane selection is
    asynchronous, so it has to wait on aria-current rather than a sleep. And
    Streamlit rebuilds the iframe on every rerun, so the frame has to be looked
    up again afterwards -- a handle kept across a click can end up reading a
    detached document and reporting a board that is no longer on screen.
    """
    frame = board_frame(page)
    label = frame.locator(".person", has_text=name).first
    label.click()
    frame.wait_for_function(
        "name => {"
        "  const b = [...document.querySelectorAll('.person')]"
        "    .find(n => n.textContent.includes(name));"
        "  return !!b && b.getAttribute('aria-current') === 'true';"
        "}",
        arg=name,
        timeout=10_000,
    )
    page.wait_for_timeout(500)
    return board_frame(page)


def wait_for_idle(page):
    page.wait_for_function(
        '() => !document.querySelector(\'[data-testid="stStatusWidget"]\')',
        timeout=20_000,
    )
    page.wait_for_load_state("networkidle")


def tap(page, frame, title):
    """Tap a task row and wait for the round trip to land.

    Anchoring on the board repainting is what makes this a real test: Streamlit
    reruns, Python writes, the payload comes back, and the frame redraws. If
    Python accepted the action but nothing moved, this waits and then fails,
    rather than passing on the strength of the flash message alone.
    """
    before = placement(frame)
    t0 = time.perf_counter()
    frame.locator(f".task__title:text-is({title!r})").first.click()
    wait_for_idle(page)
    settle(frame.page, timeout=20_000)
    deadline = time.time() + 15
    while time.time() < deadline:
        if placement(frame) != before:
            break
        frame.page.wait_for_timeout(200)
    else:
        raise AssertionError(
            f"tapping {title!r} changed nothing on the board; before={before}"
        )
    return (time.perf_counter() - t0) * 1000


def main():
    from playwright.sync_api import sync_playwright

    WRITES.unlink(missing_ok=True)
    WRITES.with_name(WRITES.stem + "-store.json").unlink(missing_ok=True)
    port = free_port()
    proc = start_app(
        port,
        script=str(REPO / "preview.py"),
        script_args=[str(WRITES)],
    )
    base = f"http://127.0.0.1:{port}"
    results = []
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": 1280, "height": 800})
            errors = []
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.on(
                "console",
                lambda m: errors.append(m.text) if m.type == "error" else None,
            )
            page.goto(base, wait_until="domcontentloaded")
            settle(page, timeout=40_000)
            page.wait_for_timeout(2000)

            frame = board_frame(page)
            frame = select_lane(page, TAPPABLE_LANE)

            # 1. does the frame fill the viewport? The board has no page of its
            # own to scroll, so anything but a full-height frame is a board
            # somebody cannot reach the bottom of.
            box = page.evaluate(
                "() => {"
                "  for (const el of document.querySelectorAll('iframe')) {"
                "    const d = el.contentDocument;"
                "    if (d && d.getElementById('board')) {"
                "      const r = el.getBoundingClientRect();"
                "      return {x: r.x, y: r.y, width: r.width, height: r.height};"
                "    }"
                "  }"
                "  return null;"
                "}"
            )
            results.append(
                check(
                    "frame fills viewport",
                    box and abs(box["height"] - 734) <= 4 and box["x"] == 0,
                    f"iframe box={box}, expected 1280x734 at x=0",
                )
            )

            # 2. does the webfont actually apply inside the frame?
            font = frame.locator("body").evaluate("n => getComputedStyle(n).fontFamily")
            results.append(
                check(
                    "webfont applies",
                    "Inter" in font,
                    f"body font-family={font!r}",
                )
            )

            # 3. the round trip. "Set the table" is due today, so tapping it
            # must move it out of the open groups and into Done today.
            elapsed = tap(page, frame, "Set the table")
            after_tap = placement(frame)
            done_now = frame.locator(".group--done").filter(
                has_text="Set the table"
            ).count()
            results.append(
                check(
                    "tapping a task writes once",
                    len(writes_for(TABLE)) == 1,
                    f"writes for {TABLE}: {writes_for(TABLE)}",
                )
            )
            results.append(
                check(
                    "completed task is written with today's date",
                    bool(writes_for(TABLE))
                    and bool(writes_for(TABLE)[0]["updates"].get("completed_date")),
                    f"updates={writes_for(TABLE)[0]['updates'] if writes_for(TABLE) else None}",
                )
            )
            results.append(
                check(
                    "completed task repaints into Done today",
                    done_now == 1 and not any("Set the table" in g for g in after_tap if not g.startswith("Done")),
                    f"placement now: {after_tap}",
                )
            )
            results.append(
                check(
                    "completed task offers undo",
                    frame.locator(".task__tick--reopen").count() >= 1,
                    f"undo affordances: {frame.locator('.task__tick--reopen').count()}",
                )
            )

            # 4. and back again. Tapping the done task has to reopen it, which
            # means clearing completed_date rather than deleting the row.
            reopen_ms = tap(page, frame, "Set the table")
            after_reopen = placement(frame)
            results.append(
                check(
                    "tapping again reopens",
                    len(writes_for(TABLE)) == 2
                    and writes_for(TABLE)[1]["updates"].get("completed_date") is None,
                    f"second write: {writes_for(TABLE)[1] if len(writes_for(TABLE)) > 1 else None}",
                )
            )
            results.append(
                check(
                    "reopened task leaves Done today",
                    frame.locator(".group--done")
                    .filter(has_text="Set the table")
                    .count()
                    == 0
                    and any("Set the table" in g for g in after_reopen if not g.startswith("Done")),
                    f"placement now: {after_reopen}",
                )
            )

            # 5. the store has to have kept the change across reruns. If it
            # reset per run this test would still pass, because the fixture's
            # own completed task is always in Done today and would paper over a
            # task that never actually moved. So assert the write log too.
            results.append(
                check(
                    "only the tapped task was written",
                    [w["task_id"] for w in writes()] == [TABLE, TABLE],
                    f"whole write log: {writes()}",
                )
            )
            results.append(
                check(
                    "the pre-existing completed task is untouched",
                    len(writes_for(DONE_TODAY)) == 0
                    and any(
                        g.startswith("Done") and DONE_TITLE in g
                        for g in after_reopen
                    ),
                    f"still listed as done: {[g for g in after_reopen if g.startswith('Done')]}",
                )
            )

            # 6. Python's rules have to survive the trip through the browser. A
            # task that cannot be completed must not arrive looking tappable.
            #
            # Select the lane by the name on its rail button rather than by
            # position, and re-acquire the board frame on every step: Streamlit
            # recreates the iframe element on each rerun, so a Frame handle held
            # across a click can go on reading a detached document and report
            # rows from a render that no longer exists. The overview lane is
            # also not a list of tasks at all, so walking by index lands on it
            # first and finds nothing to check.
            lane_rows = {}
            for lane_name in (LOCKED_LANE, TAPPABLE_LANE):
                frame = select_lane(page, lane_name)
                lane_rows[lane_name] = frame.evaluate(
                    "() => [...document.querySelectorAll('.task')].reduce("
                    "  (acc, n) => {"
                    "    const label = n.getAttribute('aria-label');"
                    "    (n.classList.contains('task--locked') ? acc.locked : acc.live)"
                    "      .push({label: label, title:"
                    "        n.querySelector('.task__title')?.textContent.trim()});"
                    "    return acc;"
                    "  }, {locked: [], live: []})"
                )
            locked = lane_rows[LOCKED_LANE]["locked"]
            unlocked = lane_rows[TAPPABLE_LANE]["live"]
            results.append(
                check(
                    "a locked task is present and not tappable",
                    len(locked) > 0
                    and all(row["label"] is None for row in locked)
                    and len(unlocked) > 0
                    and all(row["label"] is not None for row in unlocked),
                    f"{LOCKED_LANE}: {locked}; {TAPPABLE_LANE}: {unlocked}",
                )
            )

            # 7. and one tap must be one write. A family member jabbing at a
            # tick is the common case, not the edge case; every extra write is a
            # second round trip competing with the repaint.
            frame = select_lane(page, TAPPABLE_LANE)
            for _ in range(3):
                frame.locator(f".task__title:text-is('Set the table')").first.click(
                    force=True
                )
                page.wait_for_timeout(30)
            wait_for_idle(page)
            settle(page, timeout=20_000)
            page.wait_for_timeout(1500)
            results.append(
                check(
                    "three rapid taps on one tick write once",
                    len(writes_for(TABLE)) == 3,
                    f"complete, reopen, complete: {writes_for(TABLE)}",
                )
            )

            results.append(
                check(
                    "round trip is fast enough to hide",
                    max(elapsed, reopen_ms) < 4000,
                    f"complete {elapsed:.0f}ms, reopen {reopen_ms:.0f}ms",
                )
            )
            results.append(check("no console errors", not errors, f"{errors[:3]}"))
            browser.close()
    finally:
        kill(proc)

    print("\nboard write round trip")
    for name, ok, detail in results:
        print(f"  {'PASS' if ok else 'FAIL'}  {name}")
        print(f"        {detail}")
    failed = [n for n, ok, _ in results if not ok]
    if failed:
        print(f"\n{len(failed)} failed: {failed}")
    return 1 if failed else 0


def check(name, ok, detail):
    return (name, bool(ok), detail)


if __name__ == "__main__":
    raise SystemExit(main())
