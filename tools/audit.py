"""Measure the rendered UI instead of eyeballing it.

Screenshots are necessary but not sufficient: nobody can diff a picture in a
code review, and a design that is beautiful at 1280px can still be broken at
390px. This walks the live DOM and reports the numbers that actually decide
whether a layout is good -- geometry, resolved type sizes, contrast ratios,
overflow -- so design intent can be asserted rather than described.

    python tools/audit.py                     # audit the running app
    python tools/audit.py --route board
    python tools/audit.py --json out.json

Exits non-zero when a check fails, so it can gate a commit.
"""

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from shoot import (  # noqa: E402
    ROUTES,
    VIEWS,
    free_port,
    kill,
    settle,
    start_app,
    unlock_admin,
)

# ── the checks ─────────────────────────────────────────────────────────────
# Each is (name, fn) where fn returns a list of problem strings. Empty list
# means the check passed.

MIN_CONTRAST = 4.5      # WCAG AA for body text
MIN_CONTRAST_LARGE = 3.0  # AA for text at or above 24px, or 18.66px bold


def _rel_lum(rgb):
    def channel(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = (channel(x) for x in rgb[:3])
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(fg, bg):
    l1, l2 = _rel_lum(fg), _rel_lum(bg)
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)


JS_MEASURE = r"""
() => {
  // Colors are resolved by painting one, not by parsing the computed string.
  // getComputedStyle hands back whatever syntax the author wrote, so oklch(),
  // color-mix() and lab() all arrived here as unparseable text, the node was
  // skipped, and the contrast check silently compared nothing. The board is
  // authored in oklch, which means its "ok contrast" was a pass with no
  // measurements behind it. A 1x1 canvas is exact for every syntax the browser
  // can paint, and it clips out-of-gamut colors the same way the display does.
  const swatch = document.createElement('canvas');
  swatch.width = swatch.height = 1;
  const ctx = swatch.getContext('2d', {willReadFrequently: true});
  const parseRGB = (css) => {
    if (!css || css === 'transparent' || css === 'none') return null;
    // An unparseable value leaves fillStyle at its previous value, so it has to
    // be reset each time or a bad color is measured as the previous node's.
    ctx.clearRect(0, 0, 1, 1);
    ctx.fillStyle = '#000000';
    ctx.fillStyle = css;
    if (ctx.fillStyle === '#000000' && css !== '#000000' && !/^#0{6}$|^black$/i.test(css)) {
      return null;
    }
    ctx.fillRect(0, 0, 1, 1);
    const d = ctx.getImageData(0, 0, 1, 1).data;
    return {rgb: [d[0], d[1], d[2]], a: d[3] / 255};
  };
  const over = (fg, bg) => fg.rgb.map((c, i) => c * fg.a + bg[i] * (1 - fg.a));
  const effectiveBg = (el) => {
    let node = el;
    while (node && node !== document.documentElement) {
      const c = parseRGB(getComputedStyle(node).backgroundColor);
      if (c && c.a > 0.95) return c.rgb;
      node = node.parentElement;
    }
    // A document with no opaque background of its own is painted on the
    // browser's white canvas, so that is the correct answer, not a default.
    const html = parseRGB(getComputedStyle(document.documentElement).backgroundColor);
    return html && html.a > 0.95 ? html.rgb : [255, 255, 255];
  };
  const visible = (el) => {
    const s = getComputedStyle(el);
    if (s.display === 'none' || s.visibility === 'hidden' || parseFloat(s.opacity) === 0) return false;
    const r = el.getBoundingClientRect();
    return r.width > 0 && r.height > 0;
  };

  const texts = [];
  const all = document.querySelectorAll('body *');
  // Overlays that are up on their own schedule, not on the page's. The adhan and
  // the screensaver are time-boxed events: whichever one happens to be showing
  // when the audit lands decides how many font sizes and how much text the page
  // appears to have, so a run can fail on quran and pass on admin for no reason
  // connected to either page. They have their own coverage in
  // tools/spike_check.py, which triggers the adhan deliberately, so the page
  // audit leaves them out and measures the page.
  const transient = (el) => !!el.closest(
    '.adhan, .kiosk-screensaver, .kiosk-audio-status, .kiosk-status,'
    + ' .kiosk-unlock-hint'
  );
  for (const el of all) {
    if (!visible(el)) continue;
    if (transient(el)) continue;
    // only leaf-ish nodes that directly carry text
    const own = Array.from(el.childNodes)
      .filter(n => n.nodeType === 3)
      .map(n => n.textContent.trim())
      .join(' ').trim();
    if (!own) continue;
    const s = getComputedStyle(el);
    const r = el.getBoundingClientRect();
    const bg = effectiveBg(el);
    const fg = parseRGB(s.color);
    texts.push({
      tag: el.tagName.toLowerCase(),
      cls: el.className && typeof el.className === 'string' ? el.className : '',
      text: own.slice(0, 60),
      fontSize: parseFloat(s.fontSize),
      fontWeight: s.fontWeight,
      lineHeight: s.lineHeight,
      // A translucent text color has to be read as the color it actually paints,
      // which is the blend of itself and the surface behind it.
      color: fg ? (fg.a < 1 ? over(fg, bg).map(Math.round) : fg.rgb) : null,
      bg,
      box: {x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height)},
    });
  }

  const de = document.documentElement;
  const overflow = de.scrollWidth - de.clientWidth;

  // An element wider than its box is only a bug if nothing clips it. A
  // deliberately scrollable strip (the people rail on a phone) is wider than
  // its parent by design, and reporting that as a failure is how a real overflow
  // check quietly stops being used.
  const clippedByAncestor = (el) => {
    let node = el.parentElement;
    while (node && node !== de) {
      const ox = getComputedStyle(node).overflowX;
      if (/(auto|scroll|hidden|clip)/.test(ox)) return true;
      node = node.parentElement;
    }
    return false;
  };

  const wide = [];
  for (const el of all) {
    if (!visible(el)) continue;
    const r = el.getBoundingClientRect();
    if (r.width > de.clientWidth + 1) {
      wide.push({
        tag: el.tagName.toLowerCase(),
        cls: typeof el.className === 'string' ? el.className : '',
        w: Math.round(r.width),
        clipped: clippedByAncestor(el),
      });
    }
  }

  // Streamlit scrolls inside its own container rather than the document, so
  // documentElement.scrollWidth is always the viewport width and a layout that
  // overflows horizontally can hide completely from the check above. Find
  // every element that actually scrolls and report those.
  const scrollers = [];
  for (const el of all) {
    if (!visible(el)) continue;
    const s = getComputedStyle(el);
    const scrollsY = /(auto|scroll)/.test(s.overflowY) && el.scrollHeight - el.clientHeight > 1;
    const scrollsX = /(auto|scroll)/.test(s.overflowX) && el.scrollWidth - el.clientWidth > 1;
    if (scrollsY || scrollsX) {
      const r = el.getBoundingClientRect();
      scrollers.push({
        tag: el.tagName.toLowerCase(),
        cls: typeof el.className === 'string' ? el.className.slice(0, 60) : '',
        testid: el.getAttribute('data-testid') || '',
        overflowY: scrollsY ? el.scrollHeight - el.clientHeight : 0,
        overflowX: scrollsX ? el.scrollWidth - el.clientWidth : 0,
        box: {w: Math.round(r.width), h: Math.round(r.height)},
      });
    }
  }

  return {
    viewport: {w: de.clientWidth, h: de.clientHeight},
    docHeight: de.scrollHeight,
    overflowX: overflow,
    overflowing: wide.slice(0, 20),
    scrollers,
    textCount: texts.length,
    texts,
    fontFamily: getComputedStyle(document.body).fontFamily,
  };
}
"""


