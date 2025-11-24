from flask import Flask, render_template, request, flash, redirect, url_for
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import datetime
import requests
import os
import logging
from concurrent.futures import ThreadPoolExecutor
from fpdf import FPDF

# ====================================================
# 🌐 Flask App Setup
# ====================================================
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "super_secret_key_123")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] - %(message)s",
    handlers=[logging.FileHandler("app.log"), logging.StreamHandler()]
)

# ====================================================
# 📁 Config
# ====================================================
DATA_DIR = "data"
STATIC_DIR = "static"
BASE_URL = "https://nsearchives.nseindia.com/content/nsccl/fao_participant_oi_{}.csv"
NSE_OPTION_CHAIN_URL = "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"
NSE_HOME_URL = "https://www.nseindia.com"

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

# Predefined NSE holidays
NSE_HOLIDAYS = {
    datetime.date(2025, m, d) for (m, d) in [
        (2, 26), (3, 14), (3, 31), (4, 10), (4, 14),
        (4, 18), (5, 1), (8, 15), (8, 27), (10, 2),
        (10, 21), (10, 22), (11, 5), (12, 25)
    ]
}

# Thread pool for parallel downloads
executor = ThreadPoolExecutor(max_workers=5)

# ====================================================
# 🧩 Utility Functions
# ====================================================
def get_date_string(date: datetime.date) -> str:
    return date.strftime("%d%m%Y")

def adjust_for_holidays(date: datetime.date) -> datetime.date:
    """Ensure date is not weekend or NSE holiday."""
    while date.weekday() > 4 or date in NSE_HOLIDAYS:
        date -= datetime.timedelta(days=1)
    return date

def download_csv(date: datetime.date) -> str:
    """Download NSE OI CSV file for a given date."""
    date_str = get_date_string(date)
    file_path = os.path.join(DATA_DIR, f"{date_str}.csv")

    if os.path.exists(file_path):
        # logging.info(f"Using cached file: {file_path}")
        return file_path

    url = BASE_URL.format(date_str)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Referer": "https://www.nseindia.com"
    }

    logging.info(f"Downloading CSV: {url}")
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.ok:
            with open(file_path, "wb") as f:
                f.write(response.content)
            logging.info(f"✅ Downloaded {file_path}")
            return file_path
        else:
            logging.warning(f"Failed to download {url}: {response.status_code}")
            return None
    except Exception as e:
        logging.error(f"Error downloading {url}: {e}")
        return None

def create_pdf(images: list[str], output_path: str) -> None:
    """Combine chart images into one PDF report."""
    pdf = FPDF()
    for img in images:
        pdf.add_page()
        pdf.image(img, x=10, y=10, w=180)
    pdf.output(output_path)
    logging.info(f"📘 PDF Report saved: {output_path}")

# ====================================================
# 📊 Data Processing Functions
# ====================================================
def load_data(date: datetime.date) -> pd.DataFrame:
    """Load OI data for a single date."""
    file_path = download_csv(date)
    if not file_path:
        return None
    
    cols = [
        "Client Type", "Future Index Long", "Future Index Short",
        "Option Index Call Long", "Option Index Put Long",
        "Option Index Call Short", "Option Index Put Short"
    ]
    try:
        df = pd.read_csv(file_path, skiprows=1, usecols=cols).dropna()
        return df
    except Exception as e:
        logging.error(f"Error reading CSV {file_path}: {e}")
        return None

def fetch_last_n_days_data(end_date: datetime.date, n: int = 5) -> dict:
    """Fetch data for the last n trading days."""
    data_map = {}
    current_date = end_date
    count = 0
    while count < n:
        current_date = adjust_for_holidays(current_date)
        df = load_data(current_date)
        if df is not None:
            data_map[current_date] = df
            count += 1
        current_date -= datetime.timedelta(days=1)
    return data_map

def calculate_net_sentiment(df):
    """Calculate Net Call and Net Put differences."""
    df["Call Diff"] = df["Option Index Call Long"] - df["Option Index Call Short"]
    df["Put Diff"] = df["Option Index Put Long"] - df["Option Index Put Short"]
    df["Net Sentiment"] = df["Call Diff"] - df["Put Diff"] # Positive = Bullish, Negative = Bearish
    return df

