"""Gera os cards animados (cards/claro e cards/escuro) e o README.md a partir de config/perfil.json.

Rode:  python scripts/build_profile.py
Dados: data/contributions.json e data/github_stats.json (vêm do fetch_contributions.py)
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
CARDS = ROOT / "cards"
CFG = json.loads((ROOT / "config" / "perfil.json").read_text(encoding="utf-8"))

FONT = "-apple-system,BlinkMacSystemFont,'SF Pro Display','Helvetica Neue','Segoe UI',Inter,Arial,sans-serif"
W = 1000

THEMES = {
    "claro": dict(text="#1d1d1f", sub="#6e6e73", ter="#86868b", line="#d2d2d7", accent="#0071e3",
                  tile="#f5f5f7", screen="#ffffff", skel="#e8e8ed", soft="#d6e6fb", btn_text="#ffffff",
                  levels=["#ebebef", "#c9dbf2", "#8fb6e8", "#4a8edb", "#0071e3"],
                  bronze="#b07a45", silver="#9a9aa1", gold="#c9a227"),
    "escuro": dict(text="#f5f5f7", sub="#a1a1a6", ter="#86868b", line="#3a3a3c", accent="#2997ff",
                   tile="#161617", screen="#1d1d1f", skel="#2c2c2e", soft="#0f2c4d", btn_text="#ffffff",
                   levels=["#1c1c1e", "#0d355f", "#15599f", "#1f7ae0", "#2997ff"],
                   bronze="#c68a50", silver="#aeaeb2", gold="#e0b93a"),
}
MESES = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]

BASE_CSS = """
  text { font-family: %s; }
  .in { opacity: 0; animation: in 1s cubic-bezier(.2,.7,.2,1) forwards; }
  @keyframes in { from { opacity: 0; transform: translateY(14px); } to { opacity: 1; transform: none; } }
  @media (prefers-reduced-motion: reduce) { * { animation: none !important; opacity: 1 !important; transform: none !important; } }
""" % FONT


def esc(s) -> str:
    return escape(str(s))


def num(n) -> str:
    return f"{n:,}".replace(",", ".")


def wrap(text: str, width: float, size: float, max_lines: int) -> list[str]:
    per = max(8, int(width / (size * 0.52)))
    lines, cur = [], ""
    for w in text.split():
        if len(cur) + len(w) + (1 if cur else 0) > per:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        lines.append(cur)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1].rstrip(".,;:") + "…"
    return lines


def tspans(lines, x, lh) -> str:
    return "".join(f'<tspan x="{x}" dy="{0 if i == 0 else lh}">{esc(l)}</tspan>' for i, l in enumerate(lines))


def svg(h: float, body: str, css: str = "", w: float = W) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w:g}" height="{h:g}" viewBox="0 0 {w:g} {h:g}">
<style>{BASE_CSS}{css}</style>
{body}
</svg>
"""


def smooth(points) -> str:
    """Caminho suave (Catmull-Rom → Bézier) passando pelos pontos."""
    d = f"M{points[0][0]:.1f},{points[0][1]:.1f}"
    for i in range(len(points) - 1):
        p0 = points[i - 1] if i else points[i]
        p1, p2 = points[i], points[i + 1]
        p3 = points[i + 2] if i + 2 < len(points) else p2
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f" C{c1[0]:.1f},{c1[1]:.1f} {c2[0]:.1f},{c2[1]:.1f} {p2[0]:.1f},{p2[1]:.1f}"
    return d


