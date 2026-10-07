# make_app_icon.py
# Rendert icons\menu-editor.svg (Quelle des Tool-Icons) in
#   - icons\menu-editor.ico  (16/24/32/48/64/128/256 px, PNG-Einträge)
#     → für das kompilierte EXE-Icon (PyInstaller --icon) und die Taskbar
#   - icons\menu-editor.png  (256 px, RGBA)
#     → für das Fenster-/Taskbar-Icon der laufenden Tk-Anwendung
#
# Aufruf:  python make_app_icon.py
#
# Der Renderer unterstützt die im SVG verwendeten Elemente
# <rect> (inkl. rx, stroke) und <circle> — interpretiert wird der
# viewBox, Elemente werden in Dokumentreihenfolge übereinander
# gezeichnet (Painter's Algorithmus). Kantenglättung über 4x
# Supersampling. PNG/ICO werden ohne externe Libraries geschrieben
# (zlib + struct).

import os
import struct
import xml.etree.ElementTree as ET
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
SVG_PATH = os.path.join(HERE, "icons", "menu-editor.svg")
ICO_PATH = os.path.join(HERE, "icons", "menu-editor.ico")
PNG_PATH = os.path.join(HERE, "icons", "menu-editor.png")

ICO_SIZES = [16, 24, 32, 48, 64, 128, 256]
PNG_SIZE = 256
SUPERSAMPLE = 4  # Kantenglättung

# Vereinfachte Kleinform (für 16/24/32 px): das volle Design hat bei
# diesen Größen zu viele Details (Punkte, dünne Balken → Moiré).
# Koordinaten im SVG-viewBox (0 0 180 220).
SMALL_SHAPES = [
    {"kind": "rect", "x": 0, "y": 0, "w": 180, "h": 220, "rx": 36,
     "fill": "#EEF3F8"},
    {"kind": "rect", "x": 34, "y": 34, "w": 112, "h": 152, "rx": 14,
     "fill": "#193B56"},
    {"kind": "rect", "x": 52, "y": 62, "w": 76, "h": 16, "rx": 8,
     "fill": "#FFFFFF"},
    {"kind": "rect", "x": 52, "y": 96, "w": 60, "h": 16, "rx": 8,
     "fill": "#B2C2D0"},
    {"kind": "rect", "x": 52, "y": 130, "w": 68, "h": 16, "rx": 8,
     "fill": "#B2C2D0"},
]
SMALL_SIZE_LIMIT = 48  # kleiner als diese Größe → SMALL_SHAPES


# ----------------------------------------------------------------------
# SVG parsen (rect + circle)
# ----------------------------------------------------------------------

def parse_svg(path):
    tree = ET.parse(path)
    root = tree.getroot()
    ns = root.tag.split("}")[0].strip("{") if "}" in root.tag else ""
    q = lambda tag: "{%s}%s" % (ns, tag) if ns else tag

    vb = (root.get("viewBox") or "0 0 180 220").replace(",", " ").split()
    vb = [float(v) for v in vb]
    shapes = []
    for el in root.iter():
        tag = el.tag.split("}")[-1]
        if tag == "rect":
            shapes.append({
                "kind": "rect",
                "x": float(el.get("x", 0)),
                "y": float(el.get("y", 0)),
                "w": float(el.get("width", 0)),
                "h": float(el.get("height", 0)),
                "rx": float(el.get("rx", 0)),
                "fill": el.get("fill"),
                "stroke": el.get("stroke"),
                "stroke_w": float(el.get("stroke-width", 0) or 0),
            })
        elif tag == "circle":
            shapes.append({
                "kind": "circle",
                "cx": float(el.get("cx", 0)),
                "cy": float(el.get("cy", 0)),
                "r": float(el.get("r", 0)),
                "fill": el.get("fill"),
            })
    return vb, shapes


def hex_to_rgb(color):
    color = (color or "").strip()
    if not color or color == "none":
        return None
    color = color.lstrip("#")
    if len(color) == 3:
        color = "".join(c * 2 for c in color)
    return (
        int(color[0:2], 16),
        int(color[2:4], 16),
        int(color[4:6], 16),
    )


# ----------------------------------------------------------------------
# Geometrie: Punkt-Tests (SVG-Koordinaten)
# ----------------------------------------------------------------------

def in_rounded_rect(x, y, rx0, ry0, rw, rh, rr):
    if rw <= 0 or rh <= 0:
        return False
    if x < rx0 or x > rx0 + rw or y < ry0 or y > ry0 + rh:
        return False
    rr = max(0.0, min(rr, min(rw, rh) / 2.0))
    if rr <= 0:
        return True
    cx = min(max(x, rx0 + rr), rx0 + rw - rr)
    cy = min(max(y, ry0 + rr), ry0 + rh - rr)
    return (x - cx) ** 2 + (y - cy) ** 2 <= rr ** 2


def point_in_shape(s, x, y):
    if s["kind"] == "rect":
        return in_rounded_rect(x, y, s["x"], s["y"], s["w"], s["h"], s["rx"])
    if s["kind"] == "circle":
        return (x - s["cx"]) ** 2 + (y - s["cy"]) ** 2 <= s["r"] ** 2
    return False


# ----------------------------------------------------------------------
# Rendern (Rückgabe: Zeilen von RGBA-Bytearrays)
# ----------------------------------------------------------------------

