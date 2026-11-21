"""Paleta, fontes e moldura de "janela de terminal" usadas por todos os SVGs."""
from __future__ import annotations

import json
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "contributions.json"

# ---- personalize aqui -------------------------------------------------------
USER = "davi"                      # aparece em "davi@github"
DISPLAY_NAME = "Davi Marques"      # aparece no rodapé do retrato
# -----------------------------------------------------------------------------

BG = "#0d1117"
PANEL = "#0d1117"
TILE = "#161b22"
BORDER = "#30363d"
TEXT = "#e6edf3"
MUTED = "#7d8590"
GREEN = "#39d353"
LEVELS = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]

MONO = "ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,'Liberation Mono',monospace"
SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"

MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
MESES_CAP = [m.capitalize() for m in MESES]


def esc(s: str) -> str:
    return escape(str(s))


def load_days() -> list[dict]:
    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    return sorted(data["days"], key=lambda d: d["date"])


def window(width: int, height: int, title: str, body: str, extra_css: str = "") -> str:
    """Moldura de terminal: fundo escuro, borda, 3 bolinhas e título."""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<style>
  .mono {{ font-family: {MONO}; }}
  .sans {{ font-family: {SANS}; }}
  @keyframes fadeUp {{ from {{ opacity: 0; transform: translateY(6px); }} to {{ opacity: 1; transform: none; }} }}
  @keyframes fadeIn {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
  .fade {{ opacity: 0; animation: fadeIn .5s ease-out forwards; }}
  .rise {{ opacity: 0; animation: fadeUp .6s ease-out forwards; }}
  {extra_css}
</style>
<rect x="1" y="1" width="{width-2}" height="{height-2}" rx="12" fill="{PANEL}" stroke="{BORDER}" stroke-width="2"/>
<circle cx="26" cy="24" r="6" fill="#ff5f57"/>
<circle cx="46" cy="24" r="6" fill="#febc2e"/>
<circle cx="66" cy="24" r="6" fill="#28c840"/>
<text x="{width/2}" y="29" text-anchor="middle" class="mono" font-size="14" fill="{MUTED}">{esc(title)}</text>
<line x1="1" y1="46" x2="{width-1}" y2="46" stroke="{BORDER}" stroke-width="1"/>
{body}
</svg>
"""
