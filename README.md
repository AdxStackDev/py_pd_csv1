<div align="center">
<img src="assets/disclaimer.png" width="800" alt="Disclaimer" style="border-radius: 10px; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);">

<!-- ![NSE Analytics Hero](assets/hero.png) -->

# 📈 NSE F&O Analytics Dashboard

[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.0+-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-3.0+-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![Vercel](https://img.shields.io/badge/Vercel-Deployed-000000?style=for-the-badge&logo=vercel&logoColor=white)](https://adxnse.vercel.app/)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](LICENSE)

<p align="center">
  <b>Real-time Futures & Options Analysis | Institutional Sentiment Tracking | Live Option Chain</b>
</p>

[Live Demo 🚀](https://adxnse.vercel.app/) • [Report Bug 🐛](https://github.com/AdxStackDev/py_pd_csv1/issues)

</div>

---

## 📊 Project Overview

**NSE F&O Analytics Dashboard** is a high-performance web application designed for traders and analysts. It provides a real-time window into the National Stock Exchange of India's derivative market, offering institutional grade insights through a clean, modern interface.

<table>
<tr>
<td width="60%">

### 🎯 Key Features

- **FII/DII Activity Tracker**: Real-time tracking of institutional flows.
- **Sentiment Analysis**: Automated Bullish/Bearish/Neutral classification.
- **Live Option Chain**: Real-time OI tracking with ATM identification.
- **Heatmaps**: Visual position intensity indicators.
- **Smart Caching**: In-memory data management for speed.

</td>
<td width="40%">
<div align="center">
  <img src="assets/dashboard.png" alt="Mobile Responsive" style="border-radius: 10px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
</div>
</td>
</tr>
</table>

---

## 📸 Application Gallery

<div align="center">

### 🖥️ Main Dashboard
<img src="assets/dashboard.png" width="800" alt="Dashboard" style="border-radius: 10px; margin-bottom: 20px; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);">

### 🔗 Option Chain Analysis
<img src="assets/option_chain.png" width="800" alt="Option Chain" style="border-radius: 10px; margin-bottom: 20px; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);">

### 📊 Call vs Put Difference
<img src="assets/call_put_difference_graph.png" width="800" alt="Call Put Difference" style="border-radius: 10px; margin-bottom: 20px; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);">

### 🌡️ OI Position Heatmap
<img src="assets/oi_position_heat_map.png" width="800" alt="OI Heatmap" style="border-radius: 10px; margin-bottom: 20px; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);">

### 👥 Client Participation
<img src="assets/client_call_put_difference.png" width="800" alt="Client Participation" style="border-radius: 10px; margin-bottom: 20px; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);">

### 📉 Net Sentiment
<img src="assets/net_sentiment.png" width="800" alt="Net Sentiment" style="border-radius: 10px; margin-bottom: 20px; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);">
</div>

---

## 🛠️ Technology Stack

<div align="center">

| Backend | Frontend | Deployment | Data |
|:---:|:---:|:---:|:---:|
| ![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white) | ![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=flat-square&logo=html5&logoColor=white) | ![Vercel](https://img.shields.io/badge/Vercel-000000?style=flat-square&logo=vercel&logoColor=white) | ![Pandas](https://img.shields.io/badge/Pandas-150458?style=flat-square&logo=pandas&logoColor=white) |
| ![Flask](https://img.shields.io/badge/Flask-000000?style=flat-square&logo=flask&logoColor=white) | ![Tailwind](https://img.shields.io/badge/Tailwind-38B2AC?style=flat-square&logo=tailwind-css&logoColor=white) | ![Git](https://img.shields.io/badge/Git-F05032?style=flat-square&logo=git&logoColor=white) | ![Plotly](https://img.shields.io/badge/Plotly-3F4F75?style=flat-square&logo=plotly&logoColor=white) |
| ![Redis](https://img.shields.io/badge/Redis-DC382D?style=flat-square&logo=redis&logoColor=white) | ![Jinja2](https://img.shields.io/badge/Jinja2-B41717?style=flat-square&logo=jinja&logoColor=white) | | ![NSE](https://img.shields.io/badge/NSE_API-blue?style=flat-square) |

</div>

---

## 💡 Programming Concepts

<details>
<summary><b>1. Data Acquisition & Caching</b></summary>
<br>

**Challenge**: Efficiently fetch and store CSV data without file system access in serverless environment.

**Solution**: Implemented in-memory caching using Python dictionaries.

```python
_csv_cache = {}  # Global in-memory cache

def download_csv(date):
    if date_str in _csv_cache:
        return _csv_cache[date_str]
    # ... download logic
```
</details>

<details>
<summary><b>2. Holiday & Weekend Detection</b></summary>
<br>

**Logic**: Automatically skip non-trading days to find the most recent available data.

```python
def adjust_for_holidays(date):
    while date.weekday() > 4 or date in NSE_HOLIDAYS:
        date -= datetime.timedelta(days=1)
    return date
```
</details>

<details>
<summary><b>3. Sentiment Analysis Algorithm</b></summary>
<br>

**Logic**: Calculate market sentiment based on participant activity changes using a weighted scoring system for Futures and Options.
</details>

<details>
<summary><b>4. Serverless Architecture</b></summary>
<br>

Adapted for Vercel's read-only filesystem using stateless request handling and direct HTML rendering.
</details>

---

## 🚀 Getting Started

### Prerequisites

- Python 3.12+
- Git

### Installation

```bash
# Clone repository
git clone https://github.com/AdxStackDev/py_pd_csv1.git
cd py_pd_csv1

# Install dependencies
pip install -r requirements.txt

# Run application
python app.py
```

Access the dashboard at `http://localhost:5001`

---

<div align="center">

**Created with ❤️ by [Aditya (AdxStackDev)](https://github.com/AdxStackDev)**

</div>

---

<div align="center">
  <sub>⚠️ <b>Disclaimer</b>: This application is for educational purposes only. Not financial advice.</sub>
</div>
