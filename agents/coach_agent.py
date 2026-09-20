from services.ai_service import AIService


class CoachAgent:
    def __init__(self, ai_service: AIService):
        self.ai_service = ai_service

    def reply(self, question: str, context: dict) -> dict:
        lowered = question.lower().strip()
        top_gaps = context.get("top_gaps", [])
        daily_plan = context.get("daily_plan", [])
        next_skill = top_gaps[0]["skill_name"] if top_gaps else "a portfolio project"
        action = None
        if any(phrase in lowered for phrase in ("what should i learn", "today", "study plan")):
            content = self._daily_answer(daily_plan)
        elif any(phrase in lowered for phrase in ("biggest gap", "skill gap", "why do i need")):
            gap = top_gaps[0] if top_gaps else None
            content = (f"Your highest-priority gap is **{gap['skill_name']}**. {gap['explanation']} "
                       f"{gap['priority_reason']}" if gap else "You currently meet the tracked role requirements. Use projects to strengthen evidence of your skills.")
            action = "Skill Gap"
        elif any(phrase in lowered for phrase in ("practice", "problem")):
            content = f"Let’s make today practical: open Practice and complete a focused **{next_skill}** sprint. Aim for one working artifact, then log it so I can adapt your plan."
            action = "Practice"
        elif any(phrase in lowered for phrase in ("project", "portfolio")):
            content = f"A small **{next_skill}** project is the best next portfolio signal. Open Projects for a role-matched brief and build it in short, documented milestones."
            action = "Projects"
        elif any(phrase in lowered for phrase in ("test", "assessment", "quiz")):
            content = f"I’ve queued a {next_skill} check. Take the short assessment; a score below 60% will add revision support rather than simply moving you forward."
            action = "Assessment"
        elif any(phrase in lowered for phrase in ("struggling", "failed", "stuck")):
            content = f"That’s useful feedback, not a setback. Pause the harder task, revisit one foundation lesson for **{next_skill}**, finish one beginner exercise, then retake a short assessment. Your roadmap will make room for that support."
            action = "Practice"
        elif "ready" in lowered and ("intern" in lowered or "job" in lowered):
            coverage = context.get("coverage", 0)
            content = f"Your tracked role-skill coverage is **{coverage}%**. That is a learning signal, not a hiring guarantee. Strengthen your top gaps—starting with {next_skill}—and publish two role-relevant projects with clear READMEs."
            action = "Projects"
        else:
            fallback = f"For your {context.get('career_name', 'target')} path, I would focus next on **{next_skill}**. {top_gaps[0]['priority_reason'] if top_gaps else 'Use your completed skills in a portfolio project.'}"
            content = self.ai_service.contextual_answer(question, context, fallback)
        return {"content": content, "action": action}

    @staticmethod
    def _daily_answer(plan: list[dict]) -> str:
        if not plan:
            return "Open your roadmap and choose one small portfolio-improvement task for today."
        total = sum(item["minutes"] for item in plan)
        items = "\n".join(f"{index + 1}. **{item['label']}** — {item['minutes']} min: {item['detail']}" for index, item in enumerate(plan))
        return f"Here is your **{total}-minute smart daily plan**:\n\n{items}\n\nFinish by logging the activity so your plan stays accurate."
