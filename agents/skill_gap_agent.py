from utils.helpers import title_case_skill


class SkillGapAgent:
    def __init__(self, skills: dict[str, dict]):
        self.skills = skills

    def analyze(self, profile: dict, career: dict) -> list[dict]:
        findings = []
        for skill_id, requirement in career.get("skills", {}).items():
            current = int(profile.get("skills", {}).get(skill_id, 0))
            required = int(requirement.get("required_level", 0))
            gap = max(0, required - current)
            if gap == 0:
                classification = "Strong"
            elif gap <= 2:
                classification = "Developing"
            else:
                classification = "Gap"
            skill = self.skills.get(skill_id, {})
            explanation = self._explanation(skill_id, skill, current, required, classification)
            findings.append({
                "skill_id": skill_id, "skill_name": title_case_skill(skill_id, self.skills), "current_level": current,
                "required_level": required, "gap": gap, "classification": classification,
                "importance": int(requirement.get("importance", 3)), "description": skill.get("description", ""),
                "prerequisites": skill.get("prerequisites", []), "estimated_hours": int(skill.get("estimated_hours", 12)),
                "explanation": explanation,
            })
        return findings

    @staticmethod
    def _explanation(skill_id: str, skill: dict, current: int, required: int, classification: str) -> str:
        if classification == "Strong":
            return f"You are at {current}/5, meeting the {required}/5 target. Keep this skill active through projects."
        if current == 0:
            return f"This is a new capability for you. Build foundations before applying {skill.get('name', skill_id)} in a portfolio project."
        return f"You are at {current}/5 and the role target is {required}/5. Focused practice can close this {required - current}-level gap."
