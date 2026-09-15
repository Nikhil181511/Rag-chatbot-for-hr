import re
from typing import Tuple


class SensitiveDataRedactor:
    # Patterns for SSN, credit cards, confidential individual employee salary details
    SSN_PATTERN = r"\b\d{3}-\d{2}-\d{4}\b"
    CREDIT_CARD_PATTERN = r"\b(?:\d{4}[-\s]?){3}\d{4}\b"
    INDIVIDUAL_SALARY_PATTERN = r"(?:john|jane|employee\s+#?\d+|[A-Z][a-z]+\s+[A-Z][a-z]+)'s?\s+salary\s+is\s+(\$[\d,]+|\d+k)"

    @classmethod
    def redact(cls, text: str) -> Tuple[str, bool]:
        """
        Redacts highly sensitive personal data. Returns (sanitized_text, was_redacted).
        """
        sanitized = text
        redacted = False

        if re.search(cls.SSN_PATTERN, sanitized):
            sanitized = re.sub(cls.SSN_PATTERN, "[REDACTED-SSN]", sanitized)
            redacted = True

        if re.search(cls.CREDIT_CARD_PATTERN, sanitized):
            sanitized = re.sub(cls.CREDIT_CARD_PATTERN, "[REDACTED-CARD]", sanitized)
            redacted = True

        if re.search(cls.INDIVIDUAL_SALARY_PATTERN, sanitized, re.IGNORECASE):
            sanitized = re.sub(cls.INDIVIDUAL_SALARY_PATTERN, "the employee's compensation is [CONFIDENTIAL]", sanitized, flags=re.IGNORECASE)
            redacted = True

        return sanitized, redacted