def odometer(x: float, y: float, value: str, size: float, color: str, uid: str, delay: float = 0) -> str:
    """Número que rola dígito a dígito até o valor, como um odômetro."""
    lh = size * 1.12
    out, cx = [], x
    for i, ch in enumerate(value):
        if ch.isdigit():
            d = int(ch)
            cid = f"o{uid}{i}"
            strip = "".join(f'<text x="{cx:.1f}" y="{y + k*lh:.1f}">{k % 10}</text>' for k in range(20))
            out.append(
                f'<clipPath id="{cid}"><rect x="{cx-2:.1f}" y="{y - size*0.86:.1f}" width="{size*0.7:.1f}" height="{lh:.1f}"/></clipPath>'
                f'<g clip-path="url(#{cid})"><g class="roll" style="--to:-{(10+d)*lh:.1f}px;animation-delay:{delay + i*.09:.2f}s">'
                f'<g font-size="{size}" font-weight="600" fill="{color}" letter-spacing="-1">{strip}</g></g></g>'
            )
            cx += size * 0.58
        else:
            out.append(f'<text x="{cx:.1f}" y="{y}" font-size="{size}" font-weight="600" fill="{color}">{esc(ch)}</text>')
            cx += size * (0.3 if ch in ".," else 0.62 if ch == "+" else 0.32)
    return "".join(out)


ODO_CSS = ".roll { animation: roll 2.2s cubic-bezier(.16,.84,.24,1) both; } @keyframes roll { from { transform: translateY(0); } to { transform: translateY(var(--to)); } }"


# ---------------------------------------------------------------- abertura
def hero(t, months: list[tuple[dt.date, int]], total: int) -> str:
    H = 470
    words = CFG["palavras"] + [CFG["palavras"][0]]
    n = len(CFG["palavras"])
    step = 84
    # cada palavra fica parada ~80% do seu trecho e depois sobe
    kf = []
    for i in range(n):
        a, b = i / n * 100, (i + 1) / n * 100
        kf.append(f"{a:.2f}% {{ transform: translateY(-{i*step}px); }} {a + (b-a)*0.8:.2f}% {{ transform: translateY(-{i*step}px); }}")
    kf.append(f"100% {{ transform: translateY(-{n*step}px); }}")
    slot = "".join(f'<text x="0" y="{230 + i*step}" font-size="68" font-weight="700" letter-spacing="-2.4" fill="{t["accent"]}">{esc(w)}</text>'
                   for i, w in enumerate(words))
    desc = wrap(CFG["descricao"], 500, 18, 3)

    # mini dashboard com as contribuições reais por mês
    px, py, pw, ph = 600, 40, 400, 390
    cx0, cx1, cy0, cy1 = px + 32, px + pw - 32, py + 190, py + 330
    mx = max(c for _, c in months) or 1
    pts = [(cx0 + i * (cx1 - cx0) / (len(months) - 1), cy1 - (c / mx) * (cy1 - cy0)) for i, (_, c) in enumerate(months)]
    line = smooth(pts)
    area = line + f" L{pts[-1][0]:.1f},{cy1} L{pts[0][0]:.1f},{cy1} Z"
    grid = "".join(f'<line x1="{cx0}" y1="{cy0 + k*(cy1-cy0)/3:.1f}" x2="{cx1}" y2="{cy0 + k*(cy1-cy0)/3:.1f}" stroke="{t["line"]}" stroke-dasharray="2 5"/>' for k in range(4))
    labels = "".join(f'<text x="{p[0]:.1f}" y="{cy1 + 26}" text-anchor="middle" font-size="12" fill="{t["ter"]}">{MESES[m.month-1][0]}</text>'
                     for p, (m, _) in zip(pts, months))
    ex, ey = pts[-1]
    panel = f"""
<g class="in" style="animation-delay:.3s">
<rect x="{px}" y="{py}" width="{pw}" height="{ph}" rx="28" fill="{t['tile']}"/>
<circle cx="{px+36}" cy="{py+44}" r="5" fill="#30d158"><animate attributeName="opacity" values="1;.25;1" dur="1.6s" repeatCount="indefinite"/></circle>
<text x="{px+50}" y="{py+49}" font-size="14" fill="{t['sub']}">Ao vivo · atualizado todo dia</text>
<text x="{px+32}" y="{py+92}" font-size="15" fill="{t['sub']}">Contribuições no último ano</text>
{odometer(px+30, py+156, num(total), 60, t['text'], 'h' + t['accent'][1:], .5)}
{grid}
<defs><linearGradient id="ar" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{t['accent']}" stop-opacity=".28"/><stop offset="1" stop-color="{t['accent']}" stop-opacity="0"/></linearGradient></defs>
<path d="{area}" fill="url(#ar)" class="area"/>
<path d="{line}" pathLength="1" fill="none" stroke="{t['accent']}" stroke-width="3.5" stroke-linecap="round" class="draw"/>
<g class="endp"><circle cx="{ex:.1f}" cy="{ey:.1f}" r="7" fill="{t['accent']}"/>
<circle cx="{ex:.1f}" cy="{ey:.1f}" r="7" fill="none" stroke="{t['accent']}" stroke-width="2"><animate attributeName="r" values="7;22" dur="1.8s" repeatCount="indefinite"/><animate attributeName="opacity" values=".8;0" dur="1.8s" repeatCount="indefinite"/></circle></g>
{labels}
</g>"""
    body = f"""
<defs><clipPath id="slot"><rect x="0" y="160" width="590" height="{step}"/></clipPath></defs>
<text class="in" x="0" y="64" font-size="15" font-weight="600" letter-spacing="2.2" fill="{t['accent']}">{esc(CFG['eyebrow'].upper())}</text>
<text class="in" style="animation-delay:.1s" x="0" y="148" font-size="68" font-weight="700" letter-spacing="-2.4" fill="{t['text']}">{esc(CFG['manchete'])}</text>
<g clip-path="url(#slot)"><g class="words">{slot}</g></g>
<text class="in" style="animation-delay:.25s" x="0" y="300" font-size="24" font-weight="600" letter-spacing="-.4" fill="{t['text']}">{esc(CFG['nome'])}</text>
<text class="in" style="animation-delay:.35s" x="0" y="334" font-size="18" fill="{t['sub']}">{tspans(desc, 0, 27)}</text>
<text class="in" style="animation-delay:.45s" x="0" y="{334 + 27*len(desc) + 26}" font-size="15" fill="{t['ter']}">{esc(CFG['local'])}  ·  {CFG['anos_experiencia']} anos em dados e BI</text>
{panel}"""
    css = (f".words {{ animation: words {n*2.6:.1f}s cubic-bezier(.7,0,.3,1) infinite; }} @keyframes words {{ {' '.join(kf)} }} "
           ".draw { stroke-dasharray: 1; stroke-dashoffset: 1; animation: draw 2.4s cubic-bezier(.4,0,.2,1) .7s forwards; } "
           "@keyframes draw { to { stroke-dashoffset: 0; } } "
           ".area, .endp { opacity: 0; animation: show .8s ease-out 2.6s forwards; } @keyframes show { to { opacity: 1; } } " + ODO_CSS)
    return svg(H, body, css)


