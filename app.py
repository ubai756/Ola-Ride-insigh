"""Ola Ride Insights - Streamlit dashboard (reads ola_rides.db)."""
import sqlite3
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components

DB = Path(__file__).parent / "ola_rides.db"
POWERBI_EMBED_URL = ""  # paste your Power BI "Publish to web" link here later

CYAN, VIOLET, PINK, AMBER = "#22D3EE", "#A78BFA", "#F472B6", "#FBBF24"
STATUS_COLORS = {"Success": CYAN, "Canceled by Customer": PINK,
                 "Canceled by Driver": "#E11D48", "Driver Not Found": VIOLET}
NA = "Not Applicable"

QUERIES = {
    "1. All successful bookings": """SELECT *
FROM rides
WHERE Booking_Status = 'Success'""",
    "2. Average ride distance per vehicle type": """SELECT Vehicle_Type,
       ROUND(AVG(Ride_Distance), 2) AS Avg_Ride_Distance_Km
FROM rides
GROUP BY Vehicle_Type
ORDER BY Avg_Ride_Distance_Km DESC""",
    "2b. Average distance per vehicle type (completed rides only)": """SELECT Vehicle_Type,
       ROUND(AVG(Ride_Distance), 2) AS Avg_Distance_Completed_Rides_Km
FROM rides
WHERE Booking_Status = 'Success'
GROUP BY Vehicle_Type
ORDER BY Avg_Distance_Completed_Rides_Km DESC""",
    "3. Rides cancelled by customers": """SELECT COUNT(*) AS Total_Cancelled_By_Customers
FROM rides
WHERE Booking_Status = 'Canceled by Customer'""",
    "4. Top 5 customers by number of rides": """SELECT Customer_ID, COUNT(*) AS Total_Rides
FROM rides
GROUP BY Customer_ID
ORDER BY Total_Rides DESC, Customer_ID
LIMIT 5""",
    "5. Driver cancels: personal & car related issues": """SELECT COUNT(*) AS Driver_Cancels_Personal_Car_Issue
FROM rides
WHERE Canceled_Rides_by_Driver = 'Personal & Car related issue'""",
    "6. Max & min driver rating for Prime Sedan": """SELECT MAX(Driver_Ratings) AS Max_Driver_Rating,
       MIN(Driver_Ratings) AS Min_Driver_Rating
FROM rides
WHERE Vehicle_Type = 'Prime Sedan' AND Driver_Ratings IS NOT NULL""",
    "7. Rides paid using UPI": """SELECT *
FROM rides
WHERE Payment_Method = 'UPI'""",
    "8. Average customer rating per vehicle type": """SELECT Vehicle_Type,
       ROUND(AVG(Customer_Rating), 2) AS Avg_Customer_Rating
FROM rides
WHERE Customer_Rating IS NOT NULL
GROUP BY Vehicle_Type
ORDER BY Avg_Customer_Rating DESC""",
    "9. Total booking value of successful rides": """SELECT SUM(Booking_Value) AS Total_Booking_Value_Successful_Rides
FROM rides
WHERE Booking_Status = 'Success'""",
    "10. Incomplete rides with reason": """SELECT Booking_ID, Customer_ID, Vehicle_Type, Incomplete_Rides_Reason
FROM rides
WHERE Incomplete_Rides = 'Yes'""",
}

st.set_page_config(page_title="Ola Ride Insights", layout="wide")
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Lora:wght@400;500;600&family=Playfair+Display:wght@500;700&display=swap');
.stApp, .stApp p, .stApp label, .stApp li, .stApp input, .stApp textarea, .stApp button {font-family:'Lora',Georgia,'Times New Roman',serif;}
.stApp h1, .stApp h2, .stApp h3, .stApp h4, [data-testid="stMetricValue"], .hero h1, .face h4, .face b {font-family:'Playfair Display',Georgia,serif !important;letter-spacing:.3px;}
.stApp, .stApp p, .stApp label, .stApp li, .stApp h1, .stApp h2, .stApp h3, .stApp h4, [data-testid="stMetricLabel"], [data-testid="stMetricLabel"] *, [data-testid="stMetricValue"], [data-testid="stWidgetLabel"] *, [data-testid="stRadio"] *, [data-baseweb="select"] div, [data-baseweb="select"] span, [data-testid="stAlert"] * {color:#F8F5FF !important;}
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] * {color:rgba(248,245,255,.72) !important;}

