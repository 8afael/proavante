# backend/app/web/router.py
import os

from fastapi import APIRouter, FastAPI, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.services.database import get_db
from app.web.service import WebDashboardService

router = APIRouter(include_in_schema=False) # Esconde do Swagger
current_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(os.path.dirname(current_dir))
template_path = os.path.join(base_dir, "templates")
templates = Jinja2Templates(directory=template_path)

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    stocks = WebDashboardService.get_summary_cards(db)
    return templates.TemplateResponse("index.html", {"request": request, "stocks": stocks})

@router.get("/dashboard/{symbol}", response_class=HTMLResponse)
async def stock_page(request: Request, symbol: str, db: Session = Depends(get_db)):
    chart_data = WebDashboardService.prepare_chart_data(db, symbol)
    return templates.TemplateResponse("stock_detail.html", {
        "request": request, 
        "symbol": symbol.upper(),
        "chart_data": chart_data
    })

@router.get("/admin/manage", response_class=HTMLResponse)
async def admin_page(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})