from copy import deepcopy

from utils.constants import DEMO_PROFILE
from utils.helpers import clamp_level


class ProfileAgent:
    def demo_profile(self) -> dict:
        return deepcopy(DEMO_PROFILE)

    def normalize(self, profile: dict, valid_skills: set[str], valid_careers: set[str]) -> dict:
        clean = dict(profile)
        clean["name"] = (clean.get("name") or "Learner").strip()[:80]
        clean["weekly_hours"] = max(1, min(60, int(clean.get("weekly_hours", 5))))
        if clean.get("target_career") not in valid_careers:
            clean["target_career"] = next(iter(valid_careers), "")
        clean["skills"] = {
            skill_id: clamp_level(level) for skill_id, level in clean.get("skills", {}).items() if skill_id in valid_skills
        }
        return clean

    def merge_resume_skills(self, profile: dict, detected_skills: list[str]) -> dict:
        updated = deepcopy(profile)
        current_skills = updated.setdefault("skills", {})
        for skill_id in detected_skills:
            current_skills[skill_id] = max(current_skills.get(skill_id, 0), 1)
        return updated
