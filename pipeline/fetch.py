"""Pull a team's college football data (current + prior seasons) via sportsdataverse
and write data.json for the dashboard.

Data comes from the SportsDataverse data releases on GitHub (ESPN-sourced, EPA-processed),
not live ESPN calls, so it typically lags real games by roughly a day.

Usage: python fetch.py [--team-id 251 [87 ...]] [--seasons 2024 2025 2026] [--out data.json]
  Team ids: Texas 251, Notre Dame 87 (full list in README).
  With several team ids, --out must contain {id} (default data_{id}.json); season-wide
  files (schedule, pbp, box scores) are downloaded once and shared across teams.
"""
import argparse, json, datetime as dt, functools
import polars as pl
import sportsdataverse.cfb as cfb


def num(s):
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def split_pair(s):  # "26/34" or "11-15"
    if not s:
        return (0, 0)
    for sep in ("/", "-"):
        if sep in s:
            a, b = s.split(sep, 1)
            try:
                return (int(a), int(b))
            except ValueError:
                return (0, 0)
    return (0, 0)


# Season-wide loaders are cached so several teams in one run share one download.
_sched = functools.lru_cache(None)(lambda s: cfb.load_cfb_schedule([s]))
_pbp = functools.lru_cache(None)(lambda s: cfb.load_cfb_pbp([s]).filter(pl.col("scrimmage_play") == True).select(
    ["game_id", "pos_team_id", "def_pos_team_id", "EPA", "EPA_success", "EPA_explosive", "pass", "rush"]))
_tbox = functools.lru_cache(None)(lambda s: cfb.load_cfb_team_box([s]))
_pbox = functools.lru_cache(None)(lambda s: cfb.load_cfb_player_box([s]))


# --- unit rankings: traditional per-game / per-attempt stats ranked among FBS teams ---
# (key, label, group, higher_is_better or None for neutral counts, format)
UNIT_STATS = [
    ("off_ypg", "Total offense", "Offense & defense", True, "ypg"),
    ("def_ypg", "Total defense", "Offense & defense", False, "ypg"),
    ("off_pass", "Passing offense", "Offense & defense", True, "ypg"),
    ("def_pass", "Passing defense", "Offense & defense", False, "ypg"),
    ("off_rush", "Rushing offense", "Offense & defense", True, "ypg"),
    ("def_rush", "Rushing defense", "Offense & defense", False, "ypg"),
    ("st_ret", "Return game (kick + punt)", "Special teams", True, "ypr"),
    ("st_cov", "Return coverage (kick + punt)", "Special teams", False, "ypr"),
    ("punt_avg", "Punting (gross avg)", "Special teams", True, "ypp"),
    ("pr_avg", "Punt returns", "Special teams", True, "ypr"),
    ("kr_avg", "Kickoff returns", "Special teams", True, "ypr"),
    ("fga", "Field goals attempted", "Kicking", None, "fg"),
    ("fgm", "Field goals made", "Kicking", True, "fg"),
    ("fgx", "Field goals missed", "Kicking", False, "fg"),
]


def _f(col):
    return pl.col(col).cast(pl.Float64, strict=False).fill_null(0)


