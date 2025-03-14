from fints.client import FinTS3PinTanClient
import os
from dotenv import load_dotenv
import logging
from fints.utils import minimal_interactive_cli_bootstrap  # Enable TAN support

# Enable detailed logging for debugging
logging.basicConfig(level=logging.DEBUG)

# Load environment variables from the .env file
load_dotenv()

# Load banking credentials from environment variables
BANK_IDENTIFIER = os.getenv("BANK_CODE")  # Bank code (BLZ) of Volksbank Krefeld
USER_ID = os.getenv("USER_ID")            # Your FinTS user ID
CUSTOMER_ID = os.getenv("CUSTOMER_ID")    # Often the same as USER_ID
PIN = os.getenv("PIN")                    # Your FinTS PIN
SERVER = "https://fints2.atruvia.de/cgi-bin/hbciservlet"  # Volksbank Krefeld FinTS server

# Set product ID (must be registered with DK)
PRODUCT_ID = "VR-NetWorld Software 8.0"

class FinTSConnector:
    def __init__(self):
        """Initializes the FinTS client with banking credentials and enables TAN support."""
        if not all([BANK_IDENTIFIER, USER_ID, CUSTOMER_ID, PIN]):
            raise ValueError("❌ Missing banking credentials! Please set them in the .env file.")

        # Initialize FinTS client
        self.client = FinTS3PinTanClient(
            bank_identifier=BANK_IDENTIFIER,
            user_id=USER_ID,
            customer_id=CUSTOMER_ID,
            pin=PIN,
            server=SERVER,
            product_id=PRODUCT_ID
        )

        # Enable TAN handling
        minimal_interactive_cli_bootstrap(self.client)

    def get_transactions(self):
        """Fetches recent transactions for all SEPA accounts."""
        try:
            with self.client:
                # If PSD2 requires a TAN, prompt the user
                if self.client.init_tan_response:
                    print(f"🔒 TAN required: {self.client.init_tan_response.challenge}")
                    tan = input("Please enter TAN: ")
                    self.client.send_tan(self.client.init_tan_response, tan)

                # Retrieve SEPA accounts
                accounts = self.client.get_sepa_accounts()
                transactions = []

                # Fetch transactions for each account
                for account in accounts:
                    statement = self.client.get_statement(account)
                    for tx in statement:
                        transactions.append({
                            "date": tx.data["date"].strftime("%Y-%m-%d"),
                            "amount": tx.data["amount"].amount,
                            "description": tx.data["applicant_name"] or "Unknown"
                        })

                return transactions

        except Exception as e:
            logging.error(f"❌ Error retrieving transactions: {e}")
            return []

    def get_balance(self):
        """
        Retrieves the current account balance for all SEPA accounts via FinTS.
        Returns a dictionary where the IBAN is the key and the balance
        (amount and currency) is the value.
        """
        try:
            with self.client:
                # If PSD2 requires a TAN, prompt the user
                if self.client.init_tan_response:
                    print(f"🔒 TAN required: {self.client.init_tan_response.challenge}")
                    tan = input("Please enter TAN: ")
                    self.client.send_tan(self.client.init_tan_response, tan)

                accounts = self.client.get_sepa_accounts()
                balances = {}

                # Fetch the current balance for each account
                for account in accounts:
                    # Use the get_balance method (check library docs for correct method name)
                    balance = self.client.get_balance(account)
                    balances[account.iban] = {
                        "amount": balance.amount,
                        "currency": balance.currency
                    }
                return balances

        except Exception as e:
            logging.error(f"❌ Error retrieving account balance: {e}")
            return {}

    def test_connection(self):
        """Tests the connection to the bank and lists available accounts."""
        try:
            with self.client:
                if self.client.init_tan_response:
                    print(f"🔒 TAN required: {self.client.init_tan_response.challenge}")
                    tan = input("Please enter TAN: ")
                    self.client.send_tan(self.client.init_tan_response, tan)

                accounts = self.client.get_sepa_accounts()
                if accounts:
                    print("✅ Connection successful! Found accounts:")
                    for account in accounts:
                        print(f"- IBAN: {account.iban}, BIC: {account.bic}")
                else:
                    print("⚠ No accounts found. Please check your credentials.")
        except Exception as e:
            logging.error(f"❌ Connection failed: {e}")
