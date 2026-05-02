from utils.supabase_client import get_supabase_client


def get_all_data():
    supabase = get_supabase_client()

    parents = supabase.table("parents").select("*").order("id").execute().data
    kids = supabase.table("kids").select("*").order("id").execute().data
    tasks = supabase.table("tasks").select("*").order("id").execute().data
    books = supabase.table("books").select("*").order("id").execute().data
    task_templates = supabase.table("task_templates").select("*").order("id").execute().data
    book_templates = supabase.table("book_templates").select("*").order("id").execute().data

    return {
        "parents": parents,
        "kids": kids,
        "tasks": tasks,
        "books": books,
        "task_templates": task_templates,
        "book_templates": book_templates,
        "settings": {
            "points_for_done": 10
        }
    }


# -----------------------
# Parents
# -----------------------

def add_parent(name, email=None, phone=None):
    supabase = get_supabase_client()

    new_parent = {
        "name": name,
        "email": email,
        "phone": phone
    }

    return supabase.table("parents").insert(new_parent).execute().data


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


# -----------------------
# Tasks
# -----------------------

def add_task(task):
    supabase = get_supabase_client()
    return supabase.table("tasks").insert(task).execute().data


def add_tasks(tasks):
    supabase = get_supabase_client()

    if not tasks:
        return []

    return supabase.table("tasks").insert(tasks).execute().data


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

def add_book(book):
    supabase = get_supabase_client()
    return supabase.table("books").insert(book).execute().data


def add_books(books):
    supabase = get_supabase_client()

    if not books:
        return []

    return supabase.table("books").insert(books).execute().data


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

def add_task_template(title, default_points):
    supabase = get_supabase_client()

    return (
        supabase
        .table("task_templates")
        .insert(
            {
                "title": title,
                "default_points": default_points
            }
        )
        .execute()
        .data
    )


def delete_task_template(template_id):
    supabase = get_supabase_client()

    return (
        supabase
        .table("task_templates")
        .delete()
        .eq("id", template_id)
        .execute()
        .data
    )


def replace_task_templates(templates):
    """
    Deletes all task templates and inserts the edited list again.
    This is simple and works well for a small family app.
    """
    supabase = get_supabase_client()

    supabase.table("task_templates").delete().neq("id", 0).execute()

    if templates:
        return supabase.table("task_templates").insert(templates).execute().data

    return []


# -----------------------
# Book templates
# -----------------------

def add_book_template(title, language, total_pages):
    supabase = get_supabase_client()

    return (
        supabase
        .table("book_templates")
        .insert(
            {
                "title": title,
                "language": language,
                "total_pages": total_pages
            }
        )
        .execute()
        .data
    )


def delete_book_template(template_id):
    supabase = get_supabase_client()

    return (
        supabase
        .table("book_templates")
        .delete()
        .eq("id", template_id)
        .execute()
        .data
    )


def replace_book_templates(templates):
    """
    Deletes all book templates and inserts the edited list again.
    This is simple and works well for a small family app.
    """
    supabase = get_supabase_client()

    supabase.table("book_templates").delete().neq("id", 0).execute()

    if templates:
        return supabase.table("book_templates").insert(templates).execute().data

    return []

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
