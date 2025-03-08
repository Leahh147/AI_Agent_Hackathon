import openai
from dotenv import load_dotenv
import os
import json

# Load the .env file
load_dotenv()

# Get the OpenAI API key from the environment variables
openai.api_key = os.getenv("API_KEY")

print(openai.api_key)

# Function to generate a response from the OpenAI API
def generate_agenda_update(transcript_message, last_agenda):
    # Preparing the messages for the OpenAI model
    messages = [
        {"role": "system", "content": "You are an assistant helping to organize a meeting and update the agenda based on the latest transcript."},
        {"role": "user", "content": f"""
        The meeting agenda is as follows:
        {json.dumps(last_agenda, indent=2)}

        The latest transcript message is:
        {transcript_message}

        Your task is to:
        1. Identify the section or subsection in the agenda that corresponds to the transcript.
        2. Update that section or subsection with the details from the transcript.
        3. Return the index of the updated part (e.g., "1" or "2.1") and the updated version of that part.
        """}
    ]

    # Requesting OpenAI's response using the new API method
    response = response = openai.chat.completions.create(
        model="gpt-4",  # You can use gpt-4 or gpt-3.5-turbo
        messages=messages,
        temperature=0.7,
        max_tokens=150
    )

    # Parsing the response
    result = response.choices[0].message.content.strip()

    # Extracting the updated section and index
    try:
        updated_index, updated_details = result.split(":", 1)
        updated_index = updated_index.strip()
        updated_details = updated_details.strip()

        # Ensure that the updated_details have the correct format
        return {
            "updated_index": updated_index,
            "updated_section": {
                "title": last_agenda["agenda"].get(updated_index.split('.')[0], {}).get("title", ""),
                "details": updated_details
            }
        }
    except Exception as e:
        return {"error": f"Error parsing the response: {e}"}

# Example of the transcript and last meeting agenda
transcript_message = """
We have finalized the library budget proposal, and the elections will be held next month.
"""

last_agenda = {
    "date": "March 8, 2025",
    "time": "10:00 AM",
    "attendees": ["Rohan", "Adi", "Kriti", "Oishi", "Diya", "Harsh"],
    "absences": ["Connie", "Leah", "Edward"],
    "agenda": {
        "1": {
            "title": "Matters Arising from Last Meeting",
            "details": "Rohan (President) opened the meeting and asked if there were any matters arising from the last meeting."
        },
        "2": {
            "title": "President's Update",
            "subsections": {
                "2.1": {
                    "title": "Library Budget",
                    "details": ""
                },
                "2.2": {
                    "title": "Elections",
                    "details": ""
                },
                "2.3": {
                    "title": "Call with EWOR",
                    "details": ""
                }
            }
        }
    }
}

# Call the function to update the agenda
result = generate_agenda_update(transcript_message, last_agenda)

# Print the result
print(json.dumps(result, indent=2))