# Email Creator & Drafts UI Updates

This file documents the recent additions and enhancements made to the **Drafts UI** located in `email_ceator/email-application-ui`.

## 1. Tinder-Style Swipe View
- **Dual View Modes:** Added a toggle switch at the top of the interface to switch between "Grid View" and "Swipe View".
- **Swipe View (Mobile First):** Displays one job post at a time perfectly centered for easy reading.
- **Natural Swipe Flow:** Clicking `Reject` or `Draft` automatically animates the current post out of view and seamlessly slides the next post into view. No blocking pop-ups are used.
- **Keyboard Shortcuts (Desktop):** 
  - `Left Arrow`: Previous Post
  - `Right Arrow`: Next Post
  - `Backspace / Delete`: Reject Post
  - `Enter`: Draft Email for the primary contact

## 2. Advanced Layout & UX
- **Grid Layout (Dashboard):** In "Grid View", the cards now flow into a masonry-style CSS grid (`grid-template-columns`) which makes it far easier to analyze posts on a widescreen without text stretching across the entire monitor.
- **Wider Container:** The main UI container max-width was expanded from `700px` to `1000px` to utilize more desktop space while retaining full mobile responsiveness.
- **Inline Feedback:** Action buttons naturally show inline state changes (e.g., `✅ Drafted`, `❌ Failed`) instead of annoying browser alerts.

## 3. Automated Post Filtering & Cleanup
The UI now silently processes the scraped data before displaying it to you:
- **Generic Email Filter:** Any post containing an email address from generic domains (e.g., `@gmail.com`, `@programming.com`, `@hotmail.com`, `@outlook.com`, `@protonmail.com`) is completely hidden from the feed.
- **Location Filter (Keyword Blocklist):** Any post containing the keywords `lahore`, `pakistan`, `riyadh`, `rawalpindi`, `indore`, or `gujrat` (case-insensitive) is automatically hidden.
- **Spam Hashtag Cleaner:** A regex script automatically chops off those massive blocks of spammy hashtags (e.g., `#StaffAugmentation #ITStaffing #Hiring...`) attached to the bottom of the posts, ensuring the UI remains clean and easy to read.

---
*These changes are live and were pushed directly to the `main` branch of the `animeshkr7/email-creator-api.git` repository.*
