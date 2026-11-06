"""Probe 4: published availability reports for all four conferences."""
import json, os, urllib.request
OUT = "probe/out4"; os.makedirs(OUT, exist_ok=True)
B = "https://app.hdintelligence.com"
for conf in ("SEC", "B10", "ACC", "B12"):
    for ep in ("get-publish-public", "get-archive-public"):
        H = {"User-Agent": "Mozilla/5.0 (gameday-boards probe)", "Content-Type": "application/json", "Origin": B}
        body = json.dumps({"sport": "Football", "organization": conf, "conference": conf}).encode()
        try:
            r = urllib.request.urlopen(urllib.request.Request(f"{B}/api/{ep}", data=body, headers=H), timeout=60); b = r.read().decode()
        except Exception as e:
            b = str(e) + (e.read().decode() if hasattr(e, "read") else "")
        open(f"{OUT}/{conf}_{ep}.json", "w").write(b[:3000000])
