#!/usr/bin/env python3
"""Generate a Bauhaus-style Pi poster as SVG and PNG.

Primary renderer: pycairo
Fallback renderer: matplotlib
"""

from __future__ import annotations

import math
import shutil
from dataclasses import dataclass

import mpmath as mp

try:
    import cairo  # type: ignore
except Exception:  # pragma: no cover
    cairo = None


MM_PER_INCH = 25.4
DPI = 300
WIDTH_MM = 329
HEIGHT_MM = 483
WIDTH_PX = round(WIDTH_MM / MM_PER_INCH * DPI)
HEIGHT_PX = round(HEIGHT_MM / MM_PER_INCH * DPI)
BOTTOM_FADE_CM = 2.0

GRID_COLS = 30
GRID_ROWS = 50
PERSPECTIVE_ROWS = 8
# Start perspective this many rows earlier than the last PERSPECTIVE_ROWS band.
PERSPECTIVE_START_OFFSET = 2
# Perspective row scaling for the infinite effect zone (bottom).
# 0.90 means each row is 10% smaller than the previous one.
# (half the previous speed of convergence).
PERSPECTIVE_SCALE = 0.90
MARGIN_RATIO = 0.0

PALETTE = {
    "red": (0xD0 / 255.0, 0x20 / 255.0, 0x20 / 255.0),
    "blue": (0x1D / 255.0, 0x5B / 255.0, 0xB6 / 255.0),
    "yellow": (0xF1 / 255.0, 0xB7 / 255.0, 0x20 / 255.0),
    "black": (0x11 / 255.0, 0x11 / 255.0, 0x11 / 255.0),
    "cream": (0xF0 / 255.0, 0xF0 / 255.0, 0xE0 / 255.0),
    "gold": (0xD4 / 255.0, 0xAF / 255.0, 0x37 / 255.0),
    "white": (1.0, 1.0, 1.0),
}

# Feynman point starts at decimal position 762 (1-based), so zero-based index is 761.
FEYNMAN_START = 761
FEYNMAN_LEN = 6

FONT_PRESETS = {
    "inter": {
        "cairo": "Inter",
        "mpl": ["Inter", "Arial", "DejaVu Sans"],
    },
    "jetbrains-mono": {
        "cairo": "JetBrains Mono",
        "mpl": ["JetBrains Mono", "Fira Code", "DejaVu Sans Mono", "monospace"],
    },
    "sans": {
        "cairo": "Sans",
        "mpl": ["DejaVu Sans", "Arial", "sans-serif"],
    },
}


def is_feynman_index(index: int) -> bool:
    return FEYNMAN_START <= index < FEYNMAN_START + FEYNMAN_LEN


@dataclass(frozen=True)
class Cell:
    row: int
    col: int
    cols_in_row: int
    cx: float
    cy: float
    base: float
    digit: int
    index: int


def get_pi_digits(n_decimal_digits: int) -> str:
    mp.mp.dps = n_decimal_digits + 20
    pi_text = str(mp.pi)
    _, decimals = pi_text.split(".", 1)
    if len(decimals) < n_decimal_digits:
        raise ValueError("Not enough computed digits of Pi.")
    return decimals[:n_decimal_digits]


def digit_color(digit: int, index: int) -> tuple[float, float, float]:
    if is_feynman_index(index):
        return PALETTE["gold"]
    if digit % 2 == 0:
        return PALETTE["red"] if digit % 4 == 0 else PALETTE["blue"]
    return PALETTE["yellow"] if digit % 4 == 1 else PALETTE["black"]


def digit_scale(digit: int) -> float:
    return 0.22 + (digit / 9.0) * 0.76


