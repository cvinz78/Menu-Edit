#!/usr/bin/env python3
# -*- coding: utf-8 -*-

r"""
Registry Context-Menu Editor

Verwaltet Einträge unter:

    HKEY_CLASSES_ROOT\Directory\Background\Shell
    HKEY_CLASSES_ROOT\DesktopBackground\Shell

Funktionen:
- Einträge und Menüs erstellen
- Einträge innerhalb von Menüs erstellen
- Menüs bearbeiten/löschen
- Position Top/Mitte/Bottom
- Verschieben per Buttons oder Drag & Drop
- Undo der letzten 10 Änderungen
- SubCommands bei Menüs
- Icon-Auswahl
- Icon-Vorschau in der Gesamtübersicht
- Drei Farbmodi
- Umschaltung zwischen beiden Registry-Bereichen
- Backup als .reg
- Beide Registry-Bereiche einzeln oder gemeinsam sichern
- Speicherung des zuletzt verwendeten Backup-Pfades
- Windows-Systemicons für Aktionsbuttons
- Tooltips für Aktionsbuttons
"""

import os
import re
import sys
import time
import ctypes
import ctypes.wintypes as wintypes
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import configparser

# Versionsnummer: bei jeder Bearbeitung um 0.1 anheben (siehe AGENTS.md §8.2)
APP_VERSION = "4.6"


# ----------------------------------------------------------------------
# Zweisprachigkeit (v3.5)
# Deutsch ist Standard und dient als Schlüssel; die englischen Texte
# liegen in TRANSLATIONS (exakt) bzw. PREFIX_TRANSLATIONS (für dynamisch
# zusammengebaute Meldungen — längster Treffer gewinnt). Unbekannte
# Texte fallen unverändert durch.
# ----------------------------------------------------------------------

APP_LANG = "de"  # "de" | "en"; wird beim Start aus settings.ini gesetzt

TRANSLATIONS = {
    # Fenster / Leisten
    "Hilfe": "Help",
    "Sprache: Deutsch": "Language: German",
    "Sprache: English": "Language: English",
    "Design: ": "Theme: ",
    "Bereich: ": "Area: ",
    "Administrator: Ja": "Administrator: Yes",
    "Administrator: Nein (Schreibrechte eventuell eingeschränkt!)":
        "Administrator: No (write access may be limited!)",
    "Eintrag": "Entry",
    "Details / Pfad": "Details / Path",
    "Obers\\Unteres Menü": "Upper\\Lower Menu",
    # Toolbar-Tooltips
    "Neuen Eintrag erstellen": "Create new entry",
    "Neues Menü erstellen": "Create new menu",
    "Eintrag in Menü erstellen": "Create entry inside menu",
    "Ausgewählten Eintrag bearbeiten": "Edit selected entry",
    "Ausgewählten Eintrag löschen": "Delete selected entry",
    "Ansicht aktualisieren": "Refresh view",
    "Letzte Änderung rückgängig machen (max. 10)":
        "Undo last change (max. 10)",
    "Backup": "Backup",
    "Auswahl nach oben verschieben": "Move selection up",
    "Auswahl nach unten verschieben": "Move selection down",
    "Shutdown-Menü anlegen (Neustart / Herunterfahren / Abmelden)":
        "Create shutdown menu (restart / shutdown / log off)",
    # Rechtsklick-Kontextmenü
    "Bearbeiten": "Edit",
    "Löschen": "Delete",
    "Letzte Änderung rückgängig machen": "Undo last change",
    "Shutdown-Menü anlegen": "Create shutdown menu",
    # Backup-Popup
    "Beide Bereiche einzeln sichern": "Back up both areas separately",
    "Beide Bereiche gemeinsam sichern": "Back up both areas combined",
    "Aktuellen Bereich sichern": "Back up current area",
    "Backup-Einstellungen": "Backup settings",
    # Dialoge: Buttons / Felder
    "OK": "OK",
    "Abbrechen": "Cancel",
    # Positions-Werte (Anzeige; intern bleibt Mitte/Top/Bottom)
    "Mitte": "Center",
    # Dialog-Feldlabel
    "Name:": "Name:",
    "Schließen": "Close",
    "Auswählen...": "Browse...",
    "Speichern": "Save",
    "Name:": "Name:",
    "Anzeigename:": "Display name:",
    "Befehl:": "Command:",
    "Icon:": "Icon:",
    "Position:": "Position:",
    "Menü:": "Menu:",
    "Übergeordnetes Menü:": "Parent menu:",
    "(Hauptebene)": "(Top level)",
    "Bitte einen Namen angeben.": "Please enter a name.",
    "Bitte einen Programmpfad angeben.": "Please enter a program path.",
    "Bitte ein Menü auswählen.": "Please select a menu.",
    "Standard Speicherpfad:": "Default save path:",
    "Reg-Dateien": "Reg files",
    "Programme": "Programs",
    "Alle Dateien": "All files",
    "Icons/Programme": "Icons/Programs",
    # Meldungs-Titel
    "Fehler": "Error",
    "Hinweis": "Note",
    "Rückgängig": "Undo",
    "Windows-Eintrag löschen": "Delete Windows entry",
    "Löschen bestätigen": "Confirm deletion",
    "Shutdown-Menü": "Shutdown menu",
    # Statische Meldungen
    "Bitte zuerst einen Eintrag auswählen.": "Please select an entry first.",
    "Keine Änderungen zum Rückgängig machen.":
        "No changes to undo.",
    "Zugriff verweigert. Bitte starte das Programm als Administrator neu!":
        "Access denied. Please restart the program as administrator!",
    "Backup-Einstellungen gespeichert.": "Backup settings saved.",
    "Shutdown-Menü ist bereits vollständig vorhanden — keine Änderungen nötig.":
        "Shutdown menu is already complete — no changes needed.",
    # v3.5: Dialoge, Backups, Erststart
    "Neuer Eintrag (App)": "New entry (app)",
    "Neues Menü": "New menu",
    "Neuer Eintrag (in Menü)": "New entry (in menu)",
    "Standard-Speicherpfad für Backups": "Default backup save path",
    "Ordner auswählen": "Choose folder",
    "Backup speichern": "Save backup",
    "Gemeinsames Backup speichern": "Save combined backup",
    "Directory-Background Backup speichern": "Save Directory-Background backup",
    "DesktopBackground Backup speichern": "Save DesktopBackground backup",
    "Menü bearbeiten: ": "Edit menu: ",
    "Eintrag bearbeiten: ": "Edit entry: ",
    "Backup erstellt": "Backup created",
    "Backup-Fehler": "Backup error",
    "Erststart – vollständiges Backup": "First start – full backup",
    "Nicht unterstützt": "Not supported",
    "Registry-Datei": "Registry file",
    "Speichern": "Save",
    "Icon (.ico/.exe):": "Icon (.ico/.exe):",
    "Programmpfad:": "Program path:",
    "Icon (optional):": "Icon (optional):",
    "Übergeordnetes Menü:": "Parent menu:",
    "Der Name darf nicht leer sein.": "The name must not be empty.",
    "Es existiert noch kein Menü. Bitte zuerst ein Menü anlegen.":
        "There is no menu yet. Please create a menu first.",
    "Soll vor der ersten Verwendung ein vollständiges Backup der beiden Registry-Bereiche erstellt werden?\n\nJA = beide Bereiche separat sichern\nNEIN = kein Erststart-Backup erstellen":
        "Create a full backup of both registry areas before first use?\n\nYES = back up both areas separately\nNO = no first-start backup",
    "Dieses Programm greift auf die Windows-Registry zu und funktioniert nur unter Windows.":
        "This program accesses the Windows registry and only works on Windows.",
    "reg.exe konnte den Schlüssel nicht exportieren.":
        "reg.exe could not export the key.",
    "Pfad konnte nicht erstellt werden:\n": "Could not create path:\n",
    "Der Eintrag '{name}' ist ein fester Windows-Eintrag.\n\nVor dem Löschen wird automatisch ein Backup (.reg) unter Dokumente angelegt (Dateiname: Schlüsselname + Datum/Uhrzeit). Durch einfaches Ausführen dieser Datei lässt sich der Eintrag wiederherstellen.\n\nEintrag wirklich löschen?":
        "The entry '{name}' is a fixed Windows entry.\n\nBefore deletion, a backup (.reg) is automatically created in the Documents folder (file name: key name + date/time). Simply running that file restores the entry.\n\nReally delete this entry?",
    "Eintrag '{name}' einschließlich aller Untereinträge vollständig löschen?":
        "Delete entry '{name}' including all sub-entries completely?",
    "Der Eintrag '{name}' konnte nicht vollständig gelöscht werden (Schreibschutz/Rechte).":
        "The entry '{name}' could not be deleted completely (write protection/permissions).",
    "Windows-Eintrag gelöscht.\n\nBackup wurde angelegt:\n\n{file}\n\nAusführen dieser Datei stellt den Eintrag wieder her.":
        "Windows entry deleted.\n\nBackup saved at:\n\n{file}\n\nRunning this file restores the entry.",
    "Shutdown-Menü im Bereich {area} vorbereitet.\n\n":
        "Shutdown menu prepared in area {area}.\n\n",
    # Präfix-Übersetzungen (dynamische Meldungen, längster Treffer gewinnt)
}

PREFIX_TRANSLATIONS = [
    ("Der Eintrag '", "The entry '"),
    ("Eintrag '", "Entry '"),
    ("Eintrag wirklich löschen?", "Really delete this entry?"),
    ("Löschen fehlgeschlagen:\n", "Deleting failed:\n"),
    ("Rückgängig fehlgeschlagen:\n", "Undo failed:\n"),
    ("Verschieben fehlgeschlagen:\n", "Moving failed:\n"),
    ("Backup fehlgeschlagen, Löschung abgebrochen:\n",
     "Backup failed, deletion cancelled:\n"),
    ("Der Eintrag konnte nicht vollständig gelöscht werden",
     "The entry could not be deleted completely"),
    ("Shutdown-Menü konnte nicht angelegt werden:\n",
     "Shutdown menu could not be created:\n"),
    ("Shutdown-Menü im Bereich ", "Shutdown menu prepared in area "),
    ("Angelegt: ", "Created: "),
    ("Aktualisiert: ", "Updated: "),
    ("Fehler beim Laden:", "Error while loading:"),
    ("Backup wurde erstellt:\n\n", "Backup created:\n\n"),
    ("Backup konnte nicht erstellt werden:\n\n",
     "Backup could not be created:\n\n"),
    ("Backup konnte nicht vollständig erstellt werden:\n\n",
     "Backup could not be created completely:\n\n"),
    ("Beide Registry-Bereiche wurden separat gesichert:\n\n",
     "Both registry areas were saved separately:\n\n"),
    ("Gemeinsames Backup wurde erstellt:\n\n", "Combined backup created:\n\n"),
    ("Aktualisieren fehlgeschlagen:\n", "Refreshing failed:\n"),
    ("Anlegen fehlgeschlagen:\n", "Creating failed:\n"),
]


def tr(text):
    """Liefert den Text in der aktuellen Sprache (Default: Deutsch)."""
    if APP_LANG != "en":
        return text
    if text in TRANSLATIONS:
        return TRANSLATIONS[text]
    best_de, best_en = "", None
    for de, en in PREFIX_TRANSLATIONS:
        if text.startswith(de) and len(de) > len(best_de):
            best_de, best_en = de, en
    if best_en is not None:
        return best_en + text[len(best_de):]
    return text


# Positions-Werte: intern bleibt "Mitte"/"Top"/"Bottom" (Registry),
# nur die Anzeige wird übersetzt.
POSITION_INTERNAL_VALUES = ("Mitte", "Top", "Bottom")


def position_display_values():
    return [tr(v) for v in POSITION_INTERNAL_VALUES]


def position_from_display(text):
    for internal in POSITION_INTERNAL_VALUES:
        if tr(internal) == text:
            return internal
    return text


def _msg_box(kind, title, message, *args, **kwargs):

    target = getattr(messagebox, kind)

    return target(
        tr(title),
        tr(message),
        *args,
        **kwargs
    )


def msg_info(title, message, *args, **kwargs):
    return _msg_box("showinfo", title, message, *args, **kwargs)


def msg_warn(title, message, *args, **kwargs):
    return _msg_box("showwarning", title, message, *args, **kwargs)


def msg_error(title, message, *args, **kwargs):
    return _msg_box("showerror", title, message, *args, **kwargs)


def ask_yes_no(title, message, *args, **kwargs):
    return _msg_box("askyesno", title, message, *args, **kwargs)


# Auto-Scroll beim Drag & Drop (v3.8): Randzone
# in Pixeln und Scroll-Intervall in ms.
DND_SCROLL_EDGE = 28
DND_SCROLL_MS = 60


try:
    import winreg
except ImportError:
    winreg = None


# ----------------------------------------------------------------------
# Registry
# ----------------------------------------------------------------------

HIVE = winreg.HKEY_CLASSES_ROOT if winreg else None

BASE_PATH_DIRECTORY = r"Directory\Background\Shell"
BASE_PATH_DESKTOP = r"DesktopBackground\Shell"

BASE_PATH = BASE_PATH_DIRECTORY

# Eingebettete Toolbar-Icons (PNG, 16×16) im
# Projektordner `icons\` — feste Zuordnung
# Button-Name → Datei. Die Toolbar-Buttons
# verwenden AUSSCHLIESSLICH diese originalen,
# selbst gezeichneten PNGs (keine Extraktion
# aus Windows-DLLs → keine Lizenzprobleme,
# identisch auf allen Systemen und in allen
# Themes dank Alpha-Kanal). Erzeugt/anpassbar
# mit make_icons.py.
ICON_DIR = (
    os.path.join(sys._MEIPASS, "icons")
    if getattr(sys, "_MEIPASS", None)
    else os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "icons"
    )
)

TOOLBAR_ICON_FILES = {
    "new_entry": "new_entry.png",
    "new_menu": "new_menu.png",
    "new_menu_item": "new_menu_item.png",
    "edit": "edit.png",
    "delete": "delete.png",
    "refresh": "refresh.png",
    "undo": "undo.png",
    "backup": "backup.png",
    "move_up": "move_up.png",      # bereits 180° gedreht gespeichert
    "move_down": "move_down.png",
    "shutdown_menu": "shutdown_menu.png",
    "help": "help.png"
}

# Hilfe-Text für den Hilfe-Dialog (v3.2).
# Liste von (Stil, Text); "heading" = fett.
HELP_TEXT = [
    ("heading",
     "WAS MACHT DIESES TOOL?"),
    ("normal",
     "Menu-Edit bearbeitet das Desktop-Kontextmenü von Windows direkt über "
     "die Registry — ohne manuelles Regedit-Basteln. Alle Änderungen sind "
     "sofort wirksam (der Explorer wird auf Wunsch informiert) und über "
     "Rückgängig sowie .reg-Backups sicherbar.\n\n"),
    ("heading", "BEREICHE"),
    ("normal",
     "Rechts oben schaltet der Button „Bereich: …“ zwischen den zwei "
     "verwalteten Registry-Bereichen um:\n"
     "• Obers\\Unteres Menü = HKCR\\Directory\\Background\\Shell "
     "(Rechtsklick auf den Desktop-Hintergrund)\n"
     "• DesktopBackground = HKCR\\DesktopBackground\\Shell\n"
     "Der zuletzt gewählte Bereich wird beim Beenden gespeichert.\n\n"),
    ("heading", "EINTRÄGE UND MENÜS ERSTELLEN"),
    ("normal",
     "• Neuer Eintrag (Dokument-Icon): ein direkter Punkt im Kontextmenü "
     "mit Anzeigename, Befehl, Icon und Position (Top/Mitte/Bottom).\n"
     "• Neues Menü (Textdatei-Icon): ein Untermenü (Kaskade), in das "
     "weitere Einträge/Untermenüs gehören.\n"
     "• Eintrag in Menü (Ordner-Icon): wie „Neuer Eintrag“, aber direkt "
     "in ein bestehendes Menü einsortiert.\n"
     "„Mitte“ bedeutet: kein Position-Wert in der Registry → der Eintrag "
     "erscheint im mittleren Menübereich.\n\n"),
    ("heading", "BEARBEITEN UND LÖSCHEN"),
    ("normal",
     "• Bearbeiten (Stift-Icon) oder Doppelklick auf einen Eintrag: "
     "Anzeigename, Befehl, Icon und Position ändern.\n"
     "• Löschen (rotes X): entfernt den markierten Eintrag inkl. "
     "Untereinträgen. Bei festen Windows-Einträgen (cmd, PowerShell, …) "
     "erscheint vor dem Löschen ein Bestätigungsdialog und es wird "
     "automatisch ein Backup (.reg) im Dokumente-Ordner angelegt — "
     "durch Ausführen dieser Datei ist der Eintrag wiederherstellbar.\n"
     "• Aktualisieren (Kreis-Pfeile): liest die Ansicht neu aus der "
     "Registry.\n\n"),
    ("heading", "VERSCHIEBEN"),
    ("normal",
     "• Pfeil-Buttons (nach oben/unten) oder Drag & Drop im Baum: "
     "Zeile greifen und ziehen. Ein sichtbarer Balken zwischen zwei "
     "Zeilen zeigt genau, wo der Eintrag landet (v3.7). Wird der "
     "Zeiger nahe an den oberen oder unteren Rand gezogen, scrollt "
     "die Liste automatisch weiter, bis Anfang/Ende erreicht ist "
     "(v3.8).\n"
     "• Mehrere Einträge gleichzeitig: per Strg-/Shift-Klick markieren — "
     "Pfeil-Buttons und Drag & Drop bewegen den ganzen Block (Reihenfolge "
     "bleibt erhalten).\n"
     "• Die Drop-Position steuern: obere Hälfte einer Zeile = davor "
     "einsortieren, untere Hälfte = danach; untere Hälfte eines MENÜS = "
     "in das Menü hinein (dann wird die Menüzeile hervorgehoben). Drop "
     "auf freie Fläche = oberste Ebene. Der anvisierte Eintrag selbst "
     "wird dabei NIE verschoben.\n"
     "• An schreibgeschützten Windows-Einträgen (cmd, PowerShell, …) "
     "wird automatisch vorbeisortiert, ohne sie anzufassen. Hinweis: "
     "Die Reihenfolge im Kontextmenü ergibt sich aus der alphabetischen "
     "Reihenfolge der internen Schlüsselnamen — beim Vorbeisortieren "
     "kann sich deshalb der Schlüsselname eines eigenen Eintrags ändern "
     "(der sichtbare Name bleibt erhalten).\n\n"),
    ("heading", "RÜCKGÄNGIG"),
    ("normal",
     "Der blaue Rückbiege-Pfeil macht die letzten 10 Änderungen einzeln "
     "rückgängig (Anlegen, Löschen, Bearbeiten, Verschieben, Tausch). "
     "Der Undo-Speicher liegt nur im Arbeitsspeicher — nach einem "
     "Neustart des Tools ist er leer.\n\n"),
    ("heading", "BACKUP"),
    ("normal",
     "Der Backup-Button (Ordner mit Pfeil) öffnet ein Menü:\n"
     "• Beide Bereiche einzeln sichern\n"
     "• Beide Bereiche gemeinsam sichern\n"
     "• Aktuellen Bereich sichern\n"
     "• Backup-Einstellungen (Standard-Speicherpfad festlegen)\n"
     "Gespeichert wird als .reg-Datei (UTF-16), ausführbar zur "
     "Wiederherstellung. Der Backup-Pfad wird dauerhaft gespeichert.\n\n"),
    ("heading", "SHUTDOWN-MENÜ"),
    ("normal",
     "Der rote Power-Button legt per EINEM Klick das Menü „Shutdown "
     "Menü“ mit 1.Neustart / 2.Herunterfahren / 3.Abmelden im aktuell "
     "gewählten Bereich an — immer im unteren Menübereich. Das Anlegen "
     "ist wiederholbar (idempotent): fehlende Teile werden ergänzt, "
     "Ihre eigenen Befehle werden NIE überschrieben.\n\n"),
    ("heading", "RECHTSKLICK"),
    ("normal",
     "Ein Rechtsklick auf das Hauptfenster oder den Baum öffnet ein "
     "Kontextmenü mit allen Button-Funktionen (ohne die "
     "Verschiebe-Pfeile).\n\n"),
    ("heading", "DESIGN"),
    ("normal",
     "Der Button „Design: <Name>“ (neben „Bereich“) schaltet durch drei "
     "Farbthemen: Creamy → DarkGreen → BlueMoon. Das gewählte Design wird "
     "gespeichert und beim Start wiederhergestellt; auch der "
     "Hilfe-Dialog folgt dem aktiven Design.\n\n"),
    ("heading", "SONSTIGES"),
    ("normal",
     "• Statusleiste unten: Hinweis, ob das Tool mit Administrator-"
     "Rechten läuft (ohne Admin sind Schreibrechte eingeschränkt).\n"
     "• Einstellungen: %USERPROFILE%\\.config\\menu-editor\\settings.ini "
     "(Backup-Pfad, Design, Bereich, Fenstergröße).\n"
     "• Fenstertitel zeigt die Version; Größe/Fenster-Icon siehe "
     "Titelleiste.\n"),
]

