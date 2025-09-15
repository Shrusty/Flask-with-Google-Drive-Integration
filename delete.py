from flask import Flask, request, redirect, session, url_for, send_file
import os
import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery

# Flask setup
app = Flask(__name__)
app.secret_key = "your_secret_key"

# Google API Setup
CLIENT_SECRETS_FILE = "credentials2.json"
SCOPES = ["https://www.googleapis.com/auth/drive.file"]
API_SERVICE_NAME = "drive"
API_VERSION = "v3"

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
    state = session.get("state")
    if not state:
        return "Error: State not found. Try re-authorizing.", 400
    
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, SCOPES, state=state)
    flow.redirect_uri = "http://localhost:5000/oauth2callback"
    flow.fetch_token(authorization_response=request.url)

    session["credentials"] = credentials_to_dict(flow.credentials)
    return redirect(url_for("list_files"))

@app.route("/upload", methods=["GET", "POST"])
def upload_file():
    if "credentials" not in session:
        return redirect(url_for("authorize"))

    if request.method == "POST":
        file = request.files["file"]
        if file:
            credentials = google.oauth2.credentials.Credentials(**session["credentials"])
            drive_service = googleapiclient.discovery.build(API_SERVICE_NAME, API_VERSION, credentials=credentials)

            file_metadata = {"name": file.filename}
            media = googleapiclient.http.MediaIoBaseUpload(file, mimetype=file.content_type)
            uploaded_file = drive_service.files().create(body=file_metadata, media_body=media, fields="id").execute()
            return f"File uploaded successfully! File ID: {uploaded_file.get('id')}"
    
    return '<form action="/upload" method="post" enctype="multipart/form-data"><input type="file" name="file"><input type="submit" value="Upload"></form>'

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
        file_list += f'<li>{file["name"]} - <a href="/download/{file["id"]}">Download</a> - <a href="/delete/{file["id"]}">Delete</a></li>'
    file_list += "</ul>"
    
    return file_list

@app.route("/download/<file_id>")
def download_file(file_id):
    if "credentials" not in session:
        return redirect(url_for("authorize"))
    
    credentials = google.oauth2.credentials.Credentials(**session["credentials"])
    drive_service = googleapiclient.discovery.build(API_SERVICE_NAME, API_VERSION, credentials=credentials)
    request = drive_service.files().get_media(fileId=file_id)
    file_path = f"downloads/{file_id}.pdf"
    os.makedirs("downloads", exist_ok=True)
    
    with open(file_path, "wb") as f:
        f.write(request.execute())
    
    return send_file(file_path, as_attachment=True)

@app.route("/delete/<file_id>")
def delete_file(file_id):
    if "credentials" not in session:
        return redirect(url_for("authorize"))
    
    credentials = google.oauth2.credentials.Credentials(**session["credentials"])
    drive_service = googleapiclient.discovery.build(API_SERVICE_NAME, API_VERSION, credentials=credentials)
    drive_service.files().delete(fileId=file_id).execute()
    return "File deleted successfully! <a href='/list'>Back to files</a>"

def credentials_to_dict(credentials):
    return {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": credentials.scopes,
    }

if __name__ == "__main__":
    app.run(debug=True)