@functools.lru_cache(None)
def _unit_table(season):
    """One row per FBS team with the raw totals behind UNIT_STATS (both sides of every game)."""
    sched = _sched(season)
    fbs = set(sched.filter(pl.col("home_division") == "fbs")["home_id"].to_list()
              + sched.filter(pl.col("away_division") == "fbs")["away_id"].to_list())
    tb = _tbox(season).select(
        pl.col("game_id"), pl.col("team_id").cast(pl.Int64),
        _f("totalYards").alias("yds"), _f("netPassingYards").alias("pass"), _f("rushingYards").alias("rush"))
    pb = _pbox(season).with_columns(pl.col("team_id").cast(pl.Int64))
    fg = pb.filter(pl.col("category") == "kicking").with_columns(
        pl.col("fieldGoalsMade/fieldGoalAttempts").str.split("/").alias("_fg"))
    fg = fg.with_columns(pl.col("_fg").list.get(0, null_on_oob=True).cast(pl.Float64, strict=False).fill_null(0).alias("fgm"),
                         pl.col("_fg").list.get(1, null_on_oob=True).cast(pl.Float64, strict=False).fill_null(0).alias("fga"))
    per = [
        pb.filter(pl.col("category") == "kickReturns").group_by("game_id", "team_id").agg(
            _f("kickReturns").sum().alias("kr"), _f("kickReturnYards").sum().alias("kr_yds")),
        pb.filter(pl.col("category") == "puntReturns").group_by("game_id", "team_id").agg(
            _f("puntReturns").sum().alias("pr"), _f("puntReturnYards").sum().alias("pr_yds")),
        pb.filter(pl.col("category") == "punting").group_by("game_id", "team_id").agg(
            _f("punts").sum().alias("punts"), _f("puntYards").sum().alias("punt_yds")),
        fg.group_by("game_id", "team_id").agg(pl.col("fgm").sum(), pl.col("fga").sum()),
    ]
    g = tb
    for d in per:
        g = g.join(d, on=["game_id", "team_id"], how="left")
    g = g.fill_null(0)
    # opponent side of the same game, for defense and return coverage
    opp = g.select(pl.col("game_id"), pl.col("team_id").alias("opp_id"), pl.col("yds").alias("o_yds"),
                   pl.col("pass").alias("o_pass"), pl.col("rush").alias("o_rush"),
                   pl.col("kr").alias("o_kr"), pl.col("kr_yds").alias("o_kr_yds"),
                   pl.col("pr").alias("o_pr"), pl.col("pr_yds").alias("o_pr_yds"))
    g = g.join(opp, on="game_id").filter(pl.col("team_id") != pl.col("opp_id"))
    sums = [c for c in g.columns if c not in ("game_id", "team_id", "opp_id")]
    t = g.group_by("team_id").agg(pl.len().alias("gp"), *[pl.col(c).sum() for c in sums])
    return t.filter(pl.col("team_id").is_in(list(fbs)) & (pl.col("gp") > 0))


def unit_ranks(team_id, season):
    t = _unit_table(season)
    div = lambda a, b: pl.when(pl.col(b) > 0).then(pl.col(a) / pl.col(b)).otherwise(None)
    t = t.with_columns(
        (pl.col("yds") / pl.col("gp")).alias("off_ypg"), (pl.col("o_yds") / pl.col("gp")).alias("def_ypg"),
        (pl.col("pass") / pl.col("gp")).alias("off_pass"), (pl.col("o_pass") / pl.col("gp")).alias("def_pass"),
        (pl.col("rush") / pl.col("gp")).alias("off_rush"), (pl.col("o_rush") / pl.col("gp")).alias("def_rush"),
        (pl.col("kr_yds") + pl.col("pr_yds")).alias("_ret_yds"), (pl.col("kr") + pl.col("pr")).alias("_ret"),
        (pl.col("o_kr_yds") + pl.col("o_pr_yds")).alias("_cov_yds"), (pl.col("o_kr") + pl.col("o_pr")).alias("_cov"),
        div("punt_yds", "punts").alias("punt_avg"), div("pr_yds", "pr").alias("pr_avg"), div("kr_yds", "kr").alias("kr_avg"),
        (pl.col("fga") / pl.col("gp")).alias("fga_pg"), (pl.col("fgm") / pl.col("gp")).alias("fgm_pg"),
        ((pl.col("fga") - pl.col("fgm")) / pl.col("gp")).alias("fgx_pg"),
    ).with_columns(div("_ret_yds", "_ret").alias("st_ret"), div("_cov_yds", "_cov").alias("st_cov"))
    me = t.filter(pl.col("team_id") == team_id)
    if not me.height:
        return None
    me = me.to_dicts()[0]
    rows = []
    for key, label, group, better, fmt in UNIT_STATS:
        rank_col = {"fga": "fga_pg", "fgm": "fgm_pg", "fgx": "fgx_pg"}.get(key, key)
        v = me[rank_col]
        col = t.filter(pl.col(rank_col).is_not_null())[rank_col]
        if v is None or not col.len():
            rows.append({"key": key, "label": label, "group": group, "better": better, "fmt": fmt, "value": None})
            continue
        desc = better is not False   # neutral counts rank most-first
        ahead = int((col > v).sum()) if desc else int((col < v).sum())
        rank = ahead + 1
        tied = int((col == v).sum()) > 1
        row = {"key": key, "label": label, "group": group, "better": better, "fmt": fmt,
               "value": v, "rank": rank, "tied": tied, "n": col.len()}
        if fmt == "fg":
            row.update({"total": int(me["fga"] if key == "fga" else me["fgm"] if key == "fgm" else me["fga"] - me["fgm"]),
                        "pct": me["fgm"] / me["fga"] if me["fga"] else None})
        if fmt == "ypr":
            row["att"] = int({"st_ret": me["_ret"], "st_cov": me["_cov"], "pr_avg": me["pr"], "kr_avg": me["kr"]}[key])
        if fmt == "ypp":
            row["att"] = int(me["punts"])
        rows.append(row)
    return {"gp": me["gp"], "rows": rows}


