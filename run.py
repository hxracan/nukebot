import asyncio
import aiohttp
from bot_core import NukeBot
from token_loader import load_tokens
from utils.http_client import HttpClientPool
from utils.rate_limiter import GlobalRateLimiter
import config

async def validate_token(token):
    """Quickly test a token against Discord API before login."""
    url = "https://discord.com/api/v10/users/@me"
    headers = {"Authorization": f"Bot {token}"}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                print(f"[✓] Token valid. Bot: {data['username']}#{data['discriminator']}")
                return True
            else:
                print(f"[✗] Token invalid (HTTP {resp.status}). Response: {await resp.text()}")
                return False

class BotCluster:
    def __init__(self, tokens):
        self.tokens = tokens
        self.http_pool = HttpClientPool(tokens)
        self.rate_limiter = GlobalRateLimiter(tokens)
        self.bots = []
        for token in tokens:
            # Show masked token for debugging
            mask = token[:6] + "..." + token[-6:]
            print(f"[i] Using token: {mask}")
            bot = NukeBot(token, self.http_pool, self.rate_limiter)
            self.bots.append(bot)
            self._register_commands(bot)

    def _register_commands(self, bot):
        # [ Keep all your existing command registrations here – same as before ]
        # I'll include a minimal set for brevity; you can paste the full list from earlier.
        @bot.command(name="nuke")
        async def nuke_cmd(ctx):
            await bot.nuke_cmds.nuke(ctx.guild)
        # ... (add all 35 commands)

    async def start_all(self):
        await asyncio.gather(*[bot.start(bot.own_token) for bot in self.bots])

async def main():
    try:
        tokens = load_tokens()
    except Exception as e:
        print(f"Fatal: {e}")
        return

    # Validate all tokens before starting the bot cluster
    results = await asyncio.gather(*[validate_token(t) for t in tokens])
    if not any(results):
        print("No valid tokens. Make sure you are using a Bot Token, not a Client Secret.")
        return

    cluster = BotCluster(tokens)
    await cluster.start_all()

if __name__ == "__main__":
    asyncio.run(main())
