import pytest


@pytest.fixture
def mock_tracker_data():
    return {
        "trackers": {
            "1": {
                "categories": ["CategoryA"],
                "code_signature": "com.mock.tracker",
                "creation_date": "2026-01-01",
                "description": "Mock tracker for testing",
                "documentation": [],
                "id": 11,
                "name": "MockTracker1",
                "network_signature": "mocktracker\\.com",
                "website": "http://mocktracker.com",
            },
        },
    }


@pytest.fixture
def mock_aosp_data():
    return {
        "groups": {
            "android.permission-group.MOCK_PERMISSION_GROUP": {
                "description": "Mock permission group for testing",
                "description_ptr": "permgroupdesc_mockPermissionGroup",
                "icon": "",
                "icon_ptr": "",
                "label": "Mock permission group",
                "label_ptr": "permgrouplab_mockPermissionGroup",
                "name": "android.permission-group.MOCK_PERMISSION_GROUP",
            }
        },
        "permissions": {
            "android.permission.MOCK_PERMISSION": {
                "description": "Mock permission for testing",
                "description_ptr": "permdesc_mockPermission",
                "label": "Mock permission for testing",
                "label_ptr": "permlab_mockPermission",
                "name": "android.permission.MOCK_PERMISSION",
                "permissionGroup": "android.permission-group.MOCK_PERMISSION_GROUP",
                "protectionLevel": "signature",
            }
        },
    }


@pytest.fixture
def mock_override():
    return {"MOCK_PERMISSION": "High"}