# ====================================================
# 📊 Activity Table Logic
# ====================================================
def get_latest_activity_data():
    """
    Finds the latest available data date and the previous trading day.
    Calculates Day-over-Day change in Net OI.
    Returns a dict with date and participant activity.
    """
    # 1. Find Latest Date with Data
    curr_date = datetime.date.today()
    attempts = 0
    curr_df = None
    
    while attempts < 10: # Look back up to 10 days
        # Skip weekends/holidays first
        curr_date = adjust_for_holidays(curr_date)
        
        # Try to load data
        curr_df = load_data(curr_date)
        if curr_df is not None and not curr_df.empty:
            break # Found valid data!
        
        # If not found, go back one day
        curr_date -= datetime.timedelta(days=1)
        attempts += 1
        
    if curr_df is None:
        return None # No data found recently

    # 2. Find Previous Trading Day
    prev_date = curr_date - datetime.timedelta(days=1)
    prev_df = None
    attempts = 0
    while attempts < 10:
        prev_date = adjust_for_holidays(prev_date)
        prev_df = load_data(prev_date)
        if prev_df is not None and not prev_df.empty:
            break
        prev_date -= datetime.timedelta(days=1)
        attempts += 1
        
    if prev_df is None:
        return None # Can't calculate change without previous data

    # 3. Calculate Changes
    # Helper to get Net OI
    def get_net(df, client, type_long, type_short):
        row = df[df["Client Type"] == client]
        if row.empty: return 0
        return int(row[type_long].values[0] - row[type_short].values[0])

    participants = ["FII", "Pro", "DII", "Client"] # Note: CSV uses 'Client' for Retail
    display_names = {"FII": "FII", "Pro": "PRO", "DII": "DII", "Client": "RETAIL"}
    
    results = []
    
    overall_score = 0 # Simple score to determine overall trend

    for p in participants:
        p_data = {"name": display_names[p], "rows": []}
        
        # Instruments to analyze
        instruments = [
            ("Future", "Future Index Long", "Future Index Short"),
            ("CE", "Option Index Call Long", "Option Index Call Short"),
            ("PE", "Option Index Put Long", "Option Index Put Short")
        ]
        
        for instr_name, col_long, col_short in instruments:
            net_curr = get_net(curr_df, p, col_long, col_short)
            net_prev = get_net(prev_df, p, col_long, col_short)
            change = net_curr - net_prev
            
            activity = ""
            trend = ""
            trend_color = "" # green/red
            
            if instr_name == "Future":
                if change > 0: 
                    activity = "Bought Futures"
                    trend = "Bullish"
                    trend_color = "green"
                    if p == "FII": overall_score += 2
                else: 
                    activity = "Sold Futures"
                    trend = "Bearish"
                    trend_color = "red"
                    if p == "FII": overall_score -= 2
            elif instr_name == "CE":
                if change > 0: 
                    activity = "Bought Calls"
                    trend = "Bullish"
                    trend_color = "green"
                    if p == "FII": overall_score += 1
                else: 
                    activity = "Sold Calls"
                    trend = "Bearish"
                    trend_color = "red"
                    if p == "FII": overall_score -= 1
            elif instr_name == "PE":
                if change > 0: 
                    activity = "Bought Puts"
                    trend = "Bearish"
                    trend_color = "red"
                    if p == "FII": overall_score -= 1
                else: 
                    activity = "Sold Puts"
                    trend = "Bullish"
                    trend_color = "green"
                    if p == "FII": overall_score += 1
            
            p_data["rows"].append({
                "instrument": instr_name,
                "change": f"{change:,.0f}",
                "activity": activity,
                "trend": trend,
                "color": trend_color
            })
        results.append(p_data)

    overall_trend = "NEUTRAL"
    overall_color = "gray"
    if overall_score >= 2:
        overall_trend = "BULLISH"
        overall_color = "green"
    elif overall_score <= -2:
        overall_trend = "BEARISH"
        overall_color = "red"

    return {
        "date": curr_date.strftime("%d/%m/%Y"),
        "data": results,
        "overall_trend": overall_trend,
        "overall_color": overall_color
    }

