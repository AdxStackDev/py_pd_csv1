# 📊 Excel Data Analysis & Interactive Visualization with Pandas + Plotly

This project demonstrates how to:
- Read and filter data from an Excel file using **pandas**
- Group and aggregate data by **Product** and **Country**
- Create interactive bar charts with **Plotly** to explore **Units Sold** and **Profit**

---

## 🚀 Features

- 📁 Read a specific Excel file with selected columns
- 📈 Aggregate data with `groupby` and `pivot`
- 🧩 Combine top and bottom rows for custom analysis
- 🎨 Plot interactive grouped bar charts with **hover tooltips**
- ✅ Clean, beginner-friendly code with inline comments

---

## 📂 Data

**Sample data file:**


Columns used:
- `Country`
- `Product`
- `Units Sold`
- `Profit`
- `Year`

---

## 📦 Requirements

- Python 3.x
- pandas
- plotly

Install dependencies:
```bash
pip install pandas plotly
```
## An interactive Plotly bar chart will open in your browser:

- Hover over any bar to see detailed info.

- Bars are grouped by Product and colored by Country.

- Shows Profit by default — easily adjustable to plot Units Sold instead.

## How It Works
- The script reads the top 20 and bottom 20 rows.

- Combines them to create a custom dataset.

- Groups by Product and Country to sum Units Sold and Profit.

- Uses pivot and melt to reshape for Plotly.

- Renders an interactive grouped bar chart with hover details.

## License
This project is for educational purposes. Use freely and modify for your own data exploration!


