import asyncio
import discord


class DiscordNotifier:
    def __init__(self, token, channel_id):
        self.token = token
        self.channel_id = channel_id
        self.client = discord.Client(intents=discord.Intents.default())
        self.loop = None  # Will be set in run()

    async def send_dm(self, user_id, message):
        await self.client.wait_until_ready()
        try:
            user = await self.client.fetch_user(user_id)
            await user.send(message)
        except Exception as e:
            print(f"Failed to DM user {user_id}: {e}")

    def run(self):
        # Create a new event loop in this thread and store it
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        print("[DiscordNotifier] Starting Discord client...")
        self.loop.create_task(self.client.start(self.token))
        self.loop.run_forever()
