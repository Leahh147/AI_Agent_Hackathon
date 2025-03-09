import json
from openai import OpenAI
import asyncio
import os

class ContextAgent:
    def __init__(self, profile):
        self.profile = profile
        api_key = os.getenv("API_KEY")
        self.api_key = api_key
        self.current_timestamp = 0
        self.listen_in = False
        self.client = OpenAI(api_key=self.api_key)
        self.role_descriptions = self.load_role_descriptions()

    def load_role_descriptions(self):
        # Get the project root directory
        self.project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        # Set paths for files
        self.role_description_path = os.path.join(
            self.project_root, "config", "role_description.json"
        )
        with open(self.role_description_path, 'r') as file:
            role_descriptions = json.load(file)
        return role_descriptions

    async def analyze_context(self, lines): # if lines is empty, the agent should be able to give a response of no
        # try:
        response = await asyncio.to_thread(
            self.client.chat.completions.create,
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a meeting assistant to notify meeting attendee to pay attention when the current part involves or will involve them."},
                {
                    "role": "user",
                    "content": f"Analyze the following script and answer if {self.profile} should be participating in the discussion based on the role description in the provided text. Respond with 'Yes' or 'No' only:\n\nRole Descriptions:\n{self.role_descriptions}\n\nScript:\n{lines}"
                }
            ],
            temperature=0.7,
            max_tokens=300
        )

        content = response.choices[0].message.content.strip()
        return content
        # except OpenAI.APIConnectionError as e:
        #     print("The server could not be reached")
        #     print(e.__cause__)  # an underlying Exception, likely raised within httpx.
        # except OpenAI.RateLimitError as e:
        #     print("A 429 status code was received; we should back off a bit.")
        # except OpenAI.APIStatusError as e:
        #     print("Another non-200-range status code was received")
        #     print(e.status_code)
        #     print(e.response)
        # return "no"

    async def should_listen_in(self, lines=None):
        # lines = self.get_minutes_within_current_topic()
        context_analysis = await self.analyze_context(lines)
        if context_analysis.lower() == "yes":
            self.listen_in = True
        else:
            self.listen_in = False
        return self.listen_in

    # def get_listen_in_status(self):
    #     return self.listen_in

    # def reset_listen_in_status(self):
    #     self.listen_in = False

    # def get_minutes_within_current_topic(self):
    #     if not self.minutes_agent.get_current_topic():
    #         return ""
    #     return self.minutes_agent.get_current_topic()