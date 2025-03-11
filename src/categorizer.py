import json
import os

CATEGORIES_FILE = "data/categories.json"


class Categorizer:
    def __init__(self):
        """Load existing categories from a file or create a new one if it doesn't exist."""
        if os.path.exists(CATEGORIES_FILE):
            with open(CATEGORIES_FILE, "r") as file:
                self.categories = json.load(file)
        else:
            self.categories = {}

    def categorize_transaction(self, transaction):
        """Ask the user to categorize a transaction if it is not already categorized."""
        description = transaction["description"]

        if description in self.categories:
            return self.categories[description]

        print(f"New transaction detected: {description} ({transaction['amount']}€)")
        category = input("Enter category for this transaction: ").strip()

        self.categories[description] = category
        self.save_categories()

        return category

    def save_categories(self):
        """Save the updated categories to the categories.json file."""
        with open(CATEGORIES_FILE, "w") as file:
            json.dump(self.categories, file, indent=4)