# ---------------------------------------------------------------- números
def numbers(t, values: list[tuple[str, str]]) -> str:
    col = W / len(values)
    items = "".join(
        f'{odometer(i*col, 92, v, 64, t["text"], f"n{i}{t["accent"][1:]}", .2 + i*.15)}'
        f'<text class="in" style="animation-delay:{.4 + i*.15:.2f}s" x="{i*col}" y="130" font-size="16" fill="{t["sub"]}">{esc(l)}</text>'
        for i, (v, l) in enumerate(values)
    )
    return svg(170, f'<line x1="0" y1="10.5" x2="{W}" y2="10.5" stroke="{t["line"]}"/>{items}'
                    f'<line x1="0" y1="169.5" x2="{W}" y2="169.5" stroke="{t["line"]}"/>', ODO_CSS)


def header(t, title: str, link: bool) -> str:
    right = f'<text x="{W}" y="74" text-anchor="end" font-size="18" fill="{t["accent"]}">Ver todos ›</text>' if link else ""
    return svg(100, f'<text class="in" x="0" y="74" font-size="48" font-weight="700" letter-spacing="-1.6" fill="{t["text"]}">{esc(title)}</text>{right}')


# ---------------------------------------------------------------- relatórios
def preview(t, kind: int, x: float, y: float, w: float, h: float) -> str:
    """Miniatura animada de dashboard (barras, linha ou rosca), em loop."""
    s = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="18" fill="{t["screen"]}"/>',
         f'<rect x="{x+22}" y="{y+22}" width="90" height="9" rx="4.5" fill="{t["skel"]}"/>']
    for k in range(3):  # cartões de KPI
        kx = x + 22 + k * (w - 44) / 3
        s.append(f'<rect x="{kx:.1f}" y="{y+46}" width="{(w-44)/3 - 10:.1f}" height="54" rx="10" fill="{t["tile"]}"/>'
                 f'<rect x="{kx+12:.1f}" y="{y+60}" width="44" height="7" rx="3.5" fill="{t["skel"]}"/>'
                 f'<rect class="kpi" style="animation-delay:{k*.15:.2f}s" x="{kx+12:.1f}" y="{y+76}" width="{58 - k*10}" height="13" rx="4" fill="{t["accent"] if k == 0 else t["sub"]}"/>')
    top, bot = y + 120, y + h - 22
    if kind == 0:
        vals = [.35, .55, .45, .7, .6, .85, .75, 1, .9, .68]
        bw = (w - 44) / len(vals)
        for i, v in enumerate(vals):
            bh = (bot - top) * v
            s.append(f'<rect class="bar" style="animation-delay:{i*.07:.2f}s" x="{x+22+i*bw+bw*.18:.1f}" y="{bot-bh:.1f}" width="{bw*.64:.1f}" height="{bh:.1f}" rx="4" '
                     f'fill="{t["accent"] if i == 7 else t["soft"]}"/>')
    elif kind == 1:
        vals = [.3, .45, .38, .6, .52, .74, .66, .9, .82, .95]
        pts = [(x + 22 + i * (w - 44) / (len(vals) - 1), bot - (bot - top) * v) for i, v in enumerate(vals)]
        d = smooth(pts)
        s.append(f'<path d="{d} L{pts[-1][0]:.1f},{bot} L{pts[0][0]:.1f},{bot} Z" fill="{t["soft"]}" class="ar2"/>')
        s.append(f'<path d="{d}" pathLength="1" fill="none" stroke="{t["accent"]}" stroke-width="3" stroke-linecap="round" class="ln2"/>')
    else:
        cx, cy, r = x + w * 0.3, (top + bot) / 2, (bot - top) / 2 - 2
        segs = [(.46, t["accent"]), (.3, t["sub"]), (.24, t["skel"])]
        acc = 0
        for i, (frac, col) in enumerate(segs):
            s.append(f'<circle class="seg" style="--f:{frac:.3f};animation-delay:{i*.35:.2f}s" cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="none" stroke="{col}" '
                     f'stroke-width="16" pathLength="1" transform="rotate({-90 + acc*360:.1f} {cx:.1f} {cy:.1f})"/>')
            acc += frac
        for i in range(3):
            ly = top + 14 + i * 26
            s.append(f'<circle cx="{x+w*.6:.1f}" cy="{ly}" r="5" fill="{segs[i][1]}"/><rect x="{x+w*.6+14:.1f}" y="{ly-4}" width="{90 - i*18}" height="8" rx="4" fill="{t["skel"]}"/>')
    return "".join(s)


