from fints_connector import FinTSConnector
from categorizer import Categorizer
from visualizer import Visualizer
import json
import os

# File paths
TRANSACTIONS_FILE = "data/transactions.json"


def load_transactions():
    """Loads transactions from the JSON file if it exists."""
    if os.path.exists(TRANSACTIONS_FILE):
        with open(TRANSACTIONS_FILE, "r") as file:
            return json.load(file)
    return []


def save_transactions(transactions):
    """Saves transactions, ensuring only unique transactions are stored."""
    old_transactions = load_transactions()
    all_transactions = old_transactions + transactions
    unique_transactions = {f"{t['date']}-{t['amount']}-{t['description']}": t for t in all_transactions}

    with open(TRANSACTIONS_FILE, "w") as file:
        json.dump(list(unique_transactions.values()), file, indent=4)

    print(f"✅ {len(unique_transactions)} unique transactions saved.")


def main():
    """Runs the program to load, categorize, and visualize transactions."""
    # fints = FinTSConnector()
    # fints.test_connection()  # Commented out to avoid real bank connection
    # transactions = fints.get_transactions()  # Also commented out

    # Instead, load transactions from transactions.json
    transactions = load_transactions()
    print(f"🔄 Loading transactions from {TRANSACTIONS_FILE} ...")

    if not transactions:
        print("⚠ No transactions found or an error occurred while retrieving them!")
        return

    print(f"✅ {len(transactions)} transactions successfully loaded!")

    # Categorization (optional)
    categorizer = Categorizer()
    for transaction in transactions:
        # Skip if the transaction already has a category
        if "category" not in transaction or not transaction["category"]:
            transaction["category"] = categorizer.categorize_transaction(transaction)

    save_transactions(transactions)
    print("✅ Transactions successfully saved!")

    # Visualization
    visualizer = Visualizer()
    visualizer.generate_chart()


if __name__ == "__main__":
    main()
