"""Gera os cards (cards/claro e cards/escuro) e o README.md a partir de config/perfil.json.

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
    "claro": dict(text="#1d1d1f", sub="#6e6e73", ter="#86868b", line="#d2d2d7", accent="#0066cc",
                  levels=["#ebebef", "#c9dbf2", "#8fb6e8", "#4a8edb", "#0066cc"]),
    "escuro": dict(text="#f5f5f7", sub="#a1a1a6", ter="#86868b", line="#3a3a3c", accent="#2997ff",
                   levels=["#1c1c1e", "#0d355f", "#15599f", "#1f7ae0", "#2997ff"]),
}
MESES = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]


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


def svg(h: float, body: str, css: str = "") -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h:g}" viewBox="0 0 {W} {h:g}">
<style>
  text {{ font-family: {FONT}; }}
  .in {{ opacity: 0; animation: in .9s cubic-bezier(.2,.7,.2,1) forwards; }}
  @keyframes in {{ from {{ opacity: 0; transform: translateY(10px); }} to {{ opacity: 1; transform: none; }} }}
  {css}
</style>
{body}
</svg>
"""


# ---------------------------------------------------------------- blocos
def hero(t) -> str:
    desc = wrap(CFG["descricao"], 780, 19, 2)
    d = "".join(f'<tspan x="0" dy="{0 if i == 0 else 29}">{esc(l)}</tspan>' for i, l in enumerate(desc))
    meta = f"{CFG['local']}  ·  {CFG['anos_experiencia']} anos em dados e BI"
    return svg(270, f"""
<text class="in" x="0" y="74" font-size="56" font-weight="700" letter-spacing="-1.4" fill="{t['text']}">{esc(CFG['nome'])}</text>
<text class="in" style="animation-delay:.12s" x="0" y="124" font-size="32" font-weight="600" letter-spacing="-.6" fill="{t['sub']}">{esc(CFG['cargo'])}</text>
<text class="in" style="animation-delay:.24s" x="0" y="184" font-size="19" fill="{t['sub']}">{d}</text>
<text class="in" style="animation-delay:.36s" x="0" y="{184 + 29*len(desc) + 22}" font-size="15" fill="{t['ter']}">{esc(meta)}</text>""")


def numbers(t, values: list[tuple[str, str]]) -> str:
    col = W / len(values)
    items = "".join(
        f'<g class="in" style="animation-delay:{.1 + i*.08:.2f}s">'
        f'<text x="{i*col}" y="74" font-size="44" font-weight="600" letter-spacing="-1" fill="{t["text"]}">{esc(v)}</text>'
        f'<text x="{i*col}" y="104" font-size="15" fill="{t["sub"]}">{esc(l)}</text></g>'
        for i, (v, l) in enumerate(values)
    )
    return svg(140, f'<line x1="0" y1="20.5" x2="{W}" y2="20.5" stroke="{t["line"]}"/>{items}'
                    f'<line x1="0" y1="139.5" x2="{W}" y2="139.5" stroke="{t["line"]}"/>')


def header(t, title: str, link: bool) -> str:
    right = f'<text x="{W}" y="62" text-anchor="end" font-size="17" fill="{t["accent"]}">Ver todos ›</text>' if link else ""
    return svg(86, f'<text x="0" y="62" font-size="30" font-weight="700" letter-spacing="-.6" fill="{t["text"]}">{esc(title)}</text>{right}')


def activity(t, days: list[dict]) -> tuple[str, int]:
    by = {d["date"]: d["count"] for d in days}
    end = dt.date.fromisoformat(max(by))
    start = end - dt.timedelta(days=(end.weekday() + 1) % 7) - dt.timedelta(weeks=52)
    span = [start + dt.timedelta(i) for i in range((end - start).days + 1)]
    total = sum(by.get(d.isoformat(), 0) for d in span if d > end - dt.timedelta(days=365))
    nz = sorted(c for c in (by.get(d.isoformat(), 0) for d in span) if c)
    q = [nz[min(len(nz) - 1, int(p * len(nz)))] for p in (.25, .5, .75)] if nz else [1, 2, 3]
    lvl = lambda c: 0 if c <= 0 else 1 if c <= q[0] else 2 if c <= q[1] else 3 if c <= q[2] else 4

    left, top, cell = 34, 96, 13.5
    step = (W - left) / 53
    cells, months, last = [], [], None
    for i, d in enumerate(span):
        col, row = divmod(i, 7)
        x, y = left + col * step, top + row * step
        c = by.get(d.isoformat(), 0)
        cells.append(f'<rect class="c" x="{x:.1f}" y="{y:.1f}" width="{cell}" height="{cell}" rx="3.5" fill="{t["levels"][lvl(c)]}" '
                     f'style="animation-delay:{col*.018:.3f}s"><title>{c} em {d:%d/%m/%Y}</title></rect>')
        if row == 0 and d.month != last and d.day <= 7 and col < 52:
            months.append(f'<text x="{x:.1f}" y="{top-12}" font-size="12" fill="{t["ter"]}">{MESES[d.month-1]}</text>')
            last = d.month
    wd = "".join(f'<text x="0" y="{top + r*step + 11:.1f}" font-size="11" fill="{t["ter"]}">{n}</text>'
                 for r, n in ((1, "Seg"), (3, "Qua"), (5, "Sex")))
    body = f"""<text x="0" y="40" font-size="30" font-weight="700" letter-spacing="-.6" fill="{t['text']}">Atividade</text>
<text x="{W}" y="40" text-anchor="end" font-size="17" fill="{t['sub']}">{num(total)} contribuições no último ano</text>
{''.join(months)}{wd}{''.join(cells)}"""
    css = ".c { opacity: 0; animation: f .5s ease-out forwards; } @keyframes f { to { opacity: 1; } }"
    return svg(top + 7 * step + 8, body, css), total


