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

def seed_permissions(
    db_path: str = 'app_permissions.db',
    url: str = AOSP_PERMS_JSON_URL
) -> None:
    """
    Fetch and population permissions database with existing AOSP permissions (API 36),
    defined by androguard (used by Exodus).
    """
    try:
        data = requests.get(url).json()
    except Exception as e:
        print(f"Error fetching permissions: {e}")
        return

    groups = data.get('groups', {})
    perms = data.get('permissions', {})

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    for full_uri, info in perms.items():
        # Get clean name from android name
        # Example: 'android.permission.CAMERA' -> 'CAMERA' -> 'Camera'
        android_name = full_uri.split('.')[-1]
        clean_name = android_name.replace('_', ' ').title()

        # Get permission description
        description = info.get('description', clean_name)

        # Get permission group category
        group_uri = info.get('permissionGroup', '')
        group_info = groups.get(group_uri, {})
        category = group_info.get('label', '').upper() if group_info else 'OTHER'
        
        # Get severity from protection level
        severity = None
        protection_level = info.get('protectionLevel', '')
        if 'dangerous' in protection_level:
            severity = 'High'
        else:
            severity = 'Normal'

        # Upsert into permission DB
        cursor.execute("""
            INSERT OR IGNORE INTO permission (name, category, description, android_name, severity)
            VALUES (?, ?, ?, ?, ?)
        """, (clean_name, category, description, android_name, severity))

    conn.commit()
    print(f"Done! Seeded {len(data)} master permissions.")
    conn.close()


def override_permission_severity(
    db_path: str = 'app_permissions.db',
    overrides: dict = SPECIAL_PERMISSIONS,
) -> None:
    """
    Upserts permission severity overrides. Inserts permissions and their
    severity if they don't exist or updates them if they do.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    for android_name, severity in overrides.items():
        # Check if permission exists
        cursor.execute("""
            SELECT id, severity FROM permission WHERE android_name = ?
        """, (android_name,))
        row = cursor.fetchone()

        # If it exists, get its ID and update its severity
        if row:
            original_severity = row[1]
            cursor.execute("""
                UPDATE permission SET severity = ? WHERE id = ?
            """, (severity, row[0]))
            print(f'Updated {android_name} severity from {original_severity} to {severity}')
        # Insert if it doesn't exist
        else:
            cursor.execute("""
                INSERT INTO permission (android_name, severity) VALUES (?, ?)
            """, (android_name, severity))
            print(f'Inserted {android_name} with severity {severity}')

    conn.commit()
    conn.close()

if __name__ == "__main__":
    # Populate permission DB
    seed_permissions('app_permissions.db')

    # Override with special permissions
    print(f"Applying {len(SPECIAL_PERMISSIONS)} permission overrides...")
    override_permission_severity(
        overrides=SPECIAL_PERMISSIONS
    )