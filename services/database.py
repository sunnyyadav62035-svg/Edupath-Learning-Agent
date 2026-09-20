import json
import sqlite3
from contextlib import contextmanager
from datetime import date
from pathlib import Path
from typing import Any, Iterator


class EduPathDatabase:
    """Small SQLite repository. It intentionally has no Streamlit dependency."""

    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def initialize(self) -> None:
        schema = """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY, name TEXT NOT NULL, education TEXT, experience_level TEXT,
            target_career TEXT, career_goal TEXT, weekly_hours INTEGER, learning_style TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS skills (
            id TEXT PRIMARY KEY, name TEXT, category TEXT, description TEXT
        );
        CREATE TABLE IF NOT EXISTS user_skills (
            user_id INTEGER, skill_id TEXT, level INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (user_id, skill_id), FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY(skill_id) REFERENCES skills(id)
        );
        CREATE TABLE IF NOT EXISTS careers (id TEXT PRIMARY KEY, name TEXT, description TEXT);
        CREATE TABLE IF NOT EXISTS career_skills (
            career_id TEXT, skill_id TEXT, required_level INTEGER, importance INTEGER,
            PRIMARY KEY (career_id, skill_id), FOREIGN KEY(career_id) REFERENCES careers(id),
            FOREIGN KEY(skill_id) REFERENCES skills(id)
        );
        CREATE TABLE IF NOT EXISTS resources (
            id TEXT PRIMARY KEY, title TEXT, skill_id TEXT, url TEXT, payload TEXT
        );
        CREATE TABLE IF NOT EXISTS roadmaps (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, payload TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS roadmap_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT, roadmap_id INTEGER, skill_id TEXT, week INTEGER,
            status TEXT DEFAULT 'planned', FOREIGN KEY(roadmap_id) REFERENCES roadmaps(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT, skill_id TEXT, payload TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS assessment_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, skill_id TEXT, score REAL,
            answers TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS projects (
            id TEXT PRIMARY KEY, title TEXT, payload TEXT
        );
        CREATE TABLE IF NOT EXISTS progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, skill_id TEXT, event_type TEXT,
            item_id TEXT, minutes INTEGER DEFAULT 0, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, role TEXT, content TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        """
        with self.connection() as conn:
            conn.executescript(schema)

    def seed_reference_data(self, skills: dict, careers: dict, resources: list, projects: list) -> None:
        with self.connection() as conn:
            for skill_id, skill in skills.items():
                conn.execute("INSERT OR REPLACE INTO skills VALUES (?, ?, ?, ?)", (
                    skill_id, skill.get("name"), skill.get("category"), skill.get("description")))
            for career_id, career in careers.items():
                conn.execute("INSERT OR REPLACE INTO careers VALUES (?, ?, ?)", (
                    career_id, career.get("name"), career.get("description")))
                for skill_id, requirement in career.get("skills", {}).items():
                    conn.execute("INSERT OR REPLACE INTO career_skills VALUES (?, ?, ?, ?)", (
                        career_id, skill_id, requirement.get("required_level", 0), requirement.get("importance", 1)))
            for resource in resources:
                conn.execute("INSERT OR REPLACE INTO resources VALUES (?, ?, ?, ?, ?)", (
                    resource.get("id"), resource.get("title"), resource.get("skill"), resource.get("url"), json.dumps(resource)))
            for project in projects:
                conn.execute("INSERT OR REPLACE INTO projects VALUES (?, ?, ?)", (
                    project.get("id"), project.get("title"), json.dumps(project)))

    def get_profile(self, user_id: int = 1) -> dict[str, Any] | None:
        with self.connection() as conn:
            row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
            if not row:
                return None
            profile = dict(row)
            profile["skills"] = {item["skill_id"]: item["level"] for item in conn.execute(
                "SELECT skill_id, level FROM user_skills WHERE user_id = ?", (user_id,)
            )}
            return profile

    def save_profile(self, profile: dict[str, Any], user_id: int = 1) -> dict[str, Any]:
        fields = (profile.get("name") or "Learner", profile.get("education", ""), profile.get("experience_level", "Beginner"),
                  profile.get("target_career", ""), profile.get("career_goal", ""), int(profile.get("weekly_hours", 5)),
                  profile.get("learning_style", "Hands-on projects"))
        with self.connection() as conn:
            conn.execute("""INSERT INTO users (id, name, education, experience_level, target_career, career_goal, weekly_hours, learning_style)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            ON CONFLICT(id) DO UPDATE SET name=excluded.name, education=excluded.education,
                            experience_level=excluded.experience_level, target_career=excluded.target_career,
                            career_goal=excluded.career_goal, weekly_hours=excluded.weekly_hours,
                            learning_style=excluded.learning_style, updated_at=CURRENT_TIMESTAMP""", (user_id, *fields))
            conn.execute("DELETE FROM user_skills WHERE user_id = ?", (user_id,))
            for skill_id, level in profile.get("skills", {}).items():
                conn.execute("INSERT OR REPLACE INTO user_skills VALUES (?, ?, ?)", (user_id, skill_id, max(0, min(5, int(level)))))
        return self.get_profile(user_id) or profile

    def update_skill(self, skill_id: str, level: int, user_id: int = 1) -> None:
        with self.connection() as conn:
            conn.execute(
                """INSERT INTO user_skills (user_id, skill_id, level) VALUES (?, ?, ?)
                   ON CONFLICT(user_id, skill_id) DO UPDATE SET level = excluded.level""",
                (user_id, skill_id, max(0, min(5, level))),
            )

    def save_roadmap(self, roadmap: list[dict], user_id: int = 1) -> None:
        with self.connection() as conn:
            cursor = conn.execute("INSERT INTO roadmaps (user_id, payload) VALUES (?, ?)", (user_id, json.dumps(roadmap)))
            roadmap_id = cursor.lastrowid
            for week in roadmap:
                for item in week.get("items", []):
                    conn.execute("INSERT INTO roadmap_items (roadmap_id, skill_id, week, status) VALUES (?, ?, ?, ?)",
                                 (roadmap_id, item.get("skill_id"), week.get("week"), item.get("status", "planned")))

    def latest_roadmap(self, user_id: int = 1) -> list[dict]:
        with self.connection() as conn:
            row = conn.execute("SELECT payload FROM roadmaps WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id,)).fetchone()
        try:
            return json.loads(row["payload"]) if row else []
        except (KeyError, json.JSONDecodeError):
            return []

    def record_progress(self, event_type: str, item_id: str, skill_id: str | None = None, minutes: int = 0, user_id: int = 1) -> None:
        with self.connection() as conn:
            conn.execute("INSERT INTO progress (user_id, skill_id, event_type, item_id, minutes) VALUES (?, ?, ?, ?, ?)",
                         (user_id, skill_id, event_type, item_id, max(0, int(minutes))))

    def completed_ids(self, event_type: str, user_id: int = 1) -> set[str]:
        with self.connection() as conn:
            rows = conn.execute("SELECT item_id FROM progress WHERE user_id = ? AND event_type = ?", (user_id, event_type)).fetchall()
        return {row["item_id"] for row in rows}

    def record_assessment(self, skill_id: str, score: float, answers: dict, user_id: int = 1) -> None:
        with self.connection() as conn:
            conn.execute("INSERT INTO assessment_results (user_id, skill_id, score, answers) VALUES (?, ?, ?, ?)",
                         (user_id, skill_id, score, json.dumps(answers)))

    def assessment_history(self, skill_id: str | None = None, user_id: int = 1) -> list[dict]:
        query = "SELECT * FROM assessment_results WHERE user_id = ?"
        params: tuple[Any, ...] = (user_id,)
        if skill_id:
            query += " AND skill_id = ?"
            params += (skill_id,)
        query += " ORDER BY id DESC"
        with self.connection() as conn:
            return [dict(row) for row in conn.execute(query, params).fetchall()]

    def record_chat(self, role: str, content: str, user_id: int = 1) -> None:
        with self.connection() as conn:
            conn.execute("INSERT INTO chat_history (user_id, role, content) VALUES (?, ?, ?)", (user_id, role, content))

    def get_chat_history(self, user_id: int = 1, limit: int = 20) -> list[dict]:
        with self.connection() as conn:
            rows = conn.execute("SELECT role, content, created_at FROM chat_history WHERE user_id = ? ORDER BY id DESC LIMIT ?", (user_id, limit)).fetchall()
        return [dict(row) for row in reversed(rows)]

    def progress_summary(self, user_id: int = 1) -> dict[str, Any]:
        with self.connection() as conn:
            rows = conn.execute("SELECT event_type, COUNT(*) AS count, COALESCE(SUM(minutes), 0) AS minutes FROM progress WHERE user_id = ? GROUP BY event_type", (user_id,)).fetchall()
            days = conn.execute("SELECT DISTINCT DATE(created_at) AS day FROM progress WHERE user_id = ? ORDER BY day DESC", (user_id,)).fetchall()
        return {"events": {row["event_type"]: {"count": row["count"], "minutes": row["minutes"]} for row in rows}, "active_days": [row["day"] for row in days]}

    def learning_streak(self, user_id: int = 1) -> int:
        dates = set(self.progress_summary(user_id)["active_days"])
        streak, current = 0, date.today()
        while current.isoformat() in dates:
            streak += 1
            current = current.fromordinal(current.toordinal() - 1)
        return streak
