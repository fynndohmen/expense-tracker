import json
import os
from datetime import date
# ===== Live-FinTS Imports (uncomment for production) =====
# from fints_connector import FinTSConnector

from categorizer import Categorizer
from visualizer import Visualizer

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRANSACTIONS_FILE = os.path.join(BASE_DIR, "data", "transactions.json")


def load_transactions():
    """
    Loads transactions from the local JSON file if it exists.
    """
    print(f"🔄 Using local data from {TRANSACTIONS_FILE} ...")
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
    Main entry point of the app.
    Toggle between Live-FinTS mode (uncomment) and Local Test mode.
    """

    # ===== Live-FinTS Mode (uncomment to activate) =====
    """
    fints = FinTSConnector()
    fints.test_connection()

    # Ermittle ältestes Datum aus der lokalen Datei, um lückenlos nachzuladen
    existing = load_transactions()
    if existing:
        oldest_iso = min(tx["date"] for tx in existing)
        oldest_date = date.fromisoformat(oldest_iso)
        print(f"⏳ Fetching transactions since {oldest_date}")
        transactions = fints.get_transactions(start_date=oldest_date)
    else:
        print("⏳ No existing data, fetching full history")
        transactions = fints.get_transactions()

    # Aktuellen Kontostand holen
    balance_dict = fints.get_balance()
    print("🏦 Current balances by IBAN:")
    for iban, info in balance_dict.items():
        print(f"  • {iban}: {info['amount']} {info['currency']}")
    """

    # ===== Local Test Mode =====
    transactions = load_transactions()
    if not transactions:
        print("⚠ No transactions found or an error occurred while retrieving them!")
        return

    print(f"✅ {len(transactions)} transactions successfully loaded (local test).")

    # ===== Categorization =====
    categorizer = Categorizer()
    for tx in transactions:
        if "category" not in tx or not tx["category"]:
            tx["category"] = categorizer.categorize_transaction(tx)

        # Frage nach Fixkosten-Flag, wenn noch nicht gesetzt
        if "fixed" not in tx:
            ans = input(
                f"Is '{tx['description']}' (Category: {tx['category']}) a fixed cost? (y/n): "
            ).lower().strip()
            tx["fixed"] = (ans == "y")

    save_transactions(transactions)
    print("✅ Transactions successfully saved locally!")

    # ===== Visualization =====
    visualizer = Visualizer()
    visualizer.generate_chart()


if __name__ == "__main__":
    main()
