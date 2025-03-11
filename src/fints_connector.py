from fints.client import FinTS3PinTanClient
import os
from dotenv import load_dotenv
import logging
from fints.utils import minimal_interactive_cli_bootstrap  # TAN-Support hinzufügen

# Aktiviert detailliertes Logging für Fehlersuche
logging.basicConfig(level=logging.DEBUG)

# Lade Umgebungsvariablen aus der .env-Datei
load_dotenv()

# Bankverbindungsdaten aus Umgebungsvariablen laden
BANK_IDENTIFIER = os.getenv("BANK_CODE")  # BLZ der Volksbank Krefeld
USER_ID = os.getenv("USER_ID")            # Deine FinTS-Benutzerkennung
CUSTOMER_ID = os.getenv("CUSTOMER_ID")    # Oft gleich mit USER_ID
PIN = os.getenv("PIN")                    # Deine FinTS-PIN
SERVER = "https://fints2.atruvia.de/cgi-bin/hbciservlet"  # Volksbank Krefeld FinTS-Server

# Produkt-ID setzen (muss von der DK registriert werden)
PRODUCT_ID = "VR-NetWorld Software 8.0"

class FinTSConnector:
    def __init__(self):
        """Initialisiert den FinTS-Client mit Bankdaten und aktiviert TAN-Unterstützung."""
        if not all([BANK_IDENTIFIER, USER_ID, CUSTOMER_ID, PIN]):
            raise ValueError("❌ Fehlende Bank-Zugangsdaten! Bitte in der .env Datei setzen.")

        # FinTS-Client initialisieren
        self.client = FinTS3PinTanClient(
            bank_identifier=BANK_IDENTIFIER,
            user_id=USER_ID,
            customer_id=CUSTOMER_ID,
            pin=PIN,
            server=SERVER,
            product_id=PRODUCT_ID
        )

        # TAN-Verarbeitung aktivieren
        minimal_interactive_cli_bootstrap(self.client)

    def get_transactions(self):
        """Holt die letzten Transaktionen für alle SEPA-Konten."""
        try:
            with self.client:
                # Falls PSD2 eine TAN verlangt, wird sie hier eingegeben
                if self.client.init_tan_response:
                    print(f"🔒 TAN erforderlich: {self.client.init_tan_response.challenge}")
                    tan = input("Bitte TAN eingeben: ")
                    self.client.send_tan(self.client.init_tan_response, tan)

                # SEPA-Konten abrufen
                accounts = self.client.get_sepa_accounts()
                transactions = []

                # Transaktionen für jedes Konto abrufen
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
            logging.error(f"❌ Fehler beim Abrufen der Transaktionen: {e}")
            return []

    def test_connection(self):
        """Testet die Verbindung zur Bank und listet verfügbare Konten auf."""
        try:
            with self.client:
                if self.client.init_tan_response:
                    print(f"🔒 TAN erforderlich: {self.client.init_tan_response.challenge}")
                    tan = input("Bitte TAN eingeben: ")
                    self.client.send_tan(self.client.init_tan_response, tan)

                accounts = self.client.get_sepa_accounts()
                if accounts:
                    print("✅ Verbindung erfolgreich! Gefundene Konten:")
                    for account in accounts:
                        print(f"- IBAN: {account.iban}, BIC: {account.bic}")
                else:
                    print("⚠ Keine Konten gefunden. Bitte Zugangsdaten überprüfen.")
        except Exception as e:
            logging.error(f"❌ Verbindung fehlgeschlagen: {e}")
