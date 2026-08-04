import json
import re
import argparse
import os

def extract_emails(text):
    # Standard regex for email addresses
    email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
    raw_emails = re.findall(email_pattern, text)
    
    # Filter out generic gmail addresses per user request
    valid_emails = []
    for email in raw_emails:
        if not email.lower().endswith('@gmail.com'):
            valid_emails.append(email)
            
    return list(set(valid_emails))  # Return unique valid emails

def process_posts(input_file, output_file=None):
    if not os.path.exists(input_file):
        print(f"Error: Input file {input_file} not found.")
        return

    with open(input_file, 'r', encoding='utf-8') as f:
        posts = json.load(f)
    
    filtered_posts = []
    
    for post in posts:
        text = post.get('text', '')
        found_emails = extract_emails(text)
        
        if found_emails:
            # Create a copy and add the extracted emails list
            post_with_email = post.copy()
            post_with_email['extracted_emails'] = found_emails
            filtered_posts.append(post_with_email)
            
    if not filtered_posts:
        print(f"No emails found in {len(posts)} posts. Skipping file creation.")
        return None
        
    if not output_file:
        input_dir = os.path.dirname(input_file)
        base, ext = os.path.splitext(os.path.basename(input_file))
        output_file = os.path.join(input_dir, f"{base}_with_emails.json")
        
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(filtered_posts, f, indent=4)
        
    print(f"Processed {len(posts)} posts.")
    print(f"Found {len(filtered_posts)} posts containing email addresses.")
    print(f"Results saved to: {output_file}")
    
    return output_file

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Filter LinkedIn posts that contain email addresses.")
    parser.add_argument("input_file", help="Path to the JSON file containing the scraped posts")
    parser.add_argument("-o", "--output_file", help="Optional output file path. Defaults to <input_name>_with_emails.json in the current directory.")
    
    args = parser.parse_args()
    process_posts(args.input_file, args.output_file)
