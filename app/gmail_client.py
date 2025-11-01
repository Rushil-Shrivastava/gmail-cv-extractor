import os
import base64
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle

SCOPES = ['https://mail.google.com/']


def get_gmail_service(credentials_path=None, token_path=None):
    credentials_path = credentials_path or os.environ.get('OAUTH_CREDENTIALS_PATH', 'credentials.json')
    token_path = token_path or os.environ.get('OAUTH_TOKEN_PATH', 'token.pickle')

    creds = None
    if os.path.exists(token_path):
        with open(token_path, 'rb') as f:
            creds = pickle.load(f)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, 'wb') as f:
            pickle.dump(creds, f)
    return build('gmail', 'v1', credentials=creds)


def download_attachments(out_dir='attachments', q='has:attachment'):
    os.makedirs(out_dir, exist_ok=True)
    service = get_gmail_service()

    messages = []
    response = service.users().messages().list(userId='me', q=q, maxResults=500).execute()
    messages.extend(response.get('messages', []))
    while 'nextPageToken' in response:
        response = service.users().messages().list(userId='me', q=q, pageToken=response['nextPageToken']).execute()
        messages.extend(response.get('messages', []))

    downloaded = []
    for m in messages:
        msg = service.users().messages().get(userId='me', id=m['id'], format='full').execute()
        payload = msg.get('payload', {})
        parts = payload.get('parts', [])
        for part in parts:
            filename = part.get('filename')
            if not filename:
                continue
            body = part.get('body', {})
            att_id = body.get('attachmentId')
            if not att_id:
                data = body.get('data')
                if not data:
                    continue
                content = base64.urlsafe_b64decode(data)
            else:
                att = service.users().messages().attachments().get(userId='me', messageId=m['id'], id=att_id).execute()
                data = att.get('data')
                content = base64.urlsafe_b64decode(data)

            safe_fn = filename.replace('/', '_').replace('..', '')
            out_path = os.path.join(out_dir, f"{m['id']}_{safe_fn}")
            with open(out_path, 'wb') as f:
                f.write(content)
            downloaded.append({'path': out_path, 'message_id': m['id'], 'filename': filename})
    return downloaded