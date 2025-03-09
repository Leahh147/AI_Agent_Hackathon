import asyncio
from src.transcript.processor import TranscriptProcessor
from src.agents.minutes_agent import MinutesAgent
from src.agents.context_agent import ContextAgent
import os
from dotenv import load_dotenv

# Load the .env file
load_dotenv()

# async def check_listen_in(context_agent):
#     while True:
#         should_listen_in = await context_agent.should_listen_in()
#         if should_listen_in:
#             print("Adi should listen in!")
#         await asyncio.sleep(5)  # Check every 5 seconds

async def main():
    # Get the project root directory
    project_root = os.path.dirname(os.path.abspath(__file__))
    
    # Set paths for input and output files
    sample_transcript_path = os.path.join(project_root, "tests", "sample_data", "sample_transcript.json")
    output_transcript_path = os.path.join(project_root, "output_transcript.json")
    
    # Create processor and agents
    processor = TranscriptProcessor(transcript_file_path=output_transcript_path)
    minutes_doc_id = '1W6BTAWwDpQL_X3dD02Z4j9AbHHTDSek0iOWc0f6MkDM'  # minutes template doc ID
    context_agent = ContextAgent(profile="Adi")
    minutes_agent = MinutesAgent(google_doc_id = minutes_doc_id, context_agent=context_agent)
    
    
    # Load the transcript
    processor.register_observer(minutes_agent)
    
    # #start the listen_in task
    # listen_in_task = asyncio.create_task(check_listen_in(context_agent))

    # # Start the listen-in check task
    # listen_in_task = check_listen_in(context_agent)
    
    # # Simulate the transcript and process it
    # simulate_task = processor.simulate_meeting(sample_transcript_path, time_limit_seconds=120)
    
    # # Run both tasks concurrently
    # await asyncio.gather(listen_in_task, simulate_task)

    await processor.simulate_meeting(sample_transcript_path, time_limit_seconds=120)
    
    

if __name__ == "__main__":
    asyncio.run(main())