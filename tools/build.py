"""Build the profile README assets: career trace, assay plate, and link buttons.

Pure standard library so the GitHub Action needs no installs.
Run: python3 tools/build.py   (uses $GITHUB_TOKEN, else the `gh` CLI, else cache/)
"""
import datetime as dt
import json
import os
import subprocess
import sys
import urllib.request
from html import escape as e
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets"
USER = "ananthanandanan"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"
SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"

THEMES = {
    "dark": dict(bg="#0d1117", panel="#161b22", line="#30363d", dim="#484f58", txt="#e6edf3", muted="#8b949e",
                 work="#e3b341", oss="#56d4dd", play="#bc8cff", ok="#3fb950", root="#8b949e",
                 well_empty="#262c34", wells=["#253a2e", "#1f6f43", "#2ea043", "#56d364", "#aff5b4"]),
    "light": dict(bg="#ffffff", panel="#f6f8fa", line="#d0d7de", dim="#afb8c1", txt="#1f2328", muted="#656d76",
                  work="#bf8700", oss="#0a9396", play="#8250df", ok="#1a7f37", root="#8c959f",
                  well_empty="#d8dee4", wells=["#c6efce", "#8ad49b", "#3fa45b", "#1a7f37", "#0b4f22"]),
}

# depth, name, attrs, start, end (None = running), kind
SPANS = [
    (0, USER, "github.join", "2019-07-28", None, "root"),
    (1, "work.traboda", "role=llm_researcher·backend", "2023-11-01", "2024-08-01", "work"),
    (1, "work.questcraft", "role=lead_engineer·product_lead", "2024-08-01", "2026-10-31", "work"),
    (1, "work.prevalence", "role=member_of_technical_staff · pocketmd", "2026-11-01", None, "work"),  # TODO: confirm start
    (1, "oss.json-to-many", "pypi · python", "2024-06-20", "2026-05-27", "oss"),
    (1, "lab.construct", "org · r&d", "2026-02-10", None, "play"),
    (2, "reigner", "pypi · agent harness", "2026-05-06", None, "oss"),
    (1, "oss.8mm", "letterboxd rating calc · js", "2026-10-30", None, "oss"),
    (1, "play.typefeud", "typescript", "2026-10-31", None, "play"),
]
NOW = "Member of Technical Staff @ Prevalence"  # status pill in the trace header
ATTRS = [("lang", "python"), ("web", "django·fastapi"), ("async", "celery·rabbitmq"),
         ("infra", "docker·coolify·cloudflare"), ("llm", "langchain·claude-code")]
LINKS = [  # name, method, label, url
    ("web", "GET", "ananthanandanan.com", "https://ananthanandanan.com"),
    ("linkedin", "GET", "linkedin/de-blank", "https://www.linkedin.com/in/de-blank"),
    ("x", "GET", "x.com/Ananthan2k", "https://x.com/Ananthan2k"),
    ("email", "POST", "inbox/ananthan", "mailto:ananthanandanan@gmail.com"),
]


def d(s):
    return dt.date.fromisoformat(s)


# ------------------------------------------------------------------ data
CAL_QUERY = ('{user(login:"%s"){contributionsCollection{contributionCalendar{'
             'weeks{contributionDays{contributionCount date}}}}}}' % USER)


def graphql(query):
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        req = urllib.request.Request("https://api.github.com/graphql", data=json.dumps({"query": query}).encode(),
                                     headers={"Authorization": f"bearer {token}", "User-Agent": "profile-readme"})
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)["data"]
    out = subprocess.run(["gh", "api", "graphql", "-f", f"query={query}"], capture_output=True, text=True, check=True)
    return json.loads(out.stdout)["data"]