PREVIEW_CSS = """
  .bar { transform-box: fill-box; transform-origin: 50% 100%; animation: bar 6s cubic-bezier(.2,.8,.2,1) infinite; }
  @keyframes bar { 0% { transform: scaleY(0); } 18%,82% { transform: scaleY(1); } 96%,100% { transform: scaleY(0); } }
  .kpi { transform-box: fill-box; transform-origin: 0 50%; animation: kpi 6s cubic-bezier(.2,.8,.2,1) infinite; }
  @keyframes kpi { 0% { transform: scaleX(0); } 15%,85% { transform: scaleX(1); } 97%,100% { transform: scaleX(0); } }
  .ln2 { stroke-dasharray: 1; animation: ln 6s cubic-bezier(.4,0,.2,1) infinite; }
  @keyframes ln { 0% { stroke-dashoffset: 1; } 30%,85% { stroke-dashoffset: 0; } 97%,100% { stroke-dashoffset: 1; } }
  .ar2 { animation: ar 6s ease infinite; } @keyframes ar { 0%,15% { opacity: 0; } 35%,85% { opacity: 1; } 97%,100% { opacity: 0; } }
  .seg { stroke-dasharray: var(--f) 1; stroke-dashoffset: var(--f); animation: seg 6s cubic-bezier(.4,0,.2,1) infinite; }
  @keyframes seg { 0% { stroke-dashoffset: var(--f); } 25%,85% { stroke-dashoffset: 0; } 97%,100% { stroke-dashoffset: var(--f); } }
"""


