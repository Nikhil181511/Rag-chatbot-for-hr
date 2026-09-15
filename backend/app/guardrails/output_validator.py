from typing import List, Dict, Any, Tuple


class OutputValidator:
    STANDARD_ABSTENTION = (
        "I do not have sufficient information in the provided HR policy documents "
        "to answer your question accurately. Please consult your HR representative or manager."
    )

    @classmethod
    def validate_answer(
        cls, answer: str, context_chunks: List[Dict[str, Any]], citations: List[Dict[str, Any]]
    ) -> Tuple[bool, str]:
        """
        Validates whether the answer is grounded or if it requires abstention.
        Returns (is_valid, validation_status)
        """
        if not answer or not answer.strip():
            return False, "empty_answer"

        # If no context was selected and answer is not an explicit greeting/help message
        if not context_chunks and len(answer) > 100:
            return False, "ungrounded_hallucination"

        return True, "passed"
