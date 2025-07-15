import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt


excel = 'C:/Users/adity/Desktop/py/pylib/data/financial_sample.xlsx';

read = pd.read_excel(excel, usecols=['Country', 'Product', 'Units Sold', 'Profit', 'Year'])

# print(read);
#head(no. of rows/empty) = to read upper part of  excel, tail(no. of rows/empty) to read lower parth of excel
#short a column : sort_values (['column_name'], asending=false)
# check = read.sort_values(['Year']).head(10)
#shape : to get  count of columns & rows of a excel
# check = pd.read_excel(excel, usecols=range(6))
top20 = read.head(20)
bottom20 = read.tail(20)
final = pd.concat([top20, bottom20])
# print(final)

productSale = final.groupby(['Product', 'Country'])[['Units Sold', 'Profit']].sum().reset_index()


# productSale = final.groupby('Product')['Units Sold'].sum().reset_index()

# print(productSale)

# plt.figure(figsize=(10,10))
# plt.bar(productSale['Product'], productSale['Units Sold'])
# plt.xlabel('Country')
# plt.ylabel('Units Sold')
# plt.title('Units Solds By Company')
# plt.show()
#kind = ('line', 'bar', 'barh', 'kde', 'density', 'area', 'hist', 'box', 'pie', 'scatter', 'hexbin')
# pivot = productSale.pivot(index='Product', columns='Country', values='Profit')
# pivot.plot(kind='bar', figsize=(12,7))
# plt.xlabel('Products')
# plt.ylabel('Profit')
# plt.title('Profit earn by Products in countries')
# plt.show()

pivot = productSale.pivot(index='Product', columns='Country', values='Profit').reset_index()

# Convert pivoted data to long format for Plotly
melted = pivot.melt(id_vars='Product', var_name='Country', value_name='Profit')

# Plotly bar chart
fig = px.bar(
    melted,
    x='Product',
    y='Profit',
    color='Country',
    barmode='group',
    title='Profit earned by Products in Countries',
    labels={'Profit': 'Profit', 'Product': 'Product'},
    hover_data={'Profit': ':.2f', 'Country': True, 'Product': True}
)

fig.update_layout(
    xaxis_title='Products',
    yaxis_title='Profit',
    xaxis_tickangle=-45,
    bargap=0.2
)

fig.show()


