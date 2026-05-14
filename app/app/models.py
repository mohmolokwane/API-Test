from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class GistFile(BaseModel):
    filename: str
    size: int
    language: Optional[str] = None

class GistResponse(BaseModel):
    id: str
    description: Optional[str] = None
    url: str = Field(..., alias="html_url")
    created_at: datetime
    files: List[GistFile]