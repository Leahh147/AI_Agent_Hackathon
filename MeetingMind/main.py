import asyncio
from src.transcript.processor import TranscriptProcessor
from src.agents.minutes_agent import MinutesAgent
import os

async def main():
    # Get the project root directory
    project_root = os.path.dirname(os.path.abspath(__file__))
    
    # Set paths for input and output files
    sample_transcript_path = os.path.join(project_root, "tests", "sample_data", "sample_transcript.json")
    print(f"Transcript path: {sample_transcript_path}")
    print(f"File exists: {os.path.exists(sample_transcript_path)}")  # Debug check
    output_transcript_path = os.path.join(project_root, "output_transcript.json")
    
    # Create processor and agent
    processor = TranscriptProcessor(transcript_file_path=output_transcript_path)
    minutes_agent = MinutesAgent()
    
    # Register agent as observer of latest transcripts
    processor.register_observer(minutes_agent)
    
    # Start simulation - now properly awaiting the async method
    await processor.simulate_meeting(sample_transcript_path, time_limit_seconds=120) # Set time simulation limit 
    
    # At the end, we can retrieve the processed minutes
    final_minutes = minutes_agent.get_minutes()
    print("\nFinal Minutes:")
    for minute in final_minutes[:3]:  # Just show the first few
        print(f"{minute['timestamp']} - {minute['speaker']}: {minute['summary']}")

if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())