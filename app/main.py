# backend/app/main.py
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi.staticfiles import StaticFiles
from app.web.router import router as web_router
import asyncio
import logging, json

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Adicionar o diretório raiz ao path para importações
sys.path.append(str(Path(__file__).parent.parent))

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import yfinance as yf
import pandas as pd
import numpy as np

# Importações locais - ajuste os caminhos conforme sua estrutura
from app.services.database import Base, get_db, SessionLocal, engine
from app.models.stock_models import StockData, StockInfo, ValuationResult
from app.schemas.stock_schemas import (
    StockQuoteResponse, 
    StockHistoricalResponse,
    DCFRequest,
    DCFResponse,
    StockInfoResponse
)
from app.services.valuation_engine import DCFCalculator, CAPMCalculator

# Criar as tabelas no banco de dados
def init_database():
    """Inicializa o banco de dados criando todas as tabelas"""
    logger.info("Inicializando banco de dados...")
    try:
        # Criar todas as tabelas definidas nos modelos
        Base.metadata.create_all(bind=engine)
        logger.info("Tabelas criadas/verificadas com sucesso!")
        
        # Verificar se as tabelas foram criadas
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            tables = [row[0] for row in result]
            logger.info(f"Tabelas existentes: {tables}")
            
    except SQLAlchemyError as e:
        logger.error(f"Erro ao criar tabelas: {e}")
        raise

# Funções para popular o banco de dados
class DatabasePopulator:
    """Classe responsável por popular o banco de dados com dados do Yahoo Finance"""
    
    def __init__(self, db: Session):
        self.db = db
        self.default_symbols = [
            "PETR4.SA" # Índices
        ]
    
    def fetch_and_store_stock_data(self, symbol: str, period: str = "6mo") -> bool:
        """
        Busca dados de uma ação no Yahoo Finance e armazena no banco
        Retorna True se sucesso, False caso contrário
        """
        try:
            logger.info(f"Buscando dados para {symbol}...")
            
            # Buscar dados do Yahoo Finance
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period)
            
            if hist.empty:
                logger.warning(f"Sem dados para {symbol}")
                return False
            
            # Buscar informações adicionais
            info = ticker.info
            
            # Armazenar informações da empresa
            stock_info = StockInfo(
                symbol=symbol,
                longName=info.get('longName', ''),
                sector=info.get('sector', ''),
                industry=info.get('industry', ''),
                marketCap=info.get('marketCap', 0),
                currency=info.get('currency', 'BRL'),
                beta=info.get('beta', 0.0),
                peRatio=info.get('trailingPE', 0.0),
                dividendYield=info.get('dividendYield', 0.0),
                fiftyTwoWeekHigh=info.get('fiftyTwoWeekHigh', 0.0),
                fiftyTwoWeekLow=info.get('fiftyTwoWeekLow', 0.0)
            )
            
            # Verificar se já existe
            existing_info = self.db.query(StockInfo).filter(StockInfo.symbol == symbol).first()
            if existing_info:
                for key, value in stock_info.__dict__.items():
                    if not key.startswith('_'):
                        setattr(existing_info, key, value)
            else:
                self.db.add(stock_info)
            
            # Armazenar dados históricos
            for date, row in hist.iterrows():
                # Verificar se já existe para esta data
                existing = self.db.query(StockData).filter(
                    StockData.symbol == symbol,
                    StockData.date == date.date()
                ).first()
                
                if existing:
                    # Atualizar existente
                    existing.open_price = float(row['Open'])
                    existing.close_price = float(row['Close'])
                    existing.high = float(row['High'])
                    existing.low = float(row['Low'])
                    existing.volume = int(row['Volume'])
                else:
                    # Criar novo registro
                    stock_data = StockData(
                        symbol=symbol,
                        date=date.date(),
                        open_price=float(row['Open']),
                        close_price=float(row['Close']),
                        high=float(row['High']),
                        low=float(row['Low']),
                        volume=int(row['Volume'])
                    )
                    self.db.add(stock_data)
            
            # Commit a cada símbolo para não perder tudo se algo falhar
            self.db.commit()
            logger.info(f"Dados para {symbol} armazenados com sucesso!")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao processar {symbol}: {e}")
            self.db.rollback()
            return False
    
    def populate_multiple_symbols(self, symbols: Optional[List[str]] = None, period: str = "6mo"):
        """Popula múltiplos símbolos no banco de dados garantindo CAIXA ALTA"""
        
        # 1. Define a lista base
        if symbols is None:
            symbols = self.default_symbols
        
        # 2. Normaliza todos os símbolos para MAIÚSCULAS e remove espaços extras
        symbols = [s.strip().upper() for s in symbols]
        
        logger.info(f"Iniciando população de {len(symbols)} símbolos: {symbols}")
        
        results = []
        for symbol in symbols:
            # Agora 'symbol' já chega em caixa alta no método de gravação
            success = self.fetch_and_store_stock_data(symbol, period)
            results.append({"symbol": symbol, "success": success})
        
        # Resumo
        successful = sum(1 for r in results if r["success"])
        logger.info(f"População concluída! {successful}/{len(symbols)} símbolos processados.")
        return results
    

    def update_all_data(self, days_back: int = 7):
        """
        Atualiza todos os símbolos existentes com dados dos últimos dias
        """
        symbols = self.db.query(StockInfo.symbol).distinct().all()
        symbols = [s[0] for s in symbols]
        
        logger.info(f"Atualizando {len(symbols)} símbolos...")
        
        for symbol in symbols:
            try:
                # Buscar apenas dados recentes
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period=f"{days_back}d")
                
                for date, row in hist.iterrows():
                    existing = self.db.query(StockData).filter(
                        StockData.symbol == symbol,
                        StockData.date == date.date()
                    ).first()
                    
                    if not existing:
                        stock_data = StockData(
                            symbol=symbol,
                            date=date.date(),
                            open_price=float(row['Open']),
                            close_price=float(row['Close']),
                            high=float(row['High']),
                            low=float(row['Low']),
                            volume=int(row['Volume'])
                        )
                        self.db.add(stock_data)
                
                self.db.commit()
                logger.info(f"Atualizado {symbol}")
                
            except Exception as e:
                logger.error(f"Erro ao atualizar {symbol}: {e}")
                self.db.rollback()