# Englische Hilfe (v3.5) — gleiche Struktur wie HELP_TEXT.
HELP_TEXT_EN = [
    ("heading", "WHAT DOES THIS TOOL DO?"),
    ("normal",
     "Menu-Edit edits the Windows desktop context menu directly via the "
     "registry — no manual Regedit work. Changes take effect immediately "
     "and can be secured via Undo and .reg backups.\n\n"),
    ("heading", "AREAS"),
    ("normal",
     "The “Area: …” button (top right) switches between the two managed "
     "registry areas:\n"
     "• Upper\\Lower Menu = HKCR\\Directory\\Background\\Shell "
     "(right-click on the desktop background)\n"
     "• DesktopBackground = HKCR\\DesktopBackground\\Shell\n"
     "The last selected area is saved on exit.\n\n"),
    ("heading", "CREATING ENTRIES AND MENUS"),
    ("normal",
     "• New entry (document icon): a direct item in the context menu with "
     "display name, command, icon and position (Top/Center/Bottom).\n"
     "• New menu (text file icon): a submenu (cascade) for further "
     "entries/submenus.\n"
     "• Create entry inside menu (folder icon): like “New entry”, but "
     "placed directly into an existing menu.\n"
     "“Center” means: no Position value in the registry → the entry "
     "appears in the middle section of the menu. Center is the default "
     "for all create dialogs.\n\n"),
    ("heading", "EDITING AND DELETING"),
    ("normal",
     "• Edit (pencil icon) or double-click an entry: change display name, "
     "command, icon and position.\n"
     "• Delete (red X): removes the selected entry including "
     "sub-entries. For fixed Windows entries (cmd, PowerShell, …) a "
     "confirmation dialog appears first and a backup (.reg) is "
     "automatically created in the Documents folder — running that file "
     "restores the entry.\n"
     "• Refresh (circular arrows): re-reads the view from the registry.\n\n"),
    ("heading", "MOVING"),
    ("normal",
     "• Arrow buttons (up/down) or drag & drop in the tree: grab a row "
     "and drag it. A visible bar between two rows shows exactly where "
     "the entry will land (v3.7). Moving the pointer near the top or "
     "bottom edge auto-scrolls the list until its start/end is reached "
     "(v3.8).\n"
     "• Multiple entries at once: mark them with Ctrl/Shift — arrow "
     "buttons and drag & drop move the whole block (order preserved).\n"
     "• Control the drop position: upper half of a row = insert before, "
     "lower half = insert after; lower half of a MENU = move into the "
     "menu (the menu row is then highlighted). Drop on empty space = top "
     "level. The targeted entry itself is NEVER moved.\n"
     "• Read-only Windows entries (cmd, PowerShell, …) are automatically "
     "sorted around without touching them. Note: the context menu order "
     "results from the alphabetical order of the internal key names — "
     "when sorting around, an entry's key name may change (its visible "
     "name is preserved).\n\n"),
    ("heading", "UNDO"),
    ("normal",
     "The blue arrow button undoes the last 10 changes one by one "
     "(create, delete, edit, move, swap). The undo stack is memory-only "
     "— it is empty after restarting the tool.\n\n"),
    ("heading", "BACKUP"),
    ("normal",
     "The backup button (folder with arrow) opens a menu:\n"
     "• Back up both areas separately\n"
     "• Back up both areas combined\n"
     "• Back up current area\n"
     "• Backup settings (set the default save path)\n"
     "Saved as .reg files (UTF-16), executable for restoration. The "
     "backup path is stored permanently.\n\n"),
    ("heading", "SHUTDOWN MENU"),
    ("normal",
     "The red power button creates the “Shutdown Menü” with 1.Restart / "
     "2.Shutdown / 3.Log off in the currently selected area with ONE "
     "click — always in the lower menu section. Creating is repeatable "
     "(idempotent): missing parts are added, YOUR own commands are NEVER "
     "overwritten.\n\n"),
    ("heading", "RIGHT CLICK"),
    ("normal",
     "Right-clicking the main window or the tree opens a context menu "
     "with all button functions (without the move arrows).\n\n"),
    ("heading", "THEME"),
    ("normal",
     "The “Theme: <name>” button (next to “Area”) cycles through three "
     "color themes: Creamy → DarkGreen → BlueMoon. The selected theme is "
     "saved and restored on start; the help dialog follows the active "
     "theme too.\n\n"),
    ("heading", "LANGUAGE"),
    ("normal",
     "The “Language” button (next to “Help”) switches between German and "
     "English. The selection is saved; default is German.\n\n"),
    ("heading", "MISC"),
    ("normal",
     "• Status bar at the bottom: shows whether the tool runs with "
     "administrator rights (without admin, write access may be "
     "limited).\n"
     "• Settings: %USERPROFILE%\\.config\\menu-editor\\settings.ini "
     "(backup path, theme, area, language, window size).\n"
     "• The window title shows the version; size/window icon see title "
     "bar.\n"),
]

# Vorlage für das Shutdown-Menü
# (Ein-Klick-Anlegen im aktuellen Bereich).
# Icon-Referenzen mit %SystemRoot% statt
# fester Platte; sichtbare Namen = Schlüssel-
# namen der Untereinträge.
SHUTDOWN_MENU_KEY = "Shutdown"
SHUTDOWN_MENU_DISPLAY = "Shutdown Menü"
SHUTDOWN_MENU_ICON = (
    r"%SystemRoot%\System32\shell32.dll,215"
)
SHUTDOWN_ENTRIES = [
    (
        "1.Neustart",
        "shutdown.exe /r /t 0",
        r"%SystemRoot%\System32\imageres.dll,-1401"
    ),
    (
        "2.Herunterfahren",
        "shutdown.exe /s /t 0",
        SHUTDOWN_MENU_ICON
    ),
    (
        "3.Abmelden",
        "shutdown.exe /l",
        r"%SystemRoot%\System32\imageres.dll,-1029"
    )
]

# Feste Windows-Einträge (Vergleich
# kleingeschrieben). Vor dem Löschen dieser
# Einträge wird automatisch ein Backup im
# Dokumente-Ordner angelegt; verschieben
# kann man sie frei.
PROTECTED_SHELL_KEYS = {
    "cmd",
    "powershell",
    "powershelladmin",
    "openinterminal",
    "runas"
}


def is_windows_key(path):

    # Prüft, ob ein Schlüssel (auch als
    # Untereintrag, z. B. cmd\runas) zu einem
    # festen Windows-Eintrag gehört.
    return any(
        segment.lower() in PROTECTED_SHELL_KEYS
        for segment in path.split("\\")
    )


def sweep_tmp_keys():

    # Entfernt beim Start überbliebene
    # Arbeits-Schlüssel ("__tmp__") aus beiden
    # Shell-Bereichen — Überreste früherer
    # fehlgeschlagener Tausch-Vorgänge.
    removed = 0

    for base in (
        BASE_PATH_DIRECTORY,
        BASE_PATH_DESKTOP
    ):

        for name in enum_subkeys(base):

            if "__tmp__" in name:

                if delete_key_recursive(
                    HIVE,
                    f"{base}\\{name}"
                ):

                    removed += 1

    return removed


# ----------------------------------------------------------------------
# Konfiguration
# ----------------------------------------------------------------------

CONFIG_DIR = os.path.join(
    os.path.expanduser("~"),
    ".config",
    "menu-editor"
)

CONFIG_FILE = os.path.join(
    CONFIG_DIR,
    "settings.ini"
)


def load_settings():

    config = configparser.ConfigParser()

    settings = {
        "backup_path": "",
        "first_run_backup_done": "0",
        "theme": "DarkGreen",
        "area": "directory",
        "window_geometry": "",
        "lang": "de"
    }

    try:

        if os.path.exists(CONFIG_FILE):

            config.read(
                CONFIG_FILE,
                encoding="utf-8"
            )

            if config.has_section("Settings"):

                settings["backup_path"] = config.get(
                    "Settings",
                    "backup_path",
                    fallback=""
                )

                settings["first_run_backup_done"] = config.get(
                    "Settings",
                    "first_run_backup_done",
                    fallback="0"
                )

                settings["theme"] = config.get(
                    "Settings",
                    "theme",
                    fallback="DarkGreen"
                )

                # Alte Bezeichnung „Dunkel" auf den
                # neuen Namen DarkGreen abbilden
                # (gleiche Palette, nahtlos).
                if settings["theme"] == "Dunkel":
                    settings["theme"] = "DarkGreen"

                settings["area"] = config.get(
                    "Settings",
                    "area",
                    fallback="directory"
                )

                settings["window_geometry"] = config.get(
                    "Settings",
                    "window_geometry",
                    fallback=""
                )

                settings["lang"] = config.get(
                    "Settings",
                    "lang",
                    fallback="de"
                )

    except Exception:
        pass

    return settings


