import pytest
import asyncio
from unittest.mock import AsyncMock

from app.services.nft_service import NFTService


@pytest.mark.asyncio
async def test_upload_metadata_to_ipfs_monkeypatched(monkeypatch):
    # Monkeypatch IPFSClient.upload_json to return a fake hash
    fake_hash = "QmFakeHash1234567890"

    class FakeIPFS:
        async def upload_json(self, data, filename="metadata.json"):
            return fake_hash

        def get_gateway_url(self, ipfs_hash: str):
            return f"https://gateway.example/{ipfs_hash}"

    monkeypatch.setattr("app.services.nft_service.IPFSClient", lambda *args, **kwargs: FakeIPFS())

    result = await NFTService.upload_metadata_to_ipfs({"name": "Test"})
    assert result is not None
    ipfs_hash, gateway = result
    assert ipfs_hash == fake_hash
    assert gateway.endswith(fake_hash)