# ====================================================
# 📈 Chart Generation (Advanced)
# ====================================================
def generate_advanced_charts(current_date: datetime.date):
    """Generate all charts for the 7-step analysis."""
    
    # 1. Fetch Data (Current vs Previous for Change, and Last 5 Days for Trend)
    data_map = fetch_last_n_days_data(current_date, n=5)
    sorted_dates = sorted(data_map.keys())
    
    if len(sorted_dates) < 1:
        raise Exception("Not enough data available.")
        
    today_df = data_map[sorted_dates[-1]].copy()
    today_df = calculate_net_sentiment(today_df)
    
    prev_df = data_map[sorted_dates[-2]].copy() if len(sorted_dates) >= 2 else today_df
    
    # Common Layout Settings
    layout_args = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#888",
        margin=dict(l=20, r=20, t=40, b=20)
    )

    charts = {}

    # --- Step 1: Data Preparation and Overview ---
    # Bar Chart: Raw Values
    fig_raw = go.Figure()
    for col in ["Option Index Call Long", "Option Index Put Long"]:
        fig_raw.add_trace(go.Bar(x=today_df["Client Type"], y=today_df[col], name=col))
    fig_raw.update_layout(title="Raw Call vs Put OI", barmode='group', **layout_args)
    fig_raw.write_html(os.path.join(STATIC_DIR, "step1_raw_bar.html"), include_plotlyjs='cdn', full_html=False)
    charts['step1_raw'] = "step1_raw_bar.html"

    # Donut Chart: Share of Total OI
    total_oi = today_df[["Option Index Call Long", "Option Index Put Long"]].sum(axis=1)
    fig_donut = px.pie(values=total_oi, names=today_df["Client Type"], title="Participant Market Share", hole=0.4)
    fig_donut.update_layout(**layout_args)
    fig_donut.write_html(os.path.join(STATIC_DIR, "step1_donut.html"), include_plotlyjs='cdn', full_html=False)
    charts['step1_donut'] = "step1_donut.html"

    # --- Step 2: Call-Put Difference Analysis ---
    # Horizontal Bar: Net Diff
    fig_hbar = px.bar(today_df, x="Net Sentiment", y="Client Type", orientation='h', 
                      title="Net Sentiment (Call Diff - Put Diff)", color="Net Sentiment",
                      color_continuous_scale=px.colors.diverging.RdBu)
    fig_hbar.update_layout(**layout_args)
    fig_hbar.write_html(os.path.join(STATIC_DIR, "step2_hbar.html"), include_plotlyjs='cdn', full_html=False)
    charts['step2_hbar'] = "step2_hbar.html"

    # Stacked Bar: Call Diff vs Put Diff
    fig_stack = go.Figure()
    fig_stack.add_trace(go.Bar(x=today_df["Client Type"], y=today_df["Call Diff"], name="Net Call"))
    fig_stack.add_trace(go.Bar(x=today_df["Client Type"], y=today_df["Put Diff"], name="Net Put"))
    fig_stack.update_layout(title="Net Call vs Net Put Exposure", barmode='relative', **layout_args)
    fig_stack.write_html(os.path.join(STATIC_DIR, "step2_stack.html"), include_plotlyjs='cdn', full_html=False)
    charts['step2_stack'] = "step2_stack.html"

    # --- Step 3: Total Market Call-Put Difference ---
    # Column Chart
    total_calls = today_df["Option Index Call Long"].sum()
    total_puts = today_df["Option Index Put Long"].sum()
    fig_mkt = go.Figure(data=[go.Bar(x=["Total Calls", "Total Puts"], y=[total_calls, total_puts], 
                                     marker_color=['#10B981', '#EF4444'])])
    fig_mkt.update_layout(title="Total Market Open Interest", **layout_args)
    fig_mkt.write_html(os.path.join(STATIC_DIR, "step3_col.html"), include_plotlyjs='cdn', full_html=False)
    charts['step3_col'] = "step3_col.html"

    # --- Step 4: FII & Pro Specific ---
    # Radar Chart
    categories = ["Future Index Long", "Future Index Short", "Option Index Call Long", "Option Index Put Long"]
    fig_radar = go.Figure()
    for client in ["FII", "PRO"]:
        client_data = today_df[today_df["Client Type"] == client]
        if not client_data.empty:
            values = client_data[categories].values.flatten().tolist()
            fig_radar.add_trace(go.Scatterpolar(r=values, theta=categories, fill='toself', name=client))
    fig_radar.update_layout(title="FII vs PRO Positioning", polar=dict(radialaxis=dict(visible=True)), **layout_args)
    fig_radar.write_html(os.path.join(STATIC_DIR, "step4_radar.html"), include_plotlyjs='cdn', full_html=False)
    charts['step4_radar'] = "step4_radar.html"

    # --- Step 5: Trend Analysis Over Time ---
    # Line Chart
    trend_data = []
    for d in sorted_dates:
        day_df = calculate_net_sentiment(data_map[d].copy())
        for client in ["FII", "PRO", "Client", "DII"]:
            row = day_df[day_df["Client Type"] == client]
            if not row.empty:
                trend_data.append({
                    "Date": d, 
                    "Client": client, 
                    "Net Sentiment": row["Net Sentiment"].values[0]
                })
    
    trend_df = pd.DataFrame(trend_data)
    fig_trend = px.line(trend_df, x="Date", y="Net Sentiment", color="Client", markers=True, title="5-Day Net Sentiment Trend")
    fig_trend.update_layout(**layout_args)
    fig_trend.write_html(os.path.join(STATIC_DIR, "step5_trend.html"), include_plotlyjs='cdn', full_html=False)
    charts['step5_trend'] = "step5_trend.html"

    # --- Step 6: Advanced Combinational Visualization ---
    # Scatter Plot: Net Sentiment vs Change in OI
    # Calculate change from yesterday
    merged = pd.merge(today_df, prev_df, on="Client Type", suffixes=("", "_prev"))
    merged["OI Change"] = (merged["Option Index Call Long"] + merged["Option Index Put Long"]) - \
                          (merged["Option Index Call Long_prev"] + merged["Option Index Put Long_prev"])
    
    fig_scatter = px.scatter(merged, x="Net Sentiment", y="OI Change", color="Client Type", size="Option Index Call Long",
                             title="Sentiment vs OI Change", hover_data=["Client Type"])
    fig_scatter.add_vline(x=0, line_dash="dash", line_color="gray")
    fig_scatter.add_hline(y=0, line_dash="dash", line_color="gray")
    fig_scatter.update_layout(**layout_args)
    fig_scatter.write_html(os.path.join(STATIC_DIR, "step6_scatter.html"), include_plotlyjs='cdn', full_html=False)
    charts['step6_scatter'] = "step6_scatter.html"

    # Heatmap: Participant vs Position Type Intensity
    # Normalize data for heatmap
    heatmap_data = today_df.set_index("Client Type")[["Future Index Long", "Future Index Short", "Option Index Call Long", "Option Index Put Long"]]
    fig_heat = px.imshow(heatmap_data, text_auto=True, aspect="auto", title="Position Intensity Heatmap",
                         color_continuous_scale="Viridis")
    fig_heat.update_layout(**layout_args)
    fig_heat.write_html(os.path.join(STATIC_DIR, "step6_heat.html"), include_plotlyjs='cdn', full_html=False)
    charts['step6_heat'] = "step6_heat.html"

    # --- Step 8: Requested Custom Tables & Charts ---
    # Prepare Data with TOTAL row
    step8_df = today_df.copy()
    numeric_cols = step8_df.select_dtypes(include='number').columns
    total_row = step8_df[numeric_cols].sum()
    total_row["Client Type"] = "TOTAL"
    step8_df = pd.concat([step8_df, pd.DataFrame([total_row])], ignore_index=True)

    # Helper for Color Formatting (Green/Red)
    def get_colors(values):
        return ['#86efac' if v >= 0 else '#fca5a5' for v in values] # Light Green / Light Red

    # 1. Table: Call Diff vs Put Diff
    fig_tbl1 = go.Figure(data=[go.Table(
        header=dict(values=["Client Type", "Call Diff (Long-Short)", "Put Diff (Long-Short)"],
                    fill_color='#d1d5db', align='center', font=dict(color='black', size=12)),
        cells=dict(values=[step8_df["Client Type"], step8_df["Call Diff"], step8_df["Put Diff"]],
                   fill_color=[['#f3f4f6']*len(step8_df), get_colors(step8_df["Call Diff"]), get_colors(step8_df["Put Diff"])],
                   align='center', font=dict(color='black', size=11))
    )])
    fig_tbl1.update_layout(title="Call & Put Diff per Client", margin=dict(l=0, r=0, t=30, b=0))
    fig_tbl1.write_html(os.path.join(STATIC_DIR, "step8_table1.html"), include_plotlyjs='cdn', full_html=False)
    charts['step8_table1'] = "step8_table1.html"

    # 2. Table: Net Sentiment
    fig_tbl2 = go.Figure(data=[go.Table(
        header=dict(values=["Client Type", "Call-Put Diff (Call-Put)"],
                    fill_color='#d1d5db', align='center', font=dict(color='black', size=12)),
        cells=dict(values=[step8_df["Client Type"], step8_df["Net Sentiment"]],
                   fill_color=[['#f3f4f6']*len(step8_df), get_colors(step8_df["Net Sentiment"])],
                   align='center', font=dict(color='black', size=11))
    )])
    fig_tbl2.update_layout(title="Net Sentiment Diff", margin=dict(l=0, r=0, t=30, b=0))
    fig_tbl2.write_html(os.path.join(STATIC_DIR, "step8_table2.html"), include_plotlyjs='cdn', full_html=False)
    charts['step8_table2'] = "step8_table2.html"

    # 3. Charts: Side-by-Side Diff Bars
    fig_sb = make_subplots(rows=1, cols=2, subplot_titles=("Call Diff", "Put Diff"))
    
    # Call Diff Bar
    colors_call = ['#059669' if v >= 0 else '#dc2626' for v in step8_df["Call Diff"]]
    fig_sb.add_trace(go.Bar(x=step8_df["Client Type"], y=step8_df["Call Diff"], marker_color=colors_call, name="Call Diff"), row=1, col=1)
    
    # Put Diff Bar
    colors_put = ['#059669' if v >= 0 else '#dc2626' for v in step8_df["Put Diff"]]
    fig_sb.add_trace(go.Bar(x=step8_df["Client Type"], y=step8_df["Put Diff"], marker_color=colors_put, name="Put Diff"), row=1, col=2)

    fig_sb.update_layout(title="Call & Put Diff per Client Type", showlegend=False, **layout_args)
    fig_sb.write_html(os.path.join(STATIC_DIR, "step8_charts.html"), include_plotlyjs='cdn', full_html=False)
    charts['step8_charts'] = "step8_charts.html"

    return charts

