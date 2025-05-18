import json
import os

CATEGORIES_FILE = "data/categories.json"


class Categorizer:
    def __init__(self):
        """Load existing categories from a file or create a new one if it doesn't exist."""
        if os.path.exists(CATEGORIES_FILE):
            with open(CATEGORIES_FILE, "r", encoding="utf-8") as file:
                self.categories = json.load(file)
        else:
            self.categories = {}

    def categorize_transaction(self, transaction):
        """
        Ask the user to categorize a transaction if it is not already categorized.
        Also ask if it is a 'fixed cost' (z. B. Miete, Strom, etc.).
        """
        description = transaction["description"]

        # Prüfen, ob wir bereits einen Eintrag in categories.json haben
        existing_entry = self.categories.get(description)
        if existing_entry:
            # Falls es noch der alte String-Stil ist (z. B. "Food"),
            # geben wir einfach den String zurück.
            # Falls es schon ein Dict ist, extrahieren wir das "category"-Feld.
            if isinstance(existing_entry, dict):
                return existing_entry["category"]
            else:
                return existing_entry

        # Wenn wir hier sind, ist die Transaktion neu und noch nicht kategorisiert
        print(f"New transaction detected: {description} ({transaction['amount']}€)")
        cat_input = input("Enter category for this transaction: ").strip()

        # Neue Abfrage: Ist es eine fixe Kosten?
        is_fixed_str = input("Is this a fixed cost? (y/n): ").strip().lower()
        is_fixed = (is_fixed_str == "y")

        # Wir speichern nun ein Dictionary statt nur den Kategorienamen
        self.categories[description] = {
            "category": cat_input,
            "fixed": is_fixed
        }
        self.save_categories()

        return cat_input

    def save_categories(self):
        """Save the updated categories to the categories.json file."""
        with open(CATEGORIES_FILE, "w", encoding="utf-8") as file:
            json.dump(self.categories, file, indent=4, ensure_ascii=False)
