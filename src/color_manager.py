import json
import os
import random

# Pfad zur JSON-Datei, in der Kategorie-Farben gespeichert werden.
# Du kannst die Datei auch in "data/" oder woanders ablegen, Hauptsache
# du definierst den korrekten Pfad:
COLORS_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "category_colors.json")


class ColorManager:
    def __init__(self):
        self.colors_file = COLORS_FILE
        self.color_map = {}
        # Du kannst hier eine Standard-Palette definieren,
        # die vorrangig verwendet wird, bevor zufällige Farben
        # generiert werden:
        self.default_palette = [
            "#9b59b6", "#e74c3c", "#3498db", "#2ecc71",
            "#f1c40f", "#27ae60", "#000000",
            "#8e44ad", "#d35400", "#2980b9", "#1abc9c",
            "#f39c12", "#2c3e50", "#16a085"
        ]
        self._load_colors()

    def _load_colors(self):
        """Versucht, vorhandene Farben aus der JSON-Datei zu laden."""
        if os.path.exists(self.colors_file):
            try:
                with open(self.colors_file, "r", encoding="utf-8") as f:
                    self.color_map = json.load(f)
            except:
                print("⚠ Could not load color map properly. Starting with empty map.")
                self.color_map = {}
        else:
            self.color_map = {}

    def _save_colors(self):
        """Speichert den aktuellen color_map-Zustand in die JSON-Datei."""
        try:
            with open(self.colors_file, "w", encoding="utf-8") as f:
                json.dump(self.color_map, f, indent=2)
        except:
            print("⚠ Could not save color_map to file.")

    def get_color_for_category(self, category: str) -> str:
        """
        Gibt die Farbe für eine Kategorie zurück. Falls sie nicht existiert,
        wird eine neue generiert und dauerhaft in die JSON-Datei geschrieben.
        """
        if category in self.color_map:
            # Kategorie schon vorhanden => gib die gespeicherte Farbe zurück
            return self.color_map[category]

        # Kategorie ist neu => neue Farbe generieren
        new_color = self._get_new_color()
        self.color_map[category] = new_color
        self._save_colors()
        return new_color

    def _get_new_color(self) -> str:
        """
        Sucht zuerst in der default_palette eine noch nicht benutzte Farbe,
        sonst erzeugt sie eine zufällige Farbe.
        """
        used_colors = set(self.color_map.values())

        # 1) Versuche eine Farbe aus der Default-Palette
        for c in self.default_palette:
            if c not in used_colors:
                return c

        # 2) Wenn alles verbraucht => generiere zufällige Farbe
        return self._random_color_hex()

    def _random_color_hex(self) -> str:
        """Generiert einen zufälligen Farbwert im Hex-Format, z. B. '#ABC123'."""
        return "#" + "".join(random.choice("0123456789ABCDEF") for _ in range(6))
