import os
import json
import time
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(base_dir, '.env'))

def get_groq_client():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("Missing GROQ_API_KEY in environment or .env file.")
    return Groq(api_key=api_key)

def evaluate_batch_with_llm(batch_posts: list, max_retries: int = 4) -> dict:
    """
    Evaluates a batch of up to 7 posts using Groq LLM with exponential backoff retries.
    Returns a dict mapping str(post_index) -> {"Q1": bool, "Q2": bool, "Q3": bool}.
    """
    client = get_groq_client()
    
    # Format batch posts into prompt text
    batch_prompt_str = ""
    for idx, p in enumerate(batch_posts, 1):
        author = p.get("author", "Unknown")
        text = p.get("text", "")[:1000]  # Chunk text to 1000 chars to keep token usage lightweight
        batch_prompt_str += f"\n--- POST {idx} ---\nAuthor: {author}\nText:\n{text}\n"

    prompt = f"""You are a strict technical job recruiter evaluating LinkedIn posts.
Evaluate each of the following {len(batch_posts)} posts individually by answering 3 boolean (True/False) questions for each post:

Q1: Is this post announcing a hiring opening / job offer (True) vs a person looking for a job / candidate post (False)?
Q2: Is the job location Remote or in India (True) vs strictly a non-India foreign location without a remote option (False)?
Q3: Is the role core AI/ML, Data Science, MLOps, or Applied ML (True) vs generic DevOps, Data Engineering (without ML), or standard SDE without ML (False)?

Posts to evaluate:
{batch_prompt_str}

Respond ONLY with a valid JSON object mapping each post index ("1", "2", etc.) to a boolean evaluation.
Example JSON schema:
{{
  "1": {{"Q1": true, "Q2": true, "Q3": true}},
  "2": {{"Q1": true, "Q2": false, "Q3": true}}
}}
"""

    for attempt in range(max_retries):
        try:
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.1-8b-instant",
                temperature=0.0,
                response_format={"type": "json_object"}
            )
            content = chat_completion.choices[0].message.content.strip()
            data = json.loads(content)
            return data
        except Exception as e:
            err_msg = str(e).lower()
            if "rate limit" in err_msg or "429" in err_msg or "too many requests" in err_msg:
                wait_time = (2 ** attempt) * 6  # 6s, 12s, 24s, 48s
                print(f" -> Groq Rate Limit encountered. Retrying batch in {wait_time}s (Attempt {attempt+1}/{max_retries})...")
                time.sleep(wait_time)
            else:
                print(f" -> LLM evaluation error on batch: {e}")
                time.sleep(3)
                
    print(" -> Max retries reached for batch. Returning empty evaluation.")
    return {}

def process_posts_llm(input_filepath: str, batch_size: int = 7) -> str:
    """
    Processes all scraped posts from input_filepath in batches of 7 using LLM.
    Filters posts where Q1 == True and Q2 == True and Q3 == True.
    Saves qualified posts to output/linkedin_ml_posts_<timestamp>_llm_curated.json.
    """
    print("\n--- Starting Parallel LLM Post Filter ---")
    if not os.path.exists(input_filepath):
        print(f"Error: Input file {input_filepath} does not exist.")
        return ""

    with open(input_filepath, 'r', encoding='utf-8') as f:
        posts = json.load(f)

    print(f"Loaded {len(posts)} posts for LLM evaluation.")
    if not posts:
        return ""

    qualified_posts = []

    # Divide posts into batches of 7
    for i in range(0, len(posts), batch_size):
        batch = posts[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(posts) + batch_size - 1) // batch_size

        print(f"Evaluating Batch {batch_num}/{total_batches} ({len(batch)} posts)...")
        evaluations = evaluate_batch_with_llm(batch)

        for idx, post in enumerate(batch, 1):
            key = str(idx)
            post_id = post.get('id', idx)
            author = post.get('author', 'Unknown')

            if key not in evaluations:
                print(f" -> [WARNING] Post #{post_id} by {author} was MISSING from LLM response schema! Marked as Rejected.")
                continue

            eval_res = evaluations.get(key, {})
            if not isinstance(eval_res, dict):
                print(f" -> [WARNING] Post #{post_id} by {author} returned malformed response type '{type(eval_res)}'. Marked as Rejected.")
                continue

            q1 = bool(eval_res.get("Q1", False))
            q2 = bool(eval_res.get("Q2", False))
            q3 = bool(eval_res.get("Q3", False))

            if q1 and q2 and q3:
                print(f" -> [QUALIFIED] Post #{post_id} by {author} (Q1={q1}, Q2={q2}, Q3={q3})")
                post_copy = dict(post)
                post_copy["llm_evaluation"] = {"Q1": q1, "Q2": q2, "Q3": q3}
                qualified_posts.append(post_copy)
            else:
                rejection_reasons = []
                if not q1: rejection_reasons.append("Q1:Not Hiring")
                if not q2: rejection_reasons.append("Q2:Location Mismatch")
                if not q3: rejection_reasons.append("Q3:Not Core AI/ML")
                print(f" -> [REJECTED]  Post #{post_id} by {author} (Q1={q1}, Q2={q2}, Q3={q3}) -> {', '.join(rejection_reasons)}")

        # Paced delay between batch API calls
        time.sleep(2)

    # Determine output file path
    base_name = os.path.basename(input_filepath).replace(".json", "")
    output_filepath = os.path.join(os.path.dirname(input_filepath), f"{base_name}_llm_curated.json")

    with open(output_filepath, 'w', encoding='utf-8') as f:
        json.dump(qualified_posts, f, indent=4, ensure_ascii=False)

    print(f"\n[SUCCESS] LLM Evaluation Complete! Qualified {len(qualified_posts)}/{len(posts)} posts.")
    print(f"Saved LLM curated posts to: {output_filepath}")
    return output_filepath

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        process_posts_llm(sys.argv[1])
