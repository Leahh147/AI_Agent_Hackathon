import asyncio
import discord
from discord.ui import View, Button


import discord
from discord.ui import View, Button


class YesNoView(View):
    def __init__(self):
        super().__init__(timeout=None)  # No timeout, buttons remain active
        self.listening = True

    @discord.ui.button(
        label="Yes", style=discord.ButtonStyle.green, custom_id="yes_button"
    )
    async def yes_button(
        self, interaction: discord.Interaction, button: Button
    ):
        await interaction.response.send_message(
            "✅ You're in! Have a productive discussion!", ephemeral=True
        )
        self.listening = False

    @discord.ui.button(
        label="No", style=discord.ButtonStyle.red, custom_id="no_button"
    )
    async def no_button(
        self, interaction: discord.Interaction, button: Button
    ):
        await interaction.response.send_message(
            "❌ Alright, we're continuing to listen for you.", ephemeral=True
        )
        self.listening = True

    async def send_question_message(self, user, message):
        """
        Sends a message with a question and Yes/No buttons. (listen_in)
        """
        view = YesNoView()
        question = f"❓ **Do you want to listen in?**\n\n{message}"
        await user.send(question, view=view)
    
    async def send_question_message_participate(self, user, message):
        """
        Sends a message with a question and Yes/No buttons. (participate)
        """
        view = YesNoView()
        question = f"❓ **Do you want to participate?**\n\n{message}"
        await user.send(question, view=view)


class DiscordNotifier:
    def __init__(self, token, channel_id):
        self.token = token
        self.channel_id = channel_id
        self.client = discord.Client(intents=discord.Intents.default())
        self.loop = None  # Will be set in run()

    async def send_dm(self, user_id, message):
        """
        Sends a DM to the user with Yes/No interactive buttons. (listen_in)
        """
        await self.client.wait_until_ready()
        try:
            user = await self.client.fetch_user(user_id)
            if user:
                view = YesNoView()  # Attach the interactive buttons
                await view.send_question_message(user, message)
                print(
                    f"[DiscordNotifier] Sent interactive DM to user {user_id}."
                )
            else:
                print(f"[DiscordNotifier] User with ID {user_id} not found!")
        except Exception as e:
            print(f"[DiscordNotifier] Failed to DM user {user_id}: {e}")
    
    async def send_dm_participate(self, user_id, message):
        """
        Sends a DM to the user with Yes/No interactive buttons. (participate)
        """
        await self.client.wait_until_ready()
        try:
            user = await self.client.fetch_user(user_id)
            if user:
                view = YesNoView()  # Attach the interactive buttons
                await view.send_question_message_participate(user, message)
                print(
                    f"[DiscordNotifier] Sent interactive DM to user {user_id}."
                )
            else:
                print(f"[DiscordNotifier] User with ID {user_id} not found!")
        except Exception as e:
            print(f"[DiscordNotifier] Failed to DM user {user_id}: {e}")
    
    async def send_simple_dm(self, user_id, message):
        """
        Sends a DM to the user without interactive buttons.
        """
        await self.client.wait_until_ready()
        try:
            user = await self.client.fetch_user(user_id)
            if user:
                await user.send(message)
                print(f"[DiscordNotifier] Sent simple DM to user {user_id}.")
            else:
                print(f"[DiscordNotifier] User with ID {user_id} not found!")
        except Exception as e:
            print(f"[DiscordNotifier] Failed to DM user {user_id}: {e}")
    
    async def send_message(self, message):
        """
        Sends a message to a channel (without interactive buttons).
        """
        await self.client.wait_until_ready()
        if self.channel_id:
            channel = self.client.get_channel(self.channel_id)
            if channel:
                await channel.send(message)
            else:
                print(
                    f"[DiscordNotifier] Channel with ID {self.channel_id} not found!"
                )
        else:
            print("[DiscordNotifier] No channel ID provided.")

    def run(self):
        """
        Starts the Discord bot in its own event loop.
        """
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        print("[DiscordNotifier] Starting Discord client...")
        self.loop.create_task(self.client.start(self.token))
        self.loop.run_forever()