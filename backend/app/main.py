from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.api.routes import router
from app.api.model_routes import router as model_router

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="InfraTwinAI: AI-assisted, budget-aware sustainable building design and infrastructure planning assistant.",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Narrow CORS configuration for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Clean, sanitized validation error messages without leaking internal traces."""
    errors = []
    for err in exc.errors():
        loc = " -> ".join([str(x) for x in err.get("loc", []) if x != "body"])
        msg = err.get("msg", "Validation error")
        errors.append(f"{loc}: {msg}" if loc else msg)
    
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Invalid building parameters or request payload",
            "errors": errors
        }
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Sanitized 500 error handler avoiding trace leakage."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An internal processing error occurred while evaluating building parameters."
        }
    )

app.include_router(router)
app.include_router(model_router)
