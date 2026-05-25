from utils.data_helpers import today_string


def calculate_surah_progress(surah):
    total_ayahs = surah.get("total_ayahs", 0)
    if total_ayahs <= 0:
        return 0
    memorized = surah.get("memorized_ayahs", 0)
    return memorized / total_ayahs


def update_surah_ayahs(surah, memorized_ayahs):
    surah["memorized_ayahs"] = memorized_ayahs
    if memorized_ayahs >= surah["total_ayahs"]:
        surah["status"] = "Memorized"
        surah["finished_date"] = today_string()
    surah["last_practiced_date"] = today_string()
    return surah


def mark_surah_finished(surah):
    surah["memorized_ayahs"] = surah["total_ayahs"]
    surah["status"] = "Memorized"
    surah["finished_date"] = today_string()
    surah["last_practiced_date"] = today_string()
    return surah


def _filter_by_type(items, item_type):
    """Filter a list of surahs/duas by their type field."""
    return [s for s in items if s.get("type", "surah") == item_type]


def get_surahs_for_kid(data, kid_id):
    return [
        s for s in data.get("surahs", [])
        if s.get("kid_id") == kid_id
    ]


def get_surahs_for_parent(data, parent_id):
    return [
        s for s in data.get("surahs", [])
        if s.get("parent_id") == parent_id
    ]


def get_surahs_in_progress(data, kid_id):
    return [
        s for s in data.get("surahs", [])
        if s.get("kid_id") == kid_id
        and s.get("status") != "Memorized"
    ]


def get_surahs_in_progress_for_parent(data, parent_id):
    return [
        s for s in data.get("surahs", [])
        if s.get("parent_id") == parent_id
        and s.get("status") != "Memorized"
    ]


def get_finished_surahs(data, kid_id):
    return [
        s for s in data.get("surahs", [])
        if s.get("kid_id") == kid_id
        and s.get("status") == "Memorized"
    ]


def get_finished_surahs_for_parent(data, parent_id):
    return [
        s for s in data.get("surahs", [])
        if s.get("parent_id") == parent_id
        and s.get("status") == "Memorized"
    ]


# ----- Duas (prayers) -----

def get_duas_in_progress(data, kid_id):
    return _filter_by_type(
        get_surahs_in_progress(data, kid_id), "dua"
    )


def get_duas_in_progress_for_parent(data, parent_id):
    return _filter_by_type(
        get_surahs_in_progress_for_parent(data, parent_id), "dua"
    )


def get_finished_duas(data, kid_id):
    return _filter_by_type(
        get_finished_surahs(data, kid_id), "dua"
    )


def get_finished_duas_for_parent(data, parent_id):
    return _filter_by_type(
        get_finished_surahs_for_parent(data, parent_id), "dua"
    )


def get_quran_surahs_in_progress(data, kid_id):
    return _filter_by_type(
        get_surahs_in_progress(data, kid_id), "surah"
    )


def get_quran_surahs_in_progress_for_parent(data, parent_id):
    return _filter_by_type(
        get_surahs_in_progress_for_parent(data, parent_id), "surah"
    )


def get_finished_quran_surahs(data, kid_id):
    return _filter_by_type(
        get_finished_surahs(data, kid_id), "surah"
    )


def get_finished_quran_surahs_for_parent(data, parent_id):
    return _filter_by_type(
        get_finished_surahs_for_parent(data, parent_id), "surah"
    )
