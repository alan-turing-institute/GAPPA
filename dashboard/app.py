import dash
from dash import  dcc
from dash import  html
import plotly.express as px
import pandas as pd

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

from country_map import get_country_map

app = dash.Dash(__name__)

df = pd.DataFrame({
    "Fruit": ["Apples", "Oranges", "Bananas", "Apples", "Oranges", "Bananas"],
    "Amount": [4, 1, 2, 2, 4, 5],
    "City": ["SF", "SF", "SF", "Montreal", "Montreal", "Montreal"]
})

fig = px.bar(df, x="Fruit", y="Amount", color="City", barmode="group")

app.layout = html.Div([
    html.H1(children='PM2.5 by country'),
    dcc.RadioItems(
        id='weighted-button',
        options=[
            {'label': 'Population-weighted', 'value': 'Population-weighted'},
            {'label': 'Unweighted', 'value': 'Unweighted'},
        ],
        value='Population-weighted'
    ),

    dcc.Slider(
        id='year-slider',
        min=2010,
        max=2016,
        step=1,
        marks={
            2010: '2010',
            2011: '2011',
            2012: '2012',
            2013: '2013',
            2014: '2014',
            2015: '2015',
            2016: '2016'
        },
        value=2013
    ),
    html.Div(id='map-container')
])


@app.callback(dash.dependencies.Output('map-container', 'children'),
              [dash.dependencies.Input('year-slider', 'value'),
               dash.dependencies.Input('weighted-button', 'value')])
def update_output(year, weighted):
    return dcc.Graph(
        id='map',
        figure=get_country_map(year, weighted)
    )


if __name__ == '__main__':
    app.run_server(host='0.0.0.0', debug=True)
