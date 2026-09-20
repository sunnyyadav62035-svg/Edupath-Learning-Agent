from utils.helpers import title_case_skill


class PriorityAgent:
    def __init__(self, skills: dict[str, dict]):
        self.skills = skills

    def prioritize(self, gaps: list[dict]) -> list[dict]:
        unresolved = {gap["skill_id"] for gap in gaps if gap["gap"] > 0}
        prerequisite_targets = {
            prerequisite for gap in gaps if gap["gap"] > 0
            for prerequisite in gap.get("prerequisites", []) if prerequisite in unresolved
        }
        results = []
        for gap in gaps:
            item = dict(gap)
            if item["gap"] == 0:
                item.update(priority_score=0, priority="Maintained", priority_reason="You meet this requirement; reinforce it in projects.")
                results.append(item)
                continue
            time_factor = max(0, 12 - min(item["estimated_hours"], 36) / 3)
            foundation_bonus = 18 if item["skill_id"] in prerequisite_targets else 0
            readiness_bonus = item["current_level"] * 2
            score = round(item["gap"] / max(1, item["required_level"]) * 38 + item["importance"] * 9 + foundation_bonus + readiness_bonus + time_factor)
            priority = "Critical" if score >= 75 else "High" if score >= 53 else "Medium"
            reasons = [f"{item['gap']}-level gap", f"{item['importance']}/5 role importance"]
            if foundation_bonus:
                reasons.append("unblocks dependent skills")
            if readiness_bonus >= 4:
                reasons.append("builds on what you already know")
            item.update(priority_score=score, priority=priority, priority_reason="Priority reflects " + ", ".join(reasons) + ".")
            results.append(item)
        return sorted(results, key=lambda item: (-item["priority_score"], -item["gap"], item["skill_name"]))

    def explain_gap(self, gap: dict) -> dict:
        skill = self.skills.get(gap["skill_id"], {})
        name = title_case_skill(gap["skill_id"], self.skills)
        prereqs = [title_case_skill(item, self.skills) for item in skill.get("prerequisites", [])]
        return {
            "why": f"{name} supports the day-to-day work expected of this target role.",
            "current": f"Your current self-assessed level is {gap['current_level']}/5.",
            "learn": skill.get("description", f"Build practical capability in {name}."),
            "how": "Start with a guided resource, then complete a small practice task before a project.",
            "prove": "Publish a concise project README, code repository, and a short reflection on the result.",
            "prerequisites": prereqs,
        }
