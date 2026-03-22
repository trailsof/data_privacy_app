import pytest

from pipelines.ingest_apps import fetch_google_play_metadata, resolve_google_play_id


@pytest.mark.integration
def test_fetch_google_play_metadata_succeeds_for_valid_app_id():
    # test with a known app id
    metadata = fetch_google_play_metadata("com.instagram.android")
    assert metadata is not None
    assert metadata["name"] == "Instagram"
    assert metadata["google_play_id"] == "com.instagram.android"


@pytest.mark.integration
def test_fetch_google_play_metadata_fails_for_invalid_app_id():
    # test with an invalid app id
    metadata = fetch_google_play_metadata("com.nonexistent.app")
    assert metadata is None


# cases mispelled app name :check:
# cases with a shit ton of apps, which one is picked
# case where app name is complete and app id returned
# case where app name is empty
@pytest.mark.integration
def test_resolve_google_play_id_succeeds_when_valid_name_provided():
    google_play_id = resolve_google_play_id("Instagram")
    assert google_play_id == "com.instagram.android"


# see https://github.com/trailsof/data_privacy_app/issues/7
@pytest.mark.integration
def test_resolve_google_play_id_succeeds_when_misspelled_name_provided():
    google_play_id = resolve_google_play_id("Instaggram")
    assert google_play_id == "com.instagram.android"

    facebook_id = resolve_google_play_id("Facebokk")
    assert facebook_id == "com.facebook.katana"


# this is not current behavior
# should be added when https://github.com/trailsof/data_privacy_app/issues/8 is completed
@pytest.mark.skip
def test_resolve_google_play_id_gives_list_for_multiple_app_ids():
    google_play_id = resolve_google_play_id("Google D")
    assert google_play_id is None
