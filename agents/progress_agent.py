from datetime import datetime


class ProgressAgent:
    def summary(self, gaps: list[dict], profile: dict, event_summary: dict, assessment_history: list[dict]) -> dict:
        total_required = sum(item["required_level"] for item in gaps)
        current_coverage = sum(min(item["current_level"], item["required_level"]) for item in gaps)
        coverage = round(100 * current_coverage / total_required) if total_required else 0
        strong = [item for item in gaps if item["classification"] == "Strong"]
        developing = [item for item in gaps if item["classification"] == "Developing"]
        remaining = [item for item in gaps if item["classification"] == "Gap"]
        events = event_summary.get("events", {})
        return {
            "coverage": coverage, "strong": strong, "developing": developing, "remaining": remaining,
            "completed_resources": events.get("resource", {}).get("count", 0),
            "completed_practice": events.get("practice", {}).get("count", 0),
            "completed_projects": events.get("project", {}).get("count", 0),
            "learning_minutes": sum(value.get("minutes", 0) for value in events.values()),
            "assessments": len(assessment_history),
        }

    @staticmethod
    def detect_struggles(history: list[dict], skills: dict[str, dict]) -> list[dict]:
        by_skill: dict[str, list[float]] = {}
        for result in history:
            by_skill.setdefault(result["skill_id"], []).append(float(result["score"]))
        alerts = []
        for skill_id, scores in by_skill.items():
            recent = scores[:3]
            if len(recent) >= 3 and sum(recent) / len(recent) < 60:
                alerts.append({
                    "skill_id": skill_id, "skill_name": skills.get(skill_id, {}).get("name", skill_id.title()),
                    "scores": recent, "recommendation": "Review one foundation resource, complete five short practice questions, then retake a focused assessment.",
                })
        return alerts

    @staticmethod
    def daily_plan(prioritized_gaps: list[dict], weekly_hours: int) -> list[dict]:
        minutes = max(30, min(120, round(max(1, weekly_hours) * 60 / 5)))
        goals = [item for item in prioritized_gaps if item["gap"] > 0][:3]
        if not goals:
            return [{"label": "Portfolio reinforcement", "minutes": minutes, "detail": "Improve, document, or share a completed project."}]
        weights = [0.5, 0.3, 0.2]
        return [{"label": goal["skill_name"], "minutes": max(10, round(minutes * weights[index])), "detail": goal["priority_reason"]}
                for index, goal in enumerate(goals)]

    def report(self, profile: dict, career_name: str, summary: dict, prioritized_gaps: list[dict], struggles: list[dict]) -> str:
        acquired = ", ".join(item["skill_name"] for item in summary["strong"]) or "No target skills marked complete yet"
        in_progress = ", ".join(item["skill_name"] for item in summary["developing"]) or "No developing skills yet"
        gaps = ", ".join(item["skill_name"] for item in summary["remaining"][:4]) or "No major gaps identified"
        next_steps = [item["skill_name"] for item in prioritized_gaps if item["gap"] > 0][:3]
        extra = " Give extra attention to " + ", ".join(item["skill_name"] for item in struggles) + "." if struggles else ""
        return (
            f"EduPath Progress Report — {datetime.now().strftime('%d %b %Y')}\n\n"
            f"Learner: {profile.get('name', 'Learner')}\nTarget role: {career_name}\n\n"
            f"Skills acquired: {acquired}\nSkills in progress: {in_progress}\nRemaining gaps: {gaps}\n\n"
            f"Career skill coverage: {summary['coverage']}% (a learning signal, not a job-readiness guarantee).\n"
            f"Learning activity: {summary['learning_minutes']} minutes logged, {summary['completed_resources']} resources, "
            f"{summary['completed_practice']} practice tasks, and {summary['completed_projects']} projects completed.\n\n"
            f"Recommended next steps:\n" + "\n".join(f"{index + 1}. Focus on {step}." for index, step in enumerate(next_steps)) + extra
        )
