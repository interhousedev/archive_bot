from dataclasses import dataclass

from app.settings import Settings
from app.domain.user_service import UserService
from app.domain.event_service import EventService
from app.domain.media_file_service import MediaFileService
from app.domain.category_service import CategoryService
from app.infrastructure.emis.client import EMISClient
from app.infrastructure.mongodb.client import MongoClient
from app.infrastructure.mongodb.repositories.users.repository import UserRepository
from app.infrastructure.mongodb.repositories.events.repository import EventRepository
from app.infrastructure.mongodb.repositories.media_files.repository import MediaFileRepository
from app.infrastructure.mongodb.repositories.categories.repository import CategoryRepository
from app.infrastructure.s3.client import S3Client


@dataclass
class Container:
    user_service: UserService
    event_service: EventService
    media_file_service: MediaFileService
    category_service: CategoryService
    emis_client: EMISClient
    s3_client: S3Client
    settings: Settings


async def bootstrap(settings: Settings) -> Container:
    mongo = MongoClient(uri=settings.mongo_uri, db_name=settings.mongo_db_name)
    await mongo.client.admin.command("ping")

    user_repo = UserRepository(client=mongo)
    event_repo = EventRepository(client=mongo)
    media_file_repo = MediaFileRepository(client=mongo)
    category_repo = CategoryRepository(client=mongo)

    user_service = UserService(repo=user_repo)
    event_service = EventService(repo=event_repo)
    media_file_service = MediaFileService(repo=media_file_repo)
    category_service = CategoryService(repo=category_repo)

    emis_client = EMISClient(base_url=settings.emis_base_url)

    s3_client = S3Client(
        endpoint_url=settings.s3_endpoint_url,
        access_key=settings.s3_access_key,
        secret_key=settings.s3_secret_key,
        bucket_name=settings.s3_bucket_name,
        base_url=settings.s3_base_url,
    )

    return Container(
        user_service=user_service,
        event_service=event_service,
        media_file_service=media_file_service,
        category_service=category_service,
        emis_client=emis_client,
        s3_client=s3_client,
        settings=settings,
    )
