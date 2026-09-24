"""Builds the Activity card (stats + animated 3D contribution wave + snake) for the profile README.

Runs in GitHub Actions after Platane/snk has written dist/snake-{dark,light}.svg.
No third-party packages: glyph outlines are pre-baked in glyphs.json so type renders
identically on GitHub (its image CSP blocks web fonts inside SVGs).
"""
import datetime as dt
import json
import os
import random
import re
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
GLYPHS = json.load(open(os.path.join(HERE, "glyphs.json")))
SRC = sys.argv[1] if len(sys.argv) > 1 else "dist"
OUT = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith("--") else SRC
FAKE = "--fake" in sys.argv

THEMES = {
    "dark": dict(BG="#0c0c0d", SURF="#141416", LINE="#26262a", TEXT="#f2f1ee", MUTE="#8e8e93", DIM="#5a5a60",
                 ACC="#ff7a45", EDGE="#ffffff", GR="1", GRA=".06", GLOWA=".35",
                 LV=["#1f1f22", "#4a261a", "#86391f", "#c9562c", "#ff7a45"]),
    "light": dict(BG="#f6f5f2", SURF="#ffffff", LINE="#e3e1dc", TEXT="#121214", MUTE="#6b6b71", DIM="#a3a3a8",
                  ACC="#ec5b24", EDGE="#000000", GR="0", GRA=".05", GLOWA=".22",
                  LV=["#e6e3dd", "#ffd9c7", "#ffb08a", "#f57e4b", "#ec5b24"]),
}
LEVEL = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2, "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}


# ------------------------------------------------------------------ data
def fetch():
    q = """query($login:String!){ user(login:$login){
      contributionsCollection{ totalCommitContributions totalPullRequestContributions
        contributionCalendar{ totalContributions weeks{ contributionDays{ contributionCount date contributionLevel } } } }
      repositories(ownerAffiliations:OWNER,isFork:false,first:100,orderBy:{field:PUSHED_AT,direction:DESC}){
        nodes{ languages(first:8,orderBy:{field:SIZE,direction:DESC}){ edges{ size node{ name } } } } } } }"""
    body = json.dumps({"query": q, "variables": {"login": os.environ["USERNAME"]}}).encode()
    req = urllib.request.Request("https://api.github.com/graphql", body,
                                 {"Authorization": "bearer " + os.environ["GITHUB_TOKEN"], "Content-Type": "application/json"})
    d = json.load(urllib.request.urlopen(req))["data"]["user"]
    cc = d["contributionsCollection"]
    weeks = [[(x["contributionCount"], LEVEL[x["contributionLevel"]], x["date"]) for x in w["contributionDays"]]
             for w in cc["contributionCalendar"]["weeks"]]
    langs = {}
    for r in d["repositories"]["nodes"]:
        for e in r["languages"]["edges"]:
            langs[e["node"]["name"]] = langs.get(e["node"]["name"], 0) + e["size"]
    return dict(total=cc["contributionCalendar"]["totalContributions"], commits=cc["totalCommitContributions"],
                prs=cc["totalPullRequestContributions"], weeks=weeks, langs=langs)


