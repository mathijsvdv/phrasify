from fastapi import FastAPI, status
from fastapi.responses import RedirectResponse
from fastapi_versionizer import Versionizer
from pydantic import BaseModel

from .routers.cards import router as cards_router

app = FastAPI(
    title="Card Generator API",
    version="1.0",
    description="API for generating Anki cards from a prompt and input card.",
)

app.include_router(cards_router, prefix="/cards", tags=["Cards"])


versions = Versionizer(
    app=app,
    prefix_format="/v{major}",
    semantic_version_format="{major}",
    latest_prefix="/latest",
).versionize()


@app.get("/", include_in_schema=False)
async def docs_redirect():
    return RedirectResponse(url="/docs")


class HealthCheck(BaseModel):
    """Response model to validate and return when performing a health check."""

    status: str = "OK"


@app.get(
    "/health",
    tags=["Health Check"],
    summary="Perform a Health Check",
    response_description="Return HTTP Status Code 200 (OK)",
    status_code=status.HTTP_200_OK,
    response_model=HealthCheck,
)
def get_health():
    return HealthCheck(status="OK")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8800)
