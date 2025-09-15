from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

# Authenticate using the credentials.json file
SCOPES = ['https://www.googleapis.com/auth/drive']
creds = Credentials.from_service_account_file('service_acc.json', scopes=SCOPES)

# Build the Drive API service
service = build('drive', 'v3', credentials=creds)

def list_uploaded_files():
    """Lists the recently uploaded files in Google Drive."""
    FOLDER_ID = "14f_h1ICZXpbDFHK8bR9JHihiZwcKs60n"  # Replace with actual Google Drive folder ID

    results = service.files().list(
    q=f"'{FOLDER_ID}' in parents",
    pageSize=10,
    fields="files(id, name, mimeType, size, webViewLink)"
).execute()

    files = results.get('files', [])
    
    if not files:
        print("No files found.")
        return

    print("Uploaded Files:")
    for file in files:
        print(f"📂 Name: {file['name']}")
        print(f"🆔 ID: {file['id']}")
        print(f"🔗 View: {file.get('webViewLink', 'N/A')}")
        print(f"📄 Type: {file['mimeType']}")
        print(f"📏 Size: {file.get('size', 'Unknown')} bytes")
        print("-" * 50)

# Run the function to list uploaded files
list_uploaded_files()
