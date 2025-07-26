from flask import Flask, render_template, request, flash, redirect, url_for
import pandas as pd
import plotly.express as px
import datetime
import requests
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

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

    # Save plot as HTML file
    plot_file = os.path.join('static', 'plot.html')
    fig.write_html(plot_file)
    return plot_file

# === ROUTES ===

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
            process_files(first_date, second_date)
            return redirect(url_for('plot'))
        except Exception as e:
            flash(str(e), "error")
            return redirect(url_for('index'))

    return render_template('index.html')

@app.route('/plot')
def plot():
    return render_template('plot.html')


if __name__ == '__main__':
    app.run(debug=True)
