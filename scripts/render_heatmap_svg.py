"""Gera contrib-heatmap.svg: gráfico de contribuições do último ano, animado célula a célula."""
from __future__ import annotations

import datetime as dt

from theme import BG, LEVELS, MESES_CAP, MONO, MUTED, ROOT, SANS, TEXT, esc, load_days

W = 860
CELL, GAP = 12, 3
STEP = CELL + GAP
LEFT, TOP = 52, 44


def thresholds(counts: list[int]) -> list[int]:
    nz = sorted(c for c in counts if c > 0)
    if not nz:
        return [1, 2, 3]
    q = lambda p: nz[min(len(nz) - 1, int(p * len(nz)))]
    return [q(0.25), q(0.5), q(0.75)]


def level(c: int, t: list[int]) -> int:
    if c <= 0:
        return 0
    if c <= t[0]:
        return 1
    if c <= t[1]:
        return 2
    if c <= t[2]:
        return 3
    return 4


def main() -> None:
    by_date = {d["date"]: d["count"] for d in load_days()}
    end = dt.date.fromisoformat(max(by_date))
    # 53 colunas, semana começando no domingo (igual ao GitHub)
    start = end - dt.timedelta(days=(end.weekday() + 1) % 7) - dt.timedelta(weeks=52)
    span = [start + dt.timedelta(i) for i in range((end - start).days + 1)]
    year = [d for d in span if d > end - dt.timedelta(days=365)]
    total = sum(by_date.get(d.isoformat(), 0) for d in year)
    t = thresholds([by_date.get(d.isoformat(), 0) for d in span])

    cells, months = [], []
    last_month = None
    for i, d in enumerate(span):
        col, row = divmod(i, 7)
        x, y = LEFT + col * STEP, TOP + row * STEP
        c = by_date.get(d.isoformat(), 0)
        delay = col * 0.028 + row * 0.012
        tip = f"{c} contribuições em {d.day:02d}/{d.month:02d}/{d.year}"
        cells.append(
            f'<rect class="c" x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2.5" '
            f'fill="{LEVELS[level(c, t)]}" style="animation-delay:{delay:.3f}s"><title>{tip}</title></rect>'
        )
        if row == 0 and d.month != last_month and d.day <= 7 and col < 52:
            months.append(f'<text x="{x}" y="{TOP - 12}" class="sans" font-size="13" fill="{MUTED}">{MESES_CAP[d.month - 1]}</text>')
            last_month = d.month

    weekdays = "".join(
        f'<text x="{LEFT - 10}" y="{TOP + r * STEP + 10}" text-anchor="end" class="sans" font-size="12" fill="{MUTED}">{n}</text>'
        for r, n in ((1, "Seg"), (3, "Qua"), (5, "Sex"))
    )

    grid_bottom = TOP + 7 * STEP
    H = grid_bottom + 46
    legend_x = LEFT + 53 * STEP - 5 * STEP - 44
    legend = "".join(
        f'<rect x="{legend_x + i * STEP}" y="{grid_bottom + 16}" width="{CELL}" height="{CELL}" rx="2.5" fill="{col}"/>'
        for i, col in enumerate(LEVELS)
    )

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<style>
  .sans {{ font-family: {SANS}; }}
  .mono {{ font-family: {MONO}; }}
  .c {{ opacity: 0; animation: pop .35s ease-out forwards; }}
  @keyframes pop {{ 0% {{ opacity: 0; }} 60% {{ opacity: 1; }} 100% {{ opacity: 1; }} }}
  .t {{ opacity: 0; animation: pop .6s ease-out 1.6s forwards; }}
</style>
<rect width="{W}" height="{H}" rx="10" fill="{BG}"/>
{''.join(months)}
{weekdays}
{''.join(cells)}
<text class="sans t" x="{LEFT}" y="{grid_bottom + 27}" font-size="14" font-weight="600" fill="{TEXT}">{total:,} contribuições no último ano</text>
<g class="t">
<text class="sans" x="{legend_x - 8}" y="{grid_bottom + 26}" text-anchor="end" font-size="12" fill="{MUTED}">Menos</text>
{legend}
<text class="sans" x="{legend_x + 5 * STEP + 4}" y="{grid_bottom + 26}" font-size="12" fill="{MUTED}">Mais</text>
</g>
</svg>
""".replace(f"{total:,}", f"{total:,}".replace(",", "."))
    (ROOT / "contrib-heatmap.svg").write_text(svg, encoding="utf-8")
    print("contrib-heatmap.svg ok", total)


if __name__ == "__main__":
    main()
