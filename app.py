import streamlit as st

from soccer_stats.ui import style

st.set_page_config(page_title="Brasileirão · By the numbers", page_icon="⚽", layout="wide")
style()
page = st.navigation([
    st.Page("views/home.py", title="Home", icon=":material/home:", default=True),
    st.Page("views/players.py", title="Players", icon=":material/person:", url_path="players"),
    st.Page("views/teams.py", title="Teams", icon=":material/groups:", url_path="teams"),
], position="top")
page.run()
st.divider()
st.caption("BRASILEIRÃO · BY THE NUMBERS  |  A little closer to the beautiful game.  |  Supplied CSV snapshot")
