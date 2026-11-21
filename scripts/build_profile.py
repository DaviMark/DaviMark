"""Gera os cards (cards/claro e cards/escuro) e o README.md a partir de config/perfil.json.

Rode:  python scripts/build_profile.py
"""
from __future__ import annotations

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
                  tile="#f5f5f7", btn_text="#ffffff"),
    "escuro": dict(text="#f5f5f7", sub="#a1a1a6", ter="#86868b", line="#3a3a3c", accent="#2997ff",
                   tile="#161617", btn_text="#ffffff"),
}

BASE_CSS = """
  text { font-family: %s; }
  .in { opacity: 0; animation: in 1.1s cubic-bezier(.2,.7,.2,1) forwards; }
  @keyframes in { from { opacity: 0; transform: translateY(16px); } to { opacity: 1; transform: none; } }
  @media (prefers-reduced-motion: reduce) { * { animation: none !important; opacity: 1 !important; transform: none !important; } }
""" % FONT


def esc(s) -> str:
    return escape(str(s))


def wrap(text: str, width: float, size: float, max_lines: int = 99) -> list[str]:
    per = max(8, int(width / (size * 0.47)))
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


# ---------------------------------------------------------------- abertura
def hero(t) -> str:
    words = CFG["palavras"] + [CFG["palavras"][0]]
    n, step = len(CFG["palavras"]), 84
    kf = []
    for i in range(n):  # cada palavra fica parada ~80% do seu trecho e depois sobe
        a, b = i / n * 100, (i + 1) / n * 100
        kf.append(f"{a:.2f}% {{ transform: translateY(-{i*step}px); }} {a + (b-a)*0.8:.2f}% {{ transform: translateY(-{i*step}px); }}")
    kf.append(f"100% {{ transform: translateY(-{n*step}px); }}")
    slot = "".join(f'<text x="0" y="{304 + i*step}" font-size="72" font-weight="700" letter-spacing="-2.6" fill="{t["accent"]}">{esc(w)}</text>'
                   for i, w in enumerate(words))

    y = 400
    paras = []
    for k, p in enumerate(CFG["apresentacao"]):
        lines = wrap(p, 900, 21)
        paras.append(f'<text class="in" style="animation-delay:{.5 + k*.15:.2f}s" x="0" y="{y}" font-size="21" fill="{t["sub"]}">{tspans(lines, 0, 33)}</text>')
        y += 33 * len(lines) + 26
    H = y + 40
    body = f"""
<defs><clipPath id="slot"><rect x="0" y="232" width="{W}" height="{step}"/></clipPath></defs>
<text class="in" x="0" y="58" font-size="15" font-weight="600" letter-spacing="2.4" fill="{t['accent']}">{esc(CFG['eyebrow'].upper())}</text>
<text class="in" style="animation-delay:.1s" x="0" y="144" font-size="72" font-weight="700" letter-spacing="-2.6" fill="{t['text']}">{esc(CFG['saudacao'])}</text>
<text class="in" style="animation-delay:.22s" x="0" y="224" font-size="72" font-weight="700" letter-spacing="-2.6" fill="{t['ter']}">{esc(CFG['manchete'])}</text>
<g class="in" style="animation-delay:.34s"><g clip-path="url(#slot)"><g class="words">{slot}</g></g></g>
{''.join(paras)}
<g class="in" style="animation-delay:.8s">
<circle cx="6" cy="{y - 6}" r="5" fill="none" stroke="{t['ter']}" stroke-width="1.6"/>
<text x="20" y="{y}" font-size="16" fill="{t['ter']}">{esc(CFG['local'])}</text></g>"""
    css = f".words {{ animation: words {n*2.8:.1f}s cubic-bezier(.7,0,.3,1) 1.2s infinite; }} @keyframes words {{ {' '.join(kf)} }}"
    return svg(H, body, css)


def header(t, title: str, subtitle: str = "") -> str:
    sub = f'<text class="in" style="animation-delay:.12s" x="0" y="118" font-size="21" fill="{t["sub"]}">{esc(subtitle)}</text>' if subtitle else ""
    return svg(140 if subtitle else 100,
               f'<text class="in" x="0" y="74" font-size="52" font-weight="700" letter-spacing="-1.8" fill="{t["text"]}">{esc(title)}</text>{sub}')


