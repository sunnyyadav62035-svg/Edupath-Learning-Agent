import html


def render_skill_cards(st, gaps: list[dict], limit: int | None = None) -> None:
    for item in gaps[:limit] if limit else gaps:
        palette = {"Gap": "#ef4444", "Developing": "#f59e0b", "Strong": "#16a34a"}
        color = palette.get(item["classification"], "#64748b")
        st.markdown(
            f"<div class='skill-card'><div><strong>{html.escape(item['skill_name'])}</strong><br>"
            f"<span class='subtle'>{html.escape(item['description'])}</span></div>"
            f"<div class='skill-levels'><span>{item['current_level']}/5 now</span><span>{item['required_level']}/5 target</span>"
            f"<b style='color:{color}'>{item['classification']} · gap {item['gap']}</b></div></div>",
            unsafe_allow_html=True,
        )
