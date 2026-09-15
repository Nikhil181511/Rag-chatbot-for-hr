import re
from typing import List


class GenerationMetrics:
    @staticmethod
    def answer_relevance(query: str, answer: str) -> float:
        """Heuristic semantic keyword overlap for offline evaluation."""
        if not answer:
            return 0.0
        query_words = set(re.findall(r"\w+", query.lower()))
        stop_words = {"what", "is", "the", "a", "an", "and", "or", "for", "to", "in", "of", "do", "how", "does"}
        meaningful_query_words = query_words - stop_words
        if not meaningful_query_words:
            return 1.0
        answer_lower = answer.lower()
        matched = sum(1 for w in meaningful_query_words if w in answer_lower)
        return matched / len(meaningful_query_words)

    @staticmethod
    def faithfulness(answer: str, context_chunks: List[str]) -> float:
        """Groundedness score measuring context containment."""
        if not answer or not context_chunks:
            return 0.0
        all_context = " ".join(context_chunks).lower()
        sentences = re.split(r"[.!?]", answer)
        valid_sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
        if not valid_sentences:
            return 1.0
        
        supported = 0
        for sent in valid_sentences:
            words = [w for w in re.findall(r"\w+", sent.lower()) if len(w) > 3]
            if not words:
                supported += 1
                continue
            matches = sum(1 for w in words if w in all_context)
            if matches / len(words) >= 0.5:
                supported += 1

        return supported / len(valid_sentences)
