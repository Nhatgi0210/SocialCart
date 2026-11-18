import asyncio
import logging

import httpx
from sqlalchemy.exc import SQLAlchemyError

from shared.auth import AuthError
from shared.config import settings


async def internal_request(method, url, *, body=None):
    if not settings.internal_service_token:
        raise AuthError(503, "CONFIG_REQUIRED", "Cần INTERNAL_SERVICE_TOKEN ở backend")
    async with httpx.AsyncClient(timeout=8, trust_env=False) as client:
        response = await client.request(method, url, json=body,
                                        headers={"Authorization": "Bearer " + settings.internal_service_token})
    if not response.is_success:
        raise AuthError(503, "INTERNAL_UNAVAILABLE", "Dịch vụ nội bộ tạm thời không sẵn sàng")
    try:
        data = response.json()["data"]
        if not isinstance(data, dict):
            raise ValueError
        return data
    except (ValueError, KeyError, TypeError):
        raise AuthError(503, "INTERNAL_UNAVAILABLE", "Phản hồi nội bộ không hợp lệ") from None


async def poll(work):
    while True:
        try:
            if await work():
                continue
        except (SQLAlchemyError, httpx.HTTPError, AuthError):
            logging.getLogger(work.__module__).warning("Background operation failed; durable work retained")
        await asyncio.sleep(1)
