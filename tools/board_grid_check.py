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
from utils.board.payload import DISPLAY_ARC_PAST  # noqa: E402
from utils.task_helpers import OVERDUE_DAYS  # noqa: E402


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
    out.push({
      name: (group.querySelector('.group__name') || {}).textContent || '',
      tracks: getComputedStyle(items).gridTemplateColumns.split(' ').filter(Boolean).length,
      rows: rows.map(function (r) { return r.items.map(function (i) { return i.title; }); }),
      // The count in the heading has to equal the rows under it. These used to
      // disagree whenever a group overflowed its cap, which is how a wall could
      // say "6 tasks" over four of them and send the rest to another app.
      counted: parseInt(
        (group.querySelector('.group__count') || {}).textContent || '', 10),
      listed: items.querySelectorAll('.task').length,
      // No "+N more, shown in the classic app" note is left anywhere.
      remainderNotes: document.querySelectorAll('.more').length,
      // A live row is one the canvas will accept a tap on. The canvas sets
      // role="button" only when there is an action, so this is read from the
      // rendered element rather than from the payload the canvas was given.
      liveRows: items.querySelectorAll('.task--live[role="button"]').length,
      lockedRows: items.querySelectorAll('.task--locked').length,
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
      // Whether the whole list is reachable by scrolling rather than being cut
      // off with a pointer somewhere else. The stage is the scroller, so a lane
      // taller than it is fine and a document that scrolls is not.
      laneOverflowsStage: (function () {
        const stage = document.querySelector('.stage');
        if (!stage) return false;
        return stage.scrollHeight > stage.clientHeight + 1
          && getComputedStyle(stage).overflowY !== 'auto'
          && getComputedStyle(stage).overflowY !== 'scroll';
      })(),
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


ARC_MEASURE = """() => {
  const nodes = Array.from(document.querySelectorAll('.arc__node'));
  return {
    total: nodes.length,
    today: nodes.filter(function (n) { return n.classList.contains('arc__node--today'); }).length,
    selected: nodes.filter(function (n) { return n.classList.contains('arc__node--selected'); }).length,
    both: nodes.filter(function (n) {
      return n.classList.contains('arc__node--today') && n.classList.contains('arc__node--selected');
    }).length,
    // The big disc is the one drawn at the larger radius, so "which day is
    // emphasised" is read off the radius rather than off the class the canvas
    // sets, which would only prove the canvas agrees with itself.
    discRadii: nodes.map(function (n) {
      const d = n.querySelector('.arc__disc');
      return d ? d.getAttribute('r') : null;
    }),
    // Read the actual painted colour too. The class and the radius could both be
    // right while the fill rule still points at the wrong flag, which is exactly
    // what happened: the accent fill was on --today, so browsing back left the
    // selected day a small plain disc and lit up the day nobody was on.
    discFills: nodes.map(function (n) {
      const d = n.querySelector('.arc__disc');
      return d ? getComputedStyle(d).fill : null;
    }),
    // Which disc actually carries the bright fill, and which are the accent blue.
    brightFill: (function () {
      const seen = new Map();
      nodes.forEach(function (n, i) {
        const d = n.querySelector('.arc__disc');
        if (d) seen.set(getComputedStyle(d).fill, (seen.get(getComputedStyle(d).fill) || 0) + 1);
      });
      return Array.from(seen.entries());
    })(),
    // The index of the only large disc, and of the today-flagged one, so they
    // can be compared rather than assumed to be the same day.
    bigIndex: nodes.findIndex(function (n) {
      const d = n.querySelector('.arc__disc');
      return d && Number(d.getAttribute('r')) > 18;
    }),
    todayIndex: nodes.findIndex(function (n) {
      return n.classList.contains('arc__node--today');
    }),
    selectedIndex: nodes.findIndex(function (n) {
      return n.classList.contains('arc__node--selected');
    }),
    todayRingWidth: (function () {
      const n = nodes.find(function (n) { return n.classList.contains('arc__node--today'); });
      if (!n) return null;
      const d = n.querySelector('.arc__disc');
      return d ? getComputedStyle(d).strokeWidth : null;
    })(),
    labels: nodes.map(function (n) { return n.getAttribute('aria-label'); }),
    fills: document.querySelectorAll('.arc__fill').length,
  };
}"""


def check_arc(page, label):
    """The strip has to be a week, with the emphasis on the selected day.

    Read from the rendered DOM -- the disc radius and the painted fill -- because
    the bug this guards was a day drawn large and captioned "Today" while the
    real today sat beside it. The classes alone would not have caught it, and
    neither would the radius alone once the emphasis moved to the selection.
    """
    frame = board_frame(page)
    if frame is None:
        raise SystemExit(f"{label}: no board frame")
    arc = frame.evaluate(ARC_MEASURE)

    problems = []
    print(
        f"    arc nodes={arc['total']} today={arc['today']} "
        f"selected={arc['selected']} both={arc['both']} radii={arc['discRadii']}"
    )
    print(
        f"        big={arc['bigIndex']} today={arc['todayIndex']} "
        f"selected={arc['selectedIndex']} todayRing={arc['todayRingWidth']}"
    )
    for text in arc["labels"]:
        print(f"        {text}")
    if arc["total"] != 7:
        problems.append(f"{arc['total']} day cells, want 7 (three back, today, three ahead)")
    if arc["today"] != 1:
        problems.append(f"{arc['today']} day(s) drawn as today, want exactly 1")
    if arc["selected"] != 1:
        problems.append(f"{arc['selected']} day(s) drawn as selected, want exactly 1")
    if arc["both"] != 1:
        problems.append(
            f"{arc['both']} day(s) drawn as both today and selected, want 1 -- "
            "browsing today marks the same day twice"
        )
    if len({r for r in arc["discRadii"] if r}) < 2:
        problems.append("every day is drawn the same size, so the selection is not emphasised")
    if arc["fills"]:
        problems.append(
            f"{arc['fills']} progress fill(s) drawn, want 0 -- each disc already "
            "carries that day's own completion percentage"
        )
    # The big disc must be the selected day, which is the whole of point 2. On
    # the default view those are the same day, so this also confirms today is
    # the middle cell rather than an end one.
    if arc["bigIndex"] != arc["selectedIndex"]:
        problems.append(
            f"the large disc is cell {arc['bigIndex']} but the selected day is "
            f"cell {arc['selectedIndex']} -- the blue circle has to follow the "
            "selection, not the real today"
        )
    if arc["bigIndex"] < 0:
        problems.append("no disc is drawn large, so nothing marks the selected day")
    # The real today has to stay findable when it is not the selected day, which
    # is a ring on a normal-size disc. On this default view the two coincide, so
    # only the radius is checkable here; browsing back is the payload's test.
    if arc["todayIndex"] != 3:
        problems.append(
            f"the real today is cell {arc['todayIndex']}, want the middle one (3) "
            "of a seven-day strip"
        )
    # The large disc must be the only one painted the bright accent. The rest of
    # the strip shares the surface colour, which is the point -- one bright
    # circle, six ordinary discs.
    counts = {fill: n for fill, n in arc["brightFill"]}
    big_fill = arc["discFills"][arc["bigIndex"]] if arc["bigIndex"] >= 0 else None
    if big_fill is not None and counts.get(big_fill) != 1:
        problems.append(
            f"the large disc's fill {big_fill} is used by "
            f"{counts.get(big_fill)} cell(s) -- the bright circle has to mark "
            "exactly one day"
        )
    # And the ordinary days must not each get a bright fill of their own.
    bright = {f: n for f, n in counts.items() if n == 1 and f != big_fill}
    if bright:
        problems.append(
            f"{len(bright)} other cell(s) painted a unique fill besides the "
            f"selected day: {list(bright)}"
        )
    for problem in problems:
        print(f"    FAIL {problem}")
    return not problems


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
        # The heading count is the number of rows under it, now that nothing is
        # capped. A group that overflowed used to advertise more than it showed.
        if group["counted"] != group["listed"]:
            problems.append(
                f"{group['name']}: heading says {group['counted']} but {group['listed']} "
                "row(s) are listed"
            )
        if group["laneOverflowsStage"]:
            problems.append(
                f"{group['name']}: the lane is taller than the stage, which does not "
                "scroll -- the bottom of the list would be unreachable"
            )
    if any(g["remainderNotes"] for g in groups):
        problems.append(
            f"{sum(g['remainderNotes'] for g in groups)} '+N more' note(s) still "
            "rendered -- every task has to be listed, not summarised"
        )
    for problem in problems:
        print(f"    FAIL {problem}")
    return not problems


def check_future_day(page, label):
    """Select a future day and confirm every row on it refuses to be tapped.

    This is point 3, checked on the rendered board rather than the payload. The
    seven-day strip only became safe once future rows stopped looking live, and
    the canvas signals that with a missing `action` -- so a row here must have
    neither the button role nor a tick, or a child taps a chore that cannot
    honestly be earned yet.

    Selecting a day sends a message to the app, so this is a real round trip
    through the same code path a tap takes.
    """
    frame = board_frame(page)
    if frame is None:
        raise SystemExit(f"{label}: no board frame")

    picked = frame.evaluate(SELECT_A_FUTURE_DAY)
    if not picked:
        print("    (no future day with work on it; lock check skipped)")
        return True

    frame.wait_for_timeout(1200)
    rows = frame.evaluate(FUTURE_ROWS)
    problems = []
    print(
        f"    future day {picked}: rows={rows['rows']} locked={rows['locked']} "
        f"live={rows['live']} ticks={rows['ticks']} captions={sorted(set(rows['labels']))}"
    )
    if rows["rows"] == 0:
        print("    (that day rendered no rows; nothing to lock)")
        return True
    if rows["live"]:
        problems.append(
            f"{rows['live']} row(s) on a future day are clickable -- they must not be"
        )
    if rows["ticks"]:
        problems.append(
            f"{rows['ticks']} tick(s) drawn on a future day -- the affordance is the lie"
        )
    if rows["locked"] != rows["rows"]:
        problems.append(
            f"only {rows['locked']} of {rows['rows']} future rows are marked locked"
        )
    for problem in problems:
        print(f"    FAIL {problem}")
    return not problems


# Click the first future cell in the strip, found by walking right from the
# real today rather than from the selection. The selection may already have been
# moved onto a past day by the check that runs before this one, and stepping one
# cell to its right would then land on today and prove nothing. Returns the
# cell's aria-label so the failure message names the day that was tested.
SELECT_A_FUTURE_DAY = """() => {
  const nodes = Array.from(document.querySelectorAll('.arc__node'));
  const today = nodes.findIndex(function (n) {
    return n.classList.contains('arc__node--today');
  });
  const forward = nodes.slice(today + 1);
  if (!forward.length) return null;
  forward[0].dispatchEvent(new MouseEvent('click', {bubbles: true}));
  return forward[0].getAttribute('aria-label');
}"""


FUTURE_ROWS = """() => {
  const rows = Array.from(document.querySelectorAll('.group__items .task'));
  return {
    rows: rows.length,
    locked: rows.filter(function (r) { return r.classList.contains('task--locked'); }).length,
    live: rows.filter(function (r) { return r.classList.contains('task--live'); }).length,
    ticks: rows.filter(function (r) { return r.querySelector('.task__tick'); }).length,
    labels: rows.map(function (r) {
      const chip = r.querySelector('.task__lock');
      return chip ? chip.textContent : '';
    }),
  };
}"""


def check_past_day(page, label):
    """Past days inside the tick window are live; the ones past it are records.

    Undo used to be the real today alone, on the grounds that reopening from a
    past day rewrites a week whose points have already been counted. But the
    tick window is two days back as well, so a chore could be *finished* from
    two days ago and not *corrected* from there -- the wall offered a live tick
    on the real today for work the same day would have accepted. Today and the
    days behind it inside the window are now live both ways; the oldest day on
    the strip stays a record.

    Checked on the rendered board rather than the payload, because the thing that
    invites the tap is the tick and the button role on the row.
    """
    frame = board_frame(page)
    if frame is None:
        raise SystemExit(f"{label}: no board frame")

    ok = True
    for back in range(1, DISPLAY_ARC_PAST + 1):
        live_expected = back <= OVERDUE_DAYS
        here = frame.evaluate(SELECT_PAST_DAY, back)
        if not here:
            print(f"    (no day {back} back on the strip; skipped)")
            continue

        frame.wait_for_timeout(1200)
        rows = frame.evaluate(DONE_ROWS)
        verdict = "live" if live_expected else "a record"
        print(
            f"    {back} day(s) back, {here}: done rows={rows['done']} "
            f"reopenTicks={rows['reopen']} locked={rows['locked']} "
            f"live={rows['live']} chips={sorted(set(rows['chips']))} -- {verdict}"
        )

        problems = []
        if rows["done"] == 0:
            print("    (that day has no finished work; nothing to undo)")
            continue
        if live_expected:
            if not rows["reopen"]:
                problems.append(
                    f"{back} day(s) back is inside the {OVERDUE_DAYS}-day window, so a "
                    "finished chore there should offer undo"
                )
            if not rows["live"]:
                problems.append(
                    f"{back} day(s) back: finished rows are not clickable inside the window"
                )
        else:
            if rows["reopen"]:
                problems.append(
                    f"{rows['reopen']} reopen tick(s) {back} day(s) back -- that is "
                    f"outside the {OVERDUE_DAYS}-day window and is a record"
                )
            if rows["live"]:
                problems.append(
                    f"{rows['live']} row(s) {back} day(s) back are clickable, outside the window"
                )
        # A finished chore captioned "Past due" reads as work still owing.
        if any("Past due" in chip for chip in rows["chips"]):
            problems.append(
                f"a finished chore is captioned {sorted(set(rows['chips']))} -- the "
                "tick rule's lock does not apply to work that is already done"
            )
        for problem in problems:
            print(f"    FAIL {problem}")
        ok = ok and not problems

    return ok


# Walk back from the *real today* cell, not from whatever is selected, so each
# probe is a fixed number of days back however many times this runs.
SELECT_PAST_DAY = """(back) => {
  const nodes = Array.from(document.querySelectorAll('.arc__node'));
  const today = nodes.findIndex(function (n) {
    return n.classList.contains('arc__node--today');
  });
  if (today < 0) return null;
  const target = nodes[today - back];
  if (!target) return null;
  target.dispatchEvent(new MouseEvent('click', {bubbles: true}));
  return target.getAttribute('aria-label');
}"""


DONE_ROWS = """() => {
  const groups = Array.from(document.querySelectorAll('.group--done'));
  const rows = Array.from(document.querySelectorAll('.group--done .task'));
  return {
    done: rows.length,
    reopen: rows.filter(function (r) { return r.querySelector('.task__tick--reopen'); }).length,
    live: rows.filter(function (r) { return r.classList.contains('task--live'); }).length,
    locked: rows.filter(function (r) { return r.classList.contains('task--locked'); }).length,
    chips: rows.map(function (r) {
      const c = r.querySelector('.task__lock');
      return c ? c.textContent : '';
    }),
  };
}"""


def check_people_colours(page, label, want_lightness):
    """Every person has to keep their own colour, in this mode.

    A contrast check cannot see this failure. The Board builds each person's
    colour in the browser as `oklch(calc(var(--person-lightness) + lift) ...)`,
    so if that composition is unsupported -- or if the token is renamed -- the
    declaration is dropped, every person falls back to the shared accent, and
    each one is still perfectly legible. The wall just stops telling anybody
    apart, which is the only thing the colours are for.
    """
    frame = board_frame(page)
    if frame is None:
        raise SystemExit(f"{label}: no board frame")
    got = frame.evaluate(PERSON_COLOURS)

    points = [c for c in got["points"] if c]
    problems = []
    print(f"    theme={got['theme']} person-lightness={got['lightness']}")
    for i, colour in enumerate(points):
        print(f"        [{i}] {colour}")

    # Lightness, read back out of the painted colour, is the token plus lift.
    import re as _re

    lights = []
    for colour in points:
        m = _re.match(r"oklch\(([0-9.]+)", colour)
        if m:
            lights.append(float(m.group(1)))
    if not lights:
        problems.append("no person colour resolved to an oklch() value")
    elif abs(max(lights) - want_lightness) > 0.12 or abs(min(lights) - want_lightness) > 0.12:
        problems.append(
            f"person lightness spans {min(lights):.2f}..{max(lights):.2f}, "
            f"expected to sit near {want_lightness} -- the mode's base is not reaching them"
        )
    # The point of the six: they have to be six, not one repeated.
    accents_only = [c for c in points if c != got["accent"]]
    if len(set(accents_only)) < 2:
        problems.append(
            f"{len(accents_only)} person colours are all {accents_only[:1]} -- they "
            "have collapsed onto the shared accent"
        )
    for problem in problems:
        print(f"    FAIL {problem}")
    return not problems


PERSON_COLOURS = """() => {
  const de = document.documentElement;
  return {
    theme: de.getAttribute('data-theme'),
    lightness: getComputedStyle(de).getPropertyValue('--person-lightness').trim(),
    accent: getComputedStyle(de).getPropertyValue('--accent').trim(),
    points: Array.from(document.querySelectorAll('.person__points')).map(function (n) {
      return getComputedStyle(n).color;
    }),
  };
}"""


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
                ok = check_arc(page, label) and ok
                # Both navigate to another day, so they run last: they would
                # otherwise leave the layout checks looking at a read-only day.
                ok = check_past_day(page, label) and ok
                ok = check_future_day(page, label) and ok
                if errors:
                    print(f"    FAIL page errors: {errors}")
                    ok = False
                page.close()

            # Day mode, once, at the wall size. The layout is a function of width
            # and not of lighting, so the seven-viewport sweep above does not need
            # repeating in both modes -- but the person colours are recomposed per
            # mode in the browser, and that path exists nowhere else.
            print("  day 1280x800")
            day = browser.new_page(viewport={"width": 1280, "height": 800})
            day.add_init_script(
                "try { localStorage.setItem('family-task-theme', 'day'); } catch (e) {}"
            )
            day.goto(f"http://127.0.0.1:{port}", wait_until="domcontentloaded")
            settle(day)
            day.wait_for_timeout(1200)
            ok = check_people_colours(day, "day 1280x800", 0.45) and ok
            day.close()
            browser.close()
        print("PASS" if ok else "FAILED")
        return 0 if ok else 1
    finally:
        if proc is not None:
            kill(proc)


if __name__ == "__main__":
    raise SystemExit(main())
