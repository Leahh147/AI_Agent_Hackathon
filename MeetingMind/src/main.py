from utils.helpers import DiscordMonitor

# Discord Bot Credentials
TOKEN = (
    "MTM0Nzk5NTI2OTgzNjMwODUwMQ.Gc38GI.zRljhJuDTRfSi-5aAWjvttgVHwuDfmqXY_kLCo"
)
CHANNEL_ID = 1347996655013597227  # Replace with your actual Discord Channel ID
USER_ID = {
    "Marketing and Communications Director": 1346615174169231425,
    "Event planning": 401599932932292608,
    "Treasurer": 1160641318347882506,
    "Sponsor": 731882462313185350,
}

# Define Keywords
team_keywords = {
    "Sponsorship": ["Edward", "Industry", "Sponsorship", "Sponsor"],
    "President": ["Rohan", "External relations", "Collaboration"],
    "Marketing and Communications Director": [
        "Leah",
        "Marketing strategy",
        "Publicity",
    ],
    "Event Director": ["Oishi", "Diya", "Event planning"],
    "Treasurer": ["Connie", "Financial management", "Budgeting"],
    "Opportunities Director": ["Kriti", "Welfare"],
    "Vice President": ["Adi", "Internal management"],
    "Technology Director": ["Harsh", "Technology support"],
}

transcript_data = [
    ("Edward", "We need to review the sponsorship proposal soon.", "10:05 AM"),
    (
        "Bob",
        "This is an urgent matter for the event planning team.",
        "10:06 AM",
    ),
    ("Leah", "Let's discuss marketing strategy for the campaign.", "10:07 AM"),
]

# Initialize and run the DiscordMonitor
monitor = DiscordMonitor(TOKEN, CHANNEL_ID, USER_ID, team_keywords)
monitor.run_monitoring(transcript_data)
