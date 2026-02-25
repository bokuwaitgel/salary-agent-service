#here is health check endpoint, which can be used to check if the service is running and healthy.
from src.api.api_routes import register

@register(name="health", method="GET", required_keys=[])
async def health_check_handler(data: dict) -> dict:
    return {"status": "ok"}