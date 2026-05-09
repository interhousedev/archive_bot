import uuid

from app.domain.user import User


class UserService:
    def __init__(self, repo):
        self.repo = repo

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        doc = await self.repo.get_by_telegram_id(telegram_id)
        if doc is None:
            return None
        return User(**doc)

    async def create(self, telegram_id: int) -> User:
        user = User(id=str(uuid.uuid7()), telegram_id=telegram_id, is_verified=False)
        await self.repo.upsert(user.model_dump(by_alias=True))
        return user

    async def verify(self, telegram_id: int) -> None:
        await self.repo.set_verified(telegram_id=telegram_id, verified=True)

    async def set_banned(self, telegram_id: int, banned: bool) -> None:
        await self.repo.set_banned(telegram_id=telegram_id, banned=banned)
