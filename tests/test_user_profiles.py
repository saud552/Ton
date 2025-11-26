import pytest

from app.db import (
    DatabaseManager,
    User,
    UserProfileRepository,
    UserRepository,
)


@pytest.mark.asyncio
async def test_user_profile_repository(tmp_path):
    db_path = tmp_path / "profiles.db"
    manager = DatabaseManager(str(db_path))
    await manager.initialize()

    user_repo = UserRepository(manager)
    await user_repo.upsert_user(User(user_id=77, username="tester", full_name="Tester"))

    profiles = UserProfileRepository(manager)
    await profiles.ensure_profile(77, default_language="ar")
    await profiles.upsert_partial(77, primary_wallet_address="EQTEST", language="en")

    profile = await profiles.get_profile(77)
    assert profile is not None
    assert profile.primary_wallet_address == "EQTEST"
    assert profile.language == "en"
