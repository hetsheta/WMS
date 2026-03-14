from fastapi import APIRouter
from app.api.v1.endpoints import auth, warehouses, products, stock, operations, dashboard

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(warehouses.router)
api_router.include_router(products.router)
api_router.include_router(stock.router)
api_router.include_router(operations.router)
api_router.include_router(dashboard.router)