def row(t, p: dict, last: bool) -> str:
    h = 104
    desc = wrap(p["descricao"], 700, 16, 1)[0]
    bottom = f'<line x1="0" y1="{h-.5}" x2="{W}" y2="{h-.5}" stroke="{t["line"]}"/>' if last else ""
    return svg(h, f"""<line x1="0" y1=".5" x2="{W}" y2=".5" stroke="{t['line']}"/>
<text x="0" y="44" font-size="20" font-weight="600" letter-spacing="-.3" fill="{t['text']}">{esc(p['titulo'])}</text>
<text x="0" y="74" font-size="16" fill="{t['sub']}">{esc(desc)}</text>
<text x="{W-90}" y="58" text-anchor="end" font-size="15" fill="{t['ter']}">{esc(p['ferramenta'])}</text>
<text x="{W}" y="58" text-anchor="end" font-size="17" fill="{t['accent']}">Abrir ›</text>
{bottom}""")


def tools(t) -> str:
    per, lines, cur = int(W / (19 * 0.52)), [], ""
    for item in CFG["tech_stack"]:  # quebra entre ferramentas, nunca no meio de uma
        nxt = f"{cur}  ·  {item}" if cur else item
        if len(nxt) > per and cur:
            lines.append(cur)
            nxt = item
        cur = nxt
    lines.append(cur)
    body = "".join(f'<text x="0" y="{30 + i*32}" font-size="19" fill="{t["sub"]}" xml:space="preserve">{esc(l)}</text>'
                   for i, l in enumerate(lines))
    return svg(30 + 32 * (len(lines) - 1) + 14, body)


LINKS = [("linkedin", "LinkedIn"), ("email", "E-mail"), ("portfolio", "Portfólio"), ("certificados", "Certificados")]


def link(t, label: str) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="250" height="60" viewBox="0 0 250 60">'
            f'<text x="0" y="38" font-family="{FONT}" font-size="19" fill="{t["accent"]}">{esc(label)} ›</text></svg>\n')


# ---------------------------------------------------------------- README
def main() -> None:
    days = json.loads((ROOT / "data" / "contributions.json").read_text(encoding="utf-8"))["days"]
    gh = json.loads((ROOT / "data" / "github_stats.json").read_text(encoding="utf-8"))
    for f in CARDS.rglob("*.svg"):
        f.unlink()

    def emit(name: str, fn, *args):
        for theme, t in THEMES.items():
            out = CARDS / theme / name
            out.parent.mkdir(parents=True, exist_ok=True)
            res = fn(t, *args)
            out.write_text(res[0] if isinstance(res, tuple) else res, encoding="utf-8")
        return res

    _, total = emit("atividade.svg", activity, days)
    emit("hero.svg", hero)
    n_port = len(CFG["relatorios"]) + len(CFG["projetos"])
    emit("numeros.svg", numbers, [
        (f"{CFG['anos_experiencia']} anos", "de experiência"),
        (num(total), "contribuições no ano"),
        (str(n_port), "relatórios e projetos"),
        (str(gh["repositorios"]), "repositórios públicos"),
    ])
    emit("ferramentas.svg", tools)

    def pic(name: str, alt: str, href: str | None = None, width: str = "100%") -> str:
        tag = (f'<picture><source media="(prefers-color-scheme: dark)" srcset="./cards/escuro/{name}" />'
               f'<img src="./cards/claro/{name}" width="{width}" alt="{esc(alt)}" /></picture>')
        return f'<a href="{esc(href)}">{tag}</a>' if href else tag

    def section(key: str) -> str:
        title, ver, items = CFG[f"{key}_titulo"], CFG.get(f"{key}_ver_todos", "#"), CFG[key]
        emit(f"{key}.svg", header, title, ver != "#")
        out = [pic(f"{key}.svg", title, ver if ver != "#" else None)]
        for i, p in enumerate(items):
            name = f"{key}-{i+1}.svg"
            emit(name, row, p, i == len(items) - 1)
            out.append(pic(name, f"{p['titulo']}: {p['descricao']}", p["link"]))
        return "<br>\n".join(out)

    emit("ferramentas-titulo.svg", header, "Ferramentas", False)
    emit("contato.svg", header, "Contato", False)
    L = CFG["links"]
    contatos = []
    for key, label in LINKS:
        if L.get(key) and L[key] != "#":
            emit(f"link-{key}.svg", link, label)
            contatos.append(pic(f"link-{key}.svg", label, L[key], "25%"))

    readme = f"""<!-- Gerado por scripts/build_profile.py. Para mudar textos, links, relatórios
e projetos, edite config/perfil.json: o GitHub Action refaz tudo sozinho. -->

{pic('hero.svg', f"{CFG['nome']}. {CFG['cargo']} {CFG['descricao']}")}
{pic('numeros.svg', 'Números')}
<br><br>

{section('relatorios')}
<br><br>

{section('projetos')}
<br><br>

{pic('atividade.svg', f'{num(total)} contribuições no último ano')}
<br><br>

{pic('ferramentas-titulo.svg', 'Ferramentas')}<br>
{pic('ferramentas.svg', ', '.join(CFG['tech_stack']))}
<br><br>

{pic('contato.svg', 'Contato')}<br>
{''.join(contatos)}
"""
    (ROOT / "README.md").write_text(readme, encoding="utf-8")
    print("README.md e", len(list(CARDS.rglob('*.svg'))), "cards gerados")


if __name__ == "__main__":
    main()
