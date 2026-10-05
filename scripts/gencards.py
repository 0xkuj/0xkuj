"""Generate the tweak cards shown in README.md.

Each card is a stack of linked SVG pieces (a body plus one row per link),
laid out two per row on wide screens and one per row elsewhere,
with each piece picked per screen size via <picture>.

    python3 scripts/gencards.py            # redraw cards (fetches live stars/forks)
    python3 scripts/gencards.py --readme   # also rewrite the README card sections

To add or edit a tweak, change FEATURED / MORE below and run with --readme.
Icons live in assets/icons/<name>.png (112px).
"""
import base64, html, json, math, os, re, sys, urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = f'{REPO}/assets/cards'
RAW = 'https://raw.githubusercontent.com/0xkuj/0xkuj/main/assets/cards/'
IDB = 'https://www.idownloadblog.com/'

# slug, name, icon, description, article, repo
FEATURED = [
    ('safarix', 'SafariX', 'safarix', 'Must-have power-user upgrade for Safari with essential QoL features', 'https://onejailbreak.com/blog/safarix-tweak/', None),
    ('iparanger', 'IPA Ranger', 'iparanger', 'Powerful GUI for ipatool — search, download & downgrade IPAs', IDB + '2023/03/06/ipa-ranger/', 'IPARanger'),
    ('3dappversionspoofer', '3DAppVersionSpoofer', '3dappversionspoofer', 'Spoof app & iOS versions straight from the 3D Touch menu', IDB + '2022/06/23/3dappversionspoofer/', '3DAppVersionSpoofer'),
    ('filzadirprobe', 'FilzaDirProbe', 'filzadirprobe', 'Filza extension showing folder sizes with sorting options', IDB + '2024/08/07/filzadirprobe/', None),
    ('contactsextended', 'Contacts Extended', 'contactsextended', 'Contact options from Recents, bulk actions & more', IDB + '2021/08/03/contacts-extended/', None),
    ('liveactivities', 'Live Activities', 'liveactivities', 'Interactive alarms, timers, reminders & more on your Lock Screen', IDB + '2022/08/27/live-activities/', None),
]
MORE = [
    ('notificationsgroupcount', 'NotificationsGroupCount', 'notificationsgroupcount', 'Count grouped notifications on the Lock Screen', IDB + '2024/10/31/notificationsgroupcount/', 'NotificationsGroupCount'),
    ('nopastealerts16', 'NoPasteAlerts16', 'placeholder', 'Kill the annoying paste alerts introduced in iOS 16', IDB + '2024/09/13/nopastealerts16/', 'NoPasteAlerts16'),
    ('snoozelabels', 'SnoozeLabels', 'placeholder', 'Replace the snooze title with your actual alarm label', IDB + '2024/05/03/snoozelabels/', 'SnoozeLabels'),
    ('primedeck', 'PrimeDeck', 'primedeck', 'Highly customizable App Switcher', IDB + '2023/12/11/primedeck/', None),
    ('ccadsbegone', 'CCAdsBeGone', 'ccadsbegone', 'System-wide ad blocker with a Control Center toggle', IDB + '2023/07/17/ccadsbegone/', None),
    ('ccbackgrounder17', 'CCBackgrounder17', 'ccbackgrounder17', '"Toggle Background Mode" in CC on iOS 17+, with auto-toggle per app', None, 'CCBackgrounder17'),
    ('backgrounderaction15autostate', 'BackgrounderAction15AutoState', 'backgrounderaction15autostate', 'Auto-enable BackgrounderAction15 for selected apps', None, 'BackgrounderAction15AutoState'),
    ('docbox', 'Docbox', 'docbox', 'Store & organize your essential documents in one place', IDB + '2022/01/22/docbox/', None),
    ('ccdndtimer', 'CCDNDTimer', 'ccdndtimer', 'Custom Do Not Disturb timers', 'https://ioshacker.com/cydia/ccdndtimer-tweak-lets-you-enable-dnd-mode-for-a-specific-time', 'CCDNDTimer'),
    ('bubbleapps', 'Bubble Apps', 'bubbleapps', 'Floating app bubbles for quick access', 'https://kubadownload.com/news/bubble-apps-tweak/', None),
    ('cctime13', 'CCTime13', 'cctime', 'Current time in Control Center', IDB + '2020/08/22/cctime13/', 'CCTime13'),
    ('hidevoipsuggestions', 'Hide VoIP Suggestions', 'placeholder', 'Hide VoIP call suggestions in Contacts / Recents', IDB + '2021/08/26/hide-voip-suggestions/', 'Hide-VOIP-Suggestions'),
    ('cccounters', 'CCCounters', 'cccounters', 'Countdown to next alarm & timer in Control Center', 'https://kubadownload.com/news/cccounters/', 'CCCounters'),
    ('sirittl', 'SiriTTL', 'sirittl', 'Auto-dismiss Siri after a configurable idle time', IDB + '2020/06/27/siri-ttl/', 'SiriTTL'),
    ('lowernotifs', 'LowerNotifs', 'lowernotifs', 'Lower the Lock Screen notification limit anywhere you like', None, 'LowerNotifs'),
    ('fixwanotifs', 'FixWANotifs', 'fixwanotifs', 'Fix missing WhatsApp notifications by raising the NSE Jetsam limit', None, 'FixWANotifs'),
    ('nativecolorpickercellexample', 'NativeColorPickerCellExample', 'placeholder', 'Native color picker cell for tweak devs', None, 'NativeColorPickerCellExample'),
]

