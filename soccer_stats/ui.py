"""Shared page styling and ranking components."""

from html import escape

import pandas as pd
import streamlit as st

from soccer_stats.data import DATA_PATH, load_csv, ranked

LABELS = {
    "goals": "Goals", "assists": "Assists", "goals_assists": "Goals + assists",
    "non_penalty_goals": "Non-penalty goals", "appearances": "Appearances",
    "starts": "Starts", "minutes": "Minutes played", "penalties": "Penalties scored",
    "penalties_attempted": "Penalties attempted", "yellow_cards": "Yellow cards",
    "red_cards": "Red cards", "goals90": "Goals / 90", "assists90": "Assists / 90",
    "ga90": "Goals + assists / 90", "npg90": "Non-penalty goals / 90",
    "npga90": "Non-penalty goals + assists / 90",
}
GROUPS = {
    "Attacking": ["goals", "assists", "goals_assists", "non_penalty_goals"],
    "Playing time": ["appearances", "starts", "minutes"],
    "Penalties & discipline": ["penalties", "penalties_attempted", "yellow_cards", "red_cards"],
    "Per 90 minutes": ["goals90", "assists90", "ga90", "npg90", "npga90"],
}
FILTER_DEFAULTS = {
    "player": {"player_search": "", "player_teams": [], "player_positions": [],
               "player_minimum": 0, "player_minimum90": 450},
    "team": {"compare_teams": []},
}


def reset_filters(entity: str) -> None:
    for key, value in FILTER_DEFAULTS[entity].items():
        st.session_state[key] = value.copy() if isinstance(value, list) else value


def reset_view(key: str, toggle_key: str | None = None) -> None:
    if toggle_key is not None:
        st.session_state[toggle_key] = False
    revision_key = f"{key}_revision"
    st.session_state[revision_key] = st.session_state.get(revision_key, 0) + 1


def view_key(key: str) -> str:
    return f"{key}_{st.session_state.get(f'{key}_revision', 0)}"


@st.cache_data(show_spinner=False)
def cached_data(modified_ns: int, size: int) -> pd.DataFrame:
    return load_csv()


def get_data() -> pd.DataFrame:
    try:
        info = DATA_PATH.stat()
        return cached_data(info.st_mtime_ns, info.st_size)
    except (OSError, ValueError, pd.errors.ParserError) as error:
        st.error(f"We couldn't read the stats snapshot: {error}")
        st.info("Check brazil_player_stats.csv, then refresh the page.")
        st.stop()


def style() -> None:
    st.html("""
    <style>
      .stMainBlockContainer {max-width: 1280px; padding-top: 2rem;}
      h1, h2, h3 {letter-spacing: -.035em;}
      .hero {background: #123E30; color: #fff; border-radius: 22px;
             padding: clamp(24px, 4vw, 52px); margin: 12px 0 26px;
             border-bottom: 6px solid #E8C75F;}
      .hero .eyebrow {color: #E8C75F; font-size: .78rem; letter-spacing: .16em;
                      font-weight: 700; text-transform: uppercase;}
      .hero h1 {color: white; font-size: clamp(2rem, 4vw, 3.3rem); margin: 14px 0;}
      .hero p {color: #DBEBE1; max-width: 700px; line-height: 1.75;}
      .leader {display: flex; align-items: center; gap: 12px;
               padding: 16px 0; border-bottom: 1px solid #DCE5DD;}
      .leader:last-child {border-bottom: none;}
      .rank {font-size: .85rem; color: #4D6559; min-width: 20px;}
      .identity {flex: 1; min-width: 0; overflow-wrap: anywhere;}
      .identity strong {font-size: 1rem;}
      .identity small {display: block; color: #52685C; margin-top: 3px;}
      .score {font-size: 1.65rem; font-weight: 750; color: #087F5B;}
      [data-testid="stMetricValue"] {color: #087F5B;}
      .st-key-home_summary {border: 1px solid #CCD9CF; border-radius: 12px;
                            background: #FFFFFF; overflow: hidden;}
      .st-key-home_summary [data-testid="stHorizontalBlock"] {gap: 0;}
      .st-key-home_summary [data-testid="stColumn"] {border-right: 1px solid #CCD9CF;}
      .st-key-home_summary [data-testid="stColumn"]:last-child {border-right: none;}
      .st-key-home_summary [data-testid="stMetric"] {
        display: flex; flex-direction: column; align-items: center;
        text-align: center; padding: 20px 12px;
      }
      .st-key-home_summary [data-testid="stMetricLabel"] {
        width: 100%; justify-content: center; text-align: center;
      }
      .st-key-home_summary [data-testid="stMetricLabel"] > div {width: 100%;}
      .st-key-home_summary [data-testid="stMetricLabel"] p {text-align: center;}
      @media (max-width: 640px) {
        .st-key-home_summary [data-testid="stColumn"] {
          border-right: none; border-bottom: 1px solid #CCD9CF;
        }
        .st-key-home_summary [data-testid="stColumn"]:last-child {border-bottom: none;}
      }
    </style>
    """)


