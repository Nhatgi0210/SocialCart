from datetime import datetime, timezone

from fastapi.responses import JSONResponse
from sqlalchemy import text

from shared.db.session import get_engine


async def readiness(service: str, redis):
    try:
        async with get_engine().connect() as conn:
            await conn.execute(text("SELECT 1"))
        await redis.ping()
    except Exception:
        # The OpenAPI 503 response uses the common error envelope.
        return JSONResponse(status_code=503, content={"success": False, "error": {
            "code": "SERVICE_UNAVAILABLE", "message": "Dependency unavailable", "details": []}})
    return JSONResponse(content={"status": "ok", "service": service,
                                 "checked_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")})
