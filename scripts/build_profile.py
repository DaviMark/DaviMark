"""Gera o painel do perfil (cards/*.svg) e o README.md a partir de config/perfil.json.

Rode:  python scripts/build_profile.py
Dados: data/contributions.json e data/github_stats.json (vêm do fetch_contributions.py)

O painel é montado em peças lado a lado para que cada projeto continue clicável.
"""
from __future__ import annotations

import base64
import datetime as dt
import json
import os
import urllib.request
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
CARDS = ROOT / "cards"
CFG = json.loads((ROOT / "config" / "perfil.json").read_text(encoding="utf-8"))

FONT = "-apple-system,BlinkMacSystemFont,'Segoe UI','Noto Sans',Helvetica,Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"

BG = "#0a0d0b"        # fundo dos cards
EDGE = "#1f2a23"      # borda
CHIP = "#121815"
TEXT = "#e8ede9"
SUB = "#9aa39d"
TER = "#6b756e"
GREEN = "#4ade80"
GREEN_D = "#22c55e"
LEVELS = ["#151c17", "#14532d", "#166534", "#16a34a", "#4ade80"]
MESES = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
M = 6  # margem de cada peça (vira o espaço entre os cards)

D = "https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/"
ICON_URLS = {  # logotipos oficiais, baixados uma vez e guardados em assets/icons
    "Power BI": "https://upload.wikimedia.org/wikipedia/commons/c/cf/New_Power_BI_Logo.svg",
    "SQL Server": D + "microsoftsqlserver/microsoftsqlserver-original.svg",
    "Python": D + "python/python-original.svg",
    "BigQuery": "https://cdn.simpleicons.org/googlebigquery",
    "Databricks": "https://cdn.simpleicons.org/databricks",
    "Spark": D + "apachespark/apachespark-original.svg",
    "Airflow": D + "apacheairflow/apacheairflow-original.svg",
    "Google Cloud": D + "googlecloud/googlecloud-original.svg",
    "Git": D + "git/git-original.svg",
    "GitHub Actions": D + "githubactions/githubactions-original.svg",
    "PostgreSQL": D + "postgresql/postgresql-original.svg",
    "SAP HANA": "https://cdn.simpleicons.org/sap",
}
_ICON_CACHE: dict[str, str | None] = {}


def logo(name: str) -> str | None:
    """data URI do logotipo da ferramenta (ou None, se não houver)."""
    if name in _ICON_CACHE:
        return _ICON_CACHE[name]
    slug = name.lower().replace(" ", "-")
    path = ROOT / "assets" / "icons" / f"{slug}.svg"
    if not path.exists() and name in ICON_URLS:
        try:
            req = urllib.request.Request(ICON_URLS[name], headers={"User-Agent": "profile-builder"})
            with urllib.request.urlopen(req, timeout=20) as r:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(r.read())
        except Exception as e:
            print("ícone indisponível:", name, e)
    uri = f"data:image/svg+xml;base64,{base64.b64encode(path.read_bytes()).decode()}" if path.exists() else None
    _ICON_CACHE[name] = uri
    return uri


TOOLS = {  # reserva quando não há logotipo: cor, cor do texto, sigla
    "Power BI": ("#F2C811", "#1a1a1a", "BI"), "DAX": ("#00897B", "#fff", "DAX"),
    "Power Query": ("#D13348", "#fff", "PQ"), "SQL": ("#336791", "#fff", "SQL"),
    "Python": ("#3776AB", "#FFD43B", "Py"), "BigQuery": ("#4285F4", "#fff", "BQ"),
    "Databricks": ("#FF3621", "#fff", "DB"), "Spark": ("#E25A1C", "#fff", "Sp"),
    "Airflow": ("#017CEE", "#fff", "Af"), "Git": ("#F05032", "#fff", "Git"),
    "SAP HANA": ("#0FAAFF", "#fff", "SAP"), "Web": ("#0e7490", "#ecfeff", "</>"),
}