def report(t, p: dict, i: int) -> str:
    H = 300
    desc = wrap(p["descricao"], 400, 18, 3)
    body = f"""
<rect x="0" y="10" width="{W}" height="{H-20}" rx="30" fill="{t['tile']}"/>
<text x="52" y="78" font-size="14" font-weight="600" letter-spacing="1.8" fill="{t['accent']}">{esc(p['ferramenta'].upper())}</text>
<text x="52" y="124" font-size="38" font-weight="700" letter-spacing="-1.1" fill="{t['text']}">{esc(p['titulo'])}</text>
<text x="52" y="164" font-size="18" fill="{t['sub']}">{tspans(desc, 52, 27)}</text>
<text x="52" y="{H-50}" font-size="18" font-weight="500" fill="{t['accent']}">Abrir relatório ›</text>
{preview(t, i % 3, 540, 40, 420, H - 80)}"""
    return svg(H, body, PREVIEW_CSS)


# ---------------------------------------------------------------- projetos
def pipeline(t) -> str:
    H = 330
    stages = [("Fontes", "SAP · APIs · SQL", t["sub"]), ("Bronze", "dado bruto", t["bronze"]),
              ("Silver", "limpo e validado", t["silver"]), ("Gold", "star schema", t["gold"]),
              ("Power BI", "decisão", t["accent"])]
    nw, nh, y0 = 150, 92, 170
    gap = (W - 104 - nw * len(stages)) / (len(stages) - 1)
    xs = [52 + i * (nw + gap) for i in range(len(stages))]
    cy = y0 + nh / 2
    path = f"M{xs[0] + nw/2:.1f},{cy} L{xs[-1] + nw/2:.1f},{cy}"
    nodes = []
    for i, ((name, sub, col), x) in enumerate(zip(stages, xs)):
        nodes.append(f"""<g class="in" style="animation-delay:{.15 + i*.12:.2f}s">
<rect x="{x:.1f}" y="{y0}" width="{nw}" height="{nh}" rx="18" fill="{t['screen']}" stroke="{t['line']}"/>
<circle cx="{x+24:.1f}" cy="{y0+30}" r="7" fill="{col}"/>
<text x="{x+40:.1f}" y="{y0+36}" font-size="18" font-weight="600" fill="{t['text']}">{esc(name)}</text>
<text x="{x+20:.1f}" y="{y0+68}" font-size="14" fill="{t['sub']}">{esc(sub)}</text></g>""")
    packets = "".join(
        f'<circle r="5" fill="{t["accent"]}"><animateMotion dur="5s" begin="{-k*0.71:.2f}s" repeatCount="indefinite" path="{path}"/>'
        f'<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;.08;.92;1" dur="5s" begin="{-k*0.71:.2f}s" repeatCount="indefinite"/></circle>'
        for k in range(7)
    )
    body = f"""
<rect x="0" y="10" width="{W}" height="{H-20}" rx="30" fill="{t['tile']}"/>
<text x="52" y="78" font-size="14" font-weight="600" letter-spacing="1.8" fill="{t['accent']}">ARQUITETURA MEDALHÃO</text>
<text x="52" y="122" font-size="34" font-weight="700" letter-spacing="-1" fill="{t['text']}">Do dado bruto ao dashboard.</text>
<line x1="{xs[0]+nw/2:.1f}" y1="{cy}" x2="{xs[-1]+nw/2:.1f}" y2="{cy}" stroke="{t['line']}" stroke-width="2" stroke-dasharray="3 6"/>
{packets}
{''.join(nodes)}"""
    return svg(H, body)


