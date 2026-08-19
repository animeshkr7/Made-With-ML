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
        
        if not data.get("company_name") or data["company_name"].lower() in ["none", "n/a", "null"]:
            if "greenhouse.io" in url or "lever.co" in url:
                data["company_name"] = url.split("/")[3]
                
        print(f"-> Extracted Data: {json.dumps(data, indent=2)}")
        return data
    except Exception as e:
        print(f"LLM extraction failed: {e}")
        comp = ""
        if "greenhouse.io" in url or "lever.co" in url:
            comp = url.split("/")[3]
        return {"company_name": comp, "job_id": "N/A", "job_title": "Role"}

def generate_referral_draft(person_name: str, company: str, title: str = "Role", job_id: str = "N/A", job_url: str = "") -> str:
    print(f"Generating referral message for 1st-degree connection {person_name} at {company}...")
    client = get_groq_client()
    greeting = "Hi," if not person_name else f"Hi {person_name},"
    job_link_str = f"\nJob Link: {job_url}" if job_url else ""

    prompt = f"""Draft a concise, professional LinkedIn referral request to a 1st-degree connection.
Format:
{greeting}

I noticed {company} is hiring for {title} and my background matches the requirements.

If you are open to it, could you please guide me or refer me for this position?
Job ID: {job_id}{job_link_str}

Attached my resume for reference.

Details:
Company: {company}
Title: {title}

Output ONLY the final message body. No intro/outro commentary.
"""
    try:
        res = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="openai/gpt-oss-20b",
            temperature=0.1,
        )
        msg = res.choices[0].message.content.strip()
        return msg.replace("\\n", "\n")
    except Exception as e:
        print(f"LLM message generation failed: {e}")
        return f"{greeting}\n\nI noticed {company} is hiring for {title} and my background matches the requirements.\n\nIf you are open to it, could you please guide me or refer me for this position?\nJob ID: {job_id}{job_link_str}\n\nAttached my resume for reference."
