# backend/app/models/stock_models.py
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Text, Index
from sqlalchemy.sql import func
from app.services.database import Base

class StockData(Base):
    """Dados históricos de preços"""
    __tablename__ = "stock_data"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), index=True, nullable=False)
    date = Column(Date, index=True, nullable=False)
    open_price = Column(Float)
    close_price = Column(Float)
    high = Column(Float)
    low = Column(Float)
    volume = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # Índice composto para buscas eficientes
    __table_args__ = (
        Index('idx_symbol_date', 'symbol', 'date', unique=True),
    )

class StockInfo(Base):
    """Informações cadastrais das empresas"""
    __tablename__ = "stock_info"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), unique=True, index=True, nullable=False)
    longName = Column(String(200))
    sector = Column(String(100))
    industry = Column(String(100))
    marketCap = Column(Float)
    currency = Column(String(10))
    beta = Column(Float)
    peRatio = Column(Float)
    dividendYield = Column(Float)
    fiftyTwoWeekHigh = Column(Float)
    fiftyTwoWeekLow = Column(Float)
    description = Column(Text, nullable=True)
    website = Column(String(200), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

class ValuationResult(Base):
    """Resultados de cálculos de valuation (cache)"""
    __tablename__ = "valuation_results"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), index=True)
    valuation_type = Column(String(50))  # 'DCF', 'CAPM', etc.
    parameters = Column(Text)  # JSON com parâmetros usados
    result = Column(Text)  # JSON com resultado
    created_at = Column(DateTime, server_default=func.now())
    expires_at = Column(DateTime)  # Cache invalidation