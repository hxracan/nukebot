import asyncio

class MassBanCommands:
    def __init__(self, bot):
        self.bot = bot

    async def massban(self, guild):
        await self.bot.nuke_cmds.ban_all_members(guild)

    async def masskick(self, guild):
        members = [m for m in guild.members if m.id != guild.me.id and guild.me.top_role > m.top_role]
        tasks = []
        for member in members:
            tasks.append(self.bot.raw_delete(guild.id, f"members/{member.id}", ""))  # DELETE /guilds/{guild.id}/members/{member.id}
        await asyncio.gather(*tasks, return_exceptions=True)

    async def massunban(self, guild):
        bans = await guild.bans()
        tasks = []
        for ban_entry in bans:
            user = ban_entry.user
            tasks.append(self.bot.raw_delete(guild.id, f"bans/{user.id}", ""))  # DELETE /guilds/{guild.id}/bans/{user.id}
        await asyncio.gather(*tasks, return_exceptions=True)