CSS = f"""
  text {{ font-family: {FONT}; }}
  .mono {{ font-family: {MONO}; }}
  .in {{ opacity: 0; animation: in .8s cubic-bezier(.2,.7,.2,1) forwards; }}
  @keyframes in {{ from {{ opacity: 0; transform: translateY(8px); }} to {{ opacity: 1; transform: none; }} }}
  @media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; opacity: 1 !important; transform: none !important; }} }}
"""


def esc(s) -> str:
    return escape(str(s))


def num(n) -> str:
    return f"{n:,}".replace(",", ".")


def wrap(text: str, width: float, size: float, max_lines: int = 9) -> list[str]:
    per = max(8, int(width / (size * 0.5)))
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


def svg(w: float, h: float, body: str, css: str = "") -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:g}" height="{h:g}" viewBox="0 0 {w:g} {h:g}">\n'
            f'<style>{CSS}{css}</style>\n{body}\n</svg>\n')


def card(w: float, h: float) -> str:
    return f'<rect x="{M}" y="{M}" width="{w-2*M:g}" height="{h-2*M:g}" rx="14" fill="{BG}" stroke="{EDGE}" stroke-width="1.2"/>'


def tool_icon(x, y, s, name) -> str:
    uri = logo(name)
    if uri:
        pad = s * .2
        return (f'<rect x="{x:.1f}" y="{y:.1f}" width="{s}" height="{s}" rx="{s*.24:.1f}" fill="{CHIP}" stroke="{EDGE}"/>'
                f'<image href="{uri}" x="{x+pad:.1f}" y="{y+pad:.1f}" width="{s-2*pad:.1f}" height="{s-2*pad:.1f}"/>')
    bg, fg, label = TOOLS.get(name, ("#2a2f2c", TEXT, name[:2]))
    fs = s * (0.42 if len(label) <= 2 else 0.32)
    return (f'<rect x="{x:.1f}" y="{y:.1f}" width="{s}" height="{s}" rx="{s*.24:.1f}" fill="{bg}"/>'
            f'<text x="{x + s/2:.1f}" y="{y + s/2 + fs*.36:.1f}" text-anchor="middle" font-size="{fs:.1f}" font-weight="800" fill="{fg}">{esc(label)}</text>')


# ---- ícones de linha (16x16), desenhados em verde
IC = {
    "pin": "M8 15s5-4.6 5-8.5A5 5 0 0 0 3 6.5C3 10.4 8 15 8 15zM8 8.5a2 2 0 1 0 0-4 2 2 0 0 0 0 4z",
    "link": "M6.5 9.5l3-3M7 4.5l1-1a2.8 2.8 0 0 1 4 4l-1 1M9 11.5l-1 1a2.8 2.8 0 0 1-4-4l1-1",
    "mail": "M2 4h12v8H2zM2 4l6 5 6-5",
    "cal": "M2.5 3.5h11v10h-11zM2.5 6.5h11M5.5 2v3M10.5 2v3",
    "star": "M8 1.8l1.8 3.7 4 .6-2.9 2.8.7 4L8 11l-3.6 1.9.7-4L2.2 6.1l4-.6z",
    "user": "M8 8a3 3 0 1 0 0-6 3 3 0 0 0 0 6zM2.5 14.5a5.5 5.5 0 0 1 11 0",
    "chart": "M2 13.5l4-5 3 3 5-7",
    "code": "M5.5 4.5L2 8l3.5 3.5M10.5 4.5L14 8l-3.5 3.5",
    "rocket": "M9.5 2.5c2 0 4 0 4 0s0 2 0 4L8 12l-4-4zM4 8l-2 .5L3.5 6M8 12l-.5 2 2.5-1.5M10.5 5.5h.01",
    "repo": "M3.5 2.5h9v11h-9zM3.5 11h9M6 2.5v6l1.5-1 1.5 1v-6",
    "commit": "M8 10.5a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5zM1 8h4.5M10.5 8H15",
    "cert": "M8 1.5l1.6 1.2 2-.1.6 1.9 1.6 1.2-.7 1.9.7 1.9-1.6 1.2-.6 1.9-2-.1L8 14.5l-1.6-1.2-2 .1-.6-1.9L2.2 10.3l.7-1.9-.7-1.9L3.8 5.3l.6-1.9 2 .1z",
    "clock": "M8 1.5a6.5 6.5 0 1 0 0 13 6.5 6.5 0 0 0 0-13zM8 4.5V8l2.5 1.5",
    "globe": "M8 1.5a6.5 6.5 0 1 0 0 13 6.5 6.5 0 0 0 0-13zM1.5 8h13M8 1.5c2 2 2 11 0 13M8 1.5c-2 2-2 11 0 13",
}


