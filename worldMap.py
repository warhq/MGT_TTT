"""Icosahedral world-surface map generator for Mongoose Traveller 2e.

`generate_world_map(uwp, ...)` renders a UWP-driven map of a world's surface
as the unfolded 20-triangle icosahedron in the World Builder's Handbook net
layout: 5 north-cap triangles whose apices represent the north pole, a
10-triangle equatorial zigzag band, and 5 south-cap triangles whose apices
represent the south pole. Each face is subdivided into smaller terrain cells
whose physical scale is derived from world Size. A scale-reference hexagon
(labelled with km per cell edge) and a color legend are drawn below the map.

Cell terrain (water / land / polar ice) is chosen from fractal value noise
seeded deterministically by the UWP, then thresholded so the water fraction
matches Hydrographics. The color palette is selected by Atmosphere. Polar ice
is concentrated near the cap apices (y near 0 or near 3h on the net).

Run standalone:
    python worldMap.py C566662-7 tarkine.png
"""

from __future__ import annotations

import hashlib
import math
import random
import sys
from typing import Iterable, List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont


# Traveller pseudo-hex digits: 0-9 then A-... skipping I and O.
_UWP_DIGITS = "0123456789ABCDEFGHJKLMNPQRSTUV"

_ATMO_DESC = {
    0: "Vacuum",
    1: "Trace",
    2: "Very thin (tainted)",
    3: "Very thin",
    4: "Thin (tainted)",
    5: "Thin",
    6: "Standard",
    7: "Standard (tainted)",
    8: "Dense",
    9: "Dense (tainted)",
    10: "Exotic",
    11: "Corrosive",
    12: "Insidious",
    13: "Dense, high",
    14: "Ellipsoid",
    15: "Thin, low",
}


def _uwp_value(c: str) -> int:
    try:
        return _UWP_DIGITS.index(c.upper())
    except ValueError as exc:
        raise ValueError(f"Invalid UWP digit: {c!r}") from exc


def _diameter_km(size: int) -> int:
    # Size 0 is "asteroid / planetoid belt" — treat as a small body for scale.
    return 800 if size == 0 else 1600 * size


def _cells_per_face_edge(size: int) -> int:
    if size <= 0:
        return 3
    if size <= 3:
        return 4
    if size <= 6:
        return 6
    if size <= 9:
        return 8
    return 10


def _cell_side_km(size: int) -> float:
    # Edge of icosahedron inscribed in sphere of radius r:
    #   a = 4r / sqrt(10 + 2*sqrt(5))   (chord length)
    radius = _diameter_km(size) / 2
    icosa_edge = (4 * radius) / math.sqrt(10 + 2 * math.sqrt(5))
    return icosa_edge / _cells_per_face_edge(size)


def _palette(atmo: int) -> dict:
    if atmo == 0:
        return {"water": (90, 90, 100), "land": (140, 130, 120),
                "ice": (210, 210, 220), "name": "Vacuum"}
    if atmo <= 3:
        return {"water": (40, 60, 90), "land": (190, 140, 90),
                "ice": (230, 230, 235), "name": "Thin & dusty"}
    if atmo <= 9:
        return {"water": (30, 80, 160), "land": (80, 140, 60),
                "ice": (240, 240, 250), "name": "Breathable"}
    if atmo == 10:
        return {"water": (110, 60, 140), "land": (170, 130, 50),
                "ice": (200, 220, 200), "name": "Exotic"}
    return {"water": (160, 130, 30), "land": (130, 80, 30),
            "ice": (170, 150, 130), "name": "Corrosive"}


