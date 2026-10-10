from pathlib import Path

import pandas as pd
import pytest

from soccer_stats.data import (
    DATA_PATH, filter_players, goal_shares, load_csv, player_totals, position_goals,
    ranked, team_totals,
)


@pytest.fixture
def snapshot():
    return load_csv()


@pytest.fixture
def transfers(snapshot):
    rows = snapshot.head(3).copy()
    rows["id"] = ["a", "a", "b"]
    rows["player"] = ["João", "João", "Bruno"]
    rows["team"] = ["A", "B", "B"]
    rows["position_label"] = ["Forward", "Midfielder", "Forward"]
    rows["minutes"] = [90, 270, 0]
    rows["goals"] = [2, 1, 0]
    rows["assists"] = [1, 2, 0]
    rows["goals_assists"] = rows.goals + rows.assists
    rows["non_penalty_goals"] = rows.goals
    return rows


def test_snapshot_headers_encoding_and_totals(snapshot):
    assert len(snapshot) == 739
    assert snapshot.id.nunique() == 715
    assert snapshot.team.nunique() == 20
    assert snapshot.goals.sum() == 749
    assert snapshot.assists.sum() == 521
    assert "Nicolás Acevedo" in snapshot.player.values
    assert snapshot.position.eq("Unknown").sum() == 1


def test_transfers_and_rates_are_recalculated(transfers):
    players = player_totals(transfers).set_index("id")
    assert players.loc["a", "goals"] == 3
    assert players.loc["a", "team"] == "A, B"
    assert players.loc["a", "goals90"] == pytest.approx(0.75)
    assert players.loc["a", "ga90"] == pytest.approx(1.5)
    assert pd.isna(players.loc["b", "goals90"])


def test_club_filter_keeps_only_club_contributions(transfers):
    players = filter_players(transfers, ["A"], [], "joao")
    assert len(players) == 1
    assert players.iloc[0].goals == 2
    assert players.iloc[0].goals90 == 2


def test_position_filter_preserves_selected_players_other_stints(transfers):
    players = filter_players(transfers, [], ["Midfielder"], "")
    assert len(players) == 1
    assert players.iloc[0].goals == 3


def test_literal_search_and_empty_filters(transfers):
    assert filter_players(transfers, [], [], "[").empty
    assert filter_players(transfers, ["Missing"], [], "").empty


def test_team_and_position_aggregation_reconcile(snapshot):
    teams = team_totals(snapshot).set_index("team")
    positions = position_goals(snapshot).groupby("team").goals.sum()
    assert teams.goals.sum() == 749
    pd.testing.assert_series_equal(teams.goals, positions)
    assert player_totals(snapshot).goals.sum() == teams.goals.sum()


def test_percentage_denominator_stays_global(transfers):
    shares = goal_shares(transfers)
    assert shares.goal_share.sum() == pytest.approx(100)
    selected = shares[shares.team.eq("A")]
    assert selected.iloc[0].goal_share == pytest.approx(200 / 3)


def test_zero_goals_are_supported(transfers):
    transfers["goals"] = 0
    assert goal_shares(transfers).goal_share.eq(0).all()


def test_ties_share_rank_and_sort_deterministically():
    frame = pd.DataFrame({"player": ["Z", "A", "B"], "goals": [3, 3, 1]})
    ordered = ranked(frame, "goals", "player")
    assert ordered.player.tolist() == ["A", "Z", "B"]
    assert ordered["rank"].tolist() == [1, 1, 3]


def test_duplicate_stints_fail_with_clear_error(tmp_path):
    lines = DATA_PATH.read_text(encoding="utf-8").splitlines()
    bad = tmp_path / "duplicate.csv"
    bad.write_text("\n".join(lines + [lines[2]]), encoding="utf-8")
    with pytest.raises(ValueError, match="Duplicate player/team"):
        load_csv(bad)


def test_missing_numeric_values_do_not_silently_become_zero(tmp_path):
    lines = DATA_PATH.read_text(encoding="utf-8").splitlines()
    row = lines[2].split(",")
    row[11] = ""
    lines[2] = ",".join(row)
    bad = tmp_path / "missing.csv"
    bad.write_text("\n".join(lines), encoding="utf-8")
    with pytest.raises(ValueError, match="invalid values for goals"):
        load_csv(bad)
