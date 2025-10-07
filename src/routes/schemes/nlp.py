from pydantic import BaseModel
from typing import Optional

class PushRequest(BaseModel):

    do_reset : Optional[int] = 0

class SearchRequest(BaseModel):
    
    query: str
    top_k: Optional[int] = 5