def icon(name, x, y, s=1.0, color=GREEN) -> str:
    return (f'<path transform="translate({x} {y}) scale({s})" d="{IC[name]}" fill="none" stroke="{color}" '
            f'stroke-width="{1.4/s:.2f}" stroke-linecap="round" stroke-linejoin="round"/>')


def title(x, y, ic, text) -> str:
    return f'{icon(ic, x, y - 13, 1.0)}<text x="{x + 24}" y="{y}" font-size="15" font-weight="600" fill="{TEXT}">{esc(text)}</text>'


# ---------------------------------------------------------------- foto
def avatar_data() -> str | None:
    if not CFG.get("mostrar_foto", True):
        return None
    for name in ("foto.jpg", "foto.jpeg", "foto.png"):
        p = ROOT / "assets" / name
        if p.exists():
            return f"data:image/{'png' if name.endswith('png') else 'jpeg'};base64,{base64.b64encode(p.read_bytes()).decode()}"
    login = os.environ.get("GH_LOGIN", "DaviMark")
    try:
        with urllib.request.urlopen(f"https://github.com/{login}.png?size=240", timeout=20) as r:
            return f"data:image/png;base64,{base64.b64encode(r.read()).decode()}"
    except Exception as e:  # sem internet: usa as iniciais
        print("foto indisponível:", e)
        return None


