import aiohttp
import asyncio

class EmojiStickerOps:
    def __init__(self, bot):
        self.bot = bot

    async def delemojis(self, guild):
        await self.bot.nuke_cmds.delete_all_emojis(guild)

    async def delstickers(self, guild):
        await self.bot.nuke_cmds.delete_all_stickers(guild)

    async def emojicreate(self, guild, name, image_url):
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as resp:
                if resp.status == 200:
                    image_data = await resp.read()
                    await guild.create_custom_emoji(name=name, image=image_data)
