import openai
from dotenv import load_dotenv
import os
import json
import re
import asyncio
from copy import deepcopy
import queue
from typing import List, Dict, Any

# Load the .env file
load_dotenv()

# Get the OpenAI API key from the environment variables
openai.api_key = os.getenv("API_KEY")

class MinutesAgent:
    def __init__(self, name="MinutesAgent"):
        self.name = name
        self.minutes = []
        self.processing_lock = asyncio.Lock()  # Lock for synchronizing updates
        self.transcript_queue = asyncio.Queue()  # Queue for transcript lines
        self.processing_task = None  # Task for processing the queue
        
        # Get the project root directory
        self.project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        # Set paths for files
        self.sample_minute_path = os.path.join(
            self.project_root, "tests", "sample_data", "sample_minute_structure.json"
        )
        self.output_path = os.path.join(
            self.project_root, "final_minutes.json"
        )
        
        # Load the initial minutes structure
        self.load_minutes_structure()
        
        # Start the background processing task
        self.start_processing()
    
    def load_minutes_structure(self):
        """Load the initial minutes structure from the sample file."""
        try:
            with open(self.sample_minute_path, 'r') as f:
                self.minutes_structure = json.load(f)
            
            # Save the initial structure to the output file
            self.save_minutes()
            print(f"Loaded minutes structure from {self.sample_minute_path}")
        except Exception as e:
            print(f"Error loading minutes structure: {e}")
            self.minutes_structure = {}
    
    def start_processing(self):
        """Start the background task to process queued transcript lines."""
        self.processing_task = asyncio.create_task(self.process_queue())
    
    async def process_queue(self):
        """Process transcript lines from the queue one at a time."""
        while True:
            try:
                # Get the next transcript line from the queue
                transcript_line = await self.transcript_queue.get()
                
                # Process the transcript line
                await self._process_transcript_line(transcript_line)
                
                # Mark the task as done
                self.transcript_queue.task_done()
                
            except Exception as e:
                print(f"Error processing transcript line: {e}")
                continue
    
    async def update(self, transcript_line):
        """Called when a new transcript line is added. Adds the line to the processing queue."""
        print(f"{self.name} received: {transcript_line['speaker']} said: {transcript_line['message']}")
        
        # Add to basic history
        if len(transcript_line['message']) > 50:
            summary = f"Summary: {transcript_line['message'][:50]}..."
        else:
            summary = f"Short message: {transcript_line['message']}"
            
        self.minutes.append({
            "timestamp": transcript_line['timestamp'],
            "speaker": transcript_line['speaker'],
            "summary": summary
        })
        
        # Add to the processing queue instead of processing immediately
        await self.transcript_queue.put(transcript_line)
    
    async def _process_transcript_line(self, transcript_line):
        """Process a single transcript line - called from the queue processor."""
        # Generate agenda update using OpenAI
        transcript_message = f"{transcript_line['speaker']}: {transcript_line['message']}"
        
        # Use the lock to ensure only one update is processed at a time
        async with self.processing_lock:
            update = await self.generate_agenda_update_async(transcript_message, self.minutes_structure)
            
            # Process the update and modify the minutes structure if needed
            if update and isinstance(update, dict) and update.get("section") is not None and update.get("details"):
                self.update_minutes_structure(update)
                # Save the updated structure
                self.save_minutes()
    
    async def generate_agenda_update_async(self, transcript_message, last_agenda):
        """Async version of generate_agenda_update."""
        messages = [
            {"role": "system", "content": "You are an assistant helping to organize a meeting minutes based on the latest transcript."},
            {"role": "user", "content": f"""
            The meeting agenda structure is as follows:
            {json.dumps(last_agenda, indent=2)}

            The latest transcript message is:
            {transcript_message}

            Your task is to:
            1. Identify IF the section or subsection in the agenda corresponds to the transcript.
            2. ONLY if the transcript contains relevant information, update that section/subsection.
            3. The updated content to update are should be a summary of key details extracted from the transcript message.
            3. Return ONLY a JSON object in this format:
            {{
                "section": "2", 
                "subsection": "2.1", // only include if updating a subsection
                "details": "Updated content" // include relevant details from transcript
            }}

            If the transcript doesn't contain any information relevant to the agenda, return:
            {{
                "section": null,
                "details": null
            }}
            """}
        ]

        # Use asyncio to run the OpenAI call asynchronously
        response = await asyncio.to_thread(
            openai.chat.completions.create,
            model="gpt-4",  # You can use gpt-4 or gpt-3.5-turbo
            messages=messages,
            temperature=0.7,
            max_tokens=300
        )

        content = response.choices[0].message.content.strip()
        
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            try:
                update_json = json.loads(json_match.group())
                return update_json
            except json.JSONDecodeError:
                print("Error decoding JSON from OpenAI response")
                return {"section": None, "details": None}
        else:
            return {"section": None, "details": None}
    
    def update_minutes_structure(self, update):
        """Update the minutes structure with the new information."""
        section = update.get("section")
        subsection = update.get("subsection", None)
        details = update.get("details", "")
        
        if not section or section not in self.minutes_structure["agenda"]:
            return
            
        if not subsection:
            # Update main section
            self.minutes_structure["agenda"][section]["details"] = details
            print(f"Updated section {section} with: {details[:30]}...")
        else:
            # Handle nested subsections
            section_data = self.minutes_structure["agenda"][section]
            
            # Check if the section has subsections
            if "subsections" not in section_data:
                return
                
            # Check if the exact subsection exists
            if subsection in section_data["subsections"]:
                section_data["subsections"][subsection]["details"] = details
                print(f"Updated subsection {section}.{subsection} with: {details[:30]}...")
    
    def save_minutes(self):
        """Save the current minutes structure to a file."""
        try:
            with open(self.output_path, 'w') as f:
                json.dump(self.minutes_structure, f, indent=2)
        except Exception as e:
            print(f"Error saving minutes: {e}")
    
    def get_minutes(self):
        """Return the generated minutes."""
        return self.minutes