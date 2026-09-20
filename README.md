# 🚀 EduPath

> Your AI-powered personalized learning and career agent.

Built for **AI Agent Hackathon 2026**, conducted by **Product Space**.

EduPath turns a learner profile, resume evidence, target role, learning activity, and assessment performance into an adaptive path toward a career goal. It is deliberately designed as an agentic loop: observe → analyze → plan → recommend → evaluate → adapt.

## The problem

Learners often receive generic course lists without knowing which skills matter most, what to study first, or how to prove progress to employers. A static recommendation cannot respond when someone learns quickly or gets stuck.

## The solution

EduPath compares the learner’s 0–5 skill ratings with requirements for ten target careers. It identifies gaps, ranks them using a multi-factor priority score, creates a personalized weekly roadmap, recommends resources, generates practice and projects, and adapts after assessments and completion events.

## Highlights

- Profile onboarding for ten extensible career paths
- Resume analysis for PDF, DOCX, and TXT files; extracts structured skills, projects, education, experience, and improvement suggestions
- Career-requirement dataset and a separate skill metadata dataset
- Explainable skill-gap analysis: `gap = required level − current level`
- Priority engine that weighs importance, gap size, prerequisites, current momentum, and estimated learning time
- Personalized roadmap, practice sprints, resources, and portfolio project briefs
- SQLite persistence for profiles, skill ratings, roadmaps, activity, assessment results, completion events, and chat history
- Assessment-driven updates and repeated-low-score struggle detection
- Skill radar, gap chart, heatmap, progress metrics, learning streak, and PDF/text reports
- Context-aware EduPath AI Coach with natural-language learning commands
- One-click demo profile for a reliable hackathon demonstration
- Works end-to-end in **Demo Mode** without an API key

## Architecture

```text
Profile / resume / learning activity
              ↓
Profile Agent + Resume Agent
              ↓
Career Requirement + Skill Gap Agent
              ↓
Priority Agent → Roadmap Agent → Resource / Practice / Project Agents
              ↓
Assessment + Progress + Struggle Detection
              ↓
Adaptive roadmap + EduPath AI Coach
```

The `agents/` package keeps responsibilities isolated. `services/` owns SQLite, document parsing, resource matching, and the optional LLM abstraction. Reference content is kept in `data/*.json`, making careers, skills, resources, and projects easy to extend without changing application code.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

The app creates `database/edupath.db` automatically on first launch.

## Optional AI provider

EduPath is fully functional with no external AI configuration. In Demo Mode, deterministic local agents calculate gaps, create plans, recommend resources, generate tasks, evaluate short assessments, and provide contextual coaching.

To enable enhanced answers through OpenAI, copy `.env.example` to `.env` and add your key:

```env
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4o-mini
```

You can alternatively place `OPENAI_API_KEY` in Streamlit secrets. API keys are never committed because `.env` and `secrets.toml` are ignored by Git.

## Demo workflow

1. Launch the app and click **🚀 Load Demo Profile** in the sidebar.
2. On **Overview**, show the smart daily plan, skill coverage, radar chart, and priority cards.
3. Open **Skill Gap** and explain why a prerequisite is prioritized.
4. Open **Learning Roadmap**, **Resources**, and **Practice** to show concrete next actions.
5. Take an assessment. A score of 80% or above increases the tracked skill estimate; repeated scores below 60% create an adaptive support signal.
6. Use **EduPath AI Coach** with “What should I learn today?” or “Give me a practice problem.”
7. Download a progress report from **Reports**.

## Data model

SQLite tables include `users`, `skills`, `user_skills`, `careers`, `career_skills`, `resources`, `roadmaps`, `roadmap_items`, `assessments`, `assessment_results`, `projects`, `progress`, and `chat_history`. The repository class can be replaced with a PostgreSQL implementation later without changing the agents.

## Skill and roadmap logic

Every target-career skill has a required level from 0–5. EduPath classifies each result as:

- **Strong** — current level meets the target
- **Developing** — 1–2 levels below target
- **Gap** — 3+ levels below target

The priority score adds role importance, proportion of the gap, prerequisite leverage, current learner level, and a bounded time-to-progress factor. This pushes foundational, high-value skills forward rather than simply sorting the largest gaps. The roadmap uses the learner’s available weekly hours and recomputes its status when skills are completed or the struggle detector finds three low recent assessment scores.

## Project layout

```text
app.py                  Streamlit interface and page routing
agents/                 Focused reasoning agents
components/             Reusable dashboard, chart, card, sidebar, and roadmap views
data/                   Extensible careers, skills, resources, and project datasets
services/               SQLite, resume parsing, recommendations, and optional LLM adapter
utils/                  Constants and safe helper functions
database/edupath.db     Created locally at runtime (ignored by Git)
```

## Screenshots

Add dashboard and roadmap screenshots here before submitting the hackathon project.

## Future improvements

- Authenticated multi-user accounts and PostgreSQL storage
- Richer resume parsing with explicit user review before profile updates
- More domain-specific assessment banks and evaluator rubrics
- Calendar integrations and scheduled check-ins
- Curated role requirements reviewed by industry practitioners

## Notes

Career skill coverage is a planning signal, not a guarantee of employment, internship readiness, or assessment competence. Always review AI-generated suggestions before using them in a real application or portfolio.
