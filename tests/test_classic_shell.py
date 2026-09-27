"""The pages the board does not replace must keep working, page by page.

The board took over the dashboard and the Daily Board. What is left is the
family profiles, the reading and Quran logs, prayer, rewards, meeting and
admin -- none of which the board touches, so each still has to render against
the stubbed data layer.
"""

import pytest

from tests.conftest import markdown_text, widget

# Every destination the classic navbar still offers.
CLASSIC_PAGES = [
    "parents",
    "kids",
    "reading",
    "quran",
    "prayer",
    "rewards",
    "meeting",
    "admin",
]

# Pages that need the password gate opened first.
GATED = {"admin"}


def open_page(at, page, authenticated=True):
    if authenticated and page in GATED:
        at.session_state["admin_authenticated"] = True
    widget(at.button, f"nav_{page}").click().run()
    return at


@pytest.mark.parametrize("page", CLASSIC_PAGES)
def test_classic_page_renders(classic, page):
    at = classic.run()
    assert not at.exception, [str(e.value) for e in at.exception]

    open_page(at, page)

    assert not at.exception, [str(e.value) for e in at.exception]
    assert at.session_state["page"] == page


def test_admin_requires_authentication(classic):
    at = classic.run()
    open_page(at, "admin", authenticated=False)
    assert any("password-protected" in w.value for w in at.warning)


def test_admin_renders_when_authenticated(classic):
    at = classic.run()
    open_page(at, "admin")
    assert not at.exception, [str(e.value) for e in at.exception]