def save_settings(settings):

    try:

        os.makedirs(
            CONFIG_DIR,
            exist_ok=True
        )

        config = configparser.ConfigParser()

        config["Settings"] = {
            "backup_path": settings.get(
                "backup_path",
                ""
            ),
            "first_run_backup_done": settings.get(
                "first_run_backup_done",
                "0"
            ),
            "theme": settings.get(
                "theme",
                "DarkGreen"
            ),
            "area": settings.get(
                "area",
                "directory"
            ),
            "window_geometry": settings.get(
                "window_geometry",
                ""
            ),
            "lang": settings.get(
                "lang",
                "de"
            )
        }

        with open(
            CONFIG_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            config.write(file)

    except Exception:
        pass


SETTINGS = load_settings()

# Sprache aus der settings.ini (vor dem
# ersten UI-Aufbau; Default Deutsch).
if SETTINGS.get("lang") in ("de", "en"):

    APP_LANG = SETTINGS["lang"]


# ----------------------------------------------------------------------
# Shell / Administrator
# ----------------------------------------------------------------------

def is_admin():

    try:

        return bool(
            ctypes.windll.shell32.IsUserAnAdmin()
        )

    except Exception:

        return False


def notify_shell():

    try:

        SHCNE_ASSOCCHANGED = 0x08000000
        SHCNF_IDLIST = 0x0000

        ctypes.windll.shell32.SHChangeNotify(
            SHCNE_ASSOCCHANGED,
            SHCNF_IDLIST,
            0,
            0
        )

    except Exception:
        pass


# ----------------------------------------------------------------------
# Registry Hilfsfunktionen
# ----------------------------------------------------------------------

def format_command(command):

    # Befehl wird exakt wie eingegeben
    # gespeichert (nur Whitespace entfernt).
    # KEINE automatischen Anführungszeichen:
    # 'shutdown.exe /r /t 0' als Ganzes in
    # "..." zu setzen macht den Befehl
    # unausführbar (Windows sucht dann ein
    # Programm mit diesem Gesamtnamen).
    # Wer den Programmpfad quoted (z. B.
    # "C:\Program Files\...\app.exe" /x),
    # setzt die Quotes selbst.

    return (command or "").strip()


def create_app_entry(
    name,
    icon,
    command,
    parent_shell_path=None,
    position=None
):

    base_path = (
        parent_shell_path
        if parent_shell_path
        else BASE_PATH
    )

    entry_path = f"{base_path}\\{name}"

    with winreg.CreateKeyEx(
        HIVE,
        entry_path,
        0,
        winreg.KEY_READ | winreg.KEY_WRITE
    ) as entry_key:

        winreg.SetValueEx(
            entry_key,
            None,
            0,
            winreg.REG_SZ,
            ""
        )

        if icon:

            winreg.SetValueEx(
                entry_key,
                "Icon",
                0,
                winreg.REG_SZ,
                icon
            )

        if (
            not parent_shell_path
            and BASE_PATH.lower()
            == BASE_PATH_DESKTOP.lower()
            and position in ("Top", "Bottom")
        ):

            winreg.SetValueEx(
                entry_key,
                "Position",
                0,
                winreg.REG_SZ,
                position
            )

        # "Mitte": kein Position-Wert anlegen.

    command_path = f"{entry_path}\\command"

    with winreg.CreateKeyEx(
        HIVE,
        command_path,
        0,
        winreg.KEY_READ | winreg.KEY_WRITE
    ) as command_key:

        winreg.SetValueEx(
            command_key,
            None,
            0,
            winreg.REG_SZ,
            format_command(command)
        )

    return entry_path


def create_menu_entry(
    name,
    icon,
    position="Mitte",
    parent_shell_path=None
):

    base_path = (
        parent_shell_path
        if parent_shell_path
        else BASE_PATH
    )

    entry_path = f"{base_path}\\{name}"

    if position not in ("Top", "Bottom"):

        position = "Mitte"

    with winreg.CreateKeyEx(
        HIVE,
        entry_path,
        0,
        winreg.KEY_READ | winreg.KEY_WRITE
    ) as menu_key:

        winreg.SetValueEx(
            menu_key,
            None,
            0,
            winreg.REG_SZ,
            ""
        )

        if icon:

            winreg.SetValueEx(
                menu_key,
                "Icon",
                0,
                winreg.REG_SZ,
                icon
            )

        winreg.SetValueEx(
            menu_key,
            "SubCommands",
            0,
            winreg.REG_SZ,
            ""
        )

        if position in ("Top", "Bottom"):

            winreg.SetValueEx(
                menu_key,
                "Position",
                0,
                winreg.REG_SZ,
                position
            )

        # "Mitte": kein Position-Wert anlegen.

    shell_path = f"{entry_path}\\shell"

    with winreg.CreateKeyEx(
        HIVE,
        shell_path,
        0,
        winreg.KEY_READ | winreg.KEY_WRITE
    ):
        pass

    create_app_entry(
        "leer",
        "",
        "",
        shell_path
    )

    return shell_path


def update_entry_values(
    full_path,
    icon,
    command=None,
    position=None
):

    with winreg.CreateKeyEx(
        HIVE,
        full_path,
        0,
        winreg.KEY_READ | winreg.KEY_WRITE
    ) as key:

        winreg.SetValueEx(
            key,
            None,
            0,
            winreg.REG_SZ,
            ""
        )

        if icon:

            winreg.SetValueEx(
                key,
                "Icon",
                0,
                winreg.REG_SZ,
                icon
            )

        else:

            try:

                winreg.DeleteValue(
                    key,
                    "Icon"
                )

            except FileNotFoundError:
                pass

        if position in ("Top", "Bottom"):

            winreg.SetValueEx(
                key,
                "Position",
                0,
                winreg.REG_SZ,
                position
            )

        elif position == "Mitte":

            # Mitte = kein Position-Wert.
            try:

                winreg.DeleteValue(
                    key,
                    "Position"
                )

            except FileNotFoundError:
                pass

        if command is not None:

            command_path = (
                f"{full_path}\\command"
            )

            with winreg.CreateKeyEx(
                HIVE,
                command_path,
                0,
                winreg.KEY_READ | winreg.KEY_WRITE
            ) as command_key:

                winreg.SetValueEx(
                    command_key,
                    None,
                    0,
                    winreg.REG_SZ,
                    format_command(command)
                )


def read_position(path):

    try:

        with winreg.OpenKey(
            HIVE,
            path
        ) as key:

            try:

                position = winreg.QueryValueEx(
                    key,
                    "Position"
                )[0]

                if str(position).lower() == "top":
                    return "Top"

                if str(position).lower() == "bottom":
                    return "Bottom"

            except FileNotFoundError:
                pass

    except FileNotFoundError:
        pass

    # Ohne Position-Wert bleibt der Eintrag
    # im mittleren Bereich des Menüs.
    return "Mitte"


def copy_registry_key(
    src,
    dst
):

    # Kein Mischen in vorhandene Schlüssel:
    # Das Ziel muss frisch sein, sonst bleiben
    # beim Zurücknehmen fremde Reste liegen.
    if key_exists(dst):

        raise RuntimeError(
            f"Zielschlüssel existiert bereits: {dst}"
        )

    with winreg.CreateKeyEx(
        HIVE,
        dst,
        0,
        winreg.KEY_READ | winreg.KEY_WRITE
    ) as dst_key:

        with winreg.OpenKey(
            HIVE,
            src,
            0,
            winreg.KEY_READ
        ) as src_key:

            index = 0

            while True:

                try:

                    name, data, value_type = (
                        winreg.EnumValue(
                            src_key,
                            index
                        )
                    )

                    winreg.SetValueEx(
                        dst_key,
                        name,
                        0,
                        value_type,
                        data
                    )

                    index += 1

                except OSError:

                    break

            index = 0

            while True:

                try:

                    child = winreg.EnumKey(
                        src_key,
                        index
                    )

                    copy_registry_key(
                        f"{src}\\{child}",
                        f"{dst}\\{child}"
                    )

                    index += 1

                except OSError:

                    break


def rename_key(
    old_path,
    new_name
):

    parent_path, old_name = old_path.rsplit(
        "\\",
        1
    )

    new_path = f"{parent_path}\\{new_name}"

    if old_path.lower() == new_path.lower():
        return old_path

    if key_exists(new_path):

        raise RuntimeError(
            f"Der Name '{new_name}' existiert an "
            "diesem Ort bereits."
        )

    if not can_delete_key(old_path):

        raise RuntimeError(
            f"Der Schlüssel '{old_path}' ist "
            "schreibgeschützt und kann nicht "
            "verschoben oder umbenannt werden."
        )

    copy_registry_key(
        old_path,
        new_path
    )

    if not delete_key_recursive(
        HIVE,
        old_path
    ):

        # Quelle konnte nicht gelöscht werden
        # (Schreibschutz/Rechte): Kopie wieder
        # entfernen, damit kein Müll übrig bleibt.
        delete_key_recursive(
            HIVE,
            new_path
        )

        raise RuntimeError(
            f"Der Schlüssel '{old_path}' konnte an "
            "seinem alten Ort nicht gelöscht werden "
            "(Schreibschutz/Rechte). Die Änderung "
            "wurde zurückgenommen."
        )

    return new_path


def key_exists(path):

    try:

        with winreg.OpenKey(
            HIVE,
            path,
            0,
            winreg.KEY_READ
        ):
            pass

        return True

    except FileNotFoundError:

        return False

    except OSError:

        return False


DELETE_RIGHT = getattr(
    winreg,
    "DELETE",
    0x00010000
)


def can_delete_key(path):

    # Prüft rekursiv ohne Änderung, ob der
    # Schlüssel und alle Unterschlüssel
    # gelöscht werden dürften (DELETE-Recht).
    # Verhindert, dass ein fehlgeschlagener
    # Tausch/Versuch den Schlüssel "ausweidet".
    access = (
        DELETE_RIGHT
        | winreg.KEY_ENUMERATE_SUB_KEYS
    )

    try:

        key = winreg.OpenKey(
            HIVE,
            path,
            0,
            access
        )

    except OSError:

        return False

    children = []

    try:

        index = 0

        while True:

            try:

                children.append(
                    winreg.EnumKey(key, index)
                )

                index += 1

            except OSError:

                break

    finally:

        key.Close()

    return all(
        can_delete_key(f"{path}\\{child}")
        for child in children
    )


def ensure_display_name(path):

    # Sichert den angezeigten Namen eines
    # Schlüssels als (Standard)-Wert. Nötig
    # vor Namens-Tausch/ Verschieben, da sonst
    # die Anzeige (Fallback = Schlüsselname)
    # sich ändern würde.
    try:

        with winreg.OpenKey(
            HIVE,
            path,
            0,
            winreg.KEY_READ | winreg.KEY_WRITE
        ) as key:

            try:

                display = winreg.QueryValueEx(
                    key,
                    None
                )[0]

            except FileNotFoundError:

                display = ""

            if display:
                return

            try:

                muiverb = winreg.QueryValueEx(
                    key,
                    "MUIVerb"
                )[0]

            except FileNotFoundError:

                muiverb = ""

            if muiverb:
                return

            name = path.rsplit(
                "\\",
                1
            )[-1]

            winreg.SetValueEx(
                key,
                None,
                0,
                winreg.REG_SZ,
                name
            )

    except OSError:

        pass


def is_self_or_descendant(
    ancestor,
    path
):

    a = ancestor.lower()
    p = path.lower()

    return (
        p == a
        or p.startswith(a + "\\")
    )


def move_key(
    old_path,
    new_parent_path
):

    # Verschiebt einen Schlüssel (inkl.
    # Unterstruktur) unter einen anderen
    # Elternschlüssel. Der Name bleibt
    # erhalten; ist er am Ziel vorhanden,
    # wird ein Suffix _2, _3, ... angehängt.
    old_name = old_path.rsplit(
        "\\",
        1
    )[-1]

    new_name = old_name
    counter = 2

    while key_exists(
        f"{new_parent_path}\\{new_name}"
    ):

        if new_name == old_name:

            # Vor dem Umbenennen den
            # Anzeigenamen sichern.
            ensure_display_name(old_path)

        new_name = f"{old_name}_{counter}"
        counter += 1

    new_path = (
        f"{new_parent_path}\\{new_name}"
    )

    if old_path.lower() == new_path.lower():
        return old_path

    if new_name != old_name:

        ensure_display_name(old_path)

    if not can_delete_key(old_path):

        raise RuntimeError(
            f"Der Schlüssel '{old_path}' ist "
            "schreibgeschützt und kann nicht "
            "verschoben werden."
        )

    copy_registry_key(
        old_path,
        new_path
    )

    if not delete_key_recursive(
        HIVE,
        old_path
    ):

        # Quelle konnte nicht gelöscht werden:
        # Kopie entfernen, kein Müll übrig lassen.
        delete_key_recursive(
            HIVE,
            new_path
        )

        raise RuntimeError(
            f"Der Schlüssel '{old_path}' konnte an "
            "seinem alten Ort nicht gelöscht werden "
            "(Schreibschutz/Rechte). Die Änderung "
            "wurde zurückgenommen."
        )

    return new_path


def sorting_name_candidates(fixed_name, direction):

    # Liefert Kandidaten für Schlüsselnamen,
    # die (alphabetisch, case-insensitiv wie
    # die Registry-Aufzählung) direkt vor
    # (direction -1) bzw. direkt hinter
    # (direction +1) fixed_name einsortieren.
    # Der sichtbare Name ändert sich nicht,
    # da er über den (Standard)-Wert kommt.
    # Die Groß-/Kleinschreibung des
    # Zielnamens bleibt erhalten (die
    # Registry sortiert case-insensitiv).
    fixed = fixed_name

    if direction < 0:

        # Präfixe: "cm" liegt direkt vor "cmd"
        # (kürzeres Präfix sortiert zuerst).
        for i in range(len(fixed) - 1, 0, -1):

            yield fixed[:i]

        # Letztes Zeichen dekrementieren:
        # "cmczzzzzzz" liegt zwischen Namen wie
        # "cm0" und "cmd".
        for i in range(len(fixed) - 1, 0, -1):

            c = fixed[i]

            if c > "a":

                yield fixed[:i] + chr(ord(c) - 1) + "z" * 8

        # Letzter Ausweg: "!" sortiert vor
        # Buchstaben und Ziffern.
        yield "!" + fixed

    else:

        for suffix in ("!", "!!", "___", "____", "_____"):

            yield fixed + suffix

        yield fixed + "z" * 8


def reorder_key_past_neighbor(
    parent_path,
    movable_name,
    fixed_name,
    direction
):

    # Sortiert movable_name an fixed_name
    # vorbei, ohne fixed_name (z. B. einen
    # schreibgeschützten Windows-Eintrag wie
    # cmd) anzufassen: Nur der bewegliche
    # Schlüssel wird auf einen Namen getauft,
    # der alphabetisch direkt vor bzw. hinter
    # dem Nachbarn liegt. Liefert
    # (neuer_pfad, snapshot) für Undo.
    movable_path = f"{parent_path}\\{movable_name}"

    if not can_delete_key(movable_path):

        raise RuntimeError(
            f"Der Schlüssel '{movable_path}' ist "
            "schreibgeschützt und kann nicht "
            "verschoben oder umbenannt werden."
        )

    snapshot = capture_subtree(movable_path)

    ensure_display_name(movable_path)

    for candidate in sorting_name_candidates(
        fixed_name,
        direction
    ):

        if candidate.lower() == movable_name.lower():
            continue

        new_path = f"{parent_path}\\{candidate}"

        if key_exists(new_path):
            continue

        try:

            rename_key(movable_path, candidate)

        except RuntimeError:

            # Kollision o. ä.: nächsten
            # Kandidaten probieren.
            continue

        lowered = [
            n.lower()
            for n in enum_subkeys(parent_path)
        ]

        if (
            candidate.lower() not in lowered
            or fixed_name.lower() not in lowered
        ):

            rename_key(new_path, movable_name)
            continue

        i_new = lowered.index(candidate.lower())
        i_fixed = lowered.index(fixed_name.lower())

        adjacent = (
            i_new == i_fixed - 1
            if direction < 0
            else i_new == i_fixed + 1
        )

        if adjacent:

            return new_path, snapshot

        # Nicht direkt neben dem Nachbarn
        # gelandet: zurücktaufen und den
        # nächsten Kandidaten testen.
        rename_key(new_path, movable_name)

    raise RuntimeError(
        "Konnte keinen freien Schlüsselnamen "
        "finden, um an dem geschützten "
        f"Windows-Eintrag '{fixed_name}' vorbei "
        "zu sortieren."
    )


def capture_subtree(path):

    # Liest einen Schlüssel inkl. Werte und
    # Unterschlüssel als Snapshot ein (für
    # die Undo-Historie).
    snapshot = {
        "values": {},
        "subkeys": {}
    }

    try:

        with winreg.OpenKey(
            HIVE,
            path,
            0,
            winreg.KEY_READ
        ) as key:

            index = 0

            while True:

                try:

                    name, data, value_type = (
                        winreg.EnumValue(
                            key,
                            index
                        )
                    )

                    snapshot["values"][name] = (
                        value_type,
                        data
                    )

                    index += 1

                except OSError:

                    break

            index = 0

            while True:

                try:

                    child = winreg.EnumKey(
                        key,
                        index
                    )

                    snapshot["subkeys"][child] = (
                        capture_subtree(
                            f"{path}\\{child}"
                        )
                    )

                    index += 1

                except OSError:

                    break

    except (FileNotFoundError, OSError):

        pass

    return snapshot


def restore_subtree(
    parent_path,
    name,
    snapshot
):

    # Stellt einen Snapshot als Schlüssel
    # wieder her und liefert den Pfad.
    path = f"{parent_path}\\{name}"

    with winreg.CreateKeyEx(
        HIVE,
        path,
        0,
        winreg.KEY_READ | winreg.KEY_WRITE
    ) as key:

        for value_name, (
            value_type,
            data
        ) in snapshot["values"].items():

            winreg.SetValueEx(
                key,
                value_name,
                0,
                value_type,
                data
            )

    for child, child_snapshot in (
        snapshot["subkeys"].items()
    ):

        restore_subtree(
            path,
            child,
            child_snapshot
        )

    return path


def delete_key_recursive(
    hive,
    path
):

    # Liefert True, wenn der Schlüssel
    # tatsächlich entfernt wurde. Gescheiterte
    # Teil-Löschungen (Schreibschutz/Rechte)
    # werden nicht mehr still verschwiegen.
    try:

        key = winreg.OpenKey(
            hive,
            path,
            0,
            winreg.KEY_READ | winreg.KEY_WRITE
        )

    except FileNotFoundError:

        return True

    except PermissionError:

        return False

    while True:

        try:

            child_name = winreg.EnumKey(
                key,
                0
            )

        except OSError:

            break

        if not delete_key_recursive(
            hive,
            f"{path}\\{child_name}"
        ):

            winreg.CloseKey(key)

            return False

    winreg.CloseKey(key)

    try:

        winreg.DeleteKey(
            hive,
            path
        )

    except Exception:

        return False

    return not key_exists(path)


def read_default_and_icon(path):

    try:

        with winreg.OpenKey(
            HIVE,
            path
        ) as key:

            try:

                display = winreg.QueryValueEx(
                    key,
                    None
                )[0]

            except FileNotFoundError:

                display = ""

            try:

                icon = winreg.QueryValueEx(
                    key,
                    "Icon"
                )[0]

            except FileNotFoundError:

                icon = ""

            return display, icon

    except FileNotFoundError:

        return "", ""


def read_mui_verb(path):

    try:

        with winreg.OpenKey(
            HIVE,
            path
        ) as key:

            try:

                return winreg.QueryValueEx(
                    key,
                    "MUIVerb"
                )[0]

            except FileNotFoundError:

                return ""

    except FileNotFoundError:

        return ""


def read_command(path):

    try:

        with winreg.OpenKey(
            HIVE,
            f"{path}\\command"
        ) as key:

            return winreg.QueryValueEx(
                key,
                None
            )[0]

    except FileNotFoundError:

        return ""


def has_subkey(
    path,
    name
):

    try:

        with winreg.OpenKey(
            HIVE,
            f"{path}\\{name}"
        ):

            return True

    except FileNotFoundError:

        return False


def has_value(
    path,
    name
):

    try:

        with winreg.OpenKey(
            HIVE,
            path
        ) as key:

            winreg.QueryValueEx(
                key,
                name
            )

            return True

    except (
        FileNotFoundError,
        OSError
    ):

        return False


def enum_subkeys(path):

    try:

        key = winreg.OpenKey(
            HIVE,
            path
        )

    except FileNotFoundError:

        return []

    names = []
    index = 0

    while True:

        try:

            child_name = winreg.EnumKey(
                key,
                index
            )

            if child_name.lower() != "command":

                names.append(
                    child_name
                )

            index += 1

        except OSError:

            break

    key.Close()

    return names


# ----------------------------------------------------------------------
# Einträge auslesen
# ----------------------------------------------------------------------

def list_entries():

    try:

        def recurse(path):

            entries = []

            for name in enum_subkeys(path):

                entry_path = (
                    f"{path}\\{name}"
                )

                display, icon = (
                    read_default_and_icon(
                        entry_path
                    )
                )

                # MUIVerb als Anzeigename, falls
                # (Standard) leer ist (z. B.
                # Shutdown-Menü).
                display = (
                    display
                    or read_mui_verb(
                        entry_path
                    )
                )

                is_menu = has_subkey(
                    entry_path,
                    "shell"
                )

                children = []

                if is_menu:

                    children = recurse(
                        f"{entry_path}\\shell"
                    )

                entries.append({
                    "name": name,
                    "path": entry_path,
                    "display": display,
                    "icon": icon,
                    "is_menu": is_menu,
                    "children": children,
                    "position": read_position(
                        entry_path
                    )
                })

            return entries

        return recurse(
            BASE_PATH
        )

    except PermissionError:

        return []


def get_all_menu_shell_paths():

    menus = []

    def recurse(
        path,
        prefix=""
    ):

        for name in enum_subkeys(path):

            entry_path = (
                f"{path}\\{name}"
            )

            if has_subkey(
                entry_path,
                "shell"
            ):

                display, _ = (
                    read_default_and_icon(
                        entry_path
                    )
                )

                display = (
                    display
                    or read_mui_verb(
                        entry_path
                    )
                )

                label = (
                    f"{prefix}"
                    f"{display or name}"
                )

                menus.append(
                    (
                        label,
                        f"{entry_path}\\shell"
                    )
                )

                recurse(
                    f"{entry_path}\\shell",
                    prefix + "  -> "
                )

    recurse(
        BASE_PATH
    )

    return menus


# ----------------------------------------------------------------------
# Windows Icon API
# ----------------------------------------------------------------------

class ICONINFO(ctypes.Structure):

    _fields_ = [
        ("fIcon", wintypes.BOOL),
        ("xHotspot", wintypes.DWORD),
        ("yHotspot", wintypes.DWORD),
        ("hbmMask", wintypes.HBITMAP),
        ("hbmColor", wintypes.HBITMAP)
    ]


class BITMAPINFOHEADER(ctypes.Structure):

    _fields_ = [
        ("biSize", wintypes.DWORD),
        ("biWidth", wintypes.LONG),
        ("biHeight", wintypes.LONG),
        ("biPlanes", wintypes.WORD),
        ("biBitCount", wintypes.WORD),
        ("biCompression", wintypes.DWORD),
        ("biSizeImage", wintypes.DWORD),
        ("biXPelsPerMeter", wintypes.LONG),
        ("biYPelsPerMeter", wintypes.LONG),
        ("biClrUsed", wintypes.DWORD),
        ("biClrImportant", wintypes.DWORD)
    ]


class RGBQUAD(ctypes.Structure):

    _fields_ = [
        ("rgbBlue", wintypes.BYTE),
        ("rgbGreen", wintypes.BYTE),
        ("rgbRed", wintypes.BYTE),
        ("rgbReserved", wintypes.BYTE)
    ]


class BITMAPINFO(ctypes.Structure):

    _fields_ = [
        ("bmiHeader", BITMAPINFOHEADER),
        ("bmiColors", RGBQUAD * 1)
    ]


class SHSTOCKICONINFO(ctypes.Structure):

    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("hIcon", wintypes.HICON),
        ("iSysImageIndex", wintypes.INT),
        ("iIcon", wintypes.INT),
        (
            "szPath",
            wintypes.WCHAR * 260
        )
    ]


BI_RGB = 0
DIB_RGB_COLORS = 0

SHGSI_ICON = 0x000000100
SHGSI_LARGEICON = 0x000000000
SHGSI_SMALLICON = 0x000000001

SIID_DOCNOASSOC = 0
SIID_FOLDER = 3
SIID_FIND = 22
SIID_SETTINGS = 106
SIID_RENAME = 83
SIID_DELETE = 84
SIID_INFO = 79
SIID_KEY = 81
SIID_SOFTWARE = 82
SIID_ZIPFILE = 105
SIID_FOLDEROPEN = 4
SIID_APPLICATION = 2


def _configure_windows_api():

    try:

        shell32 = ctypes.WinDLL(
            "shell32",
            use_last_error=True
        )

        user32 = ctypes.WinDLL(
            "user32",
            use_last_error=True
        )

        gdi32 = ctypes.WinDLL(
            "gdi32",
            use_last_error=True
        )

        shell32.ExtractIconExW.argtypes = [
            wintypes.LPCWSTR,
            ctypes.c_int,
            ctypes.POINTER(wintypes.HICON),
            ctypes.POINTER(wintypes.HICON),
            wintypes.UINT
        ]

        shell32.ExtractIconExW.restype = wintypes.UINT

        shell32.SHGetStockIconInfo.argtypes = [
            wintypes.INT,
            wintypes.UINT,
            ctypes.POINTER(SHSTOCKICONINFO)
        ]

        shell32.SHGetStockIconInfo.restype = wintypes.LONG

        user32.GetIconInfo.argtypes = [
            wintypes.HICON,
            ctypes.POINTER(ICONINFO)
        ]

        user32.GetIconInfo.restype = wintypes.BOOL

        user32.DestroyIcon.argtypes = [
            wintypes.HICON
        ]

        user32.DestroyIcon.restype = wintypes.BOOL

        gdi32.CreateCompatibleDC.argtypes = [
            wintypes.HDC
        ]

        gdi32.CreateCompatibleDC.restype = (
            wintypes.HDC
        )

        gdi32.DeleteDC.argtypes = [
            wintypes.HDC
        ]

        gdi32.DeleteDC.restype = wintypes.BOOL

        gdi32.DeleteObject.argtypes = [
            wintypes.HGDIOBJ
        ]

        gdi32.DeleteObject.restype = wintypes.BOOL

        gdi32.GetDIBits.argtypes = [
            wintypes.HDC,
            wintypes.HBITMAP,
            wintypes.UINT,
            wintypes.UINT,
            wintypes.LPVOID,
            ctypes.POINTER(BITMAPINFO),
            wintypes.UINT
        ]

        gdi32.GetDIBits.restype = ctypes.c_int

        return shell32, user32, gdi32

    except Exception:

        return None, None, None


SHELL32, USER32, GDI32 = (
    _configure_windows_api()
)


def get_icon_handle(
    path,
    large=False,
    index=0
):

    if not path:
        return None

    if not SHELL32:
        return None

    try:

        large_icons = (
            wintypes.HICON * 1
        )()

        small_icons = (
            wintypes.HICON * 1
        )()

        count = SHELL32.ExtractIconExW(
            path,
            int(index),
            large_icons,
            small_icons,
            1
        )

        if count <= 0:
            return None

        handle = (
            large_icons[0]
            if large
            else small_icons[0]
        )

        if not handle:
            return None

        return handle

    except Exception:

        return None


def get_stock_icon_handle(
    icon_id,
    large=False
):

    if not SHELL32:
        return None

    try:

        info = SHSTOCKICONINFO()

        info.cbSize = ctypes.sizeof(
            SHSTOCKICONINFO
        )

        flags = SHGSI_ICON

        if large:
            flags |= SHGSI_LARGEICON
        else:
            flags |= SHGSI_SMALLICON

        result = SHELL32.SHGetStockIconInfo(
            int(icon_id),
            flags,
            ctypes.byref(info)
        )

        if result != 0:
            return None

        return info.hIcon

    except Exception:

        return None


def hicon_to_photo(
    root,
    hicon,
    size=16,
    background="#ffffff"
):

    if not hicon:
        return None

    if not USER32 or not GDI32:
        return None

    info = ICONINFO()

    try:

        if not USER32.GetIconInfo(
            hicon,
            ctypes.byref(info)
        ):

            return None

        dc = GDI32.CreateCompatibleDC(
            0
        )

        if not dc:
            return None

        try:

            width = int(size)
            height = int(size)

            bmi = BITMAPINFO()

            ctypes.memset(
                ctypes.byref(bmi),
                0,
                ctypes.sizeof(bmi)
            )

            bmi.bmiHeader.biSize = (
                ctypes.sizeof(
                    BITMAPINFOHEADER
                )
            )

            bmi.bmiHeader.biWidth = width
            bmi.bmiHeader.biHeight = -height
            bmi.bmiHeader.biPlanes = 1
            bmi.bmiHeader.biBitCount = 32
            bmi.bmiHeader.biCompression = BI_RGB
            bmi.bmiHeader.biSizeImage = (
                width * height * 4
            )

            buffer_size = (
                width * height * 4
            )

            buffer = ctypes.create_string_buffer(
                buffer_size
            )

            bitmap = info.hbmColor

            if not bitmap:
                return None

            copied = GDI32.GetDIBits(
                dc,
                bitmap,
                0,
                height,
                buffer,
                ctypes.byref(bmi),
                DIB_RGB_COLORS
            )

            if copied == 0:
                return None

            try:

                bg = background.lstrip("#")

                if len(bg) == 6:

                    br = int(
                        bg[0:2],
                        16
                    )

                    bgc = int(
                        bg[2:4],
                        16
                    )

                    bb = int(
                        bg[4:6],
                        16
                    )

                else:

                    br, bgc, bb = (
                        255,
                        255,
                        255
                    )

            except Exception:

                br, bgc, bb = (
                    255,
                    255,
                    255
                )

            raw = buffer.raw

            ppm = bytearray()

            ppm.extend(
                f"P6\n{width} {height}\n255\n".encode(
                    "ascii"
                )
            )

            for pos in range(
                0,
                len(raw),
                4
            ):

                b = raw[pos]
                g = raw[pos + 1]
                r = raw[pos + 2]
                a = raw[pos + 3]

                if a == 0:

                    # Bei alten Icons kann die Alpha-
                    # Information fehlen. In diesem Fall
                    # wird ein vorhandener Farbwert benutzt.
                    if (
                        r == 0
                        and g == 0
                        and b == 0
                    ):
                        r = br
                        g = bgc
                        b = bb

                elif a < 255:

                    alpha = a / 255.0

                    r = int(
                        r * alpha
                        + br * (1.0 - alpha)
                    )

                    g = int(
                        g * alpha
                        + bgc * (1.0 - alpha)
                    )

                    b = int(
                        b * alpha
                        + bb * (1.0 - alpha)
                    )

                ppm.extend(
                    bytes(
                        (
                            r,
                            g,
                            b
                        )
                    )
                )

            return tk.PhotoImage(
                data=bytes(ppm),
                format="PPM"
            )

        finally:

            try:
                GDI32.DeleteDC(dc)
            except Exception:
                pass

    except Exception:

        return None

    finally:

        try:

            if info.hbmColor:
                GDI32.DeleteObject(
                    info.hbmColor
                )

            if info.hbmMask:
                GDI32.DeleteObject(
                    info.hbmMask
                )

        except Exception:

            pass


