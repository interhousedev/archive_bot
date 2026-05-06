import aiohttp
import asyncio

from app.infrastructure.emis.exceptions import EMISAuthError, EMISRequestError


class EMISClient:
    """Client to EMIS API."""

    def __init__(
            self,
            base_url: str = "https://emis.edu.uz/api/v1/",
            concurrency: int = 20,
            request_delay: int = 0
    ):
        self.base_url = base_url
        self.semaphore = asyncio.Semaphore(concurrency)
        self.request_delay = request_delay
        self.session = aiohttp.ClientSession()

    async def authed_request(
            self,
            access_token: str,
            method: str,
            url: str,
            data: dict = None,
            headers: dict = None,
            can_retry: bool = False
    ) -> tuple[int, dict | None, str | None]:
        headers = headers or {}
        headers.update({"Authorization": access_token})


        status, data = await self.request(
            method=method, url=url, data=data, headers=headers
        )

        return status, data, None

    async def request(
            self,
            method: str,
            url: str,
            data: dict = None,
            headers: dict = None
    ) -> tuple[int, dict | None]:
        async with self.semaphore:
            await asyncio.sleep(self.request_delay)
            async with self.session.request(
                    method=method, url=url, headers=headers or {},
                    json=data or {}) as response:
                data = await response.json()
                return response.status, data

    async def login(self, login: str, password: str) -> str:
        """Login and return access token."""
        url = self.base_url + "student-profiles/login/"

        status, data = await self.request(
            method="post", url=url, data={"login": login, "password": password}
        )

        if status == 401:
            raise EMISAuthError()
        if status != 200:
            raise EMISRequestError(f"Login endpoint returned HTTP {status}.")

        return data.get("result", {}).get("access_token")

    async def get_curriculum(self, access_token: str) -> dict:
        """GET /student-profiles/curriculum/ — returns curriculum result dict."""
        url = self.base_url + "student-profiles/curriculum/"

        status, data, _ = await self.authed_request(
            access_token=access_token,
            method="get",
            url=url,
        )

        if status != 200:
            raise EMISRequestError(f"Curriculum endpoint returned HTTP {status}.")

        return data.get("result", {})