# ---------------------------------------------------------------- linha 1
def profile(photo: str | None) -> str:
    w, h = 620, 280
    cx, cy, r = 92, 104, 58
    initials = "".join(p[0] for p in CFG["nome"].split()[:2])
    face = (f'<clipPath id="av"><circle cx="{cx}" cy="{cy}" r="{r}"/></clipPath>'
            f'<image href="{photo}" x="{cx-r}" y="{cy-r}" width="{2*r}" height="{2*r}" clip-path="url(#av)" preserveAspectRatio="xMidYMid slice"/>'
            if photo else
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#122017"/><text x="{cx}" y="{cy+14}" text-anchor="middle" font-size="38" font-weight="700" fill="{GREEN}">{esc(initials)}</text>')
    bio = wrap(CFG["bio"], 380, 15, 2)
    L = CFG["links"]
    info = [("pin", CFG["local"]), ("link", CFG["site_rotulo"]), ("mail", CFG["email_rotulo"]), ("cal", CFG["status"])]
    ix, row = 34, []
    for ic, txt in info:
        tw = len(txt) * 6.3
        row.append(f'{icon(ic, ix, 186, .85, SUB)}<text x="{ix + 18}" y="{198}" font-size="12.5" fill="{SUB}" textLength="{tw:.0f}" lengthAdjust="spacingAndGlyphs">{esc(txt)}</text>')
        ix += 36 + tw
    chips, x = [], 34
    for c in CFG["chips"]:
        cw = 40 + len(c) * 7
        bg, fg, _ = TOOLS.get(c, (TER, TEXT, ""))
        uri = logo(c)
        mark = (f'<image href="{uri}" x="{x+9}" y="228" width="14" height="14"/>' if uri
                else f'<rect x="{x+10}" y="229" width="12" height="12" rx="3" fill="{bg}"/>')
        chips.append(f'<rect x="{x}" y="220" width="{cw:.0f}" height="30" rx="7" fill="{CHIP}" stroke="{EDGE}"/>' + mark +
                     f'<text x="{x+29}" y="240" font-size="12.5" fill="{TEXT}">{esc(c)}</text>')
        x += cw + 8
    nx = 176
    namew = len(CFG["nome"]) * 17
    body = f"""{card(w, h)}
<circle cx="{cx}" cy="{cy}" r="{r+5}" fill="none" stroke="{GREEN_D}" stroke-width="2.5"/>
{face}
<g class="in">
<text x="{nx}" y="88" font-size="28" font-weight="700" fill="{TEXT}">{esc(CFG['nome'])}</text>
<circle cx="{nx + namew + 16:.0f}" cy="78" r="10" fill="{GREEN_D}"/><path d="M{nx + namew + 11:.0f} 78 l3.5 3.5 6-6.5" fill="none" stroke="{BG}" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>
<text x="{nx}" y="116" font-size="16" font-weight="500" fill="{GREEN}">{esc(CFG['cargo'])}</text>
<text x="{nx}" y="146" font-size="15" fill="{SUB}">{tspans(bio, nx, 22)}</text>
</g>
<g class="in" style="animation-delay:.2s">{''.join(row)}</g>
<g class="in" style="animation-delay:.35s">{''.join(chips)}</g>
"""
    return svg(w, h, body)


def contributions(days) -> tuple[str, int]:
    w, h = 380, 280
    by = {d["date"]: d["count"] for d in days}
    end = dt.date.fromisoformat(max(by))
    total = sum(c for d, c in by.items() if dt.date.fromisoformat(d) > end - dt.timedelta(days=365))
    weeks = 24
    start = end - dt.timedelta(days=(end.weekday() + 1) % 7) - dt.timedelta(weeks=weeks - 1)
    span = [start + dt.timedelta(i) for i in range((end - start).days + 1)]
    nz = sorted(c for c in (by.get(d.isoformat(), 0) for d in span) if c)
    q = [nz[min(len(nz) - 1, int(p * len(nz)))] for p in (.25, .5, .75)] if nz else [1, 2, 3]
    lvl = lambda c: 0 if c <= 0 else 1 if c <= q[0] else 2 if c <= q[1] else 3 if c <= q[2] else 4
    x0, y0, step, cell = 32, 116, (w - 64) / weeks, 11
    cells, months, last = [], [], None
    for i, d in enumerate(span):
        col, row = divmod(i, 7)
        x, y = x0 + col * step, y0 + row * (cell + 4)
        c = by.get(d.isoformat(), 0)
        cells.append(f'<rect class="c" style="animation-delay:{col*.03:.2f}s" x="{x:.1f}" y="{y}" width="{cell}" height="{cell}" rx="2.5" fill="{LEVELS[lvl(c)]}"><title>{c} em {d:%d/%m/%Y}</title></rect>')
        if row == 0 and d.month != last and d.day <= 7:
            months.append(f'<text x="{x:.1f}" y="{y0-10}" font-size="11.5" fill="{SUB}">{MESES[d.month-1]}</text>')
            last = d.month
    body = f"""{card(w, h)}
<text x="32" y="50" font-size="16" font-weight="600" fill="{TEXT}">Contribuições</text>
<text x="32" y="74" font-size="13" fill="{SUB}">{num(total)} contribuições no último ano</text>
{''.join(months)}{''.join(cells)}"""
    css = ".c { opacity: 0; animation: f .4s ease-out forwards; } @keyframes f { to { opacity: 1; } }"
    return svg(w, h, body, css), total


# ---------------------------------------------------------------- coluna da esquerda
def thumb(x, y, w, h, kind) -> str:
    s = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="#101512" stroke="{EDGE}"/>',
         f'<rect x="{x+8}" y="{y+8}" width="{w*.35:.0f}" height="4" rx="2" fill="#2a332d"/>']
    for k in range(3):
        s.append(f'<rect x="{x+8+k*(w-16)/3:.1f}" y="{y+18}" width="{(w-16)/3-4:.1f}" height="14" rx="2" fill="#18201b"/>')
    top, bot = y + 40, y + h - 8
    if kind == 0:
        for i, v in enumerate([.4, .7, .5, .9, .6, 1, .75, .85]):
            bw = (w - 16) / 8
            bh = (bot - top) * v
            s.append(f'<rect x="{x+8+i*bw+1:.1f}" y="{bot-bh:.1f}" width="{bw-3:.1f}" height="{bh:.1f}" rx="1" fill="{GREEN_D if i == 5 else "#1d4d31"}"/>')
    elif kind == 1:
        pts = [(x + 8 + i * (w - 16) / 7, bot - (bot - top) * v) for i, v in enumerate([.3, .5, .4, .7, .55, .8, .7, .95])]
        s.append(f'<polyline points="{" ".join(f"{a:.1f},{b:.1f}" for a, b in pts)}" fill="none" stroke="{GREEN}" stroke-width="1.6"/>')
    else:
        for r in range(4):
            s.append(f'<rect x="{x+8}" y="{top + r*9:.1f}" width="{w-16}" height="5" rx="2" fill="{"#1d4d31" if r == 0 else "#18201b"}"/>')
    return "".join(s)


