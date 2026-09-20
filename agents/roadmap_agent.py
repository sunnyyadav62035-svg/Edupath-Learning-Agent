import math


class RoadmapAgent:
    TOPICS = {
        "python": ["variables and control flow", "functions and modules", "reading and transforming files"],
        "statistics": ["descriptive statistics", "probability", "distributions and inference"],
        "machine_learning": ["problem framing", "training and validation", "metrics and iteration"],
        "sql": ["SELECT and filtering", "joins and aggregation", "window functions"],
        "pandas": ["DataFrames", "cleaning and grouping", "joining and visualization"],
        "llm": ["model capabilities", "prompt patterns", "evaluation and safety"],
    }

    def __init__(self, skills: dict[str, dict]):
        self.skills = skills

    def build(self, prioritized_gaps: list[dict], weekly_hours: int) -> list[dict]:
        capacity = max(3, min(25, int(weekly_hours or 5)))
        roadmap, week_number = [], 1
        for gap in prioritized_gaps:
            if gap["gap"] <= 0:
                continue
            total_hours = max(3, math.ceil(gap["estimated_hours"] * gap["gap"] / max(1, gap["required_level"])))
            remaining = total_hours
            topics = self.TOPICS.get(gap["skill_id"], ["core concepts", "guided practice", "project application"])
            chunk_index = 0
            while remaining > 0:
                hours = min(capacity, remaining)
                topic_slice = topics[chunk_index % len(topics):] + topics[:chunk_index % len(topics)]
                skill = self.skills.get(gap["skill_id"], {})
                roadmap.append({
                    "week": week_number,
                    "theme": f"{gap['skill_name']} — {gap['priority']} priority",
                    "estimated_hours": hours,
                    "items": [{
                        "id": f"week-{week_number}-{gap['skill_id']}", "skill_id": gap["skill_id"],
                        "skill_name": gap["skill_name"], "status": "planned", "topics": topic_slice[:2],
                        "practice": skill.get("practice_tasks", ["Complete a focused practice task"])[chunk_index % max(1, len(skill.get("practice_tasks", [])))],
                        "project": skill.get("project_ideas", ["Create a small evidence-based project"])[chunk_index % max(1, len(skill.get("project_ideas", [])))],
                        "why_now": gap["priority_reason"],
                    }],
                })
                week_number += 1
                remaining -= hours
                chunk_index += 1
        return roadmap

    def adapt(self, roadmap: list[dict], struggle_skills: set[str], completed_skills: set[str]) -> list[dict]:
        adapted = []
        for week in roadmap:
            changed = dict(week)
            changed["items"] = []
            for item in week.get("items", []):
                item = dict(item)
                if item["skill_id"] in completed_skills:
                    item["status"] = "completed"
                elif item["skill_id"] in struggle_skills:
                    item["status"] = "support_needed"
                    item["practice"] = "Complete a beginner revision task, then retake a short assessment."
                    item["why_now"] = "The adaptive agent detected repeated low assessment scores, so this week adds support before moving on."
                changed["items"].append(item)
            adapted.append(changed)
        return adapted
