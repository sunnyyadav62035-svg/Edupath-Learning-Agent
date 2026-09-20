import plotly.graph_objects as go


def skill_radar(gaps: list[dict]) -> go.Figure:
    labels = [item["skill_name"] for item in gaps]
    current = [item["current_level"] for item in gaps]
    required = [item["required_level"] for item in gaps]
    figure = go.Figure()
    figure.add_trace(go.Scatterpolar(r=current, theta=labels, fill="toself", name="Current", line_color="#4f46e5"))
    figure.add_trace(go.Scatterpolar(r=required, theta=labels, fill="toself", name="Target", line_color="#f97316", opacity=0.45))
    figure.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 5], tickvals=[0, 1, 2, 3, 4, 5])),
        margin=dict(l=40, r=40, t=35, b=35), height=390, legend=dict(orientation="h", y=-0.12),
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return figure


def gap_bar(gaps: list[dict]) -> go.Figure:
    ordered = sorted(gaps, key=lambda item: item["gap"], reverse=True)
    colors = ["#ef4444" if item["classification"] == "Gap" else "#f59e0b" if item["classification"] == "Developing" else "#22c55e" for item in ordered]
    figure = go.Figure(go.Bar(x=[item["gap"] for item in ordered], y=[item["skill_name"] for item in ordered],
                              orientation="h", marker_color=colors, text=[f"{item['gap']} level" for item in ordered], textposition="outside"))
    figure.update_layout(xaxis=dict(range=[0, 5], title="Levels to close"), yaxis=dict(autorange="reversed"),
                         height=max(280, len(ordered) * 38), margin=dict(l=20, r=40, t=25, b=30), paper_bgcolor="rgba(0,0,0,0)")
    return figure
