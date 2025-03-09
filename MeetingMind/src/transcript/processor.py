# This file contains the TranscriptProcessor class, which is responsible for loading, saving, and processing meeting transcripts.
# Simulates getting the transcript line by line at the appropriate time from a speech-to-text API.
import json
import time
import datetime
from typing import List, Dict, Callable, Any
import asyncio

class TranscriptProcessor:
    def __init__(self, transcript_file_path: str = None):
        self.observers = []
        self.meeting_end_handlers = []
        self.transcript = []
        self.start_time = None
        self.transcript_file_path = transcript_file_path
        
    def register_observer(self, observer):
        """Register an observer to be notified of new transcript lines."""
        self.observers.append(observer)
        
    def remove_observer(self, observer):
        """Remove an observer from notification list."""
        if observer in self.observers:
            self.observers.remove(observer)

    async def _notify_observers(self, line):
        """
        Notify all observers about a new transcript line.
        
        Any class that registers as an observer must implement an 'update(self, transcript_line)' method.
        This method will be called each time a new transcript line is processed.
        
        The transcript_line parameter is a dictionary with:
        - 'timestamp': Time the line was spoken (e.g., "10:00:05 AM")
        - 'speaker': Name of the speaker
        - 'message': Content of what was said
        """
        for observer in self.observers:
            if asyncio.iscoroutinefunction(observer.update):
                await observer.update(line)
            else:
                observer.update(line)
    
    def load_transcript(self, transcript_json_path: str):
        """Load transcript from a JSON file and set the start time."""
        with open(transcript_json_path, 'r') as f:
            data = json.load(f)
            
        # Extract meeting start time
        meeting_time = data['meeting']['time']
        meeting_date = data['meeting']['date']
        self.start_time = datetime.datetime.strptime(f"{meeting_date} {meeting_time}", "%B %d, %Y %I:%M:%S %p")
        
        return data['meeting']['minutes']
    
    def save_transcript(self):
        """Save current transcript to a JSON file."""
        if not self.transcript_file_path:
            return
            
        meeting_data = {
            "meeting": {
                "date": self.start_time.strftime("%B %d, %Y"),
                "time": self.start_time.strftime("%I:%M:%S %p"),
                "minutes": self.transcript
            }
        }
        
        with open(self.transcript_file_path, 'w') as f:
            json.dump(meeting_data, f, indent=4)
    
    async def simulate_meeting(self, transcript_json_path: str, time_limit_seconds=None):
        """Simulate a meeting by playing transcript lines at appropriate times."""
        minutes = self.load_transcript(transcript_json_path)
        simulation_start_time = self.start_time
        real_simulation_start = datetime.datetime.now()
        
        print(f"Simulating meeting from transcript time: {simulation_start_time.strftime('%I:%M:%S %p')}")
        
        # Process all lines that fall within the time limit
        for line in minutes:
            # Get current line's timestamp
            current_timestamp = datetime.datetime.strptime(line['timestamp'], "%I:%M:%S %p")
            current_datetime = datetime.datetime.combine(
                simulation_start_time.date(), 
                current_timestamp.time()
            )
            
            # Calculate seconds from meeting start to this line
            simulated_elapsed = (current_datetime - simulation_start_time).total_seconds()
            
            # Skip lines that exceed the time limit
            if time_limit_seconds and simulated_elapsed > time_limit_seconds:
                continue
            
            # Calculate how much real time has passed
            real_elapsed = (datetime.datetime.now() - real_simulation_start).total_seconds()
            
            # Calculate how much time to wait until this line should appear
            wait_time = max(0, simulated_elapsed - real_elapsed)
            
            if wait_time > 0:
                await asyncio.sleep(wait_time)  # Use asyncio.sleep instead of time.sleep
            
            # Now process the line
            await self.add_transcript_line(line)
            
            # Print in a clearer format
            real_time_now = datetime.datetime.now().strftime('%H:%M:%S')
            print(f"Updated line with timestamp {line['timestamp']}: {line['speaker']}: {line['message'][:50]}...")
        
        # Wait until the full time limit has elapsed if specified
        if time_limit_seconds:
            total_elapsed = (datetime.datetime.now() - real_simulation_start).total_seconds()
            remaining_time = max(0, time_limit_seconds - total_elapsed)
            
            if remaining_time > 0:
                await asyncio.sleep(remaining_time)  # Use asyncio.sleep instead of time.sleep
            
            print(f"Time limit of {time_limit_seconds} seconds reached. Simulation complete.")
        
        print(f"Meeting simulation complete.")
        await self._notify_meeting_end()
    
    # Calling an observer when the meeting ends
    def register_meeting_end_handler(self, handler):
        """Register a handler to be called when the meeting ends."""
        self.meeting_end_handlers.append(handler)
        
    # Notify when meeting ends
    async def _notify_meeting_end(self):
        """Notify all registered handlers that the meeting has ended."""
        results = []
        for handler in self.meeting_end_handlers:
            if asyncio.iscoroutinefunction(handler):
                result = await handler()
            else:
                result = handler()
            results.append(result)
        return results
    
    async def add_transcript_line(self, line):
        """Add a new line to the transcript and notify observers."""
        self.transcript.append(line)
        await self._notify_observers(line)
        self.save_transcript()
        
    def get_full_transcript(self):
        """Return the full transcript."""
        return self.transcript