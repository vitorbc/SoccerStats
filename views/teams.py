import plotly.express as px
import streamlit as st

from soccer_stats.data import goal_shares, position_goals
from soccer_stats.ui import get_data, ranking_tabs, reset_filters, reset_view, view_key

data = get_data()
st.title("The clubs behind the numbers")
st.write("Compare contributions, explore scoring patterns, and see each club's share of the goals.")
selected = st.multiselect("Choose teams to compare", sorted(data.team.unique()),
                          placeholder="All 20 clubs", key="compare_teams")
st.button("Reset filters", key="team_filters_reset", on_click=reset_filters, args=("team",))
totals = goal_shares(data)
visible = totals[totals.team.isin(selected)] if selected else totals
order = visible.sort_values(["goals", "team"], ascending=[False, True]).team.tolist()
st.caption("Showing all clubs" if not selected else f"Comparing {len(selected)} clubs")


def draw(fig, key, height=530):
    fig.update_layout(height=height, margin=dict(l=0, r=20, t=15, b=0),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font=dict(color="#19362B"), legend_title_text="",
                      xaxis=dict(gridcolor="#DFE7DF"), yaxis=dict(gridcolor="#DFE7DF"))
    fig.update_layout(uirevision=view_key(key))
    st.plotly_chart(fig, width="stretch", key=view_key(key), config={"displaylogo": False})
    st.button("Reset chart", key=f"{key}_reset", on_click=reset_view, args=(key,),
              help="Restore the original zoom and show every series. Current team filters stay applied.")


st.header("A share of every goal")
st.write("Each club's percentage of all player goals recorded in this snapshot.")
fig = px.bar(visible, x="goal_share", y="team", orientation="h", text="goal_share",
             custom_data=["goals"], color_discrete_sequence=["#087F5B"],
             category_orders={"team": order}, labels={"team": "", "goal_share": "Share of recorded goals (%)"})
fig.update_traces(texttemplate="%{x:.1f}%", textposition="outside", cliponaxis=False,
                  hovertemplate="%{y}<br>%{customdata[0]} goals<br>%{x:.2f}% of recorded goals<extra></extra>")
fig.update_xaxes(range=[0, max(1, float(visible.goal_share.max()) * 1.2)])
draw(fig, "goal_share", max(310, len(visible) * 28 + 80))
st.caption(f"Denominator: {int(data.goals.sum()):,} recorded goals across all {data.team.nunique()} clubs. "
           "Selecting teams does not change this denominator.")

st.header("Where the goals come from")
st.write("A breakdown by each player's listed position, including mixed roles.")
positions = position_goals(data)
positions = positions[positions.team.isin(visible.team) & positions.position_label.ne("Unknown")]
position_order = sorted(data.loc[data.position_label.ne("Unknown"), "position_label"].unique())
palette = ["#087F5B", "#62A88A", "#D4A72C", "#5D75A5", "#8C64A0", "#CE7952", "#405F72", "#A88D62", "#838D86"]
fig = px.bar(positions, x="team", y="goals", color="position_label", barmode="stack",
             custom_data=["position_label"],
             color_discrete_map=dict(zip(position_order, palette)),
             category_orders={"team": order, "position_label": position_order},
             labels={"team": "", "goals": "Goals", "position_label": "Listed position"})
fig.update_traces(hovertemplate="%{customdata[0]}<br>Goals: %{y}<extra></extra>")
fig.update_layout(legend=dict(orientation="h", y=-0.4, x=0), xaxis_tickangle=-45)
draw(fig, "position_goals", 640)
st.caption("Mixed roles are kept intact. A listed position does not identify the position played when a goal was scored.")

st.header("Scoring & creating")
fig = px.bar(visible.melt(id_vars="team", value_vars=["goals", "assists"], var_name="stat", value_name="count")
             .replace({"stat": {"goals": "Goals", "assists": "Assists"}}),
             x="team", y="count", color="stat", barmode="group",
             custom_data=["stat"],
             color_discrete_map={"Goals": "#087F5B", "Assists": "#D4A72C"},
             category_orders={"team": order}, labels={"team": "", "count": "Contributions", "stat": "Statistic"})
fig.update_traces(hovertemplate="%{customdata[0]}: %{y}<extra></extra>")
fig.update_layout(xaxis_tickangle=-45, legend=dict(orientation="h", y=1.1))
draw(fig, "goals_assists")
st.header("Explore the team leaderboards")
st.caption("Top 10 in each list · Expand to see every selected club")
ranking_tabs(visible, "team")
