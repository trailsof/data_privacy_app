import requests
import sqlite3

# Google defined these permissions as "special". Though they don't fall under a
# "dangerous" protection level, they should be considered high risk
SPECIAL_PERMISSIONS = {
    "SYSTEM_ALERT_WINDOW": "High",
    "WRITE_SETTINGS": "High",
}

HIGH_RISK_PERMS = {
    "ACCESS_FINE_LOCATION": "High",
    "READ_CONTACTS": "High",
    "READ_SMS": "High",
    "RECORD_AUDIO": "High",
    "READ_CALL_LOG": "High",
    "READ_PHONE_NUMBERS": "High",
    "READ_PHONE_STATE": "High",
    "WRITE_EXTERNAL_STORAGE": "High",
    "GET_ACCOUNTS": "High",
    "CALL_PHONE": "High",
    "ACCESS_MEDIA_LOCATION": "High",
    "CAMERA": "High",
}

def seed_permissions(db_path='app_permissions.db'):
    # Fetching the most recent AOSP permission definitions (API 36)
    url = "https://raw.githubusercontent.com/androguard/androguard/refs/heads/master/androguard/core/api_specific_resources/aosp_permissions/permissions_36.json"   
    
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
        # Example: 'android.permission.CAMERA' -> 'CAMERA'
        android_name = full_uri.split('.')[-1]
        clean_name = android_name.replace('_', ' ').title()  # 'CAMERA' -> 'Camera'

        description = info.get('description', clean_name)
        
        group_uri = info.get('permissionGroup', '')
        group_info = groups.get(group_uri, {})

        category = group_info.get('label', '').upper() if group_info else 'OTHER'

        severity = None
        protection_level = group_info.get('protectionLevel', '')
        if 'dangerous' in protection_level:
            severity = 'High'

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
    severity if they don't existor updates them if they do.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    for android_name, severity in overrides.items():
        cursor.execute("""
            INSERT INTO permission (android_name, severity)
            VALUES (?, ?)
            ON CONFLICT(android_name) DO UPDATE SET severity = excluded.severity
        """, (android_name, severity))
        print(f'Upserted {android_name} severity to {severity}')

    conn.commit()
    conn.close()

if __name__ == "__main__":
    seed_permissions('app_permissions.db')
    override_permission_severity(
        overrides=SPECIAL_PERMISSIONS
    )