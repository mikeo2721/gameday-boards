"""Build the GitHub Pages site: one standalone page per team plus an index.

Usage: python site.py [outdir]   (expects data_<id>.json files from fetch.py)
Each page posts its height to the parent window so the WordPress embed can size itself.
"""
import json, os, subprocess, sys, html

OUT = sys.argv[1] if len(sys.argv) > 1 else "site"

# AP Top 10, week 6 poll (fixed set). id -> (slug, display name)
TEAMS = [
    (251, "texas", "Texas Longhorns"),
    (61, "georgia", "Georgia Bulldogs"),
    (87, "notre-dame", "Notre Dame Fighting Irish"),
    (2390, "miami", "Miami Hurricanes"),
    (194, "ohio-state", "Ohio State Buckeyes"),
    (333, "alabama", "Alabama Crimson Tide"),
    (84, "indiana", "Indiana Hoosiers"),
    (252, "byu", "BYU Cougars"),
    (145, "ole-miss", "Ole Miss Rebels"),
    (99, "lsu", "LSU Tigers"),
]

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
for tid, slug, _ in TEAMS:
    tmp = os.path.join(OUT, f".{slug}.body.html")
    subprocess.run([sys.executable, "build.py", f"data_{tid}.json", tmp], check=True)
    body = open(tmp).read()
    os.remove(tmp)
    with open(os.path.join(OUT, f"{slug}.html"), "w") as f:
        f.write(HEAD + body + RESIZE + "</body></html>\n")

links = "\n".join(f'<li><a href="{s}.html">{html.escape(n)}</a></li>' for _, s, n in TEAMS)
with open(os.path.join(OUT, "index.html"), "w") as f:
    f.write(HEAD.replace("</style>", "body{font:16px system-ui,sans-serif;padding:24px;max-width:640px}</style>")
            + "<title>Gameday Boards</title><h1>Gameday Boards</h1>"
            + "<p>College football dashboards for the AP Top 10 (week 6 poll). Refreshed weekly.</p>"
            + f"<ul>{links}</ul></body></html>\n")
open(os.path.join(OUT, ".nojekyll"), "w").close()
print("built", len(TEAMS), "team pages in", OUT)
