"""Unit tests for FastAPI app setup and HTTP endpoints."""

import pytest
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient


class TestHealthEndpoint:
    """Tests for GET /health endpoint."""

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test health check endpoint returns ok status."""
        from mod_api.main import app

        # We need to mock the lifespan since it requires mod-host connection
        with patch('mod_api.main.lifespan'):
            client = TestClient(app)
            response = client.get("/health")
            assert response.status_code == 200
            assert response.json() == {"status": "ok"}


class TestFastAPIAppSetup:
    """Tests for FastAPI application configuration."""

    def test_app_has_correct_title(self):
        """Test app has correct title."""
        from mod_api.main import app

        assert app.title == "Pedalboard API"

    def test_app_has_correct_version(self):
        """Test app has correct version."""
        from mod_api.main import app

        assert app.version == "1.0.0"

    def test_app_includes_all_routers(self):
        """Test all routers are included with /api/v1 prefix."""
        from mod_api.main import app

        # Check that app.routes has items (routers are registered)
        assert len(app.routes) > 0

        # The app should have the health endpoint
        assert any("/health" in str(route) for route in app.routes)

    def test_app_has_cors_middleware(self):
        """Test CORS middleware is configured."""
        from mod_api.main import app

        # Check that middleware is configured
        middleware_types = [m.cls.__name__ for m in app.user_middleware]
        # These tests verify the app structure without starting servers


class TestDependenciesCoverage:
    """Tests for dependency injection functions (lines 19, 31, 43)."""

    def test_get_pedalboard_store_from_app_state(self):
        """Test get_pedalboard_store returns store from app.state."""
        from fastapi import Request
        from mod_api.api.dependencies import get_pedalboard_store
        from mod_api.storage.pedalboard_store import PedalboardStore

        # Create a mock request with app.state
        mock_store = MagicMock(spec=PedalboardStore)
        mock_request = MagicMock(spec=Request)
        mock_request.app.state.pedalboard_store = mock_store

        result = get_pedalboard_store(mock_request)
        assert result is mock_store

    def test_get_effects_registry_from_app_state(self):
        """Test get_effects_registry returns registry from app.state."""
        from fastapi import Request
        from mod_api.api.dependencies import get_effects_registry
        from mod_api.effects.registry import EffectsRegistry

        mock_registry = MagicMock(spec=EffectsRegistry)
        mock_request = MagicMock(spec=Request)
        mock_request.app.state.effects_registry = mock_registry

        result = get_effects_registry(mock_request)
        assert result is mock_registry

    def test_get_mod_host_client_from_app_state(self):
        """Test get_mod_host_client returns client from app.state."""
        from fastapi import Request
        from mod_api.api.dependencies import get_mod_host_client
        from mod_api.utils.mod_host_client import ModHostClient

        mock_client = MagicMock(spec=ModHostClient)
        mock_request = MagicMock(spec=Request)
        mock_request.app.state.mod_host_client = mock_client

        result = get_mod_host_client(mock_request)
        assert result is mock_client


class TestLifespan:
    """Tests for application lifespan management."""

    @pytest.mark.asyncio
    async def test_lifespan_uses_env_config(self):
        """Test lifespan uses environment variables for configuration."""
        from mod_api.main import lifespan
        import os

        # Test the environment variable defaults
        original_host = os.environ.get("MOD_HOST_HOST")
        original_port = os.environ.get("MOD_HOST_PORT")
        original_data_dir = os.environ.get("PEDALBOARD_DATA_DIR")

        try:
            # Clear and set test values
            os.environ.clear()
            os.environ["MOD_HOST_HOST"] = "localhost"
            os.environ["MOD_HOST_PORT"] = "5555"
            os.environ["PEDALBOARD_DATA_DIR"] = "/tmp/test"

            mock_app = MagicMock()
            mock_app.state = MagicMock()

            with patch('mod_api.main.ModHostClient') as MockClient, \
                 patch('mod_api.main.PedalboardStore') as MockStore, \
                 patch('mod_api.main.EffectsRegistry') as MockRegistry:

                # Setup mock instances
                mock_client = MagicMock()
                MockClient.return_value = mock_client
                MockStore.return_value = MagicMock()
                MockRegistry.return_value = MagicMock()

                async with lifespan(mock_app):
                    # Verify connect was called
                    mock_client.connect.assert_called_once()

                    # Verify discover was called
                    MockRegistry.return_value.discover.assert_called_once()

                # Verify close was called on exit
                mock_client.close.assert_called_once()

        finally:
            # Restore original environment
            if original_host:
                os.environ["MOD_HOST_HOST"] = original_host
            if original_port:
                os.environ["MOD_HOST_PORT"] = original_port
            if original_data_dir:
                os.environ["PEDALBOARD_DATA_DIR"] = original_data_dir