def project(t, p: dict, i: int) -> str:
    w, H = 333.33, 250
    x0 = 8 if i % 3 else 0
    tx = x0 + 28
    desc = wrap(p["descricao"], w - 70, 15, 4)
    body = f"""<g class="in" style="animation-delay:{(i % 3) * .12:.2f}s">
<rect x="{x0}" y="10" width="{w - 8:.1f}" height="{H-20}" rx="26" fill="{t['tile']}"/>
<text x="{tx}" y="58" font-size="13" font-weight="600" letter-spacing="1.6" fill="{t['accent']}">{esc(p['ferramenta'].upper())}</text>
<text x="{tx}" y="94" font-size="24" font-weight="700" letter-spacing="-.6" fill="{t['text']}">{esc(p['titulo'])}</text>
<text x="{tx}" y="126" font-size="15" fill="{t['sub']}">{tspans(desc, tx, 22)}</text>
<text x="{tx}" y="{H-38}" font-size="16" font-weight="500" fill="{t['accent']}">Ver código ›</text></g>"""
    return svg(H, body, w=w)


# ---------------------------------------------------------------- atividade
def activity(t, days: list[dict]) -> tuple[str, int]:
    by = {d["date"]: d["count"] for d in days}
    end = dt.date.fromisoformat(max(by))
    start = end - dt.timedelta(days=(end.weekday() + 1) % 7) - dt.timedelta(weeks=52)
    span = [start + dt.timedelta(i) for i in range((end - start).days + 1)]
    total = sum(by.get(d.isoformat(), 0) for d in span if d > end - dt.timedelta(days=365))
    nz = sorted(c for c in (by.get(d.isoformat(), 0) for d in span) if c)
    q = [nz[min(len(nz) - 1, int(p * len(nz)))] for p in (.25, .5, .75)] if nz else [1, 2, 3]
    lvl = lambda c: 0 if c <= 0 else 1 if c <= q[0] else 2 if c <= q[1] else 3 if c <= q[2] else 4

    left, top, cell = 34, 150, 14
    step = (W - left) / 53
    cells, months, last = [], [], None
    for i, d in enumerate(span):
        col, row = divmod(i, 7)
        x, y = left + col * step, top + row * step
        c = by.get(d.isoformat(), 0)
        cls = "c now" if d == end else "c"
        cells.append(f'<rect class="{cls}" x="{x:.1f}" y="{y:.1f}" width="{cell}" height="{cell}" rx="4" fill="{t["levels"][lvl(c)]}" '
                     f'style="animation-delay:{(col + row) * .02:.3f}s"><title>{c} em {d:%d/%m/%Y}</title></rect>')
        if row == 0 and d.month != last and d.day <= 7 and col < 52:
            months.append(f'<text x="{x:.1f}" y="{top-14}" font-size="13" fill="{t["ter"]}">{MESES[d.month-1]}</text>')
            last = d.month
    wd = "".join(f'<text x="0" y="{top + r*step + 11:.1f}" font-size="12" fill="{t["ter"]}">{n}</text>'
                 for r, n in ((1, "Seg"), (3, "Qua"), (5, "Sex")))
    body = f"""<text class="in" x="0" y="64" font-size="48" font-weight="700" letter-spacing="-1.6" fill="{t['text']}">Atividade</text>
<text class="in" style="animation-delay:.15s" x="{W}" y="64" text-anchor="end" font-size="18" fill="{t['sub']}"><tspan fill="{t['text']}" font-weight="600">{num(total)}</tspan> contribuições no último ano</text>
{''.join(months)}{wd}{''.join(cells)}"""
    css = (".c { opacity: 0; transform-box: fill-box; transform-origin: center; animation: pop .6s cubic-bezier(.2,1.4,.4,1) forwards; } "
           "@keyframes pop { from { opacity: 0; transform: scale(.3); } to { opacity: 1; transform: scale(1); } } "
           ".now { animation: pop .6s cubic-bezier(.2,1.4,.4,1) forwards, beat 1.6s ease-in-out 2.5s infinite; } "
           "@keyframes beat { 0%,100% { transform: scale(1); } 50% { transform: scale(1.35); } }")
    return svg(top + 7 * step + 10, body, css), total


