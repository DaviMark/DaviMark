"""Gera stats.svg: sequências, totais e barras por mês, num painel de terminal 840x880."""
from __future__ import annotations

import datetime as dt

from theme import BORDER, GREEN, MESES, MUTED, ROOT, TEXT, TILE, USER, esc, load_days, window

W, H = 840, 880
PAD, GAP = 28, 20


def fmt(d: dt.date) -> str:
    return f"{d.day:02d} {MESES[d.month - 1]}"


def streaks(days: list[tuple[dt.date, int]]):
    """Retorna (atual, início, fim) e (maior, início, fim)."""
    best = (0, None, None)
    run, run_start = 0, None
    for d, c in days:
        if c > 0:
            run_start = d if run == 0 else run_start
            run += 1
            if run > best[0]:
                best = (run, run_start, d)
        else:
            run = 0
    # sequência atual: conta para trás a partir de hoje (ou ontem, se hoje ainda está zerado)
    i = len(days) - 1
    if i >= 0 and days[i][1] == 0:
        i -= 1
    cur_end = days[i][0] if i >= 0 else None
    cur = 0
    while i >= 0 and days[i][1] > 0:
        cur += 1
        i -= 1
    cur_start = days[i + 1][0] if cur else None
    return (cur, cur_start, cur_end if cur else None), best


def tile(x, y, w, h, label, value, unit, sub, color, delay) -> str:
    return f"""<g class="rise" style="animation-delay:{delay}s">
<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{TILE}" stroke="{BORDER}"/>
<text x="{x+20}" y="{y+32}" class="mono" font-size="17" fill="{MUTED}">$ {esc(label)}</text>
<text x="{x+20}" y="{y+82}" class="mono" font-size="46" font-weight="700" fill="{color}">{esc(value)}<tspan font-size="18" font-weight="400" fill="{MUTED}" dx="10">{esc(unit)}</tspan></text>
<text x="{x+20}" y="{y+108}" class="mono" font-size="14" fill="{MUTED}">{esc(sub)}</text>
</g>"""


def main() -> None:
    raw = load_days()
    days = [(dt.date.fromisoformat(d["date"]), d["count"]) for d in raw]
    today = days[-1][0]
    year = [(d, c) for d, c in days if d > today - dt.timedelta(days=365)]

    (cur, cs, ce), (best, bs, be) = streaks(days)
    total = sum(c for _, c in year)
    active = sum(1 for _, c in year if c > 0)
    best_day, best_count = max(year, key=lambda x: x[1])
    avg = total / active if active else 0
    n = len(year)

    num = lambda v: f"{v:,}".replace(",", ".")
    tw = (W - 2 * PAD - GAP) // 2
    th = 120
    x1, x2 = PAD, PAD + tw + GAP
    ys = [70, 70 + th + 18, 70 + 2 * (th + 18)]
    tiles = [
        tile(x1, ys[0], tw, th, "sequência atual", cur, "dias", f"{fmt(cs)} – {fmt(ce)}" if cur else "bora começar hoje", GREEN, 0.1),
        tile(x2, ys[0], tw, th, "maior sequência", best, "dias", f"{fmt(bs)} – {fmt(be)}" if best else "-", TEXT, 0.2),
        tile(x1, ys[1], tw, th, "contribuições", num(total), "", "no último ano", TEXT, 0.3),
        tile(x2, ys[1], tw, th, "dias ativos", active, f"/ {n}", f"{round(100 * active / n)}% do ano", TEXT, 0.4),
        tile(x1, ys[2], tw, th, "melhor dia", best_count, "", fmt(best_day), TEXT, 0.5),
        tile(x2, ys[2], tw, th, "média / dia ativo", f"{avg:.1f}".replace(".", ","), "", "contribuições", TEXT, 0.6),
    ]

    # barras por mês (13 meses, do mês de início da janela até o atual)
    first = year[0][0].replace(day=1)
    months = []
    m = first
    while m <= today:
        months.append(m)
        m = (m.replace(day=28) + dt.timedelta(days=4)).replace(day=1)
    sums = [sum(c for d, c in year if d.year == mm.year and d.month == mm.month) for mm in months]

    cy = ys[2] + th + 20
    ch = H - cy - PAD
    cw = W - 2 * PAD
    chart = [f'<g class="rise" style="animation-delay:.7s"><rect x="{PAD}" y="{cy}" width="{cw}" height="{ch}" rx="8" fill="{TILE}" stroke="{BORDER}"/>',
             f'<text x="{PAD+20}" y="{cy+32}" class="mono" font-size="17" fill="{MUTED}">$ contribuições / mês</text></g>']
    base = cy + ch - 44
    top = cy + 80
    mx = max(sums) or 1
    slot = (cw - 40) / len(months)
    bw = slot * 0.62
    imax = sums.index(max(sums))
    for i, (mm, s) in enumerate(zip(months, sums)):
        bx = PAD + 20 + i * slot + (slot - bw) / 2
        bh = max(3, (base - top) * s / mx) if s else 3
        color = GREEN if i == imax else "#26a641"
        op = "1" if s else "0.35"
        chart.append(
            f'<rect class="bar" x="{bx:.1f}" y="{base-bh:.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="3" fill="{color}" '
            f'opacity="{op}" style="animation-delay:{0.9 + i * 0.06:.2f}s"><title>{MESES[mm.month-1]}/{mm.year}: {s}</title></rect>'
        )
        chart.append(f'<text x="{bx + bw/2:.1f}" y="{base + 26}" text-anchor="middle" class="mono" font-size="14" fill="{MUTED}">{MESES[mm.month-1][0].upper()}</text>')
        if i == imax and s:
            chart.append(f'<text class="fade mono" style="animation-delay:1.8s" x="{bx + bw/2:.1f}" y="{base-bh-10:.1f}" text-anchor="middle" font-size="15" font-weight="700" fill="{TEXT}">{num(s)}</text>')

    css = ".bar { transform-box: fill-box; transform-origin: 50% 100%; transform: scaleY(0); animation: grow .7s cubic-bezier(.2,.8,.2,1) forwards; } @keyframes grow { to { transform: scaleY(1); } }"
    svg = window(W, H, f"{USER}@github: ~/stats.sh", "\n".join(tiles + chart), css)
    (ROOT / "stats.svg").write_text(svg, encoding="utf-8")
    print("stats.svg ok", cur, best, total, active)


if __name__ == "__main__":
    main()