def build_cells(margin_x: float, margin_y: float, inner_w: float, inner_h: float) -> list[Cell]:
    cells: list[Cell] = []
    row_h = inner_h / GRID_ROWS
    normal_rows = GRID_ROWS - PERSPECTIVE_ROWS - PERSPECTIVE_START_OFFSET
    next_index = 0

    # Regular grid area.
    for row in range(normal_rows):
        cols_in_row = GRID_COLS
        cell_w = inner_w / cols_in_row
        cy = margin_y + (row + 0.5) * row_h
        for col in range(cols_in_row):
            cx = margin_x + (col + 0.5) * cell_w
            base = min(cell_w, row_h)
            cells.append(
                Cell(
                    row=row,
                    col=col,
                    cols_in_row=cols_in_row,
                    cx=cx,
                    cy=cy,
                    base=base,
                    digit=0,
                    index=next_index,
                )
            )
            next_index += 1

    # Perspective zone: variable row heights/spacing packed into the last 8-row band.
    perspective_top = margin_y + normal_rows * row_h
    perspective_bottom = margin_y + inner_h
    y_cursor = perspective_top
    perspective_k = 0
    row_id = normal_rows
    min_row_h = 0.8

    while y_cursor < perspective_bottom:
        row_h_k = row_h * (PERSPECTIVE_SCALE**perspective_k)
        if row_h_k < min_row_h:
            break
        if y_cursor + row_h_k > perspective_bottom:
            row_h_k = perspective_bottom - y_cursor
            if row_h_k <= 0:
                break

        cols_in_row = max(GRID_COLS, int(round(GRID_COLS * ((1.0 / PERSPECTIVE_SCALE) ** perspective_k))))
        cell_w = inner_w / cols_in_row
        cy = y_cursor + row_h_k / 2.0

        for col in range(cols_in_row):
            cx = margin_x + (col + 0.5) * cell_w
            base = min(cell_w, row_h_k)
            cells.append(
                Cell(
                    row=row_id,
                    col=col,
                    cols_in_row=cols_in_row,
                    cx=cx,
                    cy=cy,
                    base=base,
                    digit=0,
                    index=next_index,
                )
            )
            next_index += 1

        y_cursor += row_h_k
        perspective_k += 1
        row_id += 1

    digits = get_pi_digits(len(cells))
    return [Cell(**{**c.__dict__, "digit": int(digits[c.index])}) for c in cells]


