import streamlit as st
from utils.page_chrome import render_page_header, render_stat_strip

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
    render_page_header("Quran", "Track surahs and duas with a calm, focused practice view.")

    if not data.get("surahs"):
        st.info("No surahs or duas assigned yet. Go to Admin to assign them.")
        return

    reader_labels = [f"Kid · {k['name']}" for k in data["kids"]]
    reader_labels += [f"Parent · {p['name']}" for p in data.get("parents", [])]

    selected_label = st.radio("Choose reader", reader_labels, horizontal=True, key="surah_reader_select")

    if selected_label.startswith("Kid · "):
        name = selected_label.replace("Kid · ", "")
        reader_id = next(k["id"] for k in data["kids"] if k["name"] == name)
        is_parent = False
    else:
        name = selected_label.replace("Parent · ", "")
        reader_id = next(p["id"] for p in data["parents"] if p["name"] == name)
        is_parent = True

    if is_parent:
        in_progress = get_quran_surahs_in_progress_for_parent(data, reader_id)
        finished = get_finished_quran_surahs_for_parent(data, reader_id)
        duas = get_duas_in_progress_for_parent(data, reader_id)
        finished_duas = get_finished_duas_for_parent(data, reader_id)
    else:
        in_progress = get_quran_surahs_in_progress(data, reader_id)
        finished = get_finished_quran_surahs(data, reader_id)
        duas = get_duas_in_progress(data, reader_id)
        finished_duas = get_finished_duas(data, reader_id)
    render_stat_strip([
        ("Surahs active", str(len(in_progress)), "currently practicing"),
        ("Duas active", str(len(duas)), "currently practicing"),
        ("Memorized", str(len(finished) + len(finished_duas)), "completed items"),
    ])
    show_surahs_common(data, reader_id, is_parent)
    st.divider()
    show_duas_common(data, reader_id, is_parent)


def show_surahs_common(data, reader_id, is_parent):
    st.markdown('<div class="route-section-label">Surahs</div>', unsafe_allow_html=True)

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
                f'<div class="task-item task-done row">'
                f'<span class="row-title">✅ {surah["name"]}</span>'
                f'<span class="row-meta num">{surah["total_ayahs"]} ayahs</span>'
                f'</div>',
                unsafe_allow_html=True
            )

    if not surahs and not finished:
        st.caption("No surahs assigned yet.")


def show_duas_common(data, reader_id, is_parent):
    st.markdown('<div class="route-section-label">Duas</div>', unsafe_allow_html=True)

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
                f'<div class="task-item task-done">'
                f'<span class="row-title">✅ {dua["name"]}</span>'
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
            f'<div class="row">'
            f'<span class="row-title"><h4>{item["name"]}</h4></span>'
            f'<span class="row-meta">{item["total_ayahs"]} {label}</span>'
            f'</div>'
            f'<div class="progress-line">'
            f'<span>{item.get("memorized_ayahs", 0)} / {item["total_ayahs"]} {label} ({progress_pct}%)</span>'
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
