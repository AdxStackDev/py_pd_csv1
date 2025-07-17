import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
'''
Following code is to calculate difference between OI data difference with two days to get 
proper sentiments of Markets on basis of output and output is also plotted on graph using Plotly.
Visit https://www.nseindia.com/all-reports-derivatives and click on 'F&O-Participant wise Open Interest (csv)'
to download latest data.

Also latest or previous data can we download from following link:
'https://nsearchives.nseindia.com/content/nsccl/fao_participant_oi_16072025.csv'

here 160702025 = 16th July 2025

so, if we need to download any other previous date data we can simple modify it.
Example: 'https://nsearchives.nseindia.com/content/nsccl/fao_participant_oi_30052025.csv'

'''
# Load yesterday’s data
yesterday_path = 'C:/Users/adity/Desktop/py/pylib/data/16072025.csv'
yesterday = pd.read_csv(
    yesterday_path,
    skiprows=1,
    usecols=[
        'Client Type',
        'Future Index Long',
        'Option Index Call Long',
        'Option Index Put Long',
        'Option Index Call Short',
        'Option Index Put Short'
    ]
)

# Load today’s data
today_path = 'C:/Users/adity/Desktop/py/pylib/data/17072025.csv'
today = pd.read_csv(
    today_path,
    skiprows=1,
    usecols=[
        'Client Type',
        'Future Index Long',
        'Option Index Call Long',
        'Option Index Put Long',
        'Option Index Call Short',
        'Option Index Put Short'
    ]
)

# Making sure column names have no extra spaces
yesterday.columns = yesterday.columns.str.strip()
today.columns = today.columns.str.strip()

# Merge on 'Client Type'
merged = pd.merge(today, yesterday, on='Client Type', suffixes=('_today', '_yesterday'))

# Subtract yesterday from today for each numeric column
diff_cols = ['Future Index Long', 'Option Index Call Long', 'Option Index Put Long', 'Option Index Call Short', 'Option Index Put Short']
for col in diff_cols:
    merged[col + '_change'] = merged[f"{col}_yesterday"] - merged[f"{col}_today"]

result = merged[['Client Type'] + [col + '_change' for col in diff_cols]]

# print("=== Difference (Today - Yesterday) ===")
# print(result)

# result.to_csv('difference.csv', index=False)

# Reshape for plotly: melt to long form for grouped bar plot
plot_df = result.melt(id_vars='Client Type', var_name='Position Type', value_name='Change')

# column names for legend
plot_df['Position Type'] = plot_df['Position Type'].str.replace('_change', '')

# Plot using Plotly
fig = px.bar(
    plot_df,
    x='Client Type',
    y='Change',
    color='Position Type',
    barmode='group',
    title='Change in Positions (Today - Yesterday)',
    text='Change'
)

fig.update_layout(
    xaxis_title='Client Type',
    yaxis_title='Change in Contracts',
    legend_title='Position Type',
    bargap=0.2
)

fig.show()
