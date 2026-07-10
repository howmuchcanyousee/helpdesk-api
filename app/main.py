from fastapi import FastAPI

from app.api.routes.auth import router as auth_router
from app.api.routes.comments import router as comments_router
from app.api.routes.health import router as health_router
from app.api.routes.tickets import router as tickets_router
from app.api.routes.users import router as users_router
from app.core.config import settings


def create_application() -> FastAPI:
    app = FastAPI(title=settings.app_name, debug=settings.debug)
    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(comments_router)
    app.include_router(tickets_router)
    app.include_router(users_router)
    return app


app = create_application()