def calendar():
    cache = ROOT / "cache" / "calendar.json"
    try:
        weeks = graphql(CAL_QUERY)["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
        days = [[x["date"], x["contributionCount"]] for w in weeks for x in w["contributionDays"]]
        cache.parent.mkdir(exist_ok=True)
        cache.write_text(json.dumps(days))
    except Exception as ex:  # keep building offline
        print("calendar fetch failed, using cache:", ex, file=sys.stderr)
        days = json.loads(cache.read_text())
    return [(d(a), c) for a, c in days]


# ------------------------------------------------------------------ trace
def trace(t, today):
    t0, t1 = d("2019-07-01"), d("2026-12-31")
    W = 880
    lx, gx0, gx1 = 24, 330, 800
    X = lambda day: gx0 + (day - t0).days / (t1 - t0).days * (gx1 - gx0)
    RH, top = 36, 96
    pill_w = len(NOW) * 6.6 + 44
    H = top + 14 + len(SPANS) * RH + 70
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
         f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="12" fill="{t["bg"]}" stroke="{t["line"]}"/>',
         f'<text x="{lx}" y="40" font-family="{SANS}" font-size="20" font-weight="600" fill="{t["txt"]}">K N Anantha Nandanan</text>',
         f'<text x="{lx}" y="62" font-family="{MONO}" font-size="12" fill="{t["muted"]}">trace <tspan fill="{t["oss"]}">career</tspan>'
         f'  ·  {len(SPANS)} spans  ·  status <tspan fill="{t["ok"]}">OK</tspan>  ·  service <tspan fill="{t["txt"]}">backend / agents / infra</tspan></text>',
         f'<rect x="{W-24-pill_w:.0f}" y="26" width="{pill_w:.0f}" height="26" rx="13" fill="{t["panel"]}" stroke="{t["line"]}"/>',
         f'<circle cx="{W-8-pill_w:.0f}" cy="39" r="4" fill="{t["ok"]}"><animate attributeName="opacity" values="1;.25;1" dur="1.6s" repeatCount="indefinite"/></circle>',
         f'<text x="{W-36}" y="43" font-family="{MONO}" font-size="11" fill="{t["txt"]}" text-anchor="end"'
         f' textLength="{len(NOW)*6.6:.0f}" lengthAdjust="spacingAndGlyphs">{e(NOW)}</text>',
         f'<text x="{W-24}" y="72" font-family="{MONO}" font-size="10" fill="{t["muted"]}" text-anchor="end">updated {today:%Y-%m-%d}</text>',
         f'<line x1="{lx}" y1="{top}" x2="{W-24}" y2="{top}" stroke="{t["line"]}"/>',
         f'<text x="{lx}" y="{top-8}" font-family="{MONO}" font-size="10.5" fill="{t["muted"]}">SPAN</text>']
    for yr in range(2020, 2027):
        x = X(d(f"{yr}-01-01"))
        o.append(f'<line x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{H-74}" stroke="{t["line"]}" stroke-dasharray="2 4"/>')
        o.append(f'<text x="{x:.1f}" y="{top-8}" font-family="{MONO}" font-size="10.5" fill="{t["muted"]}" text-anchor="middle">{yr}</text>')
    for i, (dep, name, attrs, s, en, kind) in enumerate(SPANS):
        y = top + 14 + i * RH
        if i % 2 == 0:
            o.append(f'<rect x="1" y="{y-6}" width="{W-2}" height="{RH}" fill="{t["panel"]}" opacity=".6"/>')
        ix = lx + dep * 18
        if dep:
            px = lx + (dep - 1) * 18 + 6
            o.append(f'<path d="M{px} {y-6}V{y+8}H{ix-4}" fill="none" stroke="{t["dim"]}"/>')
        o.append(f'<text x="{ix}" y="{y+8}" font-family="{MONO}" font-size="12.5" fill="{t["txt"]}">{e(name)}</text>')
        o.append(f'<text x="{ix}" y="{y+22}" font-family="{MONO}" font-size="10" fill="{t["muted"]}">{e(attrs)}</text>')
        start, end = d(s), (d(en) if en else today)
        x0, x1 = X(start), X(end)
        bw = max(6, x1 - x0)
        o.append(f'<rect x="{x0:.1f}" y="{y+2}" width="{bw:.1f}" height="14" rx="3" fill="{t[kind]}" opacity="{0.45 if kind == "root" else 0.95}"/>')
        if not en:
            o.append(f'<rect x="{x0+bw-3:.1f}" y="{y+2}" width="3" height="14" fill="{t["txt"]}">'
                     f'<animate attributeName="opacity" values="1;0;1" dur="1.1s" repeatCount="indefinite"/></rect>')
        days = (end - start).days
        lab = f"{days/365.25:.1f}y" if days >= 365 else f"{days//30}mo" if days >= 30 else f"{days}d"
        if not en:
            lab += " · running"
        right = x0 + bw + 6 + len(lab) * 6.1 > W - 24
        o.append(f'<text x="{(x0-6 if right else x0+bw+6):.1f}" y="{y+13}" font-family="{MONO}" font-size="10" fill="{t["muted"]}"'
                 f' text-anchor="{"end" if right else "start"}">{e(lab)}</text>')
    fy = H - 44
    o.append(f'<line x1="{lx}" y1="{fy-18}" x2="{W-24}" y2="{fy-18}" stroke="{t["line"]}"/>')
    x = lx
    for k, v in ATTRS:
        w = (len(k) + len(v) + 1) * 6.6 + 18
        o.append(f'<rect x="{x:.0f}" y="{fy-2}" width="{w:.0f}" height="22" rx="4" fill="{t["panel"]}" stroke="{t["line"]}"/>'
                 f'<text x="{x+9:.0f}" y="{fy+13}" font-family="{MONO}" font-size="11" textLength="{w-18:.0f}" lengthAdjust="spacingAndGlyphs">'
                 f'<tspan fill="{t["work"]}">{k}</tspan><tspan fill="{t["dim"]}">=</tspan><tspan fill="{t["txt"]}">{e(v)}</tspan></text>')
        x += w + 8
    o.append("</svg>")
    return "\n".join(o)


# ------------------------------------------------------------------ plate
SEQ = "MTSPYTHQNDAGFASTAPICELERYREDISDKERLLMGPS"
CLUSTAL = {**{c: "#80a0f0" for c in "AILMFWV"}, **{c: "#f01505" for c in "KR"}, **{c: "#c048c0" for c in "DE"},
           **{c: "#15c015" for c in "NQST"}, "C": "#f08080", "G": "#f09048", "P": "#c0c000", **{c: "#15a4a4" for c in "HY"}}


