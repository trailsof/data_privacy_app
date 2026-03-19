import sqlite3

DB_PATH = "data_privacy_app.db"

data_privacy_app_table = """
CREATE TABLE IF NOT EXISTS app (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    google_play_id TEXT UNIQUE NOT NULL, 
    name TEXT NOT NULL, 
    category TEXT, 
    description TEXT,
    developer TEXT,
    last_updated TEXT,
    paid BOOLEAN
);
"""

permission_table = """
CREATE TABLE IF NOT EXISTS permission (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    category TEXT,
    description TEXT,
    severity TEXT,
    associated_risks TEXT,
    android_name TEXT
);
"""


app_permission_table = """
CREATE TABLE IF NOT EXISTS app_permission (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    app_id INTEGER NOT NULL,
    permission_id INTEGER NOT NULL,
    FOREIGN KEY (app_id) REFERENCES app(id),
    FOREIGN KEY (permission_id) REFERENCES permission(id)
);
"""

session_table = """
CREATE TABLE IF NOT EXISTS session (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
"""

session_app_table = """
CREATE TABLE IF NOT EXISTS session_app (
    session_id INTEGER NOT NULL,
    app_id INTEGER NOT NULL,
    FOREIGN KEY (session_id) REFERENCES session(id),
    FOREIGN KEY (app_id) REFERENCES app(id),
    PRIMARY KEY (session_id, app_id)
);
"""


def create_tables():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(data_privacy_app_table)
    cursor.execute(permission_table)
    cursor.execute(app_permission_table)
    cursor.execute(session_table)
    cursor.execute(session_app_table)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    create_tables()
    print("Tables created / verified.")