def project(p: dict, i: int, first: bool, h: float) -> str:
    w = 380
    top = 58 if first else 22
    head = title(30, 42, "star", "Projetos em destaque") if first else ""
    ty = top + 8
    desc = wrap(p["descricao"], 190, 12.5, 3)
    tags, tx = [], 168
    for t in p.get("tags", [])[:3]:
        tw = 16 + len(t) * 6.2
        if tx + tw > w - 20:
            break
        tags.append(f'<rect x="{tx}" y="{h-48}" width="{tw:.0f}" height="20" rx="5" fill="{CHIP}" stroke="{EDGE}"/>'
                    f'<text x="{tx+8}" y="{h-34}" font-size="11" fill="{SUB}">{esc(t)}</text>')
        tx += tw + 6
    body = f"""{card(w, h)}
{head}
<g class="in" style="animation-delay:{i*.12:.2f}s">
{thumb(30, ty, 120, h - ty - 22, i % 3)}
<text x="168" y="{ty + 14}" font-size="15.5" font-weight="600" fill="{TEXT}">{esc(p['titulo'])}</text>
<text x="168" y="{ty + 36}" font-size="12.5" fill="{SUB}">{tspans(desc, 168, 17)}</text>
{''.join(tags)}
</g>"""
    return svg(w, h, body)


# ---------------------------------------------------------------- coluna do meio
def about(h) -> str:
    w = 310
    items = "".join(f'<text x="34" y="{82 + i*30}" font-size="13" fill="{GREEN}">›</text>'
                    f'<text x="50" y="{82 + i*30}" font-size="13" fill="{SUB}">{esc(t)}</text>' for i, t in enumerate(CFG["sobre"]))
    return svg(w, h, f'{card(w, h)}{title(30, 42, "user", "Sobre mim")}<g class="in">{items}</g>')


def tech(h) -> str:
    w = 310
    items = CFG["tech"][:10]
    s, gap = 38, 14
    tiles = "".join(f'<g class="in" style="animation-delay:{i*.05:.2f}s">{tool_icon(30 + (i % 5)*(s+gap), 62 + (i // 5)*(s+gap), s, t)}<title>{esc(t)}</title></g>'
                    for i, t in enumerate(items))
    return svg(w, h, f'{card(w, h)}{title(30, 42, "code", "Ferramentas")}{tiles}')


