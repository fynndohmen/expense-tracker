import os
import json
import pandas as pd
import plotly.graph_objects as go

# NEU: ColorManager importieren
from color_manager import ColorManager

"""
from fints_connector import FinTSConnector  # Original import for real bank connections
"""

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRANSACTIONS_FILE = os.path.join(BASE_DIR, "data", "transactions.json")

class Visualizer:
    def __init__(self):
        # ColorManager IMMER initialisieren, damit wir für alle Kategorien dynamische Farben haben
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
        if not self.transactions:
            print("⚠ No transaction data available. Chart will not be created.")
            return

        df = pd.DataFrame(self.transactions)
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date")
        if df.empty:
            print("⚠ No data found in DataFrame after sorting.")
            return
        print(f"ℹ DataFrame has {len(df)} rows.")

        # 1) Convert negative amounts -> abs for expenses
        df["amount_abs"] = df["amount"].abs()

        # 2) Mark Income categories
        income_cats = {"Salary", "Bonus", "Revenue"}
        df["category"] = df["category"].apply(lambda c: "Income" if c in income_cats else c)

        # 3) Stacked area categories
        area_categories = ["Rent", "Electricity", "Landline", "Food", "Utilities"]

        # Summation for monthly stacked area
        df["year_month"] = df["date"].dt.to_period("M")
        month_sum_df = df.groupby(["year_month", "category"], as_index=False).agg(
            month_sum=("amount_abs", "sum")
        )

        # Build daily pivot for stacked area
        area_list = []
        all_periods = month_sum_df["year_month"].unique()
        for period in all_periods:
            start_date = pd.Timestamp(period.start_time)
            end_date = pd.Timestamp(period.end_time)
            daily_range = pd.date_range(start=start_date, end=end_date, freq="D")
            period_data = month_sum_df[
                (month_sum_df["year_month"] == period)
                & (~month_sum_df["category"].isin(["Income"]))
            ]
            for cat in area_categories:
                row = period_data[period_data["category"] == cat]
                total_sum = row["month_sum"].values[0] if not row.empty else 0
                df_temp = pd.DataFrame({
                    "date": daily_range,
                    "category": cat,
                    "month_value": total_sum
                })
                area_list.append(df_temp)

        df_area = pd.concat(area_list, ignore_index=True) if area_list else pd.DataFrame(columns=["date", "category", "month_value"])
        df_area_pivot = df_area.pivot(index="date", columns="category", values="month_value").fillna(0)
        final_area_cols = [c for c in area_categories if c in df_area_pivot.columns]
        df_area_pivot = df_area_pivot[final_area_cols]

        # Build monthly Income
        income_data = month_sum_df[month_sum_df["category"] == "Income"]
        df_income_list = []
        for period in income_data["year_month"].unique():
            start_date = pd.Timestamp(period.start_time)
            end_date = pd.Timestamp(period.end_time)
            daily_range = pd.date_range(start=start_date, end=end_date, freq="D")
            row = income_data[income_data["year_month"] == period]
            total_sum = row["month_sum"].values[0] if not row.empty else 0
            df_temp = pd.DataFrame({
                "date": daily_range,
                "category": "Income",
                "month_value": total_sum
            })
            df_income_list.append(df_temp)
        df_income = pd.concat(df_income_list, ignore_index=True) if df_income_list else pd.DataFrame(columns=["date", "category", "month_value"])

        full_date_range = pd.date_range(start=df["date"].min(), end=df["date"].max(), freq="D")
        if not df_income.empty:
            df_income = df_income.set_index("date").reindex(full_date_range).ffill().fillna(0)

        # For test mode: static balance
        initial_balance = 1000.0
        df["cumulative_sum"] = df["amount"].cumsum()
        df_balance = df.set_index("date")[["cumulative_sum"]].copy()
        df_balance.rename(columns={"cumulative_sum": "account_balance"}, inplace=True)
        df_balance["account_balance"] += initial_balance
        df_balance = df_balance.reindex(full_date_range).ffill().fillna(initial_balance)

        # Plot
        fig = go.Figure()

        # Stacked area
        for cat in df_area_pivot.columns:
            color_for_cat = self.color_manager.get_color_for_category(cat)
            fig.add_trace(go.Scatter(
                name=cat,
                x=df_area_pivot.index,
                y=df_area_pivot[cat],
                mode="lines",
                stackgroup="same",
                hoverinfo="x+y+name",
                line=dict(width=1, color=color_for_cat),
            ))

        # Income line
        color_for_income = self.color_manager.get_color_for_category("Income")
        if not df_income.empty:
            fig.add_trace(go.Scatter(
                name="Income",
                x=df_income.index,
                y=df_income["month_value"],
                mode="lines",
                line=dict(width=2, color=color_for_income),
                hoverinfo="x+y+name"
            ))

        # Balance line
        color_for_balance = self.color_manager.get_color_for_category("Account Balance")
        fig.add_trace(go.Scatter(
            name="Account Balance",
            x=df_balance.index,
            y=df_balance["account_balance"],
            mode="lines",
            line=dict(width=2, color=color_for_balance),
            hoverinfo="x+y+name"
        ))

        # ==============================
        # Additional lines with markers
        # ==============================
        line_categories = ["Food", "Utilities"]  # which categories have multiple transactions
        category_order_map = {cat: i for i, cat in enumerate(final_area_cols)}

        df_multi = df[df["category"].isin(line_categories)].copy()
        if not df_multi.empty:
            df_multi["year_month"] = df_multi["date"].dt.to_period("M")
            df_multi = df_multi.sort_values(["category", "year_month", "date"])

            all_line_frames = []
            for (cat, period), group in df_multi.groupby(["category","year_month"]):
                start_date = pd.Timestamp(period.start_time)
                end_date = pd.Timestamp(period.end_time)
                daily_range = pd.date_range(start=start_date, end=end_date, freq="D")

                group = group.copy()
                group["expense_val"] = group["amount_abs"]
                daily_sum = group.groupby("date", as_index=False)["expense_val"].sum()
                daily_sum = daily_sum.set_index("date").reindex(daily_range).fillna(0).reset_index()
                daily_sum.rename(columns={"index": "date"}, inplace=True)
                daily_sum["cum_val"] = daily_sum["expense_val"].cumsum()

                # "is_real" to mark actual transactions
                group["is_real"] = True
                group_first_desc = group.drop_duplicates("date", keep="first")[["date","description"]]
                daily_sum = daily_sum.merge(group_first_desc, on="date", how="left")
                daily_sum["is_real"] = ~daily_sum["description"].isna()

                def get_stack_offset(d_row):
                    dday = d_row["date"]
                    if cat in category_order_map:
                        cat_idx = category_order_map[cat]
                        below_cats = final_area_cols[:cat_idx]
                        if len(below_cats) > 0 and dday in df_area_pivot.index:
                            return df_area_pivot.loc[dday, below_cats].sum()
                    return 0

                daily_sum["offset"] = daily_sum.apply(get_stack_offset, axis=1)
                daily_sum["line_y"] = daily_sum["offset"] + daily_sum["cum_val"]

                daily_sum["category"] = cat
                daily_sum["year_month"] = period
                all_line_frames.append(daily_sum)

            df_lines = pd.concat(all_line_frames, ignore_index=True) if all_line_frames else pd.DataFrame()

            for cat in line_categories:
                sub_line = df_lines[df_lines["category"] == cat].copy()
                if sub_line.empty:
                    continue

                line_color = self.color_manager.get_color_for_category(cat)

                sub_line["tx_amount"] = sub_line["expense_val"].where(sub_line["is_real"], 0)
                sub_line["desc"] = sub_line["description"].fillna("")
                sub_line["marker_size"] = sub_line["is_real"].map({True: 6, False: 0})

                fig.add_trace(go.Scatter(
                    name=f"{cat} daily cumsum",
                    x=sub_line["date"],
                    y=sub_line["line_y"],
                    mode="lines+markers",
                    line=dict(width=2, color=line_color),
                    marker=dict(size=sub_line["marker_size"], color=line_color),
                    customdata=sub_line[["tx_amount","desc","cum_val"]],
                    hovertemplate=(
                        "Date: %{x}<br>"
                        + cat + " transaction: %{customdata[0]} €<br>"
                        + "Desc: %{customdata[1]}<br>"
                        + "Cumulative: %{customdata[2]} €<extra></extra>"
                    )
                ))
        else:
            print("ℹ No multi-transaction categories found for daily cumsum lines.")

        fig.update_layout(
            title="📊 Expense Tracker (Local Test Mode)",
            xaxis_title="📅 Date",
            yaxis_title="💰 Amount (€)",
            legend_title="Categories",
            hovermode="x unified"
        )

        fig.show()
        print("✅ Chart generated successfully (test mode)!")
