"""One-off probe: fetch candidate injury / depth-chart sources and save what comes back."""
import json, os, re, urllib.request
OUT = "probe/out"; os.makedirs(OUT, exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (gameday-boards probe)"}
E = "https://site.api.espn.com/apis/site/v2/sports/football/college-football"
C = "https://sports.core.api.espn.com/v2/sports/football/leagues/college-football"
URLS = {
  "espn_site_injuries_87": f"{E}/teams/87/injuries",
  "espn_site_injuries_61": f"{E}/teams/61/injuries",
  "espn_core_injuries_61": f"{C}/teams/61/injuries",
  "espn_site_depth_61": f"{E}/teams/61/depthcharts",
  "espn_core_depth_61": f"{C}/seasons/2026/teams/61/depthcharts",
  "espn_core_depth_87": f"{C}/seasons/2026/teams/87/depthcharts",
  "espn_roster_61": f"{E}/teams/61/roster",
  "espn_summary_uga_miss": f"{E}/summary?event=401856741",
  "espn_summary_nd_mia": f"{E}/summary?event=401858291",
  "sec_fbreports": "https://www.secsports.com/fbreports",
  "bigten_fb": "https://bigten.org/fb/",
  "bigten_avail": "https://bigten.org/fb/availability-reports/",
  "acc_short": "https://theacc.co/fbreporting",
  "acc_policy": "https://theacc.com/sports/2025/8/28/availability-reporting.aspx",
  "big12_policy": "https://big12sports.com/sports/2025/8/21/availability-reporting.aspx",
}
idx = {}
for k, u in URLS.items():
    try:
        r = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=30)
        body = r.read().decode("utf-8", "replace"); st = r.status; final = r.geturl()
    except Exception as e:
        body, st, final = str(e), getattr(e, "code", None), u
    links = sorted(set(re.findall(r'(?:href|src)="([^"]*(?:vailab|report|depth|injur)[^"]*)"', body, re.I)))[:80]
    idx[k] = {"url": u, "final": final, "status": st, "bytes": len(body), "links": links}
    open(f"{OUT}/{k}.txt", "w").write(body[:400000])
json.dump(idx, open(f"{OUT}/index.json", "w"), indent=1)
