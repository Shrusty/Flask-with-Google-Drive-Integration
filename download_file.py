from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
import io
from googleapiclient.http import MediaIoBaseDownload

# Authenticate using the service account credentials
SCOPES = ['https://www.googleapis.com/auth/drive']
creds = Credentials.from_service_account_file('service_acc.json', scopes=SCOPES)
service = build('drive', 'v3', credentials=creds)

# Google Drive Folder ID (Replace with your folder's ID)
FOLDER_ID = "14f_h1ICZXpbDFHK8bR9JHihiZwcKs60n"  # Replace with the actual folder ID

def list_files_in_folder():
    """Lists files inside a specific Google Drive folder (ignores subfolders)."""
    query = f"'{FOLDER_ID}' in parents and mimeType != 'application/vnd.google-apps.folder'"
    results = service.files().list(q=query, fields="files(id, name)").execute()

    files = results.get('files', [])
    if not files:
        print("No files found in the folder.")
        return []

    print("\n📂 Files in Folder:")
    for index, file in enumerate(files):
        print(f"{index + 1}. {file['name']} (ID: {file['id']})")
    return files

def download_file(file_id, file_name):
    """Downloads a specific file from Google Drive."""
    request = service.files().get_media(fileId=file_id)
    file_path = f"./{file_name}"  # Save file in the current directory
    with open(file_path, "wb") as f:
        downloader = MediaIoBaseDownload(f, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            print(f"Download progress: {int(status.progress() * 100)}%")

    print(f"✅ File downloaded successfully: {file_path}")

def download_all_files(files):
    """Downloads all files from the folder."""
    for file in files:
        print(f"\n⬇️ Downloading: {file['name']}")
        download_file(file['id'], file['name'])

# List files inside the folder
files = list_files_in_folder()

# Ask user for action
if files:
    choice = input("\nEnter the number of the file to download (or type 'all' to download everything): ").strip()
    
    if choice.lower() == 'all':
        download_all_files(files)
    elif choice.isdigit() and 1 <= int(choice) <= len(files):
        selected_file = files[int(choice) - 1]
        download_file(selected_file['id'], selected_file['name'])
    else:
        print("❌ Invalid choice. Exiting...")
