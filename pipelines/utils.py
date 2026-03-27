import requests


def fetch_json_data_from_url(url: str) -> dict:
    """Fetch JSON data from a URL."""
    try:
        return requests.get(url).json()
    except Exception as e:
        raise RuntimeError(f"Error fetching permissions: {e}")