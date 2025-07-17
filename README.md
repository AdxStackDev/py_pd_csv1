
![OI Sentiment Chart](https://github.com/AdxStackDev/py_pd_csv1/blob/main/newplot.png?raw=true)

# 📊 Python Data Analysis: Excel Reports + Market OI Sentiment

This project demonstrates **two practical Python workflows** for data analysis and visualization:

---

## ⚙️ 1️⃣ Market Open Interest Sentiment

Analyze **daily Participant-wise Open Interest (OI)** data for equity derivatives and visualize how positions change between two days.

### 📌 How It Works

- Download daily OI CSVs from [NSE India](https://www.nseindia.com/all-reports-derivatives).
- The `market.py` script:
  - Loads yesterday’s & today’s CSVs
  - Merges by **Client Type**
  - Computes position differences:
    - Future Index Long
    - Option Index Call/Put Long & Short
  - Plots an **interactive grouped bar chart** to visualize position changes.

### 🔗 Example NSE CSV URL  
```
https://nsearchives.nseindia.com/content/nsccl/fao_participant_oi_<DDMMYYYY>.csv
```
Example:
```
https://nsearchives.nseindia.com/content/nsccl/fao_participant_oi_16072025.csv
```

### 📈 Example Output

The chart shows position changes by **Client Type** and Position Type.  
Hover for details.

---

## ⚙️ 2️⃣ Excel Product & Sales Report

Analyze a **financial Excel file** to see:
- Units Sold & Profit by **Product** and **Country**
- Top & bottom rows combined for custom insights
- Interactive grouped bar chart of **Profit by Product & Country**

### 📌 How It Works

The `app.py` script:
- Reads the Excel file `financial_sample.xlsx`
- Filters columns: `Country`, `Product`, `Units Sold`, `Profit`, `Year`
- Combines **top 20 & bottom 20 rows**
- Groups by `Product` & `Country`
- Uses `pivot` & `melt` to reshape for Plotly
- Plots an **interactive grouped bar chart** with hover details.

---

## 📦 Requirements

- Python 3.x
- pandas
- plotly
- matplotlib (optional)

Install dependencies:
```bash
pip install pandas plotly matplotlib
```

---

## 🚀 How to Run

```bash
# Run OI Sentiment script
python market.py

# Run Excel Product Sales script
python app.py
```

Each script opens an **interactive Plotly bar chart** in your default browser.

---

## 📂 Sample Data

- `financial_sample.xlsx` — example product sales data.
- `16072025.csv` / `17072025.csv` — example OI data (download from NSE).

---

## 📄 License

This project is for educational & personal analysis only.
Use freely and adapt for your own market or business data insights!

---

**Happy analyzing!**
