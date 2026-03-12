from google_play_scraper import permissions, search
import pandas as pd
import time

def get_app_id(app_name: str, country: str = 'us', lang: str = 'en') -> str | None:
    """
    Search Google Play by app name and return the top matching package ID.
    e.g. 'instagram' -> 'com.instagram.android'
    """
    results = search(query=app_name, n_hits=1, lang=lang, country=country)
    print(f"Search results for '{app_name}': {results}")
    if not results:
        return None
    
    return results[0]['appId']

def get_permissions(app_ids):
    all_rows = []
    for app_id in app_ids:
        try:
            print(f"Fetching permissions for {app_id}...")
            perms_dict = permissions(app_id=app_id, lang='en', country='us')
            if not perms_dict:
                print(f"No permissions found for {app_id}.")
                continue
            for category, perms in perms_dict.items():
                for perm in perms:
                    all_rows.append({
                        'app_id': app_id,
                        'category': category,
                        'permission': perm
                    })
            time.sleep(1)  # Sleep to avoid hitting rate limits
        except Exception as e:
            print(f"Error fetching permissions for {app_id}: {e}")

    return pd.DataFrame(all_rows)

if __name__ == "__main__":
    
    #app_ids = ['com.instagram.android', 'com.facebook.katana', 'com.whatsapp']
    app_ids = [
        get_app_id('instagram'),
        get_app_id('facebook'),
        get_app_id('whatsapp')
    ]   
    print(f"App IDs: {app_ids}")
    permissions_data = get_permissions(app_ids)
    permissions_data.to_csv('google_play_permissions.csv', index=False)
    print("Permissions data saved to google_play_permissions.csv")