import pytest
from aiogram.fsm.storage.base import StorageKey

from app.db import DatabaseManager, User, UserRepository
from app.storage import DatabaseStorage


@pytest.mark.asyncio
async def test_database_storage_persists_state(tmp_path):
    db_path = tmp_path / "fsm.db"
    manager = DatabaseManager(str(db_path))
    await manager.initialize()
    storage = DatabaseStorage(manager)

    key = StorageKey(bot_id=1, chat_id=1, user_id=42)
    user_repo = UserRepository(manager)
    await user_repo.upsert_user(User(user_id=42, username="test", full_name="Test User"))

    await storage.set_state(key, "waiting_for_stars")
    state = await storage.get_state(key)
    assert state == "waiting_for_stars"

    await storage.set_data(key, {"stars_count": 100, "ton_amount": 1.23})
    data = await storage.get_data(key)
    assert data["stars_count"] == 100
    assert pytest.approx(data["ton_amount"], rel=1e-9) == 1.23

    await storage.close()
