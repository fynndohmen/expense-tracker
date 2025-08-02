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
        """
        description = transaction["description"]

        # If we've seen this description before, return its category
        if description in self.categories:
            return self.categories[description]

        # Otherwise prompt the user for a category
        print(f"New transaction detected: {description} ({transaction['amount']}€)")
        category = input("Enter category for this transaction: ").strip()

        # Save the mapping for next time
        self.categories[description] = category
        self.save_categories()

        return category

    def save_categories(self):
        """Save the updated categories to the categories.json file."""
        # Ensure the directory exists
        os.makedirs(os.path.dirname(CATEGORIES_FILE), exist_ok=True)
        with open(CATEGORIES_FILE, "w", encoding="utf-8") as file:
            json.dump(self.categories, file, indent=4, ensure_ascii=False)
