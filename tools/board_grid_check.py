"""Measure the board's real task layout in a browser.

    python tools/board_grid_check.py

Screenshots cannot be read back in every session, so this asserts against the
rendered DOM instead: the number of resolved column tracks on each group, the
row each task actually landed on, whether titles are clipped, and whether the
rendered order matches the payload's alphabetical one. Two per row is easy to
claim in CSS and easy to get wrong, so the check is the layout itself.

The board is read from whatever the app is pointed at, so this renders real
tasks and measures those. It writes nothing.

Run at the wall tablet size and at phone size: the narrow fallback is a
deliberately different layout, so the expectation differs by viewport.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "tools"))

from shoot import free_port, kill, settle, start_app  # noqa: E402


MEASURE = """() => {
  const out = [];
  document.querySelectorAll('.group').forEach(function (group) {
    const items = group.querySelector('.group__items');
    if (!items) return;
    const rows = [];
    Array.from(items.querySelectorAll('.task')).forEach(function (task) {
      const box = task.getBoundingClientRect();
      const title = task.querySelector('.task__title');
      const tbox = title.getBoundingClientRect();
      const top = Math.round(box.top);
      let slot = rows.findIndex(function (r) { return Math.abs(r.top - top) < 4; });
      if (slot === -1) { rows.push({top: top, items: []}); slot = rows.length - 1; }
      const lineHeight = parseFloat(getComputedStyle(title).lineHeight) || 20;
      rows[slot].items.push({
        title: title.textContent,
        // A title hidden by the two-line clamp, as opposed to one that wrapped
        // inside its cell: the first loses information, the second does not.
        clipped: title.scrollHeight > title.clientHeight + 1,
        lines: Math.round(title.scrollHeight / lineHeight),
        overflows: tbox.right > box.right - 1,
      });
    });
    const more = items.querySelector('.more');
    out.push({
      name: (group.querySelector('.group__name') || {}).textContent || '',
      tracks: getComputedStyle(items).gridTemplateColumns.split(' ').filter(Boolean).length,
      rows: rows.map(function (r) { return r.items.map(function (i) { return i.title; }); }),
      clipped: Array.from(items.querySelectorAll('.task__title')).filter(
        function (el) { return el.scrollHeight > el.clientHeight + 1; }).length,
      maxLines: Math.max(0, ...Array.from(items.querySelectorAll('.task__title')).map(
        function (el) {
          const lh = parseFloat(getComputedStyle(el).lineHeight) || 20;
          return Math.round(el.scrollHeight / lh);
        })),
      overflows: Array.from(items.querySelectorAll('.task')).filter(function (task) {
        const t = task.querySelector('.task__title');
        return t.getBoundingClientRect().right > task.getBoundingClientRect().right - 1;
      }).length,
      // Whether the remainder note covers the whole list rather than one cell.
      // Measured against the list, not a task: in the single-column fallback a
      // task is the same width as the list, so comparing to a task would pass
      // a note that is stuck in a track.
      moreSpansRow: more ? Math.abs(
          more.getBoundingClientRect().width - items.getBoundingClientRect().width) < 2
        : null,
    });
  });
  return out;
}"""


def board_frame(page):
    """The board is the declared component; the kiosk frame is the one before it."""
    for frame in page.frames:
        if frame == page.main_frame:
            continue
        try:
            if frame.query_selector(".board"):
                return frame
        except Exception:
            continue
    return None


def open_a_lane(page):
    """The board lands on Everyone; a person has to be chosen to get task rows.

    Choosing rebuilds the rail, so the button is looked up again by index for
    each attempt rather than held as a handle across the click.
    """
    frame = board_frame(page)
    count = len(frame.query_selector_all(".person"))
    for index in range(1, count):
        person = frame.query_selector_all(".person")[index]
        name = person.query_selector(".person__name").text_content()
        person.click()
        page.wait_for_timeout(900)
        if frame.query_selector_all(".group__items .task"):
            return frame, name
    return frame, None


def check(page, label, expect_tracks, expect_two_up):
    frame, who = open_a_lane(page)
    if frame is None:
        raise SystemExit(f"{label}: no board frame")
    if not who:
        raise SystemExit(f"{label}: no person's lane rendered any task rows")
    groups = frame.evaluate(MEASURE)
    if not groups:
        raise SystemExit(f"{label}: {who}'s lane rendered no groups")

    problems = []
    for group in groups:
        shown = [row for row in group["rows"] if row]
        widest = max((len(row) for row in shown), default=0)
        titles = [t for row in shown for t in row]
        print(
            f"    {group['name'] or '(unnamed)':<9} tracks={group['tracks']} "
            f"tasks={len(titles)} rows={len(shown)} widest={widest} "
            f"maxLines={group['maxLines']} clipped={group['clipped']}"
        )
        for row in shown:
            print(f"        {row}")
        if group["tracks"] != expect_tracks:
            problems.append(
                f"{group['name']}: {group['tracks']} column track(s), want {expect_tracks}"
            )
        if expect_two_up and widest > 2:
            problems.append(f"{group['name']}: a row holds {widest} tasks, want at most 2")
        if expect_two_up and len(titles) > 1 and len(shown[0]) < 2:
            problems.append(f"{group['name']}: first row holds {len(shown[0])} task(s)")
        if not expect_two_up and widest != 1:
            problems.append(f"{group['name']}: narrow fallback put {widest} on a row")
        if group["clipped"]:
            problems.append(
                f"{group['name']}: {group['clipped']} title(s) cut off after two lines"
            )
        if group["maxLines"] > 2:
            problems.append(
                f"{group['name']}: a title runs to {group['maxLines']} lines"
            )
        if group["overflows"]:
            problems.append(
                f"{group['name']}: {group['overflows']} title(s) spill past their row"
            )
        if titles != sorted(titles, key=lambda s: " ".join(s.split()).casefold()):
            problems.append(f"{group['name']}: rendered order is not alphabetical")
        if group["moreSpansRow"] is False:
            problems.append(f"{group['name']}: the remainder note is stuck in one cell")
    for problem in problems:
        print(f"    FAIL {problem}")
    return not problems


def main():
    port = free_port()
    proc = None
    try:
        proc = start_app(port)
        from playwright.sync_api import sync_playwright

        ok = True
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            # Two-up is a function of how wide the list is, not of the window:
            # the rail takes a different bite at each size. 1180 is the first
            # width where a task still has room for a readable title, so 1024
            # is below it and 1280 is above. The wall tablet is the target
            # device, so 1280 and 1920 are the two that must be two-up.
            for label, size, tracks, two_up in (
                ("wall 1280x800", {"width": 1280, "height": 800}, 2, True),
                ("wall-hd 1920x1080", {"width": 1920, "height": 1080}, 2, True),
                ("desktop 1440x900", {"width": 1440, "height": 900}, 2, True),
                ("laptop 1180", {"width": 1180, "height": 900}, 2, True),
                ("small 1024", {"width": 1024, "height": 900}, 1, False),
                ("tablet 820x1180", {"width": 820, "height": 1180}, 1, False),
                ("phone 390x844", {"width": 390, "height": 844}, 1, False),
            ):
                print(f"  {label}")
                page = browser.new_page(viewport=size)
                errors = []
                page.on("pageerror", lambda e: errors.append(str(e)))
                page.goto(f"http://127.0.0.1:{port}", wait_until="domcontentloaded")
                # networkidle is racy when the page holds a connection open, and
                # a timeout there says nothing about the layout. Retried rather
                # than raised, so a flake is not read as a regression.
                for attempt in range(3):
                    try:
                        settle(page)
                        break
                    except Exception as exc:
                        if attempt == 2:
                            raise SystemExit(
                                f"{label}: page never settled ({type(exc).__name__})"
                            )
                        print(f"    retrying after settle failed: {type(exc).__name__}")
                        page.wait_for_timeout(3000)
                ok = check(page, label, tracks, two_up) and ok
                if errors:
                    print(f"    FAIL page errors: {errors}")
                    ok = False
                page.close()
            browser.close()
        print("PASS" if ok else "FAILED")
        return 0 if ok else 1
    finally:
        if proc is not None:
            kill(proc)


if __name__ == "__main__":
    raise SystemExit(main())
