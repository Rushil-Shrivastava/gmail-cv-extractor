# app/db.py
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# --- Database setup ---
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/cv_database.db")

# Ensure the directory exists
os.makedirs(os.path.dirname(DATABASE_URL.replace("sqlite:///", "")), exist_ok=True)

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# --- Model definition ---
class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200))
    email = Column(String(200), unique=True)
    phone = Column(String(100))
    skills = Column(Text)
    experience = Column(String(100))
    text_snippet = Column(Text)
    source_filename = Column(String(300))


# --- Database utilities ---
def init_db():
    """Create tables if they don't exist"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Provide a database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def add_candidate(data):
    """Insert a new candidate record, skipping duplicates."""
    db = SessionLocal()
    try:
        # Skip empty or invalid records
        if not data.get("email"):
            print("[WARN] Skipping candidate with missing email.")
            return

        # Check if candidate already exists
        existing = db.query(Candidate).filter_by(email=data["email"]).first()
        if existing:
            print(f"[INFO] Duplicate email found, skipping: {data['email']}")
            return

        candidate = Candidate(**data)
        db.add(candidate)
        db.commit()
        print(f"[DB] Added: {data.get('email')}")
    except Exception as e:
        db.rollback()
        print(f"[DB ERROR] {e}")
    finally:
        db.close()


def get_all_candidates():
    """Return all candidates as a list of dicts"""
    db = SessionLocal()
    try:
        candidates = db.query(Candidate).all()
        return [
            {
                "id": c.id,
                "name": c.name,
                "email": c.email,
                "phone": c.phone,
                "skills": c.skills,
                "experience": c.experience,
            }
            for c in candidates
        ]
    finally:
        db.close()