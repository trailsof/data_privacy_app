import json
import sqlite3

from utils import fetch_json_data_from_url
from constants import TRACKER_JSON_URL


def seed_trackers(
    data: dict | None = None,
    db_path: str = "data_privacy_app.db",
) -> None:
    """Populate tracker database with trackers identified by Exodus."""
    if data is None:
        data = fetch_json_data_from_url(TRACKER_JSON_URL)
    
    trackers = data.get("trackers", {})

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        seed_count = 0
        for id, info in trackers.items():
            name = info.get("name", "")
            category = json.dumps(info.get("categories", None)) # serialize list as json
            description = info.get("description", None)
            code_signature = info.get("code_signature", None)
            network_signature = info.get("network_signature", None)
            website = info.get("website", None)

            # Upsert into tracker DB
            cursor.execute(
                """
                INSERT OR IGNORE INTO tracker
                (id, name, category, description, code_signature, network_signature, website)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (id, name, category, description, code_signature, network_signature, website),
            )

            # Count successful insertion
            if cursor.rowcount > 0:
                seed_count += 1

        conn.commit()

    print(f"Done! Seeded {seed_count} master trackers.")


if __name__ == "__main__":
    data = fetch_json_data_from_url(TRACKER_JSON_URL)
    seed_trackers(data)
    print("Seeded trackers.")
