"""Inject a data JSON into template.html.

Usage: python build.py [data.json] [dashboard.html] [helmet.png]
Picks the page title and color theme from the team id in the data file.
The optional third argument is the helmet image URL (relative to the page); without it
the header is text-only.
"""
import json, sys

data_path = sys.argv[1] if len(sys.argv) > 1 else "data.json"
out_path = sys.argv[2] if len(sys.argv) > 2 else "dashboard.html"
helmet = sys.argv[3] if len(sys.argv) > 3 else ""

# Per-team page names and color themes. Unlisted teams get the Texas palette and a mascot title.
THEMES = {
    251: {"title": "Longhorns Gameday Board", "css": ""},
    87: {"title": "Fighting Irish Gameday Board", "css": """
:root{--bg:#f2f4f7;--surface:#ffffff;--ink:#0f1a2b;--muted:#5b6678;--line:#dbe0e8;
  --orange:#0c2340;--on-accent:#ffffff;--bar-neutral:#c3cad6;--name:#9a7600}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){
  --bg:#0d131c;--surface:#151d29;--ink:#e9edf3;--muted:#98a3b4;--line:#2a3545;
  --orange:#d4a72c;--on-accent:#0d131c;--bar-neutral:#475468;--name:#d4a72c}}
:root[data-theme="dark"]{--bg:#0d131c;--surface:#151d29;--ink:#e9edf3;--muted:#98a3b4;--line:#2a3545;
  --orange:#d4a72c;--on-accent:#0d131c;--bar-neutral:#475468;--name:#d4a72c}
header.top{border-bottom-color:#c99700}
"""},
}



def theme(light_accent, light_name, dark_accent, dark_name, rule, dark_on_accent="#0f141b"):
    """Neutral cool-gray page with a team accent (buttons, rules, offense line) and name color."""
    return {"css": f"""
:root{{--bg:#f3f4f6;--surface:#ffffff;--ink:#14181f;--muted:#5d6470;--line:#dde0e5;
  --orange:{light_accent};--on-accent:#ffffff;--bar-neutral:#c5cad2;--name:{light_name}}}
@media (prefers-color-scheme: dark){{:root:not([data-theme="light"]){{
  --bg:#111418;--surface:#1a1e24;--ink:#eceef1;--muted:#9aa1ac;--line:#2c323a;
  --orange:{dark_accent};--on-accent:{dark_on_accent};--bar-neutral:#4a515c;--name:{dark_name}}}}}
:root[data-theme="dark"]{{--bg:#111418;--surface:#1a1e24;--ink:#eceef1;--muted:#9aa1ac;--line:#2c323a;
  --orange:{dark_accent};--on-accent:{dark_on_accent};--bar-neutral:#4a515c;--name:{dark_name}}}
header.top{{border-bottom-color:{rule}}}
"""}


# AP Top 10 added Oct 2026 (week 6 poll). Accent = buttons/rules/offense line; name = school name.
THEMES.update({
    61:   {"title": "Bulldogs Gameday Board", **theme("#ba0c2f", "#ba0c2f", "#f05a6e", "#f05a6e", "#000000")},
    2390: {"title": "Hurricanes Gameday Board", **theme("#005030", "#c95a12", "#f47321", "#f47321", "#f47321")},
    194:  {"title": "Buckeyes Gameday Board", **theme("#bb0000", "#bb0000", "#ff5c5c", "#ff5c5c", "#666666")},
    333:  {"title": "Crimson Tide Gameday Board", **theme("#9e1b32", "#9e1b32", "#e86a80", "#e86a80", "#828a8f")},
    84:   {"title": "Hoosiers Gameday Board", **theme("#990000", "#990000", "#f06060", "#f06060", "#990000")},
    252:  {"title": "Cougars Gameday Board", **theme("#002e5d", "#0062b8", "#6aaee8", "#6aaee8", "#0062b8")},
    145:  {"title": "Rebels Gameday Board", **theme("#14213d", "#ce1126", "#6cace4", "#f2566a", "#ce1126")},
    99:   {"title": "Tigers Gameday Board", **theme("#461d7c", "#461d7c", "#fdd023", "#fdd023", "#fdd023")},
    2641: {"title": "Red Raiders Gameday Board", **theme("#cc0000", "#cc0000", "#ff5a5a", "#ff5a5a", "#000000")},
})

tpl = open("template.html").read()
data = json.load(open(data_path))
th = THEMES.get(data.get("team_id"))
if th is None:  # unlisted team: Texas palette, title from the mascot
    th = {"title": f"{(data.get('meta') or {}).get('mascot') or 'Team'} Gameday Board", "css": ""}
blob = json.dumps(data, separators=(",", ":")).replace("</", "<\\/")
helmet_tag = (f'<img class="helmet" src="{helmet}" alt="" width="290" height="220">' if helmet else "")
html = tpl.replace("<!--HELMET-->", helmet_tag).replace("__TITLE__", th["title"]).replace("/*THEME*/", th["css"]).replace("__DATA__", blob)
open(out_path, "w").write(html)
print("wrote", out_path, len(blob), "bytes of data")
