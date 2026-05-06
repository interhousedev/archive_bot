from app.infrastructure.mongodb.client import MongoClient


class UserRepository:
    """User repository backed by MongoDB."""

    def __init__(self, client: MongoClient):
        if not client:
            raise ValueError("MongoDB client is required")
        self.collection = client.users()

    async def get_by_telegram_id(self, telegram_id: int) -> dict | None:
        doc = await self.collection.find_one({"telegram_id": telegram_id})
        if doc:
            doc["id"] = str(doc.pop("_id"))
        return doc

    async def upsert(self, user_dict: dict) -> None:
        """Insert or replace by _id."""
        _id = user_dict.get("_id")
        await self.collection.replace_one({"_id": _id}, user_dict, upsert=True)

    async def set_verified(self, telegram_id: int, verified: bool) -> None:
        await self.collection.update_one(
            {"telegram_id": telegram_id},
            {"$set": {"is_verified": verified}},
        )
