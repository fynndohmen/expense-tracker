import os
import json
import random

# Path to the JSON file that stores category colors
COLORS_FILE = os.path.join(
    os.path.dirname(__file__),
    "..",
    "data",
    "category_colors.json"
)

class ColorManager:
    def __init__(self):
        """
        Initialize the ColorManager:
        - Defines where the color JSON lives.
        - Sets up an empty color_map.
        - Defines a default palette to draw from before falling back to random colors.
        - Loads any existing colors from disk.
        """
        self.colors_file = COLORS_FILE
        self.color_map = {}
        # A palette of preferred colors; used in order if not already assigned
        self.default_palette = [
            "#9b59b6", "#e74c3c", "#3498db", "#2ecc71",
            "#f1c40f", "#27ae60", "#000000",
            "#8e44ad", "#d35400", "#2980b9", "#1abc9c",
            "#f39c12", "#2c3e50", "#16a085"
        ]
        self._load_colors()

    def _load_colors(self):
        """Attempt to load an existing color_map from the JSON file."""
        if os.path.exists(self.colors_file):
            try:
                with open(self.colors_file, "r", encoding="utf-8") as f:
                    self.color_map = json.load(f)
            except Exception:
                print("⚠ Could not load color map properly. Starting with an empty map.")
                self.color_map = {}
        else:
            # No file yet—start with an empty mapping
            self.color_map = {}

    def _save_colors(self):
        """Persist the current color_map to the JSON file."""
        try:
            # Ensure the directory exists
            os.makedirs(os.path.dirname(self.colors_file), exist_ok=True)
            with open(self.colors_file, "w", encoding="utf-8") as f:
                json.dump(self.color_map, f, indent=2)
        except Exception:
            print("⚠ Could not save color_map to file.")

    def get_color_for_category(self, category: str) -> str:
        """
        Return the color for the given category. If it doesn’t yet exist,
        pick a new color, save it, and return it.
        """
        if category in self.color_map:
            # Already have a color, return it
            return self.color_map[category]

        # New category—generate, save, and return a new color
        new_color = self._get_new_color()
        self.color_map[category] = new_color
        self._save_colors()
        return new_color

    def _get_new_color(self) -> str:
        """
        Look for an unused color in the default_palette first;
        if they’re all taken, generate a random hex color.
        """
        used_colors = set(self.color_map.values())

        # 1) Try each color in the default palette
        for c in self.default_palette:
            if c not in used_colors:
                return c

        # 2) Fallback: random hex color
        return self._random_color_hex()

    def _random_color_hex(self) -> str:
        """Generate a random hex color string, e.g. '#A1B2C3'."""
        return "#" + "".join(random.choice("0123456789ABCDEF") for _ in range(6))
