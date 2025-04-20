#from PIL import Image
import google.generativeai as genai
import os
import json
import pandas as pd
from dotenv import load_dotenv
import mimetypes
import yaml
import PyPDF2
from langchain_community.document_loaders.pdf import PyPDFLoader
import tempfile
from fin_agents.data_extractor_agent import chat_bank
from langchain.schema import SystemMessage, HumanMessage
from fin_utilities.promptSchema import bank_system_message, bank_human
from langchain_community.document_loaders import PyPDFLoader


# Load environment variables
load_dotenv()
api_key = os.environ["GOOGLE_API_KEY"]

# Initialize Google API Client
try:
    genai.configure(api_key=api_key)
except Exception as e:
    raise RuntimeError("Failed to configure Google Generative AI client. Check your API key.") from e



def load_prompts(docu):
    """
    Loads the prompt for the given document type from a YAML file.

    Args:
        docu (str): The document type tag (e.g., 'pan', 'aadhar', etc.)

    Returns:
        str: The prompt associated with the given document type.
    """
    try:
        # Get the current file's directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Construct the full path to the YAML file
        yaml_path = os.path.join(current_dir, 'data_extraction_prompts.yaml')
        
        # Open and load the YAML file
        with open(yaml_path, 'r') as file:
            prompts = yaml.safe_load(file)
            
            # Check if the document type exists in the prompts
            if docu not in prompts:
                raise KeyError(f"Document type '{docu}' not found in prompts.")
            
            return prompts[docu]
    except FileNotFoundError:
        raise RuntimeError("YAML file not found. Please check the file path.")
    except yaml.YAMLError as e:
        raise RuntimeError(f"Error parsing YAML file: {e}") from e
    except KeyError as e:
        raise RuntimeError(f"Missing key in YAML file: {e}") from e
    except Exception as e:
        raise RuntimeError(f"Unexpected error while loading prompts: {e}") from e


def extract_raw_data(uploaded_file, tag: str) -> dict:
    """
    Extracts data from an uploaded file using the Google Generative AI API.

    Args:
        uploaded_file (UploadedFile): The uploaded file object from Streamlit.
        tag (str): The document type tag (e.g., 'pan', 'aadhar', 'itr', 'form16', and bank statement (only for bank holder name, account number and address))

    Returns:
        dict: A dictionary containing extracted document details.
    """
    try:
        # Extract MIME type
        mime_type, _ = mimetypes.guess_type(uploaded_file.name)
        if not mime_type:
            raise ValueError(f"Could not determine MIME type for the file: {uploaded_file.name}")
    except Exception as e:
        raise RuntimeError(f"Failed to determine MIME type: {e}") from e

    try:
        # Handle PDF bankstatement - extract first page only
        if mime_type == 'application/pdf' and tag == 'bankstatement':
            pdf_reader = PyPDF2.PdfReader(uploaded_file)
            if len(pdf_reader.pages) > 0:
                # Create a new PDF writer
                pdf_writer = PyPDF2.PdfWriter()
                # Add only the first page
                pdf_writer.add_page(pdf_reader.pages[0])
                
                # Save the first page to a temporary file
                with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                    pdf_writer.write(temp_file)
                    temp_file_path = temp_file.name
                
                # Upload the temporary file
                file_response = genai.upload_file(path=temp_file_path, mime_type=mime_type, display_name="bankstatement_first_page")
                # Clean up the temporary file
                os.unlink(temp_file_path)
        else:
            # For other files, process normally
            file_response = genai.upload_file(path=uploaded_file, mime_type=mime_type, display_name="document")
    except Exception as e:
        raise RuntimeError(f"Failed to upload the file to Google API: {e}") from e

    try:
        # Create the prompt
        prompt = load_prompts(tag)
        #prompt = prompts.get(tag, '')
        
        # Initialize the Gemini 1.5 API model
        model_name = "models/gemini-1.5-flash-8b"
        model = genai.GenerativeModel(model_name=model_name)
        response = model.generate_content([prompt, file_response])
    except Exception as e:
        raise RuntimeError(f"Failed to generate content using the Gemini model: {e}") from e

    try:
        # Clean the response text
        clean_response = response.text.strip()
        
        # Remove backticks and "json" markers
        if clean_response.startswith("```json"):
            clean_response = clean_response[len("```json"):].strip()
        if clean_response.endswith("```"):
            clean_response = clean_response[:-len("```")].strip()

        # Parse the cleaned JSON
        extracted_data = json.loads(clean_response)
        return extracted_data
    except json.JSONDecodeError as e:
        raise ValueError(f"The model did not return valid JSON. Cleaned Response: {clean_response}") from e
    except Exception as e:
        raise RuntimeError(f"Unexpected error while parsing the response: {e}") from e


#---------------------------------------------------------------------------------------------------------------------------#