# ---------------------------------------------------------------- coluna da direita
def stats(h, gh, total) -> str:
    w = 310
    rows = [("repo", "Repositórios", gh["repositorios"]), ("commit", "Contribuições no ano", num(total)),
            ("cert", "Certificações", CFG["certificacoes"]), ("clock", "Anos de experiência", f"{CFG['anos_experiencia']}+")]
    out = "".join(
        f'{icon(ic, 30, 66 + i*32, .9, SUB)}<text x="52" y="{78 + i*32}" font-size="13" fill="{SUB}">{esc(l)}</text>'
        f'<text x="{w-30}" y="{78 + i*32}" text-anchor="end" font-size="13" font-weight="600" fill="{GREEN}">{esc(v)}</text>'
        for i, (ic, l, v) in enumerate(rows)
    )
    return svg(w, h, f'{card(w, h)}{title(30, 42, "chart", "Estatísticas do GitHub")}<g class="in">{out}</g>')


def commits_chart(h, months, w=310) -> str:
    x0, x1, y0, y1 = 34, w - 30, 64, h - 44
    mx = max(c for _, c in months) or 1
    pts = [(x0 + i * (x1 - x0) / (len(months) - 1), y1 - (c / mx) * (y1 - y0)) for i, (_, c) in enumerate(months)]
    line = " ".join(f"{a:.1f},{b:.1f}" for a, b in pts)
    dots = "".join(f'<circle cx="{a:.1f}" cy="{b:.1f}" r="2.2" fill="{GREEN}"/>' for a, b in pts)
    labels = "".join(f'<text x="{a:.1f}" y="{h-22}" text-anchor="middle" font-size="10.5" fill="{TER}">{MESES[m.month-1][:3]}</text>'
                     for (a, _), (m, _) in zip(pts, months) if w > 400 or m.month % 2 == months[-1][0].month % 2)
    body = f"""{card(w, h)}
<text x="30" y="42" font-size="13.5" fill="{SUB}">Contribuições por mês</text>
<polyline points="{line}" pathLength="1" fill="none" stroke="{GREEN_D}" stroke-width="2" stroke-linejoin="round" class="draw"/>
<g class="dots">{dots}</g>{labels}"""
    css = (".draw { stroke-dasharray: 1; stroke-dashoffset: 1; animation: d 2s ease-out .3s forwards; } @keyframes d { to { stroke-dashoffset: 0; } } "
           ".dots { opacity: 0; animation: o .6s ease-out 2s forwards; } @keyframes o { to { opacity: 1; } }")
    return svg(w, h, body, css)


def connect(h) -> str:
    w = 310
    lines = wrap(CFG["conectar_texto"], 250, 12.5, 2)
    glyphs = [("in", None), (None, "globe"), (None, "mail"), ("GH", None)]
    btns = ""
    for i, (txt, ic) in enumerate(glyphs):
        bx = 30 + i * 46
        btns += f'<rect x="{bx}" y="{h-64}" width="36" height="36" rx="8" fill="{CHIP}" stroke="{EDGE}"/>'
        btns += (f'<text x="{bx+18}" y="{h-41}" text-anchor="middle" font-size="13" font-weight="700" fill="{TEXT}">{txt}</text>' if txt
                 else icon(ic, bx + 10, h - 54, 1.0, TEXT))
    body = f"""{card(w, h)}{title(30, 42, "link", "Vamos conversar")}
<text x="30" y="70" font-size="12.5" fill="{SUB}">{tspans(lines, 30, 17)}</text>{btns}"""
    return svg(w, h, body)


