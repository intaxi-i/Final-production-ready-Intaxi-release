from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v2.routes_admin import router as admin_router
from app.api.v2.routes_city import router as city_router
from app.api.v2.routes_driver import router as driver_router
from app.api.v2.routes_intercity import router as intercity_router
from app.api.v2.routes_public import router as public_router
from app.api.v2.routes_user import router as user_router
from app.core.config import get_settings
from app.core.errors import DomainError

settings = get_settings()

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(DomainError)
async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.http_status,
        content={"error": {"code": exc.code, "message": exc.message, "details": exc.details}},
    )


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "app": settings.app_name}


app.include_router(user_router, prefix=settings.api_prefix)
app.include_router(city_router, prefix=settings.api_prefix)
app.include_router(driver_router, prefix=settings.api_prefix)
app.include_router(intercity_router, prefix=settings.api_prefix)
app.include_router(admin_router, prefix=settings.api_prefix)
app.include_router(public_router, prefix=settings.api_prefix)
