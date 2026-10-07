# make_icons.py
# Erzeugt alle Toolbar-Icons (16x16 PNG, Alpha-Kanal) im Ordner `icons\`
# als ORIGINALE Pixel-Grafiken (keine Übernahme aus Windows-DLLs).
#
# Aufruf:  python make_icons.py
# Ergebnis: icons\<name>.png (11 Dateien) + tmp\icons_contact_sheet.png
#           (8x-Kontaktbild zur visuellen Prüfung).
#
# Die Icons werden absichtlich als Pixel-Raster definiert; jedes Raster
# ist eine Liste mit 16 Strings à 16 Zeichen ('.' = transparent).

import os
import sys
import math
import tkinter as tk

HERE = os.path.dirname(os.path.abspath(__file__))
ICON_DIR = os.path.join(HERE, "icons")
TMP_DIR = os.path.join(HERE, "tmp")

SIZE = 16

# ----------------------------------------------------------------------
# Paletten (Zeichen → RGBA-Hex); '.' ist immer transparent
# ----------------------------------------------------------------------

PALETTE = {
    "G": "#5b6770",  # Umriss grau
    "W": "#f4f6f8",  # Papier weiß
    "F": "#d8dde2",  # Papier-Falz
    "L": "#9aa5ad",  # Textzeilen hellgrau
    "Y": "#f0c060",  # Ordner amber
    "y": "#c08a30",  # Ordner dunkel
    "B": "#2e86d1",  # Blau (Pfeile/Ring)
    "b": "#1b5e93",  # Blau dunkel
    "R": "#e04b3f",  # Rot
    "r": "#a83228",  # Rot dunkel
    "X": "#ffffff",  # Weiß (X im Kreis)
    "O": "#e8912d",  # Orange (Stiftkörper)
    "E": "#e88aa0",  # Radiergummi rosa
    "H": "#e0b880",  # Stift-Holz
    "D": "#3a3f44",  # Dunkelgrau (Stiftspitze)
}


def blank_grid():
    return [["." for _ in range(SIZE)] for _ in range(SIZE)]


def grid_from_rows(rows):
    assert len(rows) == SIZE, "Raster braucht 16 Zeilen"
    for i, row in enumerate(rows):
        assert len(row) == SIZE, "Zeile %d braucht 16 Zeichen (hat %d)" % (i, len(row))
    return [list(row) for row in rows]


def set_px(grid, x, y, ch):
    if 0 <= x < SIZE and 0 <= y < SIZE:
        grid[y][x] = ch


# ----------------------------------------------------------------------
# Programmatisch aufgebaute Raster (Kreise/Ringe)
# ----------------------------------------------------------------------

def delete_grid():
    # Roter Kreis mit weißem X
    g = blank_grid()
    for y in range(SIZE):
        for x in range(SIZE):
            d2 = (x - 7.5) ** 2 + (y - 7.5) ** 2
            if d2 <= 6.9 ** 2:
                g[y][x] = "R"
            if 5.7 ** 2 <= d2 <= 6.9 ** 2:
                g[y][x] = "r"  # dunkler Rand
    for i in range(5, 11):
        set_px(g, i, i, "X")
        set_px(g, i, 15 - i, "X")
        set_px(g, i + 1, i, "X")          # X 2px dick
        set_px(g, i, 14 - i, "X")
    return g


def refresh_grid():
    # Zwei blaue Kreisbögen mit Pfeilspitzen (im Uhrzeigersinn)
    g = blank_grid()
    for y in range(SIZE):
        for x in range(SIZE):
            d2 = (x - 7.5) ** 2 + (y - 7.5) ** 2
            if 4.2 ** 2 <= d2 <= 6.3 ** 2:
                ang = math.degrees(math.atan2(y - 7.5, x - 7.5)) % 360
                if 25 <= ang <= 155 or 205 <= ang <= 335:
                    g[y][x] = "B"
    _arc_arrow_head(g, 155)
    _arc_arrow_head(g, 335)
    return g


def _arc_arrow_head(g, end_angle):
    # Gefüllte Pfeilspitze am Ende eines Bogens (Richtung: im
    # Uhrzeigersinn, also tangential weiterdrehend).
    a = math.radians(end_angle)
    ex = 7.5 + 5.2 * math.cos(a)
    ey = 7.5 + 5.2 * math.sin(a)
    tx, ty = -math.sin(a), math.cos(a)      # Laufrichtung
    nx, ny = math.cos(a), math.sin(a)       # radial nach außen
    for s in range(3):                      # entlang der Laufrichtung
        half = 2 - s
        for w in range(-half, half + 1):
            x = ex + tx * s * 1.1 + nx * w * 0.8
            y = ey + ty * s * 1.1 + ny * w * 0.8
            set_px(g, int(round(x)), int(round(y)), "B")


