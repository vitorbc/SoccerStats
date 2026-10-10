"""CSV parsing and aggregation, independent of the user interface."""

from pathlib import Path
import unicodedata

import pandas as pd

DATA_PATH = Path(__file__).resolve().parent.parent / "brazil_player_stats.csv"
COUNTS = [
    "appearances", "starts", "minutes", "goals", "assists", "goals_assists",
    "non_penalty_goals", "penalties", "penalties_attempted", "yellow_cards", "red_cards",
]
SOURCE_COUNTS = dict(zip(
    ["MP", "Starts", "Min", "Gls", "Ast", "G+A", "G-PK", "PK", "PKatt", "CrdY", "CrdR"],
    COUNTS,
))
RATE_SOURCES = {
    "goals90": "goals", "assists90": "assists", "ga90": "goals_assists",
    "npg90": "non_penalty_goals", "npga90": "non_penalty_contributions",
}
POSITIONS = {
    "GK": "Goalkeeper", "DF": "Defender", "MF": "Midfielder", "FW": "Forward",
    "MFDF": "Midfielder / Defender", "DFMF": "Defender / Midfielder",
    "MFFW": "Midfielder / Forward", "FWMF": "Forward / Midfielder",
}


def load_csv(path: Path = DATA_PATH) -> pd.DataFrame:
    raw = pd.read_csv(path, header=[0, 1], encoding="utf-8-sig", dtype=str)
    # Both header levels matter: Performance/Gls is different from Per 90 Minutes/Gls.
    required = {
        **{("Playing Time" if name in {"MP", "Starts", "Min"} else "Performance", name): dest
           for name, dest in SOURCE_COUNTS.items()},
    }
    columns = {}
    for source, dest in required.items():
        if source not in raw.columns:
            raise ValueError(f"Missing required CSV column: {source[0]} / {source[1]}")
        columns[dest] = raw[source]
    for name, dest in {"Player": "player", "Squad": "team", "Pos": "position", "Nation": "nation", "-9999": "id"}.items():
        matches = [col for col in raw.columns if col[1] == name]
        if len(matches) != 1:
            raise ValueError(f"Expected one CSV column named {name}.")
        columns[dest] = raw[matches[0]]
    frame = pd.DataFrame(columns)
    for col in ["player", "team", "id"]:
        if frame[col].fillna("").str.strip().eq("").any():
            raise ValueError(f"The CSV contains a missing {col}.")
        frame[col] = frame[col].str.strip()
    for col in COUNTS:
        values = pd.to_numeric(frame[col], errors="coerce")
        if values.isna().any() or values.lt(0).any() or values.mod(1).ne(0).any():
            raise ValueError(f"The CSV contains missing or invalid values for {col}.")
        frame[col] = values.astype("int64")
    if frame.duplicated(["id", "team"]).any():
        raise ValueError("Duplicate player/team rows would double-count statistics.")
    if not frame["goals_assists"].eq(frame["goals"] + frame["assists"]).all():
        raise ValueError("Goals + assists do not match the individual totals.")
    if not frame["non_penalty_goals"].eq(frame["goals"] - frame["penalties"]).all():
        raise ValueError("Non-penalty goals do not match goals minus penalties.")
    frame["position"] = frame["position"].fillna("Unknown").replace("", "Unknown")
    frame["position_label"] = frame["position"].map(POSITIONS).fillna(frame["position"])
    return frame


def joined(values: pd.Series) -> str:
    return ", ".join(sorted(set(values.dropna())))


def player_totals(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.groupby("id", as_index=False).agg(
        {**{col: "sum" for col in COUNTS}, "player": "first", "team": joined,
         "position_label": joined, "nation": "first"}
    )
    result["non_penalty_contributions"] = result["non_penalty_goals"] + result["assists"]
    denominator = result["minutes"].replace(0, float("nan"))
    for rate, count in RATE_SOURCES.items():
        result[rate] = result[count] * 90 / denominator
    return result


def team_totals(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.groupby("team", as_index=False)[COUNTS].sum()


def goal_shares(frame: pd.DataFrame) -> pd.DataFrame:
    result = team_totals(frame)
    total = result["goals"].sum()
    result["goal_share"] = result["goals"] / total * 100 if total else 0.0
    return result


def position_goals(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.groupby(["team", "position_label"], as_index=False)["goals"].sum()


def normalize_search(value: str) -> str:
    return "".join(char for char in unicodedata.normalize("NFKD", value.casefold())
                   if not unicodedata.combining(char))


def filter_players(frame: pd.DataFrame, teams: list[str], positions: list[str], query: str) -> pd.DataFrame:
    # Club filters select contributions; position filters select players without discarding other stints.
    scoped = frame[frame["team"].isin(teams)] if teams else frame
    result = player_totals(scoped)
    if positions:
        ids = scoped.loc[scoped["position_label"].isin(positions), "id"]
        result = result[result["id"].isin(ids)]
    if query.strip():
        result = result[result["player"].map(normalize_search).str.contains(
            normalize_search(query.strip()), regex=False)]
    return result


def ranked(frame: pd.DataFrame, metric: str, entity: str) -> pd.DataFrame:
    result = frame.dropna(subset=[metric]).copy()
    result["rank"] = result[metric].rank(method="min", ascending=False).astype(int)
    # Preserve shared ranks; alphabetic order keeps a fixed-size top 3 or top 10 deterministic.
    return result.sort_values([metric, entity], ascending=[False, True])
