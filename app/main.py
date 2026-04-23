# app/main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import pandas as pd

from app.config import settings
from app.services.model_loader import model_loader
from app.routers import players, predictions, injuries, scout

# إعداد التسجيل
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """إدارة دورة حياة التطبيق - تحميل النماذج عند البدء"""
    logger.info("🔄 Starting Player Scouting Recommendation System...")
    
    try:
        # تحميل النماذج والبيانات
        models = model_loader.load_all()
        app.state.models = models
        logger.info("✅ Models and data loaded successfully!")
        
    except Exception as e:
        logger.error(f"❌ Failed to load models: {e}")
        raise
    
    yield
    
    logger.info("👋 Shutting down Player Scouting Recommendation System...")

# إنشاء التطبيق
app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# إعداد CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# تسجيل الـ Routers
app.include_router(players.router, prefix="/api/v1/players", tags=["🔍 Players"])
app.include_router(predictions.router, prefix="/api/v1/predictions", tags=["🔮 Predictions"])
app.include_router(injuries.router, prefix="/api/v1/injuries", tags=["🏥 Injuries"])
app.include_router(scout.router, prefix="/api/v1/scout", tags=["🤖 Scout AI"])

# Endpoint للتحقق من الصحة
@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "⚽ Player Scouting Recommendation System is running!",
        "documentation": "/docs",
        "health": "/health",
        "version": settings.API_VERSION
    }

@app.get("/health", tags=["Health"])
async def health_check(request: Request):
    """Endpoint للتحقق من صحة النظام"""
    models_loaded = hasattr(request.app.state, "models") and request.app.state.models is not None
    return {
        "status": "healthy",
        "models_loaded": models_loaded,
        "timestamp": pd.Timestamp.now().isoformat()
    }

# Middleware لتسجيل الطلبات (اختياري)
@app.middleware("http")
async def log_requests(request: Request, call_next):
    import time
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s")
    
    return response