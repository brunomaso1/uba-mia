from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_keycloak_middleware import KeycloakConfiguration, setup_keycloak_middleware

from app.core.config import settings
from app.deps import map_user
from app.routers.categories import router as categories_router
from app.routers.expenses import router as expenses_router
from app.routers.groups import router as groups_router
from app.routers.users import router as users_router

app = FastAPI(title="Expense API", version="0.1.0")

app.include_router(categories_router, prefix=settings.api_prefix)
app.include_router(expenses_router, prefix=settings.api_prefix)
app.include_router(groups_router, prefix=settings.api_prefix)
app.include_router(users_router, prefix=settings.api_prefix)

keycloak_config = KeycloakConfiguration(
    url=f"{settings.keycloak_url}/",
    realm=settings.keycloak_realm,
    client_id=settings.keycloak_client_id,
)

# Add the Keycloak middleware FIRST so that, after CORS is added below, CORS is
# the OUTERMOST middleware: it answers OPTIONS preflight without auth and emits
# CORS headers even on 401 responses. (Starlette runs the last-added middleware
# first.)
setup_keycloak_middleware(
    app,
    keycloak_configuration=keycloak_config,
    user_mapper=map_user,
    exclude_patterns=["/health", "/docs", "/redoc", "/openapi.json"],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.backend_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/test")
def test_info():
    return {
        "service": app.title,
        "version": app.version,
        "api_prefix": settings.api_prefix,
        "status": "ok",
    }