def parse_icon_reference(icon_text):

    if not icon_text:
        return "", 0

    value = str(
        icon_text
    ).strip()

    if not value:
        return "", 0

    index = 0

    # Registry Icon-Werte können beispielsweise
    # "C:\test\app.exe,0" oder
    # "%SystemRoot%\System32\imageres.dll,-102"
    # enthalten.
    if "," in value:

        path_part, index_part = (
            value.rsplit(",", 1)
        )

        path_part = path_part.strip()
        index_part = index_part.strip()

        try:
            index = int(index_part)
        except ValueError:
            index = 0

        value = path_part

    if (
        len(value) >= 2
        and value.startswith('"')
        and value.endswith('"')
    ):

        value = value[1:-1]

    value = os.path.expandvars(
        value
    )

    return value, index


def resolve_icon_path(icon_text):

    path, _ = parse_icon_reference(
        icon_text
    )

    if os.path.exists(path):
        return path

    return ""


def icon_photo_from_reference(
    root,
    icon_text,
    size=16,
    background="#ffffff"
):

    path, index = parse_icon_reference(
        icon_text
    )

    if not path:
        return None

    if not os.path.exists(path):
        return None

    handle = get_icon_handle(
        path,
        large=False,
        index=index
    )

    if not handle:
        return None

    try:

        return hicon_to_photo(
            root,
            handle,
            size=size,
            background=background
        )

    finally:

        try:

            USER32.DestroyIcon(
                handle
            )

        except Exception:
            pass


# ----------------------------------------------------------------------
# Farb-Themes
# ----------------------------------------------------------------------

CREAMY = {
    "bg": "#f5e7ce",
    "fg": "#5a4632",
    "entry_bg": "#fffaf0",
    "entry_fg": "#5a4632",
    "tree_bg": "#faf0dd",
    "tree_fg": "#5a4632",
    "select_bg": "#d2a24c",
    "select_fg": "#ffffff",
    "btn_bg": "#e8d5a8"
}

DARK = {
    "bg": "#1e1e1e",
    "fg": "#90ee90",
    "entry_bg": "#2a2a2a",
    "entry_fg": "#90ee90",
    "tree_bg": "#1e1e1e",
    "tree_fg": "#90ee90",
    "select_bg": "#00008b",
    "select_fg": "#ffff66",
    "btn_bg": "#333333"
}

BLUE_YELLOW = {
    "bg": "#061a3a",
    "fg": "#ffe066",
    "entry_bg": "#0b2857",
    "entry_fg": "#ffe066",
    "tree_bg": "#061a3a",
    "tree_fg": "#ffe066",
    "select_bg": "#174ea6",
    "select_fg": "#ffed99",
    "btn_bg": "#12366d"
}


class ThemeManager:

    def __init__(
        self,
        root,
        style
    ):

        self.root = root
        self.style = style

        self.modes = [
            ("Creamy", CREAMY),
            ("DarkGreen", DARK),
            (
                "BlueMoon",
                BLUE_YELLOW
            )
        ]

        self.mode_index = 1
        self.dialogs = []

    @property
    def palette(self):

        return self.modes[
            self.mode_index
        ][1]

    @property
    def name(self):

        return self.modes[
            self.mode_index
        ][0]

    def register(
        self,
        dialog
    ):

        self.dialogs.append(
            dialog
        )

    def next_theme(self):

        self.mode_index = (
            self.mode_index + 1
        ) % len(self.modes)

        self.apply()

    def apply(self):

        palette = self.palette

        self.style.theme_use(
            "clam"
        )

        self.root.configure(
            bg=palette["bg"]
        )

        self.style.configure(
            ".",
            background=palette["bg"],
            foreground=palette["fg"],
            fieldbackground=palette["entry_bg"]
        )

        self.style.configure(
            "TFrame",
            background=palette["bg"]
        )

        self.style.configure(
            "TLabel",
            background=palette["bg"],
            foreground=palette["fg"]
        )

        self.style.configure(
            "TButton",
            background=palette["btn_bg"],
            foreground=palette["fg"]
        )

        self.style.map(
            "TButton",
            background=[
                (
                    "active",
                    palette["select_bg"]
                )
            ],
            foreground=[
                (
                    "active",
                    palette["select_fg"]
                )
            ]
        )

        self.style.configure(
            "TEntry",
            fieldbackground=palette["entry_bg"],
            foreground=palette["entry_fg"],
            insertbackground=palette["entry_fg"],
            insertwidth=2
        )

        self.style.configure(
            "TCheckbutton",
            background=palette["bg"],
            foreground=palette["fg"]
        )

        self.style.configure(
            "TCombobox",
            fieldbackground=palette["entry_bg"],
            foreground=palette["entry_fg"],
            insertbackground=palette["entry_fg"],
            insertwidth=2
        )

        self.style.map(
            "TCombobox",
            fieldbackground=[
                (
                    "readonly",
                    palette["entry_bg"]
                )
            ],
            foreground=[
                (
                    "readonly",
                    palette["entry_fg"]
                )
            ]
        )

        self.style.configure(
            "Treeview",
            background=palette["tree_bg"],
            foreground=palette["tree_fg"],
            fieldbackground=palette["tree_bg"],
            rowheight=24
        )

        self.style.map(
            "Treeview",
            background=[
                (
                    "selected",
                    palette["select_bg"]
                )
            ],
            foreground=[
                (
                    "selected",
                    palette["select_fg"]
                )
            ]
        )

        self.style.configure(
            "Treeview.Heading",
            background=palette["btn_bg"],
            foreground=palette["fg"]
        )

        open_dialogs = []

        for dialog in self.dialogs:

            try:

                if dialog.winfo_exists():

                    self._paint_plain_widgets(
                        dialog,
                        palette
                    )

                    open_dialogs.append(
                        dialog
                    )

            except tk.TclError:

                pass

        self.dialogs = open_dialogs

    def _paint_plain_widgets(
        self,
        widget,
        palette
    ):

        try:

            widget.configure(
                bg=palette["bg"]
            )

        except tk.TclError:

            pass

        for child in widget.winfo_children():

            wc = child.winfo_class()

            if wc == "Text":

                # z. B. Hilfe-Dialog: folgt dem Theme
                # live (Eingabe-Feld-Farben). Kein
                # weiteres Rekursions-Scoring, sonst
                # überschreibt das generische bg=
                # unten die Feldfarben erneut.
                try:

                    child.configure(
                        bg=palette["entry_bg"],
                        fg=palette["entry_fg"],
                        insertbackground=palette["entry_fg"]
                    )

                except tk.TclError:

                    pass

                continue

            if wc in (
                "Frame",
                "Toplevel",
                "Labelframe"
            ):

                try:

                    child.configure(
                        bg=palette["bg"]
                    )

                except tk.TclError:

                    pass

            elif wc == "Label":

                try:

                    child.configure(
                        bg=palette["bg"],
                        fg=palette["fg"]
                    )

                except tk.TclError:

                    pass

            self._paint_plain_widgets(
                child,
                palette
            )


# ----------------------------------------------------------------------
# Tooltip
# ----------------------------------------------------------------------

class ToolTip:

    # Klassenweite Liste aller Tooltips →
    # Sprachumschaltung kann alle Texte
    # live aktualisieren.
    _instances = []

    def __init__(
        self,
        widget,
        text
    ):

        self.widget = widget
        self.raw_text = text
        self.text = tr(text)
        self.tipwindow = None

        ToolTip._instances.append(self)

        self.widget.bind(
            "<Enter>",
            self.show,
            add="+"
        )

        self.widget.bind(
            "<Leave>",
            self.hide,
            add="+"
        )

    def set_text(
        self,
        raw
    ):

        # Neuer ROHTEXT (Deutsch/Schlüssel); die
        # Anzeige wird daraus übersetzt. raw_text
        # bleibt damit die stabile Referenz für
        # Sprach-Umschaltungen.
        self.raw_text = raw
        self.text = tr(raw)

        self.hide()

    @classmethod
    def retranslate_all(cls):

        for tip in cls._instances:

            try:

                if tip.widget.winfo_exists():

                    tip.set_text(
                        tip.raw_text
                    )

            except tk.TclError:

                pass

    def show(
        self,
        event=None
    ):

        if self.tipwindow:
            return

        try:

            x = (
                self.widget.winfo_rootx()
                + 20
            )

            y = (
                self.widget.winfo_rooty()
                + self.widget.winfo_height()
                + 4
            )

            self.tipwindow = tw = tk.Toplevel(
                self.widget
            )

            tw.wm_overrideredirect(
                True
            )

            tw.wm_geometry(
                f"+{x}+{y}"
            )

            label = tk.Label(
                tw,
                text=self.text,
                bg="#ffffe1",
                fg="#000000",
                relief="solid",
                borderwidth=1,
                padx=5,
                pady=3,
                font=(
                    "Segoe UI",
                    9
                )
            )

            label.pack()

        except Exception:

            self.tipwindow = None

    def hide(
        self,
        event=None
    ):

        if self.tipwindow:

            try:

                self.tipwindow.destroy()

            except Exception:
                pass

            self.tipwindow = None


# ----------------------------------------------------------------------
# Hauptfenster
# ----------------------------------------------------------------------

