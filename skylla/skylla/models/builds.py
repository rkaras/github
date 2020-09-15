from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, HttpUrl

from ..models.git import GitUrl

NHttpUrl = Optional[HttpUrl]


class BuildInfo(BaseModel):
    id: str
    version: str
    ref: str
    repo: GitUrl
    url: NHttpUrl = None
    log_url: NHttpUrl = None
    start: datetime
    end: datetime
    artifacts: Optional[List[HttpUrl]] = None


class PatchInfo(BaseModel):
    id: str
    version: str
    ref: str
    environment: str
    repo: GitUrl
    start: datetime
    end: datetime
    patches: Optional[List[HttpUrl]] = None