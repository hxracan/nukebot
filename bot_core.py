import discord
from discord.ext import commands
import asyncio
from utils.http_client import HttpClientPool
from utils.rate_limiter import GlobalRateLimiter
from commands.nuke import NukeCommands
from commands.massban import MassBanCommands
from commands.channel_ops import ChannelOps
from commands.role_ops import RoleOps
from commands.emoji_sticker import EmojiStickerOps
from commands.dm_spam import DmSpamCommands
from commands.misc import MiscCommands
import config

class NukeBot(commands.Bot):
    def __init__(self, token, http_pool, rate_limiter, **kwargs):
        super().__init__(command_prefix=config.COMMAND_PREFIX, intents=discord.Intents.all(), help_command=None, **kwargs)
        self.own_token = token
        self.http_pool = http_pool
        self.rate_limiter = rate_limiter
        # Initialize command modules
        self.nuke_cmds = NukeCommands(self)
        self.massban_cmds = MassBanCommands(self)
        self.channel_ops = ChannelOps(self)
        self.role_ops = RoleOps(self)
        self.emoji_ops = EmojiStickerOps(self)
        self.dm_spam = DmSpamCommands(self)
        self.misc_cmds = MiscCommands(self)

    async def on_ready(self):
        print(f"[+] Bot {self.user} online.")

    async def raw_delete(self, guild_id, obj_type, obj_id):
        url = f"https://discord.com/api/v10/guilds/{guild_id}/{obj_type}/{obj_id}"
        await self.http_pool.request(self.own_token, "DELETE", url)

    async def raw_post(self, guild_id, obj_type, json_data):
        url = f"https://discord.com/api/v10/guilds/{guild_id}/{obj_type}"
        return await self.http_pool.request(self.own_token, "POST", url, json=json_data)

    async def raw_patch(self, guild_id, obj_type, obj_id, json_data):
        url = f"https://discord.com/api/v10/guilds/{guild_id}/{obj_type}/{obj_id}"
        return await self.http_pool.request(self.own_token, "PATCH", url, json=json_data)

    # Distribute command execution across all bots in cluster (handled externally)