# Layouts. Wide desktops (GitHub's README column is a fixed 846px there) get two
# cards per row; everything narrower gets one card per row. Every piece of the
# README markup is a <picture> that collapses to a 0x0 image outside its layout.
PAIR_MEDIA = '(min-width: 1280px)'
# suffix, media query, piece width, side inset, icon, name px, desc px, row height, row px
PAIR = ('x', PAIR_MEDIA, 420, 6, 52, 15, 13, 38, 13)
SINGLE = [
    ('l', '(min-width: 1012px)', 560, 0, 56, 17, 14, 40, 14),
    ('m', '(min-width: 544px)', 400, 0, 52, 15, 13, 38, 13),
    ('s', None, 340, 0, 48, 15, 13, 38, 13),
]
GAP = 16  # space above each card

FONT = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
BG, BORDER, NAME, DESC, LINK, R = '#161b22', '#30363d', '#e6edf3', '#8b949e', '#A78BFA', 12


def tw(t, size):
    w = 0
    for c in t:
        w += 0.28 if c in "iljtf.,:;|!' " else 0.62 if c in 'mwMW' else 0.56 if c.isupper() or c.isdigit() else 0.5
    return w * size * 1.12


def wrap(t, size, maxw):
    lines, cur = [], ''
    for word in t.split():
        nxt = (cur + ' ' + word).strip()
        if tw(nxt, size) <= maxw:
            cur = nxt
        else:
            lines.append(cur)
            cur = word
    lines.append(cur)
    return lines


def icon_b64(name):
    return base64.b64encode(open(f'{REPO}/assets/icons/{name}.png', 'rb').read()).decode()


def shape(w, h, top, bottom):
    """Path for a box with optionally rounded top / bottom corners."""
    rt, rb = (R if top else 0), (R if bottom else 0)
    return (f'M{rt},0.5 H{w - rt} ' + (f'A{rt - .5},{rt - .5} 0 0 1 {w - .5},{rt} ' if rt else f'H{w - .5} ') +
            f'V{h - rb} ' + (f'A{rb - .5},{rb - .5} 0 0 1 {w - rb},{h - .5} ' if rb else f'V{h - .5} ') +
            f'H{rb} ' + (f'A{rb - .5},{rb - .5} 0 0 1 0.5,{h - rb} ' if rb else 'H0.5 ') +
            f'V{rt} ' + (f'A{rt - .5},{rt - .5} 0 0 1 {rt},0.5 Z' if rt else 'V0.5 Z'))


def svg(w, h, body):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">{body}</svg>'


def star(cx, cy, r):
    pts = []
    for i in range(10):
        a = math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.45
        pts.append(f'{cx + rr * math.cos(a):.1f},{cy - rr * math.sin(a):.1f}')
    return f'<polygon points="{" ".join(pts)}" fill="{DESC}"/>'


