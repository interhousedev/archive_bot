from motor.motor_asyncio import AsyncIOMotorClient


class MongoClient:
    """MongoDB client."""

    def __init__(self, uri: str, db_name: str):
        if not all([uri, db_name]):
            raise ValueError("uri and db_name are required")

        self.client = AsyncIOMotorClient(uri)
        self.db = self.client[db_name]

    def users(self):
        return self.db["users"]

    def events(self):
        return self.db["events"]

    def media_files(self):
        return self.db["media_files"]
