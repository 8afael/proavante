# backend/app/schemas/stock_schemas.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime

class StockQuoteResponse(BaseModel):
    symbol: str
    price: float
    open: float
    high: float
    low: float
    volume: int
    date: str
    source: str = "yfinance"

class StockHistoricalData(BaseModel):
    date: str
    open: float
    close: float
    high: float
    low: float
    volume: int

class StockHistoricalResponse(BaseModel):
    symbol: str
    period: str
    data: List[StockHistoricalData]
    source: str

class DCFRequest(BaseModel):
    symbol: str = Field(..., description="Ticker da ação (ex: PETR4.SA)")
    growth_rate: float = Field(0.05, description="Taxa de crescimento esperada", ge=-0.5, le=1.0)
    discount_rate: float = Field(0.10, description="Taxa de desconto (WACC)", ge=0.0, le=1.0)
    projection_years: int = Field(5, description="Anos de projeção", ge=1, le=20)

class DCFResponse(BaseModel):
    symbol: str
    company_name: str
    current_price: float
    intrinsic_value: float
    margin_of_safety: float
    recommendation: str
    assumptions: dict
    projected_fcfs: List[float]

class StockInfoResponse(BaseModel):
    symbol: str
    longName: Optional[str]
    sector: Optional[str]
    industry: Optional[str]
    marketCap: Optional[float]
    currency: Optional[str]
    beta: Optional[float]
    peRatio: Optional[float]
    dividendYield: Optional[float]
    fiftyTwoWeekHigh: Optional[float]
    fiftyTwoWeekLow: Optional[float]