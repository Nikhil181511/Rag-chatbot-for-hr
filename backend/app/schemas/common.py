from typing import Optional, Generic, TypeVar, Any
from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[Any] = None


class ErrorResponse(BaseModel):
    error: ErrorDetail


class HealthResponse(BaseModel):
    status: str = "ok"
    timestamp: str


class ReadyResponse(BaseModel):
    status: str
    database: str
    vector_index: str
    message: Optional[str] = None
