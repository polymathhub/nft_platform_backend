import aiohttp
import json
import logging
from typing import Optional
from app.config import get_settings
import re

MAX_METADATA_SIZE = 1024 * 1024
MAX_FIELD_LENGTH = 1000

logger = logging.getLogger(__name__)
settings = get_settings()


class IPFSClient:

    def __init__(self, api_url: str = settings.ipfs_api_url, gateway_url: str = settings.ipfs_gateway_url):
        self.api_url = api_url
        self.gateway_url = gateway_url

    async def upload_file(self, file_data: bytes, filename: str) -> Optional[str]:
        try:
            async with aiohttp.ClientSession() as session:
                files = {"file": (filename, file_data)}
                async with session.post(
                    f"{self.api_url}/api/v0/add",
                    data=files,
                    params={"wrap-with-directory": "true"},
                ) as response:
                    if response.status == 200:
                        lines = await response.text()
                        for line in lines.strip().split('\n'):
                            if line:
                                entry = json.loads(line)
                                if entry.get("Name") == "":
                                    return entry.get("Hash")
                        return None
                    else:
                        logger.error(f"IPFS upload failed with status {response.status}")
                        return None
        except Exception as e:
            logger.error(f"IPFS upload error: {e}")
            return None

    async def upload_json(self, data: dict, filename: str = "metadata.json") -> Optional[str]:
        clean = sanitize_metadata(data)
        json_bytes = json.dumps(clean).encode("utf-8")
        if len(json_bytes) > MAX_METADATA_SIZE:
            logger.error("Metadata size exceeds maximum allowed")
            return None
        return await self.upload_file(json_bytes, filename)

    async def retrieve_file(self, ipfs_hash: str) -> Optional[bytes]:
        try:
            gateway_url = f"{self.gateway_url}/{ipfs_hash}"
            async with aiohttp.ClientSession() as session:
                async with session.get(gateway_url, timeout=30) as response:
                    if response.status == 200:
                        return await response.read()
                    else:
                        logger.error(f"IPFS retrieval failed: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"IPFS retrieval error: {e}")
            return None

    async def retrieve_json(self, ipfs_hash: str) -> Optional[dict]:
        content = await self.retrieve_file(ipfs_hash)
        if content:
            try:
                return json.loads(content.decode("utf-8"))
            except json.JSONDecodeError as e:
                logger.error(f"JSON parse error: {e}")
                return None
        return None

    def get_gateway_url(self, ipfs_hash: str) -> str:
        return f"{self.gateway_url}/{ipfs_hash}"


def sanitize_metadata(metadata: dict) -> dict:
    if not isinstance(metadata, dict):
        return {}

    clean = {}
    for k, v in metadata.items():
        if not isinstance(k, str):
            continue
        if k.startswith("$") or "<script" in k.lower():
            continue

        if isinstance(v, str):
            val = v.strip()
            val = re.sub(r"(?i)<script.*?>.*?</script>", "", val)
            if len(val) > MAX_FIELD_LENGTH:
                val = val[:MAX_FIELD_LENGTH]
            clean[k] = val
        elif isinstance(v, (int, float, bool)):
            clean[k] = v
        elif isinstance(v, dict):
            clean[k] = sanitize_metadata(v)
        elif isinstance(v, list):
            new_list = []
            for item in v:
                if isinstance(item, str):
                    item_val = re.sub(r"(?i)<script.*?>.*?</script>", "", item).strip()
                    if len(item_val) > MAX_FIELD_LENGTH:
                        item_val = item_val[:MAX_FIELD_LENGTH]
                    new_list.append(item_val)
                elif isinstance(item, dict):
                    new_list.append(sanitize_metadata(item))
                else:
                    new_list.append(item)
            clean[k] = new_list

    return clean


def validate_cid(cid: str) -> bool:
    if not isinstance(cid, str):
        return False
    cid = cid.strip()
    if cid.startswith("Qm") and 20 <= len(cid) <= 60 and re.match(r"^[A-Za-z0-9]+$", cid):
        return True
    if re.match(r"^[A-Za-z0-9_-]{20,100}$", cid):
        return True
    return False
