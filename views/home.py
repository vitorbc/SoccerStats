import streamlit as st

from soccer_stats.data import player_totals, team_totals
from soccer_stats.ui import get_data, podium

data = get_data()
players = player_totals(data)
teams = team_totals(data)

st.html("""
<section class="hero">
  <div class="eyebrow">Brazilian first division · Stats explorer</div>
  <h1>Big moments.<br>The numbers behind them.</h1>
  <p>Welcome to your Brasileirão stats hub! Meet the players making the difference,
  follow your favourite club, and discover a new side of the beautiful game.
  Pick a leaderboard and let your curiosity lead the way.</p>
</section>
""")

with st.container(key="home_summary"):
    for col, label, value in zip(st.columns(4), ["Players", "Clubs", "Recorded goals", "Assists"],
                                 [len(players), len(teams), int(data.goals.sum()), int(data.assists.sum())]):
        col.metric(label, f"{value:,}")
st.caption("A snapshot of the competition · Season and update date unconfirmed")
st.header("Players making a difference")
st.write("The scorers, the creators, and the players doing a little of both.")
for col, metric in zip(st.columns(3), ["goals", "assists", "goals_assists"]):
    with col:
        podium(players, metric, "player")
st.page_link("views/players.py", label="Show more stats per player", icon=":material/arrow_forward:")
st.divider()
st.header("The team picture")
st.write("Individual contributions, added together. See which clubs lead the way.")
for col, metric in zip(st.columns(3), ["goals", "assists", "goals_assists"]):
    with col:
        podium(teams, metric, "team")
st.page_link("views/teams.py", label="Show more stats per team", icon=":material/arrow_forward:")
st.caption("Equal totals share a rank. Alphabetical order determines which entries appear at the cutoff.")
