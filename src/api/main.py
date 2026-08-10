import time
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from src.api.routers import (
    companies, screener, sectors, peers, 
    valuation, portfolio, documents, health
)

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="Nifty 100 Financial Intelligence API", version="1.0.0")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request Logging Middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(f"{request.method} {request.url.path} completed in {process_time:.4f}s")
    return response

# Include Routers
app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(companies.router, prefix="/api/v1/companies", tags=["Companies"])
app.include_router(screener.router, prefix="/api/v1/screener", tags=["Screener"])
app.include_router(sectors.router, prefix="/api/v1/sectors", tags=["Sectors"])
app.include_router(peers.router, prefix="/api/v1/peers", tags=["Peers"])
app.include_router(valuation.router, prefix="/api/v1/market-cap", tags=["Valuation"])
app.include_router(portfolio.router, prefix="/api/v1/portfolio", tags=["Portfolio"])
app.include_router(documents.router, prefix="/api/v1/documents", tags=["Documents"])