# ---------------------------------------------------------------- ferramentas
def tools(t) -> str:
    H = 190
    items = CFG["tech_stack"]
    seq = "     ·     ".join(items) + "     ·     "
    size = 40
    L = sum(len(s) for s in items) * size * 0.56 + len(items) * size * 2.2  # largura forçada com textLength
    copies = "".join(
        f'<text x="{k*L:.1f}" y="150" font-size="{size}" font-weight="600" letter-spacing="-1" fill="{t["ter"]}" '
        f'textLength="{L:.1f}" lengthAdjust="spacing" xml:space="preserve">{esc(seq)}</text>'
        for k in range(3)
    )
    body = f"""<defs><linearGradient id="fd" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".08" stop-color="#fff"/>
<stop offset=".92" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
<mask id="mk"><rect x="0" y="90" width="{W}" height="90" fill="url(#fd)"/></mask></defs>
<text class="in" x="0" y="64" font-size="48" font-weight="700" letter-spacing="-1.6" fill="{t['text']}">Ferramentas</text>
<g mask="url(#mk)"><g class="mq">{copies}</g></g>"""
    css = f".mq {{ animation: mq {L/45:.1f}s linear infinite; }} @keyframes mq {{ to {{ transform: translateX(-{L:.1f}px); }} }}"
    return svg(H, body, css)


# ---------------------------------------------------------------- contato
def contact(t) -> str:
    H = 250
    return svg(H, f"""<rect x="0" y="10" width="{W}" height="{H-20}" rx="30" fill="{t['tile']}"/>
<text class="in" x="{W/2}" y="122" text-anchor="middle" font-size="56" font-weight="700" letter-spacing="-1.8" fill="{t['text']}">{esc(CFG['contato_titulo'])}</text>
<text class="in" style="animation-delay:.15s" x="{W/2}" y="170" text-anchor="middle" font-size="20" fill="{t['sub']}">{esc(CFG['contato_texto'])}</text>""")


LINKS = [("linkedin", "LinkedIn"), ("email", "E-mail"), ("portfolio", "Portfólio"), ("certificados", "Certificados")]


def button(t, label: str, primary: bool) -> str:
    w, h = 250, 84
    if primary:
        shape = f'<rect x="10" y="14" width="{w-20}" height="56" rx="28" fill="{t["accent"]}"/>'
        color = t["btn_text"]
    else:
        shape = f'<rect x="11" y="15" width="{w-22}" height="54" rx="27" fill="none" stroke="{t["accent"]}" stroke-width="2"/>'
        color = t["accent"]
    return svg(h, f'{shape}<text x="{w/2}" y="49" text-anchor="middle" font-size="19" font-weight="600" fill="{color}">{esc(label)}</text>', w=w)