# ====================================================
# ⛓️ Option Chain Logic
# ====================================================
def fetch_option_chain_data():
    """Fetch option chain JSON from NSE."""
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.nseindia.com/option-chain"
    }
    session.headers.update(headers)
    
    try:
        session.get(NSE_HOME_URL, timeout=10) # Set cookies
        resp = session.get(NSE_OPTION_CHAIN_URL, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logging.error(f"Error fetching option chain: {e}")
        return None

def process_option_chain(data):
    """Process JSON to get first 2 expiries data and spot price."""
    if not data: return [], None
    
    # Extract spot price
    spot_price = data["records"].get("underlyingValue", 0)
    
    expiry_dates = data["records"]["expiryDates"][:2]
    filtered_data = [item for item in data["records"]["data"] if item.get("expiryDate") in expiry_dates]
    
    # Sort by expiry and then strike price
    filtered_data.sort(key=lambda x: (x["expiryDate"], x["strikePrice"]))
    
    # Find ATM strike (closest to spot price)
    atm_strike = None
    if spot_price and filtered_data:
        # Round to nearest 50 (Nifty strikes are in multiples of 50)
        atm_strike = round(spot_price / 50) * 50
    
    return filtered_data, spot_price, atm_strike

# ====================================================
# 🌍 Flask Routes
# ====================================================
@app.route("/", methods=["GET", "POST"])
def index():
    # Simplified Index for Dashboard
    charts = None
    activity_data = None
    try:
        # Auto-load latest available data
        today = datetime.date.today()
        target_date = adjust_for_holidays(today)
        
        # Generate Charts
        charts = generate_advanced_charts(target_date)
        
        # Generate Activity Table Data
        activity_data = get_latest_activity_data()
        
    except Exception as e:
        logging.error(f"Index Auto-Load Error: {e}")
    
    return render_template("index.html", charts=charts, activity_data=activity_data)

@app.route("/compare", methods=["GET", "POST"])
def compare():
    if request.method == "POST":
        try:
            date_str = request.form.get("date")
            if not date_str:
                 flash("Please select a date.", "warning")
                 return redirect(url_for("compare"))

            date_input = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
            date_input = adjust_for_holidays(date_input)
            
            # Generate all advanced charts
            charts = generate_advanced_charts(date_input)
            
            return render_template("compare_result.html", charts=charts)

        except Exception as e:
            logging.error(f"Compare Error: {e}")
            flash(f"Error: {e}", "error")
            return redirect(url_for("compare"))

    return render_template("compare.html")

@app.route("/option-chain")
def option_chain_view():
    raw_data = fetch_option_chain_data()
    if raw_data:
        processed_data, spot_price, atm_strike = process_option_chain(raw_data)
        return render_template("option_chain.html", data=processed_data, spot_price=spot_price, atm_strike=atm_strike)
    else:
        flash("Failed to fetch Option Chain data from NSE.", "error")
        return redirect(url_for("index"))

# ====================================================
# 🚀 Run App
# ====================================================
if __name__ == "__main__":
    app.run(debug=True, port=5001)
