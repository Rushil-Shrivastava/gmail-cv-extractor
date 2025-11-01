from pydantic import BaseModel
from typing import Optional

class CandidateOut(BaseModel):
    id: int
    name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    skills: Optional[str]
    experience: Optional[str]
    source_filename: Optional[str]

    class Config:
        orm_mode = True