def render_roadmap(st, roadmap: list[dict], completed_items: set[str]) -> str | None:
    selected = None
    if not roadmap:
        st.info("Create or load a profile to generate a learning roadmap.")
        return None
    for week in roadmap:
        item = week.get("items", [{}])[0]
        status = "✅ Complete" if item.get("id") in completed_items or item.get("status") == "completed" else "⚠️ Support added" if item.get("status") == "support_needed" else "📍 Planned"
        with st.expander(f"Week {week['week']} · {week['theme']} · {week['estimated_hours']}h · {status}", expanded=week["week"] <= 2):
            st.caption(item.get("why_now", ""))
            st.write("**Topics:** " + " · ".join(item.get("topics", [])))
            st.write("**Practice:** " + item.get("practice", ""))
            st.write("**Portfolio mini-project:** " + item.get("project", ""))
            if item.get("id") not in completed_items and st.button("Mark week complete", key=f"roadmap_complete_{item.get('id')}"):
                selected = item.get("id")
    return selected
