import sqlite3

import pytest

from db.gen_tables import tracker_table
from pipelines.utils import fetch_json_data_from_url
from pipelines.constants import TRACKER_JSON_URL
from pipelines.ingest_trackers import seed_trackers


@pytest.mark.integration
def test_fetch_trackers_from_url():
    data = fetch_json_data_from_url(TRACKER_JSON_URL)
    assert isinstance(data, dict)  # check if output is a dict
    assert list(data.keys()) == ["trackers"]  # should only contain 1 key

    # assert the exception is working
    with pytest.raises(RuntimeError):
        fetch_json_data_from_url("http://invalid.url")


@pytest.mark.integration
def test_seed_trackers(tmp_path, mock_tracker_data):
    # create a temporary trackers table
    TMP_DB_PATH = tmp_path / "test.db"
    with sqlite3.connect(TMP_DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(tracker_table)
    seed_trackers(data=mock_tracker_data, db_path=TMP_DB_PATH)

    # check if the expected values were inserted
    with sqlite3.connect(TMP_DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM tracker
        """)
        rows = cursor.fetchall()

    assert len(rows) == 1
    row = rows[0]
    assert isinstance(row[0], int)  # id should be an int
    assert row[1] == "MockTracker1"   # name
    assert row[2] == '["CategoryA"]'    # category
    assert row[3] == "Mock tracker for testing" # description
    assert row[4] == "com.mock.tracker" # code_signature
    assert row[5] == "mocktracker\\.com"    # network_signature
    assert row[6] == "http://mocktracker.com"   # website