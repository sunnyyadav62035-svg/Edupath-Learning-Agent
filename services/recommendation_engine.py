from collections import defaultdict


class RecommendationEngine:
    def __init__(self, resources: list[dict], skills: dict[str, dict]):
        self.resources = resources
        self.skills = skills

    def for_gap(self, skill_id: str, current_level: int, limit: int = 2) -> list[dict]:
        preferred = "beginner" if current_level <= 1 else "intermediate" if current_level <= 3 else "advanced"
        matches = [item for item in self.resources if item.get("skill") == skill_id]
        matches.sort(key=lambda item: (item.get("difficulty") != preferred, item.get("estimated_hours", 0)))
        return matches[:limit]

    def for_priorities(self, prioritized_gaps: list[dict], completed_ids: set[str]) -> dict[str, list[dict]]:
        recommendations: dict[str, list[dict]] = defaultdict(list)
        used: set[str] = set(completed_ids)
        for gap in prioritized_gaps:
            for resource in self.for_gap(gap["skill_id"], gap["current_level"]):
                if resource.get("id") not in used:
                    recommendations[gap["skill_id"]].append(resource)
                    used.add(resource.get("id"))
        return dict(recommendations)
