"""Build the GitHub Pages site: one standalone page per team plus an index.

Usage (from pipeline/): python site.py [outdir]   default outdir is the repo root (..)
Reads the team list from teams.json and data_<id>.json files written by fetch.py.
Removes team pages for teams no longer in teams.json.
Each page posts its height to the parent window so the WordPress embed can size itself.
"""
import json, os, subprocess, sys, html

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, ".."))
CFG = json.load(open(os.path.join(HERE, "teams.json")))
TEAMS = [(t["id"], t["slug"], t["name"]) for t in CFG["teams"]]

HEAD = ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<style>html,body{margin:0}</style></head><body>\n')

# Report page height to the embedding page (WordPress) so its iframe can fit the content.
RESIZE = """<script>
(function(){
  var last=0;
  function post(){var h=document.documentElement.scrollHeight;
    if(h!==last){last=h;try{parent.postMessage({gameday:location.pathname,height:h},'*')}catch(e){}}}
  window.addEventListener('load',post);
  if(window.ResizeObserver)new ResizeObserver(post).observe(document.body);
  setInterval(post,1000);
})();
</script>
"""

os.makedirs(OUT, exist_ok=True)
keep = {"index.html"}
for tid, slug, _ in TEAMS:
    tmp = os.path.join(HERE, f".{slug}.body.html")
    subprocess.run([sys.executable, "build.py", f"data_{tid}.json", tmp], check=True, cwd=HERE)
    body = open(tmp).read()
    os.remove(tmp)
    with open(os.path.join(OUT, f"{slug}.html"), "w") as f:
        f.write(HEAD + body + RESIZE + "</body></html>\n")
    keep.add(f"{slug}.html")

# Drop pages for teams that left the list.
for fn in os.listdir(OUT):
    if fn.endswith(".html") and fn not in keep:
        os.remove(os.path.join(OUT, fn))
        print("removed", fn)

links = "\n".join(f'<li><a href="{s}.html">{html.escape(n)}</a></li>' for _, s, n in TEAMS)
with open(os.path.join(OUT, "index.html"), "w") as f:
    f.write(HEAD.replace("</style>", "body{font:16px system-ui,sans-serif;padding:24px;max-width:640px}</style>")
            + "<title>Gameday Boards</title><h1>Gameday Boards</h1>"
            + f"<p>College football dashboards: {html.escape(CFG['poll'])}. Refreshed weekly.</p>"
            + f"<ol>{links}</ol></body></html>\n")
open(os.path.join(OUT, ".nojekyll"), "w").close()
print("built", len(TEAMS), "team pages in", OUT)
