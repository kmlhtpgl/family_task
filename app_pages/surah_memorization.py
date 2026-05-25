import streamlit as st

from utils.surah_helpers import (
    calculate_surah_progress,
    get_quran_surahs_in_progress,
    get_quran_surahs_in_progress_for_parent,
    get_finished_quran_surahs,
    get_finished_quran_surahs_for_parent,
    get_duas_in_progress,
    get_duas_in_progress_for_parent,
    get_finished_duas,
    get_finished_duas_for_parent,
)
from utils.db_helpers import update_surah, delete_surah
from utils.data_helpers import today_string


def surah_memorization_page(data):
    st.header("📖 Quran Memorization")

    if not data.get("surahs"):
        st.info("No surahs or duas assigned yet. Go to Admin to assign them.")
        return

    reader_options = build_reader_options(data)
    if not reader_options:
        st.info("Add children or parents first in Admin.")
        return

    selected_label = st.selectbox(
        "Choose reader",
        list(reader_options.keys())
    )

    reader_info = reader_options[selected_label]
    is_parent = reader_info["type"] == "parent"
    reader_id = reader_info["id"]

    show_surahs_common(data, reader_id, is_parent)
    st.divider()
    show_duas_common(data, reader_id, is_parent)


def build_reader_options(data):
    options = {}

    for kid in data["kids"]:
        options[f"🧒 {kid['name']}"] = {"type": "kid", "id": kid["id"]}

    for parent in data.get("parents", []):
        options[f"👨‍👩‍👧 {parent['name']}"] = {"type": "parent", "id": parent["id"]}

    return options


def show_surahs_common(data, reader_id, is_parent):
    st.subheader("📖 Surahs")

    if is_parent:
        surahs = get_quran_surahs_in_progress_for_parent(data, reader_id)
        finished = get_finished_quran_surahs_for_parent(data, reader_id)
    else:
        surahs = get_quran_surahs_in_progress(data, reader_id)
        finished = get_finished_quran_surahs(data, reader_id)

    if surahs:
        st.markdown("**In Progress**")
        for surah in surahs:
            show_surah_item(surah)

    if finished:
        st.markdown("**✨ Memorized**")
        for surah in finished:
            st.markdown(
                f'<div class="task-item" style="border-left-color:#4CAF50;">'
                f'<span>✅ {surah["name"]}</span>'
                f' <span style="color:#666;">{surah["total_ayahs"]} ayahs</span>'
                f'</div>',
                unsafe_allow_html=True
            )

    if not surahs and not finished:
        st.caption("No surahs assigned yet.")


def show_duas_common(data, reader_id, is_parent):
    st.subheader("🤲 Duas (Prayers)")

    if is_parent:
        duas = get_duas_in_progress_for_parent(data, reader_id)
        finished = get_finished_duas_for_parent(data, reader_id)
    else:
        duas = get_duas_in_progress(data, reader_id)
        finished = get_finished_duas(data, reader_id)

    if duas:
        st.markdown("**In Progress**")
        for dua in duas:
            show_surah_item(dua, is_dua=True)

    if finished:
        st.markdown("**✨ Memorized**")
        for dua in finished:
            st.markdown(
                f'<div class="task-item" style="border-left-color:#4CAF50;">'
                f'<span>✅ {dua["name"]}</span>'
                f'</div>',
                unsafe_allow_html=True
            )

    if not duas and not finished:
        st.caption("No duas assigned yet.")


def show_surah_item(item, is_dua=False):
    with st.container():
        progress = calculate_surah_progress(item)
        progress_pct = round(progress * 100)

        label = "ayahs" if not is_dua else "ayah"

        st.markdown(
            f'<div class="task-item">'
            f'<div style="display:flex;justify-content:space-between;align-items:center;">'
            f'<h4 style="margin:0;">{item["name"]}</h4>'
            f'<span style="color:#666;">{item["total_ayahs"]} {label}</span>'
            f'</div>'
            f'<div style="margin-top:10px;">'
            f'<span style="font-size:0.9em;color:#666;">{item.get("memorized_ayahs", 0)} / {item["total_ayahs"]} {label} ({progress_pct}%)</span>'
            f'</div>'
            f'<div class="book-progress-bar"><div class="book-progress-fill" style="width:{progress_pct}%"></div></div>'
            f'</div>',
            unsafe_allow_html=True
        )

        memorized = st.number_input(
            "Memorized" if not is_dua else "Memorized",
            min_value=0,
            max_value=int(item["total_ayahs"]),
            value=int(item.get("memorized_ayahs", 0)),
            key=f"item_ayahs_{item['id']}",
            label_visibility="collapsed"
        )

        if memorized != item.get("memorized_ayahs", 0):
            updates = {
                "memorized_ayahs": int(memorized),
                "last_practiced_date": today_string()
            }

            if memorized >= item["total_ayahs"]:
                updates["status"] = "Memorized"
                updates["finished_date"] = today_string()

            update_surah(item["id"], updates)
            st.success(f"📖 Updated: {item['name']} ({progress_pct}%)")
            st.rerun()

        col1, col2 = st.columns(2)

        with col1:
            if st.button("✅ Mark as memorized", key=f"finish_item_{item['id']}"):
                updates = {
                    "memorized_ayahs": int(item["total_ayahs"]),
                    "status": "Memorized",
                    "finished_date": today_string(),
                    "last_practiced_date": today_string()
                }
                update_surah(item["id"], updates)
                st.rerun()

        with col2:
            if st.button("🗑️ Remove", key=f"remove_item_{item['id']}"):
                delete_surah(item["id"])
                st.success("✅ Removed!")
                st.rerun()
