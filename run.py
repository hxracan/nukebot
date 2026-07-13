import asyncio
from bot_core import NukeBot
from token_loader import load_tokens
from utils.http_client import HttpClientPool
import config

async def main():
    tokens = load_tokens(config.TOKENS_FILE)
    http_pool = HttpClientPool(tokens)
    bots = []
    for token in tokens:
        bot = NukeBot(token, http_pool)
        bots.append(bot)
    await asyncio.gather(*[bot.start(token) for bot in bots])

if __name__ == "__main__":
    asyncio.run(main())
