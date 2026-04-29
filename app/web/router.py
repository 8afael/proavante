# # backend/app/web/router.py

from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pathlib import Path
from jinja2 import FileSystemBytecodeCache
from jinja2 import Environment
from app.services.database import get_db
from app.web.service import WebDashboardService

router = APIRouter(include_in_schema=False)

BASE_DIR = Path(__file__).resolve().parents[2]
templates = Jinja2Templates(directory=str(BASE_DIR / "app/templates"))
#templates = Jinja2Templates(directory=str(BASE_DIR / "/acoes/app/app/templates"))
#templates.env.cache = {}
#templates.env.bytecode_cache = None
templates.env = Environment(
    loader=templates.env.loader,
    auto_reload=True,
    cache_size=0
)


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    stocks = WebDashboardService.get_summary_cards(db)
    return templates.TemplateResponse("index.html", {
        "request": request,
        "stocks": stocks
    })


@router.get("/stocks/{symbol}", response_class=HTMLResponse)
async def stock_page(request: Request, symbol: str, db: Session = Depends(get_db)):
    chart_data = WebDashboardService.prepare_chart_data(db, symbol)
    return templates.TemplateResponse("stock_detail.html", {
        "request": request,
        "symbol": symbol.upper(),
        "chart_data": chart_data
    })


@router.get("/admin/manage", response_class=HTMLResponse)
async def admin_page(request: Request):
    return templates.TemplateResponse("admin.html", {
        "request": request
    })

