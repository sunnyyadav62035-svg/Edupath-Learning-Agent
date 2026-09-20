import os
from typing import Any


class AIService:
    """Optional LLM adapter with a dependable local fallback.

    The app never sends learner data to an external provider unless the user has
    explicitly configured an API key in the environment or Streamlit secrets.
    """

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    @property
    def is_available(self) -> bool:
        return bool(self.api_key)

    @property
    def mode_label(self) -> str:
        return "AI-enhanced mode" if self.is_available else "Demo Mode — rule-based AI fallback"

    def generate(self, system_prompt: str, user_prompt: str, fallback: str) -> str:
        """Return an LLM answer when configured, otherwise the supplied safe fallback."""
        if not self.is_available:
            return fallback
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            response = client.chat.completions.create(
                model=self.model,
                temperature=0.4,
                max_tokens=600,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            content = response.choices[0].message.content
            return content.strip() if content else fallback
        except Exception:
            return fallback

    def contextual_answer(self, question: str, context: dict[str, Any], fallback: str) -> str:
        profile = context.get("profile", {})
        system = (
            "You are EduPath AI Coach, a precise supportive career-learning coach. "
            "Use only the learner context supplied. Do not promise employment, invent achievements, "
            "or give generic advice without tying it to the roadmap and skill gaps. Keep the answer under 180 words."
        )
        user = (
            f"Learner: {profile.get('name', 'Learner')}; target role: {context.get('career_name', '')}; "
            f"weekly hours: {profile.get('weekly_hours', 0)}; gaps: {context.get('top_gaps', [])}; "
            f"next items: {context.get('next_items', [])}.\nQuestion: {question}"
        )
        return self.generate(system, user, fallback)
