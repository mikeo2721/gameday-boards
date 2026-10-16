# Gameday Boards

College football dashboards, one page per team, refreshed weekly (Monday mornings, Central).
Embedded on https://oneilltexas.com/sports/sports-stats/ (one WordPress page per team, slug = team slug).

The team set is in `pipeline/teams.json` (currently the AP Top 10, week 7, Oct 12, 2026).
It does not re-rank itself: change teams.json to change the set, and add a matching WordPress page.

## Refresh
    pip install sportsdataverse --break-system-packages
    bash pipeline/refresh.sh      # fetch data for every team in teams.json, rebuild the pages at the repo root
    git add -A && git commit -m "Weekly refresh" && git push

## Pipeline (`pipeline/`)
- `teams.json`: team list (ESPN id, page slug, display name), in poll order.
- `fetch.py`: pulls schedule, team box, player box and play-by-play (EPA) from the SportsDataverse data releases (ESPN-sourced; lag games by about a day).
- `build.py`: fills `template.html` with one team's data; per-team title and colors in THEMES (new teams need an entry).
- `site.py`: writes `<slug>.html` per team plus `index.html` to the repo root, and removes pages for teams no longer listed.

## Helmets
Header helmets live in `assets/helmets/<slug>.png` (transparent, 220px tall, facing right). `site.py` adds one to a board when a file matching the team's slug exists; a team without one gets the text-only header. 38 FBS teams are pre-cut (ACC, Big 12, Big Ten, SEC sheets plus Notre Dame and Indiana), so most top-10 changes need no new art. They are illustrations, not official marks.

## Unit rankings
`fetch.py` `unit_ranks()` ranks each team among all FBS teams in 14 categories from ESPN box scores (team box + player box), for every season tab:
- Offense/defense (total, passing, rushing): yards per game.
- Return game, return coverage (kick + punt combined), punt returns, kickoff returns: yards per return. Punting: gross average per punt.
- Field goals attempted/made/missed: totals shown, ranked per game. Attempts rank most-first and are colored neutral; misses rank fewest-first.
Longest and average made field-goal distance come from play-by-play (`yds_fg` on 'Field Goal Good' plays), ranked longest-first. Make % by range (inside 40, 40–49, 50+) uses every attempt with a distance (made, missed, blocked); ties break on number of makes, and a team with no attempts in a range is unranked there. When ESPN play-by-play lacks some kicks (summary-only games), the board says how many attempts have no distance.
Penalties: offensive and defensive penalties per game are accepted flags from play-by-play attributed by `penalty_team_id` vs. possession (kicking plays excluded; counts match the official totals for ~98% of flags). Total penalties and penalty yards per game are official box-score figures. Off/def penalty yards are not shown: play-by-play captures only ~86% of penalty yardage. Fewer is better for all four.
Ties show as T-. Rate stats need at least one attempt, so N can differ by row.

## Y/Y Scorecard tab
A "Y/Y Scorecard" tab after the season tabs compares the latest season with the one before, built in the page from data already in each board (no pipeline step). It covers 33 metrics: results (win %, scoring, turnover margin per game, 3rd down), EPA efficiency and every unit ranking. All are rate stats, so a partial season compares with a full one.
Toggle: "<last year> through week N" (default) vs. "Full <last year> season". The like-for-like view uses `seasons[<prior>].to_date`, written by `fetch.py`: the prior season cut to regular-season games through the current season's last completed week (`completed_week()`: last week with 90%+ of games final, since canceled games never finish), with EPA and unit ranks recomputed among all FBS teams as of that week.
Trend rule: Better/Worse needs a value change beyond a per-metric noise threshold and, where both seasons are ranked, an FBS rank that did not move 5+ places the other way; anything mixed is Steady. Field goals attempted is shown but not scored. On phones the rank column is hidden and trends show as arrows.

