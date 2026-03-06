import requests
import sqlite3

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

def mark_high_severity_permissions(db_path='app_permissions.db'):
    # TODO: This is a manual override and should be used only for system permissions
    high_risk_perms = {
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

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    for android_name, severity in high_risk_perms.items():
        cursor.execute("""
            UPDATE permission
            SET severity = ?
            WHERE android_name = ?
        """, (severity, android_name))

    conn.commit()
    print("Marked high severity permissions.")
    conn.close()

if __name__ == "__main__":
    seed_permissions('app_permissions.db')