def render(vb, shapes, size):
    canvas = size * SUPERSAMPLE
    scale = canvas / max(vb[2], vb[3])          #_aspect-fit
    offx = (canvas - vb[2] * scale) / 2.0
    offy = (canvas - vb[3] * scale) / 2.0

    # Puffer: pro Pixel RGB + Coverage-Zähler
    cov = [[0] * canvas for _ in range(canvas)]
    rgb = [[(255, 255, 255)] * canvas for _ in range(canvas)]

    def paint(color, test):
        r, g, b = color
        for py in range(canvas):
            sy = (py + 0.5 - offy) / scale
            for px in range(canvas):
                sx = (px + 0.5 - offx) / scale
                if test(sx, sy):
                    cov[py][px] = 1
                    rgb[py][px] = (r, g, b)

    # Painter's Algorithmus: späteres Element gewinnt.
    # Stroke-Ring (außen: rx + w/2, innen: rx - w/2) wird nach dem
    # Fill desselben Elements gezeichnet — wie in SVG.
    ops = []
    for s in shapes:
        if s.get("fill"):
            ops.append((hex_to_rgb(s["fill"]),
                        lambda s=s: lambda x, y: point_in_shape(s, x, y)))
        if s.get("stroke") and s.get("stroke_w"):
            ops.append((hex_to_rgb(s["stroke"]),
                        lambda s=s: lambda x, y: _in_stroke_ring(s, x, y)))

    for color, make_test in ops:
        paint(color, make_test())

    # Downsample: Coverage über 4x4 → Alpha
    rows = []
    ss2 = SUPERSAMPLE * SUPERSAMPLE
    for y in range(size):
        row = bytearray()
        for x in range(size):
            hit = 0
            cr = cg = cb = 0
            for dy in range(SUPERSAMPLE):
                py = y * SUPERSAMPLE + dy
                crow = cov[py]
                rrow = rgb[py]
                for dx in range(SUPERSAMPLE):
                    px = x * SUPERSAMPLE + dx
                    if crow[px]:
                        hit += 1
                        c = rrow[px]
                        cr += c[0]; cg += c[1]; cb += c[2]
            if hit:
                row += bytes((cr // hit, cg // hit, cb // hit,
                              hit * 255 // ss2))
            else:
                row += bytes((0, 0, 0, 0))
        rows.append(row)
    return rows


def _in_stroke_ring(s, x, y):
    # Rechteck-Strokes im SVG-Icon sind ohne rx außen oder mit rx
    # definiert; Ring = Differenz äußere/innere Rundrechteck-Fläche.
    w2 = s["stroke_w"] / 2.0
    outer = point_in_shape(s, x, y)
    inner_rect = dict(s)
    inner_rect["x"] = s["x"] + w2
    inner_rect["y"] = s["y"] + w2
    inner_rect["w"] = max(0.0, s["w"] - s["stroke_w"])
    inner_rect["h"] = max(0.0, s["h"] - s["stroke_w"])
    inner_rect["rx"] = max(0.0, s["rx"] - w2)
    return outer and not point_in_shape(inner_rect, x, y)


# ----------------------------------------------------------------------
# PNG-Writer (RGBA8, keine externen Libraries)
# ----------------------------------------------------------------------

def write_png(path, size, rows):
    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)
    raw = b"".join(b"\x00" + bytes(r) for r in rows)
    png = (b"\x89PNG\r\n\x1a\n"
           + chunk(b"IHDR", ihdr)
           + chunk(b"IDAT", zlib.compress(raw, 9))
           + chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(png)


# ----------------------------------------------------------------------
# ICO-Writer (PNG-Einträge, von Windows Vista+ und PyInstaller gelesen)
# ----------------------------------------------------------------------

def write_ico(path, images):
    # images: Liste (size, png_bytes)
    count = len(images)
    out = struct.pack("<HHH", 0, 1, count)
    offset = 6 + 16 * count
    entries = b""
    blobs = b""
    for size, data in images:
        entries += struct.pack("<BBBBHHII",
                               size % 256, size % 256, 0, 0, 1, 32,
                               len(data), offset)
        blobs += data
        offset += len(data)
    with open(path, "wb") as f:
        f.write(out + entries + blobs)


def png_bytes(size, rows):
    # write_png ins memory (für ICO-Einträge)
    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)
    raw = b"".join(b"\x00" + bytes(r) for r in rows)
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(raw, 9))
            + chunk(b"IEND", b""))


def main():
    vb, shapes_full = parse_svg(SVG_PATH)
    print("SVG geladen: viewBox=%s, %d Formen" % (vb, len(shapes_full)))

    images = []
    for size in ICO_SIZES:
        shapes = shapes_full if size >= SMALL_SIZE_LIMIT else SMALL_SHAPES
        rows = render(vb, shapes, size)
        images.append((size, png_bytes(size, rows)))
        print("gerendert: %dx%d" % (size, size))

    write_ico(ICO_PATH, images)
    print("geschrieben:", ICO_PATH)

    rows = render(vb, shapes, PNG_SIZE)
    write_png(PNG_PATH, PNG_SIZE, rows)
    print("geschrieben:", PNG_PATH)


if __name__ == "__main__":
    main()
