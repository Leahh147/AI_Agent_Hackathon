import os
import json
import asyncio
import openai
from dotenv import load_dotenv
from typing import List, Dict, Any

# Load the .env file
load_dotenv()

# Get the OpenAI API key from the environment variables
openai.api_key = os.getenv("API_KEY")

class ActionAgent:
    def __init__(self, name="ActionAgent"):
        self.name = name
        self.meeting_ended = False
        
        # Get the project root directory
        self.project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        # Set paths for files
        self.minutes_input_path = os.path.join(self.project_root, "final_minutes.json")
        self.todos_output_path = os.path.join(self.project_root, "todos.json")
        self.emails_output_path = os.path.join(self.project_root, "emails.json")

    async def meeting_end_handler(self):
        """Called when the meeting ends"""
        self.meeting_ended = True
        print(f"{self.name}: Meeting has ended, generating action items and emails...")
        
        # Read the final minutes
        with open(self.minutes_input_path, 'r') as f:
            minutes = json.load(f)
        
        # Process the minutes with two LLMs in parallel
        todos_task = asyncio.create_task(self.generate_todo_lists(minutes))
        emails_task = asyncio.create_task(self.generate_email_drafts(minutes))
        
        # Wait for both tasks to complete
        todos, emails = await asyncio.gather(todos_task, emails_task)
        
        # Save outputs
        with open(self.todos_output_path, 'w') as f:
            json.dump(todos, f, indent=2)
            
        with open(self.emails_output_path, 'w') as f:
            json.dump(emails, f, indent=2)
        
        print(f"{self.name}: Action items and emails generated successfully")
        return todos, emails

    async def generate_todo_lists(self, minutes):
        """Generate formatted to-do lists for each attendee"""
        prompt = """
        You are a helpful assistant that creates action items from meeting minutes.
        
        Given the meeting minutes, create a to-do list for each relevant attendee.
        
        INSTRUCTIONS:
        1. Analyze the meeting minutes to identify action items for each person
        2. Format each to-do item with an appropriate emoji at the beginning of the line
        3. Separate items with newlines (\\n)
        4. ONLY include people who actually have to-do items
        5. Make the to-do items clear, concise, and actionable
        6. Include relevant details like deadlines, amounts, or specific tasks
        
        EXAMPLE OUTPUT FORMAT:
        {
          "todo_lists": [
            {
              "name": "Person's Name",
              "role": "Their Role",
              "formatted_todos": "📋 First todo item with details\\n✅ Second todo item\\n📞 Third todo item"
            },
            {
              "name": "Another Person",
              "role": "Their Role",
              "formatted_todos": "💰 Budget-related todo item\\n📊 Follow up task with details"
            }
          ]
        }
        """
        
        prompt += json.dumps(minutes, indent=2)
        
        response = await asyncio.to_thread(
            openai.chat.completions.create,
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an AI assistant that creates actionable to-do lists from meeting minutes."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        
        try:
            return json.loads(response.choices[0].message.content)
        except json.JSONDecodeError:
            return {"error": "Failed to parse response", "raw": response.choices[0].message.content}

    async def generate_email_drafts(self, minutes):
        """Generate formatted email drafts for each attendee who needs to send emails"""
        prompt = """
        You are a helpful assistant that drafts emails based on meeting minutes.
        
        Given the meeting minutes, create email drafts for each relevant attendee who needs to follow up.
        
        INSTRUCTIONS:
        1. Analyze the minutes to identify situations where an email needs to be sent
        2. Create professional and concise email drafts that are ready to send
        3. Format with recipient, subject, and content
        4. Use Markdown for Discord: bold subject and recipient with **asterisks**
        5. ONLY include people who actually need to send emails
        6. If nobody needs to send emails, return an empty list
        
        EXAMPLE OUTPUT FORMAT:
        {
          "email_drafts": [
            {
              "name": "Person's Name",
              "formatted_email": "**To:** Recipient Name\\n**Subject:** Email Subject\\n\\nDear Recipient,\\n\\nEmail content here with proper formatting.\\n\\nBest regards,\\nPerson's Name"
            },
            {
              "name": "Another Person",
              "formatted_email": "**To:** Different Recipient\\n**Subject:** Another Subject\\n\\nHello,\\n\\nAnother email content here.\\n\\nRegards,\\nAnother Person"
            }
          ]
        }
        """
        
        prompt += json.dumps(minutes, indent=2)
        
        response = await asyncio.to_thread(
            openai.chat.completions.create,
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an AI assistant that drafts follow-up emails based on meeting minutes."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        
        try:
            return json.loads(response.choices[0].message.content)
        except json.JSONDecodeError:
            return {"error": "Failed to parse response", "raw": response.choices[0].message.content}