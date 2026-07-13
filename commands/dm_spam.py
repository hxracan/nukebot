import asyncio

class DmSpamCommands:
    def __init__(self, bot):
        self.bot = bot

    async def massdm(self, guild, message):
        members = [m for m in guild.members if m != guild.me and not m.bot]
        tasks = []
        for member in members:
            tasks.append(self.send_dm(member, message))
        await asyncio.gather(*tasks, return_exceptions=True)

    async def send_dm(self, member, message):
        try:
            await member.send(message)
        except:
            pass
