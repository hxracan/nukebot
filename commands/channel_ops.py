import asyncio

class ChannelOps:
    def __init__(self, bot):
        self.bot = bot

    async def delchannels(self, guild):
        await self.bot.nuke_cmds.delete_all_channels(guild)

    async def createchans(self, guild, name, amount):
        await self.bot.nuke_cmds.create_flood(guild, name, amount)

    async def renameall(self, guild, name):
        tasks = []
        for channel in guild.channels:
            tasks.append(self.bot.raw_patch(guild.id, "channels", channel.id, {"name": name}))
        await asyncio.gather(*tasks, return_exceptions=True)

    async def nukechannel(self, guild, channel_id):
        await self.bot.raw_delete(guild.id, "channels", channel_id)
        await asyncio.sleep(0.5)
        payload = {"name": "nuked-channel", "type": 0}
        resp = await self.bot.raw_post(guild.id, "channels", json_data=payload)
        if resp:
            new_channel = await resp.json()
            await self.spam_channel(new_channel['id'], 100, "**DESTROYED**")

    async def spam_channel(self, channel_id, amount, message):
        for _ in range(amount):
            payload = {"content": message}
            await self.bot.http_pool.request(self.bot.own_token, "POST", f"/channels/{channel_id}/messages", json=payload)
            await asyncio.sleep(0.01)

    async def webhookspam(self, webhook_url, message, amount):
        for _ in range(amount):
            payload = {"content": message}
            await self.bot.http_pool.request(self.bot.own_token, "POST", webhook_url, json=payload)
            await asyncio.sleep(0.01)

    async def lockdown(self, guild):
        everyone = guild.default_role
        overwrite = discord.PermissionOverwrite(send_messages=False)
        tasks = []
        for channel in guild.text_channels:
            tasks.append(channel.set_permissions(everyone, overwrite=overwrite))
        await asyncio.gather(*tasks, return_exceptions=True)

    async def unlockall(self, guild):
        everyone = guild.default_role
        overwrite = discord.PermissionOverwrite(send_messages=True)
        tasks = []
        for channel in guild.text_channels:
            tasks.append(channel.set_permissions(everyone, overwrite=overwrite))
        await asyncio.gather(*tasks, return_exceptions=True)

    async def massping(self, guild, amount):
        role = await guild.create_role(name="PINGED", mentionable=True)
        for member in guild.members:
            if member != guild.me:
                try:
                    await member.add_roles(role)
                except:
                    pass
        for channel in guild.text_channels[:5]:
            for _ in range(amount):
                await channel.send(f"{role.mention} EVERYONE PING")
                await asyncio.sleep(0.1)

    async def ghostping(self, guild):
        for channel in guild.text_channels:
            msg = await channel.send("@everyone")
            await msg.delete()
            await asyncio.sleep(0.5)
