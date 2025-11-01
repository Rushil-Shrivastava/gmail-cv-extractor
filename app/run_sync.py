import os
import re
import base64
import pickle
from pathlib import Path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from app.parser import parse_attachment
from app.db import SessionLocal, init_db, Candidate
import pandas as pd

SCOPES = ["https://mail.google.com/"]

def export_candidates_to_excel():
    """Export all candidates in the database to Excel."""
    from app.db import SessionLocal, Candidate

    db = SessionLocal()
    candidates = db.query(Candidate).all()
    db.close()

    if not candidates:
        print("[INFO] No candidates to export.")
        return

    data = [
        {
            "ID": c.id,
            "Name": c.name,
            "Email": c.email,
            "Phone": c.phone,
            "Skills": c.skills,
            "Experience": c.experience,
            "Source File": c.source_filename
        }
        for c in candidates
    ]

    df = pd.DataFrame(data)
    output_path = "data/candidates.xlsx"
    os.makedirs("data", exist_ok=True)
    df.to_excel(output_path, index=False)
    print(f"[EXCEL] Exported candidate data to {output_path}")

def get_gmail_service():
    """Authenticate with Gmail and return an authorized service."""
    creds = None
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

    return build("gmail", "v1", credentials=creds)


def fetch_attachments(service, out_dir="attachments", max_results=50):
    """Fetch and download relevant attachments from Gmail inbox."""
    Path(out_dir).mkdir(exist_ok=True)
    results = service.users().messages().list(
        userId="me",
        labelIds=["INBOX"],
        q="has:attachment (filename:resume OR filename:cv)",
        maxResults=max_results
    ).execute()

    messages = results.get("messages", [])
    attachments = []
    resume_pattern = re.compile(r"(cv|resume)", re.IGNORECASE)
    allowed_exts = {".pdf", ".doc", ".docx", ".txt", ".csv"}

    for msg in messages:
        message = service.users().messages().get(userId="me", id=msg["id"]).execute()

        # Skip system/no-reply/support emails
        headers = message.get("payload", {}).get("headers", [])
        sender = next((h["value"] for h in headers if h["name"].lower() == "from"), "").lower()
        if any(excl in sender for excl in ["no-reply", "support@", "noreply@", "notification"]):
            print(f"[SKIP] System email ignored: {sender}")
            continue

        parts = message.get("payload", {}).get("parts", [])
        for part in parts:
            filename = part.get("filename", "")
            ext = Path(filename).suffix.lower()
            body = part.get("body", {})
            att_id = body.get("attachmentId")

            # ✅ Only accept resume-like files
            if not filename or not (resume_pattern.search(filename) and ext in allowed_exts):
                print(f"[SKIP] Ignoring irrelevant file: {filename}")
                continue

            try:
                att = service.users().messages().attachments().get(
                    userId="me", messageId=msg["id"], id=att_id
                ).execute()
                file_data = base64.urlsafe_b64decode(att["data"].encode("UTF-8"))
                file_path = Path(out_dir) / filename
                with open(file_path, "wb") as f:
                    f.write(file_data)
                attachments.append({"filename": filename, "path": str(file_path)})
                print(f"[DOWNLOAD] Saved: {filename}")
            except Exception as e:
                print(f"[ERROR] Failed to download {filename}: {e}")

    print(f"\n[INFO] Total attachments downloaded: {len(attachments)}")
    return attachments


def run_sync():
    """Main sync routine: download, parse, and insert resumes."""
    init_db()
    service = get_gmail_service()
    out_dir = os.environ.get("ATTACHMENTS_DIR", "attachments")
    attachments = fetch_attachments(service, out_dir=out_dir)

    db = SessionLocal()
    added, skipped = 0, 0

    for f in attachments:
        parsed = parse_attachment(f["path"])

        # Skip invalid or empty parses
        if not parsed or not parsed.get("email"):
            print(f"[WARN] Skipping invalid resume: {f['filename']}")
            skipped += 1
            continue

        # Check for duplicates before insert
        existing = db.query(Candidate).filter_by(email=parsed["email"]).first()
        if existing:
            print(f"[INFO] Duplicate found, skipping: {parsed['email']}")
            skipped += 1
            continue

        cand = Candidate(
            name=parsed.get("name"),
            email=parsed.get("email"),
            phone=parsed.get("phone"),
            skills=parsed.get("skills"),
            experience=None,
            source_filename=f.get("filename") or f.get("path"),
        )
        db.add(cand)
        added += 1

    db.commit()
    db.close()

    export_candidates_to_excel()
    print(f"\n[SUMMARY] Added {added} resumes, Skipped {skipped} files.")


if __name__ == "__main__":
    run_sync()