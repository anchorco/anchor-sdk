"""Tests for HTTP client utilities."""

import pytest
from unittest.mock import Mock, patch
from requests.exceptions import Timeout, ConnectionError

from anchor.config import Config
from anchor._http import HttpClient
from anchor.exceptions import (
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ValidationError,
    RateLimitError,
    ServerError,
    NetworkError,
    PolicyViolationError,
)


class TestHttpClient:
    """Tests for HttpClient class."""

    @pytest.fixture
    def config(self):
        """Create a test config."""
        return Config(
            api_key="anc_test_key",
            base_url="https://api.getanchor.dev",
            timeout=30.0,
            retry_attempts=3,
            retry_delay=0.1,
        )

    @pytest.fixture
    def config_with_workspace(self):
        """Create a test config with workspace_id."""
        return Config(
            api_key="anc_test_key",
            workspace_id="workspace-123",
            base_url="https://api.getanchor.dev",
            timeout=30.0,
            retry_attempts=3,
            retry_delay=0.1,
        )

    @pytest.fixture
    def http_client_with_workspace(self, config_with_workspace):
        """Create an HttpClient instance with workspace_id."""
        return HttpClient(config_with_workspace)

    @pytest.fixture
    def http_client(self, config):
        """Create an HttpClient instance."""
        return HttpClient(config)

    def test_initialization(self, http_client, config):
        """Test HttpClient initialization."""
        assert http_client.config == config
        assert http_client.session is not None
        assert http_client.session.headers["X-API-Key"] == "anc_test_key"
        assert http_client.session.headers["User-Agent"] == "anchorai-python/1.0.2"

    def test_request_success(self, http_client):
        """Test successful HTTP request."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.content = b'{"result": "success"}'
        mock_response.json.return_value = {"result": "success"}

        with patch.object(http_client.session, "request", return_value=mock_response):
            result = http_client.request("GET", "/v1/test")
            assert result == {"result": "success"}

    def test_request_empty_response(self, http_client):
        """Test request with empty response."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.content = b""

        with patch.object(http_client.session, "request", return_value=mock_response):
            result = http_client.request("GET", "/v1/test")
            assert result == {}

    def test_request_with_data(self, http_client):
        """Test request with JSON data."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.content = b'{"id": "123"}'
        mock_response.json.return_value = {"id": "123"}

        with patch.object(http_client.session, "request", return_value=mock_response):
            result = http_client.request("POST", "/v1/test", data={"name": "test"})
            assert result == {"id": "123"}
            # Verify JSON was sent
            http_client.session.request.assert_called_once()
            call_kwargs = http_client.session.request.call_args[1]
            assert call_kwargs["json"] == {"name": "test"}

    def test_request_with_params(self, http_client):
        """Test request with query parameters."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.content = b'{"items": []}'
        mock_response.json.return_value = {"items": []}

        with patch.object(http_client.session, "request", return_value=mock_response):
            result = http_client.request("GET", "/v1/test", params={"limit": 10})
            assert result == {"items": []}
            # Verify params were sent
            http_client.session.request.assert_called_once()
            call_kwargs = http_client.session.request.call_args[1]
            assert call_kwargs["params"] == {"limit": 10}

    def test_handle_error_400_validation(self, http_client):
        """Test handling 400 ValidationError."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "message": "Invalid input",
            "field": "name",
        }
        mock_response.text = "Invalid input"

        with pytest.raises(ValidationError) as exc_info:
            http_client._handle_error(mock_response)
        assert exc_info.value.message == "Invalid input"
        assert exc_info.value.field == "name"

    def test_handle_error_401_authentication(self, http_client):
        """Test handling 401 AuthenticationError."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"message": "Invalid API key"}
        mock_response.text = "Invalid API key"

        with pytest.raises(AuthenticationError) as exc_info:
            http_client._handle_error(mock_response)
        assert exc_info.value.message == "Invalid API key"

    def test_handle_error_403_authorization(self, http_client):
        """Test handling 403 AuthorizationError."""
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.json.return_value = {
            "message": "Permission denied",
            "required_permission": "write:data",
        }
        mock_response.text = "Permission denied"

        with pytest.raises(AuthorizationError) as exc_info:
            http_client._handle_error(mock_response)
        assert exc_info.value.message == "Permission denied"
        assert exc_info.value.required_permission == "write:data"

    def test_handle_error_404_not_found(self, http_client):
        """Test handling 404 NotFoundError."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"message": "Resource not found"}
        mock_response.text = "Resource not found"

        with pytest.raises(NotFoundError) as exc_info:
            http_client._handle_error(mock_response)
        assert exc_info.value.message == "Resource not found"

    def test_handle_error_429_rate_limit(self, http_client):
        """Test handling 429 RateLimitError."""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.json.return_value = {
            "message": "Rate limit exceeded",
            "retry_after": 60,
        }
        mock_response.text = "Rate limit exceeded"

        with pytest.raises(RateLimitError) as exc_info:
            http_client._handle_error(mock_response)
        assert exc_info.value.message == "Rate limit exceeded"
        assert exc_info.value.retry_after == 60

    def test_handle_error_500_server_error(self, http_client):
        """Test handling 500 ServerError."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"message": "Internal server error"}
        mock_response.text = "Internal server error"

        with pytest.raises(ServerError) as exc_info:
            http_client._handle_error(mock_response)
        assert exc_info.value.message == "Internal server error"

    def test_handle_error_policy_violation(self, http_client):
        """Test handling policy violation error."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "message": "Blocked by policy",
            "blocked_by": "pii_filter",
        }
        mock_response.text = "Blocked by policy"

        with pytest.raises(PolicyViolationError) as exc_info:
            http_client._handle_error(mock_response)
        assert exc_info.value.message == "Blocked by policy"
        assert exc_info.value.policy_name == "pii_filter"

    def test_handle_error_invalid_json(self, http_client):
        """Test handling error with invalid JSON response."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.text = "Server error"

        with pytest.raises(ServerError) as exc_info:
            http_client._handle_error(mock_response)
        assert "Server error" in exc_info.value.message

    def test_retry_on_server_error(self, http_client):
        """Test retry logic on server errors."""
        mock_response_fail = Mock()
        mock_response_fail.ok = False
        mock_response_fail.status_code = 500
        mock_response_fail.json.return_value = {"message": "Server error"}
        mock_response_fail.text = "Server error"

        mock_response_success = Mock()
        mock_response_success.ok = True
        mock_response_success.status_code = 200
        mock_response_success.content = b'{"result": "success"}'
        mock_response_success.json.return_value = {"result": "success"}

        with patch.object(
            http_client.session,
            "request",
            side_effect=[mock_response_fail, mock_response_success],
        ), patch("time.sleep"):  # Don't actually sleep in tests
            result = http_client.request("GET", "/v1/test")
            assert result == {"result": "success"}
            assert http_client.session.request.call_count == 2

    def test_retry_on_timeout(self, http_client):
        """Test retry logic on timeout."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.content = b'{"result": "success"}'
        mock_response.json.return_value = {"result": "success"}

        with patch.object(
            http_client.session,
            "request",
            side_effect=[Timeout("Request timeout"), mock_response],
        ), patch("time.sleep"):  # Don't actually sleep in tests
            result = http_client.request("GET", "/v1/test")
            assert result == {"result": "success"}
            assert http_client.session.request.call_count == 2

    def test_retry_on_connection_error(self, http_client):
        """Test retry logic on connection error."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.content = b'{"result": "success"}'
        mock_response.json.return_value = {"result": "success"}

        with patch.object(
            http_client.session,
            "request",
            side_effect=[ConnectionError("Connection failed"), mock_response],
        ), patch("time.sleep"):  # Don't actually sleep in tests
            result = http_client.request("GET", "/v1/test")
            assert result == {"result": "success"}
            assert http_client.session.request.call_count == 2

    def test_no_retry_on_client_error(self, http_client):
        """Test that 4xx errors (except 429) don't retry."""
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 400
        mock_response.json.return_value = {"message": "Bad request"}
        mock_response.text = "Bad request"

        with patch.object(http_client.session, "request", return_value=mock_response):
            with pytest.raises(ValidationError):
                http_client.request("GET", "/v1/test")
            # Should not retry on 400
            assert http_client.session.request.call_count == 1

    def test_retry_on_429_rate_limit(self, http_client):
        """Test that 429 errors do retry."""
        mock_response_fail = Mock()
        mock_response_fail.ok = False
        mock_response_fail.status_code = 429
        mock_response_fail.json.return_value = {
            "message": "Rate limit",
            "retry_after": 1,
        }
        mock_response_fail.text = "Rate limit"

        mock_response_success = Mock()
        mock_response_success.ok = True
        mock_response_success.status_code = 200
        mock_response_success.content = b'{"result": "success"}'
        mock_response_success.json.return_value = {"result": "success"}

        with patch.object(
            http_client.session,
            "request",
            side_effect=[mock_response_fail, mock_response_success],
        ), patch("time.sleep"):  # Don't actually sleep in tests
            result = http_client.request("GET", "/v1/test")
            assert result == {"result": "success"}
            assert http_client.session.request.call_count == 2

    def test_max_retries_exceeded(self, http_client):
        """Test that NetworkError is raised after max retries."""
        with patch.object(
            http_client.session,
            "request",
            side_effect=ConnectionError("Connection failed"),
        ), patch("time.sleep"):  # Don't actually sleep in tests
            with pytest.raises(NetworkError) as exc_info:
                http_client.request("GET", "/v1/test")
            assert "Connection error" in str(exc_info.value)
            # Should retry 3 times (retry_attempts=3) + initial attempt = 4 total
            assert http_client.session.request.call_count == 4

    def test_exponential_backoff(self, http_client):
        """Test that exponential backoff is used."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.content = b'{"result": "success"}'
        mock_response.json.return_value = {"result": "success"}

        with patch.object(
            http_client.session,
            "request",
            side_effect=[ConnectionError("Connection failed"), mock_response],
        ), patch("time.sleep") as mock_sleep:
            http_client.request("GET", "/v1/test")
            # Should sleep with exponential backoff: retry_delay * (2^attempt)
            # First retry: 0.1 * (2^0) = 0.1
            mock_sleep.assert_called_once_with(0.1)

    def test_get_method(self, http_client):
        """Test GET convenience method."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.content = b'{"result": "success"}'
        mock_response.json.return_value = {"result": "success"}

        with patch.object(http_client.session, "request", return_value=mock_response):
            result = http_client.get("/v1/test", params={"limit": 10})
            assert result == {"result": "success"}
            http_client.session.request.assert_called_once_with(
                "GET",
                "https://api.getanchor.dev/v1/test",
                json=None,
                params={"limit": 10},
                timeout=30.0,
                verify=True,
            )

    def test_post_method(self, http_client):
        """Test POST convenience method."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.content = b'{"id": "123"}'
        mock_response.json.return_value = {"id": "123"}

        with patch.object(http_client.session, "request", return_value=mock_response):
            result = http_client.post("/v1/test", data={"name": "test"})
            assert result == {"id": "123"}
            http_client.session.request.assert_called_once_with(
                "POST",
                "https://api.getanchor.dev/v1/test",
                json={"name": "test"},
                params=None,
                timeout=30.0,
                verify=True,
            )

    def test_put_method(self, http_client):
        """Test PUT convenience method."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.content = b'{"updated": true}'
        mock_response.json.return_value = {"updated": True}

        with patch.object(http_client.session, "request", return_value=mock_response):
            result = http_client.put("/v1/test", data={"name": "updated"})
            assert result == {"updated": True}

    def test_patch_method(self, http_client):
        """Test PATCH convenience method."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.content = b'{"patched": true}'
        mock_response.json.return_value = {"patched": True}

        with patch.object(http_client.session, "request", return_value=mock_response):
            result = http_client.patch("/v1/test", data={"name": "patched"})
            assert result == {"patched": True}

    def test_delete_method(self, http_client):
        """Test DELETE convenience method."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.content = b'{"deleted": true}'
        mock_response.json.return_value = {"deleted": True}

        with patch.object(http_client.session, "request", return_value=mock_response):
            result = http_client.delete("/v1/test")
            assert result == {"deleted": True}


