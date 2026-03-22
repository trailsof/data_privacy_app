# hey we want to load our data from the API, not from a file
import sqlite3
from flask import Flask, render_template

app = Flask(__name__)
DB_PATH = "data_privacy_app.db"

def get_data(query, params=()):
    """Standard helper to handle DB connections safely."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(query, params)
    data = cur.fetchall()
    conn.close()
    return data


# just add a test we can make an api route

@app.route("api/test", methods=["GET"])
def test():
    return {"message": "Hello, World!"}

# lets create a route to get all apps and their permissions, ordered by number of high severity perms
@app.route("/api/apps", methods=["GET"])
def get_apps():
    rows = get_data("""
        SELECT a.name, a.google_play_id, COUNT(ap.permission_id) as total,
               SUM(CASE WHEN p.severity = 'High' THEN 1 ELSE 0 END) as high
        FROM app a
        LEFT JOIN app_permission ap ON a.id = ap.app_id
        LEFT JOIN permission p ON ap.permission_id = p.id
        GROUP BY a.id ORDER BY high DESC
    """)
    return {"apps": [dict(row) for row in rows]}

# lets look at the pros and cons
# pros: - a user could fetch all applications easily with a single API call
# - user could say `GET /api/apps?min_high=50` to filter to only apps with 50 or more high severity permissions
# - an extra layer to filter data, like a user could add an app with POST /api/apps rather than directly accessing our db
# - its more standard practices to have an API route for data retrieval, and it decouples the data access from the presentation layer (the dashboard)
# - user friendly feedback for success and error states

# cons
# - adds complextity, another thing that could break
# - currently were using sqlite so we cant write to db, so a post route wouldnt work without changing our db
# - our app is really simple there would only be 2 routes /app /permissions 

# first: develop the app to have tracker data
# second: allow users to write data, user aggregation logic (sqlite -> postgres)
# third: add more complex queries and an api
