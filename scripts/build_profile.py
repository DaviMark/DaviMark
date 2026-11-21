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
    H = 300
    resumo = "   ·   ".join(CFG["resumo"])
    body = f"""
<defs><clipPath id="wipe"><rect class="wipe" x="0" y="40" width="{W}" height="110"/></clipPath></defs>
<g clip-path="url(#wipe)"><text x="0" y="130" font-size="88" font-weight="700" letter-spacing="-3.4" fill="{t['text']}">{esc(CFG['nome'])}</text></g>
<line class="rule" x1="2" y1="170" x2="82" y2="170" stroke="{t['accent']}" stroke-width="4" stroke-linecap="round"/>
<text class="in" style="animation-delay:.5s" x="0" y="226" font-size="30" font-weight="600" letter-spacing="-.6" fill="{t['sub']}">{esc(CFG['cargo'])}</text>
<text class="in" style="animation-delay:.7s" x="0" y="272" font-size="18" fill="{t['ter']}" xml:space="preserve">{esc(resumo)}</text>"""
    css = (".wipe { transform: translateX(-100%); animation: wipe 1.1s cubic-bezier(.7,0,.2,1) .1s forwards; } "
           "@keyframes wipe { to { transform: none; } } " + RULE_CSS.replace("48", "80").replace(".4s", ".9s"))
    return svg(H, body, css)


RULE_CSS = (".rule { stroke-dasharray: 48; stroke-dashoffset: 48; animation: rule 1s cubic-bezier(.4,0,.2,1) .4s forwards; } "
            "@keyframes rule { to { stroke-dashoffset: 0; } }")


def header(t, title: str) -> str:
    return svg(96, f'<text class="in" x="0" y="70" font-size="44" font-weight="700" letter-spacing="-1.4" fill="{t["text"]}">{esc(title)}</text>')


# ---------------------------------------------------------------- o que eu faço
def pillar(t, p: dict, i: int) -> str:
    w, H = 333.33, 240
    x0 = 8 if i % 3 else 0
    tx = x0 + 32
    per, lines, cur = int((w - 96) / (16 * 0.47)), [], ""
    for item in p["ferramentas"].split(" · "):  # quebra entre ferramentas, nunca no meio
        nxt = f"{cur} · {item}" if cur else item
        if len(nxt) > per and cur:
            lines.append(cur)
            nxt = item
        cur = nxt
    lines.append(cur)
    d = (i % 3) * .15
    body = f"""<g class="in" style="animation-delay:{d:.2f}s">
<rect x="{x0}" y="10" width="{w - 8:.1f}" height="{H-20}" rx="28" fill="{t['tile']}"/>
<text x="{tx}" y="70" font-size="15" font-weight="600" letter-spacing="1.5" fill="{t['accent']}">0{i+1}</text>
<line class="rule" style="animation-delay:{d + .4:.2f}s" x1="{tx}" y1="90" x2="{tx + 48}" y2="90" stroke="{t['accent']}" stroke-width="3" stroke-linecap="round"/>
<text x="{tx}" y="142" font-size="26" font-weight="700" letter-spacing="-.7" fill="{t['text']}">{esc(p['titulo'])}</text>
<text x="{tx}" y="178" font-size="16" fill="{t['ter']}">{tspans(lines, tx, 24)}</text></g>"""
    return svg(H, body, RULE_CSS, w=w)


# ---------------------------------------------------------------- trabalhos
def work(t, p: dict, i: int, kind: str, last: bool) -> str:
    H, cy = 112, 56
    bottom = f'<line x1="0" y1="{H-.5}" x2="{W}" y2="{H-.5}" stroke="{t["line"]}"/>' if last else ""
    body = f"""<line x1="0" y1=".5" x2="{W}" y2=".5" stroke="{t['line']}"/>
<g class="in" style="animation-delay:{i*.08:.2f}s">
<text x="0" y="50" font-size="16" font-weight="600" fill="{t['ter']}">{i+1:02d}</text>
<text x="64" y="46" font-size="13" font-weight="600" letter-spacing="1.5" fill="{t['accent']}">{esc(kind.upper())}  ·  {esc(p['ferramenta'].upper())}</text>
<text x="64" y="80" font-size="26" font-weight="700" letter-spacing="-.7" fill="{t['text']}">{esc(p['titulo'])}</text>
<g class="go" style="animation-delay:{1 + i*.3:.1f}s">
<circle cx="{W-32}" cy="{cy}" r="24" fill="none" stroke="{t['accent']}" stroke-width="1.8"/>
<path d="M{W-41} {cy} H{W-23} M{W-31} {cy-8} L{W-23} {cy} L{W-31} {cy+8}" fill="none" stroke="{t['accent']}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></g>
</g>{bottom}"""
    css = (".go { animation: go 3.2s cubic-bezier(.4,0,.2,1) infinite; } "
           "@keyframes go { 0%,70%,100% { transform: translateX(0); } 80% { transform: translateX(6px); } 90% { transform: translateX(0); } }")
    return svg(H, body, css)


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
    emit("titulo-trabalhos.svg", header, CFG["trabalhos_titulo"])
    emit("titulo-contato.svg", header, CFG["contato_titulo"])

    pillars = []
    for i, p in enumerate(CFG["pilares"]):
        emit(f"pilar-{i+1}.svg", pillar, p, i)
        pillars.append(pic(f"pilar-{i+1}.svg", f"{p['titulo']}: {p['ferramentas']}", width="33.333%"))

    items = [("Relatório", p) for p in CFG["relatorios"]] + [("Projeto", p) for p in CFG["projetos"]]
    works = []
    for i, (kind, p) in enumerate(items):
        emit(f"trabalho-{i+1}.svg", work, p, i, kind, i == len(items) - 1)
        works.append(pic(f"trabalho-{i+1}.svg", f"{kind}: {p['titulo']} ({p['ferramenta']})", p["link"]))

    L = CFG["links"]
    buttons = []
    for key, label in LINKS:
        if L.get(key) and L[key] != "#":
            emit(f"botao-{key}.svg", button, label, not buttons)
            buttons.append(pic(f"botao-{key}.svg", label, L[key], "25%"))

    readme = f"""<!-- Gerado por scripts/build_profile.py. Para mudar textos, links, relatórios
e projetos, edite config/perfil.json: o GitHub Action refaz tudo sozinho. -->

{pic('abertura.svg', f"{CFG['nome']}. {CFG['cargo']}. " + ". ".join(CFG['resumo']))}
<br><br>

{pic('titulo-o-que-eu-faco.svg', CFG['pilares_titulo'])}<br>
{''.join(pillars)}
<br><br>

{pic('titulo-trabalhos.svg', CFG['trabalhos_titulo'])}<br>
{'<br>'.join(works)}
<br><br>

{pic('titulo-contato.svg', CFG['contato_titulo'])}<br>
{''.join(buttons)}
"""
    (ROOT / "README.md").write_text(readme, encoding="utf-8")
    print("README.md e", len(list(CARDS.rglob('*.svg'))), "cards gerados")


if __name__ == "__main__":
    main()
