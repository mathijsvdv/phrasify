from fastapi import FastAPI, status
from pydantic import BaseModel

from .routers.v1 import router as v1_router


class HealthCheck(BaseModel):
    """Response model to validate and return when performing a health check."""

    status: str = "OK"


app = FastAPI(
    title="Card Generator API",
    version="1.0",
    description="API for generating Anki cards from a prompt and input card.",
)


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


app.include_router(v1_router, prefix="/v1", tags=["v1"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8800)
