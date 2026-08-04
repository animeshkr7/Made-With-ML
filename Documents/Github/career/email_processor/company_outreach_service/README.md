# Standalone LinkedIn Company Outreach Service

A modular service to automate 1st-degree connection referral drafting and new connection requests for targeted LinkedIn companies.

## Features

1. **Multi-Format Input Support**: Accepts any of the following input formats:
   - Company Name (e.g., `"Colgate Palmolive"`)
   - LinkedIn Company URL (e.g., `https://www.linkedin.com/company/colgate-palmolive/`)
   - LinkedIn Profile URL (e.g., `https://www.linkedin.com/in/username/`)
   - Job/Careers URL (e.g., `https://jobs.lever.co/colgate/12345`)

2. **1st-Degree Connection Referral Drafting**:
   - Navigates to `https://www.linkedin.com/company/<slug>/people/?facetNetwork=F`.
   - Extracts **up to a maximum of 5** 1st-degree connection profiles.
   - Generates custom referral draft messages using Groq LLM (Llama-3.1-8b-instant) and saves them into a JSON report.

3. **Formula-Based New Connection Requests**:
   - Navigates to the unfiltered people page (`https://www.linkedin.com/company/<slug>/people/`).
   - Identifies profiles with active `Connect` buttons (excluding `Message` and `Pending`).
   - Calculates new connections target using: `num_to_connect = max(3, 5 - count_1st_degree)`.
     - *4 existing 1st-degree* $\rightarrow$ Connects **3 new**
     - *1 existing 1st-degree* $\rightarrow$ Connects **4 new**
     - *5 existing 1st-degree* $\rightarrow$ Connects **3 new**
     - *0 existing 1st-degree* $\rightarrow$ Connects **5 new**

## Usage

```powershell
cd C:\Users\aks\Documents\Github\career\email_processor\company_outreach_service
python workflow.py "Colgate Palmolive"
```

Output is saved to a timestamped JSON file like `220726-COLGATE_PALMOLIVE.json`.
