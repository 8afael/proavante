import streamlit as st
import yfinance as yf
import plotly.express as pl

st.title("ProAvante Dashboard")
st.sidebar.title("Informe o ticker")
ticker_symbol = st.sidebar.text_input("Digite o ticker:", "PETR3.SA")
start_date = st.sidebar.date_input("Data inicial:", value=None)
end_date = st.sidebar.date_input("Data final:", value=None)
ticker = yf.Ticker(ticker_symbol)
historicalData = ticker.history(start=start_date, end=end_date)

#st.write("Ola")
stockData=yf.download(ticker_symbol, start=start_date, end=end_date)


if start_date is not None and end_date is not None:
    #st.write(stockData)
    # historical data:
    st.subheader(f'{ticker_symbol} Histórico da Ação')
    price_tab, hist_tab, chart_tab = st.tabs(["Resumo Preço", "Dados Históricos", "Gráfico"])

    with price_tab:
        st.write("Resumo Preço")
        st.write(stockData)
    with hist_tab:
        st.write("Dados Históricos")
        st.write(historicalData)
    with chart_tab:
        st.write("Gráfico")
        line_charts = pl.line(stockData, stockData.index,y=stockData['Adj Close'], title=ticker_symbol)
        st.plotly_chart(line_charts)
        

