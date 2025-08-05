from flask import Flask, render_template, request, flash, redirect, url_for
import plotly.graph_objects as go
import plotly.express as px
import plotly.io as pio
from fpdf import FPDF
import pandas as pd
import datetime
import requests
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key45dxvxdfet4'

pio.kaleido.scope.default_format = "png"
# pio.kaleido.scope.default_width = 800
# pio.kaleido.scope.default_height = 600

# === CONFIG ===
DATA_DIR = 'data'
BASE_URL = 'https://nsearchives.nseindia.com/content/nsccl/fao_participant_oi_{}.csv'
os.makedirs(DATA_DIR, exist_ok=True)

# === HOLIDAYS ===
NSE_HOLIDAYS = [
    datetime.date(2025, 2, 26),
    datetime.date(2025, 3, 14),
    datetime.date(2025, 3, 31),
    datetime.date(2025, 4, 10),
    datetime.date(2025, 4, 14),
    datetime.date(2025, 4, 18),
    datetime.date(2025, 5, 1),
    datetime.date(2025, 8, 15),
    datetime.date(2025, 8, 27),
    datetime.date(2025, 10, 2),
    datetime.date(2025, 10, 21),
    datetime.date(2025, 10, 22),
    datetime.date(2025, 11, 5),
    datetime.date(2025, 12, 25),
]
# === HELPERS ===

def create_pdf(images, output_file):
    pdf = FPDF()
    for img in images:
        pdf.add_page()
        pdf.image(img, x=10, y=10, w=pdf.w - 20)  # simple fit
    pdf.output(output_file)

def get_date_string(date):
    return date.strftime('%d%m%Y')

def adjust_to_weekday(date):
    """Adjust date backward if it's Sat/Sun"""
    if date.weekday() == 5:
        return date - datetime.timedelta(days=1)  # Saturday → Friday
    elif date.weekday() == 6:
        return date - datetime.timedelta(days=2)  # Sunday → Friday
    else:
        return date

def adjust_for_holidays(date):
    """
    Keep adjusting backward until the date is not a weekend or NSE holiday.
    """
    while date in NSE_HOLIDAYS or date.weekday() > 4:
        date = date - datetime.timedelta(days=1)
    return date

def download_csv(date):
    date_str = get_date_string(date)
    url = BASE_URL.format(date_str)
    save_path = os.path.join(DATA_DIR, f"{date_str}.csv")

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://www.nseindia.com",
    }

    print(f"Downloading: {url}")
    response = requests.get(url, headers=headers, timeout=10)
    if response.status_code == 200:
        with open(save_path, 'wb') as f:
            f.write(response.content)
        print(f"✅ Downloaded: {save_path}")
        return save_path
    else:
        raise Exception(f"❌ Failed to download {url} — Status: {response.status_code}")

def process_files(date1, date2):
    import copy  # Needed to duplicate the figure safely

    cols = [
        'Client Type',
        'Future Index Long',
        'Option Index Call Long',
        'Option Index Put Long',
        'Option Index Call Short',
        'Option Index Put Short'
    ]

    file1 = download_csv(date1)
    file2 = download_csv(date2)

    df1 = pd.read_csv(file1, skiprows=1, usecols=cols)
    df2 = pd.read_csv(file2, skiprows=1, usecols=cols)

    df1.columns = df1.columns.str.strip()
    df2.columns = df2.columns.str.strip()

    merged = pd.merge(df2, df1, on='Client Type', suffixes=('_new', '_old'))

    for col in cols[1:]:
        merged[f"{col}_change"] = merged[f"{col}_new"] - merged[f"{col}_old"]

    result = merged[['Client Type'] + [f"{col}_change" for col in cols[1:]]]

    plot_df = result.melt(id_vars='Client Type', var_name='Position Type', value_name='Change')
    plot_df['Position Type'] = plot_df['Position Type'].str.replace('_change', '')

    fig = px.bar(
        plot_df,
        x='Client Type',
        y='Change',
        color='Position Type',
        barmode='group',
        title=f'Change in Positions ({get_date_string(date2)} - {get_date_string(date1)})',
        text='Change'
    )

    fig.update_layout(
        xaxis_title='Client Type',
        yaxis_title='Change in Contracts',
        legend_title='Position Type',
        bargap=0.2
    )

    # --- Light version ---
    fig_light = copy.deepcopy(fig)
    fig_light.update_layout(
        paper_bgcolor='white',
        plot_bgcolor='white',
        font_color='black'
    )
    light_file = os.path.join('static', 'plot_light.html')
    fig_light.write_html(light_file)

    # --- Dark version ---
    fig_dark = copy.deepcopy(fig)
    fig_dark.update_layout(
        paper_bgcolor='black',
        plot_bgcolor='black',
        font_color='white'
    )
    dark_file = os.path.join('static', 'plot_dark.html')
    fig_dark.write_html(dark_file)

    # ✅ Return BOTH paths
    return light_file, dark_file

