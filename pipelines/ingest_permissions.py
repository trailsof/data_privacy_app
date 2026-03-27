import sqlite3

import requests

# Google defined these permissions as "special". Though they don't fall under a
# "dangerous" protection level, they should be considered high risk
SPECIAL_PERMISSIONS = {
    "SYSTEM_ALERT_WINDOW": "High",
    "WRITE_SETTINGS": "High",
}

AOSP_PERMS_JSON_URL = (
    "https://raw.githubusercontent.com/androguard/androguard/"
    "refs/heads/master/androguard/core/api_specific_resources/"
    "aosp_permissions/permissions_36.json"
)

TRACKER_JSON_URL = "https://reports.exodus-privacy.eu.org/api/trackers"


def fetch_json_data_from_url(url: str) -> dict:
    """Fetch JSON data from a URL."""
    try:
        return requests.get(url).json()
    except Exception as e:
        raise RuntimeError(f"Error fetching permissions: {e}")

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
            category = info.get("categories", None)
            description = info.get("description", None)
            code_signature = info.get("code_signature", None)
            network_signature = info.get("network_signature", None)
            website = info.get("website", None)

            # Upsert into tracker DB
            cursor.execute(
                """
                INSERT OR IGNORE INTO tracker
                (id, name, category, description, code_signature, network_signature, website)
                VALUES (?, ?, ?, ?, ?)
            """,
                (id, name, category, description, code_signature, network_signature, website),
            )

            # Count successful insertion
            if cursor.rowcount > 0:
                seed_count += 1

        conn.commit()

    print(f"Done! Seeded {seed_count} master trackers.")

def seed_permissions(
    data: dict | None = None,
    db_path: str = "data_privacy_app.db",
) -> None:
    """
    Populate permissions database with AOSP permissions (API 36),
    defined by androguard, and used by Exodus.
    """
    if data is None:
        data = fetch_json_data_from_url(AOSP_PERMS_JSON_URL)

    groups = data.get("groups", {})
    perms = data.get("permissions", {})

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        seed_count = 0
        for full_uri, info in perms.items():
            # Get clean name from android name
            # Example: 'android.permission.CAMERA' -> 'CAMERA' -> 'Camera'
            android_name = full_uri.split(".")[-1]
            clean_name = android_name.replace("_", " ").title()

            # Get permission description
            description = info.get("description", clean_name)

            # Get permission group category
            group_uri = info.get("permissionGroup", "")
            group_info = groups.get(group_uri, {})
            category = group_info.get("label", "").upper() if group_info else "OTHER"

            # Get severity from protection level
            protection_level = info.get("protectionLevel", "")
            if protection_level == "":
                severity = "Unknown"
            elif "dangerous" in protection_level:
                severity = "High"
            else:
                severity = "Normal"

            # Upsert into permission DB
            cursor.execute(
                """
                INSERT OR IGNORE INTO permission (name, category, description, android_name, severity)
                VALUES (?, ?, ?, ?, ?)
            """,
                (clean_name, category, description, android_name, severity),
            )

            # Count successful insertion
            if cursor.rowcount > 0:
                seed_count += 1

        conn.commit()

    print(f"Done! Seeded {seed_count} master permissions.")


def override_permission_severity(
    db_path: str = "data_privacy_app.db",
    overrides: dict = SPECIAL_PERMISSIONS,
) -> None:
    """Overrides existing permission's severity."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    for android_name, severity in overrides.items():
        # Check if permission exists
        cursor.execute(
            """
            SELECT id, severity FROM permission WHERE android_name = ?
        """,
            (android_name,),
        )
        row = cursor.fetchone()

        if not row:
            print(
                f"Warning: Permission '{android_name}' not found in database. Skipping."
            )
            continue
        else:
            original_severity = row[1]
            if original_severity == severity:
                print(
                    f"Permission '{android_name}' with severity '{severity}' already exists. Skipping"
                )
                continue
            cursor.execute(
                """
                UPDATE permission SET severity = ? WHERE id = ?
            """,
                (severity, row[0]),
            )
            print(
                f"Updated '{android_name}' severity from '{original_severity}' to '{severity}'"
            )

    conn.commit()
    conn.close()
