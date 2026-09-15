import re
from typing import Tuple

INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
    r"system\s+prompt",
    r"reveal\s+(your\s+)?(prompt|instructions|secret|password)",
    r"you\s+are\s+now\s+(an\s+unrestricted|a\s+different|in\s+developer\s+mode)",
    r"jailbreak",
    r"dan\s+mode",
    r"disregard\s+all\s+(rules|guidelines)",
    r"pretend\s+you\s+have\s+no\s+rules",
    r"bypass\s+security",
    r"override\s+system",
    r"output\s+the\s+full\s+prompt",
]


class PromptInjectionScreen:
    @classmethod
    def check_query(cls, query: str) -> Tuple[bool, str]:
        """
        Returns (is_injection, reason)
        """
        query_lower = query.lower().strip()

        for pattern in INJECTION_PATTERNS:
            if re.search(pattern, query_lower, re.IGNORECASE):
                return True, f"Matched injection pattern: {pattern}"

        return False, "ok"
