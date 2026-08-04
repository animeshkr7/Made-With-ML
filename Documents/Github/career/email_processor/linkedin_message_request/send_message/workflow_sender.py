import os
import sys
import json
import time
from playwright.sync_api import sync_playwright

def send_1st_degree_message(page, profile_url, message, resume_path):
    print(f"Navigating to {profile_url} to send message...")
    page.goto(profile_url)
    time.sleep(3)
    
    try:
        # Click the Message button on the profile
        msg_btn = page.query_selector('main button:has-text("Message"), main a:has-text("Message")')
        if msg_btn:
            msg_btn.click()
            time.sleep(2)
        else:
            raise Exception("Message button not found on profile.")

        # Find the message text box
        msg_box = page.query_selector('.msg-form__contenteditable')
        if not msg_box:
            raise Exception("Message input box not found.")
            
        msg_box.click()
        msg_box.fill(message)
        time.sleep(1)
        
        # Attach Resume
        print(f"Attaching resume: {resume_path}...")
        file_input = page.query_selector('input[type="file"]')
        if file_input:
            file_input.set_input_files(resume_path)
            time.sleep(4) # Wait for upload to complete
        else:
            raise Exception("Attachment input not found.")
            
        # Send
        send_btn = page.query_selector('button.msg-form__send-button')
        if send_btn and not send_btn.is_disabled():
            send_btn.click()
            print("Message sent successfully!")
            time.sleep(2)
            
            # Close the message overlay just in case
            close_btn = page.query_selector('button.msg-overlay-bubble-header__control--close-btn')
            if close_btn:
                close_btn.click()
            return True
        else:
            raise Exception("Send button not found or disabled.")
            
    except Exception as e:
        print(f"Failed to send message: {e}")
        return str(e)

def send_connection_request(page, profile_url, note_message):
    print(f"Navigating to {profile_url} to send connection request...")
    page.goto(profile_url)
    time.sleep(3)
    
    try:
        # Try finding the primary Connect button
        connect_btn = page.query_selector('main button:has-text("Connect")')
        
        if not connect_btn:
            # Look in the "More" dropdown
            more_btn = page.query_selector('main button:has-text("More")')
            if more_btn:
                more_btn.click()
                time.sleep(1)
                connect_btn = page.query_selector('div.artdeco-dropdown__content button:has-text("Connect"), div.artdeco-dropdown__content div:has-text("Connect")')
                
        if connect_btn:
            connect_btn.click()
            time.sleep(2)
            
            # Per user request, do NOT send a note with the connection request.
            # Just click Send directly.
            send_btn = page.query_selector('button[aria-label="Send without a note"], button[aria-label="Send now"], button:has-text("Send")')
            if send_btn:
                send_btn.click()
                print("Connection request sent successfully (without note)!")
                time.sleep(2)
                return True
            else:
                raise Exception("Could not find Send button after clicking Connect.")
        else:
            raise Exception("Connect button not found on profile. Might be 3rd degree without connect option, or already pending.")
            
    except Exception as e:
        print(f"Failed to send connection request: {e}")
        return str(e)


def main():
    if len(sys.argv) < 2:
        print("Usage: python workflow_sender.py <json_file>")
        sys.exit(1)
        
    json_path = sys.argv[1]
    if not os.path.exists(json_path):
        print(f"File not found: {json_path}")
        sys.exit(1)
        
    # Paths
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # linkedin_message_request
    email_processor_dir = os.path.dirname(project_dir) # email_processor
    
    state_path = os.path.join(email_processor_dir, "linkedin_monitor", "state.json")
    if not os.path.exists(state_path):
        state_path = os.path.join(project_dir, "state.json") # Fallback
        
    resume_path = os.path.join(project_dir, "Animesh_Resume.pdf")
    if not os.path.exists(resume_path):
        print(f"Resume not found at {resume_path}!")
        sys.exit(1)
        
    with open(json_path, 'r', encoding='utf-8') as f:
        drafts = json.load(f)
        
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False) # Headless=False so you can see it
        
        # Load state
        if os.path.exists(state_path):
            print("Loading LinkedIn session...")
            context = browser.new_context(storage_state=state_path)
        else:
            print(f"State file not found at {state_path}")
            sys.exit(1)
            
        page = context.new_page()
        
        updated_count = 0
        for i, draft in enumerate(drafts):
            if draft.get("status") == "SUCCESS":
                print(f"Skipping {draft.get('connection_profile_url')} - Already processed.")
                continue
                
            is_connected = draft.get("connected", False)
            url = draft.get("connection_profile_url")
            msg = draft.get("draft_message", "")
            
            print(f"\n--- Processing {i+1}/{len(drafts)}: {url} ---")
            
            if is_connected:
                result = send_1st_degree_message(page, url, msg, resume_path)
            else:
                result = send_connection_request(page, url, msg)
                
            if result is True:
                draft["status"] = "SUCCESS"
                draft.pop("error_msg", None)
            else:
                draft["status"] = "FAILED"
                draft["error_msg"] = result
                
            # Save progress incrementally
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(drafts, f, indent=2)
                
            updated_count += 1
            
            if i < len(drafts) - 1:
                print("Waiting 15 seconds before next action...")
                time.sleep(15)
                
        browser.close()
        
    print(f"\nWorkflow complete! Processed {updated_count} profiles.")

if __name__ == "__main__":
    main()
