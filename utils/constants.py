from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
DATABASE_DIR = ROOT_DIR / "database"
DATABASE_PATH = DATABASE_DIR / "edupath.db"

NAV_ITEMS = [
    "Overview", "My Profile", "Resume Analysis", "Skill Gap", "Learning Roadmap",
    "Resources", "Practice", "Projects", "Assessment", "Progress", "AI Coach", "Reports",
]

DEMO_PROFILE = {
    "name": "Sunny",
    "education": "B.Tech CSE",
    "experience_level": "Beginner",
    "target_career": "machine_learning_engineer",
    "career_goal": "Build a portfolio and prepare for a machine learning internship.",
    "weekly_hours": 15,
    "learning_style": "Hands-on projects",
    "skills": {
        "python": 3, "statistics": 1, "machine_learning": 1, "sql": 2,
        "pandas": 2, "numpy": 1, "scikit_learn": 0, "deep_learning": 0,
        "git": 2, "deployment": 0,
    },
}

LEVEL_LABELS = {0: "New", 1: "Aware", 2: "Beginner", 3: "Working", 4: "Confident", 5: "Advanced"}
