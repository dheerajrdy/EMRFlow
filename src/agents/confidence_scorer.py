"""
LLM-as-a-judge confidence scorer for DialogueManager responses.

Provides a small wrapper around the ModelClient so we can score responses
and flag low-confidence turns for human review.
"""

import logging
import re
from typing import Any, Dict, Iterable, Optional

from src.models.model_client import ModelClient

logger = logging.getLogger(__name__)


CONFIDENCE_EVALUATION_PROMPT = """
You are evaluating the quality and correctness of an AI healthcare assistant's response.

User Query: {user_query}

Agent Response: {agent_response}

Context:
- Intent: {intent}
- Entities Extracted: {entities}
- Patient Authenticated: {authenticated}
- Conversation History: {history}

Evaluate the response on these criteria:
1. Correctness: Does it accurately address the user's query?
2. Completeness: Does it provide all necessary information?
3. Clarity: Is it clear and unambiguous?
4. Safety: Does it avoid medical advice without authorization?
5. Context Awareness: Does it use conversation context appropriately?

Assign a confidence score on a scale of 0.0-1.0:
- 1.0: Excellent response, fully confident
- 0.7-0.9: Good response, minor uncertainties
- 0.4-0.6: Acceptable but should be reviewed
- 0.0-0.3: Poor response, likely incorrect

Return ONLY a float between 0.0 and 1.0. No explanation needed.
"""


class ConfidenceScorer:
    """
    LLM-as-a-judge evaluator for agent response quality.
    """

    def __init__(self, model_client: ModelClient, threshold: float = 0.7, temperature: float = 0.1):
        """
        Initialize confidence scorer.

        Args:
            model_client: LLM client for scoring
            threshold: Confidence threshold below which to flag for review
            temperature: Sampling temperature for the judge prompt
        """
        self.model_client = model_client
        self.threshold = threshold
        self.temperature = temperature

    async def score_response(self, user_query: str, agent_response: str, context: Dict[str, Any]) -> float:
        """
        Score agent response confidence using LLM-as-a-judge.

        Args:
            user_query: Original user utterance
            agent_response: Agent's generated response
            context: Conversation context (intent, entities, patient_id, history)

        Returns:
            Confidence score between 0.0 and 1.0
        """
        prompt = CONFIDENCE_EVALUATION_PROMPT.format(
            user_query=user_query or "",
            agent_response=agent_response or "",
            intent=context.get("intent", "Unknown"),
            entities=context.get("entities", {}),
            authenticated=context.get("authenticated", False),
            history=self._format_history(context.get("history")),
        )

        try:
            response = await self.model_client.generate(
                prompt=prompt,
                temperature=self.temperature,
                max_tokens=20,
            )
            parsed = self._parse_score(response.content)
            if parsed is None:
                raise ValueError("Failed to parse confidence score from model output")
            return parsed
        except Exception as exc:  # pragma: no cover - defensive path
            logger.warning(f"Confidence scoring fell back to heuristic due to error: {exc}")
            return self._heuristic_score(user_query, agent_response, context)

    def should_flag_for_review(self, score: float) -> bool:
        """Determine if response should be flagged for human review."""
        return score < self.threshold

    async def explain_score(self, user_query: str, agent_response: str, score: float) -> str:
        """
        Generate human-readable explanation of why score was assigned.

        Returns:
            Explanation string
        """
        explanation_prompt = (
            "Explain briefly why the following response received its confidence score. "
            "Keep the explanation under 60 words.\n\n"
            f"User: {user_query}\n"
            f"Response: {agent_response}\n"
            f"Score: {score:.2f}\n\n"
            "Explanation:"
        )
        try:
            result = await self.model_client.generate(
                prompt=explanation_prompt,
                temperature=0.3,
                max_tokens=120,
            )
            return result.content.strip()
        except Exception:  # pragma: no cover - defensive fallback
            return "Confidence explanation unavailable (fallback used)."

    @staticmethod
    def _format_history(history: Optional[Iterable[Dict[str, str]]]) -> str:
        """Render a short view of recent conversation history."""
        if not history:
            return "[]"
        formatted = []
        for turn in history:
            role = turn.get("role", "unknown")
            text = turn.get("text", "")
            formatted.append(f"{role}: {text}")
        return "; ".join(formatted[-3:])

    @staticmethod
    def _parse_score(raw: str) -> Optional[float]:
        """Parse a float score from model output and clamp to [0, 1]."""
        if raw is None:
            return None
        match = re.search(r"([01](?:\.\d+)?)", str(raw))
        if not match:
            return None
        try:
            value = float(match.group(1))
        except ValueError:
            return None
        return max(0.0, min(1.0, value))

    @staticmethod
    def _heuristic_score(user_query: str, agent_response: str, context: Dict[str, Any]) -> float:
        """
        Heuristic backup when LLM scoring fails (keeps system resilient in offline tests).
        """
        if not agent_response:
            return 0.1

        score = 0.75

        # Penalize vague responses
        lower_response = agent_response.lower()
        if any(phrase in lower_response for phrase in ["not sure", "unsure", "maybe", "perhaps"]):
            score -= 0.2

        # Reward responses that mention relevant entities/intent
        intent = (context.get("intent") or "").lower()
        if intent and intent != "other" and intent in lower_response:
            score += 0.05

        entities = context.get("entities") or {}
        for value in entities.values():
            if value and str(value).lower() in lower_response:
                score += 0.02

        # Slight penalty for extremely short answers
        word_count = len(agent_response.split())
        if word_count < 4:
            score -= 0.25
        elif word_count > 120:
            score -= 0.05

        return max(0.0, min(1.0, score))