def fork(x, cy, s):
    """Small fork glyph, s px tall, left edge at x."""
    u = s / 12
    return (f'<g fill="none" stroke="{DESC}" stroke-width="{1.4 * u:.2f}" stroke-linecap="round">'
            f'<circle cx="{x + 2 * u:.1f}" cy="{cy - 4 * u:.1f}" r="{1.6 * u:.1f}"/>'
            f'<circle cx="{x + 8 * u:.1f}" cy="{cy - 4 * u:.1f}" r="{1.6 * u:.1f}"/>'
            f'<circle cx="{x + 5 * u:.1f}" cy="{cy + 4.5 * u:.1f}" r="{1.6 * u:.1f}"/>'
            f'<path d="M{x + 2 * u:.1f},{cy - 2.4 * u:.1f} v1.4 q0,1.6 1.6,1.6 h2.8 q1.6,0 1.6,-1.6 v-1.4 M{x + 5 * u:.1f},{cy + .6 * u:.1f} v2.3"/></g>')


def body_height(t, desc):
    _, _, PW, M, ic, nsz, dsz, _, _ = t
    x = 16 + ic + 14
    lines = wrap(desc, dsz, PW - 2 * M - x - 16)
    lh = round(dsz * 1.4)
    return lines, lh, max(ic + 32, nsz + 8 + lh * len(lines) + 36)


def body_svg(t, name, icon, desc, min_h=0):
    _, _, PW, M, ic, nsz, dsz, _, _ = t
    CW, pad = PW - 2 * M, 16
    x = pad + ic + 14
    lines, lh, H = body_height(t, desc)
    H = max(H, min_h)
    text_h = nsz + 8 + lh * len(lines)
    ty = (H - text_h) / 2 + nsz
    e = lambda s: html.escape(s, quote=True)
    desc_t = ''.join(f'<text x="{x}" y="{ty + 8 + lh * (i + 1) - 3:.0f}" font-family="{FONT}" font-size="{dsz}" fill="{DESC}">{e(l)}</text>'
                     for i, l in enumerate(lines))
    iy = (H - ic) / 2
    return svg(PW, GAP + H,
               f'<defs><clipPath id="c"><rect x="{pad}" y="{iy}" width="{ic}" height="{ic}" rx="{ic * .225:.1f}"/></clipPath></defs>'
               f'<g transform="translate({M},{GAP})">'
               f'<path d="{shape(CW, H, True, False)}" fill="{BG}" stroke="{BORDER}"/>'
               f'<image x="{pad}" y="{iy}" width="{ic}" height="{ic}" clip-path="url(#c)" href="data:image/png;base64,{icon_b64(icon)}"/>'
               f'<text x="{x}" y="{ty:.0f}" font-family="{FONT}" font-size="{nsz}" font-weight="600" fill="{NAME}">{e(name)}</text>{desc_t}</g>')


def row_svg(t, label, last, counts=None):
    _, _, PW, M, _, _, _, H, sz = t
    W, pad = PW - 2 * M, 16
    cy = H / 2 + sz * 0.35
    extra = ''
    if counts:
        stars, forks = counts
        end = W - pad - 18
        f_txt, s_txt = f'{forks:,}', f'{stars:,}'
        extra += f'<text x="{end}" y="{cy:.1f}" text-anchor="end" font-family="{FONT}" font-size="{sz - 1}" fill="{DESC}">{f_txt}</text>'
        fx = end - tw(f_txt, sz - 1) - 4 - sz * 0.8
        extra += fork(fx, H / 2, sz * 0.9)
        send = fx - 12
        extra += f'<text x="{send:.1f}" y="{cy:.1f}" text-anchor="end" font-family="{FONT}" font-size="{sz - 1}" fill="{DESC}">{s_txt}</text>'
        extra += star(send - tw(s_txt, sz - 1) - 4 - sz * 0.42, H / 2, sz * 0.45)
    return svg(PW, H,
               f'<g transform="translate({M},0)">'
               f'<path d="{shape(W, H, False, last)}" fill="{BG}" stroke="{BORDER}"/>'
               f'<text x="{pad}" y="{cy:.1f}" font-family="{FONT}" font-size="{sz}" fill="{LINK}" font-weight="600">{html.escape(label)}</text>'
               f'{extra}'
               f'<path d="M{W - pad - 5},{H / 2 - 5} l5,5 l-5,5" fill="none" stroke="{DESC}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></g>')


def site(u):
    for k, v in {'idownloadblog': 'iDownloadBlog', 'onejailbreak': 'OneJailbreak', 'ioshacker': 'iOSHacker', 'kubadownload': 'KubaDownload'}.items():
        if k in u:
            return v