class _ValueNoise:
    """Bilinear value noise + fBM on an integer grid. Seeded, deterministic."""

    def __init__(self, seed: int, grid: int = 64):
        self._grid = grid
        rng = random.Random(seed)
        self._v = [[rng.random() for _ in range(grid)] for _ in range(grid)]

    def _g(self, ix: int, iy: int) -> float:
        return self._v[iy % self._grid][ix % self._grid]

    def _smooth(self, x: float, y: float, scale: float) -> float:
        fx, fy = x / scale, y / scale
        ix, iy = int(math.floor(fx)), int(math.floor(fy))
        tx, ty = fx - ix, fy - iy
        sx = tx * tx * (3 - 2 * tx)
        sy = ty * ty * (3 - 2 * ty)
        v00 = self._g(ix, iy)
        v10 = self._g(ix + 1, iy)
        v01 = self._g(ix, iy + 1)
        v11 = self._g(ix + 1, iy + 1)
        return ((v00 * (1 - sx) + v10 * sx) * (1 - sy)
                + (v01 * (1 - sx) + v11 * sx) * sy)

    def fbm(self, x: float, y: float, base_scale: float, octaves: int = 4) -> float:
        total = 0.0
        amp = 1.0
        scale = base_scale
        norm = 0.0
        for _ in range(octaves):
            total += amp * self._smooth(x, y, scale)
            norm += amp
            amp *= 0.5
            scale *= 0.5
        return total / norm


# ---------------------------------------------------------------------------
# Icosahedron net: World Builder's Handbook layout.
#   Row 1 (y in [0, h])   : 5 north-cap triangles, apices at the north pole
#   Row 2 (y in [h, 2h])  : 10-triangle equatorial band in zigzag
#   Row 3 (y in [2h, 3h]) : 5 south-cap triangles, apices at the south pole
# The 5 + 10 + 5 split is the proper net. South caps are x-offset by face_side/2
# from the north caps — that's the antiprism twist, not a bug.
# ---------------------------------------------------------------------------

def _icosahedron_net(face_side: float, ox: float, oy: float):
    fs = face_side
    h = fs * math.sqrt(3) / 2
    triangles = []

    # North caps: 5 point-up triangles, apices at y=0 (north pole),
    # bases at y=h sharing edges with band point-down triangles.
    for k in range(5):
        x = ox + k * fs
        vertices = [
            (x + fs / 2, oy),         # apex (north pole)
            (x, oy + h),              # base-left
            (x + fs, oy + h),         # base-right
        ]
        triangles.append((f"N{k + 1}", vertices, True))

    # Equatorial band: 10 zigzag triangles between y=h and y=2h.
    band_y = oy + h
    for col in range(10):
        x = ox + col * (fs / 2)
        if col % 2 == 0:
            # point-down: base shared with a north cap at y=h
            vertices = [
                (x, band_y),
                (x + fs, band_y),
                (x + fs / 2, band_y + h),
            ]
            triangles.append((f"B{col + 1}", vertices, False))
        else:
            # point-up: base shared with a south cap at y=2h
            vertices = [
                (x + fs / 2, band_y),
                (x, band_y + h),
                (x + fs, band_y + h),
            ]
            triangles.append((f"B{col + 1}", vertices, True))

    # South caps: 5 point-down triangles, x-offset by fs/2,
    # apices at y=3h (south pole), bases at y=2h sharing edges with band point-ups.
    south_y = oy + 2 * h
    for k in range(5):
        x = ox + fs / 2 + k * fs
        vertices = [
            (x, south_y),
            (x + fs, south_y),
            (x + fs / 2, south_y + h),    # apex (south pole)
        ]
        triangles.append((f"S{k + 1}", vertices, False))

    width = 11 * fs / 2
    height = 3 * h
    return triangles, width, height


def _subdivide_triangle(vertices, is_up: bool, n: int) -> Iterable[List[Tuple[float, float]]]:
    """Yield n² small-triangle polygons covering the parent triangle."""
    if is_up:
        apex, left, right = vertices
    else:
        left, right, apex = vertices  # point-down: apex is the bottom point

    def vert(row: int, col: int) -> Tuple[float, float]:
        if row == 0:
            return apex
        t = row / n
        pl = (apex[0] + t * (left[0] - apex[0]),
              apex[1] + t * (left[1] - apex[1]))
        pr = (apex[0] + t * (right[0] - apex[0]),
              apex[1] + t * (right[1] - apex[1]))
        s = col / row
        return (pl[0] + s * (pr[0] - pl[0]),
                pl[1] + s * (pr[1] - pl[1]))

    for row in range(n):
        for col in range(row + 1):
            yield [vert(row, col), vert(row + 1, col), vert(row + 1, col + 1)]
            if col < row:
                yield [vert(row, col), vert(row + 1, col + 1), vert(row, col + 1)]


