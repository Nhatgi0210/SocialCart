import importlib.util
from unittest.mock import AsyncMock, MagicMock

import pytest

from tests.conftest import BACKEND
from shared.passwords import verify_password


@pytest.mark.asyncio
async def test_seller_seed_preserves_password_and_is_idempotent(monkeypatch):
    spec = importlib.util.spec_from_file_location("seed_demo", BACKEND.parent / "scripts/seed-demo.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setenv("SEED_SELLER_EMAIL", "seller@example.com")
    monkeypatch.setenv("SEED_SELLER_PASSWORD", " password with spaces ")
    monkeypatch.setenv("SEED_SELLER_NAME", "Shop")
    session = AsyncMock()
    session.add = MagicMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    session.execute.return_value = result
    await module.seed_seller(session)
    user = session.add.call_args.args[0]
    assert user.name == "Shop"
    assert verify_password(" password with spaces ", user.hashed_password)
    result.scalar_one_or_none.return_value = user
    monkeypatch.setenv("SEED_SELLER_PASSWORD", "different password")
    await module.seed_seller(session)
    session.add.assert_called_once()
    session.commit.assert_awaited_once()
    assert verify_password(" password with spaces ", user.hashed_password)
