



Expense Tracker
The Expense Tracker is a Python-based application that retrieves your bank transactions via FinTS, categorizes them, and visualizes your expenses, income, and overall account balance using interactive charts (Plotly). The program supports fetching live bank data as well as loading transactions from a local JSON file.

Features

Bank Connection via FinTS:
Retrieve transactions and current account balances from your bank using the FinTS protocol.

Transaction Categorization:
Automatically categorize transactions using user-defined categories. If a transaction is not categorized, the application prompts you for a category and saves it.

Data Visualization:
Generate interactive charts that display:

Stacked area charts for expenses (with fixed and variable cost categories).
A separate income line.
A real-time account balance line (retrieved via FinTS).

Local Data Storage:
Transactions are stored in data/transactions.json and categories in data/categories.json.

Requirements

Python 3.8+
Plotly
pandas
python-dotenv
FinTS3PinTanClient (python-fints) (Ensure you have the appropriate version installed)
You can install the required packages using pip and the provided requirements.txt:

pip install -r requirements.txt

Getting Started

Cloning the Repository
Open a terminal (or Git Bash) on your machine.

Clone the repository by running:

git clone https://github.com/fynndohmen/expense-tracker.git

Navigate into the project directory:

cd expense-tracker

Setting Up the Virtual Environment
Create a virtual environment:

python -m venv venv

Activate the virtual environment:

On Windows:

venv\Scripts\activate
On macOS/Linux:

source venv/bin/activate
Install the required dependencies:

pip install -r requirements.txt

Configuring the Application

Create a .env file in the root directory of the project with the following content:

BANK_CODE=your_bank_code
USER_ID=your_user_id
CUSTOMER_ID=your_customer_id
PIN=your_pin
Replace the placeholders with your actual bank credentials. Note: Make sure not to push the .env file to public repositories.

Running the Application
Once the environment is set up and the dependencies are installed, you can run the application by executing:

python src/main.py

The program will load transactions from data/transactions.json (or fetch them via FinTS if enabled) and then prompt for categorization if needed.

The interactive chart will be displayed once the transactions are processed.

Additional Information
FinTS Connection:
The FinTS connection is handled in fints_connector.py. Ensure that your bank supports FinTS and that you have the correct credentials and product ID.

Categorization:
Categories are stored in data/categories.json. If you update a category via the prompt, it will be saved and used for future transactions.

Visualization:
The visualization logic is in visualizer.py. You can modify this file to customize the charts.

Troubleshooting
If you encounter errors related to missing modules, ensure you have activated your virtual environment and installed all dependencies with pip install -r requirements.txt.
If the application cannot find your transactions.json or categories.json files, check that your working directory is set to the project root.
For FinTS-specific issues, refer to the python-fints documentation.