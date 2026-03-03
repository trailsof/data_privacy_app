import requests
from bs4 import BeautifulSoup
import re
import sqlite3
from google_play_scraper import app as gp_app

apps_to_scrape = {
    "Social Media": ["Instagram", "TikTok", "Snapchat", "Facebook", "X (Twitter)", "Reddit", "Threads", "Pinterest"],
    "Messaging": ["WhatsApp Messenger", "Messenger", "Telegram", "WhatsApp Business", "Signal Private Messenger"],
    "AI & Productivity": ["ChatGPT", "Google Gemini", "Zoom Workplace", "Microsoft Teams"],
    "Entertainment": ["Spotify", "YouTube", "Netflix", "Tubi: Free Movies & Live TV", "Disney+"],
    "Shopping": ["Temu", "Amazon Shopping", "SHEIN", "Walmart", "eBay"],
    "Dating": ["Tinder", "Bumble", "Hinge", "Badoo", "OkCupid", "Plenty of Fish"],
    "Banking": ["Chase Mobile", "Bank of America Mobile Banking", "Wells Fargo Mobile", "Capital One Mobile", "Citibank"],
    "Health & Fitness": ["MyFitnessPal", "Headspace", "Calm", "Fitbit", "Flo Period Tracker", "Strava"]
}

def fetch_google_play_metadata(google_play_id):
    try:
        data = gp_app(google_play_id)

        return {
            "google_play_id": google_play_id,
            "name": data.get("title"),
            "category": data.get("genre"),
            "description": data.get("description"),
            "developer": data.get("developer"),
            "last_updated": data.get("updated"),
            "paid": data.get("free") is False
        }

    except Exception as e:
        print(f"Metadata fetch failed for {google_play_id}: {e}")
        return None

def resolve_google_play_id(app_name):
    clean_name = re.sub(r"\(.*?\)", "", app_name).strip()
    search_url = f"https://play.google.com/store/search?q={clean_name}&c=apps"
    
    # fake user agent to avoid being blocked by Google
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    }
    
    response = requests.get(search_url, headers=headers)
    
    if response.status_code != 200:
        print(f"Error: Status code {response.status_code}")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Look for all links that contain 'details?id='
    links = soup.find_all('a', href=re.compile(r'/store/apps/details\?id='))
    
    for link in links:
        href = link.get('href')
        # Extract the package name (the part after 'id=')
        # Example: /store/apps/details?id=com.facebook.katana
        match = re.search(r'id=([a-zA-Z0-9._]+)', href)
        if match:
            package_id = match.group(1)
            # Filter out common false positives (like Google's own utility IDs)
            if "google" not in package_id or package_id == "com.google.android.apps.translate":
                return package_id

    return None

def upsert_app(conn, app_data):
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO app (
        google_play_id,
        name,
        category,
        description,
        developer,
        last_updated,
        paid
    )
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(google_play_id) DO UPDATE SET
        name = excluded.name,
        category = excluded.category,
        description = excluded.description,
        developer = excluded.developer,
        last_updated = excluded.last_updated,
        paid = excluded.paid;
    """, (
        app_data["google_play_id"],
        app_data["name"],
        app_data["category"],
        app_data["description"],
        app_data["developer"],
        app_data["last_updated"],
        app_data["paid"]
    ))

    conn.commit()

def get_connection(db_path="app_permissions.db"):
    return sqlite3.connect(db_path)

if __name__ == "__main__":
    conn = get_connection()

    for category, apps in apps_to_scrape.items():
        for app_name in apps:
            print(f"Processing: {app_name} ({category})")
            google_play_id = resolve_google_play_id(app_name)
            if google_play_id:
                metadata = fetch_google_play_metadata(google_play_id)
                if metadata:
                    upsert_app(conn, metadata)
                    print(f"Inserted/Updated: {metadata['name']} ({metadata['google_play_id']})")
                else:
                    print(f"Failed to fetch metadata for {app_name}")
            else:
                print(f"Could not resolve Google Play ID for {app_name}")

    conn.close()
    print("Done populating applications.")