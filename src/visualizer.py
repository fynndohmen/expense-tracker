import plotly.graph_objects as go
import json
import os
import pandas as pd
from calendar import monthrange
from fints_connector import FinTSConnector  # Importiere FinTSConnector, um den aktuellen Kontostand abzurufen

TRANSACTIONS_FILE = "data/transactions.json"

class Visualizer:
    def __init__(self):
        if os.path.exists(TRANSACTIONS_FILE):
            try:
                with open(TRANSACTIONS_FILE, "r") as file:
                    self.transactions = json.load(file)
            except json.JSONDecodeError:
                print("❌ Fehler: JSON-Datei ist beschädigt oder leer!")
                self.transactions = []
        else:
            print("⚠ Keine Transaktionsdatei gefunden.")
            self.transactions = []

    def generate_chart(self):
        if not self.transactions:
            print("⚠ Keine Transaktionsdaten verfügbar. Grafik wird nicht erstellt.")
            return

        # 1) Daten einlesen & sortieren
        df = pd.DataFrame(self.transactions)
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date")
        if df.empty:
            print("⚠ Keine Daten gefunden.")
            return

        # 2) Betrag absolut für Ausgaben
        df["amount_abs"] = df["amount"].abs()

        # 3) Einkommenskategorien -> "Income"
        income_cats = {"Gehalt", "Bonus", "Einnahmen"}
        df["category"] = df["category"].apply(lambda c: "Income" if c in income_cats else c)

        # 4) Definiere Reihenfolge für Ausgabenkategorien
        #    (unten -> oben): Miete, Strom, Festnetz, Food, Utilities
        area_categories = ["Miete", "Strom", "Festnetz", "Food", "Utilities"]

        # 5) Jahr-Monat-Spalte
        df["year_month"] = df["date"].dt.to_period("M")

        # 6) Summiere alle absoluten Beträge pro (Monat, Kategorie)
        #    => Hier ist der GESAMTE Monatswert
        month_sum_df = df.groupby(["year_month", "category"], as_index=False).agg(
            month_sum=("amount_abs", "sum")
        )

        # 7) Erstelle DataFrame pro Monat & Kategorie (nur Ausgaben),
        #    das an jedem Tag im Monat den GESAMT-Wert trägt
        area_list = []
        all_periods = month_sum_df["year_month"].unique()
        for period in all_periods:
            start_date = pd.Timestamp(period.start_time)
            end_date = pd.Timestamp(period.end_time)
            daily_range = pd.date_range(start=start_date, end=end_date, freq="D")
            period_data = month_sum_df[
                (month_sum_df["year_month"] == period) &
                (~month_sum_df["category"].isin(["Income"]))
            ]
            for cat in area_categories:
                row = period_data[period_data["category"] == cat]
                if not row.empty:
                    total_sum = row["month_sum"].values[0]
                else:
                    total_sum = 0
                df_temp = pd.DataFrame({
                    "date": daily_range,
                    "category": cat,
                    "month_value": total_sum
                })
                area_list.append(df_temp)
        if area_list:
            df_area = pd.concat(area_list, ignore_index=True)
        else:
            df_area = pd.DataFrame(columns=["date", "category", "month_value"])

        # 8) Pivot => Zeilen=Datum, Spalten=Kategorie => month_value
        df_area_pivot = df_area.pivot(index="date", columns="category", values="month_value").fillna(0)
        final_area_cols = [c for c in area_categories if c in df_area_pivot.columns]
        df_area_pivot = df_area_pivot[final_area_cols]

        # 9) Income: GESAMTER Monatswert pro Tag, jetzt in derselben Struktur wie die Ausgaben
        df_income_list = []
        income_data = month_sum_df[month_sum_df["category"] == "Income"]
        for period in income_data["year_month"].unique():
            start_date = pd.Timestamp(period.start_time)
            end_date = pd.Timestamp(period.end_time)
            daily_range = pd.date_range(start=start_date, end=end_date, freq="D")
            row = income_data[income_data["year_month"] == period]
            if not row.empty:
                total_sum = row["month_sum"].values[0]
            else:
                total_sum = 0
            df_temp = pd.DataFrame({
                "date": daily_range,
                "category": "Income",
                "month_value": total_sum
            })
            df_income_list.append(df_temp)
        if df_income_list:
            df_income = pd.concat(df_income_list, ignore_index=True)
        else:
            df_income = pd.DataFrame(columns=["date", "category", "month_value"])

        # Auf gesamten Zeitraum reindexen & füllen
        full_date_range = pd.date_range(start=df["date"].min(), end=df["date"].max(), freq="D")
        df_income = df_income.set_index("date").reindex(full_date_range).ffill().fillna(0)

        # 1️⃣ Den initialen Kontostand holen
        fin_connector = FinTSConnector()
        balance_dict = fin_connector.get_balance()
        initial_balance = sum(item["amount"] for item in balance_dict.values())

        # 2️⃣ Transaktions-Daten vorbereiten
        df["cumulative_sum"] = df["amount"].cumsum()  # Kumulativer Saldo basierend auf Transaktionen

        # 3️⃣ Den täglichen Kontostand berechnen (Startwert + kumulative Summe der Transaktionen)
        df_balance = df.set_index("date")[["cumulative_sum"]].copy()
        df_balance.rename(columns={"cumulative_sum": "account_balance"}, inplace=True)
        df_balance["account_balance"] += initial_balance  # Startkontostand einrechnen

        # 4️⃣ Fehlende Tage auffüllen (damit jeder Tag einen Wert bekommt)
        df_balance = df_balance.reindex(full_date_range).ffill().fillna(initial_balance)

        # 11) Plot erstellen
        fig = go.Figure()

        # a) Ausgaben als "relative stacking" (kein cumsum im DataFrame)
        for cat in df_area_pivot.columns:
            fig.add_trace(go.Scatter(
                name=cat,
                x=df_area_pivot.index,
                y=df_area_pivot[cat],
                mode="lines",
                stackgroup="same",
                hoverinfo="x+y+name",
                line=dict(width=1)
            ))

        # b) Income als separate Linie (grün)
        fig.add_trace(go.Scatter(
            name="Income",
            x=df_income.index,
            y=df_income["month_value"],
            mode="lines",
            line=dict(width=2, color="green"),
            hoverinfo="x+y+name"
        ))

        # c) Gesamtkontostand als durchgezogene Linie (schwarz, ohne Marker)
        fig.add_trace(go.Scatter(
            name="Gesamtkontostand",
            x=df_balance.index,
            y=df_balance["account_balance"],
            mode="lines",
            line=dict(width=2, color="black"),
            hoverinfo="x+y+name"
        ))

        fig.update_layout(
            title="📊 Monats-Gesamtwerte pro Kategorie, Income-Linie & aktueller Kontostand",
            xaxis_title="📅 Datum",
            yaxis_title="💰 Betrag (€)",
            legend_title="Kategorien",
            hovermode="x unified"
        )

        fig.show()
