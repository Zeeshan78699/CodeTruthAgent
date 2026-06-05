"""
CodeTruth Agent V2
AI Interface Gateway

Purpose:
- Provide a safe AI gateway
- Standardize AI responses
- Fallback safely when AI is unavailable
- Never modify files directly
"""

from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any
import traceback


@dataclass
class AIResponse:
    success: bool
    response: str
    risk_level: str = "LOW"
    fallback_used: bool = False
    error: Optional[str] = None
    source: str = "AI_INTERFACE"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AIInterface:
    """
    Central AI gateway for CodeTruth Agent V2.

    IMPORTANT:
    This class does NOT modify files.
    This class only analyzes and returns safe structured output.
    """

    def __init__(self, ai_enabled: bool = False):
        self.ai_enabled = ai_enabled

    def is_ai_available(self) -> bool:
        """
        Checks whether AI is available.

        For Phase 1, AI is OFF by default.
        This protects V1 and allows fallback testing.
        """
        return self.ai_enabled

    def analyze_text(self, prompt: str) -> Dict[str, Any]:
        """
        Main safe AI analysis method.

        If AI is disabled/unavailable, fallback response is returned.
        """
        try:
            if not self.is_ai_available():
                return self._fallback_response(
                    reason="AI is currently disabled or unavailable."
                ).to_dict()

            # Future AI model call will be added here.
            # Example future providers:
            # - OpenAI
            # - Local LLaMA
            # - Ollama
            # - Transformers
            # - llama.cpp

            simulated_response = self._simulate_ai_response(prompt)

            return AIResponse(
                success=True,
                response=simulated_response,
                risk_level="LOW",
                fallback_used=False,
                error=None,
                source="AI_INTERFACE"
            ).to_dict()

        except Exception as exc:
            return self._fallback_response(
                reason=f"AI interface failure: {str(exc)}",
                error=traceback.format_exc()
            ).to_dict()

    def _simulate_ai_response(self, prompt: str) -> str:
        """
        Temporary Phase 1 simulation.

        This proves the V2 pipeline works before real AI is connected.
        """
        #return (
        #    "AI simulation completed safely. "
        #    "No file modification was performed. "
        #    f"Prompt received length: {len(prompt)} characters."
        #)
        raise Exception("Simulated AI timeout failure")

    def _fallback_response(
        self,
        reason: str,
        error: Optional[str] = None
    ) -> AIResponse:
        """
        Safe fallback response.

        This protects the system when AI fails.
        """
        return AIResponse(
            success=False,
            response=reason,
            risk_level="SAFE_FALLBACK",
            fallback_used=True,
            error=error,
            source="V1_FALLBACK_PROTECTION"
        )