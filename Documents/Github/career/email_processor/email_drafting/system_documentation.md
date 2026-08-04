# Cold Email Generation System Documentation

> **IMPORTANT:** 
> - Always **READ** this document before making system changes.
> - Always **UPDATE** this document when adding new steps or modifying the system.
> - **REMOVE** any outdated or unused sections to keep it up to date with the current form of the system.

## Overview
This system is designed to automate the process of drafting cold emails or job application replies. It takes input such as recruiter emails or raw email addresses, uses an LLM to extract relevant entities (Name, Company), and generates a customized draft based on a predefined template.

---

## Step 1: Core Email Draft Generator

**Status**: Deprecated/Refactored (Moved into `llm_generator.py`)

**Goal**: Create a foundational script to accept input data, extract the recipient's first name and company, and output a drafted email.

---

## Step 2: Gmail Draft Integration & Refactoring

**Status**: Completed

**Goal**: Modularize the codebase and integrate the Google Gmail API to automatically create a draft of the generated email in the user's Gmail account.

**Implementation Details**:
- **`llm_generator.py`**: The core LLM logic extracted from Step 1. Takes input text, communicates with Groq API, and returns the formatted body string.
- **`email_drafting.py`**: Handles Google OAuth 2.0 authentication. It expects a `credentials.json` (OAuth Client ID) and saves session data to `token.json`. Uses `google-api-python-client` to create MIME drafts in the authenticated Gmail account.
- **`main.py`**: The central orchestrator. 
  1. Accepts multiline input (the email or target address).
  2. Calls `llm_generator` to build the body.
  3. Prompts the user for the explicit target email address.
  4. Calls `email_drafting` to create a draft with the subject "Testing 1".
- **Requirements**: `google-api-python-client`, `google-auth-httplib2`, `google-auth-oauthlib`.
