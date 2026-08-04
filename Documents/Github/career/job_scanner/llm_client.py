import json
import time
import logging
from groq import Groq
from job_scanner import config

# Set up simple logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self):
        if not config.GROQ_API_KEY:
            raise ValueError(
                "GROQ_API_KEY not found in environment! Please ensure your .env file "
                "contains GROQ_API_KEY=<your_key>."
            )
        self.client = Groq(api_key=config.GROQ_API_KEY)

    def chat_completion(self, system_prompt: str, user_prompt: str, json_mode: bool = True, model: str = None) -> str:
        """
        Submits a prompt to Groq API with robust error handling and optional JSON Mode structure.
        """
        model_name = model or config.DEFAULT_MODEL
        max_retries = 3
        backoff_factor = 2

        for attempt in range(max_retries):
            try:
                # Build request arguments
                kwargs = {
                    "model": model_name,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": 0.1,  # Low temperature for highly deterministic results
                }

                if json_mode:
                    kwargs["response_format"] = {"type": "json_object"}
                    # Enforce JSON formatting in the user prompt as required by Groq JSON Mode
                    if "json" not in user_prompt.lower() and "json" not in system_prompt.lower():
                        user_prompt += "\n\nIMPORTANT: Return your response strictly as a JSON object."
                        kwargs["messages"][1]["content"] = user_prompt

                response = self.client.chat.completions.create(**kwargs)
                return response.choices[0].message.content

            except Exception as e:
                logger.warning(f"Groq API call failed (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    sleep_time = backoff_factor ** attempt
                    logger.info(f"Retrying in {sleep_time}s...")
                    time.sleep(sleep_time)
                else:
                    logger.error("Max retries exceeded for Groq API call.")
                    raise e

    def parse_json_completion(self, system_prompt: str, user_prompt: str, model: str = None) -> dict:
        """
        Utility that makes a completion call and parses the result as JSON.
        """
        raw_response = self.chat_completion(system_prompt, user_prompt, json_mode=True, model=model)
        try:
            return json.loads(raw_response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {raw_response}")
            raise e
