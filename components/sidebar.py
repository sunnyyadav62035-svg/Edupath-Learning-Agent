from utils.constants import NAV_ITEMS


def render_sidebar(st, mode_label: str, profile: dict | None) -> tuple[str, bool]:
    with st.sidebar:
        st.markdown("## 🚀 EduPath")
        st.caption("Your AI-powered learning & career agent")
        st.info(mode_label)
        demo = st.button("🚀 Load Demo Profile", width="stretch")
        if profile:
            st.success(f"Learning as {profile.get('name', 'Learner')}")
            st.caption(f"Target: {profile.get('target_career', '').replace('_', ' ').title()}")
        else:
            st.warning("Set up a profile or load the demo.")
        choice = st.radio("Navigate", NAV_ITEMS, key="navigation")
        st.divider()
        st.caption("Built for AI Agent Hackathon 2026")
    return choice, demo
