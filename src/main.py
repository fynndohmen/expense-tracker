from fints_connector import FinTSConnector
from categorizer import Categorizer
from visualizer import Visualizer
import json
import os

# File paths
TRANSACTIONS_FILE = "data/transactions.json"


def load_transactions():
    if os.path.exists(TRANSACTIONS_FILE):
        with open(TRANSACTIONS_FILE, "r") as file:
            return json.load(file)
    return []


def save_transactions(transactions):
    old_transactions = load_transactions()
    all_transactions = old_transactions + transactions
    unique_transactions = {f"{t['date']}-{t['amount']}-{t['description']}": t for t in all_transactions}

    with open(TRANSACTIONS_FILE, "w") as file:
        json.dump(list(unique_transactions.values()), file, indent=4)

    print(f"✅ {len(unique_transactions)} eindeutige Transaktionen gespeichert.")


def main():
    """Test run without real bank connection."""
    # fints = FinTSConnector()
    # fints.test_connection()  # Auskommentieren, da wir keine Bankabfrage wollen
    # transactions = fints.get_transactions()  # Ebenfalls auskommentieren

    # Stattdessen: Daten direkt aus transactions.json laden
    transactions = load_transactions()
    print(f"🔄 Lade Transaktionen aus {TRANSACTIONS_FILE} ...")

    if not transactions:
        print("⚠ Keine Transaktionen gefunden oder Fehler beim Abruf!")
        return

    print(f"✅ {len(transactions)} Transaktionen erfolgreich geladen!")

    # Kategorisierung (optional)
    categorizer = Categorizer()
    for transaction in transactions:
        # Falls bereits eine Kategorie vorhanden ist, überspringen
        if "category" not in transaction or not transaction["category"]:
            transaction["category"] = categorizer.categorize_transaction(transaction)

    save_transactions(transactions)
    print("✅ Transaktionen erfolgreich gespeichert!")

    # Visualisieren
    visualizer = Visualizer()
    visualizer.generate_chart()

if __name__ == "__main__":
    main()
