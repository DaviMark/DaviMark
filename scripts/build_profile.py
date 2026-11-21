"""Gera todos os cards (cards/*.svg) e o README.md a partir de config/perfil.json.

Rode:  python scripts/build_profile.py
Dados: data/contributions.json e data/github_stats.json (vêm do fetch_contributions.py)
"""
from __future__ import annotations

import datetime as dt
import json
import math
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
CARDS = ROOT / "cards"
CFG = json.loads((ROOT / "config" / "perfil.json").read_text(encoding="utf-8"))

BG = "#0d1117"
CARD = "#0d1117"
TILE = "#161b22"
BORDER = "#30363d"
TEXT = "#e6edf3"
MUTED = "#8b949e"
ACCENT = "#3fb950"
ACCENT2 = "#7ee787"
LEVELS = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI','Noto Sans',Helvetica,Arial,sans-serif"
MESES = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
M = 6  # margem externa de cada card (vira o espaço entre eles no README)

# ícone (monograma) de cada ferramenta: cor de fundo, cor do texto, sigla
TOOLS = {
    "Power BI": ("#F2C811", "#1a1a1a", "BI"),
    "DAX": ("#00897B", "#ffffff", "DAX"),
    "Power Query": ("#D13348", "#ffffff", "PQ"),
    "SQL": ("#336791", "#ffffff", "SQL"),
    "Python": ("#3776AB", "#FFD43B", "Py"),
    "BigQuery": ("#4285F4", "#ffffff", "BQ"),
    "Databricks": ("#FF3621", "#ffffff", "DB"),
    "Spark": ("#E25A1C", "#ffffff", "Sp"),
    "Airflow": ("#017CEE", "#ffffff", "Af"),
    "Git": ("#F05032", "#ffffff", "Git"),
    "Actions": ("#2088FF", "#ffffff", "CI"),
    "SAP HANA": ("#0FAAFF", "#ffffff", "SAP"),
    "Excel": ("#217346", "#ffffff", "XL"),
    "Looker": ("#4285F4", "#ffffff", "LS"),
    "Web": ("#0e7490", "#ecfeff", "</>"),
}


def esc(s) -> str:
    return escape(str(s))


def tool(name: str):
    return TOOLS.get(name, ("#30363d", "#e6edf3", name[:2]))


def wrap(text: str, width_px: float, size: float, max_lines: int = 3) -> list[str]:
    per_line = max(8, int(width_px / (size * 0.54)))
    lines, cur = [], ""
    for word in text.split():
        if len(cur) + len(word) + (1 if cur else 0) > per_line:
            lines.append(cur)
            cur = word
        else:
            cur = f"{cur} {word}".strip()
    if cur:
        lines.append(cur)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1].rstrip(".,;") + "…"
    return lines


