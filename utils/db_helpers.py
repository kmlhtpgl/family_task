from utils.supabase_client import get_supabase_client
import time


def get_all_data(retries=3, delay=0.5):
    supabase = get_supabase_client()

    for attempt in range(retries):
        try:
            parents = supabase.table("parents").select("*").order("id").execute().data
            kids = supabase.table("kids").select("*").order("id").execute().data
            tasks = supabase.table("tasks").select("*").order("id").execute().data
            books = supabase.table("books").select("*").order("id").execute().data
            task_templates = supabase.table("task_templates").select("*").order("id").execute().data
            book_templates = supabase.table("book_templates").select("*").order("id").execute().data

            try:
                surahs = supabase.table("surahs").select("*").order("id").execute().data
            except Exception:
                surahs = []

            try:
                reward_sessions = supabase.table("reward_sessions").select("*").order("id").execute().data
            except Exception:
                reward_sessions = []

            return {
                "parents": parents,
                "kids": kids,
                "tasks": tasks,
                "books": books,
                "surahs": surahs,
                "reward_sessions": reward_sessions,
                "task_templates": task_templates,
                "book_templates": book_templates,
                "settings": {
                    "points_for_done": 10
                }
            }
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                raise e


# -----------------------
# Parents
# -----------------------

def add_parent(name, email=None, phone=None, photo_url=None):
    supabase = get_supabase_client()

    new_parent = {
        "name": name,
        "email": email,
        "phone": phone,
        "photo_url": photo_url
    }

    result = supabase.table("parents").insert(new_parent).execute().data
    return result


def update_parent(parent_id, updates):
    supabase = get_supabase_client()

    return (
        supabase
        .table("parents")
        .update(updates)
        .eq("id", parent_id)
        .execute()
        .data
    )


def delete_parent(parent_id):
    supabase = get_supabase_client()

    return (
        supabase
        .table("parents")
        .delete()
        .eq("id", parent_id)
        .execute()
        .data
    )


# -----------------------
# Kids
# -----------------------

def add_kid(name, age, photo_path=None):
    supabase = get_supabase_client()

    new_kid = {
        "name": name,
        "age": age,
        "photo_path": photo_path
    }

    return supabase.table("kids").insert(new_kid).execute().data


def update_kid(kid_id, updates):
    supabase = get_supabase_client()

    return (
        supabase
        .table("kids")
        .update(updates)
        .eq("id", kid_id)
        .execute()
        .data
    )


def delete_kid(kid_id):
    supabase = get_supabase_client()

    return (
        supabase
        .table("kids")
        .delete()
        .eq("id", kid_id)
        .execute()
        .data
    )


# -----------------------
# Tasks
# -----------------------

def add_task(task, retries=2, delay=0.3):
    supabase = get_supabase_client()

    for attempt in range(retries):
        try:
            return supabase.table("tasks").insert(task).execute().data
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                raise e


def add_tasks(tasks, retries=2, delay=0.3):
    supabase = get_supabase_client()

    if not tasks:
        return []

    for attempt in range(retries):
        try:
            return supabase.table("tasks").insert(tasks).execute().data
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                raise e


def delete_task(task_id, retries=2, delay=0.3):
    supabase = get_supabase_client()

    for attempt in range(retries):
        try:
            return (
                supabase
                .table("tasks")
                .delete()
                .eq("id", task_id)
                .execute()
                .data
            )
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                raise e


def update_task(task_id, updates):
    supabase = get_supabase_client()

    return (
        supabase
        .table("tasks")
        .update(updates)
        .eq("id", task_id)
        .execute()
        .data
    )


# -----------------------
# Books assigned to children
# -----------------------

def add_book(book, retries=2, delay=0.3):
    supabase = get_supabase_client()

    for attempt in range(retries):
        try:
            return supabase.table("books").insert(book).execute().data
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                raise e


def add_books(books, retries=2, delay=0.3):
    supabase = get_supabase_client()

    if not books:
        return []

    for attempt in range(retries):
        try:
            return supabase.table("books").insert(books).execute().data
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                raise e


def update_book(book_id, updates):
    supabase = get_supabase_client()

    return (
        supabase
        .table("books")
        .update(updates)
        .eq("id", book_id)
        .execute()
        .data
    )


# -----------------------
# Task templates
# -----------------------

def add_task_template(title, default_points, retries=2, delay=0.3):
    supabase = get_supabase_client()

    for attempt in range(retries):
        try:
            return (
                supabase
                .table("task_templates")
                .insert({
                    "title": title,
                    "default_points": default_points
                })
                .execute()
                .data
            )
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                raise e