def draw_pi_organic_overlay_cairo(ctx: "cairo.Context", digit_font: str) -> None:
    pi_size = min(WIDTH_PX, HEIGHT_PX) * 0.76
    ctx.select_font_face(FONT_PRESETS[digit_font]["cairo"], cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(pi_size)
    ext = ctx.text_extents("π")
    x = (WIDTH_PX - ext.width) / 2 - ext.x_bearing
    y = (HEIGHT_PX + ext.height) / 2 - ext.y_bearing
    # Raise the pi by ~3.5 grid rows so the top bar sits closer to a row midline.
    row_h = HEIGHT_PX / GRID_ROWS
    y -= row_h * 3.5

    # Fill semi-transparent pi so the grid stays visible underneath.
    ctx.save()
    if hasattr(cairo, "OPERATOR_MULTIPLY"):
        ctx.set_operator(cairo.OPERATOR_MULTIPLY)
    ctx.set_source_rgba(PALETTE["black"][0], PALETTE["black"][1], PALETTE["black"][2], 0.08)
    ctx.move_to(x, y)
    ctx.text_path("π")
    ctx.fill_preserve()

    # Clipped two-tone Bauhaus tiling: quarter-circles and triangles.
    ctx.clip()
    ctx.new_path()
    tile = max(30.0, min(WIDTH_PX, HEIGHT_PX) * 0.020)
    tone_a = (0.07, 0.07, 0.07, 0.14)
    tone_b = (0.12, 0.34, 0.17, 0.11)
    cols = int(math.ceil(WIDTH_PX / tile)) + 1
    rows = int(math.ceil(HEIGHT_PX / tile)) + 1

    for r in range(rows):
        for c in range(cols):
            x0 = c * tile
            y0 = r * tile
            parity = (r + c) % 2

            if parity == 0:
                ctx.set_source_rgba(*tone_a)
                orient = (r * 3 + c) % 4
                if orient == 0:
                    ctx.move_to(x0, y0)
                    ctx.arc(x0, y0, tile, 0.0, math.pi / 2)
                elif orient == 1:
                    ctx.move_to(x0 + tile, y0)
                    ctx.arc(x0 + tile, y0, tile, math.pi / 2, math.pi)
                elif orient == 2:
                    ctx.move_to(x0 + tile, y0 + tile)
                    ctx.arc(x0 + tile, y0 + tile, tile, math.pi, 3 * math.pi / 2)
                else:
                    ctx.move_to(x0, y0 + tile)
                    ctx.arc(x0, y0 + tile, tile, 3 * math.pi / 2, 2 * math.pi)
                ctx.close_path()
                ctx.fill()
            else:
                ctx.set_source_rgba(*tone_b)
                orient = (r + c * 2) % 4
                if orient == 0:
                    pts = [(x0, y0), (x0 + tile, y0), (x0, y0 + tile)]
                elif orient == 1:
                    pts = [(x0 + tile, y0), (x0 + tile, y0 + tile), (x0, y0)]
                elif orient == 2:
                    pts = [(x0 + tile, y0 + tile), (x0, y0 + tile), (x0 + tile, y0)]
                else:
                    pts = [(x0, y0 + tile), (x0, y0), (x0 + tile, y0 + tile)]
                ctx.move_to(*pts[0])
                ctx.line_to(*pts[1])
                ctx.line_to(*pts[2])
                ctx.close_path()
                ctx.fill()

    # Thin contour keeps pi legible without flattening the grid.
    ctx.set_source_rgba(PALETTE["black"][0], PALETTE["black"][1], PALETTE["black"][2], 0.16)
    ctx.set_line_width(max(1.8, min(WIDTH_PX, HEIGHT_PX) * 0.0016))
    ctx.move_to(x, y)
    ctx.text_path("π")
    ctx.stroke()
    ctx.restore()


def draw_shape_cairo(
    ctx: "cairo.Context",
    cx: float,
    cy: float,
    size: float,
    digit: int,
    index: int,
) -> None:
    radius = size / 2.0
    color = digit_color(digit, index)
    ctx.set_source_rgb(*color)

    if digit <= 2:
        ctx.arc(cx, cy, radius * 0.95, 0, 2 * math.pi)
        ctx.fill()
    elif digit <= 5:
        side = size * 0.95
        ctx.rectangle(cx - side / 2, cy - side / 2, side, side)
        ctx.fill()
    elif digit <= 8:
        r = radius * 1.05
        orientation = (index % 4) * (math.pi / 2)
        pts = [
            (cx + r * math.cos(orientation - math.pi / 2), cy + r * math.sin(orientation - math.pi / 2)),
            (cx + r * math.cos(orientation + math.pi / 6), cy + r * math.sin(orientation + math.pi / 6)),
            (cx + r * math.cos(orientation + 5 * math.pi / 6), cy + r * math.sin(orientation + 5 * math.pi / 6)),
        ]
        ctx.move_to(*pts[0])
        ctx.line_to(*pts[1])
        ctx.line_to(*pts[2])
        ctx.close_path()
        ctx.fill()
    else:
        r = radius * 0.98
        start = (index % 4) * (math.pi / 2)
        ctx.move_to(cx, cy)
        ctx.arc(cx, cy, r, start, start + math.pi / 2)
        ctx.close_path()
        ctx.fill()


def draw_optional_digit(
    ctx: "cairo.Context",
    cx: float,
    cy: float,
    digit: int,
    shape_rgb: tuple[float, float, float],
    use_feynman_style: bool,
    font_size: float,
    font_family: str,
) -> None:
    ctx.select_font_face(font_family, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(font_size)
    ext = ctx.text_extents(str(digit))
    x = cx - (ext.width / 2 + ext.x_bearing)
    y = cy - (ext.height / 2 + ext.y_bearing)

    if use_feynman_style:
        # Highlight only Feynman-point 9s with white text + black contour.
        ctx.new_path()
        ctx.move_to(x, y)
        ctx.text_path(str(digit))
        ctx.set_source_rgb(*PALETTE["black"])
        ctx.set_line_width(max(0.8, font_size * 0.12))
        ctx.stroke_preserve()
        ctx.set_source_rgb(*PALETTE["white"])
        ctx.fill()
    else:
        luminance = 0.2126 * shape_rgb[0] + 0.7152 * shape_rgb[1] + 0.0722 * shape_rgb[2]
        text_color = PALETTE["black"] if luminance > 0.58 else PALETTE["white"]
        ctx.set_source_rgb(*text_color)
        ctx.move_to(x, y)
        ctx.show_text(str(digit))


def draw_poster_with_cairo(draw_digits: bool = False, digit_font: str = "inter") -> None:
    margin_x = WIDTH_PX * MARGIN_RATIO
    margin_y = HEIGHT_PX * MARGIN_RATIO
    inner_w = WIDTH_PX - 2 * margin_x
    inner_h = HEIGHT_PX - 2 * margin_y

    cells = build_cells(margin_x, margin_y, inner_w, inner_h)

    def render_to_context(ctx: "cairo.Context") -> None:
        ctx.set_source_rgb(*PALETTE["cream"])
        ctx.paint()

        for c in cells:
            size = c.base * digit_scale(c.digit)
            draw_shape_cairo(ctx, c.cx, c.cy, size, c.digit, c.index)
            if draw_digits:
                shape_rgb = digit_color(c.digit, c.index)
                digit_font_size = c.base * (0.34 if is_feynman_index(c.index) else 0.25)
                draw_optional_digit(
                    ctx,
                    c.cx,
                    c.cy,
                    c.digit,
                    shape_rgb=shape_rgb,
                    use_feynman_style=is_feynman_index(c.index),
                    font_size=digit_font_size,
                    font_family=FONT_PRESETS[digit_font]["cairo"],
                )

        draw_pi_organic_overlay_cairo(ctx, digit_font=digit_font)

        # Soft fade to white on the last 2 cm for print finishing.
        fade_h = (BOTTOM_FADE_CM * 10.0 / MM_PER_INCH) * DPI
        y0 = HEIGHT_PX - fade_h
        grad = cairo.LinearGradient(0, y0, 0, HEIGHT_PX)
        grad.add_color_stop_rgba(0.0, 1.0, 1.0, 1.0, 0.0)
        grad.add_color_stop_rgba(1.0, 1.0, 1.0, 1.0, 0.42)
        ctx.set_source(grad)
        ctx.rectangle(0, y0, WIDTH_PX, fade_h)
        ctx.fill()

    out_base = "pi_bauhaus_poster" if not draw_digits else f"pi_bauhaus_poster_{digit_font}"

    svg_surface = cairo.SVGSurface(f"{out_base}.svg", WIDTH_PX, HEIGHT_PX)
    svg_ctx = cairo.Context(svg_surface)
    render_to_context(svg_ctx)
    svg_surface.finish()

    png_surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, WIDTH_PX, HEIGHT_PX)
    png_ctx = cairo.Context(png_surface)
    render_to_context(png_ctx)
    png_surface.write_to_png(f"{out_base}.png")


def draw_poster_with_matplotlib(draw_digits: bool = False, digit_font: str = "inter") -> None:  # pragma: no cover
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.patheffects as pe
    import numpy as np
    from matplotlib.patches import Circle, Polygon, Rectangle, Wedge

    margin_x = WIDTH_PX * MARGIN_RATIO
    margin_y = HEIGHT_PX * MARGIN_RATIO
    inner_w = WIDTH_PX - 2 * margin_x
    inner_h = HEIGHT_PX - 2 * margin_y
    cells = build_cells(margin_x, margin_y, inner_w, inner_h)

    fig = plt.figure(figsize=(WIDTH_MM / MM_PER_INCH, HEIGHT_MM / MM_PER_INCH), dpi=DPI)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, WIDTH_PX)
    ax.set_ylim(HEIGHT_PX, 0)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.patch.set_facecolor(PALETTE["cream"])
    ax.set_facecolor(PALETTE["cream"])

    for c in cells:
        cx = c.cx
        cy = c.cy
        size = c.base * digit_scale(c.digit)
        color = digit_color(c.digit, c.index)
        if c.digit <= 2:
            ax.add_patch(Circle((cx, cy), radius=size * 0.48, facecolor=color, edgecolor="none"))
        elif c.digit <= 5:
            s = size * 0.95
            ax.add_patch(Rectangle((cx - s / 2, cy - s / 2), s, s, facecolor=color, edgecolor="none"))
        elif c.digit <= 8:
            r = size * 0.52
            orientation = (c.index % 4) * (math.pi / 2)
            pts = [
                (cx + r * math.cos(orientation - math.pi / 2), cy + r * math.sin(orientation - math.pi / 2)),
                (cx + r * math.cos(orientation + math.pi / 6), cy + r * math.sin(orientation + math.pi / 6)),
                (cx + r * math.cos(orientation + 5 * math.pi / 6), cy + r * math.sin(orientation + 5 * math.pi / 6)),
            ]
            ax.add_patch(Polygon(pts, closed=True, facecolor=color, edgecolor="none"))
        else:
            start = (c.index % 4) * 90
            ax.add_patch(Wedge((cx, cy), r=size * 0.5, theta1=start, theta2=start + 90, facecolor=color, edgecolor="none"))

        if draw_digits:
            is_feynman = is_feynman_index(c.index)
            text_size = c.base * (0.31 if is_feynman_index(c.index) else 0.22)
            if is_feynman:
                txt = ax.text(
                    cx,
                    cy,
                    str(c.digit),
                    ha="center",
                    va="center",
                    fontsize=text_size,
                    color=PALETTE["white"],
                    family=FONT_PRESETS[digit_font]["mpl"],
                )
                txt.set_path_effects([pe.Stroke(linewidth=max(0.9, text_size * 0.16), foreground=PALETTE["black"]), pe.Normal()])
            else:
                lum = 0.2126 * color[0] + 0.7152 * color[1] + 0.0722 * color[2]
                tcol = PALETTE["black"] if lum > 0.58 else PALETTE["white"]
                ax.text(
                    cx,
                    cy,
                    str(c.digit),
                    ha="center",
                    va="center",
                    fontsize=text_size,
                    color=tcol,
                    family=FONT_PRESETS[digit_font]["mpl"],
                )

    ax.text(
        WIDTH_PX / 2,
        HEIGHT_PX * 0.44,
        "π",
        ha="center",
        va="center",
        fontsize=min(WIDTH_PX, HEIGHT_PX) * 0.72,
        color=(*PALETTE["black"], 0.2),
        family=FONT_PRESETS[digit_font]["mpl"],
        fontweight="bold",
    )

    fade_h = (BOTTOM_FADE_CM * 10.0 / MM_PER_INCH) * DPI
    y0 = HEIGHT_PX - fade_h
    n = 256
    alpha = np.linspace(0.0, 0.42, n).reshape(n, 1)
    rgba = np.ones((n, 1, 4), dtype=float)
    rgba[:, :, 3] = alpha
    ax.imshow(rgba, extent=(0, WIDTH_PX, HEIGHT_PX, y0), origin="upper", interpolation="bicubic", zorder=20)

    out_base = "pi_bauhaus_poster" if not draw_digits else f"pi_bauhaus_poster_{digit_font}"
    fig.savefig(f"{out_base}.svg", format="svg", dpi=DPI)
    fig.savefig(f"{out_base}.png", format="png", dpi=DPI)
    plt.close(fig)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Generate a Bauhaus Pi poster.")
    parser.add_argument(
        "--draw-digits",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Draw tiny digits inside each shape (enabled by default).",
    )
    parser.add_argument(
        "--digit-font",
        choices=("all",) + tuple(FONT_PRESETS.keys()),
        default="all",
        help="Font preset for tiny digit labels. Default: build all variants.",
    )
    args = parser.parse_args()

    fonts = list(FONT_PRESETS.keys()) if (args.draw_digits and args.digit_font == "all") else [args.digit_font]

    generated: list[str] = []
    for font in fonts:
        if cairo is not None:
            draw_poster_with_cairo(draw_digits=args.draw_digits, digit_font=font)
        else:
            draw_poster_with_matplotlib(draw_digits=args.draw_digits, digit_font=font)
        if args.draw_digits:
            generated.extend([f"pi_bauhaus_poster_{font}.svg", f"pi_bauhaus_poster_{font}.png"])
        else:
            generated.extend(["pi_bauhaus_poster.svg", "pi_bauhaus_poster.png"])
            break

    # Keep canonical filenames pointing to the default (Inter) variant for compatibility.
    if args.draw_digits:
        shutil.copyfile("pi_bauhaus_poster_inter.svg", "pi_bauhaus_poster.svg")
        shutil.copyfile("pi_bauhaus_poster_inter.png", "pi_bauhaus_poster.png")
        generated.extend(["pi_bauhaus_poster.svg", "pi_bauhaus_poster.png"])

    backend = "pycairo" if cairo is not None else "matplotlib fallback"
    print(f"Generated {', '.join(generated)} via {backend}")


if __name__ == "__main__":
    main()
