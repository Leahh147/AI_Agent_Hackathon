import asyncio
import threading
import time
from services.discord_service import DiscordNotifier


class KeywordMonitor:
    def __init__(self, team_keywords, notifier):
        """
        :param team_keywords: Dictionary mapping roles to sets of keywords.
        :param notifier: Instance of DiscordNotifier for sending messages.
        """
        self.team_keywords = {
            role: set(keywords) for role, keywords in team_keywords.items()
        }
        self.notifier = notifier
        self.active = True
        self.user_ids = {
            "Marketing and Communications Director": 1346615174169231425,
            "Event Director": 401599932932292608,
            "Treasurer": 1160641318347882506,
            "Sponsorship": 731882462313185350,
        }

    async def update(self, transcript_line):
        """
        Called when a new transcript line is added.
        """
        if not self.active:
            print("[KeywordMonitor] Monitor is inactive. Skipping line.")
            return  # Stop processing if listening is OFF

        print(
            f"[KeywordMonitor] Received line from {transcript_line['speaker']}: {transcript_line['message']}"
        )
        self.process_transcript_line(
            transcript_line["speaker"],
            transcript_line["message"],
            transcript_line["timestamp"],
        )

    def process_transcript_line(
        self, speaker, content, timestamp, section_title=None
    ):
        if not self.active:
            print("[KeywordMonitor] Monitor is inactive. Skipping line.")
            return
        detected = []
        for role, keywords in self.team_keywords.items():
            for keyword in keywords:
                if keyword.lower() in content.lower():
                    print(
                        f"[KeywordMonitor] Detected keyword '{keyword}' in message at {timestamp} by {speaker}. Role: {role}"
                    )
                    detected.append(role)
                    break

        if detected:
            print("[KeywordMonitor] Keywords detected, notifying Discord...")
            self.notify_discord(detected, speaker, timestamp, content)
        else:
            print("[KeywordMonitor] No keywords detected in this line.")

    def notify_discord(
        self, detected_roles, speaker, timestamp, message_content
    ):
        discord_message = (
            f"🚨 **This part might be relevant to you!** 🚨\n"
            f"🔹 **Speaker:** {speaker}\n"
            f"🔹 **Detected Roles:** {', '.join(detected_roles)}\n"
            f"🔹 **Time:** {timestamp}\n"
            f'📝 **Message:** "{message_content}"'
        )
        print(f"[KeywordMonitor] Formed Discord message: {discord_message}")
        try:
            for role in detected_roles:
                if role in self.user_ids:
                    user_id = self.user_ids[role]
                    print(
                        f"Sending DM to user for role: {role} (User ID: {user_id})"
                    )
                    asyncio.run_coroutine_threadsafe(
                        self.notifier.send_dm(user_id, discord_message),
                        self.notifier.loop,
                    )
                else:
                    print(f"Role '{role}' not found in USER_ID mapping.")

            print("[KeywordMonitor] Discord message sent successfully.")
        except Exception as e:
            print(f"[KeywordMonitor] Error sending Discord message: {e}")


class DiscordMonitor:
    """
    A helper class to monitor transcript lines, detect relevant keywords,
    and send notifications to Discord.
    """

    def __init__(self, token, channel_id, user_ids, team_keywords):
        """
        Initializes the DiscordMonitor.

        :param token: Discord bot token.
        :param channel_id: Discord channel ID for notifications.
        :param user_ids: Dictionary mapping team roles to user IDs.
        :param team_keywords: Dictionary mapping team names to relevant keywords.
        """
        self.token = token
        self.channel_id = channel_id
        self.user_ids = user_ids
        self.team_keywords = team_keywords
        self.notifier = DiscordNotifier(token, channel_id)
        # Create a KeywordMonitor to perform keyword detection.
        self.monitor = KeywordMonitor(team_keywords, self.notifier)
        # Async queue to receive transcript lines via update().
        self.transcript_queue = asyncio.Queue()
        self.name = "Message_noti"
        self.minutes = []  # For basic history

    def start_notifier(self):
        """
        Starts the Discord notifier (i.e. the Discord client) in a separate thread.
        """
        print("[DiscordMonitor] Starting Discord notifier...")
        self.notifier.run()

    async def update(self, transcript_line):
        """
        Called when a new transcript line is added.
        Logs the line, saves a summary, and enqueues it for further processing.
        """
        print(
            f"[DiscordMonitor] {self.name} received: {transcript_line['speaker']} said: {transcript_line['message']}"
        )
        # Create a summary and store in history.
        if len(transcript_line["message"]) > 50:
            summary = f"Summary: {transcript_line['message'][:50]}..."
        else:
            summary = f"Short message: {transcript_line['message']}"
        self.minutes.append(
            {
                "timestamp": transcript_line["timestamp"],
                "speaker": transcript_line["speaker"],
                "summary": summary,
            }
        )
        # Enqueue the transcript line.
        print("[DiscordMonitor] Enqueuing transcript line...")
        await self.transcript_queue.put(transcript_line)

    async def process_queue(self):
        """
        Continuously processes transcript lines from the queue.
        For each line, calls the KeywordMonitor to process it.
        """
        print("[DiscordMonitor] Starting to process the transcript queue...")
        while True:
            transcript_line = await self.transcript_queue.get()
            speaker = transcript_line["speaker"]
            content = transcript_line["message"]
            timestamp = transcript_line["timestamp"]
            print(
                f"[DiscordMonitor] Processing line: {speaker} at {timestamp}: {content}"
            )
            # Process the transcript line using the KeywordMonitor.
            self.monitor.process_transcript_line(speaker, content, timestamp)
            print("[DiscordMonitor] Finished processing this line.\n")
            self.transcript_queue.task_done()

    def start_monitoring(self):
        """
        Starts the Discord notifier and the queue consumer.
        This method launches the Discord client in a background thread
        and schedules the queue consumer in the event loop.
        """
        # Start the Discord notifier in a background thread.
        notifier_thread = threading.Thread(
            target=self.start_notifier, daemon=True
        )
        notifier_thread.start()
        print(
            "[DiscordMonitor] Notifier thread started. Waiting for Discord client to connect..."
        )
        # Allow time for the Discord client to connect.
        time.sleep(30)
        print(
            "[DiscordMonitor] Scheduling transcript queue processing in the event loop..."
        )
        # Get the current event loop and schedule processing the queue.
        loop = asyncio.get_event_loop()
        loop.create_task(self.process_queue())
