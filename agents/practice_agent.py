class PracticeAgent:
    def __init__(self, skills: dict[str, dict]):
        self.skills = skills

    def generate(self, skill_id: str, level: int) -> dict:
        skill = self.skills.get(skill_id, {"name": skill_id.replace("_", " ").title(), "practice_tasks": []})
        name = skill["name"]
        if level <= 1:
            difficulty, objective = "Beginner", f"Build confidence with one core {name} concept."
            instructions = ["Read a short beginner resource for 15 minutes.", f"Complete: {skill.get('practice_tasks', ['a guided exercise'])[0]}.", "Write down one concept you can now explain."]
            expected = "A small, working solution plus a three-sentence reflection."
        elif level <= 3:
            difficulty, objective = "Intermediate", f"Apply {name} to a realistic, bounded problem."
            instructions = ["Choose a small public or sample dataset/problem.", f"Complete: {skill.get('practice_tasks', ['a practical task'])[-1]}.", "Add error handling or validation and explain your decisions."]
            expected = "A reproducible notebook, script, or short project with documented results."
        else:
            difficulty, objective = "Advanced", f"Design a reusable workflow that demonstrates mature {name} judgment."
            instructions = ["Define success criteria before implementation.", "Build a reusable, tested solution.", "Compare an alternative approach and document trade-offs."]
            expected = "A polished portfolio-quality repository with tests or evaluation evidence."
        return {
            "id": f"practice-{skill_id}-{level}", "title": f"{name} practice sprint", "skill_id": skill_id,
            "objective": objective, "difficulty": difficulty, "instructions": instructions, "expected_output": expected,
            "skills_practiced": [name], "hint": "Work in a 25-minute focus block, then explain one decision aloud before continuing.",
        }
