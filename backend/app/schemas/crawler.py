from typing import List
from typing import Optional
from pydantic import BaseModel
from app.core.enums import UrlType

class BulkUrlCreateRequest(BaseModel):
    airline_code: str 
    url_type: UrlType 
    category: Optional[str] = None
    urls: List[str]