# === ROUTES ===

@app.route('/', methods=['GET', 'POST'])
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        date_input = request.form.get('date').strip()
        today = datetime.date.today()
        today = adjust_for_holidays(adjust_to_weekday(today))

        yesterday = today - datetime.timedelta(days=1)
        yesterday = adjust_for_holidays(adjust_to_weekday(yesterday))

        if date_input:
            try:
                selected_date = datetime.datetime.strptime(date_input, '%Y-%m-%d').date()
                selected_date = adjust_to_weekday(selected_date)

                if selected_date.weekday() > 4:
                    flash("❌ You selected a weekend date. Please select a weekday (Mon–Fri)!", "error")
                    return redirect(url_for('index'))

                if selected_date in NSE_HOLIDAYS:
                    flash("❌ The date you selected is an NSE holiday. Please pick another date.", "error")
                    return redirect(url_for('index'))

                if selected_date == today:
                    flash("❌ Please select a previous date, not today!", "error")
                    return redirect(url_for('index'))

                first_date = selected_date
                second_date = today
            except ValueError:
                flash("❌ Invalid date format!", "error")
                return redirect(url_for('index'))
        else:
            first_date = yesterday
            second_date = today

        try:
            light_plot, dark_plot = process_files(first_date, second_date)

            return render_template(
                'plot.html',
                light_plot=light_plot,
                dark_plot=dark_plot
            )

        except Exception as e:
            flash(str(e), "error")
            return redirect(url_for('index'))

    return render_template('index.html')

@app.route('/plot')
def plot():
    return render_template('plot.html')

