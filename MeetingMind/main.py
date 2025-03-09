import asyncio
from src.transcript.processor import TranscriptProcessor
from src.agents.minutes_agent import MinutesAgent
from src.agents.context_agent import ContextAgent
from src.agents.action_agent import ActionAgent
import os
from src.services.google_doc_service import generate_required_files

async def main():
    # Generate required structure files from google docs and save to local files
    # generated_files = generate_required_files()
    # print(f"Generated required files: {generated_files}")

    # Get the project root directory
    project_root = os.path.dirname(os.path.abspath(__file__))
    
    # Set paths for input and output files
    sample_transcript_path = os.path.join(project_root, "tests", "sample_data", "sample_transcript.json")
    output_transcript_path = os.path.join(project_root, "output_transcript.json")
    
    # Create processor and agent
    processor = TranscriptProcessor(transcript_file_path=output_transcript_path)
    minutes_doc_id = '1W6BTAWwDpQL_X3dD02Z4j9AbHHTDSek0iOWc0f6MkDM'  # minutes template doc ID

    minutes_agent = MinutesAgent(google_doc_id = minutes_doc_id)
    context_agent = ContextAgent(minutes_agent = minutes_agent)
    action_agent = ActionAgent(discord_token = discord_token, discord_channel_id=CHANNEL_ID)
    
    # Register agent as observer of latest transcripts
    processor.register_observer(minutes_agent)
    # Register agent as observer of final minutes
    processor.register_meeting_end_handler(action_agent.meeting_end_handler)
    
    # Start simulation - now properly awaiting the async method
    await processor.simulate_meeting(sample_transcript_path, time_limit_seconds=60) # Set time simulation limit 

    # during simulation, push notification if context_agent judges we should listen in

if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())