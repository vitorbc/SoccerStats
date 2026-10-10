import streamlit as st

from soccer_stats.data import filter_players
from soccer_stats.ui import get_data, ranking_tabs, reset_filters

data = get_data()
st.title("Every player. Every contribution.")
st.write("Find your favourites, discover a standout, or explore the full field.")
with st.container(border=True):
    search = st.text_input("Find a player", placeholder="Try Pedro or Viveros", key="player_search")
    team_col, position_col = st.columns(2)
    teams = team_col.multiselect("Teams", sorted(data.team.unique()), key="player_teams")
    positions = position_col.multiselect("Positions", sorted(data.position_label.unique()), key="player_positions")
    minutes_col, rates_col = st.columns(2)
    minimum = minutes_col.number_input("Minimum minutes (all rankings)", min_value=0, value=0, step=90,
                                       key="player_minimum")
    minimum90 = rates_col.number_input("Minimum minutes (per-90 rankings)", min_value=0, value=450, step=90,
                                       key="player_minimum90")
    st.button("Reset filters", key="player_filters_reset", on_click=reset_filters, args=("player",))
players = filter_players(data, teams, positions, search)
players = players[players.minutes >= minimum]
st.caption(f"{len(players):,} matching players · Club stints combined within selected teams · Top 10 in each list")
ranking_tabs(players, "player", max(minimum, minimum90))
