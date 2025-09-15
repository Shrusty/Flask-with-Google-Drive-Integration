from flask import Flask, request, redirect, session, url_for, render_template, send_file
import os
import pathlib
import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'


# Flask setup
app = Flask(__name__)
app.secret_key = "your_secret_key"  # Change this to a secure secret key

# Google API Setup
CLIENT_SECRETS_FILE = "credentials2.json"  # OAuth credentials file
SCOPES = ["https://www.googleapis.com/auth/drive.file"]
API_SERVICE_NAME = "drive"
API_VERSION = "v3"

# Authentication route
@app.route("/")
def index():
    return '<a href="/authorize">Authorize Google Drive</a>'

@app.route("/authorize")
def authorize():
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, SCOPES)
    flow.redirect_uri = "http://localhost:5000/oauth2callback"
    
    authorization_url, state = flow.authorization_url(access_type="offline", include_granted_scopes="true")
    session["state"] = state
    return redirect(authorization_url)

@app.route("/oauth2callback")
def oauth2callback():
    state = session.get("state")   # safer than session["state"]
    if not state:
        return "Error: Missing state in session. Please try again via /authorize", 400

    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, SCOPES, state=state)
    flow.redirect_uri = "http://localhost:5000/oauth2callback"

    authorization_response = request.url
    flow.fetch_token(authorization_response=authorization_response)

    credentials = flow.credentials
    session["credentials"] = credentials_to_dict(credentials)

    return redirect(url_for("upload_file"))


def credentials_to_dict(credentials):
    return {"token": credentials.token, "refresh_token": credentials.refresh_token,
            "token_uri": credentials.token_uri, "client_id": credentials.client_id,
            "client_secret": credentials.client_secret, "scopes": credentials.scopes}

# Upload file to Google Drive
FOLDER_ID = "14f_h1ICZXpbDFHK8bR9JHihiZwcKs60n"  # Replace with your folder ID

@app.route("/upload", methods=["GET", "POST"])
def upload_file():
    if "credentials" not in session:
        return redirect(url_for("authorize"))

    if request.method == "POST":
        file = request.files["file"]
        if file:
            credentials = google.oauth2.credentials.Credentials(**session["credentials"])
            drive_service = googleapiclient.discovery.build(API_SERVICE_NAME, API_VERSION, credentials=credentials)

            # Define metadata with folder ID
            file_metadata = {
                "name": file.filename,
                "parents": [FOLDER_ID]  # Upload file to the specified folder
            }
            media = googleapiclient.http.MediaIoBaseUpload(file, mimetype=file.content_type)

            uploaded_file = drive_service.files().create(body=file_metadata, media_body=media, fields="id").execute()
            return f"File uploaded successfully! File ID: {uploaded_file.get('id')}"

    return '''
        <form action="/upload" method="post" enctype="multipart/form-data">
            <input type="file" name="file">
            <input type="submit" value="Upload">
        </form>
    '''

# List files
@app.route("/list")
def list_files():
    if "credentials" not in session:
        return redirect(url_for("authorize"))

    credentials = google.oauth2.credentials.Credentials(**session["credentials"])
    drive_service = googleapiclient.discovery.build(API_SERVICE_NAME, API_VERSION, credentials=credentials)

    results = drive_service.files().list().execute()
    files = results.get("files", [])

    file_list = "<h2>Uploaded Files:</h2><ul>"
    for file in files:
        file_list += f'<li>{file["name"]} - <a href="/download/{file["id"]}">Download</a></li>'
    file_list += "</ul>"

    return file_list

# Download file
@app.route("/download/<file_id>")
def download_file(file_id):
    if "credentials" not in session:
        return redirect(url_for("authorize"))

    credentials = google.oauth2.credentials.Credentials(**session["credentials"])
    drive_service = googleapiclient.discovery.build(API_SERVICE_NAME, API_VERSION, credentials=credentials)

    request = drive_service.files().get_media(fileId=file_id)
    file_path = f"downloads/{file_id}.pdf"  # Change file extension as needed

    os.makedirs("downloads", exist_ok=True)
    with open(file_path, "wb") as f:
        f.write(request.execute())

    return send_file(file_path, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
