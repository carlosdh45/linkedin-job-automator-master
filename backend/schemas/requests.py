from typing import Optional

from pydantic import BaseModel


class SkipRequest(BaseModel):
    reason: Optional[str] = None


class NeedsResearchRequest(BaseModel):
    note: Optional[str] = None
