from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import os
from langchain_openai import ChatOpenAI
#import logging
from langchain_anthropic import ChatAnthropic
from dotenv import load_dotenv
#from langchain_openai import ChatOpenAI

# Load environment variables
try:
    load_dotenv()
except Exception as e:
    print(f"Error loading .env file: {e}")

# Fetch Google API key
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
if not GOOGLE_API_KEY :
    raise ValueError("GOOGLE_API_KEY not found in environment variables")


chat = ChatGoogleGenerativeAI(
    model="models/gemini-1.5-flash-8b-latest",
    temperature=0.2,
    google_api_key=GOOGLE_API_KEY,
   )


# ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
# if not ANTHROPIC_API_KEY:
#     raise ValueError("ANTHROPIC_API_KEY not found in environment variables")


# chat_bank = ChatAnthropic(
#     model="claude-3-5-sonnet-20240620",
#     temperature=0.7,
#     max_tokens=2048,
#     api_key=ANTHROPIC_API_KEY
# )

# import google.generativeai as genai
# def list_available_models():
#     models = genai.list_models()
#     for model in models:
#         print(model)
# # Call the function
# list_available_models()


load_dotenv()
# Configure Google API
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in environment variables")


chat_bank = ChatOpenAI(
    model="gpt-4o",
    temperature=0.2,
    openai_api_key=OPENAI_API_KEY
)