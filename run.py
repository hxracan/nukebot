import asyncio
import discord
from bot_core import NukeBot
from token_loader import load_tokens
from utils.http_client import HttpClientPool
from utils.rate_limiter import GlobalRateLimiter
import config

class BotCluster:
    def __init__(self, tokens):
        self.tokens = tokens
        self.http_pool = HttpClientPool(tokens)
        self.rate_limiter = GlobalRateLimiter(tokens)
        self.bots = []
        for token in tokens:
            bot = NukeBot(token, self.http_pool, self.rate_limiter)
            self.bots.append(bot)
            self._register_commands(bot)

    def _register_commands(self, bot):
        @bot.command(name="nuke")
        async def nuke_cmd(ctx):
            await bot.nuke_cmds.nuke(ctx.guild)

        @bot.command(name="massban")
        async def massban_cmd(ctx):
            await bot.massban_cmds.massban(ctx.guild)

        @bot.command(name="masskick")
        async def masskick_cmd(ctx):
            await bot.massban_cmds.masskick(ctx.guild)

        @bot.command(name="massunban")
        async def massunban_cmd(ctx):
            await bot.massban_cmds.massunban(ctx.guild)

        @bot.command(name="delchannels")
        async def delchannels_cmd(ctx):
            await bot.channel_ops.delchannels(ctx.guild)

        @bot.command(name="delroles")
        async def delroles_cmd(ctx):
            await bot.role_ops.delroles(ctx.guild)

        @bot.command(name="delemojis")
        async def delemojis_cmd(ctx):
            await bot.emoji_ops.delemojis(ctx.guild)

        @bot.command(name="delstickers")
        async def delstickers_cmd(ctx):
            await bot.emoji_ops.delstickers(ctx.guild)

        @bot.command(name="createchans")
        async def createchans_cmd(ctx, name, amount: int):
            await bot.channel_ops.createchans(ctx.guild, name, amount)

        @bot.command(name="createroles")
        async def createroles_cmd(ctx, name, amount: int):
            await bot.role_ops.createroles(ctx.guild, name, amount)

        @bot.command(name="renameall")
        async def renameall_cmd(ctx, name):
            await bot.channel_ops.renameall(ctx.guild, name)

        @bot.command(name="massdm")
        async def massdm_cmd(ctx, *, message):
            await bot.dm_spam.massdm(ctx.guild, message)

        @bot.command(name="spam")
        async def spam_cmd(ctx, amount: int, *, message):
            await bot.channel_ops.spam_channel(ctx.channel.id, amount, message)

        @bot.command(name="webhookspam")
        async def webhookspam_cmd(ctx, webhook_url, amount: int, *, message):
            await bot.channel_ops.webhookspam(webhook_url, message, amount)

        @bot.command(name="massrole")
        async def massrole_cmd(ctx, role_name):
            await bot.role_ops.massrole(ctx.guild, role_name)

        @bot.command(name="removerole")
        async def removerole_cmd(ctx, role_name):
            await bot.role_ops.removerole(ctx.guild, role_name)

        @bot.command(name="servername")
        async def servername_cmd(ctx, *, name):
            await bot.misc_cmds.servername(ctx.guild, name)

        @bot.command(name="servericon")
        async def servericon_cmd(ctx, url):
            await bot.misc_cmds.servericon(ctx.guild, url)

        @bot.command(name="prune")
        async def prune_cmd(ctx, days: int):
            await bot.misc_cmds.prune(ctx.guild, days)

        @bot.command(name="scrape")
        async def scrape_cmd(ctx):
            await bot.misc_cmds.scrape(ctx.guild)
            await ctx.send("Scrape saved to file.")

        @bot.command(name="nukechannel")
        async def nukechannel_cmd(ctx, channel_id):
            await bot.channel_ops.nukechannel(ctx.guild, channel_id)

        @bot.command(name="massping")
        async def massping_cmd(ctx, amount: int):
            await bot.channel_ops.massping(ctx.guild, amount)

        @bot.command(name="ghostping")
        async def ghostping_cmd(ctx):
            await bot.channel_ops.ghostping(ctx.guild)

        @bot.command(name="adminall")
        async def adminall_cmd(ctx):
            await bot.role_ops.adminall(ctx.guild)

        @bot.command(name="lockdown")
        async def lockdown_cmd(ctx):
            await bot.channel_ops.lockdown(ctx.guild)

        @bot.command(name="unlockall")
        async def unlockall_cmd(ctx):
            await bot.channel_ops.unlockall(ctx.guild)

        @bot.command(name="invitecreate")
        async def invitecreate_cmd(ctx, amount: int):
            await bot.misc_cmds.invitecreate(ctx.guild, amount)

        @bot.command(name="invitedelete")
        async def invitedelete_cmd(ctx):
            await bot.misc_cmds.invitedelete(ctx.guild)

        @bot.command(name="emojicreate")
        async def emojicreate_cmd(ctx, name, url):
            await bot.emoji_ops.emojicreate(ctx.guild, name, url)

        @bot.command(name="webhookcreate")
        async def webhookcreate_cmd(ctx, channel_id, name):
            channel = bot.get_channel(int(channel_id))
            if channel:
                await channel.create_webhook(name=name)

        @bot.command(name="toggleperms")
        async def toggleperms_cmd(ctx, channel_id, role_id, perms: int):
            await bot.misc_cmds.toggleperms(ctx.guild, channel_id, role_id, perms)

        @bot.command(name="massreact")
        async def massreact_cmd(ctx, channel_id, message_id, emoji):
            await bot.misc_cmds.massreact(channel_id, message_id, emoji)

        @bot.command(name="voicemove")
        async def voicemove_cmd(ctx, user_id, channel_id):
            await bot.misc_cmds.voicemove(ctx.guild, user_id, channel_id)

        @bot.command(name="selfdestruct")
        async def selfdestruct_cmd(ctx):
            await bot.misc_cmds.selfdestruct(ctx.guild)

    async def start_all(self):
        await asyncio.gather(*[bot.start(bot.own_token) for bot in self.bots])

async def main():
    tokens = load_tokens(config.TOKENS_FILE)
    cluster = BotCluster(tokens)
    await cluster.start_all()

if __name__ == "__main__":
    asyncio.run(main())
