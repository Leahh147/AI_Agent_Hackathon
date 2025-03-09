import os
import json
import openai
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle
import re

# Define the scopes
SCOPES = ['https://www.googleapis.com/auth/documents']
    
# Google Doc IDs
minutes_doc_id = '1W6BTAWwDpQL_X3dD02Z4j9AbHHTDSek0iOWc0f6MkDM'  # minutes template doc ID
roles_doc_id = '1Zibfc1Q8uLayySoMTbW6sZS1RhVEV6giWVShoZ450pU'  # roles doc ID

def get_google_credentials():
    """Get or refresh credentials for Google API access."""
    # Get the directory where google_doc_service.py is located
    service_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Path to credentials.json in the same directory as the script
    credentials_path = os.path.join(service_dir, 'credentials.json')
    
    # Path to token.pickle in the same directory
    token_path = os.path.join(service_dir, 'token.pickle')
    
    creds = None
    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)
    
    return creds

def get_document_content(doc_id):
    """Retrieve the content of a Google Doc by its ID."""
    creds = get_google_credentials()
    service = build('docs', 'v1', credentials=creds)
    
    document = service.documents().get(documentId=doc_id).execute()
    doc_content = document.get('body').get('content')
    
    text_content = ""
    for elem in doc_content:
        if 'paragraph' in elem:
            for para_elem in elem['paragraph']['elements']:
                if 'textRun' in para_elem:
                    text_content += para_elem['textRun']['content']
    
    return text_content

