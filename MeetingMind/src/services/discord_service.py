import asyncio
import discord
import threading
import time


class DiscordNotifier:
    def __init__(self, token, channel_id):
        self.token = token
        self.channel_id = channel_id
        self.client = discord.Client(intents=discord.Intents.default())
        self.loop = None  # We'll assign the loop in run()

    async def send_dm(self, user_id, message):
        await self.client.wait_until_ready()
        try:
            # Fetch the user from the API if not in cache.
            user = await self.client.fetch_user(user_id)
            await user.send(message)
        except Exception as e:
            print(f"Failed to DM user {user_id}: {e}")

    def run(self):
        # Create a new event loop for this thread
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        # Start the Discord client on this loop
        self.loop.create_task(self.client.start(self.token))
        self.loop.run_forever()
