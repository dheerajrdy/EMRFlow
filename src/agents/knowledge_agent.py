"""
Knowledge Base Agent.

Answers common clinic FAQs using simple keyword matching over the mock FAQ
dataset. Falls back gracefully when no match is found.
"""

import re
from typing import Any, Dict, List, Optional

from src.agents.base_agent import AgentResult, AgentStatus, BaseAgent
from src.utils.data_loader import DataLoader


class KnowledgeAgent(BaseAgent):
    """Agent for answering frequently asked questions."""

    def __init__(
        self,
        model_client,
        data_loader: Optional[DataLoader] = None,
        faq: Optional[List[Dict[str, str]]] = None,
        **kwargs
    ):
        super().__init__(model_client, **kwargs)
        self.data_loader = data_loader or DataLoader()
        self.faq = faq if faq is not None else self.data_loader.load_faq()

    async def execute(self, input_data: Dict[str, Any]) -> AgentResult:
        """
        Expected input_data: {"query": "..."}
        """
        self._validate_input(input_data)
        query = input_data.get("query", "")
        answer = self.answer_question(query)

        if answer:
            return self._create_success_result(
                {
                    "question": answer["question"],
                    "answer": answer["answer"],
                    "confidence": answer["confidence"]
                }
            )

        return AgentResult(
            status=AgentStatus.PARTIAL,
            output={
                "answer": None,
                "message": "No FAQ match found",
                "query": self._protect_phi(query)
            },
            warnings=["No FAQ matched query"]
        )

    def answer_question(self, query: str) -> Optional[Dict[str, Any]]:
        """Return the best FAQ match for the query."""
        tokens = self._tokenize(query)
        if not tokens:
            return None

        best_entry: Optional[Dict[str, str]] = None
        best_score = 0

        for entry in self.faq:
            entry_tokens = self._tokenize(entry.get("question", ""))
            score = len(tokens.intersection(entry_tokens))
            if score > best_score:
                best_entry = entry
                best_score = score

        # Require at least 2 matching tokens to avoid false positives from common words
        if best_entry and best_score >= 2:
            return {
                "question": best_entry.get("question"),
                "answer": best_entry.get("answer"),
                "confidence": best_score / max(len(tokens), 1)
            }
        return None

    @staticmethod
    def _tokenize(text: str) -> set:
        tokens = re.findall(r"[a-zA-Z0-9]+", text.lower())
        return set(tokens)
