from utils.helpers import title_case_skill


class AssessmentAgent:
    def __init__(self, skills: dict[str, dict]):
        self.skills = skills

    def generate(self, skill_id: str, current_level: int) -> dict:
        name = title_case_skill(skill_id, self.skills)
        detail = self.skills.get(skill_id, {}).get("description", "")
        level = "foundation" if current_level <= 1 else "application" if current_level <= 3 else "advanced"
        return {
            "skill_id": skill_id, "title": f"{name} {level} check", "instructions": "Answer all three questions. Your result updates the adaptive plan, not a formal credential.",
            "questions": [
                {"id": "q1", "type": "mcq", "question": f"Which is the best first step when starting a {name} task?", "options": ["Define the goal and success criteria", "Copy an answer without reviewing it", "Skip checking the input", "Only optimize speed"], "answer": "Define the goal and success criteria", "explanation": "Clear success criteria make the work measurable and easier to improve."},
                {"id": "q2", "type": "short", "question": f"In one or two sentences, explain why {name} matters for a project you could build.", "keywords": [word.lower() for word in name.replace("-", " ").split() if len(word) > 3], "explanation": detail or "Connect the skill to a practical outcome."},
                {"id": "q3", "type": "coding", "question": f"Outline the steps you would take to validate a small {name} solution before sharing it.", "keywords": ["test", "input", "result"], "explanation": "A strong answer mentions realistic inputs, checking results, and iterating on failures."},
            ],
        }

    @staticmethod
    def evaluate(assessment: dict, answers: dict[str, str]) -> tuple[float, list[dict]]:
        details, correct = [], 0
        for question in assessment["questions"]:
            response = (answers.get(question["id"], "") or "").strip()
            if question["type"] == "mcq":
                passed = response == question["answer"]
            else:
                lowered = response.lower()
                matches = sum(keyword in lowered for keyword in question.get("keywords", []))
                passed = len(response.split()) >= 8 and (matches >= 1 if question["type"] == "short" else matches >= 2)
            correct += int(passed)
            details.append({"question": question["question"], "passed": passed, "feedback": question["explanation"]})
        return round(correct / len(assessment["questions"]) * 100, 0), details
