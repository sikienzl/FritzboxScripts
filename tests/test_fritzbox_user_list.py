import pytest
from unittest.mock import patch
from click.testing import CliRunner
import fritzbox_user_list
import logging


@patch("fritzbox_user_list.requests.get")
def test_extract_usernames_from_html(mock_get, caplog):
    # Simulate Fritz!Box login page with activeUsers
    html = '''
    <script>
    var data = {"activeUsers":[{"value":"fritz1234"},{"value":"fritz5678"}]};
    </script>
    '''
    mock_get.return_value.status_code = 200
    mock_get.return_value.text = html

    runner = CliRunner()
    with caplog.at_level(logging.INFO):
        result = runner.invoke(fritzbox_user_list.main, ["--url", "http://dummy"])
        assert result.exit_code == 0
        assert "fritz1234" in caplog.text
        assert "fritz5678" in caplog.text