# ---------------------------------------------------------------- o que eu faço
def pillar(t, p: dict, i: int) -> str:
    w, H = 333.33, 380
    x0 = 8 if i % 3 else 0
    tx = x0 + 32
    lines = wrap(p["texto"], w - 96, 16.5, 8)
    d = (i % 3) * .15
    body = f"""<g class="in" style="animation-delay:{d:.2f}s">
<rect x="{x0}" y="10" width="{w - 8:.1f}" height="{H-20}" rx="28" fill="{t['tile']}"/>
<text x="{tx}" y="72" font-size="15" font-weight="600" letter-spacing="1.5" fill="{t['accent']}">0{i+1}</text>
<line class="rule" style="animation-delay:{d + .4:.2f}s" x1="{tx}" y1="92" x2="{tx + 48}" y2="92" stroke="{t['accent']}" stroke-width="3" stroke-linecap="round"/>
<text x="{tx}" y="146" font-size="27" font-weight="700" letter-spacing="-.7" fill="{t['text']}">{esc(p['titulo'])}</text>
<text x="{tx}" y="186" font-size="16.5" fill="{t['sub']}">{tspans(lines, tx, 26)}</text></g>"""
    css = (".rule { stroke-dasharray: 48; stroke-dashoffset: 48; animation: rule 1s cubic-bezier(.4,0,.2,1) forwards; } "
           "@keyframes rule { to { stroke-dashoffset: 0; } }")
    return svg(H, body, css, w=w)


def tools(t) -> str:
    H = 120
    items = CFG["tech_stack"]
    seq = "     ·     ".join(items) + "     ·     "
    size = 34
    L = sum(len(s) for s in items) * size * 0.56 + len(items) * size * 2.2  # largura forçada com textLength
    copies = "".join(
        f'<text x="{k*L:.1f}" y="78" font-size="{size}" font-weight="600" letter-spacing="-.8" fill="{t["ter"]}" '
        f'textLength="{L:.1f}" lengthAdjust="spacing" xml:space="preserve">{esc(seq)}</text>'
        for k in range(3)
    )
    body = f"""<defs><linearGradient id="fd" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".1" stop-color="#fff"/>
<stop offset=".9" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
<mask id="mk"><rect x="0" y="0" width="{W}" height="{H}" fill="url(#fd)"/></mask></defs>
<g mask="url(#mk)"><g class="mq">{copies}</g></g>"""
    css = f".mq {{ animation: mq {L/40:.1f}s linear infinite; }} @keyframes mq {{ to {{ transform: translateX(-{L:.1f}px); }} }}"
    return svg(H, body, css)


# ---------------------------------------------------------------- trabalhos
def work(t, p: dict, i: int, kind: str, last: bool) -> str:
    desc = wrap(p["descricao"], 700, 17, 2)
    H = 136 + 25 * len(desc)
    cy = H / 2
    bottom = f'<line x1="0" y1="{H-.5}" x2="{W}" y2="{H-.5}" stroke="{t["line"]}"/>' if last else ""
    body = f"""<line x1="0" y1=".5" x2="{W}" y2=".5" stroke="{t['line']}"/>
<g class="in" style="animation-delay:{i*.08:.2f}s">
<text x="0" y="58" font-size="16" font-weight="600" fill="{t['ter']}">{i+1:02d}</text>
<text x="64" y="58" font-size="13" font-weight="600" letter-spacing="1.5" fill="{t['accent']}">{esc(kind.upper())}  ·  {esc(p['ferramenta'].upper())}</text>
<text x="64" y="94" font-size="27" font-weight="700" letter-spacing="-.7" fill="{t['text']}">{esc(p['titulo'])}</text>
<text x="64" y="124" font-size="17" fill="{t['sub']}">{tspans(desc, 64, 25)}</text>
<g class="go" style="animation-delay:{1 + i*.3:.1f}s">
<circle cx="{W-32}" cy="{cy:.0f}" r="26" fill="none" stroke="{t['accent']}" stroke-width="1.8"/>
<path d="M{W-41} {cy:.0f} H{W-22} M{W-30} {cy-9:.0f} L{W-21} {cy:.0f} L{W-30} {cy+9:.0f}" fill="none" stroke="{t['accent']}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></g>
</g>{bottom}"""
    css = (".go { animation: go 3.2s cubic-bezier(.4,0,.2,1) infinite; } "
           "@keyframes go { 0%,70%,100% { transform: translateX(0); } 80% { transform: translateX(6px); } 90% { transform: translateX(0); } }")
    return svg(H, body, css)


