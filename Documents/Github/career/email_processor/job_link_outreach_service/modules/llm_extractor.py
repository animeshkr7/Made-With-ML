import os
import json
from groq import Groq

def get_groq_client():
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    if not GROQ_API_KEY:
        raise ValueError("Missing GROQ_API_KEY in .env file")
    return Groq(api_key=GROQ_API_KEY)

def extract_company_and_details(url: str, text_chunk: str) -> dict:
    """
    Passes job URL and top text chunk to Groq LLM to extract company_name, job_title, and job_id.
    """
    print("Sending text chunk to LLM (llama-3.1-8b-instant) to extract Company Name...")
    client = get_groq_client()
    
    prompt = f"""You are an expert data extractor. Identify the target employer / company name, job title, and job ID from this job posting.
Hint: Look closely at company branding, job page headers, and URL path (e.g. jobs.colgate.com -> Colgate-Palmolive).

Job URL: {url}
Posting Content Chunk:
{text_chunk}

Respond ONLY with a valid JSON object matching this schema:
{{
  "company_name": "String",
  "job_title": "String",
  "job_id": "String"
}}
"""
    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant",
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        content = chat_completion.choices[0].message.content.strip()
        data = json.loads(content)
        
        company = data.get("company_name", "").strip()
        if not company or company.lower() in ["none", "n/a", "null", "unknown"]:
            if "colgate.com" in url:
                data["company_name"] = "Colgate-Palmolive"
            elif "greenhouse.io" in url or "lever.co" in url:
                data["company_name"] = url.split("/")[3].capitalize()

        print(f"-> LLM Extracted Details: {json.dumps(data, indent=2)}")
        return data
    except Exception as e:
        print(f"LLM Extraction Error: {e}")
        # Fallback heuristic
        company = "Company"
        if "colgate.com" in url:
            company = "Colgate-Palmolive"
        elif "greenhouse.io" in url or "lever.co" in url:
            company = url.split("/")[3].capitalize()
        return {"company_name": company, "job_title": "Role", "job_id": "N/A"}