def check_contrast(measurement):
    problems = []
    measured = 0
    for t in measurement["texts"]:
        if t["color"] is None:
            continue
        measured += 1
        ratio = contrast(t["color"], t["bg"])
        large = t["fontSize"] >= 24 or (t["fontSize"] >= 18.66 and int(t["fontWeight"]) >= 700)
        floor = MIN_CONTRAST_LARGE if large else MIN_CONTRAST
        if ratio < floor:
            problems.append(
                f"{ratio:.2f}:1 (needs {floor}) {t['fontSize']}px "
                f"'{t['text']}' fg={t['color']} bg={t['bg']}"
            )
    # A check that could not read a single color must not report a pass. This is
    # what let the board's oklch palette be declared accessible while nothing was
    # being compared at all.
    if measurement["texts"] and not measured:
        problems.append(
            f"no text color could be read (unparseable colour syntax?) -- "
            f"this is a pass with no measurements behind it"
        )
    return problems


def check_no_horizontal_overflow(measurement):
    problems = []
    if measurement["overflowX"] > 1:
        problems.append(
            f"page scrolls {measurement['overflowX']}px horizontally; "
            f"offenders: {measurement['overflowing'][:3]}"
        )
    return problems


def check_nothing_clips_its_own_text(measurement):
    """An element whose scrollHeight exceeds its box is hiding content."""
    problems = []
    for t in measurement["texts"]:
        if t["box"]["h"] <= 0:
            continue
        # A single line of text in a box much shorter than the font's natural
        # line box means something is clipping it.
        if t["box"]["h"] < t["fontSize"] * 0.75:
            problems.append(
                f"box {t['box']['h']}px tall for {t['fontSize']}px text: '{t['text']}'"
            )
    return problems


def check_nothing_overflows_horizontally(measurement):
    """Catches overflow that actually reaches the screen edge.

    documentElement.scrollWidth is always the viewport width, so an element
    wider than the screen only shows up by asking the elements that scroll --
    and then only for elements no ancestor clips. A strip that scrolls inside
    its own box is a feature; one that spills out of its parent with nowhere to
    go is the bug.
    """
    problems = []
    for o in measurement["overflowing"]:
        if o.get("clipped"):
            continue
        problems.append(f"{o['tag']}.{o['cls']} is {o['w']}px wide and nothing clips it")
    if measurement["overflowX"] > 1:
        problems.append(f"document scrolls {measurement['overflowX']}px horizontally")
    return problems


