import time
import threading


import time


class KeywordMonitor:
    def __init__(self, team_keywords, notify_callback):
        """
        Initializes the keyword monitoring system.

        :param team_keywords: Dictionary where keys are roles, and values are lists of keywords.
        :param notify_callback: Function to call when a keyword is detected.
        """
        self.team_keywords = {
            role: set(keywords) for role, keywords in team_keywords.items()
        }
        self.notify_callback = notify_callback
        self.active = True
        self.detected_roles = {role: "No" for role in team_keywords}

    def process_transcript_line(self, speaker, content, timestamp):
        """
        Processes a single line of transcript.

        :param speaker: Name of the speaker.
        :param content: Text spoken by the speaker.
        :param timestamp: Time at which the text was spoken.
        """
        if not self.active:
            return

        for role, keywords in self.team_keywords.items():
            for keyword in keywords:
                if keyword.lower() in content.lower():
                    print(
                        f"[ALERT] Keyword '{keyword}' detected at {timestamp} by {speaker}. Role: {role}"
                    )
                    self.notify_callback(speaker, content, timestamp, keyword)
                    self.detected_roles[role] = "Yes"  # Mark role as detected
                    break  # Stop checking further once a keyword is found

    def get_detection_status(self):
        """Returns the dictionary indicating which roles have been detected."""
        return self.detected_roles

    def pause_monitoring(self):
        """Pauses keyword monitoring."""
        self.active = False
        print("Keyword monitoring paused.")

    def resume_monitoring(self):
        """Resumes keyword monitoring."""
        self.active = True
        print("Keyword monitoring resumed.")


# Example notification function
def notify_user(speaker, content, timestamp, keyword):
    print(
        f"[NOTIFY] User notification: '{keyword}' mentioned by {speaker} at {timestamp}. Content: {content}"
    )


# Example usage
if __name__ == "__main__":
    team_keywords = {
        "Sponsorship": ["Edward", "Industry", "Sponsorship", "Sponsor"],
        "President": ["Rohan", "External relations", "Collaboration"],
        "Marketing and Communications Director": [
            "Leah",
            "Marketing strategy",
            "Event promotion",
            "Publicity",
        ],
        "Event Director": ["Oishi", "Diya", "Event planning"],
        "Treasurer": ["Connie", "Financial management", "Budgeting"],
        "Opportunities Director": ["Kriti", "Welfare"],
        "Vice President": ["Adi", "Internal management"],
        "Technology Director": ["Harsh", "Technology support"],
    }

    monitor = KeywordMonitor(team_keywords, notify_user)

    # Simulated transcript processing
    transcript_data = [
        (
            "Edward",
            "We need to review the sponsorship proposal soon.",
            "10:05 AM",
        ),
        ("Bob", "This is an urgent matter for the event team.", "10:06 AM"),
        (
            "Leah",
            "Let's discuss marketing strategy for the campaign.",
            "10:07 AM",
        ),
    ]

    for entry in transcript_data:
        speaker, content, timestamp = entry
        monitor.process_transcript_line(speaker, content, timestamp)
        time.sleep(1)  # Simulating real-time progression

    # Output detection status
    detection_status = monitor.get_detection_status()
    print(detection_status)
