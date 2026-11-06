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
- `injuries.py`: pulls the conference availability reports into `injuries.json` at the repo root (run by GitHub Actions, see Injuries tab).
- `injuries_manual.json`: hand-entered availability for games with no official report.
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


## Injuries tab
An "Injuries" tab after Y/Y Scorecard shows which of a team's starters are on its latest availability report, with the share of offense, defense and special-teams starters listed Out.

**Reports.** The SEC, Big Ten, ACC and Big 12 publish football availability reports through one vendor app (app.hdintelligence.com, embedded on each conference site). `pipeline/injuries.py` reads its public endpoint and writes `injuries.json` with each tracked team's latest report: source, report type (Initial / Update / gameday), publish time, opponent, game date, and every player not listed Available (plus long snappers). A player with exemptStatus "Out" is shown as Out (season). "Exempt" players (excused from reporting; often 20–30 per team) are counted but not listed.
- Conference games only. Notre Dame (independent) and every non-conference game have no official report.
- Runs in GitHub Actions (`.github/workflows/injuries.yml`): every 2 hours Thu–Fri, hourly Saturday and Saturday night (UTC schedule), on any push that changes the scraper, manual file or team list, and on demand from the Actions tab. It commits only when the data changed. The feed is not reachable from the Claude cloud sandbox, so the weekly refresh does not run it.
- If one conference's feed fails, that conference's teams keep their last good report and the error is listed in `injuries.json`.

**Manual entries.** `pipeline/injuries_manual.json`, keyed by ESPN team id, for games with no report (or to override one). Format and rules are in the `injuries.py` docstring. Empty placeholders are ignored, and entries expire after their `game_date`. Pushing a change to that file triggers the Action.

**Starters.** ESPN has no college depth charts, so `fetch.py` `starters()` infers them from the current season's player box scores (weekly refresh): QB by pass attempts per game, RB by rush attempts, top 4 receivers by catches, top 11 defenders by tackles, K by kick attempts, P by punts, KR and PR by returns, among players in at least max(2, 35%) of the team's games. The board adds the long snapper from the report roster when exactly one is listed. Offensive linemen never appear in box scores, so they are not starters here; OL on the report are listed as "starter status unknown". Offense % is out of the 6 skill starters.

**Matching.** Report names are matched to box-score names after dropping punctuation and Jr./II-style suffixes, falling back to last name plus jersey number. Percentages count Out and Out (season) only; Doubtful, Questionable and Out 1st half are listed but not counted.

The board fetches `injuries.json` when the tab opens, so report updates don't require rebuilding the pages.
