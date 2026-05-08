# Google Drive Upload Git Action

A GitHub Action that uploads your repository's files and folders to Google Drive, preserving the full directory structure.

## Features

- Recursively uploads all files and folders to a target Google Drive folder or Shared Drive
- Preserves directory structure
- Overwrites existing files on subsequent runs
- Skips hidden files and folders (dotfiles)

## Prerequisites

Before using this action you will need:

1. A **Google Cloud project** with the Drive API enabled
2. A **Google Service Account** with a JSON key
3. A **Google Shared Drive** (recommended — service accounts have 0 GB quota on personal Drive)
4. The service account added as a **Contributor** to the Shared Drive
5. Two **GitHub secrets** configured in the repo that uses this action:
   - `GDRIVE_CREDENTIALS` — the full JSON contents of the service account key file (unencoded)
   - `GDRIVE_FOLDER_ID` — the ID of the target Shared Drive folder

## Usage

```yaml
- name: Upload to Google Drive
  uses: your-username/google-drive-upload-git-action@v1
  with:
    credentials: ${{ secrets.GDRIVE_CREDENTIALS }}
    folder_id: ${{ secrets.GDRIVE_FOLDER_ID }}
```

## Inputs

| Input | Required | Description |
|-------|----------|-------------|
| `credentials` | Yes | Google service account credentials JSON (unencoded) |
| `folder_id` | Yes | Google Drive folder or Shared Drive ID to upload into |

## Example Workflow

```yaml
name: Sync to Google Drive

on:
  push:
    branches:
      - main

jobs:
  upload:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Upload to Google Drive
        uses: netmindr/google-drive-upload-git-action@main
        with:
          credentials: ${{ secrets.GDRIVE_CREDENTIALS }}
          folder_id: ${{ secrets.GDRIVE_FOLDER_ID }}
```

## Finding Your Folder ID

The folder ID is the string at the end of the Google Drive folder URL:

```
https://drive.google.com/drive/folders/THIS_IS_YOUR_FOLDER_ID
```

## Author

David Fisher