import os
import json
from dotenv import load_dotenv
from groq import Groq

# Load environment variables
load_dotenv()

# Initialize Groq client
api_key = os.environ.get("GROQ_API_KEY")
if api_key:
    client = Groq(api_key=api_key)
else:
    client = None

def generate_email_body(input_email: str) -> str:
    if not client:
        raise ValueError("GROQ_API_KEY is not set. Please set it in your .env file.")

    prompt = f"""
You are an intelligent assistant. I will provide you with an email message or an email address.
Your task is to extract two specific pieces of information:
1. The first name of the person. This should be an individual person's name. If the input is just an email address (like kirti@magureinc.com or john.doe@company.com), extract the first name from the email prefix and capitalize it (e.g., Kirti, John). If it's a generic term like "HR", "Admin", "Team", "XYZ", or if you are not sure, output exactly "None".
2. The company name. If the input is an email address, extract the company name from the domain (e.g., from @magureinc.com extract Magureinc). If the company name is not available, output exactly "your company".

Return ONLY a JSON object with exactly two keys: "first_name" and "company_name".
Do not include any markdown formatting, backticks, or extra text.

Email:
\"\"\"
{input_email}
\"\"\"
"""
    
    try:
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="llama-3.1-8b-instant", 
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        data = json.loads(content)
        first_name = data.get("first_name", "None")
        company_name = data.get("company_name", "your company")
    except Exception as e:
        print(f"Error communicating with Groq API or parsing JSON: {e}")
        first_name = "None"
        company_name = "your company"

    if not first_name or str(first_name).strip().lower() in ["none", "null", "hr", "admin", "team"]:
        greeting = "Greetings,"
    else:
        greeting = f"Greetings {str(first_name).strip()},"
        
    if not company_name or str(company_name).strip().lower() in ["none", "null"]:
        company_name = "your company"
    else:
        company_name = str(company_name).strip()

    # Adjust greeting from "Greetings X," to "Hi X,"
    if greeting.startswith("Greetings"):
        greeting = greeting.replace("Greetings", "Hi")

    final_email_plain = f"""{greeting}

I’m Animesh, an Associate ML Engineer at Facctum. I saw that {company_name} is hiring for an ML Engineer, and I'd love to apply my background in AI to your team. 

My core expertise includes:
- Building and working with Large Language Models (LLMs)
- Developing Retrieval-Augmented Generation (RAG) pipelines
- Fine-tuning foundational models and Prompt Engineering
- Cloud deployment on AWS
- Classical Machine Learning & Data Science
- Python

You can find more details in my attached resume. I'd welcome the chance to chat about how my experience aligns with your goals.

Best regards,
Animesh Singh"""

    final_email_html = f"""
    <p>{greeting}</p>
    <p>I’m Animesh, an Associate <strong>ML Engineer</strong> at Facctum. I saw that {company_name} is hiring for an <strong>ML Engineer</strong>, and I'd love to apply my background in AI to your team.</p>
    <p>My core expertise includes:</p>
    <ul>
        <li>Building and working with <strong>Large Language Models (LLMs)</strong></li>
        <li>Developing <strong>Retrieval-Augmented Generation (RAG) pipelines</strong></li>
        <li><strong>Fine-tuning</strong> foundational models and <strong>Prompt Engineering</strong></li>
        <li>Cloud deployment on <strong>AWS</strong></li>
        <li><strong>Classical Machine Learning</strong> & <strong>Data Science</strong></li>
        <li><strong>Python</strong></li>
    </ul>
    <p>You can find more details in my <strong>attached resume</strong>. I'd welcome the chance to chat about how my experience aligns with your goals.</p>
    <p>Best regards,<br>Animesh Singh</p>
    """

    return final_email_plain, final_email_html, company_name
