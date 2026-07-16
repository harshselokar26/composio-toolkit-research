from typing import List

from pydantic import BaseModel, Field


class AppResearch(BaseModel):

    name: str

    category: str

    description: str

    auth_method: str

    self_serve: str

    credential_requirement: str

    api_type: str

    api_scope: str

    mcp_support: str

    buildability: str

    blocker: str

    evidence_url: str

    confidence: int

    manual_review: bool = False

    issues: List[str] = Field(default_factory=list)