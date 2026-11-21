"""Gera avatar-ascii.svg: retrato em ASCII dentro de uma janela de terminal 840x880.

Foto usada (nesta ordem):
  1. assets/foto.png ou assets/foto.jpg  (recomendado: rosto + ombros, de frente, boa luz)
  2. sua foto de perfil do GitHub (https://github.com/<GH_LOGIN>.png)

Se o pacote `rembg` estiver instalado, o fundo é removido automaticamente
(é o que deixa o retrato limpo, igual ao do vídeo).
"""
from __future__ import annotations

import io
import os

from PIL import Image, ImageEnhance, ImageFilter, ImageOps

from theme import DISPLAY_NAME, MONO, MUTED, ROOT, USER, esc, window

W, H = 840, 880
COLS = 100
X0, Y0 = 30, 66
AREA_W, AREA_H = W - 2 * X0, 760
FONT = AREA_W / (COLS * 0.6)
LINE = FONT * 1.08
ROWS = int(AREA_H // LINE)
RAMP = " .'`^\",:;Il!i><~+_-?][}{1)(|/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"
INK = "#d0d7de"


def load_photo() -> Image.Image:
    for name in ("foto.png", "foto.jpg", "foto.jpeg"):
        p = ROOT / "assets" / name
        if p.exists():
            print("usando", p)
            return Image.open(p)
    import requests
    login = os.environ.get("GH_LOGIN", "DaviMark")
    print("usando avatar do GitHub de", login)
    r = requests.get(f"https://github.com/{login}.png?size=460", timeout=30)
    r.raise_for_status()
    return Image.open(io.BytesIO(r.content))


def cut_background(img: Image.Image) -> Image.Image:
    try:
        from rembg import remove
    except ImportError:
        print("rembg não instalado: mantendo o fundo")
        return img.convert("RGBA")
    return remove(img.convert("RGB"))


def frame_subject(img: Image.Image) -> Image.Image:
    """Recorta no sujeito; se for corpo inteiro, fica só com cabeça e ombros."""
    alpha = img.getchannel("A")
    box = alpha.point(lambda a: 255 if a > 128 else 0).getbbox() or (0, 0, *img.size)
    l, t, r, b = box
    w, h = r - l, b - t
    if h > 1.25 * w:  # foto de corpo inteiro / meio corpo
        h = int(w * 1.15)
    img = img.crop((l, t, l + w, t + h))
    # encaixa na proporção da área de texto, com uma margem
    target = (COLS * FONT * 0.6) / (ROWS * LINE)
    w, h = img.size
    cw, ch = (int(h * target), h) if w / h < target else (w, int(w / target))
    cw, ch = int(cw * 1.06), int(ch * 1.06)
    canvas = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    canvas.paste(img, ((cw - w) // 2, ch - h), img)
    return canvas


def to_ascii(img: Image.Image) -> list[str]:
    img = img.resize((COLS, ROWS), Image.LANCZOS)
    alpha = img.getchannel("A")
    gray = ImageOps.autocontrast(img.convert("L"), cutoff=2)
    gray = ImageEnhance.Contrast(gray).enhance(1.25).filter(ImageFilter.SHARPEN)
    rows = []
    for y in range(ROWS):
        line = []
        for x in range(COLS):
            if alpha.getpixel((x, y)) < 110:
                line.append(" ")
                continue
            v = 1 - gray.getpixel((x, y)) / 255  # escuro = denso, como no vídeo
            line.append(RAMP[min(len(RAMP) - 1, int(v * (len(RAMP) - 1)))])
        rows.append("".join(line))
    return rows


def main() -> None:
    img = ImageOps.exif_transpose(load_photo())
    img = frame_subject(cut_background(img))
    rows = to_ascii(img)

    lines = []
    for i, row in enumerate(rows):
        if not row.strip():
            continue
        y = Y0 + (i + 1) * LINE
        lines.append(
            f'<text class="mono ln" x="{X0}" y="{y:.1f}" font-size="{FONT:.2f}" fill="{INK}" xml:space="preserve" '
            f'textLength="{AREA_W}" lengthAdjust="spacingAndGlyphs" style="animation-delay:{i * 0.022:.3f}s">{esc(row)}</text>'
        )
    footer = (
        f'<text class="mono fade" style="animation-delay:{len(rows) * 0.022 + .2:.2f}s" x="{X0}" y="{H - 22}" font-size="15" fill="{MUTED}">'
        f'{USER}@github:~$ whoami <tspan fill="#e6edf3" font-weight="700">{esc(DISPLAY_NAME)}</tspan></text>'
    )
    css = ".ln { opacity: 0; animation: fadeIn .35s ease-out forwards; }"
    svg = window(W, H, f"{USER}@github: ~/portrait.sh", "\n".join(lines) + "\n" + footer, css)
    (ROOT / "avatar-ascii.svg").write_text(svg, encoding="utf-8")
    print("avatar-ascii.svg ok", COLS, "x", ROWS)


if __name__ == "__main__":
    main()
