from typing import Optional
from pydantic import BaseModel, HttpUrl


class EvidenceItemSchema(BaseModel):
    id: Optional[str] = None
    title: str
    source_name: str
    source_url: Optional[str] = None
    publisher: Optional[str] = None
    publish_date: Optional[str] = None
    snippet: str
    stance: str  # SUPPORTS, CONTRADICTS, NEUTRAL, CONTEXT
    credibility_score: float = 75.0

    class Config:
        from_attributes = True


class SourceRegistryItem(BaseModel):
    domain: str
    name: str
    category: str  # FACT_CHECKER, NEWS_WIRE, MAINSTREAM_MEDIA, ACADEMIC, SOCIAL
    reliability_score: float  # 0 to 100
    is_ifcn_signatory: bool = False
