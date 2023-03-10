import dash_ag_grid as dag
from dash import Dash, html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import yfinance as yf

app = Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])

equities = {
    "SPY": "SPY",
    "QQQ": "QQQ",
    "IWM": "IWM",
    "TSLA": "Tesla",
    "MSTR": "MicroStrategy",
    "AAPL": "Apple",
    "GOOGL": "Alphabet",
    "MSFT": "Microsoft",
    # "AMZN": "Amazon",
}


def get_stock_data():
    return yf.download(tickers=list(equities.keys()), period="30d", group_by="ticker")


stock_data = get_stock_data()


def last_close(ticker):
    return stock_data[ticker]["Close"].iloc[-1]


data = {
    "ticker": [ticker for ticker in equities],
    "company": [name for name in equities.values()],
    "quantity": [1, 1, 1, 1, 1, 1, 1, 1],
    "price": [last_close(ticker) for ticker in equities],
    "position": ["buy", "sell", "hold", "hold", "hold", "hold", "hold", "hold"],
    "comments": ["Notes" for i in range(8)],
}
df = pd.DataFrame(data)


columnDefs = [
    {
        "headerName": "Stock Ticker",
        "field": "ticker",
    },
    {
        "headerName": "Company",
        "field": "company",
        "unhide": True,
    },
    {
        "headerName": "Shares",
        "field": "quantity",
        "type": "rightAligned",
        "filter": "agNumberColumnFilter",
        "editable": True,
    },
    {
        "headerName": "Last Close Price",
        "field": "price",
        "type": "rightAligned",
        "filter": "agNumberColumnFilter",
        "valueFormatter": "Number(value).toFixed(2)",
        "dangerously_allow_html": True,
        "cellRenderer": "agAnimateShowChangeCellRenderer",
    },
    {
        "headerName": "Market Value",
        "type": "rightAligned",
        "filter": "agNumberColumnFilter",
        "valueGetter": "Number(data.price) * Number(data.quantity)",
        "valueFormatter": "Number(value).toFixed(2)",
        "dangerously_allow_html": True,
        "cellRenderer": "agAnimateShowChangeCellRenderer",
    },
    {
        "headerName": "Position",
        "field": "position",
        "editable": True,
        "cellEditor": "agSelectCellEditor",
        "cellEditorParams": {
            "values": ["buy", "sell", "hold"],
        },
    },
    {
        "headerName": "Comments",
        "field": "comments",
        "editable": True,
        "cellEditorPopup": True,
        "cellEditor": "agLargeTextCellEditor",
    },
]

defaultColDef = {
    "filter": True,
    "resizable": True,
    "sortable": True,
    "editable": False,
    "floatingFilter": True,
}

cellStyle = {
    "styleConditions": [
        {
            "condition": "value == 'buy'",
            "style": {"backgroundColor": "#196A4E", "color": "black"},
        },
        {
            "condition": "value == 'sell'",
            "style": {"backgroundColor": "#800000", "color": "black"},
        },
        {
            "condition": "colDef.headerName == 'Shares'",
            "style": {"backgroundColor": "#444"},
        },
    ]
}


table = dag.AgGrid(
    id="portfolio-grid",
    className="ag-theme-alpine",
    columnDefs=columnDefs,
    rowData=df.to_dict("records"),
    columnSize="sizeToFit",
    defaultColDef=defaultColDef,
    cellStyle=cellStyle,
    dangerously_allow_html=True,
    dashGridOptions={"undoRedoCellEditing": True, "rowSelection": "single"},
)

candlestick = dbc.Card(dcc.Graph(id="candlestick"), body=True)
# pie = dbc.Card(dcc.Graph(id="asset-allocation"), body=True)
header = html.Div("My Portfolio", className="h2 p-2 text-white bg-primary text-center")

app.layout = dbc.Container(
    [
        header,
        dbc.Row([dbc.Col(candlestick)]),
        dbc.Row(dbc.Col(table, className="py-4")),
    ],
)


@app.callback(
    Output("candlestick", "figure"),
    Input("portfolio-grid", "selectionChanged"),
)
def update_candlestick(selected_row):
    if selected_row is None:
        ticker = "SPY"
        company = "SPY"
    else:
        ticker = selected_row[0]["ticker"]
        company = selected_row[0]["company"]

    dff_ticker_hist = stock_data[ticker].reset_index()
    dff_ticker_hist["Date"] = pd.to_datetime(dff_ticker_hist["Date"])

    fig = go.Figure(
        go.Candlestick(
            x=dff_ticker_hist["Date"],
            open=dff_ticker_hist["Open"],
            high=dff_ticker_hist["High"],
            low=dff_ticker_hist["Low"],
            close=dff_ticker_hist["Close"],
        )
    )
    fig.update_layout(
        title_text=f"{ticker} {company} Daily Price", template="plotly"
    )
    return fig

#
# @app.callback(
#     Output("asset-allocation", "figure"),
#     Input("portfolio-grid", "cellValueChanged"),
#     State("portfolio-grid", "rowData"),
# )
# def update_portfolio_stats(_, data):
#     dff = pd.DataFrame(data)
#     dff["total"] = dff["quantity"].astype(float) * dff["price"].astype(float)
#     portfolio_total = dff["total"].sum()
#
#     return px.pie(
#         dff,
#         values="total",
#         names="ticker",
#         hole=0.3,
#         title=f"Portfolio Total ${portfolio_total:,.2f}",
#         template="plotly_dark",
#     )
#

if __name__ == "__main__":
    app.run_server(debug=True)