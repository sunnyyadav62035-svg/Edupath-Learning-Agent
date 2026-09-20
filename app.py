"""EduPath — adaptive learning and skill-gap agent for Streamlit."""
from __future__ import annotations

import os
from io import BytesIO

import streamlit as st
from dotenv import load_dotenv

from agents import (
    AssessmentAgent, CoachAgent, PriorityAgent, PracticeAgent, ProfileAgent, ProgressAgent,
    ProjectAgent, ResourceAgent, ResumeAgent, RoadmapAgent, SkillGapAgent,
)
from components.charts import gap_bar, skill_radar
from components.dashboard import render_overview
from components.roadmap import render_roadmap
from components.sidebar import render_sidebar
from components.skill_cards import render_skill_cards
from services.ai_service import AIService
from services.database import EduPathDatabase
from services.resume_parser import ResumeParser
from utils.constants import DATA_DIR, DATABASE_PATH
from utils.helpers import load_json, safe_filename, title_case_skill


st.set_page_config(page_title="EduPath · AI Learning Agent", page_icon="🚀", layout="wide", initial_sidebar_state="expanded")
load_dotenv()


@st.cache_data(show_spinner=False)
def load_reference_data() -> tuple[dict, dict, list, list]:
    return (
        load_json(DATA_DIR / "careers.json", {}),
        load_json(DATA_DIR / "skills.json", {}),
        load_json(DATA_DIR / "resources.json", []),
        load_json(DATA_DIR / "projects.json", []),
    )


@st.cache_resource(show_spinner=False)
def get_database() -> EduPathDatabase:
    return EduPathDatabase(DATABASE_PATH)