# ---------------------------------------------------------------- rodapé
def terminal() -> str:
    w, h = 1000, 110
    body = f"""{card(w, h)}
<g transform="translate(800 18)" fill="none" stroke="{GREEN_D}" stroke-width="1.2" opacity=".8">
<path d="M18 4 h120 l-12 56 h-120 z"/><path d="M-4 62 h136 l-8 10 h-136 z"/>
<path d="M30 22 l8 6 -9 6" /><path d="M44 36 h12"/></g>"""
    return svg(w, h, body)


# ---------------------------------------------------------------- README
def main() -> None:
    days = json.loads((ROOT / "data" / "contributions.json").read_text(encoding="utf-8"))["days"]
    gh = json.loads((ROOT / "data" / "github_stats.json").read_text(encoding="utf-8"))
    for f in CARDS.rglob("*.svg"):
        f.unlink()
    CARDS.mkdir(exist_ok=True)
    for d in ("claro", "escuro"):
        if (CARDS / d).exists():
            (CARDS / d).rmdir()

    by = {dt.date.fromisoformat(d["date"]): d["count"] for d in days}
    m = max(by).replace(day=1)
    months = []
    for _ in range(12):
        months.insert(0, (m, sum(c for d, c in by.items() if d.year == m.year and d.month == m.month)))
        m = (m - dt.timedelta(days=1)).replace(day=1)

    def put(name, content):
        (CARDS / name).write_text(content, encoding="utf-8")

    def img(name, width, alt, href=None):
        tag = f'<img src="./cards/{name}" width="{width}" alt="{esc(alt)}" />'
        return f'<a href="{esc(href)}">{tag}</a>' if href else tag

    L = CFG["links"]
    contrib, total = contributions(days)
    put("perfil.svg", profile(avatar_data()))
    put("contribuicoes.svg", contrib)

    H = [230, 190, 190]
    projs = CFG["projetos"][:3]
    for i, p in enumerate(projs):
        put(f"projeto-{i+1}.svg", project(p, i, i == 0, H[i]))
    put("sobre.svg", about(H[0]))
    put("ferramentas.svg", tech(H[2]))
    put("estatisticas.svg", stats(H[0], gh, total))
    put("grafico.svg", commits_chart(H[1], months, 620))
    put("conectar.svg", connect(H[2]))
    put("terminal.svg", terminal())

    rows = [
        img("projeto-1.svg", "38%", f"{projs[0]['titulo']}: {projs[0]['descricao']}", projs[0]["link"])
        + img("sobre.svg", "31%", "Sobre mim: " + "; ".join(CFG["sobre"]))
        + img("estatisticas.svg", "31%", "Estatísticas do GitHub"),
        img("projeto-2.svg", "38%", f"{projs[1]['titulo']}: {projs[1]['descricao']}", projs[1]["link"])
        + img("grafico.svg", "62%", "Contribuições por mês"),
        img("projeto-3.svg", "38%", f"{projs[2]['titulo']}: {projs[2]['descricao']}", projs[2]["link"])
        + img("ferramentas.svg", "31%", "Ferramentas: " + ", ".join(CFG["tech"]))
        + img("conectar.svg", "31%", "Vamos conversar", L.get("linkedin")),
    ]
    readme = f"""<!-- Gerado por scripts/build_profile.py. Para mudar textos, links e projetos,
edite config/perfil.json: o GitHub Action refaz tudo sozinho. Mantenha as imagens de cada linha coladas. -->
<div align="center">
{img("perfil.svg", "62%", f"{CFG['nome']}, {CFG['cargo']}. {CFG['bio']}", L.get("linkedin"))}{img("contribuicoes.svg", "38%", f"{num(total)} contribuições no último ano")}<br>
{'<br>'.join(rows)}<br>
{img("terminal.svg", "100%", "Notebook")}
</div>
"""
    (ROOT / "README.md").write_text(readme, encoding="utf-8")
    print("README.md e", len(list(CARDS.glob('*.svg'))), "cards gerados")


if __name__ == "__main__":
    main()
