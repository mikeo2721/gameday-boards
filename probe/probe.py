"""Probe 3: hdintelligence report chunks + public API calls."""
import json, os, re, urllib.request
OUT = "probe/out3"; os.makedirs(OUT, exist_ok=True)
B = "https://app.hdintelligence.com"
H = {"User-Agent": "Mozilla/5.0 (gameday-boards probe)", "Content-Type": "application/json",
     "Origin": B, "Referer": "https://www.secsports.com/"}
def req(u, data=None):
    try:
        r = urllib.request.urlopen(urllib.request.Request(u, data=json.dumps(data).encode() if data is not None else None, headers=H), timeout=30)
        return r.status, r.read().decode("utf-8", "replace")
    except Exception as e:
        body = e.read().decode("utf-8", "replace") if hasattr(e, "read") else ""
        return getattr(e, "code", None), str(e) + "\n" + body
idx = {}
main = open("probe/out2/hdi_js_0.txt").read()
for c in sorted(set(re.findall(r'import\("\./([^"]+)"\)', main))):
    if re.search(r"Summary|Window|Archive|Selection|Publish|index-", c):
        st, b = req(f"{B}/assets/{c}"); open(f"{OUT}/chunk_{c}.txt", "w").write(b); idx[c] = st
        idx[c + "_api"] = sorted(set(re.findall(r'["`](/api/[A-Za-z0-9_/${}.-]+)', b)))
for conf, ref in (("SEC", "https://www.secsports.com/"), ("B10", "https://bigten.org/"), ("ACC", "https://theacc.com/"), ("B12", "https://big12sports.com/")):
    H["Referer"] = ref
    st, b = req(f"{B}/api/public-load", {"conference_param": conf, "sport_param": "Football", "type_param": "report", "referrer": ref, "source": conf})
    idx[f"public_load_{conf}"] = st; open(f"{OUT}/public_load_{conf}.txt", "w").write(b[:200000])
json.dump(idx, open(f"{OUT}/index.json", "w"), indent=1)