def get_api_key() -> str | None:
    try:
        return st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
    except Exception:
        return os.getenv("OPENAI_API_KEY")


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        :root { --edupath-indigo: #4f46e5; --edupath-violet: #7c3aed; --edupath-sky: #0ea5e9; }
        [data-testid="stAppViewContainer"] {
            background:
                radial-gradient(circle at 8% 5%, rgba(99, 102, 241, .19), transparent 27rem),
                radial-gradient(circle at 92% 18%, rgba(14, 165, 233, .15), transparent 26rem),
                radial-gradient(circle at 55% 100%, rgba(167, 139, 250, .13), transparent 31rem),
                linear-gradient(135deg, #f8faff 0%, #f2f5ff 44%, #f8fbff 100%);
        }
        [data-testid="stHeader"] { background: rgba(248, 250, 255, .55); backdrop-filter: blur(14px); }
        [data-testid="stSidebar"] > div:first-child {
            background:
                radial-gradient(circle at 12% 3%, rgba(129, 140, 248, .22), transparent 18rem),
                linear-gradient(180deg, #111a3e 0%, #172554 47%, #101b43 100%);
            border-right: 1px solid rgba(165, 180, 252, .22);
        }
        [data-testid="stSidebar"] * { color: #edf2ff; }
        [data-testid="stSidebar"] [data-testid="stCaptionContainer"] p { color: #c7d2fe; }
        [data-testid="stSidebar"] .stAlert { background: rgba(255,255,255,.10); border: 1px solid rgba(199,210,254,.22); }
        [data-testid="stSidebar"] .stButton > button { background: rgba(255,255,255,.12); color: #ffffff; border: 1px solid rgba(224,231,255,.38); }
        [data-testid="stSidebar"] .stButton > button:hover { background: rgba(129,140,248,.38); border-color: #c7d2fe; }
        [data-testid="stSidebar"] [role="radiogroup"] label { border-radius: 9px; padding: 5px 8px; transition: background .18s ease; }
        [data-testid="stSidebar"] [role="radiogroup"] label:hover { background: rgba(255,255,255,.09); }
        .block-container { max-width: 1440px; padding-top: 2rem; padding-bottom: 3rem; }
        h1, h2, h3 { letter-spacing: -0.025em; color: #172554; }
        h1 { text-shadow: 0 8px 30px rgba(79, 70, 229, .12); }
        .stMetric { background: rgba(255,255,255,.82); border: 1px solid rgba(199, 210, 254, .72); border-radius: 16px; padding: 12px 14px; box-shadow: 0 12px 30px rgba(30, 41, 99, .08); backdrop-filter: blur(12px); }
        .skill-card { display:flex; justify-content:space-between; gap:20px; padding:14px 16px; margin:9px 0;
                      border:1px solid rgba(199, 210, 254, .78); border-left:4px solid #6366f1; border-radius:14px; background:rgba(255,255,255,.84); box-shadow:0 9px 22px rgba(30,41,99,.06); backdrop-filter:blur(10px); }
        .skill-card strong { font-size:1.02rem; } .subtle { color:#64748b; font-size:.87rem; }
        .skill-levels { display:flex; flex-wrap:wrap; align-items:center; gap:9px; justify-content:flex-end; font-size:.83rem; color:#475569; }
        .skill-levels span { padding:4px 8px; background:#eef2ff; border-radius:999px; }
        .daily-item { position:relative; padding:12px 16px; margin:9px 0; border:1px solid rgba(196,181,253,.68); border-radius:13px; background:linear-gradient(100deg,rgba(237,233,254,.92),rgba(255,255,255,.85)); box-shadow:0 8px 22px rgba(76,29,149,.05); }
        .daily-item span { float:right; color:#4f46e5; font-weight:700; } .daily-item small { color:#64748b; }
        .resource-card { padding:14px; border:1px solid rgba(199,210,254,.78); border-radius:14px; min-height:168px; background:rgba(255,255,255,.86); box-shadow:0 9px 22px rgba(30,41,99,.06); }
        .status-chip { display:inline-block; padding:3px 8px; border-radius:999px; font-size:.78rem; font-weight:600; background:linear-gradient(90deg,#eef2ff,#f5f3ff); color:#4338ca; }
        .stButton > button[kind="primary"] { border: 0; background: linear-gradient(100deg, var(--edupath-indigo), var(--edupath-violet)); box-shadow: 0 8px 18px rgba(79,70,229,.25); }
        .stButton > button[kind="primary"]:hover { background: linear-gradient(100deg, #4338ca, #6d28d9); transform: translateY(-1px); }
        [data-testid="stExpander"] { background: rgba(255,255,255,.76); border: 1px solid rgba(199,210,254,.66); border-radius: 13px; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def build_state(profile: dict, careers: dict, skills: dict, resources: list, projects: list, db: EduPathDatabase) -> dict:
    career = careers.get(profile.get("target_career")) or next(iter(careers.values()), {"name": "Target role", "skills": {}})
    gap_agent = SkillGapAgent(skills)
    priority_agent = PriorityAgent(skills)
    progress_agent = ProgressAgent()
    gaps = gap_agent.analyze(profile, career)
    prioritized = priority_agent.prioritize(gaps)
    history = db.assessment_history()
    struggles = progress_agent.detect_struggles(history, skills)
    completed_skills = {item["skill_id"] for item in gaps if item["gap"] == 0}
    roadmap_agent = RoadmapAgent(skills)
    roadmap = db.latest_roadmap() or roadmap_agent.build(prioritized, profile.get("weekly_hours", 5))
    roadmap = roadmap_agent.adapt(roadmap, {item["skill_id"] for item in struggles}, completed_skills)
    event_summary = db.progress_summary()
    summary = progress_agent.summary(gaps, profile, event_summary, history)
    daily_plan = progress_agent.daily_plan(prioritized, profile.get("weekly_hours", 5))
    recommendations = ResourceAgent(resources, skills).recommend(prioritized, db.completed_ids("resource"))
    projects_for_user = ProjectAgent(projects).recommend(
        profile.get("target_career", ""), {item["skill_id"] for item in gaps if item["gap"] > 0}, db.completed_ids("project")
    )
    return {
        "career": career, "gaps": gaps, "prioritized": prioritized, "history": history,
        "struggles": struggles, "roadmap": roadmap, "summary": summary, "daily_plan": daily_plan,
        "recommendations": recommendations, "projects": projects_for_user,
    }


def make_report_pdf(report: str) -> bytes | None:
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=A4)
        text = pdf.beginText(44, 800)
        text.setFont("Helvetica", 10)
        for paragraph in report.split("\n"):
            if not paragraph:
                text.textLine("")
                continue
            words, line = paragraph.split(), ""
            for word in words:
                candidate = f"{line} {word}".strip()
                if len(candidate) > 95:
                    text.textLine(line)
                    line = word
                else:
                    line = candidate
            text.textLine(line)
        pdf.drawText(text)
        pdf.save()
        return buffer.getvalue()
    except Exception:
        return None


def show_profile_page(profile: dict | None, careers: dict, skills: dict, db: EduPathDatabase) -> None:
    st.title("Build your learning profile")
    st.caption("Your skill ratings create the first roadmap. You can refine them later with assessments and completed work.")
    existing = profile or {"name": "", "education": "", "experience_level": "Beginner", "target_career": next(iter(careers), ""), "career_goal": "", "weekly_hours": 6, "learning_style": "Hands-on projects", "skills": {}}
    career_ids = list(careers)
    current_career = existing.get("target_career") if existing.get("target_career") in careers else career_ids[0]
    experience_options = ["Beginner", "Student", "Early career", "Professional", "Career switcher"]
    style_options = ["Hands-on projects", "Visual lessons", "Reading and notes", "Guided courses", "Practice problems"]
    if "profile_draft_career" not in st.session_state or st.session_state["profile_draft_career"] not in careers:
        st.session_state["profile_draft_career"] = current_career
    st.markdown("#### Choose your target career")
    selected_career = st.selectbox(
        "Target career",
        career_ids,
        format_func=lambda item: careers[item]["name"],
        key="profile_draft_career",
    )
    st.caption("Changing this selection immediately refreshes the skill ratings below. Your profile is saved only when you create the roadmap.")
    with st.form("profile_form", clear_on_submit=False):
        left, right = st.columns(2)
        with left:
            name = st.text_input("Name", value=existing.get("name", ""), max_chars=80)
            education = st.text_input("Education", value=existing.get("education", ""), placeholder="e.g. B.Tech CSE")
            old_experience = existing.get("experience_level", "Beginner")
            experience = st.selectbox("Experience level", experience_options, index=experience_options.index(old_experience) if old_experience in experience_options else 0)
            weekly_hours = st.slider("Weekly learning hours", 1, 40, int(existing.get("weekly_hours", 6)))
        with right:
            goal = st.text_area("Career goal", value=existing.get("career_goal", ""), placeholder="What outcome are you working toward?")
            old_style = existing.get("learning_style", "Hands-on projects")
            learning_style = st.selectbox("Preferred learning style", style_options, index=style_options.index(old_style) if old_style in style_options else 0)
        st.markdown("#### Rate the role skills")
        st.caption("0 = new to me · 5 = can apply independently in a project")
        requirement_skills = careers[selected_career].get("skills", {})
        values = {}
        for skill_id, requirement in requirement_skills.items():
            values[skill_id] = st.slider(
                f"{skills.get(skill_id, {}).get('name', skill_id)} · target {requirement['required_level']}/5",
                min_value=0, max_value=5, value=int(existing.get("skills", {}).get(skill_id, 0)), key=f"profile_level_{skill_id}",
            )
        submitted = st.form_submit_button("Create my adaptive roadmap", type="primary")
    if submitted:
        candidate = {
            "name": name, "education": education, "experience_level": experience, "target_career": selected_career,
            "career_goal": goal, "weekly_hours": weekly_hours, "learning_style": learning_style, "skills": values,
        }
        clean = ProfileAgent().normalize(candidate, set(skills), set(careers))
        db.save_profile(clean)
        state = build_state(clean, careers, skills, [], [], db)
        db.save_roadmap(RoadmapAgent(skills).build(state["prioritized"], clean["weekly_hours"]))
        st.session_state["notice"] = "Profile saved — your roadmap is ready."
        st.session_state["pending_page"] = "Overview"
        st.rerun()


def show_resume_page(profile: dict, skills: dict, db: EduPathDatabase) -> None:
    st.title("Resume analyzer")
    st.caption("Upload a PDF, DOCX, or TXT resume. EduPath extracts structured evidence and asks you to review it before changing your profile. In Demo Mode, the document stays on your computer.")
    uploaded = st.file_uploader("Upload resume", type=["pdf", "docx", "txt"])
    if not uploaded:
        st.info("Tip: use a text-based PDF for the most reliable extraction.")
        return
    text, error = ResumeParser.extract(uploaded)
    if error:
        st.error(error)
        return
    analysis = ResumeAgent(skills).analyze(text)
    stats = analysis["document_stats"]
    if stats["words"] < 35:
        st.warning("Only a small amount of readable text was extracted. If this does not match your resume, upload a text-based PDF, DOCX, or TXT version.")
    else:
        st.success(f"Resume read successfully — analyzed {stats['words']} words across {stats['lines']} text lines.")
    if analysis["sections_found"]:
        st.caption("Recognized sections: " + " · ".join(analysis["sections_found"]))
    else:
        st.warning("No standard resume headings were detected. The analyzer used keyword evidence instead; review the suggestions carefully.")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Detected technical skills")
        if analysis["detected_skill_details"]:
            st.dataframe(
                [{"Skill": item["skill_name"], "Confidence": item["confidence"], "Evidence": item["evidence"]} for item in analysis["detected_skill_details"]],
                hide_index=True,
                width="stretch",
            )
        else:
            st.write("No tracked skills detected yet. Check the extracted-text preview below if skills are missing.")
        st.markdown("#### Projects")
        st.write(analysis["detected_projects"] or ["No clearly labelled project section found."])
        st.markdown("#### Experience")
        st.write(analysis["detected_experience"] or ["No clearly labelled experience section found."])
    with col2:
        st.markdown("#### Certifications")
        st.write(analysis["detected_certifications"] or ["No certification section found."])
        st.markdown("#### Education")
        st.write(analysis["detected_education"] or ["No education section found."])
        st.markdown("#### Relevant keywords")
        st.write(", ".join(analysis["relevant_keywords"]) or "No matching career keywords detected.")
    st.markdown("#### Suggested improvements")
    for recommendation in analysis["suggested_improvements"] + analysis["missing_information"]:
        st.write("• " + recommendation)
    with st.expander("Inspect extracted resume text"):
        st.code(analysis["extracted_preview"] or "No readable text extracted.", language="text")
    st.markdown("#### Review skills before adding them")
    reviewed_skills = st.multiselect(
        "Keep only skills you can confidently discuss or demonstrate.",
        options=list(skills),
        default=analysis["detected_skills"],
        format_func=lambda item: title_case_skill(item, skills),
        key=f"resume_review_{getattr(uploaded, 'file_id', uploaded.name)}",
    )
    if reviewed_skills and st.button("Add reviewed skills to my profile", type="primary"):
        updated = ProfileAgent().merge_resume_skills(profile, reviewed_skills)
        db.save_profile(updated)
        st.session_state["notice"] = "Reviewed resume skills were added at foundation level. Review their levels in My Profile."
        st.session_state["pending_page"] = "My Profile"
        st.rerun()


def show_gap_page(state: dict, skills: dict) -> None:
    st.title("Skill-gap intelligence")
    st.caption("Priority considers gap size, role importance, prerequisites, current momentum, and estimated learning time — not just the largest numeric difference.")
    col1, col2 = st.columns([1.05, 0.95])
    with col1:
        st.plotly_chart(gap_bar(state["prioritized"]), width="stretch", config={"displayModeBar": False})
    with col2:
        st.markdown("#### Priority queue")
        for index, item in enumerate([item for item in state["prioritized"] if item["gap"] > 0][:6], 1):
            st.markdown(f"**{index}. {item['skill_name']}** · <span class='status-chip'>{item['priority']} · {item['priority_score']}</span>", unsafe_allow_html=True)
            st.caption(item["priority_reason"])
    st.markdown("#### Skill details")
    render_skill_cards(st, state["prioritized"])
    priority_agent = PriorityAgent(skills)
    for item in [item for item in state["prioritized"] if item["gap"] > 0]:
        with st.expander(f"Explain my {item['skill_name']} gap"):
            explanation = priority_agent.explain_gap(item)
            st.write(f"**Why you need it:** {explanation['why']}")
            st.write(f"**What you currently know:** {explanation['current']}")
            st.write(f"**What to learn:** {explanation['learn']}")
            st.write(f"**How to learn it:** {explanation['how']}")
            st.write(f"**How to prove it:** {explanation['prove']}")
            if explanation["prerequisites"]:
                st.write("**Prerequisites:** " + ", ".join(explanation["prerequisites"]))


def show_roadmap_page(state: dict, db: EduPathDatabase) -> None:
    st.title("Adaptive learning roadmap")
    st.caption("The roadmap restructures itself around completed skills and repeated assessment difficulty.")
    completed = db.completed_ids("roadmap")
    changed = render_roadmap(st, state["roadmap"], completed)
    if changed:
        db.record_progress("roadmap", changed)
        st.session_state["notice"] = "Roadmap milestone completed. Your progress signal has been recorded."
        st.rerun()


def show_resources_page(state: dict, db: EduPathDatabase) -> None:
    st.title("Personalized resources")
    st.caption("Recommendations match your priority gaps and current level. Completed items are excluded from fresh recommendations.")
    recommendations = state["recommendations"]
    if not recommendations:
        st.success("No resource gaps are currently open. Reinforce your skills with a portfolio project.")
        return
    for skill_id, items in recommendations.items():
        st.markdown(f"### {items[0].get('skill', skill_id).replace('_', ' ').title()}")
        columns = st.columns(max(1, min(3, len(items))))
        for column, resource in zip(columns, items):
            with column:
                st.markdown(f"<div class='resource-card'><span class='status-chip'>{resource['type']} · {resource['difficulty']}</span><h4>{resource['title']}</h4><p>{resource['description']}</p><small>⏱ {resource['estimated_hours']} hours</small></div>", unsafe_allow_html=True)
                st.link_button("Open resource", resource["url"], width="stretch")
                if st.button("Mark completed", key=f"resource_{resource['id']}", width="stretch"):
                    db.record_progress("resource", resource["id"], resource["skill"])
                    st.session_state["notice"] = "Resource marked completed."
                    st.rerun()


def show_practice_page(profile: dict, state: dict, skills: dict, db: EduPathDatabase) -> None:
    st.title("AI practice generator")
    st.caption("Each task changes with your self-assessed level and gives your coach new evidence to use.")
    choices = [item["skill_id"] for item in state["prioritized"] if item["gap"] > 0] or list(state["career"].get("skills", {}))
    if not choices:
        st.info("Choose a target career in My Profile first.")
        return
    skill_id = st.selectbox("Skill to practice", choices, format_func=lambda item: title_case_skill(item, skills))
    task = PracticeAgent(skills).generate(skill_id, int(profile.get("skills", {}).get(skill_id, 0)))
    st.markdown(f"### {task['title']} <span class='status-chip'>{task['difficulty']}</span>", unsafe_allow_html=True)
    st.write(task["objective"])
    st.markdown("**Instructions**")
    for index, instruction in enumerate(task["instructions"], 1):
        st.write(f"{index}. {instruction}")
    st.markdown(f"**Expected output:** {task['expected_output']}")
    with st.expander("Optional hint"):
        st.write(task["hint"])
    if st.button("I completed this practice sprint", type="primary"):
        db.record_progress("practice", task["id"], task["skill_id"], minutes=45)
        st.session_state["notice"] = "Practice completed — nice work. Your activity is now part of the adaptive plan."
        st.rerun()


def show_projects_page(state: dict, db: EduPathDatabase) -> None:
    st.title("Portfolio project generator")
    st.caption("Projects are selected from your target role and skill gaps, so each one becomes evidence for your next opportunity.")
    if not state["projects"]:
        st.info("Complete or update a profile to receive project recommendations.")
        return
    for project in state["projects"]:
        with st.expander(f"{project['title']} · {project['difficulty'].title()}", expanded=True):
            st.write(project["problem"])
            st.write("**Skills covered:** " + ", ".join(item.replace("_", " ").title() for item in project["skills"]))
            st.write("**Dataset / API:** " + project["dataset"])
            st.write("**Features:** " + " · ".join(project["features"]))
            st.write("**Development path:**")
            for index, step in enumerate(project["steps"], 1):
                st.write(f"{index}. {step}")
            st.success("Portfolio value: " + project["portfolio_value"])
            if st.button("Mark project completed", key=f"project_{project['id']}"):
                db.record_progress("project", project["id"], minutes=180)
                st.session_state["notice"] = "Project completion recorded. Add the project to your resume with an outcome-focused bullet."
                st.rerun()


def show_assessment_page(profile: dict, state: dict, skills: dict, db: EduPathDatabase) -> None:
    st.title("Adaptive learning assessment")
    st.caption("Short checks improve the skill estimate and trigger extra support when a pattern of difficulty appears.")
    options = [item["skill_id"] for item in state["prioritized"] if item["gap"] > 0] or list(state["career"].get("skills", {}))
    if not options:
        st.info("Create a profile first.")
        return
    skill_id = st.selectbox("Assessment topic", options, format_func=lambda item: title_case_skill(item, skills), key="assessment_skill")
    assessment = AssessmentAgent(skills).generate(skill_id, int(profile.get("skills", {}).get(skill_id, 0)))
    st.markdown(f"### {assessment['title']}")
    st.caption(assessment["instructions"])
    answers: dict[str, str] = {}
    with st.form(f"assessment_form_{skill_id}"):
        for number, question in enumerate(assessment["questions"], 1):
            st.markdown(f"**{number}. {question['question']}**")
            if question["type"] == "mcq":
                answers[question["id"]] = st.radio("Choose one", question["options"], key=f"assessment_{skill_id}_{question['id']}", label_visibility="collapsed")
            else:
                answers[question["id"]] = st.text_area("Your answer", key=f"assessment_{skill_id}_{question['id']}", label_visibility="collapsed", height=90)
        submitted = st.form_submit_button("Submit assessment", type="primary")
    if submitted:
        score, feedback = AssessmentAgent.evaluate(assessment, answers)
        db.record_assessment(skill_id, score, answers)
        db.record_progress("assessment", f"{skill_id}-{len(state['history']) + 1}", skill_id, minutes=15)
        st.metric("Assessment score", f"{score:.0f}%")
        for item in feedback:
            if item["passed"]:
                st.success("✓ Good evidence of understanding.")
            else:
                st.warning("↳ " + item["feedback"])
        if score >= 80:
            previous = int(profile.get("skills", {}).get(skill_id, 0))
            new_level = min(5, previous + 1)
            db.update_skill(skill_id, new_level)
            st.success(f"Your {title_case_skill(skill_id, skills)} estimate moved from {previous}/5 to {new_level}/5. The next roadmap view will reflect it.")
        elif score < 60:
            st.warning("This score adds a support signal. Complete a simpler practice sprint, then try again after review.")
        else:
            st.info("You are building momentum. Try one applied practice task before your next check.")


def show_progress_page(state: dict, db: EduPathDatabase) -> None:
    st.title("Progress and adaptation")
    summary = state["summary"]
    stats = st.columns(4)
    stats[0].metric("Skill coverage", f"{summary['coverage']}%")
    stats[1].metric("Resources", summary["completed_resources"])
    stats[2].metric("Assessments", summary["assessments"])
    stats[3].metric("Projects", summary["completed_projects"])
    left, right = st.columns(2)
    with left:
        st.markdown("### Skill radar")
        st.plotly_chart(skill_radar(state["gaps"]), width="stretch", config={"displayModeBar": False})
    with right:
        st.markdown("### Skill-gap heatmap")
        for item in state["prioritized"]:
            ratio = item["current_level"] / max(1, item["required_level"])
            st.write(f"**{item['skill_name']}** · {item['current_level']}/{item['required_level']}")
            st.progress(min(1.0, ratio))
    st.markdown("### Learning activity")
    with st.form("log_learning"):
        minutes = st.number_input("Minutes studied today", min_value=5, max_value=600, value=30, step=5)
        note = st.text_input("What did you work on?", placeholder="e.g. Practiced pandas grouping")
        logged = st.form_submit_button("Log learning")
    if logged:
        db.record_progress("study", note or "study-session", minutes=int(minutes))
        st.session_state["notice"] = "Learning time logged — your streak is updated."
        st.rerun()
    st.markdown("### Struggle detection")
    if state["struggles"]:
        for alert in state["struggles"]:
            scores = ", ".join(f"{int(score)}%" for score in alert["scores"])
            st.warning(f"⚠️ **{alert['skill_name']} needs attention** — recent scores: {scores}. {alert['recommendation']}")
    else:
        st.success("No repeated low-score pattern detected yet. Keep using assessments to make your plan more precise.")


def show_coach_page(profile: dict, state: dict, ai_service: AIService, db: EduPathDatabase) -> None:
    st.title("EduPath AI Coach")
    st.caption("A context-aware coach that uses your target role, skill gaps, roadmap, and progress — not a generic chatbot.")
    context = {
        "profile": profile, "career_name": state["career"].get("name", "your target role"),
        "top_gaps": [item for item in state["prioritized"] if item["gap"] > 0][:3],
        "next_items": [week.get("theme") for week in state["roadmap"][:3]], "daily_plan": state["daily_plan"],
        "coverage": state["summary"]["coverage"],
    }
    history = db.get_chat_history()
    for message in history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    question = st.chat_input("Ask about your learning path…")
    if question:
        db.record_chat("user", question)
        reply = CoachAgent(ai_service).reply(question, context)
        db.record_chat("assistant", reply["content"])
        if reply["action"]:
            st.session_state["coach_action"] = reply["action"]
        st.rerun()
    action = st.session_state.pop("coach_action", None)
    if action and st.button(f"Open {action}", type="primary"):
        st.session_state["pending_page"] = action
        st.rerun()
    st.markdown("#### Try a contextual command")
    examples = ["What should I learn today?", "Show my biggest skill gap.", "Give me a practice problem.", "Test me on SQL.", "Am I ready for an internship?"]
    selected = st.selectbox("Example", examples, label_visibility="collapsed")
    if st.button("Ask the coach"):
        db.record_chat("user", selected)
        reply = CoachAgent(ai_service).reply(selected, context)
        db.record_chat("assistant", reply["content"])
        if reply["action"]:
            st.session_state["coach_action"] = reply["action"]
        st.rerun()


def show_reports_page(profile: dict, state: dict) -> None:
    st.title("Progress report")
    report = ProgressAgent().report(profile, state["career"].get("name", "Target role"), state["summary"], state["prioritized"], state["struggles"])
    st.text_area("EduPath progress report", report, height=330)
    col1, col2 = st.columns(2)
    with col1:
        st.download_button("Download text report", report, file_name=f"{safe_filename(profile.get('name', 'edupath'))}-progress-report.txt", mime="text/plain", width="stretch")
    with col2:
        pdf = make_report_pdf(report)
        if pdf:
            st.download_button("Download PDF report", pdf, file_name=f"{safe_filename(profile.get('name', 'edupath'))}-progress-report.pdf", mime="application/pdf", width="stretch")
        else:
            st.button("PDF unavailable — install requirements", disabled=True, width="stretch")
    st.caption("Career skill coverage is a learning indicator; it does not guarantee job or internship readiness.")


def main() -> None:
    inject_styles()
    careers, skills, resources, projects = load_reference_data()
    if not careers or not skills:
        st.error("EduPath reference data is unavailable or invalid. Restore the JSON files in the data folder and restart the app.")
        st.stop()
    try:
        db = get_database()
        db.seed_reference_data(skills, careers, resources, projects)
    except Exception:
        st.error("EduPath could not initialize its local database. Check that the project folder is writable, then restart the app.")
        st.stop()
    if st.session_state.get("pending_page"):
        st.session_state["navigation"] = st.session_state.pop("pending_page")
    profile = db.get_profile()
    ai_service = AIService(get_api_key())
    page, load_demo = render_sidebar(st, ai_service.mode_label, profile)
    if load_demo:
        demo = ProfileAgent().demo_profile()
        profile = db.save_profile(demo)
        initial_state = build_state(profile, careers, skills, resources, projects, db)
        db.save_roadmap(RoadmapAgent(skills).build(initial_state["prioritized"], profile["weekly_hours"]))
        st.session_state["notice"] = "Demo profile loaded — explore the agent’s full learning flow."
        st.session_state["pending_page"] = "Overview"
        st.rerun()
    if notice := st.session_state.pop("notice", None):
        st.success(notice)
    if page == "My Profile":
        show_profile_page(profile, careers, skills, db)
        return
    if not profile:
        st.title("Welcome to 🚀 EduPath")
        st.write("Create a profile or use the one-click demo to see your adaptive learning agent in action.")
        if st.button("Create my profile", type="primary"):
            st.session_state["pending_page"] = "My Profile"
            st.rerun()
        return
    state = build_state(profile, careers, skills, resources, projects, db)
    career_name = state["career"].get("name", "Target role")
    if page == "Overview":
        render_overview(st, profile, career_name, state["summary"], state["gaps"], state["daily_plan"], db.learning_streak())
    elif page == "Resume Analysis":
        show_resume_page(profile, skills, db)
    elif page == "Skill Gap":
        show_gap_page(state, skills)
    elif page == "Learning Roadmap":
        show_roadmap_page(state, db)
    elif page == "Resources":
        show_resources_page(state, db)
    elif page == "Practice":
        show_practice_page(profile, state, skills, db)
    elif page == "Projects":
        show_projects_page(state, db)
    elif page == "Assessment":
        show_assessment_page(profile, state, skills, db)
    elif page == "Progress":
        show_progress_page(state, db)
    elif page == "AI Coach":
        show_coach_page(profile, state, ai_service, db)
    elif page == "Reports":
        show_reports_page(profile, state)


if __name__ == "__main__":
    main()
