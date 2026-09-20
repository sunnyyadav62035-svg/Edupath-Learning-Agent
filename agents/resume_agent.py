"""Deterministic, section-aware resume analysis for the offline demo mode."""
from __future__ import annotations

import re
from collections import defaultdict


class ResumeAgent:
    """Convert resume text into reviewable learner-profile evidence."""

    SECTION_ALIASES = {
        "summary": {"summary", "professional summary", "profile", "professional profile", "career summary", "objective", "career objective", "about me"},
        "skills": {"skills", "technical skills", "core skills", "core competencies", "technical competencies", "tools", "technologies", "tech stack", "areas of expertise", "competencies"},
        "experience": {"experience", "work experience", "professional experience", "employment history", "work history", "career history", "internship", "internships", "internship experience"},
        "projects": {"projects", "project experience", "personal projects", "academic projects", "selected projects", "key projects", "portfolio", "portfolio projects"},
        "education": {"education", "academic background", "academics", "qualifications", "academic qualifications"},
        "certifications": {"certifications", "certificates", "certification", "credentials", "licenses and certifications"},
    }

    SKILL_ALIASES = {
        "python": {"python", "python 3", "python3", "jupyter notebook"},
        "statistics": {"statistics", "statistical analysis", "hypothesis testing", "probability", "a/b testing", "ab testing", "data analysis"},
        "machine_learning": {"machine learning", "predictive modeling", "predictive modelling", "supervised learning", "unsupervised learning", "model training"},
        "sql": {"sql", "mysql", "postgresql", "postgres", "sqlite", "mssql", "microsoft sql server", "snowflake", "bigquery"},
        "pandas": {"pandas", "dataframe", "dataframes"}, "numpy": {"numpy"},
        "scikit_learn": {"scikit-learn", "scikit learn", "sklearn"},
        "deep_learning": {"deep learning", "neural network", "neural networks", "tensorflow", "pytorch", "keras"},
        "git": {"git", "github", "gitlab", "version control"},
        "deployment": {"deployment", "deploy", "deployed", "ci/cd", "cicd", "continuous integration", "continuous delivery", "streamlit", "heroku", "render.com"},
        "data_visualization": {"data visualization", "data visualisation", "visualization", "visualisation", "tableau", "power bi", "matplotlib", "seaborn", "plotly", "dashboard"},
        "excel": {"excel", "microsoft excel", "pivot table", "pivot tables", "vlookup", "xlookup"},
        "communication": {"communication", "stakeholder management", "stakeholder communication", "presentation", "presentations", "report writing"},
        "llm": {"llm", "llms", "large language model", "large language models", "generative ai", "genai", "gpt", "openai", "langchain", "rag", "retrieval augmented generation", "transformers"},
        "api_development": {"api development", "rest api", "restful api", "fastapi", "flask", "django", "graphql", "web api"},
        "data_structures": {"data structures", "linked list", "linked lists", "hash map", "hash maps", "binary tree", "binary trees", "stack", "queue"},
        "algorithms": {"algorithms", "algorithmic", "time complexity", "dynamic programming", "sorting algorithm"},
        "testing": {"testing", "unit test", "unit tests", "pytest", "test automation", "integration test", "integration tests", "tdd"},
        "databases": {"database", "databases", "database design", "relational database", "mongodb", "redis"},
        "etl": {"etl", "data pipeline", "data pipelines", "apache airflow", "airflow", "dbt", "apache spark", "pyspark", "data ingestion"},
        "cloud": {"cloud", "aws", "amazon web services", "azure", "google cloud", "gcp", "cloud computing"},
        "docker": {"docker", "containerization", "containerisation", "docker compose"},
        "data_modeling": {"data modeling", "data modelling", "dimensional modeling", "dimensional modelling", "star schema", "data warehouse"},
        "linux": {"linux", "unix", "bash", "shell scripting", "command line"},
        "networking": {"networking", "tcp/ip", "dns", "http", "network security", "subnet"},
        "kubernetes": {"kubernetes", "k8s", "helm"}, "terraform": {"terraform", "infrastructure as code", "iac"},
        "cybersecurity": {"cybersecurity", "cyber security", "information security", "vulnerability assessment", "penetration testing", "owasp"},
        "security_tools": {"siem", "splunk", "wireshark", "burp suite", "nessus", "security monitoring", "incident response"},
        "html_css": {"html", "css", "html5", "css3", "responsive design", "bootstrap", "tailwind"},
        "javascript": {"javascript", "typescript", "node.js", "nodejs", "ecmascript"},
        "react": {"react", "reactjs", "react.js", "next.js", "nextjs"},
        "prompt_engineering": {"prompt engineering", "prompt design", "prompt optimization", "prompt optimisation", "few-shot prompting"},
        "vector_databases": {"vector database", "vector databases", "vector store", "vector stores", "pinecone", "chromadb", "weaviate", "faiss", "semantic search"},
    }

    ROLE_WORDS = re.compile(r"\b(engineer|developer|analyst|scientist|intern|consultant|manager|researcher|associate|student|trainee)\b", re.I)
    DEGREE_WORDS = re.compile(r"\b(b\.?tech|b\.?e\.?|bachelor|master|m\.?tech|m\.?sc|b\.?sc|ph\.?d|diploma|university|college)\b", re.I)
    DATE_WORDS = re.compile(r"\b(?:19|20)\d{2}\b|\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?\s+(?:19|20)\d{2}", re.I)
    CERT_WORDS = re.compile(r"\b(certified|certification|certificate|credential|coursera|udemy|nptel|aws|microsoft|google)\b", re.I)

    def __init__(self, skills: dict[str, dict]):
        self.skills = skills

    def analyze(self, text: str) -> dict:
        lines = self._clean_lines(text)
        cleaned_text = "\n".join(lines)
        sections = self._extract_sections(lines)
        evidence = self._detect_skills(cleaned_text, sections)
        detected = list(evidence)
        projects = self._section_entries(sections["projects"], limit=5) or self._fallback_projects(lines)
        experience = self._section_entries(sections["experience"], limit=5) or self._fallback_experience(lines)
        certifications = self._section_entries(sections["certifications"], limit=5) or self._fallback_certifications(lines)
        education = self._section_entries(sections["education"], limit=4) or self._fallback_education(lines)
        missing = self._missing_information(sections, projects, experience, education, cleaned_text)
        improvements = self._improvements(detected, sections, projects, experience)
        return {
            "detected_skills": detected,
            "detected_skill_details": [{"skill_id": skill_id, "skill_name": self.skills[skill_id]["name"], **evidence[skill_id]} for skill_id in detected],
            "detected_projects": projects, "detected_experience": experience,
            "detected_certifications": certifications, "detected_education": education,
            "relevant_keywords": [self.skills[item]["name"] for item in detected],
            "missing_information": missing, "suggested_improvements": improvements,
            "sections_found": [name.title() for name, values in sections.items() if values],
            "document_stats": {"lines": len(lines), "characters": len(cleaned_text), "words": len(cleaned_text.split())},
            "extracted_preview": "\n".join(lines[:80]),
        }

    def _detect_skills(self, text: str, sections: dict[str, list[str]]) -> dict[str, dict]:
        normal_text = text.lower()
        skill_section = "\n".join(sections["skills"]).lower()
        project_section = "\n".join(sections["projects"]).lower()
        results: dict[str, dict] = {}
        for skill_id, skill in self.skills.items():
            aliases = set(self.SKILL_ALIASES.get(skill_id, set()))
            aliases.update({skill_id.replace("_", " ").lower(), skill.get("name", "").lower()})
            matches = sorted({alias for alias in aliases if alias and self._contains_phrase(normal_text, alias)}, key=lambda alias: (-len(alias), alias))
            if not matches:
                continue
            in_skills = [alias for alias in matches if self._contains_phrase(skill_section, alias)]
            in_projects = [alias for alias in matches if self._contains_phrase(project_section, alias)]
            location = "skills section" if in_skills else "projects section" if in_projects else "resume text"
            results[skill_id] = {
                "matched_terms": matches[:4],
                "evidence": f"Found {', '.join(matches[:3])} in the {location}.",
                "confidence": "High" if in_skills or len(matches) >= 2 else "Medium",
            }
        return results

    @staticmethod
    def _contains_phrase(text: str, phrase: str) -> bool:
        return bool(re.search(r"(?<!\w)" + re.escape(phrase.lower()) + r"(?!\w)", text.lower()))

    def _extract_sections(self, lines: list[str]) -> dict[str, list[str]]:
        sections: dict[str, list[str]] = defaultdict(list)
        active: str | None = None
        for line in lines:
            heading, remainder = self._identify_heading(line)
            if heading:
                active = heading
                if remainder:
                    sections[active].append(remainder)
                continue
            if active:
                sections[active].append(line)
        return {name: sections[name] for name in self.SECTION_ALIASES}

    def _identify_heading(self, line: str) -> tuple[str | None, str]:
        raw = line.strip()
        if not raw or len(raw) > 70:
            return None, ""
        separator = ":" if ":" in raw else "|" if "|" in raw else ""
        possible_heading, remainder = raw.split(separator, 1) if separator else (raw, "")
        normalized = self._normalize_heading(possible_heading if separator else raw)
        for section, aliases in self.SECTION_ALIASES.items():
            if normalized in aliases:
                return section, remainder.strip(" -–—•\t") if separator else ""
        return None, ""

    @staticmethod
    def _normalize_heading(value: str) -> str:
        return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9+/#& ]", " ", value.lower())).strip()

    @staticmethod
    def _clean_lines(text: str) -> list[str]:
        text = text.replace("\x00", "").replace("\u00a0", " ").replace("\r", "\n")
        lines = []
        for line in text.split("\n"):
            line = re.sub(r"\s+", " ", line).strip()
            if not line or re.fullmatch(r"page\s*\d+(?:\s*of\s*\d+)?", line, flags=re.I):
                continue
            if not lines or lines[-1] != line:
                lines.append(line)
        return lines

    @staticmethod
    def _section_entries(lines: list[str], limit: int) -> list[str]:
        entries = []
        for line in lines:
            line = line.strip("•·-–— \t")
            if len(line) < 3 or ResumeAgent._normalize_heading(line) in {"skills", "experience", "projects", "education", "certifications"}:
                continue
            if line not in entries:
                entries.append(line)
            if len(entries) >= limit:
                break
        return entries

    def _fallback_projects(self, lines: list[str]) -> list[str]:
        return self._section_entries([line for line in lines if re.search(r"\b(project|application|dashboard|predictor|classifier|website|system)\b", line, re.I)], 5)

    def _fallback_experience(self, lines: list[str]) -> list[str]:
        return self._section_entries([line for line in lines if self.ROLE_WORDS.search(line) and (self.DATE_WORDS.search(line) or len(line) <= 130)], 5)

    def _fallback_certifications(self, lines: list[str]) -> list[str]:
        return self._section_entries([line for line in lines if self.CERT_WORDS.search(line)], 5)

    def _fallback_education(self, lines: list[str]) -> list[str]:
        return self._section_entries([line for line in lines if self.DEGREE_WORDS.search(line)], 4)

    @staticmethod
    def _missing_information(sections: dict[str, list[str]], projects: list[str], experience: list[str], education: list[str], text: str) -> list[str]:
        missing = []
        if not sections["summary"]:
            missing.append("Add a 2–3 line professional summary tailored to the role you want.")
        if not projects:
            missing.append("Add 1–2 outcome-focused project entries with links to code or demos.")
        if not experience:
            missing.append("Add relevant internship, volunteer, freelance, or academic experience with dates.")
        if not education:
            missing.append("Add your degree, institution, and expected or graduation year.")
        if not re.search(r"https?://|github\.com|linkedin\.com", text, re.I):
            missing.append("Include a GitHub, portfolio, or LinkedIn link.")
        if not re.search(r"\d+\s*%|\d+\s*(?:hours|users|records|models|projects|features|days)", text, re.I):
            missing.append("Quantify results where possible (for example, time saved, accuracy, or records analyzed).")
        return missing

    @staticmethod
    def _improvements(detected: list[str], sections: dict[str, list[str]], projects: list[str], experience: list[str]) -> list[str]:
        improvements = []
        if experience:
            improvements.append("Lead each experience bullet with an action verb, the tool used, and a measurable result.")
        if projects:
            improvements.append("For each project, state the problem, your contribution, technologies, and outcome in one clear bullet.")
        if detected and not sections["skills"]:
            improvements.append("Create a concise Technical Skills section so recruiters can scan your strengths quickly.")
        if not detected:
            improvements.append("Name the tools and technologies you used explicitly; the analyzer found few role-related technical terms.")
        improvements.append("Review the detected skills below before adding them to your learning profile; only keep skills you can discuss in an interview.")
        return improvements
