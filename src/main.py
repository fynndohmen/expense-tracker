import json
import os

# =========== Original Imports (commented out) ===========
"""
from fints_connector import FinTSConnector
"""

from categorizer import Categorizer
from visualizer import Visualizer

# =========== Original Variables (commented out) ===========
"""
# Potential environment-based variables or references
# (Not needed for the local test version)
"""

# =========== Paths for local test version ===========
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRANSACTIONS_FILE = os.path.join(BASE_DIR, "data", "transactions.json")

# =========== Utility Functions for local test version ===========

def load_transactions():
    """
    Loads transactions from the local JSON file if it exists.
    """
    print(f"🔄 Using local test data from {TRANSACTIONS_FILE} ...")
    if os.path.exists(TRANSACTIONS_FILE):
        try:
            with open(TRANSACTIONS_FILE, "r", encoding="utf-8") as file:
                data = json.load(file)
                print(f"✅ Loaded {len(data)} transactions from file.")
                return data
        except Exception as e:
            print(f"❌ Could not load transactions: {e}")
            return []
    else:
        print(f"⚠ File {TRANSACTIONS_FILE} not found.")
        return []

def save_transactions(transactions):
    """
    Saves transactions locally to the JSON file, ensuring uniqueness.
    """
    old_transactions = load_transactions()
    all_transactions = old_transactions + transactions
    unique_transactions = {
        f"{t['date']}-{t['amount']}-{t['description']}": t
        for t in all_transactions
    }

    try:
        with open(TRANSACTIONS_FILE, "w", encoding="utf-8") as file:
            json.dump(list(unique_transactions.values()), file, indent=4)
        print(f"✅ {len(unique_transactions)} unique transactions saved to {TRANSACTIONS_FILE}")
    except Exception as e:
        print(f"❌ Error while saving transactions: {e}")

def main():
    """
    Main entry point of the app (local test version).
    """

    # =========== Original FinTS Code (commented out) ===========
    """
    # fints = FinTSConnector()
    # fints.test_connection()
    # transactions = fints.get_transactions()
    """

    # =========== Local Test-Loading of transactions ===========
    transactions = load_transactions()
    if not transactions:
        print("⚠ No transactions found or an error occurred while retrieving them!")
        return

    print(f"✅ {len(transactions)} transactions successfully loaded (local test).")

    # Categorization
    categorizer = Categorizer()
    for tx in transactions:
        if "category" not in tx or not tx["category"]:
            tx["category"] = categorizer.categorize_transaction(tx)

        # Abfrage: Falls "fixed" fehlt, Nachfragen
        if "fixed" not in tx:
            ans = input(f"Is '{tx['description']}' (Category: {tx['category']}) a fixed cost? (y/n): ").lower().strip()
            tx["fixed"] = (ans == "y")

    save_transactions(transactions)
    print("✅ Transactions successfully saved locally!")

    # Visualization
    visualizer = Visualizer()
    visualizer.generate_chart()

if __name__ == "__main__":
    main()
