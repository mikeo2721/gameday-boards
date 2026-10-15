# Gameday Boards

College football dashboards, one page per team, refreshed weekly (Sunday mornings, Central).
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
