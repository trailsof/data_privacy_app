import sqlite3

import click
from flask import Flask, render_template
from flask.cli import with_appcontext

from pipelines.ingest_permissions import seed_permissions
from pipelines.ingest_apps import seed_apps

app = Flask(__name__)
DB_PATH = "data_privacy_app.db"


def register_commands(app):
    @app.cli.command("seed")
    @with_appcontext
    def seed():
        """Command to populate the database: perms then apps."""
        click.echo("🌱 Starting database seed...")

        click.echo("Step 1: Ingesting Permissions...")
        seed_permissions()

        click.echo("Step 2: Ingesting Apps & Linking Permissions...")
        seed_apps()

        click.echo("✅ Seed complete!")


# Call it immediately after app definition
register_commands(app)


def get_data(query, params=()):
    """Standard helper to handle DB connections safely."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(query, params)
    data = cur.fetchall()
    conn.close()
    return data


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/dashboard")
def dashboard():
    rows = get_data("""
        SELECT a.name, a.google_play_id, COUNT(ap.permission_id) as total,
               SUM(CASE WHEN p.severity = 'High' THEN 1 ELSE 0 END) as high
        FROM app a
        LEFT JOIN app_permission ap ON a.id = ap.app_id
        LEFT JOIN permission p ON ap.permission_id = p.id
        GROUP BY a.id ORDER BY high DESC
    """)
    return render_template("dashboard.html", rows=rows)


@app.route("/overlap")
def overlap():
    top_5 = [
        "com.openai.chatgpt",
        "com.zhiliaoapp.musically",
        "com.instagram.android",
        "com.facebook.katana",
        "com.whatsapp",
    ]
    placeholders = ",".join(["?"] * len(top_5))

    perms_rows = get_data(
        f"""
        SELECT DISTINCT p.android_name 
        FROM permission p
        JOIN app_permission ap ON p.id = ap.permission_id
        JOIN app a ON ap.app_id = a.id
        WHERE p.severity = 'High' AND a.google_play_id IN ({placeholders})
    """,
        top_5,
    )

    apps = get_data(
        f"SELECT name, google_play_id FROM app WHERE google_play_id IN ({placeholders})",
        top_5,
    )

    links = get_data(
        f"""
        SELECT a.google_play_id, p.android_name 
        FROM app_permission ap
        JOIN app a ON ap.app_id = a.id
        JOIN permission p ON ap.permission_id = p.id
        WHERE a.google_play_id IN ({placeholders})
    """,
        top_5,
    )

    ownership = {f"{link['google_play_id']}|{link['android_name']}" for link in links}
    return render_template(
        "overlap.html", perms=perms_rows, apps=apps, ownership=ownership
    )
