"""A profile edit has to be submittable, photo and all.

The editor used to put a plain st.button inside its st.form. Streamlit does not
allow that, so the call raised partway through the form: the name and age
inputs and the save button never rendered, and Streamlit replaced the form with
its own "Missing Submit Button" error. Uploading a photo therefore had nowhere to
be submitted, which is the bug this file exists to keep fixed.

The editor is shared by parents and children, so both roles are held to the same
contract here rather than only the one that was reported.
"""

import pytest

from tests.conftest import widget

PNG = ("face.png", b"\x89PNG\r\n\x1a\nnot-really-a-png", "image/png")


@pytest.fixture
def photos(monkeypatch):
    """Stand in for the photo store, recording uploads and deletions."""
    import utils.storage_helpers as storage

    state = {"uploads": [], "deletes": [], "fail": False, "url": "https://cdn.test/new.png"}

    def upload(content, filename):
        if state["fail"]:
            raise RuntimeError("upload rejected")
        state["uploads"].append((filename, content))
        return state["url"]

    def delete(url):
        state["deletes"].append(url)

    monkeypatch.setattr(storage, "upload_profile_photo", upload)
    monkeypatch.setattr(storage, "delete_profile_photo", delete)
    return state


SECTIONS = {"parents": "Parents", "children": "Children"}


def open_admin(at, section):
    """Land on the admin page and select one of its sections."""
    at.session_state["admin_authenticated"] = True
    widget(at.button, "nav_admin").click().run()
    # The section rail is a radio, so its own widget state is what decides the
    # tab; setting `admin_tab` alone loses to the stored radio value.
    at.session_state["admin_tab"] = section
    at.session_state["admin_tab_radio"] = SECTIONS[section]
    at.run()
    return at


def admin_page(classic, section):
    at = classic.run()
    open_admin(at, section)
    assert not at.exception, [str(e.value) for e in at.exception]
    return at


def submit_buttons(at):
    return [b for b in at.button if getattr(b, "is_form_submitter", False)]


# ── the editor renders something you can actually press ───────────────────────


def test_child_editor_renders_a_save_button(classic):
    at = admin_page(classic, "children")
    widget(at.button, "edit_kid_1").click().run()

    assert not at.exception, [str(e.value) for e in at.exception]
    labels = [b.label for b in submit_buttons(at)]
    assert "Save changes" in labels, f"no save button in {labels}"
    assert not at.error, [e.value for e in at.error]


def test_parent_editor_renders_a_save_button(classic):
    at = admin_page(classic, "parents")
    widget(at.button, "edit_parent_1").click().run()

    assert not at.exception, [str(e.value) for e in at.exception]
    labels = [b.label for b in submit_buttons(at)]
    assert "Save changes" in labels, f"no save button in {labels}"
    assert not at.error, [e.value for e in at.error]


def test_both_editors_can_be_cancelled(classic):
    at = admin_page(classic, "children")
    widget(at.button, "edit_kid_1").click().run()

    cancel = next(b for b in submit_buttons(at) if b.label == "Cancel")
    cancel.click().run()

    assert not at.exception, [str(e.value) for e in at.exception]
    assert at.session_state["editing_kid_id"] is None
    assert not [e for e in at.error if "Missing Submit" in e.value]


def test_no_plain_button_is_ever_placed_inside_a_form():
    """The structural rule behind the crash, checked on the source itself.

    Rendering tests only see the forms that happen to be reached; this one
    notices a button moved into a form anywhere in the admin page, including
    branches no test opens.
    """
    import ast
    from pathlib import Path

    source = Path(__file__).resolve().parent.parent / "app_pages" / "admin.py"
    tree = ast.parse(source.read_text())

    def is_call(node, attr):
        return (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == attr
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "st"
        )

    offenders = []
    for form in [n for n in ast.walk(tree) if isinstance(n, ast.With)]:
        # The body of `with st.form(...)` is the form's whole scope, so a button
        # anywhere in it is one Streamlit will reject.
        if not any(is_call(item.context_expr, "form") for item in form.items):
            continue
        for inner in ast.walk(form):
            if is_call(inner, "button"):
                offenders.append(inner.lineno)

    assert not offenders, (
        "st.button() inside st.form() raises and blanks the rest of the form, "
        f"leaving the editor with no save button: lines {sorted(offenders)}"
    )


