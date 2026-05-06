from app.infrastructure.mongodb.client import MongoClient


class EventRepository:
    """Event repository backed by MongoDB."""

    def __init__(self, client: MongoClient):
        if not client:
            raise ValueError("MongoDB client is required")
        self.collection = client.events()

    def _normalize(self, doc: dict) -> dict:
        doc["id"] = str(doc.pop("_id"))
        return doc

    async def get_all(self) -> list[dict]:
        docs = await self.collection.find({}).to_list(length=None)
        return [self._normalize(d) for d in docs]

    async def get_by_id(self, event_id: str) -> dict | None:
        doc = await self.collection.find_one({"_id": event_id})
        if doc:
            return self._normalize(doc)
        return None

    async def create(self, event_dict: dict) -> None:
        await self.collection.insert_one(event_dict)

    async def increment_photos_count(self, event_id: str) -> None:
        await self.collection.update_one(
            {"_id": event_id},
            {"$inc": {"photos_count": 1}},
        )
