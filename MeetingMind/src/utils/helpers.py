import threading
import time
from agents.keyword_monitor import KeywordMonitor

# Adjust path as necessary
from services.discord_service import DiscordNotifierv


class DiscordMonitor:
    """
    A helper class to monitor messages, detect relevant keywords,
    and send notifications to a Discord channel.
    """

    def __init__(self, token, channel_id, user_ids, team_keywords):
        """
        Initializes the DiscordMonitor.

        :param token: Discord bot token.
        :param channel_id: Discord channel ID where notifications will be sent.
        :param user_ids: Dictionary mapping team roles to user IDs.
        :param team_keywords: Dictionary mapping team names to relevant keywords.
        """
        self.token = token
        self.channel_id = channel_id
        self.user_ids = user_ids
        self.team_keywords = team_keywords
        self.notifier = DiscordNotifier(token, channel_id)
        self.monitor = KeywordMonitor(team_keywords, self.notifier)

    def start_notifier(self):
        """
        Runs the Discord notifier in a separate thread.
        """
        self.notifier.run()

    def run_monitoring(self, transcript_data):
        """
        Starts the Discord client and processes transcript data.

        :param transcript_data: List of tuples containing (speaker, content, timestamp).
        """
        # Start the notifier in a background thread
        notifier_thread = threading.Thread(
            target=self.start_notifier, daemon=True
        )
        notifier_thread.start()

        # Allow some time for the Discord client to connect
        time.sleep(10)

        # Process transcript messages
        for speaker, content, timestamp in transcript_data:
            self.monitor.process_transcript_line(speaker, content, timestamp)
            time.sleep(1)  # Simulate real-time processing