# ---------------------------------------------------------------- README
def main() -> None:
    days = json.loads((ROOT / "data" / "contributions.json").read_text(encoding="utf-8"))["days"]
    gh = json.loads((ROOT / "data" / "github_stats.json").read_text(encoding="utf-8"))
    for f in CARDS.rglob("*.svg"):
        f.unlink()

    # contribuições por mês, últimos 12 meses (inclui o mês atual)
    by = {dt.date.fromisoformat(d["date"]): d["count"] for d in days}
    today = max(by)
    months, m = [], today.replace(day=1)
    for _ in range(12):
        months.insert(0, (m, sum(c for d, c in by.items() if d.year == m.year and d.month == m.month)))
        m = (m - dt.timedelta(days=1)).replace(day=1)

    def emit(name: str, fn, *args):
        res = None
        for theme, t in THEMES.items():
            out = CARDS / theme / name
            out.parent.mkdir(parents=True, exist_ok=True)
            res = fn(t, *args)
            out.write_text(res[0] if isinstance(res, tuple) else res, encoding="utf-8")
        return res

    _, total = emit("atividade.svg", activity, days)
    emit("hero.svg", hero, months, total)
    emit("numeros.svg", numbers, [
        (f"{CFG['anos_experiencia']}+", "anos de experiência"),
        (str(CFG["certificacoes"]), "cursos e certificações"),
        (str(len(CFG["relatorios"]) + len(CFG["projetos"])), "relatórios e projetos"),
        (str(gh["repositorios"]), "repositórios públicos"),
    ])
    emit("pipeline.svg", pipeline)
    emit("ferramentas.svg", tools)
    emit("contato.svg", contact)

    def pic(name: str, alt: str, href: str | None = None, width: str = "100%") -> str:
        tag = (f'<picture><source media="(prefers-color-scheme: dark)" srcset="./cards/escuro/{name}" />'
               f'<img src="./cards/claro/{name}" width="{width}" alt="{esc(alt)}" /></picture>')
        return f'<a href="{esc(href)}">{tag}</a>' if href else tag

    def head(key: str) -> str:
        title, ver = CFG[f"{key}_titulo"], CFG.get(f"{key}_ver_todos", "#")
        emit(f"titulo-{key}.svg", header, title, ver != "#")
        return pic(f"titulo-{key}.svg", title, ver if ver != "#" else None)

    reports = []
    for i, p in enumerate(CFG["relatorios"]):
        emit(f"relatorio-{i+1}.svg", report, p, i)
        reports.append(pic(f"relatorio-{i+1}.svg", f"{p['titulo']}: {p['descricao']}", p["link"]))

    projs, rowbuf = [], []
    for i, p in enumerate(CFG["projetos"]):
        emit(f"projeto-{i+1}.svg", project, p, i)
        rowbuf.append(pic(f"projeto-{i+1}.svg", f"{p['titulo']}: {p['descricao']}", p["link"], "33.333%"))
        if len(rowbuf) == 3 or i == len(CFG["projetos"]) - 1:
            projs.append("".join(rowbuf))
            rowbuf = []

    L = CFG["links"]
    buttons = []
    for key, label in LINKS:
        if L.get(key) and L[key] != "#":
            emit(f"botao-{key}.svg", button, label, not buttons)
            buttons.append(pic(f"botao-{key}.svg", label, L[key], "25%"))

    readme = f"""<!-- Gerado por scripts/build_profile.py. Para mudar textos, links, relatórios
e projetos, edite config/perfil.json: o GitHub Action refaz tudo sozinho. -->

{pic('hero.svg', f"{CFG['nome']}. {CFG['eyebrow']}. {CFG['descricao']}")}
{pic('numeros.svg', 'Números')}
<br><br>

{head('relatorios')}<br>
{'<br>'.join(reports)}
<br><br>

{head('projetos')}<br>
{pic('pipeline.svg', 'Arquitetura medalhão: Fontes, Bronze, Silver, Gold e Power BI')}<br>
{'<br>'.join(projs)}
<br><br>

{pic('atividade.svg', f'{num(total)} contribuições no último ano')}
<br><br>

{pic('ferramentas.svg', 'Ferramentas: ' + ', '.join(CFG['tech_stack']))}
<br><br>

{pic('contato.svg', CFG['contato_titulo'])}
<p align="center">{''.join(buttons)}</p>
"""
    (ROOT / "README.md").write_text(readme, encoding="utf-8")
    print("README.md e", len(list(CARDS.rglob('*.svg'))), "cards gerados")


if __name__ == "__main__":
    main()
