import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from app.core.config import settings

# Load environment variables
load_dotenv()

# Model configurations
DEFAULT_OPENAI_MODEL = os.environ.get("OPENAI_MODEL_NAME") or getattr(settings, "OPENAI_MODEL_NAME", None) or "gpt-4.1-mini"
openai_api_key = os.environ.get("OPENAI_API_KEY") or getattr(settings, "OPENAI_API_KEY", "")

# Shared LLM Instance
llm = ChatOpenAI(model=DEFAULT_OPENAI_MODEL, api_key=openai_api_key)

# Provider configurations
IMAGE_PROVIDER = (os.environ.get("IMAGE_PROVIDER") or getattr(settings, "IMAGE_PROVIDER", "gemini")).lower()
SEARCH_PROVIDER = (os.environ.get("SEARCH_PROVIDER") or getattr(settings, "SEARCH_PROVIDER", "tavily")).lower()
OPENAI_IMAGE_MODEL = (os.environ.get("OPENAI_IMAGE_MODEL") or getattr(settings, "OPENAI_IMAGE_MODEL", "dall-e-3")).lower()

# API Keys validation helpers
def get_tavily_api_key() -> str:
    return os.environ.get("TAVILY_API_KEY") or getattr(settings, "TAVILY_API_KEY", "")

def get_google_api_key() -> str:
    return os.environ.get("GOOGLE_API_KEY") or getattr(settings, "GOOGLE_API_KEY", "")
