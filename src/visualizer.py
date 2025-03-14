import plotly.graph_objects as go
import json
import os
import pandas as pd
from fints_connector import FinTSConnector  # Import FinTSConnector to retrieve the current account balance

TRANSACTIONS_FILE = "data/transactions.json"

class Visualizer:
    def __init__(self):
        if os.path.exists(TRANSACTIONS_FILE):
            try:
                with open(TRANSACTIONS_FILE, "r") as file:
                    self.transactions = json.load(file)
            except json.JSONDecodeError:
                print("❌ Error: JSON file is corrupted or empty!")
                self.transactions = []
        else:
            print("⚠ No transaction file found.")
            self.transactions = []

    def generate_chart(self):
        if not self.transactions:
            print("⚠ No transaction data available. Chart will not be created.")
            return

        # 1) Load and sort data
        df = pd.DataFrame(self.transactions)
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date")
        if df.empty:
            print("⚠ No data found.")
            return

        # 2) Convert amounts to absolute values for expenses
        df["amount_abs"] = df["amount"].abs()

        # 3) Recategorize income categories -> "Income"
        income_cats = {"Salary", "Bonus", "Revenue"}
        df["category"] = df["category"].apply(lambda c: "Income" if c in income_cats else c)

        # 4) Define category order for expenses
        #    (bottom -> top): Rent, Electricity, Landline, Food, Utilities
        area_categories = ["Rent", "Electricity", "Landline", "Food", "Utilities"]

        # 5) Create a "year_month" column
        df["year_month"] = df["date"].dt.to_period("M")

        # 6) Sum up all absolute amounts per (month, category)
        #    => This gives the TOTAL monthly value
        month_sum_df = df.groupby(["year_month", "category"], as_index=False).agg(
            month_sum=("amount_abs", "sum")
        )

        # 7) Create a DataFrame per month & category (only expenses),
        #    where each day of the month carries the TOTAL monthly value
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

        # 8) Pivot => Rows = Date, Columns = Category => month_value
        df_area_pivot = df_area.pivot(index="date", columns="category", values="month_value").fillna(0)
        final_area_cols = [c for c in area_categories if c in df_area_pivot.columns]
        df_area_pivot = df_area_pivot[final_area_cols]

        # 9) Income: TOTAL monthly value per day, now in the same format as expenses
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

        # Reindex over the entire period and fill missing values
        full_date_range = pd.date_range(start=df["date"].min(), end=df["date"].max(), freq="D")
        df_income = df_income.set_index("date").reindex(full_date_range).ffill().fillna(0)

        # 1️⃣ Retrieve the initial account balance
        fin_connector = FinTSConnector()
        balance_dict = fin_connector.get_balance()
        initial_balance = sum(item["amount"] for item in balance_dict.values())

        # 2️⃣ Prepare transaction data
        df["cumulative_sum"] = df["amount"].cumsum()  # Cumulative balance based on transactions

        # 3️⃣ Calculate the daily account balance (starting balance + cumulative sum of transactions)
        df_balance = df.set_index("date")[["cumulative_sum"]].copy()
        df_balance.rename(columns={"cumulative_sum": "account_balance"}, inplace=True)
        df_balance["account_balance"] += initial_balance  # Add starting balance

        # 4️⃣ Fill in missing days (to ensure every day has a value)
        df_balance = df_balance.reindex(full_date_range).ffill().fillna(initial_balance)

        # 11) Create plot
        fig = go.Figure()

        # a) Expenses as "relative stacking" (no cumsum in the DataFrame)
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

        # b) Income as a separate line (green)
        fig.add_trace(go.Scatter(
            name="Income",
            x=df_income.index,
            y=df_income["month_value"],
            mode="lines",
            line=dict(width=2, color="green"),
            hoverinfo="x+y+name"
        ))

        # c) Account balance as a solid line (black, no markers)
        fig.add_trace(go.Scatter(
            name="Account Balance",
            x=df_balance.index,
            y=df_balance["account_balance"],
            mode="lines",
            line=dict(width=2, color="black"),
            hoverinfo="x+y+name"
        ))

        fig.update_layout(
            title="📊 Expense Tracker",
            xaxis_title="📅 Date",
            yaxis_title="💰 Amount (€)",
            legend_title="Categories",
            hovermode="x unified"
        )

        fig.show()
