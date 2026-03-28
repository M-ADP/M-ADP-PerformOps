from typing import Any, Optional

import aiohttp

from src.core.requester import Requester


class HttpRequester(Requester):
    async def get(self, url: str, **kwargs) -> Any:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, **kwargs) as response:
                response.raise_for_status()
                return await response.json()

    async def post(self, url: str, body: Any = None, **kwargs) -> Any:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=body, **kwargs) as response:
                response.raise_for_status()
                return await response.json()

    async def patch(self, url: str, body: Any = None, **kwargs) -> Any:
        async with aiohttp.ClientSession() as session:
            async with session.patch(url, json=body, **kwargs) as response:
                response.raise_for_status()
                return await response.json()

    async def put(self, url: str, body: Any = None, **kwargs) -> Any:
        async with aiohttp.ClientSession() as session:
            async with session.put(url, json=body, **kwargs) as response:
                response.raise_for_status()
                return await response.json()

    async def delete(self, url: str, **kwargs) -> Any:
        async with aiohttp.ClientSession() as session:
            async with session.delete(url, **kwargs) as response:
                response.raise_for_status()
                return await response.json()
