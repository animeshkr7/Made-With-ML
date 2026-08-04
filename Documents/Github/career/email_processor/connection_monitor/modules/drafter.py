import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

def get_groq_client():
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    if not GROQ_API_KEY:
        raise ValueError("Missing GROQ_API_KEY in .env file")
    return Groq(api_key=GROQ_API_KEY)

def generate_accepted_referral_message(first_name: str, company: str, job_title: str = "Role", job_id: str = "N/A", job_url: str = "") -> str:
    """
    Generates a polite referral message for a newly accepted 1st-degree connection.
    """
    print(f"Generating accepted referral message for {first_name} at {company}...")
    try:
        client = get_groq_client()
        greeting = "Hi," if not first_name else f"Hi {first_name},"
        job_link_str = f"\nJob Link: {job_url}" if job_url else ""

        prompt = f"""Draft a short, polite LinkedIn message to a 1st-degree connection who just accepted your connection request.
Format:
{greeting}

Thanks for connecting! I noticed {company} is hiring for {job_title} and my background aligns with the requirements.

If you are open to it, could you please guide me or refer me for this position?
Job ID: {job_id}{job_link_str}

Attached my resume for reference.

Details:
Company: {company}
Title: {job_title}

Output ONLY the final message text.
"""
        res = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant",
            temperature=0.1,
        )
        msg = res.choices[0].message.content.strip()
        return msg.replace("\\n", "\n")
    except Exception as e:
        print(f"LLM draft generation fallback: {e}")
        greeting = "Hi," if not first_name else f"Hi {first_name},"
        return f"{greeting}\n\nThanks for connecting! I noticed {company} is hiring for {job_title} and my background aligns with the requirements.\n\nIf you are open to it, could you please guide me or refer me for this position?\nJob ID: {job_id}\n\nAttached my resume for reference."
