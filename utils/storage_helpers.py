import uuid
from utils.supabase_client import get_supabase_client

BUCKET_NAME = "profile_photos"


def upload_profile_photo(file_bytes, file_name):
    """
    Uploads a profile photo to Supabase Storage.
    Returns the public URL of the uploaded file.
    """
    supabase = get_supabase_client()

    unique_file_name = f"{uuid.uuid4().hex}_{file_name}"

    try:
        supabase.storage.from_(BUCKET_NAME).upload(
            unique_file_name,
            file_bytes,
            {"content-type": "image/jpeg"}
        )

        public_url = supabase.storage.from_(BUCKET_NAME).get_public_url(
            unique_file_name
        )

        return public_url
    except Exception as e:
        raise e


def delete_profile_photo(file_url):
    """
    Deletes a profile photo from Supabase Storage.
    Extracts the file path from the public URL and deletes it.
    """
    if not file_url:
        return False

    supabase = get_supabase_client()

    file_path = file_url.split(f"/{BUCKET_NAME}/")[-1]

    if "?" in file_path:
        file_path = file_path.split("?")[0]

    try:
        supabase.storage.from_(BUCKET_NAME).remove([file_path])
        return True
    except Exception:
        return False
