import os
import json
import mimetypes
from pathlib import Path
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

# Auth
credentials_json = json.loads(os.environ["GDRIVE_CREDENTIALS"])
credentials = service_account.Credentials.from_service_account_info(
    credentials_json,
    scopes=["https://www.googleapis.com/auth/drive"]
)
service = build("drive", "v3", credentials=credentials)

ROOT_FOLDER_ID = os.environ["GDRIVE_FOLDER_ID"]

num_of_uploaded_files = 0
num_of_updated_files = 0
num_of_created_folders = 0
num_of_existing_folders = 0

def verify_target_folder(folder_id):
    print(f"Verifying access to Google Drive folder ID: {folder_id}")
    try:
        folder = service.files().get(
            fileId=folder_id,
            supportsAllDrives=True,
            fields="id, name, mimeType"
        ).execute()
    except Exception as e:
        raise SystemExit(
            f"ERROR: Unable to access Google Drive folder '{folder_id}'. "
            f"Verify that the folder ID is correct and that the service account has permission to read it. "
            f"Drive API error: {e}"
        ) from e

    print(f"Found Drive folder: '{folder.get('name', '<unknown>')}' ({folder.get('mimeType', '<unknown>')})")
    return folder

def clear_target_folder(parent_id):
    print(f"Clearing contents of folder ID: {parent_id}")
    deleted_items = 0
    page_token = None

    while True:
        try:
            query = (
                f"'{parent_id}' in parents and "
                f"trashed=false"
            )
            results = service.files().list(
                q=query,
                fields="files(id, name, mimeType)",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
                pageSize=1000,
                pageToken=page_token
            ).execute()
        except Exception as e:
            raise SystemExit(
                f"ERROR: Failed to list contents of Google Drive folder '{parent_id}'. "
                f"Check that the folder is still accessible and that the service account has permission to manage it. "
                f"Drive API error: {e}"
            ) from e

        items = results.get("files", [])
        if not items:
            break

        for item in items:
            try:
                service.files().delete(
                    fileId=item["id"],
                    supportsAllDrives=True
                ).execute()
            except HttpError as e:
                if e.resp.status == 404:
                    print(
                        f"Skipping item '{item.get('name', item.get('id', 'unknown'))}' because it no longer exists in Drive (404)."
                    )
                    continue
                raise SystemExit(
                    f"ERROR: Failed to delete item '{item.get('name', item.get('id', 'unknown'))}' from folder '{parent_id}'. "
                    f"Check that the service account has permission to delete contents in that folder. "
                    f"Drive API error: {e}"
                ) from e
            except Exception as e:
                raise SystemExit(
                    f"ERROR: Failed to delete item '{item.get('name', item.get('id', 'unknown'))}' from folder '{parent_id}'. "
                    f"Check that the service account has permission to delete contents in that folder. "
                    f"Drive API error: {e}"
                ) from e
            deleted_items += 1

        page_token = results.get("nextPageToken")
        if not page_token:
            break

    print(f"Deleted {deleted_items} item(s) from folder ID: {parent_id}")
    return deleted_items

def create_folder(name, parent_dir_id):
    global num_of_created_folders
    metadata = {
        "name": name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_dir_id],
    }
    try:
        folder = service.files().create(
            body=metadata,
            fields="id",
            supportsAllDrives=True
        ).execute()
    except Exception as e:
        raise SystemExit(
            f"ERROR: Failed to create folder '{name}' inside parent folder '{parent_dir_id}'. "
            f"Check that the target Drive folder is writable and that the service account has permission to create folders there. "
            f"Drive API error: {e}"
        ) from e
    num_of_created_folders += 1
    return folder["id"]

def upload_file(local_path, dir_id):
    global num_of_uploaded_files
    filename = local_path.name

    mime_type = mimetypes.guess_type(local_path)[0] or "application/octet-stream"

    media = MediaFileUpload(str(local_path), mimetype=mime_type, resumable=True)

    metadata = {"name": filename, "parents": [dir_id]}
    try:
        service.files().create(
            body=metadata,
            media_body=media,
            fields="id",
            supportsAllDrives=True
        ).execute()
    except Exception as e:
        raise SystemExit(
            f"ERROR: Failed to upload file '{filename}' to folder '{dir_id}'. "
            f"Check that the target Drive folder is writable and that the service account has permission to add files there. "
            f"Drive API error: {e}"
        ) from e
    num_of_uploaded_files += 1
    # print(f"  Uploaded: {local_path}")

def upload_directory(local_dir, dir_id):
    for item in sorted(local_dir.iterdir()):
        # Ignore system files and hidden files (like .git, .DS_Store, etc.)
        if item.name.startswith("."):
            continue
        if item.is_dir():
            folder_id = create_folder(item.name, dir_id)
            upload_directory(item, folder_id)
        elif item.is_file():
            upload_file(item, dir_id)

# Verify access before destructive operations begin
verify_target_folder(ROOT_FOLDER_ID)

# Start upload from repo root
repo_root = Path("/github/workspace")

# Clear the target Drive folder before uploading fresh content
clear_target_folder(ROOT_FOLDER_ID)

# Start upload
print(f"Starting upload to folder ID: {ROOT_FOLDER_ID}")
upload_directory(repo_root, ROOT_FOLDER_ID)
print(f"Successfully created {num_of_created_folders} folders and uploaded {num_of_uploaded_files} files.")