def compare_options(date1, date2):
    import plotly.subplots as sp

    os.makedirs('static', exist_ok=True)

    table1_image = os.path.join('static', 'table1.png')
    table2_image = os.path.join('static', 'table2.png')
    table3_image = os.path.join('static', 'table3.png')
    bars_image = os.path.join('static', 'bars.png')

    cols = [
        'Client Type',
        'Option Index Call Long',
        'Option Index Call Short',
        'Option Index Put Long',
        'Option Index Put Short'
    ]
    file1 = download_csv(date1)
    file2 = download_csv(date2)

    df1 = pd.read_csv(file1, skiprows=1, usecols=cols)
    df2 = pd.read_csv(file2, skiprows=1, usecols=cols)

    df1.columns = df1.columns.str.strip()
    df2.columns = df2.columns.str.strip()

    merged = pd.merge(df2, df1, on='Client Type', suffixes=('_new', '_old'))

    for col in cols[1:]:
        merged[f"{col}_change"] = merged[f"{col}_new"] - merged[f"{col}_old"]

    # merged['Net Option'] = (
    #     (merged['Option Index Call Long_change'] + merged['Option Index Put Long_change'])
    #     - (merged['Option Index Call Short_change'] + merged['Option Index Put Short_change'])
    # )

    # ✅ Calculate Call & Put Diff
    merged['Call Diff'] = merged['Option Index Call Long_change'] - merged['Option Index Call Short_change']
    merged['Put Diff'] = merged['Option Index Put Long_change'] - merged['Option Index Put Short_change']

    # ✅ Add total row
    total_row = pd.DataFrame([{
        'Client Type': 'Total',
        **{col+'_change': merged[col+'_change'].sum() for col in cols[1:]},
        # 'Net Option': merged['Net Option'].sum(),
        'Call Diff': merged['Call Diff'].sum(),
        'Put Diff': merged['Put Diff'].sum()
    }])

    final_df = pd.concat([
        merged[['Client Type'] + [f"{col}_change" for col in cols[1:]]],
        total_row
    ])
    diff_df = pd.concat([
        merged[['Client Type', 'Call Diff', 'Put Diff']],
        total_row[['Client Type', 'Call Diff', 'Put Diff']]
    ])

    # ✅ Add Call–Put Diff
    diff_df['Call–Put Diff'] = diff_df['Call Diff'] - diff_df['Put Diff']

    def get_colors(values):
        return ['#90EE90' if v >= 0 else '#FF7F7F' for v in values]

    # === 1️⃣ Option Buy/Sell Table ===
    table1 = go.Figure(
        data=[go.Table(
            header=dict(
                values=[
                    'Client Type &#128100;',  # Client Type with Person Icon
                    'Call Long &#9650;',     # Call Long with Upward Triangle
                    'Call Short &#9660;',    # Call Short with Downward Triangle
                    'Put Long &#9660;',      # Put Long with Downward Triangle
                    'Put Short &#9650;'      # Put Short with Delta Symbol
                ],
                fill_color='paleturquoise',
                align='center'
            ), 
            cells=dict(
                values=[
                    final_df['Client Type'],
                    final_df['Option Index Call Long_change'],
                    final_df['Option Index Call Short_change'],
                    final_df['Option Index Put Long_change'],
                    final_df['Option Index Put Short_change'],
                    # final_df['Net Option']
                ],
                fill_color='lavender',
                align='center'
            )
        )]
    )
    table1.update_layout(
        title=f"Option Buy/Sell Comparison ({get_date_string(date2)} vs {get_date_string(date1)})",
    )
    table1_file = os.path.join('static', 'options_compare.html')
    table1.write_html(table1_file)

    # === 2️⃣ Call & Put Diff Table ===
    table2 = go.Figure(
        data=[go.Table(
            header=dict(
                values=['Client Type', 'Call Diff (Long–Short)', 'Put Diff (Long–Short)'],
                fill_color='lightgrey',
                align='center'
            ),
            cells=dict(
                values=[
                    diff_df['Client Type'],
                    diff_df['Call Diff'],
                    diff_df['Put Diff'],
                ],
                fill_color=[
                    ['white'] * len(diff_df),
                    get_colors(diff_df['Call Diff']),
                    get_colors(diff_df['Put Diff'])
                ],
                align='center'
            )
        )]
    )
    table2.update_layout(
        title=f"Call & Put Diff Table ({get_date_string(date2)} vs {get_date_string(date1)})",
    )
    table2_file = os.path.join('static', 'call_put_diff.html')
    table2.write_html(table2_file)

    # === 3️⃣ Call–Put Diff Table ===
    table3 = go.Figure(
        data=[go.Table(
            header=dict(
                values=['Client Type', 'Call–Put Diff (Call–Put)'],
                fill_color='lightgrey',
                align='center'
            ),
            cells=dict(
                values=[
                    diff_df['Client Type'],
                    diff_df['Call–Put Diff']
                ],
                fill_color=[
                    ['white'] * len(diff_df),
                    get_colors(diff_df['Call–Put Diff'])
                ],
                align='center'
            )
        )]
    )
    table3.update_layout(
        title=f"Call–Put Diff Table ({get_date_string(date2)} vs {get_date_string(date1)})"
    )
    call_put_diff_file = os.path.join('static', 'call_put_diff_table.html')
    table3.write_html(call_put_diff_file)

    # === 4️⃣ Bar charts ===
    fig_bar = sp.make_subplots(rows=1, cols=2, subplot_titles=("Call Diff", "Put Diff"))

    fig_bar.add_trace(
        go.Bar(
            x=merged['Client Type'],
            y=merged['Call Diff'],
            name='Call Diff',
            marker_color=['green' if v >= 0 else 'red' for v in merged['Call Diff']]
        ),
        row=1, col=1
    )

    fig_bar.add_trace(
        go.Bar(
            x=merged['Client Type'],
            y=merged['Put Diff'],
            name='Put Diff',
            marker_color=['green' if v >= 0 else 'red' for v in merged['Put Diff']]
        ),
        row=1, col=2
    )

    fig_bar.update_layout(
        title_text="Call & Put Diff per Client Type",
        showlegend=False
    )

    bars_file = os.path.join('static', 'call_put_diff_bars.html')
    fig_bar.write_html(bars_file)

    # SAVE IMAGES
    table1.write_image(table1_image)
    table2.write_image(table2_image)
    table3.write_image(table3_image)
    fig_bar.write_image(bars_image)

    pdf_file = os.path.join('static', 'compare_report.pdf')
    create_pdf([table1_image, table2_image, table3_image, bars_image], pdf_file)

    # ✅ FINAL correct return
    return table1_file, table2_file, bars_file, call_put_diff_file, pdf_file

@app.route('/compare', methods=['GET', 'POST'])
def compare():
    if request.method == 'POST':
        date_input = request.form.get('date').strip()
        today = adjust_to_weekday(datetime.date.today())

        if date_input:
            try:
                selected_date = datetime.datetime.strptime(date_input, '%Y-%m-%d').date()
                selected_date = adjust_to_weekday(selected_date)

                if selected_date.weekday() > 4 or selected_date in NSE_HOLIDAYS:
                    flash("❌ Selected date is weekend/holiday!", "error")
                    return redirect(url_for('compare'))

                if selected_date == today:
                    flash("❌ Please select a previous date, not today!", "error")
                    return redirect(url_for('compare'))

                file1, file2, bars_file, call_put_diff_file, pdf_file = compare_options(selected_date, today)

                return render_template(
                    'compare_result.html',
                    table1=file1,
                    table2=file2,
                    bars=bars_file,
                    call_put=call_put_diff_file,
                    pdf_url=url_for('static', filename='compare_report.pdf')
                )

            except ValueError:
                flash("❌ Invalid date format!", "error")
                return redirect(url_for('compare'))
        else:
            flash("❌ Please select a date!", "error")
            return redirect(url_for('compare'))

    return render_template('compare.html')

if __name__ == '__main__':
    app.run(debug=True)
