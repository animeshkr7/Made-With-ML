import sys
import os
import json

# Add email_drafting to sys.path so we can import modules
script_dir = os.path.dirname(os.path.abspath(__file__))
email_drafting_dir = os.path.join(script_dir, "email_drafting")
sys.path.append(email_drafting_dir)

# Temporarily change directory to email_drafting so the imported modules
# can find their credentials.json and token.json correctly.
os.chdir(email_drafting_dir)
from llm_generator import generate_email_body
from email_drafting import create_draft
# Change back to the main directory for our outputs (audit log, etc.)
os.chdir(script_dir)

def process_batch(json_file_path):
    print(f"Loading data from {json_file_path}...")
    try:
        with open(json_file_path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
    except UnicodeDecodeError:
        with open(json_file_path, "r", encoding="utf-16le") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading JSON: {e}")
        return

    records = data.get("data", [])
    if not records:
        print("No records found to process.")
        return

    # Files will be read/written in the email_processor directory (above email_drafting)
    config_path = os.path.join(script_dir, "config.json")
    default_subject = "Application for ML Engineer"
    subject = default_subject
    
    # Try local config first, fallback to email_drafting config
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8-sig") as f:
                config_data = json.load(f)
                subject = config_data.get("email_subject", subject)
        except Exception:
            pass
    else:
        fallback_config = os.path.join(email_drafting_dir, "config.json")
        if os.path.exists(fallback_config):
            try:
                with open(fallback_config, "r", encoding="utf-8-sig") as f:
                    config_data = json.load(f)
                    subject = config_data.get("email_subject", subject)
            except Exception:
                pass

    audit_file = os.path.join(script_dir, "audit_log.json")
    resume_path = os.path.join(email_drafting_dir, "Animesh_Resume.pdf")

    # Load audit data
    audit_data = {}
    if os.path.exists(audit_file):
        try:
            with open(audit_file, "r", encoding="utf-8-sig") as f:
                audit_data = json.load(f)
        except Exception:
            pass

    for index, record in enumerate(records):
        target_email = record.get("email")
        if not target_email:
            print(f"[{index+1}/{len(records)}] Skipping record with no email.")
            continue

        print(f"\n[{index+1}/{len(records)}] Processing email: {target_email}")
        
        # 1. Generate Email Body
        try:
            # Note: the API call might depend on CWD for some things, but Groq doesn't.
            body_plain, body_html, company_name = generate_email_body(target_email)
        except Exception as e:
            print(f"Failed to generate email body for {target_email}: {e}")
            continue

        company_key = company_name if company_name else "unknown"
        
        # Check audit
        if company_key not in audit_data:
            audit_data[company_key] = []
            
        is_redundant = False
        if target_email in audit_data[company_key]:
            is_redundant = True
            
        # Add to audit and save
        if not is_redundant:
            audit_data[company_key].append(target_email)
            with open(audit_file, "w", encoding="utf-8-sig") as f:
                json.dump(audit_data, f, indent=4)

        # 2. Create Draft
        print(f"Creating draft for {target_email} in your Gmail account...")
        try:
            # Switch to email_drafting temporarily for create_draft so it finds token.json
            os.chdir(email_drafting_dir)
            draft = create_draft(target_email, subject, body_plain, attachment_path=resume_path, html_body=body_html)
            os.chdir(script_dir)
            
            if draft:
                print(f"Successfully created draft for {target_email}.")
                if is_redundant:
                    print(f"[Audit] Redundant found: {target_email} was already processed for {company_key}.")
            else:
                print(f"Failed to create draft for {target_email}.")
        except Exception as e:
            os.chdir(script_dir)
            print(f"Error creating draft for {target_email}: {e}")

    print("\nBatch processing complete.")

if __name__ == "__main__":
    import glob
    # Find the most recent json file in data folder, or take argument
    if len(sys.argv) > 1:
        json_file = sys.argv[1]
    else:
        # Default to the most recent one in data directory
        data_dir = os.path.join(script_dir, "data")
        files = glob.glob(os.path.join(data_dir, "*.json"))
        if not files:
            print("No JSON files found in data folder.")
            sys.exit(1)
        json_file = max(files, key=os.path.getmtime)
        
    process_batch(json_file)
