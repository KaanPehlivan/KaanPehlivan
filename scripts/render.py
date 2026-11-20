"""Render the profile README cards (animated SVGs) into cards/. Standard library only.

Design matches kaanpehlivan.com: night blue, silk, ivory; Instrument Serif, Geist, Geist Mono (SIL OFL, fonts/).
GitHub shows these through <img>, so only inline CSS animation and data-URI fonts/images work there.
Every element's resting style is its final state and animations only run *from* hidden (fill-mode backwards),
so a viewer that doesn't animate still shows the full card.

Contribution numbers come from the public calendar at github.com/users/<USER>/contributions (no token).
Run daily by .github/workflows/cards.yml. Hand-set content lives in the constants below.
"""
import base64
import datetime as dt
import os
import re
import sys
import urllib.request
import xml.dom.minidom
from html import escape, unescape

USER = "KaanPehlivan"
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "cards")

BG, BG2, FG = "#030b1a", "#071330", "#ecebe6"
LINE = "rgba(236,235,230,.14)"
W, GAP = 880, 14  # README column width; transparent space under each full-width card

SERIF, SANS, MONO = "'Instrument Serif',Georgia,serif", "Geist,system-ui,sans-serif", "'Geist Mono',ui-monospace,Menlo,monospace"
FONTS = {"serif": ("Instrument Serif", "normal", 400), "serif-italic": ("Instrument Serif", "italic", 400),
         "sans": ("Geist", "normal", 400), "sans-600": ("Geist", "normal", 600), "mono": ("Geist Mono", "normal", 400)}

HERO = {
    "label": "WEB DESIGNER & DEVELOPER",
    "first": "Kaan", "last": "Pehlivan",
    "blurb": "I design and build fast, original websites and web apps for businesses. "
             "Remote, for clients in Türkiye and worldwide.",
    "link": "kaanpehlivan.com",
}
# (file, label, big text, blurb, fill, ink); numbers are the live work listed on kaanpehlivan.com
TILES = [
    ("tile-sites", "WEBSITES", "4 live", "Business sites in Turkish and English, fast to load and easy to find on Google.", "#0c1d45", FG),
    ("tile-apps", "WEB APPS", "2 in use", "A QR menu and a booking system that a restaurant group runs every day.", "#1c3a7c", FG),
    ("tile-care", "CARE", "$50/mo", "Domain, hosting, updates and small changes, long after launch.", FG, BG),
]
# (file, title, description, tags)
WORK = [
    ("work-trakya", "Trakya Global", "Turkish and English business website for a road freight company serving Europe.", "Business site · Next.js"),
    ("work-yali-menu", "Yalı QR Menu", "QR menu with an admin panel for Yalı steakhouse, updated by the staff in minutes.", "Web app · Supabase"),
    ("work-invitation", "Wedding invitation", "A digital invitation that opens on the phone with a sealed-envelope intro.", "Invitation · GSAP"),
]

CSS = """
.u{animation:u 1s cubic-bezier(.16,1,.3,1) backwards}
.f{animation:f 1.2s ease backwards}
.g{transform-box:fill-box;transform-origin:50% 100%;animation:g 1.1s cubic-bezier(.16,1,.3,1) backwards}
.c{animation:c .5s ease backwards}
.p{animation:p 2.4s ease-in-out 3s infinite}
.sw{animation:sw 1.8s cubic-bezier(.65,0,.35,1) forwards}
@keyframes u{from{opacity:0;transform:translateY(16px)}}
@keyframes f{from{opacity:0}}
@keyframes g{from{transform:scaleY(0)}}
@keyframes c{from{opacity:0}}
@keyframes p{50%{opacity:.35}}
@keyframes sw{to{transform:translateX(560px)}}
@media (prefers-reduced-motion:reduce){*{animation:none!important}}
"""


def b64(path):
    return base64.b64encode(open(os.path.join(ROOT, path), "rb").read()).decode()


def svg(w, h, body, fonts, label):
    faces = "".join(f"@font-face{{font-family:'{FONTS[k][0]}';font-style:{FONTS[k][1]};font-weight:{FONTS[k][2]};"
                    f"src:url(data:font/woff;base64,{b64(f'fonts/{k}.woff')}) format('woff')}}" for k in fonts)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.3f}" height="{h}" viewBox="0 0 {w:.3f} {h}" '
            f'role="img" aria-label="{escape(label)}"><title>{escape(label)}</title><style>{faces}{CSS}</style>{body}</svg>')


def write(name, content):
    xml.dom.minidom.parseString(content)  # never commit a card that GitHub can't render
    with open(os.path.join(OUT, name), "w") as f:
        f.write(content)


