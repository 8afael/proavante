
from sqlalchemy.orm import Session
from app.models.stock_models import StockInfo, StockData
from typing import Dict, Optional
import yfinance as yf
import logging


logger = logging.getLogger(__name__)

class DCFCalculator:
    @staticmethod
    def calculate(db: Session, symbol: str, growth_rate: float = 0.05, projection_years: int = 5):
        """
        Calcula o Valor Intrínseco buscando dados automaticamente do banco.
        """
        # 1. Buscar Informações da Empresa
        stock_info = db.query(StockInfo).filter(StockInfo.symbol == symbol).first()
        if not stock_info:
            raise ValueError(f"Informações para {symbol} não encontradas no banco. Execute a população primeiro.")

        # 2. Buscar Cotação Atual e Fluxo de Caixa Aproximado
        # Como o yfinance gratuito é limitado para FCF histórico, vamos usar uma 
        # estimativa baseada em Proxy (ex: Lucro/EBITDA simplificado se tivermos)
        # Para este exemplo, vamos usar o Market Cap e Dividend Yield como base de retorno
        
        current_price = db.query(StockData.close_price).filter(
            StockData.symbol == symbol
        ).order_by(StockData.date.desc()).first()[0]

        # 3. Definir Taxa de Desconto (WACC Simplificado via CAPM)
        # Selic (Risk Free) ~ 10.75% (ajuste conforme o mercado atual)
        risk_free_rate = 0.1075 
        market_return = 0.15  # Retorno esperado do Ibovespa
        beta = stock_info.beta if stock_info.beta > 0 else 1.0
        
        discount_rate = risk_free_rate + beta * (market_return - risk_free_rate)

        # 4. Projeção de Fluxos de Caixa (Simplificada)
        # Vamos assumir que o "Fluxo de Caixa Base" é uma fração do Market Cap / PE Ratio
        if stock_info.peRatio and stock_info.peRatio > 0:
            estimated_earnings = (current_price / stock_info.peRatio)
        else:
            estimated_earnings = current_price * 0.07 # Assume 7% de margem caso não tenha P/L

        future_values = []
        for year in range(1, projection_years + 1):
            cf = estimated_earnings * ((1 + growth_rate) ** year)
            pv = cf / ((1 + discount_rate) ** year)
            future_values.append(pv)

        # 5. Valor Terminal (Crescimento perpétuo de 2%)
        g_long_term = 0.02
        terminal_value = (cf * (1 + g_long_term)) / (discount_rate - g_long_term)
        pv_terminal_value = terminal_value / ((1 + discount_rate) ** projection_years)

        intrinsic_value = sum(future_values) + pv_terminal_value
        
        # 6. Margem de Segurança (ex: 20%)
        margin_of_safety = 0.20
        buy_price = intrinsic_value * (1 - margin_of_safety)

        return {
            "symbol": symbol,
            "current_price": round(current_price, 2),
            "intrinsic_value": round(intrinsic_value, 2),
            "suggested_buy_price": round(buy_price, 2),
            "discount_rate_used": round(discount_rate, 4),
            "margin_of_safety": "20%",
            "recommendation": "COMPRAR" if current_price < buy_price else "AGUARDAR"
        }

# # backend/app/services/valuation_engine.py
# import yfinance as yf
# import numpy as np
# from datetime import datetime, timedelta
# from typing import Dict, Optional

# class DCFCalculator:
#     """Calculadora de Fluxo de Caixa Descontado"""
    
#     @staticmethod
#     def calculate(symbol: str, growth_rate: float = 0.05, 
#                   discount_rate: float = 0.10, projection_years: int = 5) -> Dict:
#         """
#         Calcula o valor intrínseco usando DCF simplificado
#         """
#         try:
#             ticker = yf.Ticker(symbol)
#             info = ticker.info
            
#             # Obter fluxo de caixa livre (FCF) - simplificado
#             fcf = info.get('freeCashflow', info.get('operatingCashflow', 0))
            
#             if fcf == 0 or fcf is None:
#                 # Fallback: estimar baseado em EBITDA
#                 ebitda = info.get('ebitda', 0)
#                 if ebitda > 0:
#                     fcf = ebitda * 0.6  # Assumindo 60% do EBITDA como FCF
#                 else:
#                     return {"error": "Dados insuficientes para cálculo"}
            
#             # Projetar FCFs futuros
#             projected_fcfs = []
#             for year in range(1, projection_years + 1):
#                 fcf_growth = fcf * ((1 + growth_rate) ** year)
#                 discounted_fcf = fcf_growth / ((1 + discount_rate) ** year)
#                 projected_fcfs.append(discounted_fcf)
            
#             # Calcular valor presente
#             intrinsic_value = sum(projected_fcfs)
            
#             # Valor por ação
#             shares_outstanding = info.get('sharesOutstanding', 1)
#             value_per_share = intrinsic_value / shares_outstanding
            
#             # Preço atual
#             current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
            
#             # Margem de segurança
#             margin_of_safety = ((value_per_share - current_price) / current_price) * 100 if current_price > 0 else 0
            
#             return {
#                 "symbol": symbol,
#                 "company_name": info.get('longName', symbol),
#                 "current_price": current_price,
#                 "intrinsic_value": value_per_share,
#                 "margin_of_safety": margin_of_safety,
#                 "recommendation": "COMPRAR" if margin_of_safety > 15 else "MANTER" if margin_of_safety > 0 else "VENDER",
#                 "assumptions": {
#                     "growth_rate": growth_rate,
#                     "discount_rate": discount_rate,
#                     "projection_years": projection_years,
#                     "fcf_used": fcf
#                 },
#                 "projected_fcfs": projected_fcfs
#             }
            
#         except Exception as e:
#             return {"error": str(e)}

class CAPMCalculator:
    """Calculadora de CAPM (Capital Asset Pricing Model)"""
    
    @staticmethod
    def calculate(symbol: str, market_return: float = 0.10, 
                  risk_free_rate: float = 0.05) -> Dict:
        """
        Calcula o retorno esperado usando CAPM
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Obter beta
            beta = info.get('beta', 1.0)
            
            # Calcular retorno esperado
            expected_return = risk_free_rate + beta * (market_return - risk_free_rate)
            
            # Preço atual
            current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
            
            return {
                "symbol": symbol,
                "company_name": info.get('longName', symbol),
                "beta": beta,
                "risk_free_rate": risk_free_rate,
                "market_return": market_return,
                "expected_return": expected_return,
                "current_price": current_price,
                "interpretation": f"O ativo deve render {expected_return:.2%} ao ano segundo o CAPM"
            }
            
        except Exception as e:
            return {"error": str(e)}