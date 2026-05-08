import os
import json
import mimetypes
from pathlib import Path
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Auth
credentials_json = json.loads(os.environ["GDRIVE_CREDENTIALS"])
credentials = service_account.Credentials.from_service_account_info(
    credentials_json,
    scopes=["https://www.googleapis.com/auth/drive"]
)
service = build("drive", "v3", credentials=credentials)

ROOT_FOLDER_ID = os.environ["GDRIVE_FOLDER_ID"]

num_of_files = 0
num_of_folders = 0

def get_or_create_folder(name, parent_id):
    query = (
        f"name='{name}' and "
        f"'{parent_id}' in parents and "
        f"mimeType='application/vnd.google-apps.folder' and "
        f"trashed=false"
    )
    results = service.files().list(
        q=query,
        fields="files(id, name)",
        supportsAllDrives=True,
        includeItemsFromAllDrives=True
    ).execute()
    folders = results.get("files", [])
    if folders:
        return folders[0]["id"]

    metadata = {
        "name": name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_id],
    }
    folder = service.files().create(
        body=metadata,
        fields="id",
        supportsAllDrives=True
    ).execute()
    return folder["id"]


def upload_file(local_path, parent_id):
    filename = local_path.name

    if filename.endswith(".py"):
        return

    mime_type = mimetypes.guess_type(local_path)[0] or "application/octet-stream"

    query = (
        f"name='{filename}' and "
        f"'{parent_id}' in parents and "
        f"trashed=false"
    )
    results = service.files().list(
        q=query,
        fields="files(id, name)",
        supportsAllDrives=True,
        includeItemsFromAllDrives=True
    ).execute()
    existing = results.get("files", [])

    media = MediaFileUpload(str(local_path), mimetype=mime_type, resumable=True)

    if existing:
        service.files().update(
            fileId=existing[0]["id"],
            media_body=media,
            supportsAllDrives=True
        ).execute()
        # print(f"  Updated: {local_path}")
    else:
        metadata = {"name": filename, "parents": [parent_id]}
        service.files().create(
            body=metadata,
            media_body=media,
            fields="id",
            supportsAllDrives=True
        ).execute()
        # print(f"  Uploaded: {local_path}")


def upload_directory(local_dir, parent_id):
    global num_of_files, num_of_folders

    for item in sorted(local_dir.iterdir()):
        if item.name.startswith("."):
            continue
        if item.is_dir():
            # print(f"Folder: {item}")
            folder_id = get_or_create_folder(item.name, parent_id)
            upload_directory(item, folder_id)
            num_of_folders += 1
        elif item.is_file():
            upload_file(item, parent_id)
            num_of_files += 1

# Debug
# print(f"Verifying access to folder ID: {ROOT_FOLDER_ID}")
# try:
#     folder = service.files().get(
#         fileId=ROOT_FOLDER_ID,
#         supportsAllDrives=True,
#         fields="id, name, mimeType"
#     ).execute()
#     print(f"Found: '{folder['name']}' ({folder['mimeType']})")
# except Exception as e:
#     print(f"ERROR accessing folder: {e}")

# results = service.files().list(
#     q=f"'{ROOT_FOLDER_ID}' in parents and trashed=false",
#     fields="files(id, name, mimeType)",
#     supportsAllDrives=True,
#     includeItemsFromAllDrives=True
# ).execute()
# print(f"Current contents: {results.get('files', [])}")

# Start upload from repo root
repo_root = Path("/github/workspace")

# Start upload
print(f"Starting upload to folder ID: {ROOT_FOLDER_ID}")
upload_directory(repo_root, ROOT_FOLDER_ID)
print(f"Successfully uploaded {num_of_folders} folders and {num_of_files} files.")