.stApp {isolation:isolate;background:linear-gradient(135deg,#0F0C29,#302B63 35%,#7C3AED 68%,#DB2777 100%);background-size:300% 300%;animation:flow 18s ease infinite;}
.stApp::before, .stApp::after {content:"";position:fixed;border-radius:50%;filter:blur(90px);z-index:-1;pointer-events:none;animation:float 14s ease-in-out infinite;}
.stApp::before {width:440px;height:440px;background:#22D3EE;opacity:.30;top:-90px;right:8%;}
.stApp::after {width:380px;height:380px;background:#F472B6;opacity:.28;bottom:-70px;left:32%;animation-delay:-6s;}
[data-testid="stAppViewContainer"], [data-testid="stMain"], [data-testid="stHeader"] {background:transparent !important;}
@keyframes flow {0%{background-position:0% 50%}50%{background-position:100% 50%}100%{background-position:0% 50%}}
@keyframes float {0%,100%{transform:translate(0,0)}50%{transform:translate(45px,-55px)}}
@keyframes rise {from{opacity:0;transform:translateY(26px)}to{opacity:1;transform:none}}
@keyframes shine {0%{left:-60%}60%,100%{left:130%}}

[data-testid="stSidebar"] {background:rgba(255,255,255,.08) !important;backdrop-filter:blur(22px);-webkit-backdrop-filter:blur(22px);border-right:1px solid rgba(255,255,255,.18);}
[data-testid="stSidebar"] > div {background:transparent !important;}
[data-testid="stMainBlockContainer"] {animation:rise .7s ease both;}

[data-testid="stMetric"], [data-testid="stPlotlyChart"], [data-testid="stDataFrame"], [data-testid="stExpander"], [data-testid="stCode"], [data-testid="stAlert"] {
  background:rgba(255,255,255,.10);backdrop-filter:blur(18px) saturate(140%);-webkit-backdrop-filter:blur(18px) saturate(140%);
  border:1px solid rgba(255,255,255,.22);border-radius:20px;overflow:hidden;
  box-shadow:0 10px 36px rgba(10,5,40,.35), inset 0 1px 0 rgba(255,255,255,.25);}
[data-testid="stPlotlyChart"] {padding:.6rem;animation:rise .9s ease both;}
[data-testid="stMetric"] {padding:1rem 1.2rem;animation:rise .8s ease both;transition:transform .35s ease, box-shadow .35s ease;}
[data-testid="stMetric"]:hover {transform:translateY(-6px) scale(1.02);box-shadow:0 18px 44px rgba(34,211,238,.38), inset 0 1px 0 rgba(255,255,255,.3);}
[data-testid="stMetricValue"] {font-size:1.9rem;}
[data-testid="stMetricValue"] > div {overflow:visible !important;text-overflow:clip !important;}

.hero {position:relative;overflow:hidden;padding:1.8rem 2rem;border-radius:26px;margin-bottom:1.2rem;
  background:linear-gradient(120deg,rgba(34,211,238,.30),rgba(124,58,237,.38),rgba(244,114,182,.32));background-size:200% 200%;animation:flow 10s ease infinite;
  border:1px solid rgba(255,255,255,.32);backdrop-filter:blur(22px);-webkit-backdrop-filter:blur(22px);
  box-shadow:0 16px 48px rgba(10,5,40,.45), inset 0 1px 0 rgba(255,255,255,.35);}
.hero h1 {margin:0;font-size:2.6rem;color:#fff !important;}
.hero p {margin:.4rem 0 0;color:rgba(255,255,255,.88) !important;font-style:italic;font-size:1.05rem;}
.hero::after {content:"";position:absolute;top:0;left:-60%;width:40%;height:100%;background:linear-gradient(100deg,transparent,rgba(255,255,255,.28),transparent);transform:skewX(-20deg);animation:shine 5s ease-in-out infinite;}

.flips {display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:1rem;margin-top:.6rem;}
.flip {perspective:1000px;height:180px;outline:none;}
.flip-in {position:relative;width:100%;height:100%;transition:transform .8s cubic-bezier(.4,.2,.2,1);transform-style:preserve-3d;}
.flip:hover .flip-in, .flip:focus .flip-in {transform:rotateY(180deg);}
.face {position:absolute;inset:0;backface-visibility:hidden;-webkit-backface-visibility:hidden;border-radius:20px;padding:1.1rem;display:flex;flex-direction:column;justify-content:center;gap:.4rem;border:1px solid rgba(255,255,255,.28);backdrop-filter:blur(16px);box-shadow:0 10px 30px rgba(10,5,40,.35);}
.front {background:linear-gradient(145deg,rgba(255,255,255,.18),rgba(255,255,255,.05));}
.back {transform:rotateY(180deg);background:linear-gradient(145deg,rgba(124,58,237,.60),rgba(236,72,153,.50));}
.face h4 {margin:0;font-size:1.3rem;color:#fff !important;}
.face b {font-size:1.2rem;color:#fff !important;line-height:1.3;}
.face small {color:rgba(255,255,255,.78) !important;font-style:italic;}

[data-baseweb="select"] > div, [data-baseweb="input"] > div, [data-baseweb="textarea"] {background:rgba(255,255,255,.10) !important;border:1px solid rgba(255,255,255,.25) !important;border-radius:12px !important;}
.stApp input, .stApp textarea {color:#F8F5FF !important;}
span[data-baseweb="tag"] {background:linear-gradient(90deg,#7C3AED,#EC4899) !important;border-radius:10px !important;}
span[data-baseweb="tag"] * {color:#fff !important;}
.stButton > button, .stDownloadButton > button {background:linear-gradient(90deg,#7C3AED,#EC4899);color:#fff;border:none;border-radius:14px;padding:.55rem 1.3rem;transition:transform .25s ease, box-shadow .25s ease;}
.stButton > button:hover, .stDownloadButton > button:hover {transform:translateY(-3px);box-shadow:0 12px 28px rgba(236,72,153,.45);color:#fff;}
hr {border-color:rgba(255,255,255,.2) !important;}
@media (prefers-reduced-motion:reduce) {* {animation:none !important;transition:none !important;}}
</style>""", unsafe_allow_html=True)


@st.cache_data
def load():
    con = sqlite3.connect(DB)
    data = pd.read_sql("SELECT * FROM rides", con, parse_dates=["Date"])
    con.close()
    return data


def run_sql(query):
    con = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    try:
        return pd.read_sql(query, con)
    finally:
        con.close()


def show(fig, height=360):
    fig.update_layout(template="plotly_dark", height=height, margin=dict(l=10, r=10, t=50, b=10),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font=dict(family="Lora, Georgia, serif", color="#F8F5FF"),
                      title_font=dict(family="Playfair Display, Georgia, serif", size=18),
                      legend=dict(bgcolor="rgba(0,0,0,0)"))
    fig.update_xaxes(gridcolor="rgba(255,255,255,.12)")
    fig.update_yaxes(gridcolor="rgba(255,255,255,.12)")
    st.plotly_chart(fig, theme=None)


def bar(data, x, y, title, color=CYAN, horizontal=False):
    fig = px.bar(data, x=x, y=y, title=title, text_auto=".3s",
                 color_discrete_sequence=[color],
                 orientation="h" if horizontal else "v")
    if horizontal:
        fig.update_layout(yaxis=dict(autorange="reversed"))
    show(fig)


def reasons(frame, col, title, color):
    s = frame.loc[frame[col] != NA, col].value_counts().reset_index()
    s.columns = ["Reason", "Rides"]
    bar(s, "Rides", "Reason", title, color, horizontal=True)


def top(s):
    return s.value_counts().idxmax() if len(s) else "n/a"


df = load()

# ------------------------------------------------------------ sidebar
st.sidebar.title("Ola Ride Insights")
PAGES = ["Overview", "Vehicle Type", "Revenue", "Cancellations", "Ratings",
         "SQL Insights", "Data Explorer", "Power BI"]
page = st.sidebar.radio("Go to", PAGES)
st.sidebar.markdown("---")
st.sidebar.subheader("Filters")
dmin, dmax = df.Date.min().date(), df.Date.max().date()
dates = st.sidebar.date_input("Date range", (dmin, dmax), min_value=dmin, max_value=dmax)
start, end = dates if isinstance(dates, (tuple, list)) and len(dates) == 2 else (dmin, dmax)
all_v, all_s = sorted(df.Vehicle_Type.unique()), sorted(df.Booking_Status.unique())
vehicles = st.sidebar.multiselect("Vehicle type", all_v, default=all_v)
statuses = st.sidebar.multiselect("Booking status", all_s, default=all_s)

f = df[(df.Date >= pd.Timestamp(start)) & (df.Date <= pd.Timestamp(end))
       & df.Vehicle_Type.isin(vehicles) & df.Booking_Status.isin(statuses)]
ok = f[f.Booking_Status == "Success"]

st.markdown('<div class="hero"><h1>Ola Ride Insights</h1>'
            '<p>Ride-sharing analytics for July 2024: bookings, revenue, cancellations and ratings</p></div>',
            unsafe_allow_html=True)

if page in PAGES[:5] and f.empty:
    st.warning("No rides match the current filters. Please widen your selection in the sidebar.")
    st.stop()

# ------------------------------------------------------------ pages
if page == "Overview":
    c = st.columns(5)
    c[0].metric("Total bookings", f"{len(f):,}")
    c[1].metric("Success rate", f"{len(ok) / len(f):.1%}")
    c[2].metric("Revenue (successful)", f"₹{ok.Booking_Value.sum() / 1e7:.2f} Cr")
    c[3].metric("Avg distance (km)", f"{ok.Ride_Distance.mean():.1f}")
    c[4].metric("Avg driver rating", f"{ok.Driver_Ratings.mean():.2f}")

    left, right = st.columns([3, 2])
    with left:
        daily = f.groupby("Date").size().reset_index(name="Rides")
        show(px.area(daily, x="Date", y="Rides", title="Ride volume over time",
                     color_discrete_sequence=[CYAN]))
    with right:
        show(px.pie(f, names="Booking_Status", hole=0.55, title="Booking status breakdown",
                    color="Booking_Status", color_discrete_map=STATUS_COLORS))
    hourly = f.groupby("Hour").size().reset_index(name="Rides")
    bar(hourly, "Hour", "Rides", "Peak demand by hour of day")

    st.subheader("Key insights")
    peak = int(hourly.loc[hourly.Rides.idxmax(), "Hour"])
    cards = [
        ("Peak demand", f"{peak}:00 to {peak + 1}:00", "Best window to keep more drivers online"),
        ("Completion rate", f"{len(ok) / len(f):.1%}", "Share of bookings that became completed rides"),
        ("Customer cancellations", top(f.loc[f.Canceled_Rides_by_Customer != NA, "Canceled_Rides_by_Customer"]), "Most common reason customers cancel"),
        ("Driver cancellations", top(f.loc[f.Canceled_Rides_by_Driver != NA, "Canceled_Rides_by_Driver"]), "Most common reason drivers cancel"),
        ("Payment method", top(ok.Payment_Method), "Most used way to pay for completed rides"),
    ]
    st.markdown('<div class="flips">' + "".join(
        f'<div class="flip" tabindex="0"><div class="flip-in"><div class="face front"><h4>{t}</h4><small>Hover to flip</small></div>'
        f'<div class="face back"><b>{v}</b><small>{d}</small></div></div></div>' for t, v, d in cards) + '</div>',
        unsafe_allow_html=True)

elif page == "Vehicle Type":
    dist = ok.groupby("Vehicle_Type").Ride_Distance.sum().nlargest(5).reset_index()
    bar(dist, "Vehicle_Type", "Ride_Distance", "Top 5 vehicle types by total ride distance (km)")
    a, b = st.columns(2)
    with a:
        avg = ok.groupby("Vehicle_Type").Ride_Distance.mean().round(2).reset_index()
        bar(avg, "Vehicle_Type", "Ride_Distance", "Average distance per completed ride (km)", VIOLET)
    with b:
        rat = ok.groupby("Vehicle_Type").Customer_Rating.mean().round(2).reset_index()
        bar(rat, "Vehicle_Type", "Customer_Rating", "Average customer rating", CYAN)

elif page == "Revenue":
    a, b = st.columns(2)
    with a:
        pay = ok.groupby("Payment_Method").Booking_Value.sum().reset_index()
        show(px.pie(pay, names="Payment_Method", values="Booking_Value", hole=0.5,
                    title="Revenue by payment method",
                    color_discrete_sequence=[CYAN, VIOLET, PINK, AMBER]))
    with b:
        cust = ok.groupby("Customer_ID").Booking_Value.sum().nlargest(5).reset_index()
        bar(cust, "Booking_Value", "Customer_ID", "Top 5 customers by total booking value (₹)",
            horizontal=True)
    day = ok.groupby("Date").Ride_Distance.sum().reset_index()
    show(px.line(day, x="Date", y="Ride_Distance", title="Total ride distance per day (km)",
                 color_discrete_sequence=[CYAN]))

elif page == "Cancellations":
    a, b = st.columns(2)
    with a:
        reasons(f, "Canceled_Rides_by_Customer", "Cancellation reasons: customers", PINK)
    with b:
        reasons(f, "Canceled_Rides_by_Driver", "Cancellation reasons: drivers", "#E11D48")
    reasons(f, "Incomplete_Rides_Reason", "Incomplete ride reasons", VIOLET)

elif page == "Ratings":
    a, b = st.columns(2)
    with a:
        show(px.histogram(ok, x="Driver_Ratings", nbins=20, title="Driver ratings distribution",
                          color_discrete_sequence=[CYAN]))
    with b:
        show(px.histogram(ok, x="Customer_Rating", nbins=20, title="Customer ratings distribution",
                          color_discrete_sequence=[VIOLET]))
    show(px.density_heatmap(ok, x="Customer_Rating", y="Driver_Ratings", nbinsx=20, nbinsy=20,
                            title="Customer vs driver ratings",
                            color_continuous_scale=["#1E1B4B", "#7C3AED", "#EC4899", "#FBBF24"]), height=420)

elif page == "SQL Insights":
    st.subheader("SQL query results")
    st.caption("Queries run live on the database using all bookings (sidebar filters do not apply here).")
    name = st.selectbox("Choose a question", list(QUERIES))
    sql = QUERIES[name]
    st.code(sql, language="sql")
    res = run_sql(sql)
    st.success(f"{len(res):,} row(s) returned" + (" (showing first 1,000)" if len(res) > 1000 else ""))
    st.dataframe(res.head(1000))
    st.download_button("Download result as CSV", res.to_csv(index=False),
                       "query_result.csv", "text/csv")
    with st.expander("Run your own SELECT query"):
        q = st.text_area("SQL", "SELECT Vehicle_Type, COUNT(*) AS Rides FROM rides GROUP BY Vehicle_Type")
        if st.button("Run query"):
            if q.strip().lower().startswith("select"):
                try:
                    st.dataframe(run_sql(q).head(5000))
                except Exception as e:
                    st.error(f"Query error: {e}")
            else:
                st.error("Only SELECT queries are allowed.")

elif page == "Data Explorer":
    st.subheader("Explore and search the data")
    c1, c2 = st.columns(2)
    term = c1.text_input("Search Booking ID or Customer ID")
    loc = c2.selectbox("Pickup location", ["All"] + sorted(df.Pickup_Location.unique()))
    view = f
    if term:
        view = view[view.Booking_ID.str.contains(term, case=False, regex=False)
                    | view.Customer_ID.str.contains(term, case=False, regex=False)]
    if loc != "All":
        view = view[view.Pickup_Location == loc]
    st.caption(f"{len(view):,} rides match (sidebar filters also apply)")
    st.dataframe(view.head(2000))
    st.download_button("Download filtered data", view.to_csv(index=False),
                       "filtered_rides.csv", "text/csv")

elif page == "Power BI":
    st.subheader("Power BI dashboard")
    if POWERBI_EMBED_URL:
        components.iframe(POWERBI_EMBED_URL, height=700, scrolling=True)
    else:
        st.info("The Power BI report isn't connected yet. Once it is published, paste its "
                "embed link into `POWERBI_EMBED_URL` at the top of `app.py` and it will "
                "appear here.")

st.markdown("---")
st.caption("Ola Ride Insights · Data: July 2024 Ola bookings · Built with Streamlit")
