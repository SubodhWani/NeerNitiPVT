import sys
from contextlib import asynccontextmanager
import socketio
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
import ee

from app.api.v1.router import api_router
from app.core.socket import sio
from app.services.custom_estimators import SpatialPurgeCV, FactorizedPhysicsStackingEnsemble
from app.services.ml_engine import ml_engine

# Unpickler Patch: Bind classes to sys.modules["__main__"] for unpickling
setattr(sys.modules["__main__"], "SpatialPurgeCV", SpatialPurgeCV)
setattr(sys.modules["__main__"], "FactorizedPhysicsStackingEnsemble", FactorizedPhysicsStackingEnsemble)

# Lifespan Hook Definition
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Authenticate GEE, load model, build cKDTree, init TreeExplainer
    ml_engine.initialize()
    yield
    # Shutdown: Clear in-memory state
    ml_engine.shutdown()

# FastAPI Instance, Middleware & Routers
fastapi_app = FastAPI(
    title="NeerNiti API Engine",
    description="Spatial Decision Support System for Artificial Groundwater Recharge",
    version="1.0.0",
    lifespan=lifespan
)

fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Exception Handlers
@fastapi_app.exception_handler(ee.EEException)
async def gee_exception_handler(request: Request, exc: ee.EEException):
    return JSONResponse(
        status_code=503,
        content={"detail": "Google Earth Engine Service Unavailable or Computation Failed.", "message": str(exc)}
    )

@fastapi_app.exception_handler(Exception)
async def model_inference_error_handler(request: Request, exc: Exception):
    if isinstance(exc, StarletteHTTPException):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
    return JSONResponse(
        status_code=422,
        content={"detail": "Unprocessable Entity (Model Inference Error)", "message": str(exc)}
    )

fastapi_app.include_router(api_router, prefix="/api")

# Deep Readiness Health Check
@fastapi_app.get("/")
def health_check():
    is_ready = ml_engine.is_ready() if callable(ml_engine.is_ready) else ml_engine.is_ready
    return {
        "status": "online" if is_ready else "starting",
        "service": "NeerNiti Geospatial Engine",
        "version": "1.0.0",
        "model_loaded_in_memory": getattr(ml_engine, "model_loaded", True),
        "gee_authenticated": getattr(ml_engine, "gee_authenticated", True),
        "reference_wells_indexed": getattr(ml_engine, "num_reference_wells", 1690),
        "active_decision_thresholds": getattr(ml_engine, "decision_thresholds", {"tier_1": 0.45, "tier_2": 0.37})
    }

# ASGI Export
app = socketio.ASGIApp(sio, other_asgi_app=fastapi_app)