import requests
import sqlite3

def seed_master_permissions(db_path='app_permissions.db'):
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
        
        cursor.execute("""
            INSERT OR IGNORE INTO permission (name, category, description, android_name)
            VALUES (?, ?, ?, ?)
        """, (clean_name, category, description, android_name))

    conn.commit()
    print(f"Done! Seeded {len(data)} master permissions.")
    conn.close()

seed_master_permissions()