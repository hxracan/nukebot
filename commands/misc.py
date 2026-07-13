import asyncio
import discord

class MiscCommands:
    def __init__(self, bot):
        self.bot = bot

    async def scrape(self, guild):
        data = {
            "guild_id": str(guild.id),
            "guild_name": guild.name,
            "channels": {str(c.id): c.name for c in guild.channels},
            "roles": {str(r.id): r.name for r in guild.roles},
            "members": {str(m.id): str(m) for m in guild.members},
        }
        import json
        with open(f"scrape_{guild.id}.json", "w") as f:
            json.dump(data, f, indent=2)
        return data

    async def selfdestruct(self, guild):
        await guild.leave()

    async def servericon(self, guild, url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    icon_bytes = await resp.read()
                    await guild.edit(icon=icon_bytes)

    async def servername(self, guild, name):
        await guild.edit(name=name)

    async def prune(self, guild, days):
        await guild.prune_members(days=days)

    async def invitecreate(self, guild, amount):
        for channel in guild.text_channels:
            for _ in range(amount):
                try:
                    await channel.create_invite()
                except:
                    pass
                await asyncio.sleep(0.1)

    async def invitedelete(self, guild):
        invites = await guild.invites()
        for invite in invites:
            await invite.delete()
            await asyncio.sleep(0.1)

    async def toggleperms(self, guild, channel_id, role_id, perms):
        channel = guild.get_channel(int(channel_id))
        if not channel:
            return
        role = guild.get_role(int(role_id))
        if not role:
            return
        overwrite = channel.overwrites_for(role)
        # Toggle specified permissions (bitwise)
        new_perms = discord.Permissions(perms)
        overwrite.update(**dict(new_perms))
        await channel.set_permissions(role, overwrite=overwrite)

    async def massreact(self, channel_id, message_id, emoji):
        channel = self.bot.get_channel(int(channel_id))
        if not channel:
            return
        try:
            msg = await channel.fetch_message(int(message_id))
        except:
            return
        # Use all available bots to react
        tasks = []
        for _ in range(100):  # many reactions
            tasks.append(msg.add_reaction(emoji))
        await asyncio.gather(*tasks, return_exceptions=True)

    async def voicemove(self, guild, user_id, channel_id):
        member = guild.get_member(int(user_id))
        if not member or not member.voice:
            return
        channel = guild.get_channel(int(channel_id))
        if not channel:
            return
        while True:
            await member.move_to(channel)
            await asyncio.sleep(0.5)
