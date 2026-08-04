# ATS Scraping Insights: Keka & Embedded Widgets

When scraping company career pages, Applicant Tracking Systems (ATS) are often embedded dynamically. This document details the methodology used to reverse-engineer the Keka ATS embed on `akaike.ai` and provides generalizable insights for future scraping tasks.

## 1. The Challenge of Embedded ATS Widgets

Many modern websites do not render their job listings in the static HTML payload sent by the server. Instead, they use embedded widgets (like Keka, Greenhouse, Lever, etc.) which load the listings dynamically via JavaScript. 

When you fetch the raw HTML of the careers page, you might only see a container `<div>` and a `<script>` tag.

## 2. The Keka Embed Architecture

Initially, Keka injected all active jobs directly into a Javascript file loaded by the client. The jobs were hardcoded into a variable:
```javascript
var jobList = [...]; // Previously contained all jobs
```

**The Shift to API-First Loading:**
To improve performance and maintain live synchronization, Keka (and many other modern ATS platforms) shifted to an asynchronous API model. 
1. The website loads the Keka Javascript embed widget.
2. The Javascript initializes the UI and makes a background `fetch()` call to a specific JSON API endpoint.
3. The `jobList` variable in the JS payload is now left completely empty (`[]`).

## 3. Discovering the Hidden API (Methodology)

If standard DOM parsing fails or returns empty lists, follow this methodology to find the hidden data:

1. **Visual Browser Inspection:** Launch a real browser (or use the AI `browser_subagent`) to load the page.
2. **Network Tab Interception:** Check the Network tab in DevTools (filtered by `Fetch/XHR`). Look for background requests returning JSON objects.
3. **Trace the Embed ID:** In the case of Keka, the embed script tag looked like this:
   ```html
   <script src="https://akaike.keka.com/careers/api/embedjobs/js/e5a4c096-b298-441c-9700-14aba5c577c5"></script>
   ```
   The UUID at the end (`e5a4c096...`) is the unique identifier for that company's active job portal.
4. **Endpoint Translation:** By tracing the network calls, we discovered that the actual active jobs were being loaded from a parallel endpoint using the exact same UUID:
   - **JS Payload:** `/api/embedjobs/js/{uuid}`
   - **JSON API:** `/api/embedjobs/default/active/{uuid}`

## 4. The Extraction Logic

To scrape this reliably in the future without needing a headless browser (which is slow and resource-heavy), we can simulate the API discovery programmatically:

```python
import urllib.request
import re
import json

# 1. Fetch the static HTML
html = urllib.request.urlopen("http://company.com/careers").read().decode('utf-8')

# 2. Extract the JS Embed URL using regex
match = re.search(r'src="(https://.*?keka\.com/careers/api/embedjobs/js/[^"]+)"', html)
if match:
    js_url = match.group(1)
    
    # 3. Translate the JS endpoint to the hidden JSON active endpoint
    api_url = js_url.replace('/js/', '/default/active/')
    
    # 4. Fetch the raw JSON directly!
    json_data = urllib.request.urlopen(api_url).read().decode('utf-8')
    jobs = json.loads(json_data)
```

## 5. Generalizing to Other ATS Platforms

This exact methodology applies broadly across the ATS scraping landscape:

* **Greenhouse & Lever:** Often embed via an `<iframe>`. You must extract the `src` attribute of the iframe, request that URL, and scrape *that* DOM. Alternatively, they often expose a public JSON API board (e.g., `boards-api.greenhouse.io/board/{company}/jobs`).
* **Workday:** Uses complex shadow DOMs and pagination. They often require intercepting internal POST requests with specific CSRF tokens and headers to an endpoint like `/wday/cxs/{company}/jobs`.
* **Always look for the JSON:** HTML scraping is brittle. Whenever an ATS widget is used, there is almost always a pure JSON endpoint powering it. Spending 5 minutes finding the hidden JSON API saves hours of writing and fixing brittle HTML XPath/CSS selectors.