def wrap(text, n):
    lines, cur = [], ""
    for word in text.split():
        if cur and len(cur) + 1 + len(word) > n:
            lines.append(cur)
            cur = word
        else:
            cur = f"{cur} {word}".strip()
    return lines + [cur]


def d(s):
    return f'style="animation-delay:{s:.2f}s"'


def card(w, h, fill=BG, x=0):
    return f'<rect x="{x + .5}" y=".5" width="{w - 1}" height="{h - 1}" rx="16" fill="{fill}" stroke="{LINE}"/>'


# ---- data ----------------------------------------------------------------------
def fetch():
    req = urllib.request.Request(f"https://github.com/users/{USER}/contributions", headers={"User-Agent": "profile-cards"})
    page = urllib.request.urlopen(req, timeout=30).read().decode()
    counts = {}
    for m in re.finditer(r'<tool-tip[^>]*\bfor="([^"]+)"[^>]*>([^<]*)</tool-tip>', page):
        n = re.match(r"\s*(\d[\d,]*) contribution", unescape(m.group(2)))
        counts[m.group(1)] = int(n.group(1).replace(",", "")) if n else 0
    days = {}
    for td in re.finditer(r"<td\b[^>]*ContributionCalendar-day[^>]*>", page):
        tag = td.group(0)
        date, cid = re.search(r'data-date="([\d-]+)"', tag), re.search(r'\bid="([^"]+)"', tag)
        if date and cid:
            days[dt.date.fromisoformat(date.group(1))] = counts.get(cid.group(1), 0)
    total = int(re.search(r"([\d,]+)\s+contributions?\s+in the last year", page).group(1).replace(",", ""))
    assert len(days) >= 365, f"calendar parse failed: {len(days)} days"
    if sum(days.values()) != total:
        print(f"warning: day sum {sum(days.values())} != header total {total}", file=sys.stderr)
    return dict(sorted(days.items())), total


def streaks(days):
    run = longest = 0
    for n in days.values():
        run = run + 1 if n else 0
        longest = max(longest, run)
    vals = list(days.values())
    if vals and vals[-1] == 0:  # today may still be empty; the streak then counts up to yesterday
        vals.pop()
    current = 0
    for n in reversed(vals):
        if not n:
            break
        current += 1
    return current, longest


# ---- cards -----------------------------------------------------------------------
def hero():
    h = 420
    art = open(os.path.join(ROOT, "data", "portrait.txt")).read().rstrip("\n").split("\n")
    fs, lh = 8.6, 10.6
    ax, ay = W - 40 - 72 * fs * .6, (h - len(art) * lh) / 2 + 6
    ascii_svg = "".join(f'<text class="c" {d(.4 + i * .035)} x="{ax:.1f}" y="{ay + i * lh:.1f}" xml:space="preserve">{escape(l)}</text>'
                        for i, l in enumerate(art) if l.strip())
    blurb = "".join(f'<tspan x="44" dy="{0 if i == 0 else 26}">{escape(l)}</tspan>' for i, l in enumerate(wrap(HERO["blurb"], 46)))
    body = f"""
<defs>
  <clipPath id="k"><rect width="{W}" height="{h}" rx="16"/></clipPath>
  <linearGradient id="v" x2="1"><stop offset="0" stop-color="{BG}" stop-opacity=".96"/><stop offset=".55" stop-color="{BG}" stop-opacity=".78"/><stop offset="1" stop-color="{BG}" stop-opacity=".55"/></linearGradient>
</defs>
<g clip-path="url(#k)">
  <rect width="{W}" height="{h}" fill="{BG}"/>
  <image class="f" href="data:image/jpeg;base64,{b64('data/silk.jpg')}" width="{W}" height="{h}" preserveAspectRatio="xMidYMid slice"/>
  <rect width="{W}" height="{h}" fill="url(#v)"/>
</g>
<rect x=".5" y=".5" width="{W - 1}" height="{h - 1}" rx="16" fill="none" stroke="{LINE}"/>
<g font-family="{MONO}" font-size="{fs}" fill="{FG}" fill-opacity=".9">{ascii_svg}</g>
<g class="u" {d(.1)}><circle cx="48" cy="58" r="3.5" fill="{FG}"/>
  <text x="60" y="62" font-family="{MONO}" font-size="12" letter-spacing="1.6" fill="{FG}" fill-opacity=".72">{escape(HERO['label'])}</text></g>
<text class="u" {d(.25)} x="40" y="160" font-family="{SERIF}" font-size="104" fill="{FG}">{HERO['first']}</text>
<text class="u" {d(.4)} x="52" y="248" font-family="{SERIF}" font-style="italic" font-size="104" fill="{FG}">{HERO['last']}</text>
<text class="u" {d(.6)} y="294" font-family="{SANS}" font-size="17" fill="{FG}" fill-opacity=".86">{blurb}</text>
<text class="u" {d(.75)} x="44" y="390" font-family="{MONO}" font-size="13" fill="{FG}">{HERO['link']}  ↗</text>
"""
    write("hero.svg", svg(W, h + GAP, body, ["serif", "serif-italic", "sans", "mono"],
                          f"{HERO['first']} {HERO['last']}. {HERO['blurb']}"))


