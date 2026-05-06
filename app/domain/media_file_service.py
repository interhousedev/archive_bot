import uuid

from app.domain.media_file import MediaFile
from app.domain.file_type import FileType


class MediaFileService:
    def __init__(self, repo):
        self.repo = repo

    async def get_by_id(self, file_id: str) -> MediaFile | None:
        doc = await self.repo.get_by_id(file_id)
        return MediaFile(**doc) if doc else None

    async def get_visible_for_event(self, event_id: str) -> list[MediaFile]:
        docs = await self.repo.get_by_event_id(event_id, only_visible=True)
        return [MediaFile(**d) for d in docs]

    async def get_all_for_event(self, event_id: str) -> list[MediaFile]:
        docs = await self.repo.get_by_event_id(event_id, only_visible=False)
        return [MediaFile(**d) for d in docs]

    async def get_by_author_and_event(self, author_id: str, event_id: str) -> list[MediaFile]:
        docs = await self.repo.get_by_author_and_event(author_id, event_id)
        return [MediaFile(**d) for d in docs]

    async def create(
        self, file_name: str, event_id: str, author_id: str, file_type: FileType
    ) -> MediaFile:
        media_file = MediaFile(
            id=str(uuid.uuid7()),
            file_name=file_name,
            event_id=event_id,
            author_id=author_id,
            type=file_type,
            is_showed=True,
        )
        await self.repo.create(media_file.model_dump(by_alias=True))
        return media_file

    async def set_showed(self, file_id: str, showed: bool) -> None:
        await self.repo.set_showed(file_id, showed)
