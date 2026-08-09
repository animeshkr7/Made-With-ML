import json
import os
import re

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "filter_config.json")

def load_config():
    """Load filtering configuration from JSON file."""
    if not os.path.exists(CONFIG_PATH):
        return {"exclude_keywords": [], "exclude_email_domains": []}
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def should_exclude_post(text, config=None):
    """
    Check if a post should be excluded based on its text.
    Returns (True, reason) if it should be excluded, (False, "") otherwise.
    """
    if not text:
        return False, ""
        
    if config is None:
        config = load_config()
    
    text_lower = text.lower()
    
    # 1. Check for excluded keywords
    for kw in config.get("exclude_keywords", []):
        if kw.lower() in text_lower:
            return True, f"Keyword match: '{kw}'"
            
    # 2. Check for excluded email domains
    for domain in config.get("exclude_email_domains", []):
        if domain.lower() in text_lower:
            return True, f"Email domain match: '{domain}'"
            
    return False, ""
