# Data Privacy App

This application shows all the permissions granted to a set of Android mobile apps.

## Database
<p align="center">
  <img width="50%" alt="image" src="https://github.com/user-attachments/assets/6b8f2405-446f-4872-8b7c-da8abf8ab4da" />
</p>

## Overview

This repository collects Android app permission data (from Google Play Scraper and AOSP definitions), seeds a normalized SQLite permissions database, and runs a lightweight Flask dashboard to inspect apps and high-risk permission overlaps.

<img width="970" height="518" alt="image" src="https://github.com/user-attachments/assets/0342bfec-6685-435a-a2a6-b0277fd68d60" />


Key capabilities:
- Fetch app IDs and permissions from Google Play 
- Seed master Android permission definitions (AOSP) into a local SQLite DB.
- Serve a dashboard that ranks apps by high-severity permissions and shows permission overlap.


## Repository layout

- `data_privacy_app/`
  - `db/gen_tables.py` — creates the SQLite schema (`app`, `permission`, `app_permission`, `session`, `session_app`).
  - `pipelines/ingest_permissions.py` — downloads AOSP permission metadata and seeds `permission` table; provides a manual high-severity override.
  - `scripts/fetch_google_play_perms.py` — example script using `google_play_scraper` to resolve app IDs and fetch permissions (saves `google_play_permissions.csv`).
  - `web_app/common_app_dashboard.py` — Flask app serving the dashboard and overlap pages using templates in `web_app/templates/`.
  - `web_app/templates/` — HTML templates for the dashboard and overlap views.
  - `data/` — place for CSVs and other ingest artifacts (e.g., `google_play_permissions.csv`).

Other top-level folders in the workspace include ingestion helpers, tests, and notebooks for exploration.

## Setup


Install required packages (suggested):

```bash
pip install flask requests pandas google-play-scraper
```


## Database initialization

1. From `data_privacy_app/`, create the SQLite database and tables:

```bash
python db/gen_tables.py
```

This creates `data_privacy_app.db` (in the working directory) and the schema used by the app and pipelines.

## Seeding master permissions

Run the permissions seeding script to populate the `permission` table with AOSP permission metadata:

```bash
python pipelines/ingest_permissions.py
```

## Ingesting app permissions (example)

Use the example script in `data_privacy_app/scripts/fetch_google_play_perms.py` to look up app IDs by name and fetch their Play Store permissions. Example run:


## Running the dashboard

Start the Flask app (development mode):

```bash
python web_app/common_app_dashboard.py
```

Open `http://127.0.0.1:5000/dashboard` to view the app ranking and `http://127.0.0.1:5000/overlap` for permission overlap visualizations. The dashboard expects `app_permissions.db` to exist and be populated with `app`, `permission`, and `app_permission` data.

## Notes & next steps
- Run db scripts with `flask seed` by registering ingest code with flask
- Setup docker, create a Dockerfile and `docker-compose.yaml` to package the app, SQLite DB and templates.
- Upload app to an EC2 instance
- Add unit/integration tests around ingestion and the Flask routes
