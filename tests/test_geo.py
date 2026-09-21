"""US location classifier for scraped posting location strings."""

from geo import is_us_location


def test_state_abbreviation_is_us():
    assert is_us_location("Minneapolis, MN") is True


def test_remote_us_marker_is_us():
    assert is_us_location("Remote (US)") is True


def test_united_states_in_string_is_us():
    assert is_us_location("Waukesha, Wisconsin, United States of America") is True


def test_london_is_not_us():
    assert is_us_location("London, UK") is False


def test_costa_rica_city_starting_with_la_is_not_louisiana():
    assert is_us_location("La Garita, Costa Rica") is False