# ── the photo actually saves ──────────────────────────────────────────────────


def test_uploading_a_child_photo_saves_with_the_form(classic, photos):
    at = admin_page(classic, "children")
    widget(at.button, "edit_kid_1").click().run()

    widget(at.file_uploader, "edit_kid_form_1_photo").set_value(PNG)
    at.run()
    next(b for b in submit_buttons(at) if b.label == "Save changes").click().run()

    assert not at.exception, [str(e.value) for e in at.exception]
    assert photos["uploads"] == [("face.png", PNG[1])]
    assert photos["deletes"] == []
    assert at.session_state["editing_kid_id"] is None
    assert at.success, "no confirmation after saving"


def test_uploading_a_parent_photo_saves_with_the_form(classic, photos):
    at = admin_page(classic, "parents")
    widget(at.button, "edit_parent_1").click().run()

    widget(at.file_uploader, "edit_parent_form_1_photo").set_value(PNG)
    at.run()
    next(b for b in submit_buttons(at) if b.label == "Save changes").click().run()

    assert not at.exception, [str(e.value) for e in at.exception]
    assert photos["uploads"] == [("face.png", PNG[1])]
    assert at.session_state["editing_parent_id"] is None


def test_a_failed_upload_keeps_the_existing_photo(classic, photos):
    """The old picture is only thrown away once the new one has landed."""
    at = admin_page(classic, "children")
    widget(at.button, "edit_kid_1").click().run()

    photos["fail"] = True
    widget(at.file_uploader, "edit_kid_form_1_photo").set_value(PNG)
    at.run()
    next(b for b in submit_buttons(at) if b.label == "Save changes").click().run()

    assert not at.exception, [str(e.value) for e in at.exception]
    assert photos["deletes"] == [], "a failed upload discarded the existing photo"
    assert any("Could not upload" in e.value for e in at.error), [e.value for e in at.error]


def test_renaming_without_a_photo_does_not_touch_the_photo_store(classic, photos):
    at = admin_page(classic, "children")
    widget(at.button, "edit_kid_1").click().run()

    widget(at.text_input, "edit_kid_form_1_name").set_value("Zayd II")
    next(b for b in submit_buttons(at) if b.label == "Save changes").click().run()

    assert not at.exception, [str(e.value) for e in at.exception]
    assert photos == {"uploads": [], "deletes": [], "fail": False, "url": "https://cdn.test/new.png"}


def test_removing_a_photo_is_offered_and_clears_it(classic, store, photos):
    store.data["kids"][0]["photo_path"] = "https://cdn.test/old.png"
    at = admin_page(classic, "children")
    widget(at.button, "edit_kid_1").click().run()

    remove = next(b for b in at.button if "Remove photo" in b.label)
    # It is a plain button, not a form submitter: st.button is illegal inside a
    # form, which is exactly why it lives out here rather than in the form.
    assert not getattr(remove, "is_form_submitter", False)

    remove.click().run()

    assert not at.exception, [str(e.value) for e in at.exception]
    assert photos["deletes"] == ["https://cdn.test/old.png"]
    assert store.recorded("update_kid")[-1]["updates"] == {"photo_path": None}
    assert at.session_state["editing_kid_id"] is None


def test_no_remove_offer_without_a_photo(classic, store, photos):
    store.data["kids"][0]["photo_path"] = None
    at = admin_page(classic, "children")
    widget(at.button, "edit_kid_1").click().run()

    assert not [b for b in at.button if "Remove photo" in b.label]


def test_a_blank_name_is_refused(classic, photos):
    at = admin_page(classic, "children")
    widget(at.button, "edit_kid_1").click().run()

    widget(at.text_input, "edit_kid_form_1_name").set_value("   ")
    next(b for b in submit_buttons(at) if b.label == "Save changes").click().run()

    assert any("Please enter a" in e.value for e in at.error), [e.value for e in at.error]
    assert at.session_state["editing_kid_id"] == 1, "the editor closed despite the bad name"
