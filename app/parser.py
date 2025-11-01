# app/parser.py  –  lightweight, no spaCy
import re
from pathlib import Path
import pdfplumber, docx, pandas as pd
from fuzzywuzzy import fuzz
from PIL import Image
import pytesseract

EMAIL_RE = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')
PHONE_RE = re.compile(r'(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{2,4}\)?[\s.-]?)?\d{6,12}')
SKILL_WORDS = [
    "python","java","sql","javascript","react","django","flask","aws","azure","docker",
    "kubernetes","c++","c#","html","css","node","pandas","numpy","git","linux"
]

def extract_text(path: str) -> str:
    try:
        p = Path(path)
        suf = p.suffix.lower()
        if suf == ".pdf":
            try:
                with pdfplumber.open(path) as pdf:
                    txt = "\n".join([pg.extract_text() or "" for pg in pdf.pages])
            except Exception:
                print(f"[WARN] Skipping locked or unreadable PDF: {path}")
                txt = ""
            if not txt.strip():
                try:
                    txt = pytesseract.image_to_string(Image.open(path))
                except Exception:
                    txt = ""
        elif suf in (".docx", ".doc"):
            doc = docx.Document(path)
            txt = "\n".join([p.text for p in doc.paragraphs])
        elif suf == ".csv":
            df = pd.read_csv(path, dtype=str, keep_default_na=False)
            txt = "\n".join(df.astype(str).fillna("").agg(" ".join, axis=1).tolist())
        else:
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    txt = f.read()
            except Exception:
                txt = ""
        return txt
    except Exception as e:
        print(f"[ERROR] Failed to read file {path}: {e}")
        return ""

def extract_email(t): m = EMAIL_RE.search(t or ""); return m.group(0) if m else None
def extract_phone(t): m = PHONE_RE.search(t or ""); return m.group(0) if m else None

def extract_skills(t):
    t = (t or "").lower()
    found = {s for s in SKILL_WORDS if s in t or any(fuzz.partial_ratio(s, w)>=90 for w in t.split())}
    return ", ".join(sorted(found))

def extract_name(t):
    for line in (t or "").splitlines()[:10]:
        if 1 < len(line.split()) <= 4 and line == line.title():
            return line.strip()
    return None

def extract_experience(t):
    m = re.search(r"(\d{1,2})\+?\s*years?", t or "", flags=re.I)
    if m: return f"{m.group(1)} years"
    return None

def parse_attachment(path):
    text = extract_text(path)
    return {
        "name": extract_name(text),
        "email": extract_email(text),
        "phone": extract_phone(text),
        "skills": extract_skills(text),
        "experience": extract_experience(text),
        "text_snippet": (text or "")[:2000],
    }