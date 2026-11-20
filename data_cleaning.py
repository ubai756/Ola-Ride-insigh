"""
Ola Ride Insights - Data Cleaning & Preprocessing
-------------------------------------------------
Reads the raw Excel file, cleans it, adds useful derived columns and saves:
  1. ola_rides_clean.csv  -> for Power BI / Tableau / Excel
  2. ola_rides.db         -> SQLite database used by the SQL queries and the Streamlit app

Run:  python data_cleaning.py
Put OLA_DataSet.xlsx in the same folder as this script first.
"""

import sqlite3
import pandas as pd

RAW_FILE = "OLA_DataSet.xlsx"
CLEAN_CSV = "ola_rides_clean.csv"
DB_FILE = "ola_rides.db"

# ---------------------------------------------------------------- 1. LOAD
df = pd.read_excel(RAW_FILE, sheet_name="July")
vehicle_icons = pd.read_excel(RAW_FILE, sheet_name="Sheet2", header=None).dropna()
vehicle_icons.columns = ["Vehicle_Type", "Icon_URL"]

print(f"Raw data: {df.shape[0]:,} rows x {df.shape[1]} columns")

# ---------------------------------------------------------------- 2. CLEAN
# 2a. Tidy column names and text (remove stray spaces)
df.columns = [c.strip().replace(" ", "_") for c in df.columns]
text_cols = df.select_dtypes(include=["object", "string"]).columns
for col in text_cols:
    df[col] = df[col].astype("string").str.strip()

# 2b. Remove duplicates (checked: none in this dataset, kept for safety)
df = df.drop_duplicates(subset="Booking_ID")

# 2c. Fix data types
df["Date"] = pd.to_datetime(df["Date"]).dt.normalize()          # date only
df["Time"] = df["Time"].astype(str)                              # HH:MM:SS text

# 2d. Missing values
# These blanks are NOT errors: they are structural. Example: a cancelled ride
# has no payment method and no rating. So:
#   - text columns  -> "Not Applicable" (clear label for filters / charts)
#   - numeric columns (ratings, TAT) -> left empty, because filling with 0
#     would wrongly pull averages down.
fill_na_cols = [
    "Canceled_Rides_by_Customer",
    "Canceled_Rides_by_Driver",
    "Incomplete_Rides",
    "Incomplete_Rides_Reason",
    "Payment_Method",
]
for col in fill_na_cols:
    df[col] = df[col].fillna("Not Applicable")

# 2e. Vehicle image links live in their own small table (not repeated 100k times)
df = df.drop(columns=["Vehicle_Images"])

# ---------------------------------------------------------------- 3. FEATURES
df["Hour"] = pd.to_datetime(df["Time"], format="%H:%M:%S").dt.hour
df["Day_Name"] = df["Date"].dt.day_name()
df["Day_Of_Week_No"] = df["Date"].dt.dayofweek + 1               # Mon=1 ... Sun=7
df["Is_Weekend"] = df["Day_Of_Week_No"].isin([6, 7]).map({True: "Yes", False: "No"})
df["Time_Of_Day"] = pd.cut(
    df["Hour"],
    bins=[-1, 5, 11, 16, 20, 23],
    labels=["Late Night", "Morning", "Afternoon", "Evening", "Night"],
).astype(str)

# ---------------------------------------------------------------- 4. CHECKS
print("\nBooking status counts:")
print(df["Booking_Status"].value_counts().to_string())
print("\nRemaining missing values (numeric, expected for cancelled rides):")
print(df.isna().sum()[df.isna().sum() > 0].to_string())

# ---------------------------------------------------------------- 5. SAVE
df.to_csv(CLEAN_CSV, index=False)

con = sqlite3.connect(DB_FILE)
df.assign(Date=df["Date"].dt.strftime("%Y-%m-%d")).to_sql(
    "rides", con, if_exists="replace", index=False
)
vehicle_icons.to_sql("vehicle_icons", con, if_exists="replace", index=False)
con.close()

print(f"\nSaved {CLEAN_CSV} and {DB_FILE} ({len(df):,} rows). Done!")
