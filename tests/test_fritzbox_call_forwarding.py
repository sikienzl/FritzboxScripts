import pytest
from unittest.mock import patch, MagicMock
import fritzbox_call_forwarding


@patch("fritzbox_call_forwarding.requests.Session")
def test_get_sid_success(mock_session):
    # Simulate successful SID response
    mock_instance = MagicMock()
    mock_session.return_value = mock_instance
    mock_instance.get.return_value.text = (
        "<SessionInfo><SID>1234567890123456</SID><Challenge>dummy</Challenge></SessionInfo>"
    )
    sid, session = fritzbox_call_forwarding.get_sid()
    assert sid == "1234567890123456"
    assert session is not None


@patch("fritzbox_call_forwarding.requests.Session")
def test_get_sid_failure(mock_session):
    # Simulate failed SID response
    mock_instance = MagicMock()
    mock_session.return_value = mock_instance
    mock_instance.get.return_value.text = (
        "<SessionInfo><SID>0000000000000000</SID><Challenge>dummy</Challenge></SessionInfo>"
    )
    sid, session = fritzbox_call_forwarding.get_sid()
    assert sid is None
    assert session is None