def season_block(team_id, season):
    sched = _sched(season)
    fbs_ids = set(
        sched.filter(pl.col("home_division") == "fbs")["home_id"].to_list()
        + sched.filter(pl.col("away_division") == "fbs")["away_id"].to_list()
    )
    tg = sched.filter((pl.col("home_id") == team_id) | (pl.col("away_id") == team_id)).sort("start_date")

    games = []
    for g in tg.iter_rows(named=True):
        home = g["home_id"] == team_id
        pf, pa = (g["home_points"], g["away_points"]) if home else (g["away_points"], g["home_points"])
        games.append({
            "game_id": g["game_id"], "week": g["week"], "season_type": g["season_type"],
            "date": g["start_date"], "completed": bool(g["completed"]),
            "home": home, "neutral": bool(g["neutral_site"]), "conf": bool(g["conference_game"]),
            "opp": g["away_team"] if home else g["home_team"],
            "opp_abbr": g["away_abbreviation"] if home else g["home_abbreviation"],
            "opp_rank": g["away_rank"] if home else g["home_rank"],
            "rank": g["home_rank"] if home else g["away_rank"],
            "pf": pf, "pa": pa,
            "result": None if not g["completed"] else ("W" if pf > pa else "L"),
            "bowl": g.get("playoff_bowl_name") or (g.get("notes") if g["season_type"] in (3, "postseason") else None),
            "venue": g["venue"],
        })
    team_name = None
    r0 = tg.row(0, named=True) if tg.height else None
    if r0:
        team_name = r0["home_team"] if r0["home_id"] == team_id else r0["away_team"]

    # --- play-by-play efficiency (EPA) for every FBS team, to rank our team ---
    pbp = _pbp(season)
    off = pbp.group_by("pos_team_id").agg(
        pl.len().alias("plays"), pl.col("EPA").mean().alias("epa"),
        pl.col("EPA_success").mean().alias("sr"), pl.col("EPA_explosive").mean().alias("xr"),
        pl.col("EPA").filter(pl.col("pass") == True).mean().alias("epa_pass"),
        pl.col("EPA").filter(pl.col("rush") == True).mean().alias("epa_rush"),
    ).rename({"pos_team_id": "team_id"})
    de = pbp.group_by("def_pos_team_id").agg(
        pl.col("EPA").mean().alias("d_epa"), pl.col("EPA_success").mean().alias("d_sr"),
        pl.col("EPA_explosive").mean().alias("d_xr"),
        pl.col("EPA").filter(pl.col("pass") == True).mean().alias("d_epa_pass"),
        pl.col("EPA").filter(pl.col("rush") == True).mean().alias("d_epa_rush"),
    ).rename({"def_pos_team_id": "team_id"})
    eff = off.join(de, on="team_id").filter(pl.col("team_id").is_in(list(fbs_ids)) & (pl.col("plays") >= 100))
    n_fbs = eff.height
    eff = eff.with_columns(
        pl.col("epa").rank("ordinal", descending=True).alias("epa_rk"),
        pl.col("sr").rank("ordinal", descending=True).alias("sr_rk"),
        pl.col("d_epa").rank("ordinal", descending=False).alias("d_epa_rk"),
        pl.col("d_sr").rank("ordinal", descending=False).alias("d_sr_rk"),
        (pl.col("epa") - pl.col("d_epa")).alias("net_epa"),
    ).with_columns(pl.col("net_epa").rank("ordinal", descending=True).alias("net_rk"))
    mine = eff.filter(pl.col("team_id") == team_id)
    efficiency = mine.to_dicts()[0] if mine.height else None
    if efficiency:
        efficiency["n_fbs"] = n_fbs

    # per-game EPA
    tgp = pbp.filter((pl.col("pos_team_id") == team_id) | (pl.col("def_pos_team_id") == team_id))
    pg_off = tgp.filter(pl.col("pos_team_id") == team_id).group_by("game_id").agg(
        pl.col("EPA").mean().alias("off_epa"), pl.col("EPA_success").mean().alias("off_sr"))
    pg_def = tgp.filter(pl.col("def_pos_team_id") == team_id).group_by("game_id").agg(
        pl.col("EPA").mean().alias("def_epa"), pl.col("EPA_success").mean().alias("def_sr"))
    pg = {r["game_id"]: r for r in pg_off.join(pg_def, on="game_id", how="full", coalesce=True).to_dicts()}

    # --- team box per game ---
    tb = _tbox(season)
    game_ids = [g["game_id"] for g in games]
    tbx = tb.filter(pl.col("game_id").is_in(game_ids))
    box = {}
    for r in tbx.iter_rows(named=True):
        side = "us" if r["team_id"] == team_id else "them"
        box.setdefault(r["game_id"], {})[side] = {
            "yards": num(r["totalYards"]), "pass": num(r["netPassingYards"]),
            "rush": num(r["rushingYards"]), "to": num(r["turnovers"]),
            "third": split_pair(r["thirdDownEff"]), "pen": r["totalPenaltiesYards"],
            "top": r["possessionTime"],
        }
    for g in games:
        g["box"] = box.get(g["game_id"])
        e = pg.get(g["game_id"])
        g["off_epa"] = e["off_epa"] if e else None
        g["def_epa"] = e["def_epa"] if e else None
        g["off_sr"] = e["off_sr"] if e else None
        g["def_sr"] = e["def_sr"] if e else None

    done = [g for g in games if g["completed"] and g["pf"] is not None]
    w = sum(g["result"] == "W" for g in done)
    cw = sum(g["result"] == "W" for g in done if g["conf"])
    cl = sum(g["result"] == "L" for g in done if g["conf"])
    to_us = sum((g["box"] or {}).get("us", {}).get("to") or 0 for g in done)
    to_them = sum((g["box"] or {}).get("them", {}).get("to") or 0 for g in done)
    t3 = [sum((g["box"] or {}).get("us", {}).get("third", (0, 0))[i] for g in done) for i in (0, 1)]
    yds = [sum(((g["box"] or {}).get(k, {}).get("yards") or 0) for g in done) for k in ("us", "them")]
    summary = {
        "season": season, "team": team_name, "games": len(done), "w": w, "l": len(done) - w,
        "cw": cw, "cl": cl,
        "ppg": sum(g["pf"] for g in done) / len(done) if done else None,
        "opp_ppg": sum(g["pa"] for g in done) / len(done) if done else None,
        "ypg": yds[0] / len(done) if done else None, "opp_ypg": yds[1] / len(done) if done else None,
        "to_margin": to_them - to_us, "third_pct": t3[0] / t3[1] if t3[1] else None,
    }

    # --- player leaders (season totals from player box) ---
    pb = _pbox(season).filter(
        (pl.col("team_id") == team_id) & pl.col("game_id").is_in(game_ids))

    def agg(cat, cols):
        d = pb.filter(pl.col("category") == cat)
        out = {}
        for r in d.iter_rows(named=True):
            k = r["athlete_id"]
            if not r["athlete_name"] or r["athlete_name"].strip().lower() == "team":
                continue
            o = out.setdefault(k, {"id": k, "name": r["athlete_name"], "jersey": r["jersey"], "gp": 0})
            o["gp"] += 1
            for c in cols:
                if c == "completions/passingAttempts":
                    a, b = split_pair(r[c])
                    o["cmp"] = o.get("cmp", 0) + a
                    o["att"] = o.get("att", 0) + b
                else:
                    o[c] = o.get(c, 0) + (num(r[c]) or 0)
        return list(out.values())

    passing = sorted(agg("passing", ["completions/passingAttempts", "passingYards", "passingTouchdowns", "interceptions"]),
                     key=lambda x: -x.get("passingYards", 0))[:3]
    rushing = sorted(agg("rushing", ["rushingAttempts", "rushingYards", "rushingTouchdowns"]),
                     key=lambda x: -x.get("rushingYards", 0))[:5]
    receiving = sorted(agg("receiving", ["receptions", "receivingYards", "receivingTouchdowns"]),
                       key=lambda x: -x.get("receivingYards", 0))[:5]
    defense = sorted(agg("defensive", ["totalTackles", "sacks", "tacklesForLoss", "passesDefended"]),
                     key=lambda x: -x.get("totalTackles", 0))[:6]
    ints = agg("interceptions", ["interceptions"])
    imap = {x["id"]: x["interceptions"] for x in ints}
    for d in defense:
        d["ints"] = imap.get(d["id"], 0)

    return {"summary": summary, "efficiency": efficiency, "units": unit_ranks(team_id, season), "games": games,
            "leaders": {"passing": passing, "rushing": rushing, "receiving": receiving, "defense": defense}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--team-id", type=int, nargs="+", default=[251])
    ap.add_argument("--seasons", type=int, nargs="+")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    out = a.out or ("data.json" if len(a.team_id) == 1 else "data_{id}.json")
    if len(a.team_id) > 1 and "{id}" not in out:
        ap.error("with several --team-id values, --out must contain {id}")
    seasons = a.seasons or [cfb.most_recent_cfb_season() - i for i in (2, 1, 0)]
    all_teams = cfb.load_cfb_teams([seasons[-1]])
    for team_id in a.team_id:
        teams = all_teams.filter(pl.col("team_id") == team_id).to_dicts()
        t = teams[0] if teams else {}
        meta = {"school": t.get("school") or t.get("location"), "mascot": t.get("mascot") or t.get("name"),
                "conf": t.get("conference_short_name") or t.get("conference_abbreviation", "").upper(),
                "independent": "independent" in (t.get("conference_name") or "").lower(),
                "color": t.get("color"), "alt_color": t.get("alternate_color")}
        data = {"team_id": team_id, "meta": meta,
                "generated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="minutes"), "seasons": {}}
        for s in seasons:
            print(team_id, "season", s)
            data["seasons"][str(s)] = season_block(team_id, s)
        path = out.format(id=team_id)
        with open(path, "w") as f:
            json.dump(data, f, default=str)
        print("wrote", path)


if __name__ == "__main__":
    main()
