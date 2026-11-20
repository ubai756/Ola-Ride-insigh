# 🚖 Ola Ride Insights

An interactive analytics dashboard for Ola ride-sharing data (July 2024, ~103,000 bookings).
It covers data cleaning, SQL analysis and a Streamlit web app, with a Power BI dashboard planned.

## Features
- **Overview**: KPIs, ride volume over time, booking status breakdown, peak hours, key insights
- **Vehicle Type**: distance and rating comparison across vehicle types
- **Revenue**: revenue by payment method, top customers, daily distance
- **Cancellations**: why customers and drivers cancel, and why rides end incomplete
- **Ratings**: driver and customer rating distributions
- **SQL Insights**: the 10 project questions, run live, plus a box for your own SELECT queries
- **Data Explorer**: search by Booking ID / Customer ID, filter, download CSV
- **Power BI**: embed slot for the published report

## Project files
| File | Purpose |
|---|---|
| `app.py` | Streamlit application |
| `data_cleaning.py` | Cleans the raw Excel file, creates the CSV and database |
| `sql_queries.sql` | The 10 SQL queries with comments |
| `ola_rides.db` | SQLite database used by the app |
| `ola_rides_clean.csv` | Cleaned data (for Power BI / Tableau) |
| `requirements.txt` | Python packages |
| `.streamlit/config.toml` | Glassmorphism dark theme |

## Data cleaning summary
- Fixed data types and removed stray spaces; checked for duplicate bookings (none)
- Missing text values (e.g. payment method for cancelled rides) labelled "Not Applicable"
- Missing ratings and turnaround times left empty so averages stay accurate
- Added Hour, Day_Name, Is_Weekend and Time_Of_Day columns

## Run locally
```
pip install -r requirements.txt
streamlit run app.py
```

## Tech stack
Python, Pandas, SQLite, Plotly, Streamlit

## License
MIT