class App(tk.Tk):

    def __init__(self):

        super().__init__()

        self.title(
            f"Menu-Edit v{APP_VERSION}"
        )

        # Tool-Icon (menu-editor.svg → icons\menu-editor.ico/.png,
        # erzeugt mit make_app_icon.py): Titelleiste + Taskbar.
        self._set_window_icon()

        # Gespeicherte Fenstergröße aus der
        # settings.ini wiederherstellen.
        saved_geometry = SETTINGS.get(
            "window_geometry",
            ""
        )

        if re.match(
            r"^\d+x\d+$",
            saved_geometry or ""
        ):

            self.geometry(saved_geometry)

        else:

            self.geometry(
                "1000x650"
            )

        self.minsize(
            750,
            500
        )

        self.style = ttk.Style(
            self
        )

        self.theme = ThemeManager(
            self,
            self.style
        )

        # Zuletzt verwendeten Bereich aus der
        # settings.ini wiederherstellen.
        global BASE_PATH

        if SETTINGS.get(
            "area"
        ) == "desktop":

            BASE_PATH = (
                BASE_PATH_DESKTOP
            )

        # Zuletzt verwendetes Design aus der
        # settings.ini wiederherstellen.
        theme_names = [
            name
            for name, _ in self.theme.modes
        ]

        if SETTINGS.get(
            "theme"
        ) in theme_names:

            self.theme.mode_index = (
                theme_names.index(
                    SETTINGS["theme"]
                )
            )

        self.node_paths = {}

        self.tree_icon_cache = {}
        self.toolbar_icons = {}
        self.toolbar_buttons = []

        # Undo-Historie (nur im Speicher,
        # max. 10 Einträge; wird bei jedem
        # Programmstart zurückgesetzt).
        self.undo_stack = []
        self._undoing = False
        self._drop_target_iid = None
        self._drop_state = None
        self._drop_into = False
        self._drop_bar = None
        self._dnd_scroll_dir = 0
        self._dnd_scroll_after = None

        self._build_ui()

        # Überbliebene __tmp__-Schlüssel
        # früherer Tausch-Vorgänge aufräumen.
        try:

            sweep_tmp_keys()

        except Exception:

            pass

        self.theme.apply()

        self.refresh()

        self.after(
            350,
            self.first_start_backup
        )

        # Fenstergröße beim Beenden speichern.
        self.protocol(
            "WM_DELETE_WINDOW",
            self.on_close
        )

    # ------------------------------------------------------------------
    # Schließen
    # ------------------------------------------------------------------

    def on_close(self):

        SETTINGS["window_geometry"] = (
            f"{self.winfo_width()}x{self.winfo_height()}"
        )

        save_settings(SETTINGS)

        self.destroy()

    # ------------------------------------------------------------------
    # Bereich
    # ------------------------------------------------------------------

    def get_registry_title(self):

        if (
            BASE_PATH.lower()
            == BASE_PATH_DIRECTORY.lower()
        ):

            return (
                r"HKCR\Directory\Background\Shell"
            )

        return (
            r"HKCR\DesktopBackground\Shell"
        )

    def get_registry_display_name(self):

        if (
            BASE_PATH.lower()
            == BASE_PATH_DIRECTORY.lower()
        ):

            return (
                tr("Obers\\Unteres Menü")
            )

        return "DesktopBackground"

    def switch_registry_root(self):

        global BASE_PATH

        if (
            BASE_PATH.lower()
            == BASE_PATH_DIRECTORY.lower()
        ):

            BASE_PATH = (
                BASE_PATH_DESKTOP
            )

        else:

            BASE_PATH = (
                BASE_PATH_DIRECTORY
            )

        self.switch_button.configure(
            text=(
                tr("Bereich: ")
                + self.get_registry_display_name()
            )
        )

        # Bereich merken, damit er beim
        # nächsten Start wiederhergestellt wird.
        SETTINGS["area"] = (
            "desktop"
            if BASE_PATH.lower()
            == BASE_PATH_DESKTOP.lower()
            else "directory"
        )

        save_settings(SETTINGS)

        self.refresh()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self):

        # --------------------------------------------------------------
        # Button-Leiste
        # --------------------------------------------------------------

        action_buttons_frame = ttk.Frame(
            self
        )

        action_buttons_frame.pack(
            side="top",
            fill="x",
            padx=8,
            pady=(6, 2)
        )

        self._create_toolbar_buttons(
            action_buttons_frame
        )

        # --------------------------------------------------------------
        # Leiste rechts: eine Reihe, rechtsbündig —
        # Hilfe + Sprache LINKS neben dem Design-
        # Button, dann Bereich (Nutzer-Vorgabe v3.6).
        # --------------------------------------------------------------

        toolbar = ttk.Frame(
            self
        )

        toolbar.pack(
            side="top",
            fill="x",
            padx=8,
            pady=(2, 6)
        )

        right_bar = ttk.Frame(
            toolbar
        )

        right_bar.pack(
            side="right"
        )

        self.switch_button = ttk.Button(
            right_bar,
            text=(
                tr("Bereich: ")
                + self.get_registry_display_name()
            ),
            command=self.switch_registry_root
        )

        self.switch_button.grid(
            row=0,
            column=3,
            padx=3,
            sticky="e"
        )

        self.theme_button = ttk.Button(
            right_bar,
            text=(
                tr("Design: ")
                + self.theme.name
            ),
            command=self.cycle_theme
        )

        self.theme_button.grid(
            row=0,
            column=2,
            padx=3,
            sticky="e"
        )

        # Sprach-Button (direkt links neben
        # Design): schaltet Deutsch ↔ English um.
        self.lang_button = ttk.Button(
            right_bar,
            text=(
                "Sprache: Deutsch"
                if APP_LANG == "de"
                else "Language: English"
            ),
            command=self.switch_language
        )

        self.lang_button.grid(
            row=0,
            column=1,
            padx=3,
            sticky="e"
        )

        # Hilfe-Button (links neben Sprache);
        # öffnet den Hilfe-Dialog.
        self.help_button = ttk.Button(
            right_bar,
            text=tr("Hilfe"),
            command=self.show_help_dialog
        )

        self.help_button.grid(
            row=0,
            column=0,
            padx=3,
            sticky="e"
        )

        # --------------------------------------------------------------
        # Tree
        # --------------------------------------------------------------

        tree_frame = ttk.Frame(
            self
        )

        tree_frame.pack(
            side="top",
            fill="both",
            expand=True,
            padx=8,
            pady=(0, 6)
        )

        self.tree = ttk.Treeview(
            tree_frame,
            columns=("info",),
            show="tree headings",
            selectmode="extended"
        )

        self.tree.heading(
            "#0",
            text=tr("Eintrag")
        )

        self.tree.heading(
            "info",
            text=tr("Details / Pfad")
        )

        self.tree.column(
            "#0",
            width=360
        )

        self.tree.column(
            "info",
            width=600
        )

        self.tree.pack(
            side="left",
            fill="both",
            expand=True
        )

        scrollbar = ttk.Scrollbar(
            tree_frame,
            orient="vertical",
            command=self.tree.yview
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )

        self.tree.configure(
            yscrollcommand=scrollbar.set
        )

        self.tree.bind(
            "<Double-1>",
            lambda event:
            self.edit_selected()
        )

        # Drag & Drop zum Verschieben
        self.tree.bind(
            "<Button-1>",
            self._on_tree_press
        )

        self.tree.bind(
            "<B1-Motion>",
            self._on_tree_motion,
            add="+"
        )

        self.tree.bind(
            "<ButtonRelease-1>",
            self._on_tree_release
        )

        # Rechtsklick: Hauptfenster-Kontextmenü
        # (Fenster und Baum; add="+" erhält
        # bestehende Bindings).
        self.bind(
            "<Button-3>",
            self._show_main_context_menu,
            add="+"
        )

        self.tree.bind(
            "<Button-3>",
            self._show_main_context_menu,
            add="+"
        )

        # --------------------------------------------------------------
        # Status
        # --------------------------------------------------------------

        status = ttk.Frame(
            self
        )

        status.pack(
            side="bottom",
            fill="x",
            padx=8,
            pady=4
        )

        admin_text = (
            "Administrator: Ja"
            if is_admin()
            else
            "Administrator: Nein "
            "(Schreibrechte eventuell eingeschränkt!)"
        )

        self.status_label = ttk.Label(
            status,
            text=(
                f"{self.get_registry_title()}   |   "
                f"{tr(admin_text)}"
            )
        )

        self.status_label.pack(
            side="left"
        )

    def _set_window_icon(
        self
    ):

        # Eigenes Tool-Icon für Titelleiste und
        # Taskbar. Quelle: icons\menu-editor.svg,
        # konvertiert mit make_app_icon.py.
        # Zuerst das .ico (alle Größen von 16 bis
        # 256 px, auch für PyInstaller --icon);
        # falls das nicht ladbar ist, Fallback auf
        # die 256-px-PNG via iconphoto.
        ico_path = os.path.join(
            ICON_DIR,
            "menu-editor.ico"
        )

        png_path = os.path.join(
            ICON_DIR,
            "menu-editor.png"
        )

        if os.path.isfile(ico_path):

            try:

                self.iconbitmap(ico_path)

                return

            except Exception:

                pass

        if os.path.isfile(png_path):

            try:

                image = tk.PhotoImage(
                    file=png_path,
                    master=self
                )

                self.iconphoto(
                    True,
                    image
                )

                # Referenz halten (Tk-Garbage-Collection)
                self._app_icon_image = image

            except Exception:

                pass

    # ------------------------------------------------------------------
    # Toolbar Buttons
    # ------------------------------------------------------------------

    def _create_toolbar_buttons(
        self,
        parent
    ):

        # Alle Buttons verwenden die eingebetteten
        # PNG-Icons aus ICON_DIR (feste Zuordnung
        # siehe TOOLBAR_ICON_FILES).
        button_definitions = [
            (
                "new_entry",
                "Neuen Eintrag erstellen",
                self.open_add_app_dialog
            ),
            (
                "new_menu",
                "Neues Menü erstellen",
                self.open_add_menu_dialog
            ),
            (
                "new_menu_item",
                "Eintrag in Menü erstellen",
                self.open_add_menu_item_dialog
            ),
            (
                "edit",
                "Ausgewählten Eintrag bearbeiten",
                self.edit_selected
            ),
            (
                "delete",
                "Ausgewählten Eintrag löschen",
                self.delete_selected
            ),
            (
                "refresh",
                "Ansicht aktualisieren",
                self.refresh
            )
        ]

        for (
            name,
            tooltip,
            command
        ) in button_definitions:

            image = self._load_toolbar_icon(
                name
            )

            button = ttk.Button(
                parent,
                image=image,
                command=command,
                width=3
            )

            button.icon_name = name

            if image:

                button.image = image

            button.pack(
                side="left",
                padx=2
            )

            ToolTip(
                button,
                tooltip
            )

            self.toolbar_buttons.append(
                button
            )

        # Undo (vor Backup, mit Abstand)
        undo_image = (
            self._load_toolbar_icon(
                "undo"
            )
        )

        self.undo_button = ttk.Button(
            parent,
            image=undo_image,
            command=self.undo_last,
            width=3
        )

        self.undo_button.icon_name = "undo"

        if undo_image:

            self.undo_button.image = (
                undo_image
            )

        self.undo_button.pack(
            side="left",
            padx=(10, 2)
        )

        ToolTip(
            self.undo_button,
            "Letzte Änderung rückgängig "
            "machen (max. 10)"
        )

        self.toolbar_buttons.append(
            self.undo_button
        )

        # Backup separat mit Menü
        backup_image = (
            self._load_toolbar_icon(
                "backup"
            )
        )

        self.backup_button = ttk.Button(
            parent,
            image=backup_image,
            command=self.show_backup_menu,
            width=3
        )

        self.backup_button.icon_name = "backup"

        if backup_image:
            self.backup_button.image = (
                backup_image
            )

        self.backup_button.pack(
            side="left",
            padx=(2, 2)
        )

        ToolTip(
            self.backup_button,
            "Backup"
        )

        self.toolbar_buttons.append(
            self.backup_button
        )

        # Nach oben / nach unten rechts
        # neben dem Backup-Button.
        move_up_image = (
            self._load_toolbar_icon(
                "move_up"
            )
        )

        self.move_up_button = ttk.Button(
            parent,
            image=move_up_image,
            command=lambda:
                self.move_selected(-1),
            width=3
        )

        self.move_up_button.icon_name = "move_up"

        if move_up_image:

            self.move_up_button.image = (
                move_up_image
            )

        self.move_up_button.pack(
            side="left",
            padx=(10, 2)
        )

        ToolTip(
            self.move_up_button,
            "Auswahl nach oben verschieben"
        )

        self.toolbar_buttons.append(
            self.move_up_button
        )

        move_down_image = (
            self._load_toolbar_icon(
                "move_down"
            )
        )

        self.move_down_button = ttk.Button(
            parent,
            image=move_down_image,
            command=lambda:
                self.move_selected(1),
            width=3
        )

        self.move_down_button.icon_name = "move_down"

        if move_down_image:

            self.move_down_button.image = (
                move_down_image
            )

        self.move_down_button.pack(
            side="left",
            padx=(2, 2)
        )

        ToolTip(
            self.move_down_button,
            "Auswahl nach unten verschieben"
        )

        self.toolbar_buttons.append(
            self.move_down_button
        )

        # Shutdown-Menü ganz rechts, mit
        # Abstand neben dem Pfeil-Paar.
        shutdown_image = (
            self._load_toolbar_icon(
                "shutdown_menu"
            )
        )

        self.shutdown_menu_button = ttk.Button(
            parent,
            image=shutdown_image,
            command=self.create_shutdown_menu,
            width=3
        )

        self.shutdown_menu_button.icon_name = (
            "shutdown_menu"
        )

        if shutdown_image:

            self.shutdown_menu_button.image = (
                shutdown_image
            )

        self.shutdown_menu_button.pack(
            side="left",
            padx=(10, 2)
        )

        ToolTip(
            self.shutdown_menu_button,
            "Shutdown-Menü anlegen (Neustart / "
            "Herunterfahren / Abmelden)"
        )

        self.toolbar_buttons.append(
            self.shutdown_menu_button
        )

    def _load_toolbar_icon(
        self,
        name
    ):

        if name in self.toolbar_icons:

            return self.toolbar_icons[name]

        # Toolbar-Icons kommen ausschließlich aus
        # dem Projektordner `icons\` (feste
        # Zuordnung Button → Datei, siehe
        # TOOLBAR_ICON_FILES). Keine DLL-Extraktion
        # mehr: die PNGs sind originale, selbst
        # gezeichnete Grafiken (make_icons.py) mit
        # Alpha-Kanal — identisch auf allen
        # Systemen und in allen Themes.
        filename = TOOLBAR_ICON_FILES.get(name)

        if not filename:
            return None

        png_path = os.path.join(
            ICON_DIR,
            filename
        )

        if not os.path.isfile(png_path):
            return None

        try:

            image = tk.PhotoImage(
                file=png_path,
                master=self
            )

        except Exception:

            return None

        self.toolbar_icons[name] = image

        return image

    # ------------------------------------------------------------------
    # Backup Button Menü
    # ------------------------------------------------------------------

    def show_backup_menu(self):

        menu = tk.Menu(
            self._menu_popup_holder(),
            tearoff=0
        )

        self._fill_backup_menu_entries(menu)

        try:

            x = (
                self.backup_button.winfo_rootx()
            )

            y = (
                self.backup_button.winfo_rooty()
                + self.backup_button.winfo_height()
            )

            menu.tk_popup(
                x,
                y
            )

        finally:

            menu.grab_release()

    def _menu_popup_holder(
        self
    ):

        # Versteckter Container als Parent für Popup-
        # Menüs. Wichtig: Ein tk.Menu-Kind des
        # Hauptfensters (Tk) würde von Tk automatisch
        # als Menüleiste des Fensters registriert —
        # dabei ging der erste Menüeintrag verloren.
        holder = getattr(
            self,
            "_menu_popup_holder_frame",
            None
        )

        if holder is None:

            holder = tk.Frame(self)

            self._menu_popup_holder_frame = holder

        return holder

    def _fill_backup_menu_entries(
        self,
        menu
    ):

        # Die vier Backup-Funktionen des Backup-
        # Buttons; genutzt vom Backup-Popup und
        # vom Hauptfenster-Kontextmenü (Cascade).
        menu.add_command(
            label=tr("Beide Bereiche einzeln sichern"),
            command=self.backup_both_separate
        )

        menu.add_command(
            label=tr("Beide Bereiche gemeinsam sichern"),
            command=self.backup_combined
        )

        menu.add_separator()

        menu.add_command(
            label=tr("Aktuellen Bereich sichern"),
            command=self.backup_current
        )

        menu.add_separator()

        menu.add_command(
            label=tr("Backup-Einstellungen"),
            command=self.backup_settings_dialog
        )

    # ------------------------------------------------------------------
    # Hauptfenster-Kontextmenü (Rechtsklick)
    # ------------------------------------------------------------------

    def _build_main_context_menu(
        self
    ):

        # Enthält alle Funktionen der Toolbar-
        # Buttons (wie show_backup_menu jedes Mal
        # neu gebaut → immer aktuelle Palette).
        # Bewusst NICHT: Nach oben/Nach unten
        # (Pfeil-Buttons, Nutzer-Vorgabe).
        palette = self.theme.palette

        menu = tk.Menu(
            self._menu_popup_holder(),
            tearoff=0,
            bg=palette["btn_bg"],
            fg=palette["fg"],
            activebackground=palette["select_bg"],
            activeforeground=palette["select_fg"]
        )

        menu.add_command(
            label=tr("Neuen Eintrag erstellen"),
            command=self.open_add_app_dialog
        )

        menu.add_command(
            label=tr("Neues Menü erstellen"),
            command=self.open_add_menu_dialog
        )

        menu.add_command(
            label=tr("Eintrag in Menü erstellen"),
            command=self.open_add_menu_item_dialog
        )

        menu.add_separator()

        menu.add_command(
            label=tr("Bearbeiten"),
            command=self.edit_selected
        )

        menu.add_command(
            label=tr("Löschen"),
            command=self.delete_selected
        )

        menu.add_command(
            label=tr("Ansicht aktualisieren"),
            command=self.refresh
        )

        menu.add_separator()

        menu.add_command(
            label=tr("Letzte Änderung rückgängig machen"),
            command=self.undo_last
        )

        menu.add_cascade(
            label=tr("Backup"),
            menu=self._build_backup_cascade(menu)
        )

        menu.add_separator()

        menu.add_command(
            label=tr("Shutdown-Menü anlegen"),
            command=self.create_shutdown_menu
        )

        return menu

    def _build_backup_cascade(
        self,
        parent
    ):

        palette = self.theme.palette

        cascade = tk.Menu(
            parent,
            tearoff=0,
            bg=palette["btn_bg"],
            fg=palette["fg"],
            activebackground=palette["select_bg"],
            activeforeground=palette["select_fg"]
        )

        self._fill_backup_menu_entries(cascade)

        return cascade

    def _show_main_context_menu(
        self,
        event
    ):

        menu = self._build_main_context_menu()

        try:

            menu.tk_popup(
                event.x_root,
                event.y_root
            )

        finally:

            menu.grab_release()

    # ------------------------------------------------------------------
    # Hilfe-Dialog
    # ------------------------------------------------------------------

    def show_help_dialog(self):

        # Nur über den Toolbar-Button erreichbar
        # (bewusst NICHT im Rechtsklick-Kontext-
        # menü). Nicht-modal: kann beim Arbeiten
        # offen bleiben.
        if getattr(
            self,
            "_help_dialog",
            None
        ) is not None:

            try:

                if self._help_dialog.winfo_exists():

                    self._help_dialog.deiconify()
                    self._help_dialog.lift()
                    self._help_dialog.focus_set()

                    return

            except tk.TclError:

                pass

        dialog = tk.Toplevel(
            self
        )

        dialog.title(
            tr("Hilfe")
            + f" – Menu-Edit v{APP_VERSION}"
        )

        dialog.transient(self)

        dialog.geometry("780x600")

        self.theme.register(dialog)

        self._help_dialog = dialog

        frame = ttk.Frame(
            dialog,
            padding=10
        )

        frame.pack(
            fill="both",
            expand=True
        )

        palette = self.theme.palette

        text = tk.Text(
            frame,
            wrap="word",
            bd=0,
            relief="flat",
            padx=10,
            pady=8,
            bg=palette["entry_bg"],
            fg=palette["entry_fg"],
            insertbackground=palette["entry_fg"],
            font=("Segoe UI", 10)
        )

        scrollbar = ttk.Scrollbar(
            frame,
            orient="vertical",
            command=text.yview
        )

        text.configure(
            yscrollcommand=scrollbar.set
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )

        text.pack(
            side="left",
            fill="both",
            expand=True
        )

        text.tag_configure(
            "heading",
            font=("Segoe UI", 10, "bold"),
            spacing1=8,
            spacing3=2
        )

        for style, content in (
            HELP_TEXT_EN if APP_LANG == "en" else HELP_TEXT
        ):

            text.insert(
                "end",
                content,
                ("heading",) if style == "heading" else ()
            )

        text.configure(state="disabled")

        ttk.Button(
            frame,
            text=tr("Schließen"),
            command=dialog.destroy
        ).pack(
            side="bottom",
            anchor="e",
            pady=(8, 0)
        )

        dialog.focus_set()

    # ------------------------------------------------------------------
    # Design
    # ------------------------------------------------------------------

    def cycle_theme(self):

        # Schaltet zum nächsten Design durch
        # und übernimmt es sofort. Das zuletzt
        # angezeigte Design bleibt ausgewählt.
        self.theme.next_theme()

        self.theme_button.configure(
            text=(
                tr("Design: ")
                + self.theme.name
            )
        )        # Design merken, damit es beim
        # nächsten Start wiederhergestellt wird.
        SETTINGS["theme"] = self.theme.name

        save_settings(SETTINGS)

        # Die Toolbar-Icons besitzen einen Hintergrund
        # passend zum Button. Nach einem Theme-Wechsel
        # werden sie neu erzeugt.
        self._rebuild_toolbar_icons()

        self.refresh()

    def switch_language(self):

        # Deutsch ↔ English (v3.5). Wird in der
        # settings.ini persistiert; bereits sichtbare
        # Texte werden live umgeschaltet (Buttons,
        # Statusleiste, Tree-Header, Tooltips, Hilfe).
        global APP_LANG

        APP_LANG = (
            "en"
            if APP_LANG == "de"
            else "de"
        )

        SETTINGS["lang"] = APP_LANG

        save_settings(SETTINGS)

        self.lang_button.configure(
            text=(
                "Sprache: Deutsch"
                if APP_LANG == "de"
                else "Language: English"
            )
        )

        self.help_button.configure(
            text=tr("Hilfe")
        )

        self.theme_button.configure(
            text=(
                tr("Design: ")
                + self.theme.name
            )
        )

        self.switch_button.configure(
            text=(
                tr("Bereich: ")
                + self.get_registry_display_name()
            )
        )

        self.tree.heading(
            "#0",
            text=tr("Eintrag")
        )

        self.tree.heading(
            "info",
            text=tr("Details / Pfad")
        )

        admin_text = (
            "Administrator: Ja"
            if is_admin()
            else
            "Administrator: Nein "
            "(Schreibrechte eventuell eingeschränkt!)"
        )

        self.status_label.configure(
            text=(
                f"{self.get_registry_title()}   |   "
                f"{tr(admin_text)}"
            )
        )

        ToolTip.retranslate_all()

        # Offenen Hilfe-Dialog in der neuen
        # Sprache neu aufbauen — aber NUR wenn
        # er tatsächlich offen war (v4.5-Fix:
        # vorher wurde die Hilfe bei jedem
        # Sprach-Button-Klick geöffnet, sobald
        # sie einmal geöffnet gewesen war).
        help_dialog = getattr(
            self,
            "_help_dialog",
            None
        )

        was_open = False

        if help_dialog is not None:

            try:

                if help_dialog.winfo_exists():

                    help_dialog.destroy()
                    was_open = True

            except tk.TclError:
                pass

        if was_open:

            self.show_help_dialog()

    def _rebuild_toolbar_icons(self):

        for button in self.toolbar_buttons:

            try:

                button.configure(
                    image=""
                )

            except Exception:
                pass

        self.toolbar_icons.clear()

        for button in self.toolbar_buttons:

            try:

                current = button

                name = getattr(
                    current,
                    "icon_name",
                    None
                )

                if not name:
                    continue

                image = (
                    self._load_toolbar_icon(
                        name
                    )
                )

                if image:

                    current.configure(
                        image=image
                    )

                    current.image = image

            except Exception:

                pass

    # ------------------------------------------------------------------
    # Refresh
    # ------------------------------------------------------------------

    def refresh(self):

        self.tree.delete(
            *self.tree.get_children()
        )

        self.node_paths = {}
        self.tree_icon_cache = {}

        def add_nodes(
            parent_iid,
            entries,
            depth=0
        ):

            for entry in entries:

                # Anzeigename zeigen, wenn
                # vorhanden (reist beim Tausch
                # mit dem Inhalt mit); sonst
                # Schlüsselname.
                label = (
                    entry["display"]
                    or entry["name"]
                )

                prefix = (
                    "[Menü] "
                    if entry["is_menu"]
                    else
                    "[App] "
                )

                iid = (
                    f"node_"
                    f"{len(self.node_paths)}"
                )

                self.node_paths[iid] = (
                    entry["path"]
                )

                info_text = (
                    entry["path"].replace(
                        BASE_PATH + "\\",
                        ""
                    )
                )

                if entry["icon"]:

                    info_text += (
                        f"  (Icon: "
                        f"{entry['icon']})"
                    )

                if entry["is_menu"]:

                    info_text += (
                        f"  [Position: "
                        f"{entry['position']}]"
                    )

                elif (
                    BASE_PATH.lower()
                    == BASE_PATH_DESKTOP.lower()
                ):

                    info_text += (
                        f"  [Position: "
                        f"{entry['position']}]"
                    )

                # --------------------------------------------------
                # Icon-Miniatur
                # --------------------------------------------------

                image = None

                if entry["icon"]:

                    cache_key = (
                        entry["icon"],
                        self.theme.mode_index
                    )

                    if cache_key in (
                        self.tree_icon_cache
                    ):

                        image = (
                            self.tree_icon_cache[
                                cache_key
                            ]
                        )

                    else:

                        image = (
                            icon_photo_from_reference(
                                self,
                                entry["icon"],
                                size=16,
                                background=(
                                    self.theme.palette[
                                        "tree_bg"
                                    ]
                                )
                            )
                        )

                        if image:

                            self.tree_icon_cache[
                                cache_key
                            ] = image

                # --------------------------------------------------
                # WICHTIG:
                #
                # Werte mit Windows-Backslashes nicht
                # direkt über values= an insert() übergeben.
                #
                # Das verhindert den bisherigen TclError:
                # unknown option "1.Explorer..."
                # --------------------------------------------------

                insert_kwargs = {
                    "iid": iid,
                    "text": (
                        "    " * depth
                        + prefix
                        + label
                    ),
                    "open": True
                }

                if image:

                    insert_kwargs["image"] = (
                        image
                    )

                self.tree.insert(
                    parent_iid,
                    "end",
                    **insert_kwargs
                )

                # Wert erst NACH insert setzen.
                # Dadurch werden Backslashes und
                # Sonderzeichen sicher als ein Wert
                # behandelt.
                self.tree.set(
                    iid,
                    "info",
                    info_text
                )

                if entry["children"]:

                    add_nodes(
                        iid,
                        entry["children"],
                        depth + 1
                    )

        add_nodes(
            "",
            list_entries()
        )

        admin_text = (
            "Administrator: Ja"
            if is_admin()
            else
            "Administrator: Nein "
            "(Schreibrechte eventuell eingeschränkt!)"
        )

        self.status_label.configure(
            text=(
                f"{self.get_registry_title()}   |   "
                f"{tr(admin_text)}"
            )
        )

        notify_shell()

    # ------------------------------------------------------------------
    # Selection
    # ------------------------------------------------------------------

    def _selected_iid(self):

        selection = self.tree.selection()

        if not selection:

            msg_info(
                "Hinweis",
                "Bitte zuerst einen Eintrag auswählen."
            )

            return None

        return selection[0]

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def delete_selected(self):

        iid = self._selected_iid()

        if not iid:
            return

        full_path = self.node_paths.get(
            iid
        )

        if not full_path:
            return

        entry_name = full_path.rsplit(
            "\\",
            1
        )[-1]

        backup_file = None

        if is_windows_key(full_path):

            if not ask_yes_no(
                "Windows-Eintrag löschen",
                tr(
                    "Der Eintrag '{name}' ist ein "
                    "fester Windows-Eintrag.\n\n"
                    "Vor dem Löschen wird automatisch ein "
                    "Backup (.reg) unter Dokumente angelegt "
                    "(Dateiname: Schlüsselname + Datum/Uhrzeit). "
                    "Durch einfaches Ausführen dieser Datei "
                    "lässt sich der Eintrag wiederherstellen.\n\n"
                    "Eintrag wirklich löschen?"
                ).format(name=entry_name)
            ):

                return

            try:

                backup_file = (
                    self.backup_windows_entry_to_documents(
                        full_path
                    )
                )

            except Exception as error:

                msg_error(
                    "Fehler",
                    "Backup fehlgeschlagen, "
                    "Löschung abgebrochen:\n"
                    f"{error}"
                )

                return

        elif not ask_yes_no(
            "Löschen bestätigen",
            tr(
                "Eintrag '{name}' einschließlich "
                "aller Untereinträge vollständig löschen?"
            ).format(name=entry_name)
        ):

            return

        delete_snapshot = capture_subtree(
            full_path
        )

        delete_parent, delete_name = full_path.rsplit(
            "\\",
            1
        )

        try:

            deleted = delete_key_recursive(
                HIVE,
                full_path
            )

        except PermissionError:

            msg_error(
                "Fehler",
                "Zugriff verweigert. "
                "Bitte starte das Programm als Administrator neu!"
            )

            return

        except Exception as error:

            msg_error(
                "Fehler",
                f"Löschen fehlgeschlagen:\n{error}"
            )

            return

        if not deleted:

            msg_error(
                "Fehler",
                tr(
                    "Der Eintrag '{name}' konnte "
                    "nicht vollständig gelöscht werden "
                    "(Schreibschutz/Rechte)."
                ).format(name=entry_name)
            )

            return

        self._push_undo(
            [
                (
                    "restore",
                    delete_parent,
                    delete_name,
                    delete_snapshot,
                    None
                )
            ]
        )

        self.refresh()

        if backup_file:

            msg_info(
                "Backup erstellt",
                tr(
                    "Windows-Eintrag gelöscht.\n\n"
                    "Backup wurde angelegt:\n\n"
                    "{file}\n\n"
                    "Ausführen dieser Datei stellt den "
                    "Eintrag wieder her."
                ).format(file=backup_file)
            )

    def backup_windows_entry_to_documents(
        self,
        registry_path
    ):

        # Exportiert einen Schlüssel als .reg
        # in den Dokumente-Ordner des Benutzers
        # (vor dem Löschen fester Windows-
        # Einträge).
        documents = os.path.join(
            os.path.expanduser("~"),
            "Documents"
        )

        if not os.path.isdir(documents):

            documents = os.path.expanduser(
                "~"
            )

        entry_name = registry_path.rsplit(
            "\\",
            1
        )[-1]

        file_name = (
            f"{entry_name}_backup_"
            f"{time.strftime('%Y%m%d_%H%M%S')}.reg"
        )

        target = os.path.join(
            documents,
            file_name
        )

        text = self.registry_export_text(
            registry_path
        )

        with open(
            target,
            "w",
            encoding="utf-16"
        ) as file:

            file.write(text)

        return target

    # ------------------------------------------------------------------
    # Undo
    # ------------------------------------------------------------------

    def _push_undo(self, ops):

        if self._undoing:
            return

        self.undo_stack.append(ops)

        if len(self.undo_stack) > 10:

            self.undo_stack.pop(0)

    def _record_restore(
        self,
        path,
        cleanup_path=None
    ):

        # Macht eine vorangegangene Änderung
        # eines Schlüssels über einen Snapshot
        # des Urzustands rückgängig machbar.
        parent_path, name = path.rsplit(
            "\\",
            1
        )

        snapshot = capture_subtree(path)

        self._push_undo(
            [
                (
                    "restore",
                    parent_path,
                    name,
                    snapshot,
                    cleanup_path
                )
            ]
        )

    def undo_last(self):

        if not self.undo_stack:

            msg_info(
                "Rückgängig",
                "Keine Änderungen zum "
                "Rückgängig machen."
            )

            return

        ops = self.undo_stack.pop()

        self._undoing = True

        try:

            for op in ops:

                kind = op[0]

                if kind == "create":

                    delete_key_recursive(
                        HIVE,
                        op[1]
                    )

                elif kind == "restore":

                    _, parent_path, name, snapshot, cleanup = op

                    target_path = (
                        f"{parent_path}\\{name}"
                    )

                    # Aktuellen (geänderten)
                    # Zustand entfernen: erst das
                    # Cleanup-Ziel (z. B. neuer Pfad
                    # nach Umbenennung), dann den
                    # Wiederherstellungspfad selbst.
                    if (
                        cleanup
                        and cleanup.lower()
                        != target_path.lower()
                        and key_exists(cleanup)
                    ):

                        delete_key_recursive(
                            HIVE,
                            cleanup
                        )

                    if key_exists(target_path):

                        delete_key_recursive(
                            HIVE,
                            target_path
                        )

                    restore_subtree(
                        parent_path,
                        name,
                        snapshot
                    )

        except Exception as error:

            msg_error(
                "Fehler",
                f"Rückgängig fehlgeschlagen:\n{error}"
            )

        finally:

            self._undoing = False

        notify_shell()
        self.refresh()

    # ------------------------------------------------------------------
    # Shutdown-Menü (Ein-Klick-Anlage)
    # ------------------------------------------------------------------

    def create_shutdown_menu(self):

        # Legt das Shutdown-Menü im aktuell
        # gewählten Bereich an bzw. ergänzt es
        # (idempotent): Anzeigename
        # "Shutdown Menü", Untereinträge
        # 1.Neustart / 2.Herunterfahren /
        # 3.Abmelden. Vorhandene Befehle werden
        # NICHT geändert, fehlende Icon-Werte
        # werden normiert.
        created = []
        updated = []
        ops = []

        menu_path = (
            f"{BASE_PATH}\\{SHUTDOWN_MENU_KEY}"
        )

        shell_path = f"{menu_path}\\shell"

        try:

            if not key_exists(menu_path):

                create_menu_entry(
                    SHUTDOWN_MENU_KEY,
                    SHUTDOWN_MENU_ICON,
                    "Bottom"
                )

                created.append(
                    SHUTDOWN_MENU_DISPLAY
                )

                # Platzhalter "leer" des leeren
                # Menüs entfernen, da sofort echte
                # Untereinträge angelegt werden.
                leer_path = f"{shell_path}\\leer"

                if key_exists(leer_path):

                    delete_key_recursive(
                        HIVE,
                        leer_path
                    )

            # Anzeigename über MUIVerb (kanonischer
            # Wert für Kaskaden-Menüs). Der
            # (Standard)-Wert bleibt leer — ein
            # gefüllter (Standard) neben SubCommands
            # hatte den Explorer-Menüaufbau gestört.
            display, icon = (
                read_default_and_icon(menu_path)
            )

            mui = read_mui_verb(menu_path)

            if mui != SHUTDOWN_MENU_DISPLAY:

                with winreg.OpenKey(
                    HIVE,
                    menu_path,
                    0,
                    winreg.KEY_WRITE
                ) as key:

                    winreg.SetValueEx(
                        key,
                        "MUIVerb",
                        0,
                        winreg.REG_SZ,
                        SHUTDOWN_MENU_DISPLAY
                    )

                updated.append(
                    "MUIVerb: " + SHUTDOWN_MENU_DISPLAY
                )

            if display is not None:

                # (Standard)-Wert am Menü-Schlüssel
                # KOMPLETT entfernen — auch wenn er
                # nur leer existiert (v4.3): genau
                # dieser leere Wert (create_menu_entry
                # legt ihn an) unterschied die kaputte
                # Struktur von der funktionierenden
                # Vorlage ohne (Standard)-Wert. Anzeige
                # läuft über MUIVerb bzw. Schlüsselnamen.
                try:

                    with winreg.OpenKey(
                        HIVE,
                        menu_path,
                        0,
                        winreg.KEY_WRITE
                    ) as key:

                        winreg.DeleteValue(
                            key,
                            None
                        )

                    updated.append(
                        "(Standard) entfernt"
                    )

                except OSError:

                    pass

            # Shutdown-Menü IMMER unten fixieren.
            if read_position(menu_path) != "Bottom":

                with winreg.OpenKey(
                    HIVE,
                    menu_path,
                    0,
                    winreg.KEY_WRITE
                ) as key:

                    winreg.SetValueEx(
                        key,
                        "Position",
                        0,
                        winreg.REG_SZ,
                        "Bottom"
                    )

                updated.append(
                    "Position: Bottom"
                )

            if icon != SHUTDOWN_MENU_ICON:

                with winreg.OpenKey(
                    HIVE,
                    menu_path,
                    0,
                    winreg.KEY_WRITE
                ) as key:

                    winreg.SetValueEx(
                        key,
                        "Icon",
                        0,
                        winreg.REG_SZ,
                        SHUTDOWN_MENU_ICON
                    )

                updated.append("Icon: Menü")

            # Untereinträge anlegen bzw. ergänzen.
            for (
                name,
                command,
                icon
            ) in SHUTDOWN_ENTRIES:

                entry_path = (
                    f"{shell_path}\\{name}"
                )

                if not key_exists(entry_path):

                    create_app_entry(
                        name,
                        icon,
                        command,
                        shell_path
                    )

                    created.append(name)

                    continue

                entry_display, entry_icon = (
                    read_default_and_icon(
                        entry_path
                    )
                )

                if entry_icon != icon:

                    # Vorher Snapshot für Undo
                    # sichern.
                    ops.append(
                        (
                            "restore",
                            shell_path,
                            name,
                            capture_subtree(
                                entry_path
                            ),
                            None
                        )
                    )

                    with winreg.OpenKey(
                        HIVE,
                        entry_path,
                        0,
                        winreg.KEY_WRITE
                    ) as key:

                        winreg.SetValueEx(
                            key,
                            "Icon",
                            0,
                            winreg.REG_SZ,
                            icon
                        )

                    updated.append(
                        f"Icon: {name}"
                    )

                if not has_subkey(
                    entry_path,
                    "command"
                ):

                    with winreg.CreateKeyEx(
                        HIVE,
                        f"{entry_path}\\command",
                        0,
                        winreg.KEY_READ
                        | winreg.KEY_WRITE
                    ) as command_key:

                        winreg.SetValueEx(
                            command_key,
                            None,
                            0,
                            winreg.REG_SZ,
                            format_command(
                                command
                            )
                        )

                    updated.append(
                        f"Befehl: {name}"
                    )

                else:

                    # Alte Fehlspeicherung heilen:
                    # war der Vorlagen-Befehl als
                    # Ganzes in Anführungszeichen
                    # gesetzt ("shutdown.exe /r /t 0"),
                    # war er unausführbar. Nur solcher
                    # Müll wird korrigiert — eigene
                    # Befehle des Nutzers bleiben
                    # unangetastet.
                    current = read_command(
                        entry_path
                    ).strip()

                    if (
                        current.startswith('"')
                        and current.endswith('"')
                        and len(current) > 1
                        and current[1:-1].strip()
                        == command
                    ):

                        with winreg.OpenKey(
                            HIVE,
                            f"{entry_path}\\command",
                            0,
                            winreg.KEY_WRITE
                        ) as command_key:

                            winreg.SetValueEx(
                                command_key,
                                None,
                                0,
                                winreg.REG_SZ,
                                command
                            )

                        updated.append(
                            f"Befehl korrigiert: "
                            f"{name}"
                        )

            if not key_exists(shell_path):

                # Bestehender Eintrag ohne
                # Menü-Struktur: shell anlegen,
                # damit die Untereinträge greifen.
                with winreg.CreateKeyEx(
                    HIVE,
                    shell_path,
                    0,
                    winreg.KEY_READ
                    | winreg.KEY_WRITE
                ):
                    pass

            # SubCommands bleibt LEER (Platzhalter
            # von create_menu_entry) — exakt wie in
            # der funktionierenden Vorlage des
            # Nutzers: der Explorer enumeriert die
            # Kinder unter shell selbst. Ein Füllen
            # (v4.2-Versuch) wurde zurückgenommen.

        except Exception as error:

            msg_error(
                "Fehler",
                "Shutdown-Menü konnte nicht "
                f"angelegt werden:\n{error}"
            )

            return

        if created or updated:

            # Undo-Eintrag: alle neu angelegten
            # Teile werden beim Rückgängig-Machen
            # entfernt (Reihenfolge: außen zuerst).
            if (
                SHUTDOWN_MENU_DISPLAY
                in created
            ):

                ops.append(
                    ("create", menu_path)
                )

            for (
                name,
                _command,
                _icon
            ) in SHUTDOWN_ENTRIES:

                if (
                    name in created
                    and not (
                        SHUTDOWN_MENU_DISPLAY
                        in created
                    )
                ):

                    ops.append(
                        (
                            "create",
                            f"{shell_path}\\{name}"
                        )
                    )

            if ops:

                self._push_undo(ops)

            message_parts = []

            if created:

                message_parts.append(
                    tr("Angelegt: ")
                    + ", ".join(created)
                )

            if updated:

                message_parts.append(
                    tr("Aktualisiert: ")
                    + ", ".join(updated)
                )

            message = (
                tr(
                    "Shutdown-Menü im Bereich "
                    "{area} vorbereitet.\n\n"
                ).format(
                    area=self.get_registry_display_name()
                )
                + "\n".join(message_parts)
            )

        else:

            message = (
                "Shutdown-Menü ist bereits "
                "vollständig vorhanden — keine "
                "Änderungen nötig."
            )

        notify_shell()
        self.refresh()

        msg_info(
            "Shutdown-Menü",
            message
        )

    # ------------------------------------------------------------------
    # Verschieben (Buttons + Drag & Drop)
    # ------------------------------------------------------------------

    def move_selected(self, direction):

        selection = self.tree.selection()

        if not selection:

            msg_info(
                "Hinweis",
                "Bitte zuerst einen Eintrag auswählen."
            )

            return

        # Mehrfachauswahl: der markierte Block
        # wandert als Ganzes. Dazu wird von
        # oben nach unten (Hoch) bzw. von
        # unten nach oben (Runter) gearbeitet,
        # damit sich die Einträge nicht
        # gegenseitig überholen.
        ordered = sorted(
            selection,
            key=self.tree.index,
            reverse=(direction > 0)
        )

        moved_paths = []
        errors = []

        for iid in ordered:

            src_path = self.node_paths.get(
                iid
            )

            if not src_path:
                continue

            try:

                new_path = self._move_one_step(
                    src_path,
                    direction
                )

            except Exception as error:

                errors.append(
                    f"{src_path.rsplit(chr(92), 1)[-1]}: "
                    f"{error}"
                )

                continue

            if new_path:

                moved_paths.append(new_path)

        if moved_paths or errors:

            notify_shell()
            self.refresh()

        if errors:

            msg_error(
                "Fehler",
                "Verschieben fehlgeschlagen:\n"
                + "\n".join(errors)
            )

        if moved_paths:

            self._select_paths(moved_paths)

    def _move_one_step(
        self,
        src_path,
        direction
    ):

        # Verschiebt EINEN Eintrag um eine
        # Position in Richtung direction
        # (-1 hoch, +1 runter). Liefert den
        # neuen Pfad (oder None am Rand/keine
        # Änderung); wirft bei Fehlern.
        parent_path, name = src_path.rsplit(
            "\\",
            1
        )

        siblings = enum_subkeys(
            parent_path
        )

        if name not in siblings:

            self.refresh()
            return None

        index = siblings.index(name)

        target_index = index + direction

        if target_index < 0 or target_index >= len(siblings):

            return None

        neighbor = siblings[target_index]

        src_can = can_delete_key(src_path)
        neighbor_can = can_delete_key(
            f"{parent_path}\\{neighbor}"
        )

        if src_can and neighbor_can:

            new_path = self._swap_sibling_keys(
                parent_path,
                name,
                neighbor
            )

        elif src_can:

            # Nachbar ist schreibgeschützt
            # (Windows-Eintrag): nur den
            # eigenen Schlüssel an ihm
            # vorbei sortieren.
            new_path, snapshot = (
                reorder_key_past_neighbor(
                    parent_path,
                    name,
                    neighbor,
                    direction
                )
            )

            self._push_undo(
                [
                    (
                        "restore",
                        parent_path,
                        name,
                        snapshot,
                        new_path
                    )
                ]
            )

        elif neighbor_can:

            # Ausgewählter Eintrag selbst ist
            # geschützt: der löschbare Nachbar
            # wird auf die andere Seite
            # sortiert — Ergebnis wie Tausch.
            new_path, snapshot = (
                reorder_key_past_neighbor(
                    parent_path,
                    neighbor,
                    name,
                    -direction
                )
            )

            self._push_undo(
                [
                    (
                        "restore",
                        parent_path,
                        neighbor,
                        snapshot,
                        new_path
                    )
                ]
            )

        else:

            raise RuntimeError(
                "Beide Schlüssel sind "
                "schreibgeschützt, keine Position "
                "kann geändert werden."
            )

        return new_path

    def _swap_sibling_keys(
        self,
        parent_path,
        name_a,
        name_b
    ):

        # Tauscht die Positionen zweier
        # Geschwister-Schlüssel. Die Registry
        # liefert Schlüssel alphabetisch, daher
        # werden die Schlüsselnamen getauscht.
        # Die Anzeigenamen reisen als
        # (Standard)-Wert mit dem Inhalt mit.
        path_a = f"{parent_path}\\{name_a}"
        path_b = f"{parent_path}\\{name_b}"

        # Snapshots für Undo (vor jeder
        # Änderung einlesen).
        snapshot_a = capture_subtree(path_a)
        snapshot_b = capture_subtree(path_b)

        ensure_display_name(path_a)
        ensure_display_name(path_b)

        # Temporärer Name, der im Elternschlüssel
        # garantiert frei ist.
        counter = 1
        tmp_name = f"{name_a}__tmp__{counter}"
        tmp_path = f"{parent_path}\\{tmp_name}"

        while key_exists(tmp_path):

            counter += 1
            tmp_name = f"{name_a}__tmp__{counter}"
            tmp_path = f"{parent_path}\\{tmp_name}"

        # Transaktional tauschen: Scheitert ein
        # Schritt, wird vollständig zurückgenommen
        # und der Arbeits-Schlüssel (__tmp__)
        # garantiert entfernt — so bleiben keine
        # Überreste wie "@shell32.dll"-Kopien liegen.
        try:

            rename_key(path_a, tmp_name)

            try:

                rename_key(path_b, name_a)

            except Exception:

                # Schritt 2 fehlgeschlagen:
                # a-Inhalt aus tmp zurückholen.
                if key_exists(tmp_path):

                    rename_key(
                        tmp_path,
                        name_a
                    )

                raise

            try:

                rename_key(tmp_path, name_b)

            except Exception:

                # Schritt 3 fehlgeschlagen:
                # b-Inhalt liegt unter a, a-Inhalt
                # noch in tmp — beides zurückholen.
                if key_exists(tmp_path):

                    if key_exists(path_a):

                        rename_key(
                            path_a,
                            name_b
                        )

                    rename_key(
                        tmp_path,
                        name_a
                    )

                raise

        except Exception:

            # Sicherheitsnetz: tmp darf nie
            # übrig bleiben.
            if key_exists(tmp_path):

                delete_key_recursive(
                    HIVE,
                    tmp_path
                )

            raise

        # Der gewählte Inhalt liegt nach dem
        # Tausch unter dem Namen des Nachbarn.
        self._push_undo(
            [
                (
                    "restore",
                    parent_path,
                    name_a,
                    snapshot_a,
                    None
                ),
                (
                    "restore",
                    parent_path,
                    name_b,
                    snapshot_b,
                    None
                )
            ]
        )

        return f"{parent_path}\\{name_b}"

    def _select_path(self, path):

        for iid, node_path in (
            self.node_paths.items()
        ):

            if node_path.lower() == path.lower():

                self.tree.selection_set(iid)
                self.tree.see(iid)
                return

    def _select_paths(self, paths):

        # Mehrere Einträge nach einem
        # Mehrfach-Verschieben wieder
        # markieren.
        wanted = {
            p.lower() for p in paths
        }

        iids = [
            iid
            for iid, node_path in (
                self.node_paths.items()
            )
            if node_path.lower() in wanted
        ]

        if not iids:
            return

        self.tree.selection_set(iids)

        try:

            self.tree.see(iids[-1])

        except tk.TclError:

            pass

    def _on_tree_press(self, event):

        iid = self.tree.identify_row(
            event.y
        )

        self._drag_iid = (
            iid if iid else None
        )

        self._drag_armed = False
        self._drag_start_y = event.y
        self._drop_target_iid = None

        # Markierung JETZT sichern: Dieser
        # Handler läuft VOR dem Tk-Klassen-
        # Binding, das bei Press auf eine
        # markierte Zeile die Markierung auf
        # genau diese eine Zeile zurücksetzt
        # — sonst würde beim Ziehen immer
        # nur ein Eintrag verschoben.
        if iid and iid in self.tree.selection():

            self._drag_iids = list(
                self.tree.selection()
            )

        else:

            self._drag_iids = (
                [iid] if iid else []
            )

    def _on_tree_motion(self, event):

        if not self._drag_iid:
            return

        if not self._drag_armed:

            if abs(event.y - self._drag_start_y) < 5:
                return

            self._drag_armed = True

        try:

            self.tree.configure(
                cursor="fleur"
            )

        except tk.TclError:
            pass

        # Drop-Vorschau an der Mausposition.
        self._update_drop_preview(
            event.x,
            event.y
        )

        # Auto-Scroll (v3.8): nahe am oberen/
        # unteren Rand des Baums scrollt die
        # Liste weiter, bis Anfang/Ende erreicht
        # ist — so lassen sich auch Einträge
        # erreichen, die außerhalb des sichtbaren
        # Bereichs liegen.
        direction = 0

        height = self.tree.winfo_height()

        if event.y < DND_SCROLL_EDGE:

            if self.tree.yview()[0] > 0:
                direction = -1

        elif event.y > height - DND_SCROLL_EDGE:

            # Achtung: Tk liefert am Listen-Ende
            # yview()=(0.975, 0.35) — der zweite Wert
            # wird NICHT auf 1.0 normalisiert. Daher
            # Summe statt Einzelwert prüfen.
            if sum(self.tree.yview()) < 1:
                direction = 1

        self._start_dnd_scroll(direction)

    def _update_drop_preview(
        self,
        event_x,
        event_y
    ):

        # Einfüge-Vorschau: ein sichtbarer
        # Einfüge-Balken ZWISCHEN zwei Zeilen zeigt,
        # wo der Eintrag landet — obere Hälfte einer
        # Zeile = davor, untere Hälfte = danach.
        # Untere Hälfte eines MENÜS = in das Menü
        # hinein (dann wird die Zeile hervorgehoben).
        # Das Ziel selbst wird nie verschoben.
        target, half = self._drop_target_at(
            event_y
        )

        into_mode = False

        if target and half == "after":

            target_path = self.node_paths.get(
                target
            )

            if target_path and has_subkey(
                target_path,
                "shell"
            ):

                into_mode = True

        self._drop_into = into_mode

        state = (target, half, into_mode)

        if state == self._drop_state:
            return

        self._drop_state = state

        # Alte Zeilen-Hervorhebung entfernen.
        if self._drop_target_iid:

            try:

                self.tree.item(
                    self._drop_target_iid,
                    tags=()
                )

            except tk.TclError:
                pass

        self._drop_target_iid = target

        if not target:

            self._hide_drop_bar()
            return

        palette = self.theme.palette

        if into_mode:

            # In das Menü hinein: Zeile hervorheben,
            # kein Balken.
            self._hide_drop_bar()

            self.tree.tag_configure(
                "drop_target",
                background=palette[
                    "select_bg"
                ],
                foreground=palette[
                    "select_fg"
                ]
            )

            try:

                self.tree.item(
                    target,
                    tags=("drop_target",)
                )

            except tk.TclError:
                pass

            return

        # Einfüge-Balken an der Grenze
        # vor/hinter der Zielzeile.
        try:

            self.tree.item(
                target,
                tags=()
            )

        except tk.TclError:
            pass

        self._show_drop_bar(
            target,
            half
        )

    # Auto-Scroll während des Ziehens (v3.8)

    def _start_dnd_scroll(
        self,
        direction
    ):

        if direction == getattr(
            self,
            "_dnd_scroll_dir",
            0
        ):
            return

        self._stop_dnd_scroll()

        if not direction:
            return

        self._dnd_scroll_dir = direction

        self._dnd_scroll_step()

    def _dnd_scroll_step(self):

        # Scrollt einen Schritt weiter und aktualisiert
        # die Drop-Vorschau an der (unveränderten)
        # Mausposition — beim Halten ohne Mausbewegung
        # wandert der Balken so mit.
        direction = getattr(
            self,
            "_dnd_scroll_dir",
            0
        )

        if (
            not direction
            or not getattr(
                self,
                "_drag_armed",
                False
            )
        ):

            self._dnd_scroll_dir = 0
            self._dnd_scroll_after = None

            return

        prev_top = self.tree.yview()[0]

        try:

            self.tree.yview_scroll(
                1 if direction > 0 else -1,
                "units"
            )

        except tk.TclError:
            pass

        try:

            px, py = self.tree.winfo_pointerxy()

            self._update_drop_preview(
                px - self.tree.winfo_rootx(),
                py - self.tree.winfo_rooty()
            )

        except tk.TclError:
            pass

        # Am Ende angekommen (kein Fortschritt mehr)?
        # Tk normalisiert yview am Rand nicht zuverlässig
        # auf 1.0/0.0 — daher Fortschritts-Vergleich.
        if self.tree.yview()[0] == prev_top:

            self._stop_dnd_scroll()
            return

        self._dnd_scroll_after = self.after(
            DND_SCROLL_MS,
            self._dnd_scroll_step
        )

    def _stop_dnd_scroll(self):

        if getattr(
            self,
            "_dnd_scroll_after",
            None
        ):

            try:

                self.after_cancel(
                    self._dnd_scroll_after
                )

            except Exception:
                pass

        self._dnd_scroll_after = None
        self._dnd_scroll_dir = 0

    def _drop_target_at(
        self,
        event_y
    ):

        # Liefert (iid, "before"/"after") für die
        # Zeile unter der Maus; (None, None) auf
        # freier Fläche.
        iid = self.tree.identify_row(
            event_y
        )

        if not iid:
            return None, None

        bbox = self.tree.bbox(iid)

        if not bbox:
            return iid, "before"

        _x, y, _w, h = bbox

        return (
            iid,
            "before"
            if event_y < y + h / 2
            else "after"
        )

    def _show_drop_bar(
        self,
        iid,
        half
    ):

        # Dünner Balken (Palette select_bg) an der
        # Einfügeposition zwischen zwei Zeilen.
        palette = self.theme.palette

        if getattr(
            self,
            "_drop_bar",
            None
        ) is None:

            self._drop_bar = tk.Canvas(
                self.tree,
                height=4,
                highlightthickness=0,
                bg=palette["select_bg"]
            )

        else:

            try:

                self._drop_bar.configure(
                    bg=palette["select_bg"]
                )

            except tk.TclError:
                pass

        bbox = self.tree.bbox(iid)

        if not bbox:

            self._hide_drop_bar()
            return

        _x, y, _w, h = bbox

        gap = (
            y
            if half == "before"
            else y + h
        )

        self._drop_bar.place(
            x=0,
            y=max(0, gap - 2),
            relwidth=1
        )

    def _hide_drop_bar(self):

        bar = getattr(
            self,
            "_drop_bar",
            None
        )

        if bar is not None:

            try:

                bar.place_forget()

            except tk.TclError:
                pass

    def _on_tree_release(self, event):

        src_iid = getattr(
            self,
            "_drag_iid",
            None
        )

        armed = getattr(
            self,
            "_drag_armed",
            False
        )

        self._drag_iid = None
        self._drag_armed = False
        self._drag_start_y = None

        # Laufenden Auto-Scroll sofort beenden.
        self._stop_dnd_scroll()

        if self._drop_target_iid:

            try:

                self.tree.item(
                    self._drop_target_iid,
                    tags=()
                )

            except tk.TclError:
                pass

            self._drop_target_iid = None

        self._hide_drop_bar()
        self._drop_state = None

        try:

            self.tree.configure(
                cursor=""
            )

        except tk.TclError:
            pass

        if not src_iid or not armed:
            return

        target_iid, half = self._drop_target_at(
            event.y
        )

        # Einfügeposition: "into" (Menü, untere
        # Hälfte), sonst "before"/"after" —
        # identisch zur angezeigten Vorschau.
        position = "after"

        if target_iid:

            position = (
                "into"
                if getattr(
                    self,
                    "_drop_into",
                    False
                )
                else half
            )

        # Die beim PRESS gesicherte Markierung
        # verwenden (das Tk-Klassen-Binding hat
        # sie inzwischen auf eine Zeile
        # zurückgesetzt).
        drag_iids = getattr(
            self,
            "_drag_iids",
            []
        ) or [src_iid]

        self._drag_iids = []

        self._handle_drop(
            drag_iids,
            target_iid if target_iid else None,
            position
        )

    def _handle_drop(
        self,
        drag_iids,
        target_iid,
        position="into"
    ):

        try:

            self._handle_drop_impl(
                drag_iids,
                target_iid,
                position
            )

        except Exception as error:

            msg_error(
                "Fehler",
                f"Verschieben fehlgeschlagen:\n{error}"
            )

    def _handle_drop_impl(
        self,
        drag_iids,
        target_iid,
        position="into"
    ):

        # Ein einzelner iid (alte Aufrufe,
        # Tests) wird verträglich verpackt.
        if isinstance(drag_iids, str):

            drag_iids = [drag_iids]

        # Pfade in Baumreihenfolge sammeln
        # (Duplikate ausfiltern).
        drag_paths = []

        for iid in sorted(
            drag_iids,
            key=self.tree.index
        ):

            path = self.node_paths.get(iid)

            if path and path not in drag_paths:

                drag_paths.append(path)

        if not drag_paths:
            return

        errors = []
        moved_paths = []

        def _level_move(src_path, target_parent):

            # In eine andere Ebene verschieben;
            # liefert neuen Pfad oder wirft.
            if src_path.lower() == target_parent.lower():
                return src_path

            src_parent, src_name = src_path.rsplit(
                "\\",
                1
            )

            if is_self_or_descendant(
                src_path,
                target_parent
            ):

                raise RuntimeError(
                    "Ein Menü kann nicht in sich "
                    "selbst oder in eines seiner "
                    "Untermenüs verschoben werden."
                )

            snapshot = capture_subtree(src_path)

            new_path = move_key(
                src_path,
                target_parent
            )

            self._push_undo(
                [
                    (
                        "restore",
                        src_parent,
                        src_name,
                        snapshot,
                        new_path
                    )
                ]
            )

            return new_path

        if target_iid is None:

            # Auf freie Fläche gezogen: die
            # komplette Markierung auf die
            # oberste Ebene verschieben.
            for src_path in drag_paths:

                if src_path.rsplit("\\", 1)[0].lower() == BASE_PATH.lower():
                    continue

                try:

                    moved_paths.append(
                        _level_move(src_path, BASE_PATH)
                    )

                except Exception as error:

                    errors.append(
                        f"{src_path.rsplit(chr(92), 1)[-1]}: "
                        f"{error}"
                    )

            self._finish_drop(moved_paths, errors)
            return

        target_path = self.node_paths.get(
            target_iid
        )

        if not target_path:
            return

        rest = [
            p for p in drag_paths
            if p.lower() != target_path.lower()
        ]

        if not rest:

            # Nur das Ziel selbst wurde gezogen.
            return

        if (
            position == "into"
            and has_subkey(
                target_path,
                "shell"
            )
        ):

            # Ziel ist ein Menü (untere Hälfte):
            # die komplette Markierung hinein
            # verschieben.
            shell_path = (
                f"{target_path}\\shell"
            )

            for src_path in rest:

                try:

                    moved_paths.append(
                        _level_move(src_path, shell_path)
                    )

                except Exception as error:

                    errors.append(
                        f"{src_path.rsplit(chr(92), 1)[-1]}: "
                        f"{error}"
                    )

            self._finish_drop(moved_paths, errors)
            return

        # Ziel ist ein Eintrag (oder obere Hälfte
        # eines Menüs): die Markierung wird VOR
        # oder HINTER dem Ziel EINGESORTIERT —
        # das Ziel selbst wird nie verschoben
        # (v3.7; ersetzt den früheren Tausch).
        target_parent = target_path.rsplit(
            "\\",
            1
        )[0]

        # "before" → oberhalb einsortieren,
        # "after"/"into"-Fallback → unterhalb.
        above = (position == "before")

        anchor = target_path.rsplit(
            "\\",
            1
        )[-1]

        items = (
            list(reversed(rest))
            if above
            else list(rest)
        )

        for src_path in items:

            name = src_path.rsplit(
                "\\",
                1
            )[-1]

            try:

                cur_path = _level_move(
                    src_path,
                    target_parent
                )

                cur_name = cur_path.rsplit(
                    "\\",
                    1
                )[-1]

                # Bereits direkt neben dem
                # Anker? Dann nur Anker
                # weiterbewegen.
                siblings = [
                    n.lower()
                    for n in enum_subkeys(
                        target_parent
                    )
                ]

                i_cur = siblings.index(
                    cur_name.lower()
                )

                i_anchor = siblings.index(
                    anchor.lower()
                )

                adjacent = (
                    i_cur == i_anchor - 1
                    if above
                    else i_cur == i_anchor + 1
                )

                if adjacent:

                    moved_paths.append(cur_path)
                    anchor = cur_name
                    continue

                new_path, snapshot = (
                    reorder_key_past_neighbor(
                        target_parent,
                        cur_name,
                        anchor,
                        -1 if above else 1
                    )
                )

                self._push_undo(
                    [
                        (
                            "restore",
                            target_parent,
                            cur_name,
                            snapshot,
                            new_path
                        )
                    ]
                )

                moved_paths.append(new_path)

                anchor = new_path.rsplit(
                    "\\",
                    1
                )[-1]

            except Exception as error:

                errors.append(
                    f"{name}: {error}"
                )

        self._finish_drop(moved_paths, errors)

    def _finish_drop(
        self,
        moved_paths,
        errors
    ):

        if moved_paths or errors:

            notify_shell()
            self.refresh()

        if errors:

            msg_error(
                "Fehler",
                "Verschieben fehlgeschlagen:\n"
                + "\n".join(errors)
            )

        if moved_paths:

            self._select_paths(moved_paths)

    # ------------------------------------------------------------------
    # Edit
    # ------------------------------------------------------------------

    def edit_selected(self):

        iid = self._selected_iid()

        if not iid:
            return

        full_path = self.node_paths.get(
            iid
        )

        if not full_path:
            return

        entry_name = full_path.rsplit(
            "\\",
            1
        )[-1]

        _, icon = read_default_and_icon(
            full_path
        )

        is_menu = has_subkey(
            full_path,
            "shell"
        )

        position = read_position(
            full_path
        )

        if is_menu:

            self._menu_dialog(
                title=(
                    tr("Menü bearbeiten: ")
                    + entry_name
                ),
                name=entry_name,
                name_editable=True,
                icon=icon,
                position=position,
                on_ok=lambda p, n, i, pos:
                self._do_update(
                    full_path,
                    n,
                    i,
                    None,
                    pos
                )
            )

        else:

            command = read_command(
                full_path
            )

            self._entry_dialog(
                title=(
                    tr("Eintrag bearbeiten: ")
                    + entry_name
                ),
                name=entry_name,
                name_editable=True,
                icon=icon,
                command=command,
                position=(
                    position
                    if BASE_PATH.lower()
                    == BASE_PATH_DESKTOP.lower()
                    else None
                ),
                on_ok=lambda p, n, i, c, pos:
                self._do_update(
                    full_path,
                    n,
                    i,
                    c,
                    pos
                )
            )

    def _do_update(
        self,
        full_path,
        new_name,
        icon,
        command,
        position=None
    ):

        try:

            clean_name = (
                new_name
                .strip()
                .replace("\\", "")
            )

            if not clean_name:

                msg_warn(
                    "Hinweis",
                    "Der Name darf nicht leer sein."
                )

                return False

            # Snapshot für Undo (vor jeder
            # Änderung einlesen).
            update_snapshot = capture_subtree(
                full_path
            )

            update_parent, update_name = full_path.rsplit(
                "\\",
                1
            )

            old_name = full_path.rsplit(
                "\\",
                1
            )[-1]

            if (
                clean_name.lower()
                != old_name.lower()
            ):

                full_path = rename_key(
                    full_path,
                    clean_name
                )

            update_entry_values(
                full_path,
                icon,
                command,
                position
            )

            if command is None:

                shell_path = (
                    f"{full_path}\\shell"
                )

                try:

                    with winreg.CreateKeyEx(
                        HIVE,
                        shell_path,
                        0,
                        winreg.KEY_READ
                        | winreg.KEY_WRITE
                    ):
                        pass

                except Exception:

                    pass

        except PermissionError:

            msg_error(
                "Fehler",
                "Zugriff verweigert. "
                "Bitte starte das Programm als Administrator neu!"
            )

            return False

        except Exception as error:

            msg_error(
                "Fehler",
                "Aktualisieren fehlgeschlagen:\n"
                f"{error}"
            )

            return False

        self._push_undo(
            [
                (
                    "restore",
                    update_parent,
                    update_name,
                    update_snapshot,
                    full_path
                )
            ]
        )

        self.refresh()

        return True

    # ------------------------------------------------------------------
    # Neuer App-Eintrag
    # ------------------------------------------------------------------

    def open_add_app_dialog(self):

        # Standard-Position „Mitte" (v3.3) — in
        # beiden Bereichen; None → Dialog zeigt
        # „Mitte" vorbefüllt an.
        self._entry_dialog(
            title=tr("Neuer Eintrag (App)"),
            name="",
            name_editable=True,
            icon="",
            command="",
            position=None,
            on_ok=self._do_create_app,
            allow_parent_selection=True
        )

    def _do_create_app(
        self,
        parent_shell_path,
        name,
        icon,
        command,
        position=None
    ):

        if not name.strip():

            msg_warn(
                "Hinweis",
                "Bitte einen Namen angeben."
            )

            return False

        if not command.strip():

            msg_warn(
                "Hinweis",
                "Bitte einen Programmpfad angeben."
            )

            return False

        try:

            create_app_entry(
                name.strip(),
                icon.strip(),
                command.strip(),
                parent_shell_path,
                position
            )

        except PermissionError:

            msg_error(
                "Fehler",
                "Zugriff verweigert. "
                "Bitte starte das Programm als Administrator neu!"
            )

            return False

        except Exception as error:

            msg_error(
                "Fehler",
                f"Anlegen fehlgeschlagen:\n{error}"
            )

            return False

        create_base = (
            parent_shell_path
            if parent_shell_path
            else BASE_PATH
        )

        self._push_undo(
            [
                (
                    "create",
                    f"{create_base}\\{name.strip()}"
                )
            ]
        )

        self.refresh()

        return True

    # ------------------------------------------------------------------
    # Neues Menü
    # ------------------------------------------------------------------

    def open_add_menu_dialog(self):

        # Standard-Position „Mitte" (v3.3).
        self._menu_dialog(
            title=tr("Neues Menü"),
            name="",
            name_editable=True,
            icon="",
            position="Mitte",
            on_ok=self._do_create_menu,
            allow_parent_selection=True
        )

    def _do_create_menu(
        self,
        parent_shell_path,
        name,
        icon,
        position
    ):

        if not name.strip():

            msg_warn(
                "Hinweis",
                "Bitte einen Namen angeben."
            )

            return False

        try:

            create_menu_entry(
                name.strip(),
                icon.strip(),
                position,
                parent_shell_path
            )

        except PermissionError:

            msg_error(
                "Fehler",
                "Zugriff verweigert. "
                "Bitte starte das Programm als Administrator neu!"
            )

            return False

        except Exception as error:

            msg_error(
                "Fehler",
                f"Anlegen fehlgeschlagen:\n{error}"
            )

            return False

        create_base = (
            parent_shell_path
            if parent_shell_path
            else BASE_PATH
        )

        self._push_undo(
            [
                (
                    "create",
                    f"{create_base}\\{name.strip()}"
                )
            ]
        )

        self.refresh()

        return True

    # ------------------------------------------------------------------
    # Menüeintrag
    # ------------------------------------------------------------------

    def open_add_menu_item_dialog(self):

        menus = (
            get_all_menu_shell_paths()
            if winreg
            else []
        )

        if not menus:

            msg_info(
                "Hinweis",
                "Es existiert noch kein Menü. "
                "Bitte zuerst ein Menü anlegen."
            )

            return

        self._entry_dialog(
            title=tr("Neuer Eintrag (in Menü)"),
            name="",
            name_editable=True,
            icon="",
            command="",
            position=None,
            on_ok=self._do_create_menu_item,
            menu_select=menus
        )

    def _do_create_menu_item(
        self,
        parent_shell_path,
        name,
        icon,
        command,
        position=None
    ):

        if not parent_shell_path:

            msg_warn(
                "Hinweis",
                "Bitte ein Menü auswählen."
            )

            return False

        if not name.strip():

            msg_warn(
                "Hinweis",
                "Bitte einen Namen angeben."
            )

            return False

        if not command.strip():

            msg_warn(
                "Hinweis",
                "Bitte einen Programmpfad angeben."
            )

            return False

        try:

            create_app_entry(
                name.strip(),
                icon.strip(),
                command.strip(),
                parent_shell_path,
                position
            )

        except PermissionError:

            msg_error(
                "Fehler",
                "Zugriff verweigert. "
                "Bitte starte das Programm als Administrator neu!"
            )

            return False

        except Exception as error:

            msg_error(
                "Fehler",
                f"Anlegen fehlgeschlagen:\n{error}"
            )

            return False

        self._push_undo(
            [
                (
                    "create",
                    f"{parent_shell_path}\\{name.strip()}"
                )
            ]
        )

        self.refresh()

        return True

    # ------------------------------------------------------------------
    # Entry Dialog
    # ------------------------------------------------------------------

    def _entry_dialog(
        self,
        title,
        name,
        name_editable,
        icon,
        command,
        on_ok,
        menu_select=None,
        allow_parent_selection=False,
        position=None
    ):

        dialog = tk.Toplevel(
            self
        )

        dialog.title(
            title
        )

        dialog.transient(
            self
        )

        dialog.grab_set()

        self.theme.register(
            dialog
        )

        frame = ttk.Frame(
            dialog,
            padding=12
        )

        frame.pack(
            fill="both",
            expand=True
        )

        row = 0

        parent_var = None
        menu_dict = {}

        if (
            menu_select is not None
            or allow_parent_selection
        ):

            if allow_parent_selection:

                options = [
                    (
                        tr("(Hauptebene)"),
                        None
                    )
                ] + get_all_menu_shell_paths()

            else:

                options = menu_select

            menu_dict = {
                label: path
                for label, path in options
            }

            ttk.Label(
                frame,
                text=tr("Übergeordnetes Menü:")
            ).grid(
                row=row,
                column=0,
                sticky="w",
                pady=4
            )

            parent_var = tk.StringVar(
                value=options[0][0]
            )

            combo = ttk.Combobox(
                frame,
                textvariable=parent_var,
                values=list(
                    menu_dict.keys()
                ),
                state="readonly",
                width=35
            )

            combo.grid(
                row=row,
                column=1,
                columnspan=2,
                sticky="we",
                pady=4
            )

            row += 1

        ttk.Label(
            frame,
            text=tr("Name:")
        ).grid(
            row=row,
            column=0,
            sticky="w",
            pady=4
        )

        name_var = tk.StringVar(
            value=name
        )

        name_entry = ttk.Entry(
            frame,
            textvariable=name_var,
            width=40
        )

        name_entry.grid(
            row=row,
            column=1,
            columnspan=2,
            sticky="we",
            pady=4
        )

        if not name_editable:

            name_entry.configure(
                state="readonly"
            )

        row += 1

        ttk.Label(
            frame,
            text=tr("Icon (.ico/.exe):")
        ).grid(
            row=row,
            column=0,
            sticky="w",
            pady=4
        )

        icon_var = tk.StringVar(
            value=icon
        )

        icon_entry = ttk.Entry(
            frame,
            textvariable=icon_var,
            width=32
        )

        icon_entry.grid(
            row=row,
            column=1,
            sticky="we",
            pady=4
        )

        ttk.Button(
            frame,
            text="...",
            width=3,
            command=lambda:
            self._browse(
                icon_var,
                [
                    (
                        tr("Icons/Programme"),
                        "*.ico;*.exe"
                    ),
                    (
                        tr("Alle Dateien"),
                        "*.*"
                    )
                ]
            )
        ).grid(
            row=row,
            column=2,
            padx=(4, 0),
            pady=4
        )

        row += 1

        # --------------------------------------------------------------
        # Programmpfad
        # --------------------------------------------------------------

        command_var = None

        if command is not None:

            ttk.Label(
                frame,
                text=tr("Programmpfad:")
            ).grid(
                row=row,
                column=0,
                sticky="w",
                pady=4
            )

            command_var = tk.StringVar(
                value=command
            )

            ttk.Entry(
                frame,
                textvariable=command_var,
                width=32
            ).grid(
                row=row,
                column=1,
                sticky="we",
                pady=4
            )

            ttk.Button(
                frame,
                text="...",
                width=3,
                command=lambda:
                self._browse(
                    command_var,
                    [
                        (
                            "Programme",
                            "*.exe;*.bat;*.cmd"
                        ),
                        (
                            tr("Alle Dateien"),
                            "*.*"
                        )
                    ]
                )
            ).grid(
                row=row,
                column=2,
                padx=(4, 0),
                pady=4
            )

            row += 1

        # Positions-Auswahl IMMER anzeigen,
        # vorbelegt mit „Mitte" (Standard seit
        # v3.3); None im Aufruf ist ebenfalls
        # „Mitte".
        ttk.Label(
            frame,
            text=tr("Position:")
        ).grid(
            row=row,
            column=0,
            sticky="w",
            pady=4
        )

        position_var = tk.StringVar(
            value=(
                tr(position)
                if position in ("Top", "Bottom", "Mitte")
                else tr("Mitte")
            )
        )

        ttk.Combobox(
            frame,
            textvariable=position_var,
            values=position_display_values(),
            state="readonly",
            width=15
        ).grid(
            row=row,
            column=1,
            sticky="w",
            pady=4
        )

        row += 1

        buttons = ttk.Frame(
            frame
        )

        buttons.grid(
            row=row,
            column=0,
            columnspan=3,
            sticky="e",
            pady=(12, 0)
        )

        def confirm():

            cmd_val = (
                command_var.get()
                if command_var is not None
                else None
            )

            p_path = (
                menu_dict.get(
                    parent_var.get()
                )
                if parent_var
                else None
            )

            pos_val = (
                position_from_display(
                    position_var.get()
                )
                if position_var is not None
                else None
            )

            result = on_ok(
                p_path,
                name_var.get(),
                icon_var.get(),
                cmd_val,
                pos_val
            )

            if result is not False:

                dialog.destroy()

        ttk.Button(
            buttons,
            text=tr("OK"),
            command=confirm
        ).pack(
            side="right",
            padx=4
        )

        ttk.Button(
            buttons,
            text=tr("Abbrechen"),
            command=dialog.destroy
        ).pack(
            side="right"
        )

        frame.columnconfigure(
            1,
            weight=1
        )

        self.theme.apply()

        name_entry.focus_set()

    # ------------------------------------------------------------------
    # Menü Dialog
    # ------------------------------------------------------------------

    def _menu_dialog(
        self,
        title,
        name,
        name_editable,
        icon,
        on_ok,
        allow_parent_selection=False,
        position="Bottom"
    ):

        dialog = tk.Toplevel(
            self
        )

        dialog.title(
            title
        )

        dialog.transient(
            self
        )

        dialog.grab_set()

        self.theme.register(
            dialog
        )

        frame = ttk.Frame(
            dialog,
            padding=12
        )

        frame.pack(
            fill="both",
            expand=True
        )

        row = 0

        parent_var = None
        menu_dict = {}

        if allow_parent_selection:

            options = [
                (
                    tr("(Hauptebene)"),
                    None
                )
            ] + get_all_menu_shell_paths()

            menu_dict = {
                label: path
                for label, path in options
            }

            ttk.Label(
                frame,
                text=tr("Übergeordnetes Menü:")
            ).grid(
                row=row,
                column=0,
                sticky="w",
                pady=4
            )

            parent_var = tk.StringVar(
                value=options[0][0]
            )

            ttk.Combobox(
                frame,
                textvariable=parent_var,
                values=list(
                    menu_dict.keys()
                ),
                state="readonly",
                width=35
            ).grid(
                row=row,
                column=1,
                columnspan=2,
                sticky="we",
                pady=4
            )

            row += 1

        ttk.Label(
            frame,
            text=tr("Name:")
        ).grid(
            row=row,
            column=0,
            sticky="w",
            pady=4
        )

        name_var = tk.StringVar(
            value=name
        )

        name_entry = ttk.Entry(
            frame,
            textvariable=name_var,
            width=40
        )

        name_entry.grid(
            row=row,
            column=1,
            columnspan=2,
            sticky="we",
            pady=4
        )

        if not name_editable:

            name_entry.configure(
                state="readonly"
            )

        row += 1

        ttk.Label(
            frame,
            text=tr("Icon (optional):")
        ).grid(
            row=row,
            column=0,
            sticky="w",
            pady=4
        )

        icon_var = tk.StringVar(
            value=icon
        )

        ttk.Entry(
            frame,
            textvariable=icon_var,
            width=32
        ).grid(
            row=row,
            column=1,
            sticky="we",
            pady=4
        )

        ttk.Button(
            frame,
            text="...",
            width=3,
            command=lambda:
            self._browse(
                icon_var,
                [
                    (
                        tr("Icons/Programme"),
                        "*.ico;*.exe"
                    ),
                    (
                        tr("Alle Dateien"),
                        "*.*"
                    )
                ]
            )
        ).grid(
            row=row,
            column=2,
            padx=(4, 0),
            pady=4
        )

        row += 1

        ttk.Label(
            frame,
            text=tr("Position:")
        ).grid(
            row=row,
            column=0,
            sticky="w",
            pady=4
        )

        position_var = tk.StringVar(
            value=(
                tr(position)
                if position in ("Top", "Bottom", "Mitte")
                else tr("Mitte")
            )
        )

        ttk.Combobox(
            frame,
            textvariable=position_var,
            values=position_display_values(),
            state="readonly",
            width=15
        ).grid(
            row=row,
            column=1,
            sticky="w",
            pady=4
        )

        row += 1

        buttons = ttk.Frame(
            frame
        )

        buttons.grid(
            row=row,
            column=0,
            columnspan=3,
            sticky="e",
            pady=(12, 0)
        )

        def confirm():

            p_path = (
                menu_dict.get(
                    parent_var.get()
                )
                if parent_var
                else None
            )

            result = on_ok(
                p_path,
                name_var.get(),
                icon_var.get(),
                position_from_display(
                    position_var.get()
                )
            )

            if result is not False:

                dialog.destroy()

        ttk.Button(
            buttons,
            text=tr("OK"),
            command=confirm
        ).pack(
            side="right",
            padx=4
        )

        ttk.Button(
            buttons,
            text=tr("Abbrechen"),
            command=dialog.destroy
        ).pack(
            side="right"
        )

        frame.columnconfigure(
            1,
            weight=1
        )

        self.theme.apply()

        name_entry.focus_set()

    # ------------------------------------------------------------------
    # Browse
    # ------------------------------------------------------------------

    def _browse(
        self,
        variable,
        filetypes
    ):

        path = filedialog.askopenfilename(
            filetypes=filetypes
        )

        if path:

            variable.set(
                path.replace(
                    "/",
                    "\\"
                )
            )

    # ------------------------------------------------------------------
    # Backup
    # ------------------------------------------------------------------

    def choose_backup_directory(self):

        current = SETTINGS.get(
            "backup_path",
            ""
        )

        initial = (
            current
            if os.path.isdir(current)
            else os.path.expanduser("~")
        )

        path = filedialog.askdirectory(
            title=tr("Standard-Speicherpfad für Backups"),
            initialdir=initial
        )

        if path:

            SETTINGS["backup_path"] = (
                path
            )

            save_settings(
                SETTINGS
            )

            return path

        return ""

    def get_backup_directory(self):

        path = SETTINGS.get(
            "backup_path",
            ""
        )

        if (
            not path
            or not os.path.isdir(path)
        ):

            path = (
                self.choose_backup_directory()
            )

        return path

    def backup_settings_dialog(self):

        dialog = tk.Toplevel(
            self
        )

        dialog.title(
            "Backup-Einstellungen"
        )

        dialog.transient(
            self
        )

        dialog.grab_set()

        self.theme.register(
            dialog
        )

        frame = ttk.Frame(
            dialog,
            padding=15
        )

        frame.pack(
            fill="both",
            expand=True
        )

        ttk.Label(
            frame,
            text=tr("Standard Speicherpfad:")
        ).grid(
            row=0,
            column=0,
            sticky="w",
            pady=5
        )

        path_var = tk.StringVar(
            value=SETTINGS.get(
                "backup_path",
                ""
            )
        )

        ttk.Entry(
            frame,
            textvariable=path_var,
            width=55
        ).grid(
            row=0,
            column=1,
            padx=5,
            pady=5
        )

        ttk.Button(
            frame,
            text=tr("Auswählen..."),
            command=lambda:
            self._choose_path_to_var(
                path_var
            )
        ).grid(
            row=0,
            column=2,
            pady=5
        )

        def save():

            path = path_var.get().strip()

            if path and not os.path.isdir(path):

                try:

                    os.makedirs(
                        path,
                        exist_ok=True
                    )

                except Exception as error:

                    msg_error(
                        "Fehler",
                        "Pfad konnte nicht erstellt werden:\n"
                        f"{error}",
                        parent=dialog
                    )

                    return

            SETTINGS["backup_path"] = (
                path
            )

            save_settings(
                SETTINGS
            )

            dialog.destroy()

        buttons = ttk.Frame(
            frame
        )

        buttons.grid(
            row=1,
            column=0,
            columnspan=3,
            sticky="e",
            pady=(15, 0)
        )

        ttk.Button(
            buttons,
            text=tr("Speichern"),
            command=save
        ).pack(
            side="right",
            padx=4
        )

        ttk.Button(
            buttons,
            text=tr("Abbrechen"),
            command=dialog.destroy
        ).pack(
            side="right"
        )

        self.theme.apply()

    def _choose_path_to_var(
        self,
        variable
    ):

        current = variable.get()

        initial = (
            current
            if os.path.isdir(current)
            else os.path.expanduser("~")
        )

        path = filedialog.askdirectory(
            title=tr("Ordner auswählen"),
            initialdir=initial
        )

        if path:

            variable.set(
                path
            )

    def registry_export_text(
        self,
        registry_path
    ):

        try:

            result = subprocess.run(
                [
                    "reg",
                    "export",
                    rf"HKCR\{registry_path}",
                    "-",
                    "/y"
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=0x08000000
            )

            if result.returncode != 0:

                raise RuntimeError(
                    result.stderr.strip()
                    or
                    "reg.exe konnte den Schlüssel "
                    "nicht exportieren."
                )

            return result.stdout

        except Exception as error:

            raise RuntimeError(
                str(error)
            )

    def backup_single(
        self,
        registry_path,
        default_filename
    ):

        directory = (
            self.get_backup_directory()
        )

        if not directory:
            return

        target = (
            filedialog.asksaveasfilename(
                title=tr("Backup speichern"),
                initialdir=directory,
                initialfile=default_filename,
                defaultextension=".reg",
                filetypes=[
                    (
                        tr("Registry-Datei"),
                        "*.reg"
                    ),
                    (
                        tr("Alle Dateien"),
                        "*.*"
                    )
                ]
            )
        )

        if not target:
            return

        try:

            text = (
                self.registry_export_text(
                    registry_path
                )
            )

            with open(
                target,
                "w",
                encoding="utf-16"
            ) as file:

                file.write(
                    text
                )

            SETTINGS["backup_path"] = (
                os.path.dirname(target)
            )

            save_settings(
                SETTINGS
            )

            msg_info(
                "Backup erstellt",
                "Backup wurde erstellt:\n\n"
                f"{target}"
            )

        except Exception as error:

            msg_error(
                "Backup-Fehler",
                "Backup konnte nicht erstellt werden:\n\n"
                f"{error}"
            )

    def backup_both_separate(self):

        directory = (
            self.get_backup_directory()
        )

        if not directory:
            return

        targets = []

        target_directory = (
            filedialog.asksaveasfilename(
                title=(
                    tr("Directory-Background Backup speichern")
                ),
                initialdir=directory,
                initialfile=(
                    "Directory_Background_Shell.reg"
                ),
                defaultextension=".reg",
                filetypes=[
                    (
                        tr("Registry-Datei"),
                        "*.reg"
                    ),
                    (
                        tr("Alle Dateien"),
                        "*.*"
                    )
                ]
            )
        )

        if not target_directory:
            return

        targets.append(
            (
                BASE_PATH_DIRECTORY,
                target_directory
            )
        )

        target_desktop = (
            filedialog.asksaveasfilename(
                title=(
                    tr("DesktopBackground Backup speichern")
                ),
                initialdir=(
                    os.path.dirname(
                        target_directory
                    )
                ),
                initialfile=(
                    "DesktopBackground_Shell.reg"
                ),
                defaultextension=".reg",
                filetypes=[
                    (
                        tr("Registry-Datei"),
                        "*.reg"
                    ),
                    (
                        tr("Alle Dateien"),
                        "*.*"
                    )
                ]
            )
        )

        if not target_desktop:
            return

        targets.append(
            (
                BASE_PATH_DESKTOP,
                target_desktop
            )
        )

        created = []

        try:

            for registry_path, target in targets:

                text = (
                    self.registry_export_text(
                        registry_path
                    )
                )

                with open(
                    target,
                    "w",
                    encoding="utf-16"
                ) as file:

                    file.write(
                        text
                    )

                created.append(
                    target
                )

            SETTINGS["backup_path"] = (
                os.path.dirname(
                    created[-1]
                )
            )

            save_settings(
                SETTINGS
            )

            msg_info(
                "Backup erstellt",
                "Beide Registry-Bereiche wurden "
                "separat gesichert:\n\n"
                + "\n".join(
                    created
                )
            )

        except Exception as error:

            msg_error(
                "Backup-Fehler",
                "Backup konnte nicht vollständig "
                "erstellt werden:\n\n"
                f"{error}"
            )

    def backup_combined(self):

        directory = (
            self.get_backup_directory()
        )

        if not directory:
            return

        target = (
            filedialog.asksaveasfilename(
                title=tr("Gemeinsames Backup speichern"),
                initialdir=directory,
                initialfile="backup.reg",
                defaultextension=".reg",
                filetypes=[
                    (
                        tr("Registry-Datei"),
                        "*.reg"
                    ),
                    (
                        tr("Alle Dateien"),
                        "*.*"
                    )
                ]
            )
        )

        if not target:
            return

        try:

            directory_text = (
                self.registry_export_text(
                    BASE_PATH_DIRECTORY
                )
            )

            desktop_text = (
                self.registry_export_text(
                    BASE_PATH_DESKTOP
                )
            )

            def strip_header(text):

                lines = (
                    text.splitlines()
                )

                while lines and (
                    lines[0].strip()
                    ==
                    "Windows Registry Editor Version 5.00"
                ):

                    lines.pop(0)

                while lines and not lines[0].strip():

                    lines.pop(0)

                return "\n".join(
                    lines
                )

            combined = (
                "Windows Registry Editor Version 5.00\n\n"
                +
                strip_header(
                    directory_text
                )
                +
                "\n\n"
                +
                strip_header(
                    desktop_text
                )
                +
                "\n"
            )

            with open(
                target,
                "w",
                encoding="utf-16"
            ) as file:

                file.write(
                    combined
                )

            SETTINGS["backup_path"] = (
                os.path.dirname(target)
            )

            save_settings(
                SETTINGS
            )

            msg_info(
                "Backup erstellt",
                "Gemeinsames Backup wurde erstellt:\n\n"
                f"{target}"
            )

        except Exception as error:

            msg_error(
                "Backup-Fehler",
                "Backup konnte nicht erstellt werden:\n\n"
                f"{error}"
            )

    def backup_current(self):

        if (
            BASE_PATH.lower()
            == BASE_PATH_DIRECTORY.lower()
        ):

            self.backup_single(
                BASE_PATH_DIRECTORY,
                "Directory_Background_Shell.reg"
            )

        else:

            self.backup_single(
                BASE_PATH_DESKTOP,
                "DesktopBackground_Shell.reg"
            )

    # ------------------------------------------------------------------
    # Erststart-Backup
    # ------------------------------------------------------------------

    def first_start_backup(self):

        if SETTINGS.get(
            "first_run_backup_done",
            "0"
        ) == "1":

            return

        # Einstellung sofort setzen, damit die Frage
        # nicht bei jedem Programmstart erneut kommt,
        # selbst wenn der Benutzer das Backup abbricht.
        SETTINGS[
            "first_run_backup_done"
        ] = "1"

        save_settings(
            SETTINGS
        )

        answer = ask_yes_no(
            "Erststart – vollständiges Backup",
            "Soll vor der ersten Verwendung ein vollständiges "
            "Backup der beiden Registry-Bereiche erstellt werden?\n\n"
            "JA = beide Bereiche separat sichern\n"
            "NEIN = kein Erststart-Backup erstellen"
        )

        if answer:

            self.backup_both_separate()


# ----------------------------------------------------------------------
# Programmstart
# ----------------------------------------------------------------------

def relaunch_as_admin():

    # Startet das Tool per UAC-Abfrage neu
    # (ShellExecuteW "runas") — v4.4: das Programm
    # braucht Admin-Rechte und soll immer
    # erhöhrt starten. Liefert True, wenn der
    # Neustart veranlasst wurde (dann beendet
    # sich diese Instanz), sonst False (User
    # hat abgelehnt/Fehler → Start ohne Rechte
    # mit Warnung in der Statusleiste).
    if winreg is None:
        return False

    try:

        if getattr(sys, "frozen", False):

            # PyInstaller-EXE: die EXE selbst neu
            # starten.
            target = sys.executable
            params = ""

        else:

            # Script: python.exe mit Script-Pfad.
            target = sys.executable
            params = f'"{os.path.abspath(sys.argv[0])}"'

        ret = ctypes.windll.shell32.ShellExecuteW(
            None,
            "runas",
            target,
            params,
            None,
            1
        )

        return ret > 32

    except Exception:

        return False


def main():

    if winreg is None:

        root = tk.Tk()

        root.withdraw()

        msg_error(
            "Nicht unterstützt",
            "Dieses Programm greift auf die Windows-Registry zu "
            "und funktioniert nur unter Windows."
        )

        return

    # Ohne Admin-Rechte: einmal per UAC erhöht
    # neu starten (v4.4). Lehnt der Nutzer ab,
    # läuft das Tool mit Warnung weiter.
    if not is_admin() and relaunch_as_admin():
        return

    app = App()

    app.mainloop()


if __name__ == "__main__":

    main()