class TestHttpClientWorkspaceId:
    """Tests for workspace_id functionality in HttpClient."""

    @pytest.fixture
    def config_with_workspace(self):
        """Create a test config with workspace_id."""
        return Config(
            api_key="anc_test_key",
            workspace_id="workspace-123",
            base_url="https://api.getanchor.dev",
        )

    @pytest.fixture
    def config_without_workspace(self):
        """Create a test config without workspace_id."""
        return Config(
            api_key="anc_test_key",
            base_url="https://api.getanchor.dev",
        )

    @pytest.fixture
    def http_client_with_workspace(self, config_with_workspace):
        """Create an HttpClient instance with workspace_id."""
        return HttpClient(config_with_workspace)

    @pytest.fixture
    def http_client_without_workspace(self, config_without_workspace):
        """Create an HttpClient instance without workspace_id."""
        return HttpClient(config_without_workspace)

    def test_post_includes_workspace_id_in_body(self, http_client_with_workspace):
        """Test that POST requests include workspaceId in body."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.content = b'{"id": "123"}'
        mock_response.json.return_value = {"id": "123"}

        with patch.object(http_client_with_workspace.session, "request", return_value=mock_response):
            http_client_with_workspace.post("/v1/test", data={"name": "test"})
            call_args = http_client_with_workspace.session.request.call_args
            assert call_args[0][0] == "POST"
            assert "workspaceId" in call_args[1]["json"]
            assert call_args[1]["json"]["workspaceId"] == "workspace-123"
            assert call_args[1]["json"]["name"] == "test"

    def test_get_includes_workspace_id_in_params(self, http_client_with_workspace):
        """Test that GET requests include workspaceId in query params."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.content = b'{"result": "success"}'
        mock_response.json.return_value = {"result": "success"}

        with patch.object(http_client_with_workspace.session, "request", return_value=mock_response):
            http_client_with_workspace.get("/v1/test", params={"limit": 10})
            call_args = http_client_with_workspace.session.request.call_args
            assert call_args[0][0] == "GET"
            assert "workspaceId" in call_args[1]["params"]
            assert call_args[1]["params"]["workspaceId"] == "workspace-123"
            assert call_args[1]["params"]["limit"] == 10

    def test_put_includes_workspace_id_in_body(self, http_client_with_workspace):
        """Test that PUT requests include workspaceId in body."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.content = b'{"updated": true}'
        mock_response.json.return_value = {"updated": True}

        with patch.object(http_client_with_workspace.session, "request", return_value=mock_response):
            http_client_with_workspace.put("/v1/test", data={"name": "updated"})
            call_args = http_client_with_workspace.session.request.call_args
            assert "workspaceId" in call_args[1]["json"]
            assert call_args[1]["json"]["workspaceId"] == "workspace-123"

    def test_delete_includes_workspace_id_in_params(self, http_client_with_workspace):
        """Test that DELETE requests include workspaceId in query params."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.content = b'{"deleted": true}'
        mock_response.json.return_value = {"deleted": True}

        with patch.object(http_client_with_workspace.session, "request", return_value=mock_response):
            http_client_with_workspace.delete("/v1/test")
            call_args = http_client_with_workspace.session.request.call_args
            assert "workspaceId" in call_args[1]["params"]
            assert call_args[1]["params"]["workspaceId"] == "workspace-123"

    def test_per_request_workspace_id_override(self, http_client_with_workspace):
        """Test that per-request workspace_id overrides config default."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.content = b'{"id": "123"}'
        mock_response.json.return_value = {"id": "123"}

        with patch.object(http_client_with_workspace.session, "request", return_value=mock_response):
            # Override workspace_id for this request
            http_client_with_workspace.post("/v1/test", data={"name": "test"}, workspace_id="workspace-999")
            call_args = http_client_with_workspace.session.request.call_args
            assert call_args[1]["json"]["workspaceId"] == "workspace-999"  # Should use override, not config default

    def test_workspace_id_not_added_if_already_present(self, http_client_with_workspace):
        """Test that workspaceId is not duplicated if already in request."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.content = b'{"id": "123"}'
        mock_response.json.return_value = {"id": "123"}

        with patch.object(http_client_with_workspace.session, "request", return_value=mock_response):
            # Request already has workspaceId
            http_client_with_workspace.post("/v1/test", data={"name": "test", "workspaceId": "workspace-999"})
            call_args = http_client_with_workspace.session.request.call_args
            # Should keep the one from request, not add config default
            assert call_args[1]["json"]["workspaceId"] == "workspace-999"

    def test_warning_when_workspace_id_missing(self, http_client_without_workspace):
        """Test that warning is shown when workspace_id is not provided."""
        import warnings
        mock_response = Mock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.content = b'{"result": "success"}'
        mock_response.json.return_value = {"result": "success"}

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            with patch.object(http_client_without_workspace.session, "request", return_value=mock_response):
                http_client_without_workspace.get("/v1/test")
                # Should have warning about missing workspace_id
                assert len(w) > 0
                assert any("workspace_id" in str(warning.message).lower() for warning in w)

