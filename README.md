# Brasileirão · By the numbers

A local Streamlit website for exploring Brazilian first division player and team statistics from `brazil_player_stats.csv`.

## Run

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then run from this directory:

```powershell
uv sync
uv run streamlit run app.py
```

Open the local URL printed by Streamlit, normally http://localhost:8501. Stop the server with Ctrl+C.
The project selects Python 3.14 and uv manages its environment and locked dependencies.
If your network uses system-managed certificates, use `uv sync --system-certs`.
If the default uv cache is not writable, add `--cache-dir .uv-cache` to your uv command.

## Pages

- **Home:** welcoming introduction and three-player / three-team highlights for goals, assists, and goals + assists.
- **Players:** top-ten leaderboards with individual Show all controls; player search, team and position filters, and minutes thresholds. Search ignores accents and capitalization.
- **Teams:** aggregate leaderboards, goal-share percentages, goals by listed position, and goals versus assists. Select any combination of clubs to compare.

Reset filters restores the original selections and minute thresholds, updating results immediately.
Each leaderboard's reset restores its top-ten view; each chart's reset restores zoom and all legend series.
These individual view resets preserve the page's current filters.

## Data and calculations

The supplied snapshot contains 739 player-team rows, 715 distinct player IDs, 20 clubs, 749 goals and 521 assists. Its season and effective update date have not been confirmed. It is not a live feed.

The loader preserves UTF-8 accents and reads both CSV header rows so count columns cannot be confused with per-90 columns. Missing or invalid counts and duplicate player/team rows produce a visible error instead of silently changing totals. Missing positions are labeled Unknown.

- Overall player totals combine all club stints using the player ID. A team filter counts only contributions to the selected clubs.
- Position filters select players with that listed position in a selected club; their other contributions within the selected clubs remain included.
- Team totals sum player contributions. Player appearances, starts and minutes do not represent team match counts. Team per-match/per-90 statistics are not computed because team match data is unavailable.
- Rates use `90 × contributions / minutes`, recalculated after aggregation. Players with zero minutes have no rate. The per-90 minimum is initially 450 minutes; the all-rankings minimum also applies.
- Goal-share charts divide by all goals recorded in the dataset, even when only some clubs are selected. Player goals may exclude own goals, so these shares are not claimed as independently verified competition totals.
- Mixed positions remain distinct, and do not describe the position occupied at the time of a goal. Unknown positions are omitted from the position chart only; all player contributions remain included in other totals.
- Equal values share ranks. Alphabetical ordering decides top-three/top-ten cutoff entries; expand a leaderboard to see everyone.
- Goals + assists counts both contributions for assisted goals. Cards are presented highest first, without implying that more cards is better.

To update the snapshot, replace the CSV with the same two-header format and refresh the app. File modification time and size invalidate the data cache. No CSV changes are made by the app.

## Development

```powershell
uv run pytest
```

`soccer_stats/data.py` owns parsing and calculations; `soccer_stats/ui.py` owns shared components. `app.py` provides navigation to the three scripts in `views/`. Tests check aggregation, transfers, zero-minute rates, chart denominators, invalid inputs, and Streamlit page interactions.
