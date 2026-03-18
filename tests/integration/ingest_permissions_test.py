import sqlite3

import pytest

from db.gen_tables import permission_table
from pipelines.ingest_permissions import (
    AOSP_PERMS_JSON_URL,
    fetch_permissions_from_url,
    seed_permissions,
    override_permission_severity,
)


@pytest.mark.integration
def test_fetch_permissions_from_url():
    data = fetch_permissions_from_url(AOSP_PERMS_JSON_URL)
    assert isinstance(data, dict) # check if output is a dict
    assert sorted(data.keys()) == ["groups", "permissions"] # check for expected_row keys

    # assert the exception is working
    with pytest.raises(RuntimeError):
        fetch_permissions_from_url("http://invalid.url")


@pytest.mark.integration
def test_seed_permissions(tmp_path, mock_aosp_data):
    # create a temporary permissions table
    TMP_DB_PATH = tmp_path / "test.db"
    with sqlite3.connect(TMP_DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(permission_table)
    seed_permissions(data=mock_aosp_data, db_path=TMP_DB_PATH)

    # check if the expected values were inserted
    with sqlite3.connect(TMP_DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM permission
        """)
        rows = cursor.fetchall()
    
    assert len(rows) == 1
    row = rows[0]
    assert isinstance(row[0], int) # id should be an int
    assert row[1] == "Mock Permission"  # name ('android.permission.MOCK_PERMISSION' -> 'Mock Permission')
    assert row[2] == "MOCK PERMISSION GROUP"    # category ('Mock permission group' -> 'MOCK PERMISSION GROUP')
    assert row[3] == "Mock permission for testing"  # description (as is -> 'Mock permission group for testing')
    assert row[4] == "Normal"   # severity ('signature' -> 'Normal')
    assert row[5] == None # associated_risks (TODO: not populated with anything at the moment)
    assert row[6] == "MOCK_PERMISSION"  # android_name ('android.permission.MOCK_PERMISSION' -> 'MOCK_PERMISSION')


@pytest.mark.integration
def test_override_permission_severity_update(tmp_path, mock_aosp_data, mock_override):
    """ Updates permission severity if permission exists """
    # create a temporary permissions table
    TMP_DB_PATH = tmp_path / "test.db"
    with sqlite3.connect(TMP_DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(permission_table)
    seed_permissions(data=mock_aosp_data, db_path=TMP_DB_PATH)

    # check if 'Normal' -> 'High' override worked
    override_permission_severity(db_path=TMP_DB_PATH, overrides=mock_override)
    with sqlite3.connect(TMP_DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""SELECT severity FROM permission""")
        row = cursor.fetchone()
    
    assert row[0] == "High"
