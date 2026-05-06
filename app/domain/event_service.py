import uuid
from datetime import datetime

from app.domain.event import Event


class EventService:
    def __init__(self, repo):
        self.repo = repo

    async def get_all(self) -> list[Event]:
        docs = await self.repo.get_all()
        return [Event(**doc) for doc in docs]

    async def get_by_id(self, event_id: str) -> Event | None:
        doc = await self.repo.get_by_id(event_id)
        if doc is None:
            return None
        return Event(**doc)

    async def create(self, name: str, date: datetime, images_folder: str) -> Event:
        event = Event(
            id=str(uuid.uuid7()),
            name=name,
            date=date,
            images_folder=images_folder,
            photos_count=0,
        )
        await self.repo.create(event.model_dump(by_alias=True))
        return event

    async def increment_photos_count(self, event_id: str) -> None:
        await self.repo.increment_photos_count(event_id)
