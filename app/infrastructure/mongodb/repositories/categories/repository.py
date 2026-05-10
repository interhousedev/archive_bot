from app.infrastructure.mongodb.client import MongoClient


class CategoryRepository:
    def __init__(self, client: MongoClient):
        if not client:
            raise ValueError("MongoDB client is required")
        self.collection = client.categories()

    def _normalize(self, doc: dict) -> dict:
        doc["id"] = str(doc.pop("_id"))
        return doc

    async def get_all(self) -> list[dict]:
        docs = await self.collection.find({}).to_list(length=None)
        return [self._normalize(d) for d in docs]

    async def get_by_id(self, category_id: str) -> dict | None:
        doc = await self.collection.find_one({"_id": category_id})
        if doc:
            return self._normalize(doc)
        return None

    async def create(self, category_dict: dict) -> None:
        await self.collection.insert_one(category_dict)