import asyncio
import boto3
from botocore.client import BaseClient


class S3Client:
    """Async-friendly S3 client wrapping boto3 (sync calls run in thread pool)."""

    def __init__(
        self,
        endpoint_url: str,
        access_key: str,
        secret_key: str,
        bucket_name: str,
        base_url: str,
    ):
        self.bucket_name = bucket_name
        self.base_url = base_url.rstrip("/")
        self._client: BaseClient = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
        )

    def _upload_sync(self, key: str, data: bytes, content_type: str) -> None:
        self._client.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=data,
            ContentType=content_type,
        )

    def _list_sync(self, prefix: str) -> list[str]:
        paginator = self._client.get_paginator("list_objects_v2")
        keys = []
        for page in paginator.paginate(Bucket=self.bucket_name, Prefix=prefix):
            for obj in page.get("Contents", []):
                keys.append(obj["Key"])
        return keys

    async def upload(self, folder: str, filename: str, data: bytes,
                     content_type: str = "image/jpeg") -> str:
        """Upload bytes to {bucket}/{folder}/{filename}. Returns public URL."""
        key = f"{folder}/{filename}"
        await asyncio.to_thread(self._upload_sync, key, data, content_type)
        return f"{self.base_url}/{key}"

    async def list_folder(self, folder: str) -> list[str]:
        """List object keys under {bucket}/{folder}/."""
        prefix = f"{folder}/"
        return await asyncio.to_thread(self._list_sync, prefix)

    def _presign_sync(self, key: str, expires: int) -> str:
        return self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket_name, "Key": key},
            ExpiresIn=expires,
        )

    async def presigned_url(self, key: str, expires_seconds: int = 86400) -> str:
        """Generate a presigned GET URL valid for `expires_seconds` (default 1 day)."""
        return await asyncio.to_thread(self._presign_sync, key, expires_seconds)

    def public_url(self, key: str) -> str:
        return f"{self.base_url}/{key}"
