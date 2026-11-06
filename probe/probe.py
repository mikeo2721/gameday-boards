"""Probe 2: hdintelligence availability app, Big 12 page, ESPN starter flags."""
import json, os, re, urllib.request, urllib.parse
OUT = "probe/out2"; os.makedirs(OUT, exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (gameday-boards probe)"}
E = "https://site.api.espn.com/apis/site/v2/sports/football/college-football"
def get(u):
    try:
        r = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=30)
        return r.status, r.geturl(), r.read().decode("utf-8", "replace")
    except Exception as e:
        return getattr(e, "code", None), u, str(e)
idx = {}
def save(k, u):
    st, fin, b = get(u); idx[k] = {"url": u, "final": fin, "status": st, "bytes": len(b)}
    open(f"{OUT}/{k}.txt", "w").write(b[:2000000]); return b
app = save("hdi_sec", "https://app.hdintelligence.com/?source=SEC&sport=Football&conf=SEC&type=report")
# pull every script referenced by the app and save it, so API endpoints can be found
for i, s in enumerate(sorted(set(re.findall(r'<script[^>]+src="([^"]+)"', app)))[:12]):
    save(f"hdi_js_{i}", urllib.parse.urljoin("https://app.hdintelligence.com/", s))
save("big12_fb", "https://big12sports.com/sports/2025/8/14/FBreporting.aspx")
save("espn_summary_done", f"{E}/summary?event=401858282")
json.dump(idx, open(f"{OUT}/index.json", "w"), indent=1)
