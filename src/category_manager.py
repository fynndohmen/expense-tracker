#!/usr/bin/env python3
import json
import os
import tkinter as tk
import sys

# --------------------------------------------------------------------
# Paths / Files
# --------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

ORDER_FILE = os.path.join(DATA_DIR, "category_order.json")
TRANSACTIONS_FILE = os.path.join(DATA_DIR, "transactions.json")

# --------------------------------------------------------------------
# Helpers to load / save category order
# --------------------------------------------------------------------
def load_category_order():
    if not os.path.exists(ORDER_FILE):
        return [], [], []  # fixed, variable, unassigned leer
    try:
        with open(ORDER_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        fixed = data.get("fixed", [])
        variable = data.get("variable", [])
        unassigned = data.get("unassigned", [])
        return fixed, variable, unassigned
    except Exception:
        return [], [], []


def save_category_order(fixed, variable, unassigned):
    """
    Persist the three lists to ORDER_FILE.
    """
    os.makedirs(DATA_DIR, exist_ok=True)
    data = {
        "fixed": fixed,
        "variable": variable,
        "unassigned": unassigned
    }
    with open(ORDER_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def discover_categories_from_transactions():
    """
    Scan transactions.json and return a set of all categories present.
    """
    if not os.path.exists(TRANSACTIONS_FILE):
        # The transactions file doesn't exist → no categories can be discovered.
        # Return an empty *set* (not None) so callers can safely do set operations
        # (|, -, membership checks, etc.) without extra None-checks.
        return set()
    try:
        with open(TRANSACTIONS_FILE, "r", encoding="utf-8") as f:
            tx = json.load(f)
        cats = {t.get("category") for t in tx if t.get("category")}
        # Filter out income-like categories if they should not be user-managed
        return {c for c in cats if c not in {"Income"}}
    except Exception:
        return set()


# --------------------------------------------------------------------
# GUI Class
# --------------------------------------------------------------------
class CategoryManager(tk.Tk):
    """
    Three-list category manager:
      - Fixed Costs
      - Variable Costs
      - Unassigned (new / not yet classified)
    User can reorder within a list and move categories between lists.
    """

    def __init__(self):
        super().__init__()
        self.title("Category Manager")
        self.geometry("900x800")

        fixed, variable, unassigned = load_category_order()

        # Merge in new categories from transactions
        existing_all = set(fixed) | set(variable) | set(unassigned)
        discovered = discover_categories_from_transactions()
        missing = [c for c in sorted(discovered) if c not in existing_all]

        # Add missing categories into unassigned
        unassigned.extend(missing)

        self._build_ui(fixed, variable, unassigned)

    # ----------------------------------------------------------------
    # UI Construction
    # ----------------------------------------------------------------
    def _build_ui(self, fixed, variable, unassigned):
        top_frame = tk.Frame(self)
        top_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Frames for each category group
        fixed_frame = tk.LabelFrame(top_frame, text="Fixed Costs")
        variable_frame = tk.LabelFrame(top_frame, text="Variable Costs")
        unassigned_frame = tk.LabelFrame(top_frame, text="Unassigned")

        fixed_frame.pack(side="left", fill="both", expand=True, padx=5)
        variable_frame.pack(side="left", fill="both", expand=True, padx=5)
        unassigned_frame.pack(side="left", fill="both", expand=True, padx=5)

        # Listboxes
        self.fixed_lb = tk.Listbox(fixed_frame, activestyle="none")
        self.variable_lb = tk.Listbox(variable_frame, activestyle="none")
        self.unassigned_lb = tk.Listbox(unassigned_frame, activestyle="none")

        self.fixed_lb.pack(fill="both", expand=True)
        self.variable_lb.pack(fill="both", expand=True)
        self.unassigned_lb.pack(fill="both", expand=True)

        for c in fixed:
            self.fixed_lb.insert("end", c)
        for c in variable:
            self.variable_lb.insert("end", c)
        for c in unassigned:
            self.unassigned_lb.insert("end", c)

        # Reorder buttons under each list
        self._add_reorder_controls(fixed_frame, self.fixed_lb)
        self._add_reorder_controls(variable_frame, self.variable_lb)
        self._add_reorder_controls(unassigned_frame, self.unassigned_lb)

        # Transfer controls
        transfer_frame = tk.Frame(self)
        transfer_frame.pack(fill="x", padx=10, pady=(0, 10))

        tk.Label(transfer_frame, text="Move selection between lists:").pack(anchor="w")

        move_row1 = tk.Frame(transfer_frame)
        move_row1.pack(fill="x", pady=2)
        tk.Button(move_row1, text="Unassigned → Fixed",
                  command=lambda: self._move_between(self.unassigned_lb, self.fixed_lb)).pack(side="left", padx=4)
        tk.Button(move_row1, text="Unassigned → Variable",
                  command=lambda: self._move_between(self.unassigned_lb, self.variable_lb)).pack(side="left", padx=4)

        move_row2 = tk.Frame(transfer_frame)
        move_row2.pack(fill="x", pady=2)
        tk.Button(move_row2, text="Fixed → Variable",
                  command=lambda: self._move_between(self.fixed_lb, self.variable_lb)).pack(side="left", padx=4)
        tk.Button(move_row2, text="Variable → Fixed",
                  command=lambda: self._move_between(self.variable_lb, self.fixed_lb)).pack(side="left", padx=4)

        move_row3 = tk.Frame(transfer_frame)
        move_row3.pack(fill="x", pady=2)
        tk.Button(move_row3, text="Fixed → Unassigned",
                  command=lambda: self._move_between(self.fixed_lb, self.unassigned_lb)).pack(side="left", padx=4)
        tk.Button(move_row3, text="Variable → Unassigned",
                  command=lambda: self._move_between(self.variable_lb, self.unassigned_lb)).pack(side="left", padx=4)

        # Save / Cancel
        bottom = tk.Frame(self)
        bottom.pack(fill="x", padx=10, pady=5)
        tk.Button(bottom, text="Save & Exit", command=self._on_save, width=15).pack(side="right", padx=5)
        tk.Button(bottom, text="Cancel", command=self.destroy, width=10).pack(side="right")

    def _add_reorder_controls(self, parent, listbox):
        btns = tk.Frame(parent)
        btns.pack(fill="x", pady=4)
        tk.Button(btns, text="Up", command=lambda lb=listbox: self._move_up(lb), width=6).pack(side="left", padx=3)
        tk.Button(btns, text="Down", command=lambda lb=listbox: self._move_down(lb), width=6).pack(side="left", padx=3)

    # ----------------------------------------------------------------
    # Movement & Reordering
    # ----------------------------------------------------------------
    def _move_between(self, src: tk.Listbox, dst: tk.Listbox):
        sel = src.curselection()
        if not sel:
            return
        idx = sel[0]
        item = src.get(idx)
        src.delete(idx)
        dst.insert("end", item)
        dst.select_clear(0, "end")
        dst.select_set("end")

    def _move_up(self, lb: tk.Listbox):
        sel = lb.curselection()
        if not sel:
            return
        idx = sel[0]
        if idx == 0:
            return
        val = lb.get(idx)
        lb.delete(idx)
        lb.insert(idx - 1, val)
        lb.select_set(idx - 1)

    def _move_down(self, lb: tk.Listbox):
        sel = lb.curselection()
        if not sel:
            return
        idx = sel[0]
        if idx >= lb.size() - 1:
            return
        val = lb.get(idx)
        lb.delete(idx)
        lb.insert(idx + 1, val)
        lb.select_set(idx + 1)

    # ----------------------------------------------------------------
    # Save
    # ----------------------------------------------------------------
    def _on_save(self):
        fixed = list(self.fixed_lb.get(0, "end"))
        variable = list(self.variable_lb.get(0, "end"))
        unassigned = list(self.unassigned_lb.get(0, "end"))
        save_category_order(fixed, variable, unassigned)
        self.destroy()


# --------------------------------------------------------------------
# CLI Entry
# --------------------------------------------------------------------
def run_category_manager():
    app = CategoryManager()
    app.mainloop()


if __name__ == "__main__":
    # Optional: allow `python category_manager.py` or `python category_manager.py cm`
    if (len(sys.argv) > 1 and sys.argv[1] == "cm"):
        run_category_manager()
    else:
        print("Unknown arguments. Usage:")
        print("  python category_manager.py")
        print("  python category_manager.py cm")