def shutdown_grid():
    # Rotes Power-Symbol: Ring mit Lücke oben + vertikaler Balken
    g = blank_grid()
    for y in range(SIZE):
        for x in range(SIZE):
            d2 = (x - 7.5) ** 2 + (y - 7.5) ** 2
            if 4.3 ** 2 <= d2 <= 6.4 ** 2:
                g[y][x] = "R"
    # Lücke oben (durch die der Balken läuft)
    for y in range(4):
        for x in range(5, 11):
            g[y][x] = "."
    # Balken
    for y in range(1, 9):
        set_px(g, 7, y, "R")
        set_px(g, 8, y, "R")
    return g


def help_grid():
    # Blauer Kreis mit weißem Fragezeichen
    g = blank_grid()
    for y in range(SIZE):
        for x in range(SIZE):
            d2 = (x - 7.5) ** 2 + (y - 7.5) ** 2
            if d2 <= 6.9 ** 2:
                g[y][x] = "B"
            if 5.7 ** 2 <= d2 <= 6.9 ** 2:
                g[y][x] = "b"  # dunkler Rand
    # Fragezeichen (weiß)
    mark = [
        (6, 3), (7, 3), (8, 3), (9, 3),
        (5, 4), (10, 4), (11, 4),
        (5, 5), (10, 5), (11, 5),
        (9, 6), (10, 6),
        (8, 7), (9, 7),
        (7, 8), (8, 8),
        (7, 9), (8, 9),
        (7, 11), (8, 11),
    ]
    for x, y in mark:
        set_px(g, x, y, "X")
        set_px(g, x + 1, y, "X")  # 2 px dick
    return g


# ----------------------------------------------------------------------
# Von Hand definierte Raster
# ----------------------------------------------------------------------

NEW_ENTRY = grid_from_rows([
    "................",
    "..GGGGGGGGG.....",
    "..GWWWWWWWGG....",
    "..GWWWWWWWGFG...",
    "..GWWWWWWWGFFG..",
    "..GWWWWWWWWGGG..",
    "..GWWWWWWWWWWG..",
    "..GWWWWWWWWWWG..",
    "..GWWWWWWWWWWG..",
    "..GWWWWWWWWWWG..",
    "..GWWWWWWWWWWG..",
    "..GWWWWWWWWWWG..",
    "..GWWWWWWWWWWG..",
    "..GWWWWWWWWWWG..",
    "..GGGGGGGGGGGG..",
    "................",
])

NEW_MENU = grid_from_rows([
    "................",
    "..GGGGGGGGG.....",
    "..GWWWWWWWGG....",
    "..GWWWWWWWGFG...",
    "..GWWWWWWWGFFG..",
    "..GWWWWWWWWGGG..",
    "..GWWWWWWWWWWG..",
    "..GWLLLLLLLLWG..",
    "..GWWWWWWWWWWG..",
    "..GWLLLLLLLLWG..",
    "..GWWWWWWWWWWG..",
    "..GWLLLLLLLLWG..",
    "..GWWWWWWWWWWG..",
    "..GWWWWWWWWWWG..",
    "..GGGGGGGGGGGG..",
    "................",
])

NEW_MENU_ITEM = grid_from_rows([
    "................",
    "................",
    "...GGGGGGGGGG...",
    "...GYYYYYYYYG...",
    "...GYYYYYYYYG...",
    ".GGGGGGGGGGGGG..",
    ".GYYYYYYYYYYYYG.",
    ".GYWWWWWWWWWYYG.",
    ".GYWGGGGGGGWYYG.",
    ".GYWGGGGGGGWYYG.",
    ".GYWGGGGGGGWYYG.",
    ".GYWWWWWWWWWYYG.",
    ".GYYYYYYYYYYYYG.",
    ".GGGGGGGGGGGGGG.",
    "................",
    "................",
])

EDIT = grid_from_rows([
    "................",
    "..GGGGGGGG..EE..",
    "..GWWWWWWWG.EE..",
    "..GWWWWWWWG.OO..",
    "..GWWWWWWWG.OO..",
    "..GWWWWWWWG.OO..",
    "..GWWWWWWWG.OO..",
    "..GWWWWWWWG.OO..",
    "..GWWWWWWWG.OO..",
    "..GWWWWWWWG.OO..",
    "..GWWWWWWWG.HH..",
    "..GGGGGGGGG.DD..",
    "................",
    "................",
    "................",
    "................",
])

