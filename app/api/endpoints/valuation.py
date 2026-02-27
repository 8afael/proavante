from fastapi import APIRouter
from app.services.valuation_engine import DCFCalculator
from app.schemas.stock_schemas import DCFRequest, DCFResponse

router = APIRouter()

@router.post("/dcf", response_model=DCFResponse)
async def calculate_dcf(request: DCFRequest):
    """
    Endpoint para calcular o DCF de uma ação.
    - **symbol**: Ticker da ação (ex: PETR4.SA)
    - **growth_rate**: Taxa de crescimento esperada
    - **discount_rate**: Taxa de desconto (WACC)
    """
    result = DCFCalculator.calculate(
        symbol=request.symbol,
        growth_rate=request.growth_rate,
        discount_rate=request.discount_rate
    )
    return result