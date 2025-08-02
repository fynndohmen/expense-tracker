#!/usr/bin/env python3
import sys
import json
import os
from datetime import date
# ===== Live-FinTS Imports (uncomment for production) =====
# from fints_connector import FinTSConnector

from categorizer import Categorizer
from visualizer import Visualizer
from category_manager import (
    run_category_manager,
    load_category_order,
    discover_categories_from_transactions
)

# --------------------------------------------------------------------
# Paths / Config
# --------------------------------------------------------------------
BASE_DIR          = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR          = os.path.join(BASE_DIR, "data")
TRANSACTIONS_FILE = os.path.join(DATA_DIR, "transactions.json")
ORDER_FILE        = os.path.join(DATA_DIR, "category_order.json")

# --------------------------------------------------------------------
# Auto-launch Category Manager if no order file / lists empty / new cats
# --------------------------------------------------------------------
fixed, variable, unassigned = load_category_order()
known       = set(fixed) | set(variable) | set(unassigned)
discovered  = discover_categories_from_transactions()
missing     = [c for c in discovered if c not in known]

need_manager = (
    not os.path.exists(ORDER_FILE) or
    (not fixed and not variable) or
    bool(missing)
)

if need_manager:
    print("🛠 Opening Category Manager to define/sort your categories…")
    run_category_manager()
    fixed, variable, unassigned = load_category_order()

# --------------------------------------------------------------------
# Helpers for transactions.json
# --------------------------------------------------------------------
def load_transactions():
    """
    Load transactions from local JSON file if it exists.
    """
    print(f"🔄 Loading transactions from {TRANSACTIONS_FILE}…")
    if os.path.exists(TRANSACTIONS_FILE):
        try:
            with open(TRANSACTIONS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                print(f"✅ Loaded {len(data)} transactions.")
                return data
        except Exception as e:
            print(f"❌ Could not load transactions: {e}")
    else:
        print(f"⚠ File not found: {TRANSACTIONS_FILE}")
    return []

def save_transactions(transactions):
    """
    Save transactions locally, ensuring uniqueness by date-amount-description key.
    """
    old = load_transactions()
    combined = old + transactions
    uniq = {
        f"{t['date']}-{t['amount']}-{t['description']}": t
        for t in combined
    }
    try:
        with open(TRANSACTIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(list(uniq.values()), f, indent=4)
        print(f"✅ {len(uniq)} unique transactions saved.")
    except Exception as e:
        print(f"❌ Error while saving transactions: {e}")

# --------------------------------------------------------------------
# Main application logic
# --------------------------------------------------------------------
def main():
    # ===== Live-FinTS Mode (uncomment to activate) =====
    """
    fints = FinTSConnector()
    fints.test_connection()

    existing = load_transactions()
    if existing:
        oldest_iso = min(tx["date"] for tx in existing)
        oldest_date = date.fromisoformat(oldest_iso)
        print(f"⏳ Fetching since {oldest_date}")
        transactions = fints.get_transactions(start_date=oldest_date)
    else:
        print("⏳ Fetching full history")
        transactions = fints.get_transactions()

    balance_dict = fints.get_balance()
    print("🏦 Current balances:")
    for iban, info in balance_dict.items():
        print(f"  • {iban}: {info['amount']} {info['currency']}")
    """

    # ===== Local Test Mode =====
    transactions = load_transactions()
    if not transactions:
        print("⚠ No transactions available. Exiting.")
        return

    print(f"✅ {len(transactions)} transactions loaded (local).")

    # ===== Categorization =====
    categorizer = Categorizer()
    for tx in transactions:
        if not tx.get("category"):
            tx["category"] = categorizer.categorize_transaction(tx)
        # no more "fixed" flag prompting here

    save_transactions(transactions)

    # ===== Visualization =====
    viz = Visualizer()
    viz.generate_chart()

# --------------------------------------------------------------------
# CLI Entry Point
# --------------------------------------------------------------------
if __name__ == "__main__":
    # manual: python src/main.py cm  → opens Category Manager
    if len(sys.argv) > 1 and sys.argv[1].lower() == "cm":
        run_category_manager()
    else:
        main()
