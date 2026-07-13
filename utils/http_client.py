import aiohttp
import asyncio

class HttpClientPool:
    def __init__(self, tokens):
        self.sessions = {}
        for token in tokens:
            connector = aiohttp.TCPConnector(limit=0, force_close=False)
            self.sessions[token] = aiohttp.ClientSession(
                connector=connector,
                headers={
                    "Authorization": f"Bot {token}",
                    "Content-Type": "application/json"
                }
            )

    async def close(self):
        for session in self.sessions.values():
            await session.close()

    async def request(self, token, method, url, **kwargs):
        session = self.sessions[token]
        for attempt in range(5):
            async with session.request(method, url, **kwargs) as resp:
                if resp.status == 429:
                    retry_after = float(resp.headers.get("Retry-After", 0.5))
                    await asyncio.sleep(retry_after)
                    continue
                return resp
        return None
