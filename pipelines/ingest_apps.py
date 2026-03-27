import re
import sqlite3

import requests
from bs4 import BeautifulSoup
from google_play_scraper import app as gp_app

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


def get_connection(db_path: str = "data_privacy_app.db") -> sqlite3.Connection:
    """Intialize and return a SQLite connection to the DB."""
    return sqlite3.connect(db_path)


def fetch_google_play_metadata(google_play_id: str) -> dict | None:
    """Use google_play_scraper to get an app's metadata."""
    try:
        data = gp_app(google_play_id)

        return {
            "google_play_id": google_play_id,
            "name": data.get("title"),
            "category": data.get("genre"),
            "description": data.get("description"),
            "developer": data.get("developer"),
            "last_updated": data.get("updated"),
            "paid": data.get("free") is False,
        }

    except Exception as e:
        print(f"Metadata fetch failed for {google_play_id}: {e}")
        return None


def resolve_google_play_id(app_name: str) -> str | None:
    """Use Google App Store's search engine to resolve name of app into its Google Play ID."""
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

    soup = BeautifulSoup(response.text, "html.parser")

    # Look for all links that contain 'details?id='
    links = soup.find_all("a", href=re.compile(r"/store/apps/details\?id="))

    for link in links:
        href = link.get("href")
        # Extract the package name (the part after 'id=')
        # Example: /store/apps/details?id=com.facebook.katana
        match = re.search(r"id=([a-zA-Z0-9._]+)", href)
        if match:
            package_id = match.group(1)
            # Filter out common false positives (like Google's own utility IDs)
            if (
                "google" not in package_id
                or package_id == "com.google.android.apps.translate"
            ):
                return package_id

    return None


def upsert_app(conn: sqlite3.Connection, app_data: dict) -> None:
    """Insert app into the app table, if it doesn't already exist."""
    cur = conn.cursor()
    # check if app already exists
    existing_app = cur.execute(
        "SELECT id FROM app WHERE google_play_id = ?", (app_data["google_play_id"],)
    ).fetchall()
    if existing_app:
        print(
            f"App already exists: {app_data['name']} ({app_data['google_play_id']}) - Skipping insert."
        )
        return

    cur.execute(
        """
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
    """,
        (
            app_data["google_play_id"],
            app_data["name"],
            app_data["category"],
            app_data["description"],
            app_data["developer"],
            app_data["last_updated"],
            app_data["paid"],
        ),
    )

    conn.commit()


def fetch_exodus_page_text(google_play_id: str) -> str | None:
    """Without Exodus's API, retrieve app's info from their web page."""
    url = f"https://reports.exodus-privacy.eu.org/en/reports/{google_play_id}/latest/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(
            f"Failed to fetch permissions for {google_play_id} from Exodus Privacy: Status code {response.status_code}"
        )
        return None
    return response.text


def insert_app_permissions(
    conn: sqlite3.Connection, app_id: int, perms: set[str]
) -> None:
    """Link a set of permissions to an app in the app_permission table."""
    cur = conn.cursor()
    for perm in perms:
        cur.execute("SELECT id FROM permission WHERE android_name = ?", (perm,))
        perm_row = cur.fetchone()
        if perm_row:
            cur.execute(
                "INSERT OR IGNORE INTO app_permission (app_id, permission_id) VALUES (?, ?)",
                (app_id, perm_row[0]),
            )
        else:
            print(f"Permission not found in master list: {perm}")


def insert_app_trackers(
    conn: sqlite3.Connection, app_id: int, tracker_ids: set[int]
) -> None:
    """Link a set of tracker IDs to an app in the app_tracker table."""
    cur = conn.cursor()
    for tracker_id in tracker_ids:
        cur.execute("SELECT id FROM tracker WHERE id = ?", (tracker_id,))
        tracker_row = cur.fetchone()
        if tracker_row:
            cur.execute(
                "INSERT OR IGNORE INTO app_tracker (app_id, tracker_id) VALUES (?, ?)",
                (app_id, tracker_id),
            )
        else:
            print(f"Tracker ID {tracker_id} not found in DB")


def link_app_permissions_and_trackers(
    conn: sqlite3.Connection, google_play_id: str
) -> None:
    """Fetch permissions and tracker data for a given app from Exodus and insert into `app_permission` and `app_tracker` tables, respectively."""
    cur = conn.cursor()

    # Check if app exists in app table
    cur.execute("SELECT id FROM app WHERE google_play_id = ?", (google_play_id,))
    app_row = cur.fetchone()
    if not app_row:
        print(f"No app found with Google Play ID: {google_play_id}")
        return
    app_id = app_row[0]

    # Parse permissions and tracker data from Exodus
    page_text = fetch_exodus_page_text(google_play_id)
    if not page_text:
        print(f"Unable to fetch page for {google_play_id} from Exodus Privacy.")
        return

    perms = set(re.findall(r'android\.permission\.([^"]+)"', page_text))
    tracker_ids = set(
        int(id) for id in re.findall(r'href="/en/trackers/(\d+)/"', page_text)
    )
    print(f"Found {len(perms)} permissions and {len(tracker_ids)} trackers.")

    # Insert into tables
    insert_app_permissions(conn, app_id, perms)
    insert_app_trackers(conn, app_id, tracker_ids)
    conn.commit()


def process_and_link_app(conn, app_name):
    google_play_id = resolve_google_play_id(app_name)

    if google_play_id:
        metadata = fetch_google_play_metadata(google_play_id)
        if metadata:
            upsert_app(conn, metadata)
            link_app_permissions_and_trackers(conn, google_play_id)
            print(
                f"Inserted/Updated: {metadata['name']} ({metadata['google_play_id']})"
            )
        else:
            print(f"Failed to fetch metadata for {app_name}")
    else:
        print(f"Could not resolve Google Play ID for {app_name}")


def seed_apps(apps: list[str] | None = None) -> None:
    """Seed the database with metadata and permissions data for a list of apps."""
    conn = get_connection()

    if apps is None:
        apps = [app for app_list in APPS_TO_SCRAPE.values() for app in app_list]

    for app_name in apps:
        print(f"Processing: {app_name}")
        process_and_link_app(conn, app_name)

    conn.close()
    print("Done populating applications.")
