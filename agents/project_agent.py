class ProjectAgent:
    def __init__(self, projects: list[dict]):
        self.projects = projects

    def recommend(self, career_id: str, missing_skills: set[str], completed_ids: set[str], limit: int = 3) -> list[dict]:
        candidates = []
        for project in self.projects:
            if project.get("id") in completed_ids:
                continue
            role_match = career_id in project.get("roles", [])
            skill_overlap = len(set(project.get("skills", [])) & missing_skills)
            if role_match or skill_overlap:
                item = dict(project)
                item["match_score"] = (10 if role_match else 0) + skill_overlap
                candidates.append(item)
        return sorted(candidates, key=lambda item: (-item["match_score"], item["difficulty"]))[:limit]
