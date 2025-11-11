import os.path
import os
from typing import Optional, Tuple, Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseUpload
import io

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/drive"]
CREDENTIALS = os.environ["FRIDGE_GDRIVE_CREDENTIALS"]
FOLDER_NAME = "Fridge Monitoring Data"


def get_drive_service() -> Any:
    """
    OAuth user auth. Expects a 'credentials.json' from Google Cloud Console
    (OAuth client ID of type 'Desktop'). Caches/refreshes token in token.json.
    """
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS, SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return build("drive", "v3", credentials=creds)

def find_folder_id(service, folder_name: str, parent_id: str = "root") -> Optional[str]:
    """
    Returns the first matching folder ID with given name under parent_id, or None.
    """
    # Makes sure that single quotes are properly escaped
    folder_name_gdrive = folder_name.replace("'", "\\'")
    q = (
        f"mimeType='application/vnd.google-apps.folder' "
        f"and name='{folder_name_gdrive}' "
        f"and '{parent_id}' in parents and trashed=false"
    )
    resp = service.files().list(
        q=q,
        fields="files(id, name)",
        pageSize=1,
        supportsAllDrives=True,
        includeItemsFromAllDrives=True,
        corpora="user",   # change to 'allDrives' if you need Shared Drives
    ).execute()
    files = resp.get("files", [])
    return files[0]["id"] if files else None

def ensure_folder(service, folder_name: str, parent_id: str = "root") -> str:
    """
    Gets the folder ID by name under parent_id; creates it if missing.
    """
    folder_id = find_folder_id(service, folder_name, parent_id)
    if folder_id:
        return folder_id

    metadata = {
        "name": folder_name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_id],
    }
    folder = service.files().create(
        body=metadata,
        fields="id",
        supportsAllDrives=True,
    ).execute()
    return folder["id"]

def upload_csv_to_drive(csv_text: str, filename: str) -> dict:
    """
    Upload a CSV string to Google Drive in the specified folder.

    Args:
        service: An authorized Drive API service instance from googleapiclient.discovery.build('drive', 'v3', ...)
        csv_text: The CSV content as a single string.
        filename: The name for the file ('.csv' will be appended if missing).
        folder_id: The Drive folder ID to place the file in.

    Returns:
        dict with file metadata (id, name, webViewLink, webContentLink).
    """

    service = get_drive_service()
    folder_id = ensure_folder(service, FOLDER_NAME)

    if not filename.lower().endswith(".csv"):
        filename += ".csv"

    file_metadata = {
        "name": filename,
        "mimeType": "text/csv",
        "parents": [folder_id],
    }

    media = MediaIoBaseUpload(
        io.BytesIO(csv_text.encode("utf-8")),
        mimetype="text/csv",
        resumable=False,
    )

    created = (
        service.files()
        .create(body=file_metadata, media_body=media, fields="id,name,webViewLink,webContentLink,parents")
        .execute()
    )
    return created

def main():
  """Shows basic usage of the Drive v3 API.
  Prints the names and ids of the first 10 files the user has access to.
  """

  try:
    service = get_drive_service()

    # Call the Drive v3 API
    results = (
        service.files()
        .list(pageSize=10, fields="nextPageToken, files(id, name)")
        .execute()
    )
    items = results.get("files", [])

    if not items:
      print("No files found.")
      return
    print("Files:")
    for item in items:
      print(f"{item['name']} ({item['id']})")
  except HttpError as error:
    # TODO(developer) - Handle errors from drive API.
    print(f"An error occurred: {error}")


if __name__ == "__main__":
  main()