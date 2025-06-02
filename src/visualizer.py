import os
import json
import pandas as pd
import plotly.graph_objects as go
from color_manager import ColorManager
from fints_connector import FinTSConnector

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRANSACTIONS_FILE = os.path.join(BASE_DIR, "data", "transactions.json")


class Visualizer:
    def __init__(self):
        self.color_manager = ColorManager()

        print(f"🔎 Checking for local file: {TRANSACTIONS_FILE}")
        if os.path.exists(TRANSACTIONS_FILE):
            try:
                with open(TRANSACTIONS_FILE, "r", encoding="utf-8") as file:
                    self.transactions = json.load(file)
                    print(f"✅ Loaded {len(self.transactions)} transactions into Visualizer.")
                return
            except json.JSONDecodeError:
                print("❌ Error: JSON file is corrupted or empty!")
        else:
            print(f"⚠ No transaction file found at {TRANSACTIONS_FILE}.")

        self.transactions = []

    def generate_chart(self):
        """
        Erzeugt:
         - Ein gestapeltes Area-Chart aller Ausgaben (fixe unten, variable oben),
         - Eine separate Income-Linie (Monatswert konstant pro Tag),
         - Eine Balance-Linie (static; zum Test),
         - Pro Tag/Kategorie genau einen Marker mit allen Transaktionen im Tooltip
           (dabei erscheint "Transactions:..." nur, wenn zum Datum tatsächlich Buchungen vorliegen).
        """
        if not self.transactions:
            print("⚠ No transaction data available. Chart will not be created.")
            return

        # --- 1) Basis-DF vorbereiten ---
        df = pd.DataFrame(self.transactions)
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date")
        print(f"ℹ DataFrame has {len(df)} rows.")

        # Negative Beträge als positiv für Ausgaben
        df["amount_abs"] = df["amount"].abs()

        # Income-Kategorien zusammenfassen
        income_cats = {"Salary", "Bonus", "Revenue"}
        df["category"] = df["category"].apply(lambda c: "Income" if c in income_cats else c)

        # Reihenfolge der Ausgaben (unten → oben)
        area_categories = ["Rent", "Electricity", "Landline", "Food", "Utilities"]

        # Monatliche Gesamtsumme je Kategorie
        df["year_month"] = df["date"].dt.to_period("M")
        month_sum_df = df.groupby(["year_month", "category"], as_index=False).agg(
            month_sum=("amount_abs", "sum")
        )

        # Vollständige Tagesreihe (vom frühesten bis zum spätesten Datum)
        full_date_range = pd.date_range(start=df["date"].min(), end=df["date"].max(), freq="D")

        # --- 2) Gestapeltes Area-Chart der Ausgaben ---
        area_list = []
        for period in month_sum_df["year_month"].unique():
            start = pd.Timestamp(period.start_time)
            end   = pd.Timestamp(period.end_time)
            days  = pd.date_range(start=start, end=end, freq="D")

            data = month_sum_df[
                (month_sum_df["year_month"] == period) &
                (~month_sum_df["category"].isin(["Income"]))
            ]

            for cat in area_categories:
                # Falls diese Kategorie in diesem Monat existiert, holen wir den Wert; sonst 0
                val = data.loc[data["category"] == cat, "month_sum"]
                total = int(val.iloc[0]) if not val.empty else 0

                area_list.append(pd.DataFrame({
                    "date": days,
                    "category": cat,
                    "month_value": total
                }))

        df_area = (
            pd.concat(area_list, ignore_index=True)
            if area_list
            else pd.DataFrame(columns=["date", "category", "month_value"])
        )
        df_area = df_area.pivot(index="date", columns="category", values="month_value").fillna(0)
        # Nur die in area_categories vorkommenden Spalten in der richtigen Reihenfolge belassen
        df_area = df_area[[c for c in area_categories if c in df_area.columns]]

        # --- 3) Income-Linie (Monatswert konstant pro Tag) ---
        income_list = []
        inc_data = month_sum_df[month_sum_df["category"] == "Income"]
        for period in inc_data["year_month"].unique():
            start = pd.Timestamp(period.start_time)
            end   = pd.Timestamp(period.end_time)
            days  = pd.date_range(start=start, end=end, freq="D")

            val = inc_data.loc[inc_data["year_month"] == period, "month_sum"]
            total = int(val.iloc[0]) if not val.empty else 0

            income_list.append(pd.DataFrame({
                "date": days,
                "category": "Income",
                "month_value": total
            }))

        df_income = (
            pd.concat(income_list, ignore_index=True)
            if income_list
            else pd.DataFrame(columns=["date", "category", "month_value"])
        )
        # Index-Setzen und Duplikate im Index entfernen, bevor reindex:
        df_income = df_income.set_index("date")
        df_income = df_income[~df_income.index.duplicated(keep="last")]
        df_income = df_income.reindex(full_date_range).ffill().fillna(0)

        # --- 4) Balance-Linie (static; zum Test) ---
        initial_balance = 1000.0
        df["cumulative_sum"] = df["amount"].cumsum()
        df_balance = (
            df.set_index("date")[["cumulative_sum"]]
              .rename(columns={"cumulative_sum": "account_balance"})
        )
        # Duplikate am gleichen Datum entfernen, bevor reindex:
        df_balance = df_balance[~df_balance.index.duplicated(keep="last")]
        # Startsaldo hinzurechnen
        df_balance["account_balance"] += initial_balance
        # Fehlende Tage auffüllen
        df_balance = df_balance.reindex(full_date_range).ffill().fillna(initial_balance)

        # Live-Balance via FinTS abrufen:
        '''
        fin = FinTSConnector()
        bal_dict = fin.get_balance()  # {iban: {"amount": X, "currency": Y}, …}
        initial_balance = sum(item["amount"] for item in bal_dict.values())
                # # kumulative Transaktionssumme ermitteln
        df["cumulative_sum"] = df["amount"].cumsum()
        
        # echten Kontostand berechnen (Startsaldo + Transaktionen)
        df_balance = (
            df
            .set_index("date")[["cumulative_sum"]]
            .rename(columns={"cumulative_sum": "account_balance"})
        )
        # Duplikate am selben Tag entfernen
        df_balance = df_balance[~df_balance.index.duplicated(keep="last")]
        # Startsaldo addieren
        df_balance["account_balance"] += initial_balance
        # Fehlende Tage auffüllen
        df_balance = df_balance.reindex(full_date_range).ffill().fillna(initial_balance)
        '''

        # --- 5) Plot aufbauen ---
        fig = go.Figure()

        # a) Ausgaben als gestapeltes Area (hoverinfo für Flächen ausblenden)
        for cat in df_area.columns:
            fig.add_trace(go.Scatter(
                name=cat,
                x=df_area.index,
                y=df_area[cat],
                mode="lines",
                stackgroup="same",
                line=dict(width=0, color=self.color_manager.get_color_for_category(cat)),
                hoverinfo="none",  # <-- Hier wird kein Hover-Text für die Flächen angezeigt
                showlegend=False
            ))

        # b) Income-Linie
        fig.add_trace(go.Scatter(
            name="Income",
            x=df_income.index,
            y=df_income["month_value"],
            mode="lines",
            line=dict(width=2, color=self.color_manager.get_color_for_category("Income")),
            hoverinfo="x+y+name"
        ))

        # c) Balance-Linie
        fig.add_trace(go.Scatter(
            name="Account Balance",
            x=df_balance.index,
            y=df_balance["account_balance"],
            mode="lines",
            line=dict(width=1, color=self.color_manager.get_color_for_category("Account Balance")),
            hoverinfo="x+y+name"
        ))

        # --- 6) Daily cumsum-Linien mit Marker & allen Transaktionen im Tooltip ---
        df_multi = df[df["category"].isin(area_categories)].copy()
        if not df_multi.empty:
            df_multi["year_month"] = df_multi["date"].dt.to_period("M")
            df_multi = df_multi.sort_values(["category", "year_month", "date"])
            order_map = {cat: i for i, cat in enumerate(area_categories)}
            all_lines = []

            for (cat, period), grp in df_multi.groupby(["category", "year_month"]):
                start = pd.Timestamp(period.start_time)
                end   = pd.Timestamp(period.end_time)
                days  = pd.date_range(start=start, end=end, freq="D")

                grp = grp.copy()
                grp["expense_val"] = grp["amount_abs"]

                # 6.1) Tageswerte summieren
                daily = grp.groupby("date", as_index=False)["expense_val"].sum()
                daily = (
                    daily
                    .set_index("date")
                    .reindex(days)
                    .fillna(0)
                    .reset_index()
                    .rename(columns={"index": "date"})
                )
                daily["cum_val"] = daily["expense_val"].cumsum()

                # 6.2) Alle TX-Details pro Tag sammeln (inkl. Präfix "Transactions:<br>")
                tx_det = (
                    grp.groupby("date")
                       .apply(
                           lambda g: "Transactions:<br>" +
                                     "<br>".join(f"{int(a)} € – {d}"
                                                 for a, d in zip(g["expense_val"], g["description"]))
                       )
                       .reset_index(name="tx_details")
                )
                tx_det["tx_details"] = tx_det["tx_details"].fillna("")  # fehlende Tage → leerer String

                daily = daily.merge(tx_det, on="date", how="left")
                daily["tx_details"] = daily["tx_details"].fillna("")  # NaN → leerer String
                daily["marker_size"] = daily["tx_details"].apply(lambda txt: 6 if txt else 0)

                # 6.3) Stapel-Offset berechnen (damit Linie oberhalb des Area-Charts gezeichnet wird)
                def offset(r):
                    below = area_categories[: order_map[cat]]
                    return df_area.loc[r["date"], below].sum() if below else 0

                daily["offset"] = daily.apply(offset, axis=1)
                daily["line_y"] = daily["offset"] + daily["cum_val"]
                daily["category"] = cat

                all_lines.append(daily)

            df_lines = pd.concat(all_lines, ignore_index=True)

            for cat in area_categories:
                sub = df_lines[df_lines["category"] == cat]
                if sub.empty:
                    continue

                fig.add_trace(go.Scatter(
                    name=f"{cat} daily cumsum",
                    x=sub["date"],
                    y=sub["line_y"],
                    mode="lines+markers",
                    line=dict(width=1, color=self.color_manager.get_color_for_category(cat)),
                    marker=dict(size=sub["marker_size"], color="black", symbol="diamond"),
                    customdata=sub[["cum_val", "tx_details"]],
                    hovertemplate=(
                        "Date: %{x}<br>"
                        + f"{cat} cumulative: %{{customdata[0]}} €"
                        + "<br>%{customdata[1]}<extra></extra>"
                    )
                ))
        else:
            print("ℹ No daily cumsum categories found.")

        # Layout final
        fig.update_layout(
            title="📊 Expense Tracker",
            xaxis_title="📅 Date",
            yaxis_title="💰 Amount (€)",
            legend_title="Categories",
            hovermode="x unified"
        )
        fig.show()
        print("✅ Chart generated successfully!")