def plate(t, days, today):
    total, peak = sum(c for _, c in days), max(c for _, c in days)
    W, H = 880, 330
    ox, oy, P = 64, 128, 14.6
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
         f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="12" fill="{t["bg"]}" stroke="{t["line"]}"/>',
         f'<text x="24" y="38" font-family="{MONO}" font-size="13" fill="{t["oss"]}">&gt;{USER}|gh_activity|contrib_assay_{today.year}</text>',
         f'<g font-family="{MONO}" font-size="13" font-weight="600">',
         *[f'<text x="{24 + i*9.6:.1f}" y="60" fill="{CLUSTAL.get(ch, t["muted"])}">{ch}</text>' for i, ch in enumerate(SEQ)],
         '</g>',
         f'<text x="24" y="92" font-family="{SANS}" font-size="13" fill="{t["muted"]}">PLATE <tspan fill="{t["txt"]}">gh-activity · 53×7</tspan>'
         f'   ·   readout <tspan fill="{t["txt"]}">contributions/day</tspan>   ·   total <tspan fill="{t["work"]}">{total}</tspan>'
         f'   ·   peak <tspan fill="{t["work"]}">{peak}</tspan></text>']
    for r, lab in enumerate("ABCDEFG"):
        o.append(f'<text x="{ox-18}" y="{oy + r*P + 4:.1f}" font-family="{MONO}" font-size="10" fill="{t["muted"]}" text-anchor="middle">{lab}</text>')
    for wk in range(0, 54, 4):
        o.append(f'<text x="{ox + wk*P:.1f}" y="{oy-14}" font-family="{MONO}" font-size="10" fill="{t["muted"]}" text-anchor="middle">{wk+1:02d}</text>')
    o.append(f'<rect x="{ox-30}" y="{oy-28}" width="{54*P+34:.0f}" height="{7*P+38:.0f}" rx="14" fill="none" stroke="{t["line"]}"/>')
    start = days[0][0] - dt.timedelta(days=(days[0][0].weekday() + 1) % 7)  # align to Sunday
    for day, c in days:
        idx = (day - start).days
        cx, cy = ox + (idx // 7) * P, oy + (idx % 7) * P
        if c == 0:
            o.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="5.1" fill="none" stroke="{t["well_empty"]}"/>')
        else:
            lvl = 0 if c < 2 else 1 if c < 5 else 2 if c < 10 else 3 if c < 20 else 4
            o.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="5.6" fill="{t["wells"][lvl]}"/>')
    o.append(f'<rect x="{ox-7}" y="{oy-10}" width="14" height="{6*P+20:.0f}" rx="7" fill="{t["oss"]}" fill-opacity=".12" '
             f'stroke="{t["oss"]}" stroke-opacity=".5"><animateTransform attributeName="transform" type="translate" '
             f'from="0 0" to="{53*P:.0f} 0" dur="9s" repeatCount="indefinite"/></rect>')
    ly = H - 30
    o.append(f'<text x="{ox-30}" y="{ly+4}" font-family="{MONO}" font-size="10.5" fill="{t["muted"]}">empty</text>')
    o += [f'<circle cx="{ox+30+i*16}" cy="{ly}" r="5.6" fill="{cc}"/>' for i, cc in enumerate(t["wells"])]
    o.append(f'<text x="{ox+110}" y="{ly+4}" font-family="{MONO}" font-size="10.5" fill="{t["muted"]}">saturated</text>')
    o.append(f'<text x="{W-24}" y="{ly+4}" font-family="{MONO}" font-size="10.5" fill="{t["muted"]}" text-anchor="end">'
             f'read {today:%Y-%m-%d} · auto-refreshed by gh actions</text>')
    o.append("</svg>")
    return "\n".join(o)


# ------------------------------------------------------------------ links
def link(t, method, label):
    W, H = 212, 40
    mcol = t["ok"] if method == "GET" else t["work"]
    return "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
        f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="8" fill="{t["bg"]}" stroke="{t["line"]}"/>',
        f'<text x="14" y="25" font-family="{MONO}" font-size="12" font-weight="600" fill="{mcol}">{method}</text>',
        f'<text x="{14 + len(method)*7.6 + 8:.0f}" y="25" font-family="{MONO}" font-size="12" fill="{t["txt"]}">{e(label)}</text>',
        "</svg>"])


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    today = dt.date.today()
    days = calendar()
    for name, t in THEMES.items():
        (OUT / f"trace_{name}.svg").write_text(trace(t, today))
        (OUT / f"plate_{name}.svg").write_text(plate(t, days, today))
        for key, method, label, _ in LINKS:
            (OUT / f"link_{key}_{name}.svg").write_text(link(t, method, label))
    print(f"built {len(list(OUT.glob('*.svg')))} svgs · {sum(c for _, c in days)} contributions")