def extract_structure_with_llm(text_content):
    """Use an LLM to extract the meeting structure from text content."""
    openai.api_key = os.getenv("API_KEY")  # Make sure your API key is set
    
    prompt = f"""
    Extract the meeting structure from the following meeting minutes template:
    
    {text_content}
    
    Create a JSON structure with the following format:
    {{
        "date": "Meeting date",
        "time": "Meeting time",
        "attendees": ["Person1", "Person2", ...],
        "absences": ["Person1", "Person2", ...],
        "agenda": {{
            "1": {{
                "title": "Section title",
                "details": ""
            }},
            "2": {{
                "title": "Section with subsections",
                "subsections": {{
                    "2.1": {{
                        "title": "Subsection title",
                        "details": ""
                    }},
                    // More subsections...
                }}
            }},
            // More sections...
        }},
        "nextMeeting": ""
    }}
    
    Make sure to:
    1. Properly nest all sections, subsections, and sub-subsections
    2. Keep the section, subsection, and sub-subsection numbering format (e.g., "2", "2.1", "2.1.1")
    3. Set all "details" fields to empty strings
    4. Extract attendees and absences as arrays
    5. Include the date and time if available
    
    Return only the JSON structure with no additional text.
    """
    
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo-1106",
            messages=[
                {"role": "system", "content": "You are a helper that extracts structured data from meeting minutes templates."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        
        structure_json = response.choices[0].message.content
        return json.loads(structure_json)
    except Exception as e:
        print(f"Error with OpenAI API: {e}")
        # Fall back to simpler API call without response_format
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helper that extracts structured data from meeting minutes templates."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        
        content = response.choices[0].message.content
        
        # Try to extract JSON from the response
        import re
        json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
        if json_match:
            content = json_match.group(1)
        else:
            # If no code block, try to find JSON in the whole response
            json_match = re.search(r'({.*})', content, re.DOTALL)
            if json_match:
                content = json_match.group(1)
        
        return json.loads(content)

def extract_roles_data_from_text(text_content):
    """Extract role data directly from text content using regex parsing."""
    import re
    
    # Initialize empty roles dictionary
    roles_data = {}
    
    # Pattern to match roles with people in parentheses
    role_pattern = r'([A-Za-z&\s]+)\s*\(([^)]+)\)\s*\n((?:.+\n?)+?)(?:\n\s*[A-Za-z&\s]+\s*\(|\Z)'
    
    # Find all matches
    matches = re.finditer(role_pattern, text_content, re.MULTILINE)
    
    for match in matches:
        role_title = match.group(1).strip()
        person = match.group(2).strip()
        
        # Get the description and join multiple lines
        description_lines = match.group(3).strip().split('\n')
        description = ' '.join([line.strip() for line in description_lines])
        
        # Add to roles data
        roles_data[role_title] = {
            "person": person,
            "description": description
        }
    
    return roles_data

def generate_roles_data(doc_id, output_path=None):
    """Generate roles data from Google Doc."""
    # Get document content from Google Docs
    text_content = get_document_content(doc_id)
    
    # Extract roles data using direct parsing
    roles_data = extract_roles_data_from_text(text_content)
    
    # Save to file if output path provided
    if output_path:
        with open(output_path, 'w') as f:
            json.dump(roles_data, f, indent=2)
        print(f"Roles data generated and saved to {output_path}")
    
    return roles_data

def generate_minutes_structure(doc_id=minutes_doc_id, output_path=None):
    """Generate meeting minutes structure from Google Doc and save to file."""
    # Get document content
    content = get_document_content(doc_id)
    
    # Extract structure using LLM
    structure = extract_structure_with_llm(content)
    
    # Save to file if output path provided
    if output_path:
        with open(output_path, 'w') as f:
            json.dump(structure, f, indent=2)
        print(f"Minutes structure generated and saved to {output_path}")
    
    return structure

def get_project_root():
    """Get the project root directory from current script location."""
    # From meetingmind/src/services/google_doc_service.py to meetingmind/
    current_file_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(os.path.dirname(current_file_dir))

def generate_required_files():
    """Generate all required structure files."""
    project_root = get_project_root()
    
    # Output paths
    minutes_path = os.path.join(
        project_root, "tests", "sample_data", "sample_minute_structure_generated.json"
    )
    roles_path = os.path.join(
        project_root, "config", "role_description_generated.json"
    )
    
    # Generate minutes structure
    generate_minutes_structure(doc_id=minutes_doc_id, output_path=minutes_path)
    
    # Generate roles data
    generate_roles_data(doc_id=roles_doc_id, output_path=roles_path)
    
    return {
        "minutes_path": minutes_path,
        "roles_path": roles_path
    }

def append_detail_to_doc(doc_id, section_id, detail):
    """Append a detail to a specific section or subsection in the Google Doc.
    
    Args:
        doc_id: The Google Doc ID
        section_id: The section identifier (e.g., "2.1")
        detail: The detail text to add
    """
    creds = get_google_credentials()
    service = build('docs', 'v1', credentials=creds)
    
    # Get the document
    document = service.documents().get(documentId=doc_id).execute()
    
    # Define the pattern to search for based on section_id
    if '.' in section_id and not section_id.endswith('.'):
        # It's a subsection like "2.1"
        pattern = f"#### {section_id} "
    else:
        # It's a main section like "2." (strip the dot for matching)
        section_num = section_id.rstrip('.')
        pattern = f"### **{section_num}. "
    
    # Find the heading in the document
    content = document.get('body').get('content')
    found_section = False
    insert_position = None
    
    for i, element in enumerate(content):
        if not found_section and 'paragraph' in element:
            paragraph_text = ""
            
            for text_run in element['paragraph']['elements']:
                if 'textRun' in text_run:
                    paragraph_text += text_run['textRun']['content']
            
            if paragraph_text.startswith(pattern):
                # Found our section heading
                found_section = True
                # Start with the position right after this paragraph
                insert_position = element.get('endIndex', None)
                continue
        
        if found_section and 'paragraph' in element:
            paragraph_text = ""
            
            for text_run in element['paragraph']['elements']:
                if 'textRun' in text_run:
                    paragraph_text += text_run['textRun']['content']
            
            # If we find a new section or subsection heading, stop looking
            if (paragraph_text.startswith("### **") or 
                paragraph_text.startswith("#### ")):
                break
            
            # If we're still in bullet points, update our insert position
            # to the end of this paragraph
            if paragraph_text.strip().startswith("- "):
                insert_position = element.get('endIndex', None)
                continue
    
    if insert_position:
        # Insert the bullet point at the position we found
        requests = [{
            'insertText': {
                'location': {'index': insert_position},
                'text': f"- {detail}\n"
            }
        }]
        
        service.documents().batchUpdate(
            documentId=doc_id,
            body={'requests': requests}
        ).execute()
        
        print(f"Added bullet point to {section_id}")
        return True
    else:
        print(f"Could not find section {section_id}")
        return False

if __name__ == "__main__":
    generate_required_files()