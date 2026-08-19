import os
from pathlib import Path
from dotenv import load_dotenv

# Path resolution for .env loading
# Look in the current working directory, then the package directory, and then the sibling email_drafting folder.
current_dir = Path(__file__).resolve().parent
possible_env_paths = [
    current_dir / ".env",
    current_dir.parent / ".env",
    current_dir.parent / "email_drafting" / ".env"
]

env_loaded = False
for env_path in possible_env_paths:
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
        env_loaded = True
        break

if not env_loaded:
    load_dotenv()  # Default system loading

# API Configurations
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Groq Model Selection
# We'll use Llama 3.3 70B for highly accurate reasoning and structured outputs
DEFAULT_MODEL = "llama-3.3-70b-versatile"
FAST_MODEL = "openai/gpt-oss-20b"

# Selenium Configurations
SELENIUM_HEADLESS = True
SELENIUM_TIMEOUT = 10  # Seconds

# Scanning Configuration
# DAYS_LIMIT = 1 means only postings made "Today" or "1 day ago" (or matching the current day).
# 0 means strictly matching the current day ("Today" or matching current date).
DAYS_LIMIT = 1

# Classification Keywords (pre-gating to avoid excessive API calls on completely unrelated roles)
ML_KEYWORDS = [
    "machine learning", "ml", "deep learning", "nlp", "computer vision", 
    "reinforcement learning", "neural network", "llm", "large language model", 
    "generative ai", "ai engineer", "ai researcher", "ml engineer", 
    "data scientist", "data science"
]

# Sample targets to showcase adaptability out-of-the-box
DEFAULT_TARGET_SITES = [
    {"name": "OpenAI", "url": "https://openai.com/careers"},
    {"name": "Cohere", "url": "https://jobs.ashbyhq.com/cohere"},
    {"name": "Anthropic", "url": "https://www.anthropic.com/careers"}
]
