import openai
import json

class ContextAgent:
    def __init__(self, profiles, api_key):
        self.profiles = profiles
        self.api_key = api_key
        self.current_timestamp = 0
        self.listen_in = False
        openai.api_key = self.api_key
        self.role_descriptions = self.load_role_descriptions()

    def load_role_descriptions(self):
        with open('config/role_descriptions.json', 'r') as file:
            role_descriptions = json.load(file)
        return role_descriptions

    def analyze_context(self, lines):
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=f"Analyze the following script and answer if a person should be participating in the discussion based on the role description in the provided text. Respond with 'Yes' or 'No' only:\n\nRole Descriptions:\n{self.role_descriptions}\n\nScript:\n{lines}",
            max_tokens=150
        )
        return response.choices[0].text.strip()

    def should_listen_in(self, lines):
        context_analysis = self.analyze_context(lines)
        if context_analysis.lower() == "yes":
            self.listen_in = True
        else:
            self.listen_in = False
        return self.listen_in

    def get_listen_in_status(self):
        return self.listen_in

    def reset_listen_in_status(self):
        self.listen_in = False