from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, health, jobs, reports, similar, variants
from app.config.settings import get_settings
from app.db.database import SessionLocal
from app.services.reference_data import seed_reference_data


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(variants.router)
    app.include_router(jobs.router)
    app.include_router(similar.router)
    app.include_router(reports.router)

    @app.on_event("startup")
    def startup() -> None:
        db = SessionLocal()
        try:
            seed_reference_data(db)
        finally:
            db.close()

    return app


app = create_app()