def podium(frame: pd.DataFrame, metric: str, entity: str) -> None:
    with st.container(border=True):
        st.subheader(LABELS[metric])
        leaders = ranked(frame, metric, entity).head(3)
        for row in leaders.to_dict("records"):
            subtitle = escape(str(row["team"])) if entity == "player" else "Recorded team total"
            st.html(f'<div class="leader"><span class="rank">{row["rank"]:02d}</span>'
                    f'<div class="identity"><strong>{escape(str(row[entity]))}</strong>'
                    f'<small>{subtitle}</small></div><span class="score">{row[metric]:,}</span></div>')


def leaderboard(frame: pd.DataFrame, metric: str, entity: str, key: str) -> None:
    label = LABELS[metric]
    if entity == "team" and metric in {"appearances", "starts", "minutes"}:
        label = {"appearances": "Player appearances", "starts": "Player starts",
                 "minutes": "Player minutes"}[metric]
    with st.container(border=True):
        st.subheader(label)
        ordered = ranked(frame, metric, entity)
        show_all = st.toggle(f"Show all {len(ordered)}", key=key, disabled=len(ordered) <= 10)
        shown = ordered if show_all else ordered.head(10)
        if shown.empty:
            st.info("No results for these filters. Try another team or a lower minutes threshold.")
        else:
            cols = ["rank", entity] + (["team"] if entity == "player" else []) + [metric]
            names = {"rank": "Rank", "player": "Player", "team": "Team", metric: label}
            table = shown[cols].rename(columns=names)
            config = {label: st.column_config.NumberColumn(format="%.2f" if metric.endswith("90") else "%d")}
            # A new container remounts the read-only table, clearing browser-side sorting.
            with st.container(key=view_key(f"{key}_table")):
                st.dataframe(table, hide_index=True, width="stretch", column_config=config,
                             height=min(570, 38 + 35 * len(shown)))
            st.caption(f"Showing {len(shown)} of {len(ordered)} · Highest first")
        st.button("Reset leaderboard", key=f"{key}_reset", on_click=reset_view,
                  args=(f"{key}_table", key),
                  help="Restore the top 10 and default table view. Current filters stay applied.")


def ranking_tabs(frame: pd.DataFrame, entity: str, minimum90: int = 450) -> None:
    groups = GROUPS if entity == "player" else {k: v for k, v in GROUPS.items() if k != "Per 90 minutes"}
    for tab, (group, metrics) in zip(st.tabs(list(groups)), groups.items()):
        with tab:
            if group == "Penalties & discipline":
                st.caption("Card rankings show the most cards received; they are not a performance rating.")
            selected = frame
            if group == "Per 90 minutes":
                selected = frame[frame["minutes"] >= minimum90]
                st.caption(f"At least {minimum90:,} minutes · Rates recalculated from minutes played.")
            for offset in range(0, len(metrics), 2):
                for column, metric in zip(st.columns(2), metrics[offset:offset + 2]):
                    with column:
                        leaderboard(selected, metric, entity, f"{entity}_{metric}_all")


