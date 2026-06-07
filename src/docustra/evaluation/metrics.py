"""
RAG evaluation using RAGAS metrics:
  - Faithfulness: is the answer grounded in the retrieved context?
  - Answer Relevancy: does the answer address the question?
  - Context Precision: are retrieved chunks actually used?
  - Context Recall: does the retrieved context cover the answer?
"""

from __future__ import annotations

import sys
import types
from dataclasses import dataclass

from docustra.core import EvaluationError, get_logger

logger = get_logger(__name__)


def _patch_ragas_compat() -> None:
    """
    Inject a lightweight compatibility shim before importing ragas.

    ragas ≤ 0.2.x imports ``langchain_community.chat_models.vertexai``
    which was removed from langchain-community in 0.3+.  We inject a
    stub module so the import succeeds without pinning the entire
    dependency tree to old versions.
    """
    missing = "langchain_community.chat_models.vertexai"
    if missing in sys.modules:
        return
    try:
        import langchain_community.chat_models.vertexai  # noqa: F401

        return  # already importable — nothing to do
    except ModuleNotFoundError:
        pass

    stub = types.ModuleType(missing)

    class ChatVertexAI:  # type: ignore[no-redef]
        """Stub — install langchain-google-vertexai for real VertexAI support."""

    stub.ChatVertexAI = ChatVertexAI  # type: ignore[attr-defined]
    sys.modules[missing] = stub
    # Also register sub-key so `from … import ChatVertexAI` works
    parent = sys.modules.get("langchain_community.chat_models")
    if parent is not None:
        parent.vertexai = stub  # type: ignore[attr-defined]


_patch_ragas_compat()

# --- ragas imports (must come after the compat patch) ---
import warnings  # noqa: E402

with warnings.catch_warnings():
    warnings.simplefilter("ignore", DeprecationWarning)
    from datasets import Dataset  # noqa: E402
    from ragas import evaluate  # noqa: E402
    from ragas.metrics import (  # noqa: E402
        answer_relevancy,
        context_precision,
        context_recall,
        faithfulness,
    )


@dataclass
class EvaluationResult:
    faithfulness: float
    answer_relevancy: float
    context_precision: float
    context_recall: float

    def as_dict(self) -> dict:
        return {
            "faithfulness": round(self.faithfulness, 4),
            "answer_relevancy": round(self.answer_relevancy, 4),
            "context_precision": round(self.context_precision, 4),
            "context_recall": round(self.context_recall, 4),
        }


def evaluate_rag(
    questions: list[str],
    answers: list[str],
    contexts: list[list[str]],
    ground_truths: list[str] | None = None,
) -> EvaluationResult:
    if not (len(questions) == len(answers) == len(contexts)):
        raise EvaluationError("questions, answers, and contexts must have the same length.")

    data: dict[str, list] = {
        "question": questions,
        "answer": answers,
        "contexts": contexts,
    }
    if ground_truths:
        data["ground_truth"] = ground_truths

    dataset = Dataset.from_dict(data)
    metrics = [faithfulness, answer_relevancy, context_precision]
    if ground_truths:
        metrics.append(context_recall)

    try:
        result = evaluate(dataset, metrics=metrics)
        return EvaluationResult(
            faithfulness=float(result["faithfulness"]),
            answer_relevancy=float(result["answer_relevancy"]),
            context_precision=float(result["context_precision"]),
            context_recall=float(result.get("context_recall", 0.0)),
        )
    except Exception as e:
        raise EvaluationError(f"RAGAS evaluation failed: {e}") from e
