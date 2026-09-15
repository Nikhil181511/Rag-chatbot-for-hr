import re
from typing import Dict, Any, Optional
from datetime import datetime


class MetadataEnricher:
    # HR Category detection patterns
    CATEGORY_PATTERNS = {
        "leave": r"\b(leave|vacation|time off|pto|sick leave|maternity|paternity|bereavement|parental|sabbatical|carryover)\b",
        "benefits": r"\b(health insurance|medical|dental|vision|401k|pension|wellness|gym|allowance|stipend|bonus)\b",
        "onboarding": r"\b(onboarding|new hire|probation|orientation|documents required|first day|welcome)\b",
        "wfh": r"\b(work from home|remote work|hybrid|telecommuting|wfh|remote allowance|office equipment)\b",
        "conduct": r"\b(code of conduct|harassment|anti-discrimination|ethics|disciplinary|whistleblower|workplace behavior)\b",
        "compensation": r"\b(salary band|payroll|reimbursement|per diem|travel expense|overtime|appraisal)\b",
        "performance": r"\b(kpi|performance review|okr|pip|promotion|evaluation|feedback)\b",
    }

    DATE_PATTERNS = [
        r"effective\s+date\s*[:\-]?\s*([A-Za-z]+\s+\d{1,2},?\s+\d{4}|\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4})",
        r"last\s+updated\s*[:\-]?\s*([A-Za-z]+\s+\d{1,2},?\s+\d{4}|\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4})",
        r"version\s+date\s*[:\-]?\s*([A-Za-z]+\s+\d{1,2},?\s+\d{4}|\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4})",
    ]

    REGION_PATTERNS = {
        "US": r"\b(united states|u\.s\.|usa|california|new york|texas|fmla|flsa|w-2|401\(?k\)?)\b",
        "UK": r"\b(united kingdom|u\.k\.|uk|london|hmrc|statutory sick pay|ssp|national insurance)\b",
        "EU": r"\b(european union|eu|gdpr|germany|france|netherlands)\b",
        "Global": r"\b(global|all regions|worldwide|all employees)\b",
    }

    @classmethod
    def enrich_document(cls, title: str, content: str) -> Dict[str, Any]:
        combined_text = f"{title}\n{content[:4000]}".lower()
        
        # Detect category
        detected_category: Optional[str] = None
        for category, pattern in cls.CATEGORY_PATTERNS.items():
            if re.search(pattern, combined_text, re.IGNORECASE):
                detected_category = category
                break

        # Detect effective date
        effective_date_str: Optional[str] = None
        for date_pat in cls.DATE_PATTERNS:
            match = re.search(date_pat, content[:3000], re.IGNORECASE)
            if match:
                effective_date_str = match.group(1)
                break

        # Detect region
        detected_region: Optional[str] = None
        for region, reg_pat in cls.REGION_PATTERNS.items():
            if re.search(reg_pat, combined_text, re.IGNORECASE):
                detected_region = region
                break

        return {
            "document_category": detected_category,
            "effective_date": effective_date_str,
            "region": detected_region,
        }