def svg(w: float, h: float, body: str, css: str = "") -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w:g}" height="{h:g}" viewBox="0 0 {w:g} {h:g}">
<style>
  text {{ font-family: {SANS}; }}
  @keyframes fadeUp {{ from {{ opacity: 0; transform: translateY(8px); }} to {{ opacity: 1; transform: none; }} }}
  @keyframes fadeIn {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
  .in {{ opacity: 0; animation: fadeUp .7s ease-out forwards; }}
  .fade {{ opacity: 0; animation: fadeIn .5s ease-out forwards; }}
  {css}
</style>
{body}
</svg>
"""


def panel(w: float, h: float, stroke: str = BORDER) -> str:
    return f'<rect x="{M}" y="{M}" width="{w - 2*M:g}" height="{h - 2*M:g}" rx="12" fill="{CARD}" stroke="{stroke}" stroke-width="1.2"/>'


def tool_icon(x, y, size, name) -> str:
    bg, fg, label = tool(name)
    fs = size * (0.42 if len(label) <= 2 else 0.32)
    return (f'<rect x="{x}" y="{y}" width="{size}" height="{size}" rx="{size*0.22:.1f}" fill="{bg}"/>'
            f'<text x="{x + size/2}" y="{y + size/2 + fs*0.36:.1f}" text-anchor="middle" font-size="{fs:.1f}" '
            f'font-weight="800" fill="{fg}">{esc(label)}</text>')


# ---------------------------------------------------------------- hero
def hero() -> str:
    W, H = 1000, 320
    x0 = 44
    chips, cx = [], x0
    for c in CFG["chips"]:
        bg, fg, label = tool(c)
        w = 34 + len(c) * 7.6
        chips.append(
            f'<g class="in" style="animation-delay:{.5 + len(chips)*.07:.2f}s">'
            f'<rect x="{cx}" y="236" width="{w:.0f}" height="30" rx="7" fill="{TILE}" stroke="{BORDER}"/>'
            f'<rect x="{cx+9}" y="245" width="12" height="12" rx="3" fill="{bg}"/>'
            f'<text x="{cx+28}" y="256" font-size="13" fill="{TEXT}">{esc(c)}</text></g>'
        )
        cx += w + 8
    desc = wrap(CFG["descricao"], 520, 15, 2)
    desc_svg = "".join(f'<tspan x="{x0}" dy="{0 if i == 0 else 22}">{esc(l)}</tspan>' for i, l in enumerate(desc))

    # ilustração: órbita, notebook com mini dashboard, estrelas
    ix, iy = 770, 160
    bars = "".join(
        f'<rect class="bar" x="{ix - 62 + i*16}" y="{iy + 10 - h}" width="10" height="{h}" rx="2" fill="{ACCENT if i % 3 else ACCENT2}" '
        f'style="animation-delay:{.6 + i*.08:.2f}s"/>'
        for i, h in enumerate([18, 30, 24, 40, 34, 48, 44, 58])
    )
    stars = "".join(
        f'<path d="M{x} {y-s} L{x+s*.28} {y-s*.28} L{x+s} {y} L{x+s*.28} {y+s*.28} L{x} {y+s} L{x-s*.28} {y+s*.28} L{x-s} {y} L{x-s*.28} {y-s*.28}Z" '
        f'fill="#c9d1ff" class="tw" style="animation-delay:{d}s"/>'
        for x, y, s, d in [(640, 70, 7, 0), (920, 60, 9, .8), (950, 230, 6, 1.6), (610, 250, 5, 2.2), (860, 280, 5, 1.1)]
    )
    illo = f"""
<defs>
  <radialGradient id="glow" cx="50%" cy="50%" r="50%">
    <stop offset="0" stop-color="#5865f2" stop-opacity=".45"/>
    <stop offset=".6" stop-color="#3b2f8f" stop-opacity=".15"/>
    <stop offset="1" stop-color="#0d1117" stop-opacity="0"/>
  </radialGradient>
  <linearGradient id="edge" x1="0" x2="1"><stop offset="0" stop-color="{BORDER}"/><stop offset=".6" stop-color="{BORDER}"/><stop offset="1" stop-color="#5865f2"/></linearGradient>
</defs>
<ellipse cx="{ix}" cy="{iy}" rx="190" ry="140" fill="url(#glow)"/>
<ellipse id="orb" cx="{ix}" cy="{iy}" rx="170" ry="62" fill="none" stroke="#6e7cff" stroke-opacity=".55" stroke-width="1.4" stroke-dasharray="4 6" transform="rotate(-14 {ix} {iy})"/>
<g transform="rotate(-14 {ix} {iy})">
  <circle r="5" fill="#a5b4ff"><animateMotion dur="9s" repeatCount="indefinite" path="M{ix-170},{iy} a170,62 0 1,0 340,0 a170,62 0 1,0 -340,0"/></circle>
  <circle r="3.5" fill="{ACCENT2}"><animateMotion dur="9s" begin="-4.5s" repeatCount="indefinite" path="M{ix-170},{iy} a170,62 0 1,0 340,0 a170,62 0 1,0 -340,0"/></circle>
</g>
{stars}
<g class="float">
  <rect x="{ix-86}" y="{iy-66}" width="172" height="104" rx="8" fill="#0b1020" stroke="#6e7cff" stroke-opacity=".8" stroke-width="1.5"/>
  <rect x="{ix-74}" y="{iy-56}" width="46" height="18" rx="3" fill="{TILE}"/>
  <rect x="{ix-22}" y="{iy-56}" width="46" height="18" rx="3" fill="{TILE}"/>
  <rect x="{ix+30}" y="{iy-56}" width="46" height="18" rx="3" fill="{TILE}"/>
  <rect x="{ix-70}" y="{iy-50}" width="20" height="5" rx="2" fill="{ACCENT}"/>
  <rect x="{ix-18}" y="{iy-50}" width="28" height="5" rx="2" fill="#a5b4ff"/>
  <rect x="{ix+34}" y="{iy-50}" width="16" height="5" rx="2" fill="#F2C811"/>
  {bars}
  <polyline points="{ix+70},{iy-26} {ix+56},{iy-10} {ix+44},{iy-16} {ix+30},{iy+4}" fill="none" stroke="#a5b4ff" stroke-width="2" class="fade" style="animation-delay:1.4s"/>
  <path d="M{ix-104} {iy+38} H{ix+104} L{ix+118} {iy+52} H{ix-118} Z" fill="#1c2230" stroke="#6e7cff" stroke-opacity=".6"/>
  <g transform="translate({ix+96} {iy-96})" class="fade" style="animation-delay:1s">
    <ellipse cx="0" cy="0" rx="18" ry="6" fill="#161b22" stroke="{ACCENT}"/>
    <path d="M-18 0 V20 A18 6 0 0 0 18 20 V0" fill="#161b22" stroke="{ACCENT}"/>
    <path d="M-18 10 A18 6 0 0 0 18 10" fill="none" stroke="{ACCENT}"/>
  </g>
</g>"""
    body = f"""
<rect x="{M}" y="{M}" width="{W-2*M}" height="{H-2*M}" rx="14" fill="{CARD}" stroke="url(#edge)" stroke-width="1.4"/>
{illo}
<g class="in" style="animation-delay:.05s"><rect x="{x0}" y="36" width="104" height="24" rx="6" fill="#0f2417" stroke="#1f6f3a"/>
<text x="{x0+12}" y="53" font-size="12.5" font-weight="600" fill="{ACCENT2}">▤ README.md</text></g>
<text class="in" style="animation-delay:.15s" x="{x0}" y="112" font-size="42" font-weight="800" fill="{TEXT}">Olá, eu sou o <tspan fill="{ACCENT}">{esc(CFG['nome'])}</tspan> 👋</text>
<text class="in" style="animation-delay:.25s" x="{x0}" y="148" font-size="18" font-weight="600" fill="{TEXT}">{esc(CFG['titulo'])} <tspan fill="{ACCENT}">{esc(CFG['destaque_titulo'])}</tspan></text>
<text class="in" style="animation-delay:.35s" x="{x0}" y="184" font-size="15" fill="{MUTED}">{desc_svg}</text>
{''.join(chips)}"""
    css = (".tw { animation: tw 2.6s ease-in-out infinite; transform-box: fill-box; transform-origin: center; } "
           "@keyframes tw { 0%,100% { opacity: .25; transform: scale(.7); } 50% { opacity: 1; transform: scale(1); } } "
           ".float { animation: fl 6s ease-in-out infinite; } @keyframes fl { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-6px); } } "
           ".bar { transform-box: fill-box; transform-origin: 50% 100%; transform: scaleY(0); animation: grow .8s cubic-bezier(.2,.8,.2,1) forwards; } "
           "@keyframes grow { to { transform: scaleY(1); } }")
    return svg(W, H, body, css)


# ---------------------------------------------------------------- stats
ICONS = {
    "repo": "M3 2.5A1.5 1.5 0 0 1 4.5 1h8A1.5 1.5 0 0 1 14 2.5v11a.5.5 0 0 1-.5.5h-9A1.5 1.5 0 0 1 3 12.5zM4.5 2a.5.5 0 0 0-.5.5v8.55A1.5 1.5 0 0 1 4.5 11H13V2zM4.5 12a.5.5 0 0 0 0 1H13v-1z",
    "pulse": "M1 8h3l2-5 4 10 2-5h3",
    "chart": "M2 14h12M4 12V8M7 12V4M10 12V6M13 12V9",
    "clock": "M8 1.5a6.5 6.5 0 1 0 0 13 6.5 6.5 0 0 0 0-13zM8 4v4.2l2.8 1.7",
}


def stat(icon: str, value, label: str, sub: str = "", delay: float = 0) -> str:
    W, H = 250, 104
    path = ICONS[icon]
    fill_mode = 'fill="none" stroke="#7ee787" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"' if icon != "repo" else 'fill="#7ee787"'
    body = f"""{panel(W, H)}
<g class="in" style="animation-delay:{delay}s">
<rect x="26" y="32" width="40" height="40" rx="10" fill="#0f2417" stroke="#1f6f3a"/>
<g transform="translate(34 40) scale(1.5)"><path d="{path}" {fill_mode}/></g>
<text x="82" y="56" font-size="28" font-weight="800" fill="{TEXT}">{esc(value)}</text>
<text x="82" y="76" font-size="13" fill="{MUTED}">{esc(label)}</text>
{f'<text x="82" y="91" font-size="11" fill="#6e7681">{esc(sub)}</text>' if sub else ''}
</g>"""
    return svg(W, H, body)


# ---------------------------------------------------------------- atividade
def activity(days: list[dict]) -> tuple[str, int]:
    by_date = {d["date"]: d["count"] for d in days}
    end = dt.date.fromisoformat(max(by_date))
    start = end - dt.timedelta(days=(end.weekday() + 1) % 7) - dt.timedelta(weeks=52)
    span = [start + dt.timedelta(i) for i in range((end - start).days + 1)]
    total = sum(by_date.get(d.isoformat(), 0) for d in span if d > end - dt.timedelta(days=365))
    nz = sorted(c for c in (by_date.get(d.isoformat(), 0) for d in span) if c)
    q = [nz[min(len(nz) - 1, int(p * len(nz)))] for p in (.25, .5, .75)] if nz else [1, 2, 3]
    lvl = lambda c: 0 if c <= 0 else 1 if c <= q[0] else 2 if c <= q[1] else 3 if c <= q[2] else 4

    W, H = 1000, 262
    cell, step, left, top = 13, 16.6, 78, 104
    cells, months, last = [], [], None
    for i, d in enumerate(span):
        col, row = divmod(i, 7)
        x, y = left + col * step, top + row * step
        c = by_date.get(d.isoformat(), 0)
        cells.append(f'<rect class="c" x="{x:.1f}" y="{y:.1f}" width="{cell}" height="{cell}" rx="3" fill="{LEVELS[lvl(c)]}" '
                     f'style="animation-delay:{col*.025 + row*.01:.3f}s"><title>{c} em {d:%d/%m/%Y}</title></rect>')
        if row == 0 and d.month != last and d.day <= 7 and col < 52:
            months.append(f'<text x="{x:.1f}" y="{top-10}" font-size="12" fill="{MUTED}">{MESES[d.month-1]}</text>')
            last = d.month
    wd = "".join(f'<text x="{left-10}" y="{top + r*step + 11:.1f}" text-anchor="end" font-size="11" fill="{MUTED}">{n}</text>'
                 for r, n in ((1, "Seg"), (3, "Qua"), (5, "Sex")))
    lx = left + 53 * step - 5 * 17 - 40
    ly = top + 7 * step + 14
    legend = "".join(f'<rect x="{lx + i*17}" y="{ly}" width="{cell}" height="{cell}" rx="3" fill="{c}"/>' for i, c in enumerate(LEVELS))
    tot = f"{total:,}".replace(",", ".")
    body = f"""{panel(W, H)}
<text x="34" y="46" font-size="18" font-weight="700" fill="{TEXT}">Atividade de contribuições</text>
<text x="34" y="72" font-size="14" fill="{MUTED}">🔥 <tspan fill="{TEXT}" font-weight="600">{tot}</tspan> contribuições no último ano</text>
{''.join(months)}{wd}{''.join(cells)}
<g class="fade" style="animation-delay:1.5s"><text x="{lx-8}" y="{ly+11}" text-anchor="end" font-size="11" fill="{MUTED}">Menos</text>{legend}
<text x="{lx + 5*17 + 4}" y="{ly+11}" font-size="11" fill="{MUTED}">Mais</text></g>"""
    css = ".c { opacity: 0; animation: fadeIn .35s ease-out forwards; }"
    return svg(W, H, body, css), total


# ---------------------------------------------------------------- seções e projetos
def section(title: str, show_all: bool) -> str:
    W, H = 1000, 58
    body = f"""<text x="20" y="38" font-size="20" font-weight="700" fill="{TEXT}">{esc(title)}</text>
{f'<text x="980" y="38" text-anchor="end" font-size="14" fill="{ACCENT}">Ver todos →</text>' if show_all else ''}"""
    return svg(W, H, body)


def project(p: dict, delay: float) -> str:
    W, H = 333.33, 176
    bg, fg, label = tool(p["ferramenta"])
    lines = wrap(p["descricao"], W - 2*M - 44, 13, 3)
    desc = "".join(f'<tspan x="26" dy="{0 if i == 0 else 18}">{esc(l)}</tspan>' for i, l in enumerate(lines))
    body = f"""{panel(W, H)}
<g class="in" style="animation-delay:{delay}s">
{tool_icon(26, 26, 36, p['ferramenta'])}
<text x="74" y="41" font-size="16" font-weight="700" fill="{ACCENT}">{esc(p['titulo'])}</text>
<text x="74" y="59" font-size="12" fill="{MUTED}">{esc(p['ferramenta'])}</text>
<text x="26" y="90" font-size="13" fill="#c9d1d9">{desc}</text>
<circle cx="31" cy="{H-30}" r="5" fill="{bg}"/>
<text x="42" y="{H-26}" font-size="12" fill="{MUTED}">{esc(p['ferramenta'])}</text>
<text x="{W-26:.0f}" y="{H-26}" text-anchor="end" font-size="12.5" font-weight="600" fill="{ACCENT}">Abrir ↗</text>
</g>"""
    return svg(W, H, body)


def tech() -> str:
    W, H = 1000, 150
    items = CFG["tech_stack"]
    slot = (W - 60) / max(len(items), 1)
    tiles = "".join(
        f'<g class="in" style="animation-delay:{i*.05:.2f}s">{tool_icon(30 + i*slot + slot/2 - 22, 62, 44, t)}'
        f'<text x="{30 + i*slot + slot/2:.1f}" y="126" text-anchor="middle" font-size="11.5" fill="{MUTED}">{esc(t)}</text></g>'
        for i, t in enumerate(items)
    )
    return svg(W, H, f'{panel(W, H)}<text x="34" y="44" font-size="18" font-weight="700" fill="{TEXT}">Tech Stack</text>{tiles}')


LINK_ICONS = {
    "portfolio": ("Portfólio", "M2 4h12v9H2zM6 4V2.5h4V4"),
    "linkedin": ("LinkedIn", "M3 6v7M3 3.2v.1M6.5 13V6M6.5 9a2.5 2.5 0 0 1 5 0v4"),
    "email": ("E-mail", "M2 4h12v8H2zM2 4l6 5 6-5"),
    "certificados": ("Certificados", "M8 1.8l1.8 3.7 4 .6-2.9 2.8.7 4L8 11l-3.6 1.9.7-4L2.2 6.1l4-.6z"),
}


def link_pill(key: str) -> str:
    W, H = 250, 70
    label, path = LINK_ICONS[key]
    body = f"""{panel(W, H)}
<g transform="translate(28 25) scale(1.25)"><path d="{path}" fill="none" stroke="{ACCENT2}" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></g>
<text x="60" y="41" font-size="15" font-weight="600" fill="{TEXT}">{esc(label)}</text>
<text x="222" y="41" text-anchor="end" font-size="15" fill="{ACCENT}">↗</text>"""
    return svg(W, H, body)


def quote() -> str:
    W, H = 1000, 76
    body = f"""{panel(W, H)}
<text x="500" y="44" text-anchor="middle" font-size="15" font-style="italic" fill="{MUTED}"><tspan fill="{ACCENT}" font-weight="800">“</tspan> {esc(CFG['frase'])} <tspan fill="{ACCENT}" font-weight="800">”</tspan></text>"""
    return svg(W, H, body)


# ---------------------------------------------------------------- README
def main() -> None:
    CARDS.mkdir(exist_ok=True)
    for old in CARDS.glob("*.svg"):
        old.unlink()
    days = json.loads((ROOT / "data" / "contributions.json").read_text(encoding="utf-8"))["days"]
    gh = json.loads((ROOT / "data" / "github_stats.json").read_text(encoding="utf-8"))

    write = lambda name, content: (CARDS / name).write_text(content, encoding="utf-8")
    write("hero.svg", hero())
    act, total = activity(days)
    write("atividade.svg", act)
    n_rel = len(CFG["relatorios"]) + len(CFG["projetos"])
    write("stat-repos.svg", stat("repo", gh["repositorios"], "Repositórios", "públicos", .1))
    write("stat-contrib.svg", stat("pulse", f"{total:,}".replace(",", "."), "Contribuições", "último ano", .2))
    write("stat-relatorios.svg", stat("chart", n_rel, "Relatórios e projetos", "no portfólio", .3))
    write("stat-exp.svg", stat("clock", f"{CFG['anos_experiencia']}+", "Anos de experiência", "dados e BI", .4))
    for k in LINK_ICONS:
        write(f"link-{k}.svg", link_pill(k))
    write("secao-relatorios.svg", section(CFG["relatorios_titulo"], CFG.get("relatorios_ver_todos", "#") != "#"))
    write("secao-projetos.svg", section(CFG["projetos_titulo"], CFG.get("projetos_ver_todos", "#") != "#"))
    write("tech.svg", tech())
    write("frase.svg", quote())

    L = CFG["links"]
    lk = lambda href, src, w, alt: f'<a href="{esc(href)}"><img src="./cards/{src}" width="{w}" alt="{esc(alt)}" /></a>'
    im = lambda src, w, alt: f'<img src="./cards/{src}" width="{w}" alt="{esc(alt)}" />'

    def grid(items, prefix):
        out, row = [], []
        for i, p in enumerate(items):
            name = f"{prefix}-{i+1}.svg"
            write(name, project(p, (i % 3) * .1))
            row.append(lk(p["link"], name, "33.333%", f"{p['titulo']}: {p['descricao']}"))
            if len(row) == 3:
                out.append("".join(row) + "<br>")
                row = []
        if row:
            out.append("".join(row) + "<br>")
        return "\n".join(out)

    readme = f"""<!-- Este README é gerado por scripts/build_profile.py.
Para mudar textos, links, relatórios e projetos, edite config/perfil.json:
o GitHub Action refaz tudo sozinho. Mantenha as imagens de cada linha coladas, sem espaços. -->
<div align="center">
{lk(L['portfolio'], 'hero.svg', '100%', f"Olá, eu sou o {CFG['nome_completo']}. {CFG['titulo']} {CFG['destaque_titulo']}.")}<br>
{im('stat-repos.svg', '25%', 'Repositórios públicos')}{im('stat-contrib.svg', '25%', 'Contribuições no último ano')}{im('stat-relatorios.svg', '25%', 'Relatórios e projetos')}{im('stat-exp.svg', '25%', 'Anos de experiência')}<br>
{im('atividade.svg', '100%', 'Gráfico de contribuições do último ano')}<br>
{lk(CFG.get('relatorios_ver_todos', '#'), 'secao-relatorios.svg', '100%', CFG['relatorios_titulo'])}<br>
{grid(CFG['relatorios'], 'relatorio')}
{lk(CFG.get('projetos_ver_todos', '#'), 'secao-projetos.svg', '100%', CFG['projetos_titulo'])}<br>
{grid(CFG['projetos'], 'projeto')}
{im('tech.svg', '100%', 'Tech stack: ' + ', '.join(CFG['tech_stack']))}<br>
{''.join(lk(L[k], f'link-{k}.svg', '25%', LINK_ICONS[k][0]) for k in LINK_ICONS)}<br>
{im('frase.svg', '100%', CFG['frase'])}
</div>
"""
    (ROOT / "README.md").write_text(readme, encoding="utf-8")
    print("README.md e", len(list(CARDS.glob('*.svg'))), "cards gerados")


if __name__ == "__main__":
    main()
