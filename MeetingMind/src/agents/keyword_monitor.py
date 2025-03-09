import asyncio


class KeywordMonitor:
    def __init__(self, team_keywords, notifier):
        """
        :param team_keywords: Dictionary of roles and their associated keywords.
        :param notifier: Instance of DiscordNotifier to send alerts.
        """
        self.team_keywords = {
            role: set(keywords) for role, keywords in team_keywords.items()
        }
        self.notifier = notifier  # Store the DiscordNotifier instance
        self.active = True
        self.detected_roles = {role: "No" for role in team_keywords}
        self.user_ids = {
            "Marketing and Communications Director": 1346615174169231425,
            "Event Director": 401599932932292608,
            "Treasurer": 1160641318347882506,
            "Sponsorship": 731882462313185350,
        }

    def process_transcript_line(self, speaker, content, timestamp):
        """
        Detects keywords in a transcript and notifies via Discord.

        :param speaker: Who spoke the content.
        :param content: What was said.
        :param timestamp: When it was spoken.
        """
        if not self.active:
            return

        detected = []
        for role, keywords in self.team_keywords.items():
            for keyword in keywords:
                if keyword.lower() in content.lower():
                    alert_msg = f"[ALERT] '{keyword}' detected at {timestamp} by {speaker}. Role: {role}"
                    print(alert_msg)

                    # Store detected role
                    self.detected_roles[role] = "Yes"
                    detected.append(role)
                    break  # Stop checking after finding a match

        # If any roles were detected, trigger Discord notification
        if detected:
            self.notify_discord(detected, speaker, timestamp, content)

    def notify_discord(
        self, detected_roles, speaker, timestamp, message_content
    ):
        """
        Sends a DM to each user corresponding to the detected role(s).

        :param detected_roles: List of roles detected.
        :param speaker: Who spoke the content.
        :param timestamp: When it was spoken.
        :param message_content: The full message content that triggered the detection.
        """
        # Format the message to send
        discord_message = (
            f"🚨 **Keyword Alert!** 🚨\n"
            f"🔹 **Speaker:** {speaker}\n"
            f"🔹 **Time:** {timestamp}\n"
            f'📝 **Message:** "{message_content}"'
        )

        # Iterate over the detected roles and send a DM if the role is in the mapping.
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

    def get_detection_status(self):
        """Returns which roles have been detected."""
        return self.detected_roles
