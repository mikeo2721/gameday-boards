# Gameday Boards

College football dashboards for the AP Top 10 (week 6 poll), one page per team, refreshed weekly.
Embedded on https://oneilltexas.com/sports/sports-stats/.

Data: ESPN data via the SportsDataverse data releases (EPA-processed). Pipeline code is in `pipeline/`:
`fetch.py` pulls data, `build.py` fills `template.html`, `site.py` writes the team pages to the repo root.
