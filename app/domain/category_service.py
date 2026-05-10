import uuid

from app.domain.category import Category


class CategoryService:
    def __init__(self, repo):
        self.repo = repo

    async def get_all(self) -> list[Category]:
        docs = await self.repo.get_all()
        return [Category(**doc) for doc in docs]

    async def get_by_id(self, category_id: str) -> Category | None:
        doc = await self.repo.get_by_id(category_id)
        if doc is None:
            return None
        return Category(**doc)

    async def create(self, name: str) -> Category:
        category = Category(
            id=str(uuid.uuid7()),
            name=name,
        )
        await self.repo.create(category.model_dump(by_alias=True))
        return category