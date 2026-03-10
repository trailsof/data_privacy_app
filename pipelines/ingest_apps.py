import requests
from bs4 import BeautifulSoup
import re
import sqlite3
from google_play_scraper import app as gp_app, permissions

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
    # check if app already exists
    existing_app = cur.execute("SELECT id FROM app WHERE google_play_id = ?", (app_data["google_play_id"],)).fetchall()
    if existing_app:
        print(f"App already exists: {app_data['name']} ({app_data['google_play_id']}) - Skipping insert.")
        return

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


def link_app_permissions(conn, google_play_id):
    url = f"https://reports.exodus-privacy.eu.org/en/reports/{google_play_id}/latest/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    }
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"Failed to fetch permissions for {google_play_id} from Exodus Privacy: Status code {response.status_code}")
        return
    
    print(f"Fetched permissions page for {google_play_id} from Exodus Privacy.")
    found_perms = set(re.findall(r'\b[A-Z_]{5,}\b', response.text))
    print(f"Permissions found for {google_play_id} from Exodus Privacy: {found_perms}")
    cur = conn.cursor()
    cur.execute("SELECT id FROM app WHERE google_play_id = ?", (google_play_id,))
    app_row = cur.fetchone()
    if not app_row:
        print(f"No app found with Google Play ID: {google_play_id}")
        return
    app_id = app_row[0]
    for perm in found_perms:
        print(f"Looking up permission: {perm}")
        cur.execute("SELECT id FROM permission WHERE android_name = ?", (perm,))
        perm_row = cur.fetchone()
        if perm_row:
            permission_id = perm_row[0]
            if not permission_id:
                print(f"Permission ID not found for {perm} in master list.")
                continue
            cur.execute("""
                INSERT OR IGNORE INTO app_permission (app_id, permission_id)
                VALUES (?, ?)
            """, (app_id, permission_id))
        else:
            print(f"Permission not found in master list: {perm}")
    conn.commit()

def process_and_link_app(conn, app_name):
    google_play_id = resolve_google_play_id(app_name)

    if google_play_id:
        metadata = fetch_google_play_metadata(google_play_id)
        if metadata:
            upsert_app(conn, metadata)
            link_app_permissions(conn, google_play_id)
            print(f"Inserted/Updated: {metadata['name']} ({metadata['google_play_id']})")
        else:
            print(f"Failed to fetch metadata for {app_name}")
    else:
        print(f"Could not resolve Google Play ID for {app_name}")

def seed_apps():
    conn = get_connection()

    for category, apps in apps_to_scrape.items():
        for app_name in apps:
            print(f"Processing: {app_name} ({category})")
            process_and_link_app(conn, app_name)

    conn.close()
    print("Done populating applications.")