UNDO = grid_from_rows([
    "................",
    "................",
    "..........BBB...",
    ".........B...B..",
    ".........B....B.",
    "..............B.",
    "...B..........B.",
    "..BB..........B.",
    ".BBBBBBBBBBBBBB.",
    "..BB............",
    "...B............",
    "................",
    "................",
    "................",
    "................",
    "................",
])

def _block_arrow(direction):
    # Gerader Blockpfeil; direction "down" oder "up"
    g = blank_grid()
    rows_down = [
        "......BBBB......",
        "......BBBB......",
        "......BBBB......",
        "......BBBB......",
        "......BBBB......",
        "......BBBB......",
        "......BBBB......",
        "..BBBBBBBBBBBB..",
        "...BBBBBBBBBB...",
        "....BBBBBBBB....",
        ".....BBBBBB.....",
        "......BBBB......",
        "................",
        "................",
        "................",
        "................",
    ]
    rows = rows_down if direction == "down" else rows_down[::-1]
    return grid_from_rows(rows)

MOVE_DOWN = _block_arrow("down")
MOVE_UP = _block_arrow("up")

BACKUP = grid_from_rows([
    "................",
    "..GGGGGGGGGGG...",
    "..GYYYYYYYYYYG..",
    "..GYYYYYYYYYYG..",
    ".GGGGGGGGGGGGGG.",
    ".GYYYYYYYYYYYYG.",
    ".GYYYYYBBYYYYYG.",
    ".GYYYYYBBYYYYYG.",
    ".GYYYBBBBBBYYYG.",
    ".GYYYYBBBBYYYYG.",
    ".GYYYYYBBYYYYYG.",
    ".GYYYYYYYYYYYYG.",
    ".GGGGGGGGGGGGGG.",
    "................",
    "................",
    "................",
])

ICONS = {
    "new_entry": NEW_ENTRY,
    "new_menu": NEW_MENU,
    "new_menu_item": NEW_MENU_ITEM,
    "edit": EDIT,
    "delete": delete_grid(),
    "refresh": refresh_grid(),
    "undo": UNDO,
    "backup": BACKUP,
    "move_up": MOVE_UP,
    "move_down": MOVE_DOWN,
    "shutdown_menu": shutdown_grid(),
    "help": help_grid(),
}


# ----------------------------------------------------------------------
# Rendern → PNG (Tk PhotoImage.write) + Kontaktbild
# ----------------------------------------------------------------------

def grid_to_photo(root, grid):
    img = tk.PhotoImage(width=SIZE, height=SIZE, master=root)
    for y in range(SIZE):
        for x in range(SIZE):
            ch = grid[y][x]
            if ch in PALETTE:
                img.put(PALETTE[ch], to=(x, y))
            else:
                img.transparency_set(x, y, True)
    return img


def grid_to_ascii(grid):
    return "\n".join("".join("#" if c != "." else "." for c in row) for row in grid)


def contact_sheet(root, photos, scale=8):
    n = len(photos)
    pad = 2
    w = (SIZE * scale + pad) * n + pad
    h = SIZE * scale + 2 * pad
    sheet = tk.PhotoImage(width=w, height=h, master=root)
    for idx, (name, img) in enumerate(photos.items()):
        x0 = pad + idx * (SIZE * scale + pad)
        sheet.put(PALETTE["G"], to=(x0, pad, x0 + SIZE * scale + 1, h - 1))
        for y in range(SIZE):
            for x in range(SIZE):
                if img.transparency_get(x, y):
                    continue
                c = "#%02x%02x%02x" % img.get(x, y)
                sheet.put(c, to=(
                    x0 + 1 + x * scale, pad + 1 + y * scale,
                    x0 + 1 + (x + 1) * scale, pad + 1 + (y + 1) * scale
                ))
    return sheet


def main():
    os.makedirs(ICON_DIR, exist_ok=True)
    os.makedirs(TMP_DIR, exist_ok=True)

    root = tk.Tk()
    root.withdraw()

    photos = {}
    for name, grid in ICONS.items():
        img = grid_to_photo(root, grid)
        photos[name] = img
        out = os.path.join(ICON_DIR, name + ".png")
        img.write(out, format="png")
        print("geschrieben:", out)
        print(grid_to_ascii(grid))
        print()

    sheet = contact_sheet(root, photos)
    sheet_path = os.path.join(TMP_DIR, "icons_contact_sheet.png")
    sheet.write(sheet_path, format="png")
    print("Kontaktbild:", sheet_path)

    root.destroy()


if __name__ == "__main__":
    main()
