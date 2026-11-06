"""Pull conference availability reports for every team in teams.json and write ../injuries.json.

Runs in GitHub Actions (.github/workflows/injuries.yml); the conference feeds are not reachable
from every network. Usage (from pipeline/): python injuries.py [out_path]

Source: the SEC, Big Ten, ACC and Big 12 all publish their football availability reports through the
same vendor app (app.hdintelligence.com), embedded on each conference's website. Its public endpoint
returns the latest published report for every conference game of the current week, with the full
travel roster (position, jersey, name, status). Reports exist for conference games only.

injuries_manual.json covers everything else (independents such as Notre Dame, non-conference games)
and overrides the official report player by player. Format:
  {"<team id>": {"opponent": "Miami", "game_date": "2026-11-07", "note": "Coach's Thursday presser",
                 "replace": false,
                 "players": [{"name": "Malachi Toney", "pos": "WR", "jersey": "1", "status": "Out"}]}}
"replace": true drops the official report for that team and uses only the manual list.
A manual entry is ignored once its game_date is in the past.
"""
import datetime as dt, json, os, re, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "injuries.json")
API = "https://app.hdintelligence.com/api/get-publish-public"
CONFS = {"SEC": "SEC", "B10": "Big Ten", "ACC": "ACC", "B12": "Big 12"}
KEEP_STATUSES = {"Out", "Out - (1st Half)", "Doubtful", "Questionable", "Probable", "Exempt"}
ST_POS = {"LS", "DS", "SN"}  # long snappers are kept even when Available, to fill the special-teams starter list
# Report team names that don't normalize to the ESPN school name.
ALIASES = {145: ["Mississippi"], 2390: ["Miami (FL)", "Miami FL"]}


def norm(s):
    s = (s or "").lower().replace("&", "and")
    s = re.sub(r"\bst\.?(?=\s|$)", "state", s)
    return re.sub(r"[^a-z0-9]", "", s)


def fetch(conf):
    body = json.dumps({"sport": "Football", "organization": conf, "conference": conf}).encode()
    req = urllib.request.Request(API, data=body, headers={
        "Content-Type": "application/json", "User-Agent": "gameday-boards (github.com/mikeo2721/gameday-boards)",
        "Origin": "https://app.hdintelligence.com"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def parse_name(s):  # "LB #0 Owen Chambliss" -> ("LB", "0", "Owen Chambliss")
    m = re.match(r"^(\S+)\s+#(\S+)\s+(.+)$", s.strip())
    if m:
        return m.group(1), m.group(2), m.group(3).strip()
    m = re.match(r"^(\S+)\s+(.+)$", s.strip())
    return (m.group(1), None, m.group(2).strip()) if m else (None, None, s.strip())


def main():
    teams = json.load(open(os.path.join(HERE, "teams.json")))["teams"]
    want = {}
    for t in teams:
        school = t["name"].rsplit(" ", 1)[0]
        for n in [school, t["name"], *t.get("report_names", []), *ALIASES.get(t["id"], [])]:
            want[norm(n)] = t["id"]
        # multi-word mascots ("Crimson Tide", "Fighting Irish", "Red Raiders"): also try the first word(s)
        for k in range(1, len(t["name"].split())):
            want.setdefault(norm(" ".join(t["name"].split()[:k])), t["id"])

    found, errors, failed = {}, [], set()
    for conf, label in CONFS.items():
        try:
            reports = fetch(conf)
        except Exception as e:  # one conference failing should not wipe the others
            errors.append(f"{label}: {e}")
            failed.add(label)
            continue
        for rep in reports.values():
            games = rep.get("games") or []
            for i, g in enumerate(games):
                tid = want.get(norm(g.get("teamName"))) or want.get(norm(g.get("teamDisplayName")))
                if tid is None:
                    continue
                opp = games[1 - i] if len(games) == 2 else {}
                players = []
                for r in g.get("rows") or []:
                    pos, jersey, name = parse_name(r.get("name", ""))
                    status = r.get("status")
                    if r.get("exemptStatus") == "Out" and status == "Out":
                        status = "Out (season)"
                    if status in KEEP_STATUSES or status == "Out (season)" or (pos or "").upper() in ST_POS:
                        players.append({"pos": pos, "jersey": jersey, "name": name, "status": status})
                foot = rep.get("footer") or {}
                entry = {"source": label, "report_type": rep.get("ReportType"),
                         "published": f"{rep.get('publishDate')} {rep.get('postedTime') or ''}".strip(),
                         "tz": rep.get("conferenceTimeZone"), "game_date": foot.get("date"),
                         "game_time": foot.get("time"), "location": foot.get("location"),
                         "opponent": opp.get("teamDisplayName") or opp.get("teamName"),
                         "roster_size": len(g.get("rows") or []), "players": players}
                prev = found.get(tid)  # keep the newest report if a team somehow appears twice
                if not prev or (entry["published"], entry["report_type"] or "") > (prev["published"], prev["report_type"] or ""):
                    found[tid] = entry

    manual_path = os.path.join(HERE, "injuries_manual.json")
    manual = json.load(open(manual_path)) if os.path.exists(manual_path) else {}
    today = dt.date.today().isoformat()
    for k, m in manual.items():
        if k.startswith("_") or (m.get("game_date") and m["game_date"] < today):
            continue
        if not m.get("players") and not m.get("note"):  # empty placeholder: not a report
            continue
        tid = int(k)
        base = found.get(tid)
        mp = [{**p, "manual": True} for p in m.get("players", [])]
        if base and not m.get("replace"):
            names = {norm(p["name"]) for p in mp}
            base["players"] = [p for p in base["players"] if norm(p["name"]) not in names] + mp
            base["manual_note"] = m.get("note")
        else:
            found[tid] = {"source": "Manual", "report_type": None, "published": m.get("updated"), "tz": "CT",
                          "game_date": m.get("game_date"), "game_time": None, "location": None,
                          "opponent": m.get("opponent"), "roster_size": None, "players": mp,
                          "manual_note": m.get("note")}

    out = {"teams": {str(t["id"]): found.get(t["id"]) for t in teams}, "errors": errors}
    old = json.load(open(OUT)) if os.path.exists(OUT) else None
    if old and failed:  # keep last good data for teams whose conference feed failed this run
        for t in teams:
            k, prev = str(t["id"]), (old.get("teams") or {}).get(str(t["id"]))
            if out["teams"][k] is None and prev and prev.get("source") in failed:
                out["teams"][k] = prev
    if old and {k: v for k, v in old.items() if k != "updated"} == out:
        print("no change"); return
    out["updated"] = dt.datetime.now(dt.timezone.utc).isoformat(timespec="minutes")
    with open(OUT, "w") as f:
        json.dump(out, f, indent=1)
    print("wrote", OUT, {k: (len(v["players"]) if v else None) for k, v in out["teams"].items()}, errors or "")


if __name__ == "__main__":
    main()
