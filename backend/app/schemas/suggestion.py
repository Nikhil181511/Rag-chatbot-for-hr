from typing import List
from pydantic import BaseModel


class SuggestionResponse(BaseModel):
    suggestions: List[str]
