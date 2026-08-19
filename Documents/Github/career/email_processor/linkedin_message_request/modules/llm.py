import os
import json
from groq import Groq

def get_groq_client():
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    if not GROQ_API_KEY:
        raise ValueError("Missing GROQ_API_KEY in .env file")
    return Groq(api_key=GROQ_API_KEY)

def extract_job_details(url: str, text: str) -> dict:
    print("Extracting job details using LLM (llama-3.1-8b-instant)...")
    client = get_groq_client()
    prompt = f"""You are a precise data extractor. Extract the company name, job ID, and job title from the following job posting.
Hint: Company name is often in the URL path (e.g. greenhouse.io/COMPANY_NAME). If Job ID is missing, output "N/A". If Job Title is missing, guess from the URL or output "Role".

Job URL: {url}
Job Text:
{text[:3000]}

Respond ONLY with a valid JSON object matching this schema:
{{
  "company_name": "String",
  "job_id": "String",
  "job_title": "String"
}}
"""
    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="openai/gpt-oss-20b",
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        content = chat_completion.choices[0].message.content.strip()
        data = json.loads(content)
        
        # Fallbacks if LLM misses company
        if not data.get("company_name") or data["company_name"].lower() in ["none", "n/a", "null"]:
            if "greenhouse.io" in url or "lever.co" in url:
                data["company_name"] = url.split("/")[3]
                
        print(f"-> Extracted Data: {json.dumps(data, indent=2)}")
        return data
    except Exception as e:
        print(f"LLM extraction failed: {e}")
        # Manual fallback
        comp = ""
        if "greenhouse.io" in url or "lever.co" in url:
            comp = url.split("/")[3]
        return {"company_name": comp, "job_id": "N/A", "job_title": "Role"}

def generate_draft_message(person_name: str, company: str, title: str, job_id: str, job_url: str, is_connected: bool = True) -> str:
    print(f"Generating tailored message for {person_name} (connected: {is_connected})...")
    client = get_groq_client()
    
    if is_connected:
        prompt_instruction = "a 1st-degree connection"
        body = f"I found {company} is hiring and profile matches my expertise."
    else:
        prompt_instruction = "a 2nd/3rd-degree connection (who you will send this to later)"
        body = f"I'm looking to connect as I found {company} is hiring and my profile matches the expertise needed."
        
    greeting = "Hi," if not person_name else f"Hi {person_name},"

    prompt = f"""Draft a very short, professional LinkedIn message to {prompt_instruction} exactly matching this format:

{greeting}

{body}

If you can look into it and guide me for this :
Job Id:[Job ID] - [Job Title]
Job Link: {job_url}

Attached my resume for reference.

Use these exact details:
Company: {company}
Job ID: {job_id}
Job Title: {title}

Output ONLY the final message. Do not include any extra text, pleasantries, or quotes.
"""
    try:
        res = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="openai/gpt-oss-20b",
            temperature=0.0,
        )
        msg = res.choices[0].message.content.strip()
        return msg.replace("\\n", "\n")
    except Exception as e:
        print(f"Message generation failed: {e}")
        return f"{greeting}\n\nI found {company} is hiring and profile matches my expertise.\n\nIf you can look into it and guide me for this :\nJob Id:{job_id} - {title}\nJob Link: {job_url}\n\nAttached my resume for reference."
