from typing import Optional
from fastapi import APIRouter, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.schemas.suggestion import SuggestionResponse

router = APIRouter(prefix="/suggestions", tags=["Suggestions"])

SAMPLE_SUGGESTIONS = [
    "What is the annual leave entitlement for full-time employees?",
    "How does the unused leave carryover policy work?",
    "What documents are required during the first week of onboarding?",
    "What is the work from home equipment allowance and internet stipend?",
    "When does company health insurance coverage begin?",
    "What is the policy for parental leave and primary caregivers?",
    "How do I submit an expense reimbursement report?",
    "What are the official working hours and core office days?",
]


@router.get("", response_model=SuggestionResponse)
async def get_suggestions(
    q: Optional[str] = Query(None, min_length=1),
    limit: int = Query(5, ge=1, le=10),
):
    if not q:
        return SuggestionResponse(suggestions=SAMPLE_SUGGESTIONS[:limit])

    query_lower = q.lower()
    matched = [s for s in SAMPLE_SUGGESTIONS if query_lower in s.lower()]
    if not matched:
        matched = [f"What is the policy on {q}?", f"Tell me more about {q} in our handbook"]

    return SuggestionResponse(suggestions=matched[:limit])


@router.post("/generate", response_model=SuggestionResponse)
async def generate_suggestions(db: AsyncSession = Depends(get_db)):
    return SuggestionResponse(suggestions=SAMPLE_SUGGESTIONS[:4])