def heatmap(days):
    h, cell, step, x0, y0 = 270, 11.5, 15, 44, 112
    start = next(iter(days))
    start -= dt.timedelta(days=(start.weekday() + 1) % 7)  # GitHub's grid starts on Sunday
    alpha = [.07, .28, .5, .74, 1]
    top = max(days.values()) or 1
    cells, months, last_month = [], [], None
    today = max(days)
    for day, n in days.items():
        col, row = (day - start).days // 7, (day.weekday() + 1) % 7
        lvl = 0 if n == 0 else min(4, 1 + 4 * n // (top + 1))
        x, y = x0 + col * step, y0 + row * step
        cls = "p" if day == today and n else "c"
        cells.append(f'<rect class="{cls}" {d(.3 + col * .018) if cls == "c" else ""} x="{x}" y="{y}" width="{cell}" '
                     f'height="{cell}" rx="2.5" fill="{FG}" fill-opacity="{alpha[lvl]}"/>')
        if day.day <= 7 and row == 0 and day.month != last_month:
            months.append(f'<text x="{x}" y="{y0 + 7 * step + 14}">{day.strftime("%b")}</text>')
            last_month = day.month
    legend = "".join(f'<rect x="{W - 44 - 42 - (4 - i) * 15 - 11.5}" y="{h - 36}" width="11.5" height="11.5" rx="2.5" '
                     f'fill="{FG}" fill-opacity="{a}"/>' for i, a in enumerate(alpha))
    body = f"""
{card(W, h)}
<text class="u" {d(.05)} x="40" y="70" font-family="{SERIF}" font-size="38" fill="{FG}">Shipping, <tspan font-style="italic">every day</tspan></text>
<text class="u" {d(.15)} x="{W - 40}" y="66" text-anchor="end" font-family="{MONO}" font-size="11" letter-spacing="1.5" fill="{FG}" fill-opacity=".6">REFRESHED DAILY</text>
{''.join(cells)}
<g font-family="{MONO}" font-size="10" fill="{FG}" fill-opacity=".5">{''.join(months)}
  <text x="{W - 44 - 42 - 4 * 15 - 11.5 - 8}" y="{h - 26}" text-anchor="end">less</text><text x="{W - 44 - 34}" y="{h - 26}">more</text></g>
{legend}
"""
    write("heatmap.svg", svg(W, h + GAP, body, ["serif", "serif-italic", "mono"],
                             f"{USER}'s GitHub contribution graph for the last year, refreshed daily"))


def activity(days, total):
    h = 300
    by_month = {}
    for day, n in days.items():
        by_month[day.strftime("%Y-%m")] = by_month.get(day.strftime("%Y-%m"), 0) + n
    months = list(by_month.items())[-12:]
    top = max(v for _, v in months) or 1
    bw, gap, base, x0 = 38, 14, h - 52, 44
    bars = []
    for i, (key, v) in enumerate(months):
        bh = max(2, 120 * v / top)
        x = x0 + i * (bw + gap)
        busiest = v == top
        bars.append(f'<rect class="g" {d(.5 + i * .06)} x="{x}" y="{base - bh:.1f}" width="{bw}" height="{bh:.1f}" rx="3" '
                    f'fill="{FG}" fill-opacity="{1 if busiest else .32}"/>'
                    f'<text x="{x + bw / 2}" y="{base + 20}" text-anchor="middle">{dt.date.fromisoformat(key + "-01").strftime("%b")}</text>')
    current, longest = streaks(days)
    best_day = max(days, key=days.get)
    rx = W - 44
    body = f"""
{card(W, h)}
<text class="u" {d(.05)} x="44" y="58" font-family="{MONO}" font-size="11" letter-spacing="1.5" fill="{FG}" fill-opacity=".6">THE LAST 12 MONTHS ON GITHUB</text>
<text class="u" {d(.15)} x="40" y="112" font-family="{SERIF}" font-size="50" fill="{FG}">{total:,} <tspan font-style="italic">contributions</tspan></text>
<g font-family="{MONO}" font-size="10" fill="{FG}" fill-opacity=".55">{''.join(bars)}</g>
<g class="u" {d(.35)} text-anchor="end">
  <text x="{rx}" y="160" font-family="{SERIF}" font-style="italic" font-size="44" fill="{FG}">{current} {'day' if current == 1 else 'days'}</text>
  <text x="{rx}" y="184" font-family="{SANS}" font-size="13" fill="{FG}" fill-opacity=".6">current streak · longest {longest}</text>
  <text x="{rx}" y="236" font-family="{SERIF}" font-style="italic" font-size="32" fill="{FG}">{days[best_day]} in a day</text>
  <text x="{rx}" y="258" font-family="{SANS}" font-size="13" fill="{FG}" fill-opacity=".6">busiest day · {best_day.strftime('%b %-d, %Y')}</text>
</g>
"""
    write("activity.svg", svg(W, h + GAP, body, ["serif", "serif-italic", "sans", "mono"],
                              f"{total:,} contributions in the last 12 months; current streak {current} days, longest {longest}"))


def side_cards():
    tw, th = W / 3, 236
    for pos, (name, label, big, blurb, fill, ink) in enumerate(TILES):
        cx, cw = 7 * pos, tw - 14  # 14px gaps once the three images sit side by side
        lines = "".join(f'<text x="{cx + 24}" y="{168 + i * 20}">{escape(l)}</text>' for i, l in enumerate(wrap(blurb, 32)))
        body = f"""
<defs><clipPath id="k"><rect x="{cx}" width="{cw}" height="{th}" rx="16"/></clipPath>
  <linearGradient id="s" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".22"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient></defs>
<g class="u" {d(.1 + pos * .12)}>
  <g clip-path="url(#k)">
    <rect x="{cx}" width="{cw}" height="{th}" fill="{fill}"/>
    <circle cx="{cx + cw - 30}" cy="{th - 30}" r="58" fill="none" stroke="{ink}" stroke-opacity=".22" stroke-width="1.5"/>
    <rect class="sw" {d(1.2 + pos * .15)} x="{cx - 160}" y="-20" width="110" height="{th + 40}" fill="url(#s)"/>
  </g>
  <rect x="{cx + .5}" y=".5" width="{cw - 1}" height="{th - 1}" rx="16" fill="none" stroke="{LINE}"/>
  <text x="{cx + 24}" y="42" font-family="{MONO}" font-size="12" letter-spacing="1.5" fill="{ink}">{label}</text>
  <text x="{cx + cw - 24}" y="42" text-anchor="end" font-family="{MONO}" font-size="14" fill="{ink}">→</text>
  <text x="{cx + 22}" y="126" font-family="{SERIF}" font-size="52" fill="{ink}">{escape(big)}</text>
  <g font-family="{SANS}" font-size="14" fill="{ink}" fill-opacity=".85">{lines}</g>
</g>
"""
        write(f"{name}.svg", svg(tw, th + GAP, body, ["serif", "sans", "mono"], f"{label}: {big}. {blurb}"))

    for pos, (name, title, desc, tags) in enumerate(WORK):
        cx, cw, ch = 7 * pos, tw - 14, 188
        lines = "".join(f'<text x="{cx + 24}" y="{86 + i * 20}">{escape(l)}</text>' for i, l in enumerate(wrap(desc, 33)))
        body = f"""
<g class="u" {d(.1 + pos * .12)}>
  {card(cw, ch, BG2, cx)}
  <circle cx="{cx + 29}" cy="45" r="4" fill="{FG}"/>
  <text x="{cx + 42}" y="51" font-family="{SANS}" font-weight="600" font-size="18" fill="{FG}">{escape(title)}</text>
  <g font-family="{SANS}" font-size="13.5" fill="{FG}" fill-opacity=".72">{lines}</g>
  <text x="{cx + 24}" y="{ch - 26}" font-family="{MONO}" font-size="11" fill="{FG}" fill-opacity=".55">{escape(tags)}</text>
  <text x="{cx + cw - 24}" y="{ch - 26}" text-anchor="end" font-family="{MONO}" font-size="11" fill="{FG}">live ↗</text>
</g>
"""
        write(f"{name}.svg", svg(tw, ch + GAP, body, ["sans", "sans-600", "mono"], f"{title}: {desc}"))


def section_title(text, italic):
    for theme, color in (("dark", FG), ("light", BG)):
        body = (f'<text class="u" x="2" y="46" font-family="{SERIF}" font-size="40" fill="{color}">{text} '
                f'<tspan font-style="italic">{italic}</tspan></text>')
        write(f"title-work-{theme}.svg", svg(W, 66, body, ["serif", "serif-italic"], f"{text} {italic}"))


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    days, total = fetch()
    assert streaks({1: 1, 2: 1, 3: 0, 4: 1, 5: 1, 6: 1, 7: 0}) == (3, 3)  # today empty -> streak up to yesterday
    hero()
    heatmap(days)
    activity(days, total)
    side_cards()
    section_title("What I’ve", "shipped")
    print(f"rendered {len(os.listdir(OUT))} cards · {total} contributions · streak {streaks(days)}")
