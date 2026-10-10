from pathlib import Path
import json

from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / "app.py")


def app():
    return AppTest.from_file(APP, default_timeout=30).run()


def test_home_and_page_navigation():
    at = app()
    assert not at.exception
    assert [metric.value for metric in at.metric] == ["715", "20", "749", "521"]
    assert len(at.get("page_link")) == 2
    at.switch_page("views/players.py").run()
    assert not at.exception
    assert at.title[0].value == "Every player. Every contribution."
    at.switch_page("views/teams.py").run()
    assert not at.exception
    assert len(at.get("plotly_chart")) == 3


def test_player_expansion_filters_and_empty_state():
    at = app().switch_page("views/players.py").run()
    assert not at.exception
    assert len(at.dataframe[0].value) == 10
    at.toggle(key="player_goals_all").set_value(True).run()
    assert len(at.dataframe[0].value) == 715
    at.multiselect(key="player_teams").set_value(["São Paulo"]).run()
    assert at.dataframe[0].value.Team.eq("São Paulo").all()
    at.text_input(key="player_search").set_value("nonexistent-player-xyz").run()
    assert not at.exception
    assert len(at.dataframe) == 0
    assert len(at.info) > 0


def test_team_selection_and_expansion():
    at = app().switch_page("views/teams.py").run()
    assert not at.exception
    assert len(at.dataframe[0].value) == 10
    at.toggle(key="team_goals_all").set_value(True).run()
    assert len(at.dataframe[0].value) == 20
    at.multiselect(key="compare_teams").set_value(["Flamengo", "Santos"]).run()
    assert not at.exception
    assert set(at.dataframe[0].value.Team) == {"Flamengo", "Santos"}
    assert len(at.get("plotly_chart")) == 3


def test_minute_thresholds():
    at = app().switch_page("views/players.py").run()
    at.number_input[1].set_value(100000).run()
    assert not at.exception
    # Counting-stat lists remain visible; all five per-90 lists have no qualifiers.
    assert len(at.dataframe) == 11
    assert len(at.info) == 5
    at.number_input[0].set_value(100000).run()
    assert not at.exception
    assert len(at.dataframe) == 0


def test_player_filter_reset_restores_defaults_and_results():
    at = app().switch_page("views/players.py").run()
    at.text_input(key="player_search").set_value("nothing-matches")
    at.multiselect(key="player_teams").set_value(["Santos"])
    at.multiselect(key="player_positions").set_value(["Forward"])
    at.number_input(key="player_minimum").set_value(900)
    at.number_input(key="player_minimum90").set_value(900).run()
    assert len(at.dataframe) == 0
    at.button(key="player_filters_reset").click().run()
    assert not at.exception
    assert at.text_input(key="player_search").value == ""
    assert at.multiselect(key="player_teams").value == []
    assert at.multiselect(key="player_positions").value == []
    assert at.number_input(key="player_minimum").value == 0
    assert at.number_input(key="player_minimum90").value == 450
    assert len(at.dataframe[0].value) == 10
    assert at.dataframe[0].value.iloc[0].Player == "Kevin Viveros"


def test_leaderboard_reset_preserves_other_features():
    for page, entity in [("views/players.py", "player"), ("views/teams.py", "team")]:
        at = app().switch_page(page).run()
        at.toggle(key=f"{entity}_goals_all").set_value(True)
        at.toggle(key=f"{entity}_assists_all").set_value(True).run()
        assert len(at.dataframe[0].value) > 10
        at.button(key=f"{entity}_goals_all_reset").click().run()
        assert not at.exception
        assert len(at.dataframe[0].value) == 10
        assert not at.toggle(key=f"{entity}_goals_all").value
        assert at.toggle(key=f"{entity}_assists_all").value


def test_team_filter_and_chart_resets():
    at = app().switch_page("views/teams.py").run()
    at.multiselect(key="compare_teams").set_value(["Santos"]).run()
    assert len(at.dataframe[0].value) == 1
    for index, key in enumerate(["goal_share", "position_goals", "goals_assists"]):
        old_ids = [chart.proto.id for chart in at.get("plotly_chart")]
        at.button(key=f"{key}_reset").click().run()
        assert not at.exception
        assert at.multiselect(key="compare_teams").value == ["Santos"]
        new_ids = [chart.proto.id for chart in at.get("plotly_chart")]
        assert old_ids[index] != new_ids[index]
        assert all(old == new for i, (old, new) in enumerate(zip(old_ids, new_ids)) if i != index)
    at.button(key="team_filters_reset").click().run()
    assert not at.exception
    assert at.multiselect(key="compare_teams").value == []
    assert len(at.dataframe[0].value) == 10


def test_position_chart_excludes_unknown_and_tooltips_are_concise():
    at = app().switch_page("views/teams.py").run()
    positions = json.loads(at.get("plotly_chart")[1].proto.spec)
    assert "Unknown" not in [trace["name"] for trace in positions["data"]]
    assert "Unknown" not in positions["layout"]["legend"].get("title", {}).get("text", "")
    assert all(trace["hovertemplate"] == "%{customdata[0]}<br>Goals: %{y}<extra></extra>"
               for trace in positions["data"])
    scoring = json.loads(at.get("plotly_chart")[2].proto.spec)
    assert all(trace["hovertemplate"] == "%{customdata[0]}: %{y}<extra></extra>"
               for trace in scoring["data"])
