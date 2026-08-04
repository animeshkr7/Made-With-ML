import time

def check_profile_connection_status(page, profile_url: str) -> str:
    """
    Navigates to a person's LinkedIn profile URL and checks connection status.
    Returns: "Accepted" | "Pending" | "Not Connected" | "Unknown"
    """
    if not profile_url or not profile_url.startswith("http"):
        return "Unknown"

    print(f" -> Inspecting profile: {profile_url}")
    try:
        page.goto(profile_url, timeout=25000)
        time.sleep(3)

        # Check for 1st degree badge or Message button
        badge = page.query_selector('.dist-value:has-text("1st"), span.artdeco-badge:has-text("1st")')
        msg_btn = page.query_selector('button:has-text("Message"), a:has-text("Message"), button[aria-label*="Message"]')
        
        if badge or (msg_btn and msg_btn.is_visible()):
            print("    Status: ACCEPTED (1st Degree Connection)")
            return "Accepted"

        # Check for Pending / Pending Request
        pending_btn = page.query_selector('button:has-text("Pending"), button:has-text("Invite Sent"), button[aria-label*="Pending"]')
        if pending_btn and pending_btn.is_visible():
            print("    Status: PENDING")
            return "Pending"

        # Check for Connect button (request was not accepted or withdrawn)
        connect_btn = page.query_selector('button:has-text("Connect"), button[aria-label*="Connect"]')
        if connect_btn and connect_btn.is_visible():
            print("    Status: NOT CONNECTED (Connect button present)")
            return "Not Connected"

        print("    Status: PENDING (Default fallback)")
        return "Pending"
    except Exception as e:
        print(f"    Error inspecting profile: {e}")
        return "Unknown"