# Criar aplicação FastAPI
app = FastAPI(
    title="Valuation Data API",
    description="API para dados financeiros e valuation de ações",
    version="1.0.0"
)

#Configurar Static
app.include_router(web_router)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especifique as origens permitidas
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependência para obter sessão do banco
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Endpoints de teste e utilidades
@app.on_event("startup")
def startup_event():
    init_database()

@app.get("/")
async def root():
    return {
        "message": "Financial Data API",
        "version": "1.0.0",
        "endpoints": [
            "/docs - Documentação",
            "/health - Health check",
            "/stocks/{symbol} - Dados de uma ação",
            "/stocks/{symbol}/historical - Dados históricos",
            "/stocks/{symbol}/info - Informações da empresa",
            "/dcf - Calcular DCF",
            "/capm - Calcular CAPM",
            "/admin/populate - Popular banco de dados",
            "/admin/update - Atualizar dados"
        ]
    }

@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Verifica se a API e o banco estão funcionando"""
    try:
        # Testar conexão com banco
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {e}"
    
    return {
        "status": "healthy",
        "database": db_status,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/stocks/{symbol}")
async def get_stock_quote(symbol: str, db: Session = Depends(get_db)):
    """Retorna a cotação mais recente de uma ação"""
    try:
        # Tentar buscar do banco primeiro
        latest = db.query(StockData).filter(
            StockData.symbol == symbol
        ).order_by(StockData.date.desc()).first()
        
        if latest:
            return {
                "symbol": symbol,
                "price": latest.close_price,
                "open": latest.open_price,
                "high": latest.high,
                "low": latest.low,
                "volume": latest.volume,
                "date": latest.date.isoformat(),
                "source": "database"
            }
        
        # Se não encontrar, buscar do Yahoo Finance
        ticker = yf.Ticker(symbol)
        data = ticker.history(period="1d")
        
        if data.empty:
            raise HTTPException(status_code=404, detail="Símbolo não encontrado")
        
        latest = data.iloc[-1]
        return {
            "symbol": symbol,
            "price": float(latest['Close']),
            "open": float(latest['Open']),
            "high": float(latest['High']),
            "low": float(latest['Low']),
            "volume": int(latest['Volume']),
            "date": data.index[-1].isoformat(),
            "source": "yfinance"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stocks/{symbol}/historical")
async def get_historical_data(
    symbol: str, 
    period: str = Query("6mo", description="Período: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y"),
    db: Session = Depends(get_db)
):
    """Retorna dados históricos de uma ação"""
    try:
        # Calcular data inicial baseada no período
        end_date = datetime.now().date()
        period_map = {
            "1d": 1, "5d": 5, "1mo": 30, "3mo": 90, "6mo": 180, "1y": 365, "2y": 730, "5y": 1825
        }
        days = period_map.get(period, 180)
        start_date = end_date - timedelta(days=days)
        
        # Buscar do banco
        data = db.query(StockData).filter(
            StockData.symbol == symbol,
            StockData.date >= start_date
        ).order_by(StockData.date).all()
        
        if data:
            return {
                "symbol": symbol,
                "period": period,
                "data": [
                    {
                        "date": d.date.isoformat(),
                        "open": d.open_price,
                        "close": d.close_price,
                        "high": d.high,
                        "low": d.low,
                        "volume": d.volume
                    }
                    for d in data
                ],
                "source": "database"
            }
        
        # Se não encontrar, buscar do Yahoo Finance
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period)
        
        if hist.empty:
            raise HTTPException(status_code=404, detail="Dados não encontrados")
        
        return {
            "symbol": symbol,
            "period": period,
            "data": [
                {
                    "date": date.isoformat(),
                    "open": float(row['Open']),
                    "close": float(row['Close']),
                    "high": float(row['High']),
                    "low": float(row['Low']),
                    "volume": int(row['Volume'])
                }
                for date, row in hist.iterrows()
            ],
            "source": "yfinance"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/dcf")
async def calculate_dcf(request: DCFRequest, db: Session = Depends(get_db)):
    try:
        symbol_to_query = request.symbol.upper() 
        
        # 1. Calcula o DCF
        result = DCFCalculator.calculate(
            db=db,
            symbol=symbol_to_query,
            growth_rate=request.growth_rate,
            projection_years=request.projection_years
        )
        
        # 2. Salva o resultado na sua tabela de cache (ValuationResult)
        new_valuation = ValuationResult(
            symbol=symbol_to_query,
            valuation_type='DCF',
            parameters=json.dumps({"growth_rate": request.growth_rate}),
            result=json.dumps(result)
        )
        db.add(new_valuation)
        db.commit()
        
        return result
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    

@app.post("/capm")
async def calculate_capm(request: DCFRequest): # Use apenas o request se o symbol estiver no JSON
    """Calcula o retorno esperado pelo CAPM"""
    try:
        symbol_to_query = request.symbol.upper()
        # Se o seu DCFRequest não tiver market_return e risk_free, 
        # você pode usar valores padrão aqui
        result = CAPMCalculator.calculate(
            symbol=symbol_to_query,
            market_return=0.12, # Exemplo de prêmio de mercado
            risk_free_rate=0.1075 # Exemplo Selic
        )
        return result
    except Exception as e:
        # Troquei 'detail=str(e)' para algo mais amigável caso queira
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")
    

# Endpoints administrativos
# @app.post("/admin/populate")
# async def populate_database(
#     symbols: Optional[str] = Query(None, description="Símbolos separados por vírgula"),
#     period: str = Query("6mo", description="Período para buscar dados"),
#     db: Session = Depends(get_db)
# ):
#     """Popula o banco de dados com dados do Yahoo Finance"""
#     try:
#         populator = DatabasePopulator(db)
        
#         symbol_list = None
#         if symbols:
#             symbol_list = [s.strip() for s in symbols.split(",")]
        
#         results = populator.populate_multiple_symbols(symbol_list, period)
        
#         return {
#             "message": "População concluída",
#             "results": results,
#             "timestamp": datetime.now().isoformat()
#         }
        
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

@app.post("/admin/update")
async def update_database(
    days_back: int = Query(7, description="Dias para atualizar"),
    db: Session = Depends(get_db)
):
    """Atualiza dados existentes no banco"""
    try:
        populator = DatabasePopulator(db)
        populator.update_all_data(days_back)
        
        return {
            "message": f"Atualização concluída para os últimos {days_back} dias",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin/status")
async def database_status(db: Session = Depends(get_db)):
    """Retorna status do banco de dados"""
    try:
        # Contar registros
        stock_count = db.query(StockData).count()
        info_count = db.query(StockInfo).count()
        symbols = db.query(StockInfo.symbol).distinct().all()
        
        # Última atualização
        latest = db.query(StockData).order_by(StockData.date.desc()).first()
        
        return {
            "total_stock_records": stock_count,
            "total_companies": info_count,
            "symbols": [s[0] for s in symbols],
            "latest_data_date": latest.date.isoformat() if latest else None,
            "database_ready": stock_count > 0
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@app.post("/admin/populate")
async def populate_asset(symbol: str = None, months: int = 6, db: Session = Depends(get_db)):
    service = DatabasePopulator(db)
    
    # Transformamos o 'symbol' único em uma LISTA para o método aceitar
    # Se o usuário não enviou nada, passamos None para ele usar a lista padrão
    target_symbols = [symbol.upper()] if symbol else None
    
    # Convertemos meses para o formato que o yfinance espera (ex: 6 -> "6mo")
    period_str = f"{months}mo"
    
    # Chama o seu método
    results = service.populate_multiple_symbols(symbols=target_symbols, period=period_str)
    
    return {"status": "success", "results": results}

# @app.post("/admin/populate")
# async def populate_asset(symbol: str, months: int = 6, db: Session = Depends(get_db)):
#     try:
#         # Aqui você chama a lógica do seu serviço de populate existente
#         # Exemplo: result = AssetService.populate_db(db, symbol, months)
#         # Por enquanto, vou simular o sucesso:
#         return {"status": "success", "message": f"Dados de {symbol} importados."}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))   

# Script para executar diretamente
if __name__ == "__main__":
    import uvicorn
    
    # Inicializar banco de dados
    init_database()
    
    # Verificar se deve popular automaticamente
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--populate", action="store_true", help="Popular banco de dados na inicialização")
    parser.add_argument("--symbols", type=str, help="Símbolos para popular (separados por vírgula)")
    args = parser.parse_args()
    
    if args.populate:
        logger.info("Populando banco de dados...")
        db = SessionLocal()
        try:
            populator = DatabasePopulator(db)
            symbol_list = None
            if args.symbols:
                symbol_list = [s.strip() for s in args.symbols.split(",")]
            populator.populate_multiple_symbols(symbol_list)
        finally:
            db.close()
    
    # Iniciar servidor
    logger.info("Iniciando servidor FastAPI...")
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8080,
        reload=True,  # Apenas para desenvolvimento
        log_level="info"
    )