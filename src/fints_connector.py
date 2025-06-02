from fints.client import FinTS3PinTanClient
import os
from dotenv import load_dotenv
import logging
from datetime import date
from fints.utils import minimal_interactive_cli_bootstrap  # Enable TAN support

# Enable detailed logging for debugging
logging.basicConfig(level=logging.DEBUG)

# Load environment variables from the .env file
load_dotenv()

# Load banking credentials from environment variables
BANK_IDENTIFIER = os.getenv("BANK_CODE")  # Bank code (BLZ) of your bank
USER_ID = os.getenv("USER_ID")            # Your FinTS user ID
CUSTOMER_ID = os.getenv("CUSTOMER_ID")    # Often the same as USER_ID
PIN = os.getenv("PIN")                    # Your FinTS PIN
SERVER = os.getenv("FINTS_SERVER", "https://fints2.atruvia.de/cgi-bin/hbciservlet")

# Set product ID (must be registered with DK)
PRODUCT_ID = os.getenv("PRODUCT_ID", "VR-NetWorld Software 8.0")

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

    def get_transactions(self, start_date: date = None, end_date: date = None):
        """
        Fetches transactions for all SEPA accounts.
        If start_date is provided, only transactions from that date onward are fetched.
        end_date defaults to today if not given.
        """
        if end_date is None:
            end_date = date.today()

        try:
            with self.client:
                # If PSD2 requires a TAN, prompt the user
                if self.client.init_tan_response:
                    print(f"🔒 TAN required: {self.client.init_tan_response.challenge}")
                    tan = input("Please enter TAN: ")
                    self.client.send_tan(self.client.init_tan_response, tan)

                accounts = self.client.get_sepa_accounts()
                transactions = []

                for account in accounts:
                    # Pass start_date/end_date to the bank call if supported by the backend
                    if start_date:
                        statement = self.client.get_statement(
                            account,
                            start_date=start_date,
                            end_date=end_date
                        )
                    else:
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
                if self.client.init_tan_response:
                    print(f"🔒 TAN required: {self.client.init_tan_response.challenge}")
                    tan = input("Please enter TAN: ")
                    self.client.send_tan(self.client.init_tan_response, tan)

                accounts = self.client.get_sepa_accounts()
                balances = {}

                for account in accounts:
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