def _centroid(poly):
    return (sum(p[0] for p in poly) / 3, sum(p[1] for p in poly) / 3)


def _seed_from_uwp(uwp: str, seed: Optional[int]) -> int:
    if seed is not None:
        return seed
    return int.from_bytes(hashlib.sha256(uwp.encode("ascii")).digest()[:4], "big")


def _load_fonts():
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/Library/Fonts/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "C:\\Windows\\Fonts\\arial.ttf",
    ]
    body = title = None
    for path in candidates:
        try:
            body = ImageFont.truetype(path, 14)
            title = ImageFont.truetype(path, 20)
            break
        except OSError:
            continue
    if body is None:
        body = ImageFont.load_default()
        title = body
    return body, title


def _hex_polygon(cx: float, cy: float, r: float, flat_top: bool = False) -> List[Tuple[float, float]]:
    """Regular hexagon centred at (cx, cy) with circumradius r."""
    offset = 0 if flat_top else math.pi / 6
    return [
        (cx + r * math.cos(offset + i * math.pi / 3),
         cy + r * math.sin(offset + i * math.pi / 3))
        for i in range(6)
    ]


def generate_world_map(
    uwp: str,
    out_path: Optional[str] = None,
    seed: Optional[int] = None,
    face_side: int = 240,
) -> Image.Image:
    """Render an icosahedral world surface map for the given UWP.

    Returns a `PIL.Image.Image`. If `out_path` is given, also writes a PNG.
    `seed` defaults to a hash of the UWP, so the same UWP always produces
    the same map.
    """
    if len(uwp) < 9:
        raise ValueError(f"UWP must be at least 9 characters, got {uwp!r}")

    starport = uwp[0]
    size = _uwp_value(uwp[1])
    atmo = _uwp_value(uwp[2])
    hydro = _uwp_value(uwp[3])

    n_cells = _cells_per_face_edge(size)
    palette = _palette(atmo)
    noise = _ValueNoise(_seed_from_uwp(uwp, seed))

    margin = 50
    map_origin_x = margin
    map_origin_y = margin
    triangles, map_w, map_h = _icosahedron_net(face_side, map_origin_x, map_origin_y)

    legend_height = 220
    img_w = int(map_w + 2 * margin)
    img_h = int(map_h + legend_height + 3 * margin)

    img = Image.new("RGB", (img_w, img_h), (18, 20, 30))
    draw = ImageDraw.Draw(img)
    body_font, title_font = _load_fonts()

    # ---------- pass 1: gather cell noise so we can pick an exact hydro-% threshold
    cells: List[Tuple[List[Tuple[float, float]], float, float]] = []
    base_scale = face_side * 0.9
    for _face_id, vertices, is_up in triangles:
        for poly in _subdivide_triangle(vertices, is_up, n_cells):
            cx, cy = _centroid(poly)
            rel_y = (cy - map_origin_y) / map_h if map_h > 0 else 0.5
            lat_factor = abs(rel_y - 0.5) * 2  # 0=equator, 1=pole
            nv = noise.fbm(cx, cy, base_scale=base_scale, octaves=4)
            cells.append((poly, nv, lat_factor))

    hydro_frac = max(0.0, min(hydro / 10, 1.0))
    sorted_nv = sorted(c[1] for c in cells)
    idx = min(int(len(sorted_nv) * hydro_frac), len(sorted_nv) - 1)
    water_threshold = sorted_nv[idx] if sorted_nv else 0.5

    # ---------- pass 2: draw cells.
    # With the 5+10+5 net, lat_factor > ~0.66 lies inside the cap regions
    # (north cap is y in [0, h] of a 3h-tall map). Picking 0.75 gives nicely
    # tapered polar caps near the apex points.
    for poly, nv, lat_factor in cells:
        if lat_factor > 0.75 and nv > water_threshold * 0.55:
            color = palette["ice"]
        elif nv < water_threshold:
            color = palette["water"]
        else:
            color = palette["land"]
        draw.polygon(poly, fill=color)

    # ---------- pass 3: face outlines for the 20-triangle net
    for _face_id, vertices, _is_up in triangles:
        draw.polygon(vertices, outline=(8, 8, 12), width=2)

    # ---------- legend ----------
    legend_top = int(map_origin_y + map_h + margin)
    draw.line(
        [(margin, legend_top - 12), (img_w - margin, legend_top - 12)],
        fill=(70, 75, 90), width=1,
    )

    # Scale-reference hexagon (user-requested "big hex" showing km/cell)
    cell_km = _cell_side_km(size)
    hex_cx = margin + 90
    hex_cy = legend_top + 90
    hex_r = 70
    hex_poly = _hex_polygon(hex_cx, hex_cy, hex_r, flat_top=False)
    draw.polygon(hex_poly, fill=(50, 55, 70), outline=(230, 230, 240), width=3)

    km_text = f"{cell_km:,.0f} km"
    bbox = draw.textbbox((0, 0), km_text, font=title_font)
    draw.text(
        (hex_cx - (bbox[2] - bbox[0]) / 2, hex_cy - (bbox[3] - bbox[1]) / 2 - 6),
        km_text, fill=(255, 255, 255), font=title_font,
    )
    sub = "per cell edge"
    bbox = draw.textbbox((0, 0), sub, font=body_font)
    draw.text(
        (hex_cx - (bbox[2] - bbox[0]) / 2, hex_cy + 14),
        sub, fill=(200, 200, 210), font=body_font,
    )
    label = "Map scale"
    bbox = draw.textbbox((0, 0), label, font=body_font)
    draw.text(
        (hex_cx - (bbox[2] - bbox[0]) / 2, hex_cy + hex_r + 8),
        label, fill=(180, 180, 200), font=body_font,
    )

    # Color swatches
    swatch_x = margin + 200
    swatch_y = legend_top + 18
    sw = 28
    swatches = [
        (palette["water"], "Water (Hydrographics)"),
        (palette["land"], f"Land ({palette['name']} atmosphere)"),
        (palette["ice"], "Polar ice"),
    ]
    for i, (color, label) in enumerate(swatches):
        y = swatch_y + i * 40
        draw.rectangle([swatch_x, y, swatch_x + sw, y + sw],
                       fill=color, outline=(230, 230, 240), width=1)
        draw.text((swatch_x + sw + 12, y + 6), label,
                  fill=(235, 235, 245), font=body_font)

    # World info column
    info_x = swatch_x + 320
    info_y = legend_top + 12
    diameter = _diameter_km(size)
    atmo_label = _ATMO_DESC.get(atmo, "Unknown")
    lines = [
        (f"UWP  {uwp}", title_font, (255, 255, 255)),
        (f"Starport class {starport}", body_font, (220, 220, 230)),
        (f"Size {uwp[1]}  diameter {diameter:,} km", body_font, (220, 220, 230)),
        (f"Atm  {uwp[2]}  {atmo_label}", body_font, (220, 220, 230)),
        (f"Hyd  {uwp[3]}  {int(hydro_frac * 100)}% surface water", body_font, (220, 220, 230)),
        (f"Map  20 faces × {n_cells}² cells  =  {20 * n_cells * n_cells} surface cells",
         body_font, (180, 185, 205)),
    ]
    cur_y = info_y
    for text, font, color in lines:
        draw.text((info_x, cur_y), text, fill=color, font=font)
        cur_y += 22 if font is title_font else 19

    if out_path:
        img.save(out_path)
    return img


if __name__ == "__main__":
    uwp = sys.argv[1] if len(sys.argv) > 1 else "C566662-7"
    out = sys.argv[2] if len(sys.argv) > 2 else f"world_{uwp.replace('-', '')}.png"
    generate_world_map(uwp, out_path=out)
    print(f"Wrote {out}")