def fake():
    random.seed(4)
    start = dt.date.today() - dt.timedelta(days=364)
    start -= dt.timedelta(days=(start.weekday() + 1) % 7)
    weeks, day = [], start
    while day <= dt.date.today():
        w = []
        for _ in range(7):
            if day <= dt.date.today():
                c = random.choice([0, 0, 0, 0, 1, 2, 3, 5, 8, 12]) if 20 < (day - start).days // 7 < 45 else random.choice([0] * 9 + [1, 3])
                w.append((c, 0 if c == 0 else min(4, 1 + c // 3), day.isoformat()))
            day += dt.timedelta(days=1)
        weeks.append(w)
    total = sum(c for w in weeks for c, _, _ in w)
    return dict(total=total, commits=int(total * .8), prs=12, weeks=weeks,
                langs={"TypeScript": 900, "JavaScript": 120, "Java": 80, "Python": 40, "HTML": 30})


def streaks(weeks):
    days = [c for w in weeks for c, _, _ in w]
    best = cur = 0
    for c in days:
        cur = cur + 1 if c > 0 else 0
        best = max(best, cur)
    now = 0
    for c in reversed(days):
        if c > 0:
            now += 1
        elif now == 0:
            continue  # today may still be empty
        else:
            break
    return best, now, max(days)


# ------------------------------------------------------------------ type
class Type:
    def __init__(self):
        self.used = {}

    def text(self, key, s, size, x, y, fill, anchor="start", tracking=0, cls=""):
        f = GLYPHS[key]
        upm = f["upm"]
        tr = tracking * upm / size
        adv, uses = 0, []
        for ch in s:
            if ch not in f["g"]:
                ch = " " if " " in f["g"] else next(iter(f["g"]))
            a, d = f["g"][ch]
            if d:
                gid = f"g{key}{ord(ch)}"
                self.used[gid] = d
                uses.append(f'<use href="#{gid}" x="{adv:.0f}"/>')
            adv += a + tr
        adv -= tr
        w = adv * size / upm
        if anchor == "end":
            x -= w
        elif anchor == "middle":
            x -= w / 2
        sc = size / upm
        c = f' class="{cls}"' if cls else ""
        return f'<g{c} fill="{fill}" transform="translate({x:.1f} {y:.1f}) scale({sc:.5f} {-sc:.5f})">{"".join(uses)}</g>', w

    def defs(self):
        return "".join(f'<path id="{k}" d="{d}"/>' for k, d in self.used.items())


def shade(hex_, f):
    h = hex_.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return "#%02x%02x%02x" % tuple(max(0, min(255, int(v * f))) for v in (r, g, b))


def fmt(n):
    return f"{n:,}"


# ------------------------------------------------------------------ snake
def load_snake(path):
    s = open(path).read()
    vb = re.search(r'viewBox="([^"]+)"', s).group(1)
    inner = s[s.index(">", s.index("<svg")) + 1: s.rindex("</svg>")]
    x, y, w, h = map(float, vb.split())
    y, h = -14, 7 * 16 + 24          # crop to the grid; drop snk's progress bar underneath
    return f"{x:g} {y:g} {w:g} {h:g}", inner, w, h


# ------------------------------------------------------------------ card
def card(data, theme, snake):
    t = THEMES[theme]
    T = Type()
    W = 1280
    weeks = data["weeks"]
    best, now, busiest = streaks(weeks)
    maxc = max(1, busiest)

    # ---- calendar geometry (cabinet oblique)
    cx0, cx1 = 432, 1208
    dx, dy = 5.2, 6.4          # row step (depth)
    bw, bdx, bdy = 10.5, 3.6, 4.4
    nweeks = len(weeks)
    cw = (cx1 - cx0 - 6 * dx - bdx) / nweeks
    base = 318                 # front row baseline
    hmax = 84
    bars = []
    for d in range(7):                     # back (Sunday) to front (Saturday)
        depth = 6 - d
        for w, week in enumerate(weeks):
            if d >= len(week):
                continue
            c, lv, _ = week[d]
            x = cx0 + w * cw + depth * dx
            yb = base - depth * dy
            h = 2.2 if c == 0 else 5 + (c / maxc) ** .6 * hmax
            top, front, side = t["LV"][lv], shade(t["LV"][lv], .82), shade(t["LV"][lv], .66)
            if theme == "dark" and lv == 0:
                top, front, side = "#232326", "#1a1a1c", "#141416"
            g = (f'<path d="M{x:.1f} {yb:.1f}h{bw}v{-h:.1f}h{-bw}z" fill="{front}"/>'
                 f'<path d="M{x+bw:.1f} {yb:.1f}l{bdx} {-bdy}v{-h:.1f}l{-bdx} {bdy}z" fill="{side}"/>'
                 f'<path d="M{x:.1f} {yb-h:.1f}l{bdx} {-bdy}h{bw}l{-bdx} {bdy}z" fill="{top}"/>')
            delay = w * .045 + depth * .03
            bars.append(f'<g class="bx" style="animation-delay:{delay:.2f}s">{g}</g>' if c else g)

    # ---- text
    parts = []
    s, _ = T.text("M", "ACTIVITY", 14, 72, 70, t["MUTE"], tracking=1.6); parts.append(s)
    s, _ = T.text("M", "LAST 12 MONTHS", 14, W - 72, 70, t["MUTE"], anchor="end", tracking=1.6); parts.append(s)
    s, nw = T.text("D", fmt(data["total"]), 92, 66, 196, t["TEXT"], tracking=-3); parts.append(s)
    s, _ = T.text("B", "contributions", 20, 72, 232, t["MUTE"]); parts.append(s)
    pl = lambda n: f"{n} day" + ("" if n == 1 else "s")
    stats = [("LONGEST STREAK", pl(best)), ("CURRENT STREAK", pl(now)), ("BEST DAY", f"{busiest}")]
    sx = 72
    for lab, val in stats:
        s, lw = T.text("M", lab, 11.5, sx, 284, t["DIM"], tracking=1.3); parts.append(s)
        s, vw = T.text("B5", val, 19, sx, 312, t["TEXT"]); parts.append(s)
        sx += max(lw, vw) + 30

    # ---- languages bar
    langs = sorted(data["langs"].items(), key=lambda kv: -kv[1])
    tot = sum(v for _, v in langs) or 1
    top = [(k, v / tot) for k, v in langs[:4]]
    rest = 1 - sum(p for _, p in top)
    if rest > .005:
        top.append(("Other", rest))
    lx, ly, lw_ = 72, 352, W - 144
    segs, x = [], lx
    shades = [t["ACC"], shade(t["ACC"], .8) if theme == "light" else "#c9562c", t["LV"][2], t["LV"][1], t["DIM"]]
    for i, (k, p) in enumerate(top):
        w_ = lw_ * p
        segs.append(f'<rect x="{x:.1f}" y="{ly}" width="{max(0, w_ - 3):.1f}" height="6" rx="3" fill="{shades[i]}"/>')
        x += w_
    labx = lx
    for i, (k, p) in enumerate(top):
        segs.append(f'<circle cx="{labx + 4}" cy="{ly + 29}" r="4" fill="{shades[i]}"/>')
        s, w1 = T.text("B", k, 15, labx + 16, ly + 34, t["TEXT"]); segs.append(s)
        s, w2 = T.text("M", f"{round(p * 100)}%", 13, labx + 16 + w1 + 8, ly + 34, t["MUTE"]); segs.append(s)
        labx += 16 + w1 + 8 + w2 + 28

    # ---- snake strip
    svb, sinner, sw, sh = snake
    sy0 = 98
    swidth = W - 144 + 16
    sheight = swidth * sh / sw
    OFF = int(sy0 + sheight + 34 - 100)
    H = 400 + OFF + 24

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{fmt(data['total'])} contributions in the last year. Longest streak {best} days.">
<defs>
  <style>
    .bx{{transform-box:fill-box;transform-origin:50% 100%;animation:wv3d 7s cubic-bezier(.45,0,.2,1) infinite}}
    @keyframes wv3d{{0%,55%,100%{{transform:scaleY(1)}}70%{{transform:scaleY(.08)}}}}
    .glw{{animation:drf 16s ease-in-out infinite alternate}}
    @keyframes drf{{from{{transform:translate(0,0)}}to{{transform:translate(-160px,40px)}}}}
    @media (prefers-reduced-motion: reduce){{.bx,.glw{{animation:none}}}}
  </style>
  <clipPath id="card"><rect width="{W}" height="{H}" rx="28"/></clipPath>
  <linearGradient id="edge" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="{t['EDGE']}" stop-opacity=".14"/><stop offset="1" stop-color="{t['EDGE']}" stop-opacity=".06"/></linearGradient>
  <radialGradient id="g1"><stop offset="0" stop-color="{t['ACC']}" stop-opacity="{t['GLOWA']}"/><stop offset="1" stop-color="{t['ACC']}" stop-opacity="0"/></radialGradient>
  <filter id="grain" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="2" stitchTiles="stitch"/><feColorMatrix values="0 0 0 0 {t['GR']}  0 0 0 0 {t['GR']}  0 0 0 0 {t['GR']}  0 0 0 {t['GRA']} 0"/></filter>
  {T.defs()}
</defs>
<g clip-path="url(#card)">
  <rect width="{W}" height="{H}" fill="{t['BG']}"/>
  <g class="glw"><circle cx="1100" cy="120" r="380" fill="url(#g1)"/></g>
  <rect width="{W}" height="{H}" filter="url(#grain)"/>
</g>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="27.5" fill="none" stroke="url(#edge)"/>
{"".join(parts[:2])}
<svg x="64" y="{sy0}" width="{swidth:.1f}" height="{sheight:.1f}" viewBox="{svb}">{sinner}</svg>
<rect x="72" y="{sy0 + sheight + 18:.0f}" width="{W - 144}" height="1" fill="{t['LINE']}"/>
<g transform="translate(0 {OFF})">
{"".join(parts[2:])}
<g>{"".join(bars)}</g>
{"".join(segs)}
</g>
</svg>
'''


def main():
    data = fake() if FAKE else fetch()
    os.makedirs(OUT, exist_ok=True)
    for theme in THEMES:
        snake = load_snake(os.path.join(SRC, f"snake-{theme}.svg"))
        open(os.path.join(OUT, f"activity-{theme}.svg"), "w").write(card(data, theme, snake))
        print("wrote", theme)


if __name__ == "__main__":
    main()