def delete_task_template(template_id, retries=2, delay=0.3):
    supabase = get_supabase_client()

    for attempt in range(retries):
        try:
            return (
                supabase
                .table("task_templates")
                .delete()
                .eq("id", template_id)
                .execute()
                .data
            )
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                raise e


def update_task_template(template_id, updates):
    supabase = get_supabase_client()

    return (
        supabase
        .table("task_templates")
        .update(updates)
        .eq("id", template_id)
        .execute()
        .data
    )


def replace_task_templates(templates):
    supabase = get_supabase_client()

    supabase.table("task_templates").delete().neq("id", 0).execute()

    if templates:
        return supabase.table("task_templates").insert(templates).execute().data

    return []


# -----------------------
# Book templates
# -----------------------

def add_book_template(title, language, total_pages, writer=None, retries=2, delay=0.3):
    supabase = get_supabase_client()

    for attempt in range(retries):
        try:
            return (
                supabase
                .table("book_templates")
                .insert({
                    "title": title,
                    "language": language,
                    "total_pages": total_pages,
                    "writer": writer
                })
                .execute()
                .data
            )
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                raise e


def delete_book_template(template_id, retries=2, delay=0.3):
    supabase = get_supabase_client()

    for attempt in range(retries):
        try:
            return (
                supabase
                .table("book_templates")
                .delete()
                .eq("id", template_id)
                .execute()
                .data
            )
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                raise e


def replace_book_templates(templates):
    supabase = get_supabase_client()

    supabase.table("book_templates").delete().neq("id", 0).execute()

    if templates:
        return supabase.table("book_templates").insert(templates).execute().data

    return []


def replace_book_template(template_id, template_data):
    supabase = get_supabase_client()

    return (
        supabase
        .table("book_templates")
        .update(template_data)
        .eq("id", template_id)
        .execute()
        .data
    )

def delete_book(book_id):
    supabase = get_supabase_client()

    return (
        supabase
        .table("books")
        .delete()
        .eq("id", book_id)
        .execute()
        .data
    )


# -----------------------
# Surahs
# -----------------------

def add_surah(surah, retries=2, delay=0.3):
    supabase = get_supabase_client()
    for attempt in range(retries):
        try:
            return supabase.table("surahs").insert(surah).execute().data
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                raise e


def add_surahs(surahs, retries=2, delay=0.3):
    supabase = get_supabase_client()
    if not surahs:
        return []
    for attempt in range(retries):
        try:
            return supabase.table("surahs").insert(surahs).execute().data
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                raise e


def update_surah(surah_id, updates):
    supabase = get_supabase_client()
    return (
        supabase
        .table("surahs")
        .update(updates)
        .eq("id", surah_id)
        .execute()
        .data
    )


def delete_surah(surah_id):
    supabase = get_supabase_client()
    return (
        supabase
        .table("surahs")
        .delete()
        .eq("id", surah_id)
        .execute()
        .data
    )


# -----------------------
# Reward Sessions
# -----------------------

def add_reward_session(session, retries=2, delay=0.3):
    supabase = get_supabase_client()
    for attempt in range(retries):
        try:
            return supabase.table("reward_sessions").insert(session).execute().data
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                raise e


def update_reward_session(session_id, updates):
    supabase = get_supabase_client()
    return (
        supabase
        .table("reward_sessions")
        .update(updates)
        .eq("id", session_id)
        .execute()
        .data
    )


# -----------------------
# Points Reset
# -----------------------

def reset_all_points():
    """Set points to 0 for all Done tasks."""
    supabase = get_supabase_client()
    return (
        supabase
        .table("tasks")
        .update({"points": 0})
        .eq("status", "Done")
        .execute()
        .data
    )


def reset_monthly_points(year, month):
    """Set points to 0 for tasks completed in a specific month."""
    supabase = get_supabase_client()
    month_str = f"{year:04d}-{month:02d}"
    return (
        supabase
        .table("tasks")
        .update({"points": 0})
        .eq("status", "Done")
        .like("completed_date", f"{month_str}%")
        .execute()
        .data
    )


def reset_person_points(person_id, is_kid=True):
    """Set points to 0 for Done tasks of a specific person."""
    supabase = get_supabase_client()
    field = "kid_id" if is_kid else "parent_id"
    return (
        supabase
        .table("tasks")
        .update({"points": 0})
        .eq("status", "Done")
        .eq(field, person_id)
        .execute()
        .data
    )


def delete_done_tasks():
    """Delete all Done tasks."""
    supabase = get_supabase_client()
    return (
        supabase
        .table("tasks")
        .delete()
        .eq("status", "Done")
        .execute()
        .data
    )
