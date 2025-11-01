import re
import hashlib

EMAIL_RE = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')
PHONE_RE = re.compile(r'(?:\+?\d{1,3}[\s-]?)?(?:\(?\d{2,4}\)?[\s-]?)?\d{6,10}')

DEFAULT_SKILLS = [
    'python','java','sql','javascript','react','django','flask','aws','azure','docker','kubernetes','c++','c#'
]


def sha256_of_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()


def extract_email(text: str):
    m = EMAIL_RE.search(text or '')
    return m.group(0) if m else None

def extract_phone(text: str):
    m = PHONE_RE.search(text or '')
    return m.group(0) if m else None


def extract_skills(text: str, skill_list=None):
    skill_list = skill_list or DEFAULT_SKILLS
    found = []
    low = (text or '').lower()
    for s in skill_list:
        if s.lower() in low:
            found.append(s)
    return ', '.join(sorted(set(found)))