def repo_counts(repo):
    req = urllib.request.Request(f'https://api.github.com/repos/0xkuj/{repo}', headers={'Accept': 'application/vnd.github+json'})
    if os.environ.get('GITHUB_TOKEN'):
        req.add_header('Authorization', f'Bearer {os.environ["GITHUB_TOKEN"]}')
    data = json.load(urllib.request.urlopen(req, timeout=30))
    return data['stargazers_count'], data['forks_count']


def rows_for(article, repo):
    rows = []
    if article:
        rows.append(('article', article, f'Read on {site(article)}'))
    if repo:
        rows.append(('code', f'https://github.com/0xkuj/{repo}', '</> View source on GitHub'))
    return rows


def write(path, content):
    path = f'{OUT}/{path}'
    if not os.path.exists(path) or open(path).read() != content:
        open(path, 'w').write(content)


def pairs(items):
    return [items[i:i + 2] for i in range(0, len(items), 2)]


def draw(items):
    write('blank.svg', svg(0, 0, ''))
    write('filler-x.svg', svg(PAIR[2], PAIR[7], ''))
    write('spacer-x.svg', svg(PAIR[2], 0, ''))
    for group in pairs(items):
        min_h = max(body_height(PAIR, c[3])[2] for c in group)
        for slug, name, icon, desc, article, repo in group:
            rows = rows_for(article, repo)
            counts = repo_counts(repo) if repo else None
            for t, h in [(PAIR, min_h)] + [(t, 0) for t in SINGLE]:
                write(f'{slug}-{t[0]}.svg', body_svg(t, name, icon, desc, h))
                for i, (kind, _, label) in enumerate(rows):
                    write(f'{slug}-{kind}-{t[0]}.svg', row_svg(t, label, i == len(rows) - 1, counts if kind == 'code' else None))


def pic(sources, fallback, alt=''):
    srcs = ''.join(f'<source media="{m}" srcset="{RAW}{f}.svg">' for m, f in sources)
    return f'<picture>{srcs}<img src="{RAW}{fallback}.svg" alt="{html.escape(alt, quote=True)}" align="top"></picture>'


def link(url, inner):
    return f'<a href="{url}">{inner}</a>'


def pair_piece(fname, url, alt):
    return link(url, pic([(PAIR_MEDIA, f'{fname}-x')], 'blank', alt))


def single_piece(fname, url, alt):
    sources = [(PAIR_MEDIA, 'blank')] + [(m, f'{fname}-{s}') for s, m, *_ in SINGLE if m]
    return link(url, pic(sources, f'{fname}-s', alt))


def pieces(slug, name, desc, article, repo):
    rows = rows_for(article, repo)
    body = (slug, rows[0][1], f'{name} — {desc}')
    return body, [(f'{slug}-{kind}', url, label.removeprefix('</> ')) for kind, url, label in rows]


def section(items):
    filler = pic([(PAIR_MEDIA, 'filler-x')], 'blank')
    spacer = pic([(PAIR_MEDIA, 'spacer-x')], 'blank')
    out = []
    for group in pairs(items):  # two-column layout, interleaved line by line
        cards = [pieces(slug, name, desc, article, repo) for slug, name, _, desc, article, repo in group]
        lone = len(cards) == 1
        out += [pair_piece(*body) + (spacer if lone else '') for body, _ in cards]
        for i in range(max(len(rows) for _, rows in cards)):
            for _, rows in cards:
                out.append(pair_piece(*rows[i]) if i < len(rows) else filler)
            if lone:
                out.append(spacer)
    for slug, name, _, desc, article, repo in items:  # one-column layout
        body, rows = pieces(slug, name, desc, article, repo)
        out += [single_piece(*body)] + [single_piece(*r) for r in rows]
    return '<p align="center">' + ''.join(out) + '</p>'


def update_readme():
    path = f'{REPO}/README.md'
    r = open(path).read()
    for key, items in (('featured', FEATURED), ('more', MORE)):
        start, end = f'<!-- cards:{key}:start -->', f'<!-- cards:{key}:end -->'
        r = re.sub(re.escape(start) + r'.*?' + re.escape(end), lambda _: f'{start}\n{section(items)}\n{end}', r, flags=re.S)
    open(path, 'w').write(r)


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    for f in os.listdir(OUT):
        os.remove(f'{OUT}/{f}')
    draw(FEATURED)
    draw(MORE)
    if '--readme' in sys.argv:
        update_readme()
