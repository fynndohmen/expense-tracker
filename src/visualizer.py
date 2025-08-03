import os
import json
import pandas as pd
import plotly.graph_objects as go
from color_manager import ColorManager
from fints_connector import FinTSConnector

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
CATEGORY_ORDER_FILE = os.path.join(DATA_DIR, "category_order.json")


def load_area_categories():
    try:
        with open(CATEGORY_ORDER_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("fixed", []) + data.get("variable", [])
    except Exception:
        return []  # keine Kategorien -> evtl. nur Balance/Income plotten


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
        Generates:
         - A stacked area chart of all expenses (fixed at bottom, variable on top),
         - A separate income line (monthly total constant per day),
         - A balance line (static for testing),
         - One marker per day/category showing all transactions in the tooltip
           (the "Transactions:..." section appears only on days with actual entries).
        """
        if not self.transactions:
            print("⚠ No transaction data available. Chart will not be created.")
            return

        # --- 1) Prepare base DataFrame ---
        df = pd.DataFrame(self.transactions)
        df["date"] = pd.to_datetime(df["date"])  # Convert the date column to pandas datetime objects
        df = df.sort_values("date")
        print(f"ℹ DataFrame has {len(df)} rows.")

        # Convert negative amounts to positive for expense calculations
        df["amount_abs"] = df["amount"].abs()

        # Consolidate income categories into a single "Income" label
        income_cats = {"Salary", "Bonus", "Revenue"}
        df["category"] = df["category"].apply(lambda c: "Income" if c in income_cats else c)

        # Define expense categories in stacking order (bottom → top)
        area_categories = load_area_categories()
        if not area_categories:
            print("ℹ No area categories defined. Skipping stacked area plot.")

        # Compute the monthly total per category
        df["year_month"] = df["date"].dt.to_period("M")
        month_sum_df = df.groupby(["year_month", "category"], as_index=False).agg(
            month_sum=("amount_abs", "sum")
        )
        # with as_index=False, "year_month" and "category" remain columns instead of becoming the index

        # Create a full date range from the earliest to the latest transaction date
        full_date_range = pd.date_range(start=df["date"].min(), end=df["date"].max(), freq="D")

        # --- 2) stacked area-chart of the output ---
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

        # --- 3) Income-Line (monthvalue constant for days) ---
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
        # set index and remove duplicates, before reindex:
        df_income = df_income.set_index("date")
        df_income = df_income[~df_income.index.duplicated(keep="last")]
        df_income = df_income.reindex(full_date_range).fillna(0)

        # --- 4) Balance line ---
        # --- STATIC PART: Use a fixed initial balance for testing ---
        #"""
        initial_balance = 1000.0
        df["cumulative_sum"] = df["amount"].cumsum()
        df_balance = (
            df.set_index("date")[ ["cumulative_sum"] ]
              .rename(columns={"cumulative_sum": "account_balance"})
        )
        df_balance = df_balance[~df_balance.index.duplicated(keep="last")]
        df_balance["account_balance"] += initial_balance
        df_balance = df_balance.reindex(full_date_range).ffill().fillna(initial_balance)
        #"""

        # --- DYNAMIC PART: Fetch live balances via FinTS Connector ---
        """
        fin = FinTSConnector()
        bal_dict = fin.get_balance()  # {iban: {"amount": X, "currency": Y}, …}
        initial_balance = sum(item["amount"] for item in bal_dict.values())
        df["cumulative_sum"] = df["amount"].cumsum()

        df_balance = (
            df
            .set_index("date")[ ["cumulative_sum"] ]
            .rename(columns={"cumulative_sum": "account_balance"})
        )

        df_balance = df_balance[~df_balance.index.duplicated(keep="last")]
        df_balance["account_balance"] += initial_balance
        df_balance = df_balance.reindex(full_date_range).ffill().fillna(initial_balance)
        """

        # --- 5) build Plot  ---
        fig = go.Figure()
        # a) output as stacked area (not show hoverinfo for areas)
        for cat in df_area.columns:
            fig.add_trace(go.Scatter(
                name=cat,
                x=df_area.index,
                y=df_area[cat],
                mode="lines",
                stackgroup="same",
                line=dict(width=0, color=self.color_manager.get_color_for_category(cat)),
                hoverinfo="none",
                showlegend=False
            ))

        # b) Income-Line
        fig.add_trace(go.Scatter(
            name="Income",
            x=df_income.index,
            y=df_income["month_value"],
            mode="lines",
            line=dict(width=2, color=self.color_manager.get_color_for_category("Income")),
            hoverinfo="x+y+name"
        ))

        # c) Balance-Line
        fig.add_trace(go.Scatter(
            name="Account Balance",
            x=df_balance.index,
            y=df_balance["account_balance"],
            mode="lines",
            line=dict(width=1, color=self.color_manager.get_color_for_category("Account Balance")),
            hoverinfo="x+y+name"
        ))

        # --- 6) Daily cumsum-Lines with markers & all transactions in the tooltip ---
        df_multi = df[df["category"].isin(area_categories)].copy()
        if not df_multi.empty:
            df_multi["year_month"] = df_multi["date"].dt.to_period("M")
            df_multi = df_multi.sort_values(["category", "year_month", "date"])
            order_map = {cat: i for i, cat in enumerate(area_categories)}

            all_lines = []
            for (cat, period), grp in df_multi.groupby(["category", "year_month"]):
            # (cat, period), grp are key and value in df_multi
                start = pd.Timestamp(period.start_time)
                end   = pd.Timestamp(period.end_time)
                days  = pd.date_range(start=start, end=end, freq="D")

                grp = grp.copy()
                grp["expense_val"] = grp["amount_abs"]

                # 6.1) sum daily values
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

                # 6.2) collect all TX-Details per day (incl. Präfix "Transactions:<br>")
                tx_det = (
                    grp.groupby("date")
                       .apply(
                           lambda g: "Transactions:<br>" +
                                     "<br>".join(f"{int(a)} € – {d}"
                                                 for a, d in zip(g["expense_val"], g["description"]))
                       )
                       .reset_index(name="tx_details")
                )
                tx_det["tx_details"] = tx_det["tx_details"].fillna("")  # missing days -> empty string

                daily = daily.merge(tx_det, on="date", how="left")
                daily["tx_details"] = daily["tx_details"].fillna("")  # NaN → empty string
                daily["marker_size"] = daily["tx_details"].apply(lambda txt: 6 if txt else 0)

                # 6.3) calculate stack-offset (so lines are displayed above area chart)
                def offset(r):
                    # 'r' is a pandas.Series representing one row of the 'daily' DataFrame.
                    # It contains fields such as the date (r["date"]) and the cumulative expense value (r["cum_val"]).

                    # 1) Build the list of categories that lie **below** the current category 'cat' in the stack.
                    #    'order_map' maps each category to its stacking order index
                    #    (e.g. 0 = bottom, 1 = next, etc.).
                    #    Example: if cat="Food" and order_map["Food"]=3, then
                    #    below = area_categories[:3] == ["Rent","Electricity","Landline"].
                    below = area_categories[: order_map[cat]]

                    # 2) If there are any 'below' categories, look up in the pivot table 'df_area'
                    #    at the row for r["date"] the values for all these 'below' categories,
                    #    then sum them. This yields the total stacked height **below** 'cat' on that date.
                    #    If 'below' is empty (i.e. 'cat' is the bottommost category), return 0.
                    return df_area.loc[r["date"], below].sum() if below else 0

                    # 3) Apply the 'offset' function to each row of 'daily' (axis=1 means row-wise).
                    #    The result is a sequence of offset values, which we store in the new column "offset".
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
                    marker=dict(size=sub["marker_size"], color="yellow", symbol="diamond"),
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


