import discord
from discord.ext import commands
import asyncio
from token_loader import load_tokens
from utils.http_client import HttpClientPool
import config

class NukeBot(commands.Bot):
    def __init__(self, token, http_pool, **kwargs):
        super().__init__(command_prefix=config.COMMAND_PREFIX, intents=discord.Intents.all(), **kwargs)
        self.own_token = token
        self.http_pool = http_pool

    async def on_ready(self):
        print(f"{self.user} is online")

    async def raw_delete(self, guild_id, channel_id):
        await self.http_pool.request(self.own_token, "DELETE", f"https://discord.com/api/v10/channels/{channel_id}")

    # Additional helper methods...
