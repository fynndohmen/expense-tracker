# Expense Tracker

The **Expense Tracker** is a Python-based application that connects to your bank via FinTS or loads transactions from a local JSON file, automatically categorizes them, lets you manage and order your spending categories through a GUI, assigns colors to each category, and generates rich, interactive visualizations of your income, expenses, and account balance using Plotly.

---

## Key Features

- **Live Bank Integration (FinTS)**: Fetch SEPA transactions and current balances directly from your bank using the FinTS-Pin/TAN protocol (via `fints_connector.py`).
- **Local JSON Fallback**: Load and test transactions locally from `data/transactions.json` without bank connection.
- **Smart Categorization**: The `Categorizer` prompts you once for each new transaction description and saves mappings in `data/categories.json` for future automatic categorization.
- **Category Management GUI**: Organize categories into **Fixed**, **Variable**, and **Unassigned** using a Tkinter-based Category Manager. Your order is persisted in `data/category_order.json`.
- **Automated Color Assignment**: `ColorManager` assigns distinct colors per category (from a preset palette or random hex) and saves them in `data/category_colors.json`.
- **Interactive Visualization**:
  - Stacked area chart of monthly fixed and variable expenses
  - Separate income line
  - Account balance line (static for testing or fetched live)
  - Daily cumulative expense lines with markers and hover tooltips showing transaction details
- **Duplicate Detection**: `save_transactions` merges and deduplicates transactions based on date, amount, and description.
- **Mode Toggle**: Switch between **Dynamic (FinTS)** and **Static (Local)** modes by commenting/uncommenting blocks in `src/main.py`.
- **Quick Category Manager Launch**: Run `python src/main.py cm` to open the Category Manager GUI directly.

---

## Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/fynndohmen/expense-tracker.git
cd expense-tracker
```

### 2. Ensure `.env` is Ignored

Make sure your root `.gitignore` contains:

```
.env
```

### 3. Create a Virtual Environment

```bash
python3 -m venv venv
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

\`\` should include at least:

```
pandas
plotly
python-dotenv
python-fints
```

### 5. Configure Environment Variables

Create a file named `.env` in the project root with your banking credentials:

```dotenv
BANK_CODE=YOUR_BANK_CODE
USER_ID=YOUR_USER_ID
CUSTOMER_ID=YOUR_CUSTOMER_ID
PIN=YOUR_PIN
FINTS_SERVER=https://...
PRODUCT_ID=YourProductID
```

> **Warning:** Never commit your `.env` file to version control.

---

## Usage

### Dynamic Mode (Live FinTS)

1. In \`\`, uncomment the **DYNAMIC PART** block and comment out the **STATIC PART**.
2. Run:
   ```bash
   python src/main.py
   ```
3. The app will prompt for TAN if required, fetch new transactions since the last sync, retrieve current balances, categorize uncategorized transactions, and display the interactive chart.

### Static Mode (Local JSON)

1. In \`\`, uncomment the **STATIC PART** block and comment out the **DYNAMIC PART**.
2. Ensure `data/transactions.json` contains your test data.
3. Run:
   ```bash
   python src/main.py
   ```
4. Transactions will be loaded locally and visualized; no bank connection is needed.

### Open Category Manager

```bash
python src/main.py cm
```

---

## Project Structure

```
expense-tracker/
├── data/
│   ├── transactions.json       # Stored transactions
│   ├── categories.json         # Description→category mappings
│   ├── category_order.json     # Fixed, Variable, Unassigned order
│   └── category_colors.json    # Assigned category colors
├── src/
│   ├── main.py                 # Entry point with mode toggle
│   ├── categorizer.py          # Interactive category mapping
│   ├── category_manager.py     # Tkinter GUI for ordering categories
│   ├── color_manager.py        # Color assignment per category
│   ├── fints_connector.py      # Live FinTS connection logic
│   └── visualizer.py           # Plotly-based chart generator
├── requirements.txt            # Python dependencies
├── .gitignore                  # Files to ignore in Git
└── README.md                   # This file
```

---

## Troubleshooting

- **Missing Modules**: Activate your virtual environment and run `pip install -r requirements.txt`.
- \`\`\*\* not read\*\*: Verify `.env` is in the project root and named exactly `.env`.
- **Gan**: If you cloned an older branch, pull the latest changes: `git pull`.
- **FinTS Issues**: Consult the [python-fints documentation](https://github.com/steinfletcher/python-fints).

---

Enjoy deeper insights into your spending with this flexible, FinTS-powered Python Expense Tracker!

