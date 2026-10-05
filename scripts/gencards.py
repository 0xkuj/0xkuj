"""Generate the tweak cards shown in README.md.

Each card is a stack of linked SVG pieces (a body plus one row per link),
rendered in three widths and picked per screen size via <picture>.

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

# Cards fill GitHub's README column. Each piece sits on its own line, so a piece
# wider than the column scales down to fit it exactly; tiers are sized to the
# widest column they serve and split so nothing shrinks below MIN_SCALE.
def column_width(vw):
    """GitHub profile README column width for a given viewport width."""
    if vw >= 1280:
        return 846
    if vw >= 1012:
        return vw - 434
    if vw >= 768:
        return vw - 370
    return vw - 82


MIN_SCALE = 0.8


def make_tiers():
    tiers, top = [], 1280
    while top >= 320:
        w, v = column_width(top), top
        while v - 1 >= 320 and column_width(v - 1) / w >= MIN_SCALE and column_width(v - 1) <= w:
            v -= 1
        tiers.append((v, w))
        top = v - 1
    out = []
    for i, (vmin, w) in enumerate(tiers):
        k = min(max((w - 300) / 546, 0), 1)  # 0 at 300px .. 1 at 846px
        media = None if i == len(tiers) - 1 else f'(min-width: {vmin}px)'
        # suffix, media query, width, icon, name px, desc px, row height, row px
        out.append((str(w), media, w, round(48 + 12 * k), round(15 + 3 * k), round(13 + 2 * k), round(38 + 6 * k), round(13 + 2 * k)))
    return out


TIERS = make_tiers()
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


def body_svg(t, name, icon, desc):
    _, _, W, ic, nsz, dsz, _, _ = t
    pad = 16
    x = pad + ic + 14
    lines = wrap(desc, dsz, W - x - pad)
    lh = round(dsz * 1.4)
    text_h = nsz + 8 + lh * len(lines)
    H = max(ic + 2 * pad, text_h + 2 * pad + 4)
    ty = (H - text_h) / 2 + nsz
    e = lambda s: html.escape(s, quote=True)
    desc_t = ''.join(f'<text x="{x}" y="{ty + 8 + lh * (i + 1) - 3:.0f}" font-family="{FONT}" font-size="{dsz}" fill="{DESC}">{e(l)}</text>'
                     for i, l in enumerate(lines))
    iy = (H - ic) / 2
    return svg(W, H,
               f'<defs><clipPath id="c"><rect x="{pad}" y="{iy}" width="{ic}" height="{ic}" rx="{ic * .225:.1f}"/></clipPath></defs>'
               f'<path d="{shape(W, H, True, False)}" fill="{BG}" stroke="{BORDER}"/>'
               f'<image x="{pad}" y="{iy}" width="{ic}" height="{ic}" clip-path="url(#c)" href="data:image/png;base64,{icon_b64(icon)}"/>'
               f'<text x="{x}" y="{ty:.0f}" font-family="{FONT}" font-size="{nsz}" font-weight="600" fill="{NAME}">{e(name)}</text>{desc_t}')


def row_svg(t, label, last, counts=None):
    _, _, W, _, _, _, H, sz = t
    pad = 16
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
    return svg(W, H,
               f'<path d="{shape(W, H, False, last)}" fill="{BG}" stroke="{BORDER}"/>'
               f'<text x="{pad}" y="{cy:.1f}" font-family="{FONT}" font-size="{sz}" fill="{LINK}" font-weight="600">{html.escape(label)}</text>'
               f'{extra}'
               f'<path d="M{W - pad - 5},{H / 2 - 5} l5,5 l-5,5" fill="none" stroke="{DESC}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>')


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


def draw(slug, name, icon, desc, article, repo):
    rows = rows_for(article, repo)
    counts = repo_counts(repo) if repo else None
    for t in TIERS:
        write(f'{slug}-{t[0]}.svg', body_svg(t, name, icon, desc))
        for i, (kind, _, label) in enumerate(rows):
            write(f'{slug}-{kind}-{t[0]}.svg', row_svg(t, label, i == len(rows) - 1, counts if kind == 'code' else None))


def piece(fname, url, alt):
    srcs = ''.join(f'<source media="{m}" srcset="{RAW}{fname}-{s}.svg">' for s, m, *_ in TIERS if m)
    return f'<a href="{url}"><picture>{srcs}<img src="{RAW}{fname}-s.svg" alt="{html.escape(alt, quote=True)}" align="top"></picture></a><br>'


def card_html(slug, name, icon, desc, article, repo):
    rows = rows_for(article, repo)
    out = [piece(slug, rows[0][1], f'{name} — {desc}')]
    out += [piece(f'{slug}-{kind}', url, label.removeprefix('</> ')) for kind, url, label in rows]
    return '\n'.join(out)


def section(items):
    return '<p align="center">\n' + '\n<br>\n'.join(card_html(*c) for c in items) + '\n</p>'


def update_readme():
    path = f'{REPO}/README.md'
    r = open(path).read()
    for key, items in (('featured', FEATURED), ('more', MORE)):
        start, end = f'<!-- cards:{key}:start -->', f'<!-- cards:{key}:end -->'
        r = re.sub(re.escape(start) + r'.*?' + re.escape(end), lambda _: f'{start}\n{section(items)}\n{end}', r, flags=re.S)
    open(path, 'w').write(r)


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    for c in FEATURED + MORE:
        draw(*c)
    if '--readme' in sys.argv:
        update_readme()
