# URLs
AOSP_PERMS_JSON_URL = (
    "https://raw.githubusercontent.com/androguard/androguard/"
    "refs/heads/master/androguard/core/api_specific_resources/"
    "aosp_permissions/permissions_36.json"
)

TRACKER_JSON_URL = "https://reports.exodus-privacy.eu.org/api/trackers"

# Overrides
SPECIAL_PERMISSIONS = {
    "SYSTEM_ALERT_WINDOW": "High",
    "WRITE_SETTINGS": "High",
}

# Example data
APPS_TO_SCRAPE = {
    "Social Media": [
        "Instagram",
        "TikTok",
        "Snapchat",
        "Facebook",
        "X (Twitter)",
        "Reddit",
        "Threads",
        "Pinterest",
    ],
    "Messaging": [
        "WhatsApp Messenger",
        "Messenger",
        "Telegram",
        "WhatsApp Business",
        "Signal Private Messenger",
    ],
    "AI & Productivity": [
        "ChatGPT",
        "Google Gemini",
        "Zoom Workplace",
        "Microsoft Teams",
    ],
    "Entertainment": [
        "Spotify",
        "YouTube",
        "Netflix",
        "Tubi: Free Movies & Live TV",
        "Disney+",
    ],
    "Shopping": ["Temu", "Amazon Shopping", "SHEIN", "Walmart", "eBay"],
    "Dating": ["Tinder", "Bumble", "Hinge", "Badoo", "OkCupid", "Plenty of Fish"],
    "Banking": [
        "Chase Mobile",
        "Bank of America Mobile Banking",
        "Wells Fargo Mobile",
        "Capital One Mobile",
        "Citibank",
    ],
    "Health & Fitness": [
        "MyFitnessPal",
        "Headspace",
        "Calm",
        "Fitbit",
        "Flo Period Tracker",
        "Strava",
    ],
}
