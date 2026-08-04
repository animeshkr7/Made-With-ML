import sys
from llm_generator import generate_email_body
from email_drafting import create_draft

def main():
    print("Welcome to the Cold Email Generation System!")
    print("Please paste the input email or target email address below.")
    print("When you are finished, press Enter twice (leave a blank line) to process:\n")
    
    lines = []
    empty_lines = 0
    while True:
        try:
            line = input()
            if not line.strip():
                empty_lines += 1
                if empty_lines >= 2:
                    break
            else:
                empty_lines = 0
            lines.append(line)
        except EOFError:
            break
            
    input_text = "\n".join(lines).strip()
    
    if not input_text:
        print("No input provided. Exiting.")
        sys.exit(1)
        
    print("\n[1/3] Generating email body using Groq LLM...")
    try:
        body_plain, body_html, company_name = generate_email_body(input_text)
    except Exception as e:
        print(f"Failed to generate email body: {e}")
        sys.exit(1)

    print("\n--- Generated Body ---")
    print(body_plain)
    print("----------------------\n")

    print("[2/3] Extracting target email address...")
    import re
    # Attempt to extract an email address from the input text
    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', input_text)
    
    if email_match:
        target_email = email_match.group(0)
        print(f"Found target email address: {target_email}")
    else:
        # Fallback if no email is found in the text
        target_email = input("No email address found in input. Please enter the exact target email address for this draft: ").strip()
        
    if not target_email:
        print("No target email provided. Exiting.")
        sys.exit(1)
        
    import json
    import os

    # Audit Logging
    audit_file = "audit_log.json"
    audit_data = {}
    is_redundant = False
    
    if os.path.exists(audit_file):
        try:
            with open(audit_file, "r", encoding="utf-8") as f:
                audit_data = json.load(f)
        except Exception:
            pass

    company_key = company_name if company_name else "unknown"
    if company_key not in audit_data:
        audit_data[company_key] = []
        
    if target_email in audit_data[company_key]:
        is_redundant = True
    else:
        audit_data[company_key].append(target_email)
        with open(audit_file, "w", encoding="utf-8") as f:
            json.dump(audit_data, f, indent=4)

    print(f"\n[3/3] Creating draft for {target_email} in your Gmail account...")
    
    # Load configuration
    config_path = "config.json"
    subject = "Application for ML Engineer"  # fallback
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)
                subject = config_data.get("email_subject", subject)
        except Exception as e:
            print(f"Warning: Could not read {config_path}: {e}")

    resume_path = "Animesh_Resume.pdf"
    
    try:
        draft = create_draft(target_email, subject, body_plain, attachment_path=resume_path, html_body=body_html)
        if draft:
            print("Successfully completed! Check your Gmail Drafts folder.")
            if is_redundant:
                print(f"[Audit] Redundant found: {target_email} was already processed for {company_key}.")
        else:
            print("Failed to create draft.")
    except FileNotFoundError as e:
        print(f"\nConfiguration Error: {e}")
        print("You must set up your Google Cloud project and download credentials.json to this directory.")

if __name__ == "__main__":
    main()