def report_scroll_depth(measurement):
    """How far the user has to scroll. Not a failure, but worth knowing."""
    return measurement["scrollers"]


def check_type_scale(measurement):
    """The type ramp has to have real steps, not one size used everywhere."""
    # A page holding a heading, a nav row and an empty-state line has three
    # sizes because that is all the text on it -- a fresh database, not a flat
    # design. Demanding four steps of a page with eleven words in it is how a
    # useful heuristic gets ignored: the same check then cries wolf on whichever
    # page happened to be nearly empty, and stops being read on the ones that
    # are not.
    if len(measurement["texts"]) < 15:
        return []
    sizes = sorted({t["fontSize"] for t in measurement["texts"]}, reverse=True)
    if len(sizes) < 4:
        return [f"only {len(sizes)} distinct font size(s) in use: {sizes}"]
    return []


CHECKS = {
    "contrast": check_contrast,
    "no-horizontal-overflow": check_nothing_overflows_horizontally,
    "no-clipped-text": check_nothing_clips_its_own_text,
    "type-scale": check_type_scale,
}


def audit(route="board", view="kiosk", out=None):
    from playwright.sync_api import sync_playwright

    width, height = VIEWS[view]
    port = free_port()
    board = route == "board"
    # The board is the default shell, so auditing a classic page means asking
    # for the classic shell explicitly. Without this the classic routes would
    # quietly measure the board instead and report a clean pass for a page
    # nobody ever looked at.
    proc = start_app(
        port, env_overrides=None if board else {"FAMILY_TASK_CLASSIC": "1"}
    )
    base = f"http://127.0.0.1:{port}"
    report = {}
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": height})
            page.goto(base, wait_until="domcontentloaded")
            settle(page)

            if board:
                # The board is a component iframe, so the interesting document is
                # the child frame, not the host page. Measuring the host would
                # report Streamlit's chrome and say nothing about the canvas.
                page.wait_for_timeout(2000)
                frames = [f for f in page.frames if f != page.main_frame]
                board_frames = [
                    f
                    for f in frames
                    if f.evaluate("() => !!document.getElementById('board')")
                ]
                if not board_frames:
                    raise SystemExit("no board frame found; is the board shell serving?")
                target = board_frames[-1]
                measurement = target.evaluate(JS_MEASURE)
            else:
                if route in ROUTES:
                    target = page.locator("button", has_text=ROUTES[route]).first
                    if target.count():
                        target.click()
                        settle(page)
                    # Admin is a fifth of the app's pages and sits behind a
                    # password, so auditing it without unlocking measured the
                    # login form and called the page covered.
                    if route == "admin" and not unlock_admin(page):
                        raise SystemExit(
                            "admin is locked; set FAMILY_TASK_ADMIN_PASSWORD to audit it"
                        )
                measurement = page.evaluate(JS_MEASURE)

            report[route] = {"view": view, "measurement": measurement, "checks": {}}
            for name, fn in CHECKS.items():
                report[route]["checks"][name] = fn(measurement)
            browser.close()
    finally:
        kill(proc)

    if out:
        Path(out).write_text(json.dumps(report, indent=2))

    return report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--route", default="board", choices=["board", *ROUTES])
    ap.add_argument("--view", default="kiosk", choices=list(VIEWS))
    ap.add_argument("--json")
    ap.add_argument("--show-text", action="store_true", help="print every text node")
    args = ap.parse_args()

    report = audit(args.route, args.view, args.json)
    entry = report[args.route]
    m = entry["measurement"]

    print(f"\n{args.route} @ {args.view}  ({m['viewport']['w']}x{m['viewport']['h']})")
    print(f"  body font      {m['fontFamily']}")
    print(f"  text nodes     {m['textCount']}")
    print(f"  doc height     {m['docHeight']}px")
    for s in m["scrollers"]:
        tag = f"{s['tag']}.{s['cls']}" if s["cls"] else s["tag"]
        print(
            f"  scrolls        {tag} [{s['testid']}] "
            f"y+{s['overflowY']}px x+{s['overflowX']}px in {s['box']['w']}x{s['box']['h']}"
        )

    if args.show_text:
        print("\n  resolved type:")
        for t in sorted(m["texts"], key=lambda x: -x["fontSize"])[:60]:
            print(
                f"    {t['fontSize']:>6.1f}px  w{t['fontWeight']:>4}  "
                f"{t['box']['w']:>5}x{t['box']['h']:<4} @{t['box']['x']:>5},{t['box']['y']:<5} {t['text'][:44]}"
            )

    failed = 0
    print("\n  checks:")
    for name, problems in entry["checks"].items():
        if problems:
            failed += 1
            print(f"    FAIL {name}")
            for p in problems[:12]:
                print(f"         {p}")
            if len(problems) > 12:
                print(f"         ... and {len(problems) - 12} more")
        else:
            print(f"    ok   {name}")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
