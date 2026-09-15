import json
import asyncio
import os
import sys
from typing import Dict, Any, List

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

from app.workflows.rag_graph import rag_app
from evaluation.metrics.generation_metrics import GenerationMetrics


async def run_benchmark(dataset_path: str = "evaluation/datasets/hr-golden-v1.json"):
    print(f"Loading dataset from {dataset_path}...")
    with open(dataset_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    test_cases = data.get("test_cases", [])
    print(f"Running benchmark on {len(test_cases)} test cases...\n")

    results: List[Dict[str, Any]] = []

    for tc in test_cases:
        tc_id = tc["id"]
        query = tc["query"]
        category = tc["category"]
        expected_intent = tc.get("expected_intent")

        print(f"[{tc_id}] Testing '{query}'...")

        initial_state = {
            "original_query": query,
            "conversation_history": [],
        }

        state = await rag_app.ainvoke(initial_state)
        answer = state.get("final_answer", "")
        intent = state.get("intent", "")
        status = state.get("final_answer_status", "")
        citations = state.get("citations", [])

        # Calculate metrics
        relevance = GenerationMetrics.answer_relevance(query, answer)

        passed = True
        if expected_intent and intent != expected_intent:
            passed = False

        results.append({
            "id": tc_id,
            "category": category,
            "passed": passed,
            "intent": intent,
            "status": status,
            "relevance": relevance,
            "citations_count": len(citations),
        })

    print("\n" + "="*50)
    print("BENCHMARK RESULTS SUMMARY")
    print("="*50)
    for r in results:
        status_symbol = "✓" if r["passed"] else "✗"
        print(f"{status_symbol} [{r['id']}] {r['category']} - Intent: {r['intent']} | Relevance: {r['relevance']:.2f}")

    pass_count = sum(1 for r in results if r["passed"])
    print(f"\nTotal: {len(results)} | Passed: {pass_count} ({pass_count/len(results)*100:.1f}%)")


if __name__ == "__main__":
    asyncio.run(run_benchmark())
