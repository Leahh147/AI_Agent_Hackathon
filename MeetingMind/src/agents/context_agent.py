import json
from openai import OpenAI
import asyncio

class ContextAgent:
    def __init__(self, profiles, api_key):
        self.profiles = profiles
        self.api_key = api_key
        self.current_timestamp = 0
        self.listen_in = False
        self.client = OpenAI(api_key=self.api_key)
        self.role_descriptions = self.load_role_descriptions()

    def load_role_descriptions(self):
        with open('config/role_descriptions.json', 'r') as file:
            role_descriptions = json.load(file)
        return role_descriptions

    async def analyze_context(self, lines):
        try:
            completion = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {
                        "role": "user",
                        "content": f"Analyze the following script and answer if a person should be participating in the discussion based on the role description in the provided text. Respond with 'Yes' or 'No' only:\n\nRole Descriptions:\n{self.role_descriptions}\n\nScript:\n{lines}"
                    }
                ]
            )
            return completion.choices[0].message['content'].strip()
        except openai.APIConnectionError as e:
            print("The server could not be reached")
            print(e.__cause__)  # an underlying Exception, likely raised within httpx.
        except openai.RateLimitError as e:
            print("A 429 status code was received; we should back off a bit.")
        except openai.APIStatusError as e:
            print("Another non-200-range status code was received")
            print(e.status_code)
            print(e.response)
        return "no"

    async def should_listen_in(self, lines):
        context_analysis = await self.analyze_context(lines)
        if context_analysis.lower() == "yes":
            self.listen_in = True
        else:
            self.listen_in = False
        return self.listen_in

    def get_listen_in_status(self):
        return self.listen_in

    def reset_listen_in_status(self):
        self.listen_in = False