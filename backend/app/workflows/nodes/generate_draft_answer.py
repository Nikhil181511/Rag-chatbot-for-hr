from typing import Dict, Any, List
from openai import AsyncOpenAI
from app.workflows.graph_state import RAGState
from app.config.settings import settings
from app.config.logging import get_logger

logger = get_logger(__name__)

HR_SYSTEM_PROMPT = """You are the official HR Knowledge Assistant for the company.
Your role is to assist employees by answering questions regarding company policies, leave entitlements, benefits, onboarding, remote work, compensation guidelines, and workplace standards.

Rules:
1. Base your answer EXCLUSIVELY on the provided Context excerpts.
2. If the context does not contain sufficient information to answer the question, clearly state that you do not have enough information and advise the employee to contact HR.
3. Use a helpful, professional, and clear tone.
4. Structure your response with concise bullet points or short paragraphs where appropriate.
5. Reference specific section titles or document names when citing information.
6. Do NOT invent rules, numbers, dates, or contact info that is not in the context.
"""


async def generate_draft_answer_node(state: RAGState) -> Dict[str, Any]:
    query = state.get("original_query", "")
    context_chunks = state.get("selected_context", [])
    conversation_history = state.get("conversation_history", [])

    if not context_chunks:
        return {
            "draft_answer": "I do not have sufficient information in the HR policy documents to answer your question. Please consult your HR representative.",
            "groundedness_result": "abstention",
        }

    # Format context block
    context_text = "\n\n---\n\n".join(
        [
            f"[Source: {c['document_name']}, Section: {c.get('section', 'General')}, Page: {c.get('page_number', 1)}]\n{c['content']}"
            for c in context_chunks
        ]
    )

    messages = [{"role": "system", "content": HR_SYSTEM_PROMPT}]

    # Append recent conversation history
    for msg in conversation_history[-6:]:
        messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})

    # Append current user query with context
    user_prompt = f"Context Information:\n{context_text}\n\nUser Question: {query}\n\nPlease provide a clear, accurate, and fully grounded answer based solely on the context above."
    messages.append({"role": "user", "content": user_prompt})

    draft_answer = ""
    api_key = settings.effective_llm_key
    lf_root = state.get("_lf_root")

    import time
    llm_start = time.time()

    span = None
    if lf_root:
        try:
            span = lf_root.start_observation(
                name="generate_draft_answer",
                input={"query": query, "context_chunks_count": len(context_chunks)},
                metadata={"model": settings.LLM_MODEL},
            )
        except Exception:
            pass

    if api_key:
        try:
            if settings.LLM_PROVIDER == "gemini":
                # Connect to Google Gemini using Google's official OpenAI-compatible endpoint
                client = AsyncOpenAI(
                    api_key=api_key,
                    base_url=settings.GEMINI_BASE_URL,
                )
            else:
                client = AsyncOpenAI(api_key=api_key)

            response = await client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=messages,
                temperature=0.0,
                max_tokens=1000,
            )
            draft_answer = response.choices[0].message.content or ""
            if response.usage:
                prompt_tokens = response.usage.prompt_tokens or 0
                completion_tokens = response.usage.completion_tokens or 0
                total_tokens = response.usage.total_tokens or (prompt_tokens + completion_tokens)
            else:
                prompt_tokens = len(user_prompt) // 4
                completion_tokens = len(draft_answer) // 4
                total_tokens = prompt_tokens + completion_tokens
        except Exception as e:
            logger.error("LLM generation failed", exc_info=e)
            draft_answer = f"Based on {context_chunks[0]['document_name']}:\n\n{context_chunks[0]['content'][:300]}..."
            prompt_tokens = len(user_prompt) // 4
            completion_tokens = len(draft_answer) // 4
            total_tokens = prompt_tokens + completion_tokens
    else:
        # Deterministic grounded fallback when running in offline/local test mode
        top_doc = context_chunks[0]
        draft_answer = (
            f"Based on the **{top_doc['document_name']}** (Section: {top_doc.get('section', 'Policy')}):\n\n"
            f"{top_doc['content'][:400]}..."
        )
        prompt_tokens = len(user_prompt) // 4
        completion_tokens = len(draft_answer) // 4
        total_tokens = prompt_tokens + completion_tokens

    llm_duration = round(time.time() - llm_start, 3)

    if span:
        try:
            span.update(
                output=draft_answer,
                metadata={
                    "duration_seconds": llm_duration,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens,
                },
            )
            span.end()
        except Exception:
            pass

    existing_durations = dict(state.get("node_durations") or {})
    existing_durations["generate_draft_answer"] = llm_duration

    return {
        "draft_answer": draft_answer,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "node_durations": existing_durations,
    }
