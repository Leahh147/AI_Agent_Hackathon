import os
import json
import asyncio
import openai
import threading
from dotenv import load_dotenv
from typing import List, Dict, Any
from src.services.discord_service import DiscordNotifier

# Load the .env file
load_dotenv()

# Get the OpenAI API key from the environment variables
openai.api_key = os.getenv("API_KEY")

class ActionAgent:
    def __init__(self, name="ActionAgent", discord_token=None, discord_channel_id=None):
        self.name = name
        self.meeting_ended = False
        
        # Get the project root directory
        self.project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        # Set paths for files
        self.minutes_input_path = os.path.join(self.project_root, "final_minutes.json")
        self.todos_output_path = os.path.join(self.project_root, "todos.json")
        self.emails_output_path = os.path.join(self.project_root, "emails.json")
        
        # Initialize Discord notifier if token is provided
        self.discord_token = discord_token
        self.discord_channel_id = discord_channel_id
        self.discord_notifier = None
        
        # Dictionary mapping people to their Discord user IDs
        self.user_id_mapping = {
            "Adi": 1346615174169231425,
            "Oishi": 401599932932292608,
            "Harsh": 401599932932292608,
            "Diya": 1160641318347882506,
            "Rohan": 731882462313185350,
            # Add more mappings as needed
        }
        
        if discord_token:
            self.discord_notifier = DiscordNotifier(discord_token, discord_channel_id)
            # Start the Discord notifier in a separate thread
            self._start_discord_notifier()
    
    def _start_discord_notifier(self):
        """Start the Discord notifier in a separate thread."""
        if self.discord_notifier:
            notifier_thread = threading.Thread(target=self.discord_notifier.run, daemon=True)
            notifier_thread.start()
            print("[ActionAgent] Discord notifier thread started.")

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
        
        # Print outputs to console
        self._print_todo_lists(todos)
        self._print_email_drafts(emails)

        # Send Discord notifications with todo items and email drafts
        if self.discord_notifier:
            self.send_discord_notifications(todos, emails)
        
        return todos, emails
        
    def send_discord_notifications(self, todos, emails):
        """Send todos and email drafts to respective users via Discord."""
        if not self.discord_notifier:
            print("[ActionAgent] Discord notifier not initialized, skipping notifications.")
            return
            
        print("[ActionAgent] Sending todo items and email drafts to users via Discord...")
        
        # Process and send todo items
        if "todo_lists" in todos:
            for todo_item in todos["todo_lists"]:
                person_name = todo_item.get("name")
                formatted_todos = todo_item.get("formatted_todos")
                role = todo_item.get("role", "")
                
                if person_name in self.user_id_mapping and formatted_todos:
                    user_id = self.user_id_mapping[person_name]
                    todo_message = (
                        f"📋 **Your Action Items from the Meeting** 📋\n\n"
                        f"Hello {person_name}"
                        f"{f' ({role})' if role else ''}"
                        f",\n\n"
                        f"Here are your action items based on the meeting minutes:\n\n"
                        f"{formatted_todos}\n\n"
                        f"Please complete these tasks as discussed in the meeting."
                    )
                    
                    # Send todo list to user using discord_notifier
                    asyncio.run_coroutine_threadsafe(
                        self.discord_notifier.send_simple_dm(user_id, todo_message),
                        self.discord_notifier.loop
                    )
                    print(f"[ActionAgent] Sent todo list to {person_name}")
                else:
                    if person_name not in self.user_id_mapping:
                        print(f"[ActionAgent] User {person_name} not found in mapping")
                    elif not formatted_todos:
                        print(f"[ActionAgent] No formatted todos for {person_name}")
        
        # Process and send email drafts
        if "email_drafts" in emails:
            for email_draft in emails["email_drafts"]:
                person_name = email_draft.get("name")
                formatted_email = email_draft.get("formatted_email")
                
                if person_name in self.user_id_mapping and formatted_email:
                    user_id = self.user_id_mapping[person_name]
                    email_message = (
                        f"📧 **Email Draft from Meeting Minutes** 📧\n\n"
                        f"Hello {person_name},\n\n"
                        f"Here's a draft email based on the meeting discussion:\n\n"
                        f"{formatted_email}\n\n"
                        f"Feel free to modify this draft before sending."
                    )
                    
                    # Send email draft to user using discord_notifier
                    asyncio.run_coroutine_threadsafe(
                        self.discord_notifier.send_simple_dm(user_id, email_message),
                        self.discord_notifier.loop
                    )
                    print(f"[ActionAgent] Sent email draft to {person_name}")
                else:
                    if person_name not in self.user_id_mapping:
                        print(f"[ActionAgent] User {person_name} not found in mapping")
                    elif not formatted_email:
                        print(f"[ActionAgent] No formatted email for {person_name}")
    
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
        1. Analyze the minutes to identify situations where an email needs to be sent, to external departments or clients
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

    def _print_todo_lists(self, todos):
        """Print todo lists to console in a readable format"""
        print("\n" + "="*50)
        print("TODO LISTS".center(50))
        print("="*50)
        
        if "todo_lists" in todos:
            for todo_item in todos["todo_lists"]:
                name = todo_item.get("name", "Unknown")
                role = todo_item.get("role", "")
                formatted_todos = todo_item.get("formatted_todos", "No todos")
                
                print(f"\n📋 {name}{f' ({role})' if role else ''}:")
                print("-"*50)
                print(formatted_todos)
                print("-"*50)
        else:
            print("\nNo todo lists found or error occurred.")
            if "error" in todos:
                print(f"Error: {todos['error']}")
                if "raw" in todos:
                    print(f"Raw response: {todos['raw']}")

    def _print_email_drafts(self, emails):
        """Print email drafts to console in a readable format"""
        print("\n" + "="*50)
        print("EMAIL DRAFTS".center(50))
        print("="*50)
        
        if "email_drafts" in emails:
            for email_draft in emails["email_drafts"]:
                name = email_draft.get("name", "Unknown")
                formatted_email = email_draft.get("formatted_email", "No email content")
                
                print(f"\n📧 Email draft for {name}:")
                print("-"*50)
                print(formatted_email)
                print("-"*50)
        else:
            print("\nNo email drafts found or error occurred.")
            if "error" in emails:
                print(f"Error: {emails['error']}")
                if "raw" in emails:
                    print(f"Raw response: {emails['raw']}")       