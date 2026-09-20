from services.recommendation_engine import RecommendationEngine


class ResourceAgent:
    def __init__(self, resources: list[dict], skills: dict[str, dict]):
        self.engine = RecommendationEngine(resources, skills)

    def recommend(self, prioritized_gaps: list[dict], completed_resources: set[str]) -> dict[str, list[dict]]:
        return self.engine.for_priorities([gap for gap in prioritized_gaps if gap["gap"] > 0], completed_resources)
