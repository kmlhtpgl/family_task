"""Drive the Phase 1 spike and assert the three technical risks are retired.

    python tools/spike_check.py

1. the component frame fills the host viewport
2. the webfont loads and applies inside the frame
3. a click in the frame reaches Python, Python writes, the new payload comes
   back down, and the whole round trip is fast enough to hide behind optimistic
   UI

Exits non-zero if any of them fails, with the measurement that failed.
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from shoot import free_port, kill, settle, start_app  # noqa: E402

SPIKE = "spike.py"

READ_PROBE = """
(el) => {
  const node = document.querySelector(`[data-probe="${el}"]`);
  return node ? node.textContent : null;
}
"""


def main():
    from playwright.sync_api import sync_playwright

    port = free_port()
    proc = start_app(
        port, script=SPIKE, env_overrides={"FAMILY_TASK_SPIKE_REAL_WRITE": "0"}
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
            settle(page)

            frame = page.frame_locator("iframe").first

            def probe(name):
                return frame.locator(f'[data-probe="{name}"]').inner_text()

            # 1. does the frame fill the viewport?
            iframe_box = page.locator("iframe").first.bounding_box()
            frame_height = probe("frame-height")
            parent_viewport = probe("parent-viewport")
            results.append(
                check(
                    "frame fills viewport",
                    iframe_box and abs(iframe_box["height"] - 800) <= 2,
                    f"iframe box={iframe_box}, frame reports {frame_height}, "
                    f"host viewport {parent_viewport}",
                )
            )

            # 2. does the webfont actually apply?
            font = (probe("font") or "").split("=")[-1].strip()
            inter = probe("inter-400")
            results.append(
                check(
                    "webfont applies",
                    font.startswith("Inter") and inter == "inter-400 = yes",
                    f"font={font!r}, {inter!r}",
                )
            )

            # 3. does a click round-trip, and land exactly once?
            t0 = time.perf_counter()
            frame.locator("#spike-click").click()
            page.wait_for_function(
                "() => !document.querySelector('[data-testid=\"stStatusWidget\"]')",
                timeout=20_000,
            )
            page.wait_for_load_state("networkidle")
            elapsed_ms = (time.perf_counter() - t0) * 1000
            settle(page, timeout=20_000)

            body = page.locator("body").inner_text().replace("\n", " ")
            results.append(
                check(
                    "click reaches Python and writes",
                    "applied = [1]" in body and "writes = 1" in body,
                    f"python side: {body[:180]}",
                )
            )
            results.append(
                check(
                    "payload reaches the frame",
                    int((probe("people") or "0").split("=")[-1].strip()) == 3,
                    f"{probe('people')!r}",
                )
            )

            # Clicking again is what actually tests the dedupe. Streamlit keeps a
            # widget's value until it changes, so the second rerun sees seq=1
            # sitting in the channel as well as seq=2. Without comparing seq, the
            # stale value would be written again and applied would read [1, 1, 1].
            frame.locator("#spike-click").click()
            page.wait_for_function(
                "() => !document.querySelector('[data-testid=\"stStatusWidget\"]')",
                timeout=20_000,
            )
            page.wait_for_load_state("networkidle")
            settle(page, timeout=20_000)
            body2 = page.locator("body").inner_text().replace("\n", " ")
            results.append(
                check(
                    "action is handled exactly once",
                    "applied = [1, 1]" in body2 and "writes = 2" in body2,
                    f"two clicks, two writes: {body2[-120:]}",
                )
            )
            results.append(
                check(
                    "round trip is fast enough to hide",
                    elapsed_ms < 1500,
                    f"{elapsed_ms:.0f}ms click to painted payload",
                )
            )
            results.append(
                check("no console errors", not errors, f"{errors[:3]}")
            )
            browser.close()
    finally:
        kill(proc)

    print("\nPhase 1 spike")
    for name, ok, detail in results:
        print(f"  {'PASS' if ok else 'FAIL'}  {name}")
        print(f"        {detail}")
    return 0 if all(ok for _, ok, _ in results) else 1


def check(name, ok, detail):
    return (name, bool(ok), detail)


if __name__ == "__main__":
    raise SystemExit(main())