# ---------------------------------------------------------------- contato
def contact(t) -> str:
    lines = wrap(CFG["contato_texto"], 900, 21)
    return svg(110 + 32 * len(lines), f"""
<text class="in" x="0" y="74" font-size="52" font-weight="700" letter-spacing="-1.8" fill="{t['text']}">{esc(CFG['contato_titulo'])}</text>
<text class="in" style="animation-delay:.12s" x="0" y="124" font-size="21" fill="{t['sub']}">{tspans(lines, 0, 32)}</text>""")


LINKS = [("linkedin", "LinkedIn"), ("email", "E-mail"), ("portfolio", "Portfólio"), ("certificados", "Certificados")]


def button(t, label: str, primary: bool) -> str:
    w, h = 250, 84
    if primary:
        shape = f'<rect x="0" y="14" width="{w-20}" height="56" rx="28" fill="{t["accent"]}"/>'
        color = t["btn_text"]
    else:
        shape = f'<rect x="1" y="15" width="{w-22}" height="54" rx="27" fill="none" stroke="{t["accent"]}" stroke-width="2"/>'
        color = t["accent"]
    return svg(h, f'{shape}<text x="{(w-20)/2}" y="49" text-anchor="middle" font-size="19" font-weight="600" fill="{color}">{esc(label)}</text>', w=w)


# ---------------------------------------------------------------- README
def main() -> None:
    for f in CARDS.rglob("*.svg"):
        f.unlink()

    def emit(name: str, fn, *args):
        for theme, t in THEMES.items():
            out = CARDS / theme / name
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(fn(t, *args), encoding="utf-8")

    def pic(name: str, alt: str, href: str | None = None, width: str = "100%") -> str:
        tag = (f'<picture><source media="(prefers-color-scheme: dark)" srcset="./cards/escuro/{name}" />'
               f'<img src="./cards/claro/{name}" width="{width}" alt="{esc(alt)}" /></picture>')
        return f'<a href="{esc(href)}">{tag}</a>' if href else tag

    emit("abertura.svg", hero)
    emit("titulo-o-que-eu-faco.svg", header, CFG["pilares_titulo"])
    emit("titulo-trabalhos.svg", header, CFG["trabalhos_titulo"], CFG["trabalhos_subtitulo"])
    emit("ferramentas.svg", tools)
    emit("contato.svg", contact)

    pillars = []
    for i, p in enumerate(CFG["pilares"]):
        emit(f"pilar-{i+1}.svg", pillar, p, i)
        pillars.append(pic(f"pilar-{i+1}.svg", f"{p['titulo']}: {p['texto']}", width="33.333%"))

    items = [("Relatório", p) for p in CFG["relatorios"]] + [("Projeto", p) for p in CFG["projetos"]]
    works = []
    for i, (kind, p) in enumerate(items):
        emit(f"trabalho-{i+1}.svg", work, p, i, kind, i == len(items) - 1)
        works.append(pic(f"trabalho-{i+1}.svg", f"{p['titulo']}: {p['descricao']}", p["link"]))

    L = CFG["links"]
    buttons = []
    for key, label in LINKS:
        if L.get(key) and L[key] != "#":
            emit(f"botao-{key}.svg", button, label, not buttons)
            buttons.append(pic(f"botao-{key}.svg", label, L[key], "25%"))

    intro = " ".join(CFG["apresentacao"])
    readme = f"""<!-- Gerado por scripts/build_profile.py. Para mudar textos, links, relatórios
e projetos, edite config/perfil.json: o GitHub Action refaz tudo sozinho. -->

{pic('abertura.svg', f"{CFG['saudacao']} {CFG['eyebrow']}. {intro}")}
<br><br>

{pic('titulo-o-que-eu-faco.svg', CFG['pilares_titulo'])}<br>
{''.join(pillars)}<br>
{pic('ferramentas.svg', 'Ferramentas: ' + ', '.join(CFG['tech_stack']))}
<br><br>

{pic('titulo-trabalhos.svg', CFG['trabalhos_titulo'])}<br>
{'<br>'.join(works)}
<br><br>

{pic('contato.svg', CFG['contato_titulo'] + ' ' + CFG['contato_texto'])}<br>
{''.join(buttons)}
"""
    (ROOT / "README.md").write_text(readme, encoding="utf-8")
    print("README.md e", len(list(CARDS.rglob('*.svg'))), "cards gerados")


if __name__ == "__main__":
    main()
