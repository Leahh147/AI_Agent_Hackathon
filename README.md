# MeetingMind

MeetingMind is an AI-powered meeting assistant that participates in meetings on your behalf, keeps you in the loop, and notifies you when your attention is required. It uses OpenAI's GPT-3 to analyze meeting transcripts, generate minutes, and determine if you should listen in based on role descriptions.

## Features

- **Transcript Processing**: Parses and simulates meeting transcripts.
- **Minutes Generation**: Uses GPT-3 to generate relevant meeting minutes.
- **Context Monitoring**: Analyzes the context of the meeting to decide if you should listen in.
- **Keyword Monitoring**: Checks for potential keyword triggers to call you into the meeting.
- **Notification System**: Notifies you via Discord when your attention is required.
- **Role-Based Participation**: Determines if you should participate based on your role description.

## Clone the Repo
```bash
git clone https://github.com/yourusername/MeetingMind.git
cd MeetingMind
```

## Install the Dependencies
```bash
pip install -r requirements.txt
```

## Set up the Environment Variables
In your .env file
```bash
OPENAI_API_KEY=your_openai_api_key
DISCORD_WEBHOOK_URL=your_discord_webhook_url
```


## Usage
1. Configure your settings in config/default_config.json and config/user_profiles.json.
2. Run the main script:
```bash
python src/main.py
```

## Contributing
Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.
