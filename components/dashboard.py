from components.charts import skill_radar
from components.skill_cards import render_skill_cards


def render_overview(st, profile: dict, career_name: str, summary: dict, gaps: list[dict], daily_plan: list[dict], streak: int) -> None:
    st.title("Learning command center")
    st.caption(f"A personalized path toward **{career_name}** — updated from your profile, work, and assessments.")
    metrics = st.columns(4)
    metrics[0].metric("Skill coverage", f"{summary['coverage']}%", help="Coverage of the role requirements you are tracking; it is not a job-readiness guarantee.")
    metrics[1].metric("Learning streak", f"{streak} day{'s' if streak != 1 else ''}")
    metrics[2].metric("Practice completed", summary["completed_practice"])
    metrics[3].metric("Hours logged", round(summary["learning_minutes"] / 60, 1))
    st.markdown("### Smart daily plan")
    for index, item in enumerate(daily_plan, start=1):
        st.markdown(f"<div class='daily-item'><b>{index}. {item['label']}</b><span>{item['minutes']} min</span><br><small>{item['detail']}</small></div>", unsafe_allow_html=True)
    left, right = st.columns([1.08, 1])
    with left:
        st.markdown("### Your skill profile")
        st.plotly_chart(skill_radar(gaps), width="stretch", config={"displayModeBar": False})
    with right:
        st.markdown("### Highest-leverage next steps")
        render_skill_cards(st, [item for item in gaps if item["gap"] > 0], limit=4)
