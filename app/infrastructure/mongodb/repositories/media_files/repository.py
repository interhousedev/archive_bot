from app.infrastructure.mongodb.client import MongoClient


class MediaFileRepository:
    def __init__(self, client: MongoClient):
        if not client:
            raise ValueError("MongoDB client is required")
        self.collection = client.media_files()

    def _normalize(self, doc: dict) -> dict:
        doc["id"] = str(doc.pop("_id"))
        return doc

    async def get_by_id(self, file_id: str) -> dict | None:
        doc = await self.collection.find_one({"_id": file_id})
        return self._normalize(doc) if doc else None

    async def get_by_event_id(self, event_id: str, only_visible: bool = False) -> list[dict]:
        query: dict = {"event_id": event_id}
        if only_visible:
            query["is_showed"] = True
            query["is_banned"] = False
        docs = await self.collection.find(query).to_list(length=None)
        return [self._normalize(d) for d in docs]

    async def get_by_author_and_event(self, author_id: str, event_id: str) -> list[dict]:
        docs = await self.collection.find(
            {"author_id": author_id, "event_id": event_id}
        ).to_list(length=None)
        return [self._normalize(d) for d in docs]

    async def create(self, file_dict: dict) -> None:
        await self.collection.insert_one(file_dict)

    async def set_showed(self, file_id: str, showed: bool) -> None:
        await self.collection.update_one(
            {"_id": file_id}, {"$set": {"is_showed": showed}}
        )

    async def set_banned(self, file_id: str, banned: bool) -> None:
        await self.collection.update_one(
            {"_id": file_id}, {"$set": {"is_banned": banned}}
        )

    async def delete(self, file_id: str) -> None:
        await self.collection.delete_one({"_id": file_id})