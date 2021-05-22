import io
import os

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

from googleapiclient import errors
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

from gdrive.upload_file_dict import file_dict


SCOPES = ['https://www.googleapis.com/auth/drive']


def setup_service():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if not os.path.exists('gdrive/client_secret.json'):
        print('Secret located at gdrive/client_secret.json not found. Running without Google access.')
        return None

    if os.path.exists('gdrive/token.json'):
        creds = Credentials.from_authorized_user_file('gdrive/token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'gdrive/client_secret.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('gdrive/token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('drive', 'v3', credentials=creds)
    return service


def update_file(service, file_id, new_filename):
    """Update an existing file's metadata and content.

  Args:
    service: Drive API service instance.
    file_id: ID of the file to update.
    new_filename: Filename of the new content to upload.
  Returns:
    Updated file metadata if successful, None otherwise.
  """
    try:
        # First retrieve the file from the API.
        file = service.files().get(fileId=file_id).execute()

        # File's new content.
        media_body = MediaFileUpload(
            new_filename, mimetype=file['mimeType'], resumable=True)

        # Send the request to the API.
        updated_file = service.files().update(
            fileId=file_id,
            media_body=media_body).execute()
        return updated_file
    except errors.HttpError as error:
        print('An error occurred: %s' % error)
        return None


def download_banner(service, file_id, path):
    if not service:
        return True
    print("Downloading Banner: ", end="")
    os.remove(path)
    fh = io.FileIO(path, 'wb')
    request = service.files().get_media(fileId=file_id)
    media_req = MediaIoBaseDownload(fh, request)

    while True:
        try:
            prog, complete = media_req.next_chunk()
        except errors.HttpError as error:
            print("An error occured: %s" % error)
            fh.close()
            return False
        if complete:
            print("Done")
            fh.close()
            return os.path.exists(path)


def batch_upload(service, file_list):
    if not service:
        return
    for file_name in file_list:
        base_name = os.path.basename(file_name)
        file_id = file_dict.get(base_name, None)
        if not file_id:
            print(f"Error: {base_name} not known to the file dict")
            continue
        result = update_file(service, file_id, file_name)
        if result.get('name', None):
            print("*", end="", flush=True)
        else:
            print(result)