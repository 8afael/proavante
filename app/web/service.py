import json
from sqlalchemy import desc
from app.models.stock_models import StockInfo, ValuationResult, StockData

class WebDashboardService:
    @staticmethod
    def get_summary_cards(db):
        """Busca todas as ações e anexa o último valuation de cada uma"""
        stocks = db.query(StockInfo).all()
        
        for stock in stocks:
            # Busca o último DCF na tabela valuation_results
            last_valuation = db.query(ValuationResult)\
                .filter(ValuationResult.symbol == stock.symbol, ValuationResult.valuation_type == 'DCF')\
                .order_by(desc(ValuationResult.created_at)).first()
            
            if last_valuation:
                res_data = json.loads(last_valuation.result)
                stock.intrinsic_value = res_data.get("intrinsic_value")
                
                # Busca o preço mais recente no banco para o Upside
                latest_data = db.query(StockData.close_price)\
                    .filter(StockData.symbol == stock.symbol)\
                    .order_by(desc(StockData.date)).first()
                
                if latest_data and stock.intrinsic_value:
                    stock.upside = ((stock.intrinsic_value / latest_data[0]) - 1) * 100
            else:
                stock.intrinsic_value = None
                stock.upside = None
        return stocks

    @staticmethod
    def prepare_chart_data(db, symbol: str):
        """Prepara os dados para o Chart.js na página de detalhes"""
        # Busca os últimos 30 registros de preço
        historical = db.query(StockData)\
            .filter(StockData.symbol == symbol.upper())\
            .order_by(StockData.date.asc())\
            .limit(30).all()
        
        return {
            "labels": [d.date.strftime("%d/%m") for d in historical],
            "prices": [d.close_price for d in historical]
        }

