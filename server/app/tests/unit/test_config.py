"""Unit tests for configuration settings."""

import pytest
import os
from config import Settings


# ============================================
# BASIC SETTINGS TESTS
# ============================================

class TestBasicSettings:
    """Test basic application settings."""
    
    def test_settings_instance_created(self, test_settings):
        """Test that Settings instance is created successfully."""
        assert test_settings is not None
        assert isinstance(test_settings, Settings)
    
    def test_app_name_present(self, test_settings):
        """Test that APP_NAME is configured."""
        assert test_settings.APP_NAME is not None
        assert len(test_settings.APP_NAME) > 0
        assert "DECO" in test_settings.APP_NAME or "Chat" in test_settings.APP_NAME
    
    def test_app_version_present(self, test_settings):
        """Test that APP_VERSION is configured."""
        assert test_settings.APP_VERSION is not None
        assert len(test_settings.APP_VERSION) > 0
        # Should be in format x.y.z
        assert test_settings.APP_VERSION.count(".") >= 2
    
    def test_environment_is_testing(self, test_settings):
        """Test that environment is set to testing."""
        assert test_settings.ENVIRONMENT == "testing"
    
    def test_debug_enabled_in_testing(self, test_settings):
        """Test that DEBUG is True in testing environment."""
        assert test_settings.DEBUG is True
    
    def test_server_id_present(self, test_settings):
        """Test that SERVER_ID is configured."""
        assert test_settings.SERVER_ID is not None
        assert len(test_settings.SERVER_ID) > 0


# ============================================
# HOST AND PORT SETTINGS
# ============================================

class TestHostPortSettings:
    """Test host and port configuration."""
    
    def test_host_is_string(self, test_settings):
        """Test that HOST is a string."""
        assert isinstance(test_settings.HOST, str)
    
    def test_host_not_empty(self, test_settings):
        """Test that HOST is not empty."""
        assert len(test_settings.HOST) > 0
    
    def test_port_is_integer(self, test_settings):
        """Test that PORT is an integer."""
        assert isinstance(test_settings.PORT, int)
    
    def test_port_in_valid_range(self, test_settings):
        """Test that PORT is in valid range (1-65535)."""
        assert 1 <= test_settings.PORT <= 65535
    
    def test_workers_is_integer(self, test_settings):
        """Test that WORKERS is an integer."""
        assert isinstance(test_settings.WORKERS, int)
    
    def test_workers_positive(self, test_settings):
        """Test that WORKERS is positive."""
        assert test_settings.WORKERS > 0


# ============================================
# SECURITY SETTINGS
# ============================================

class TestSecuritySettings:
    """Test security-related settings."""
    
    def test_jwt_secret_present(self, test_settings):
        """Test that JWT_SECRET is configured."""
        assert test_settings.JWT_SECRET is not None
        assert len(test_settings.JWT_SECRET) > 0
    
    def test_jwt_secret_minimum_length(self, test_settings):
        """Test that JWT_SECRET meets minimum length requirement."""
        # Should be at least 32 characters for secure HS256
        assert len(test_settings.JWT_SECRET) >= 32
    
    def test_jwt_secret_not_default(self, test_settings):
        """Test that JWT_SECRET is not default value."""
        default_secrets = [
            "secret",
            "default-secret",
            "change-me",
        ]
        # Should not be a known default
        assert test_settings.JWT_SECRET not in default_secrets
    
    def test_jwt_algorithm_is_hs256(self, test_settings):
        """Test that JWT_ALGORITHM is HS256."""
        assert test_settings.JWT_ALGORITHM == "HS256"
    
    def test_jwt_access_token_expire_minutes_positive(self, test_settings):
        """Test that JWT_ACCESS_TOKEN_EXPIRE_MINUTES is positive."""
        assert test_settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES > 0
    
    def test_jwt_refresh_token_expire_days_positive(self, test_settings):
        """Test that JWT_REFRESH_TOKEN_EXPIRE_DAYS is positive."""
        assert test_settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS > 0
    
    def test_jwt_refresh_longer_than_access(self, test_settings):
        """Test that refresh token expires longer than access token."""
        # Convert to same unit for comparison
        access_minutes = test_settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        refresh_minutes = test_settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60
        
        assert refresh_minutes > access_minutes
    
    def test_bcrypt_rounds_valid(self, test_settings):
        """Test that BCRYPT_ROUNDS is valid."""
        # Should be between 10 and 15
        assert 10 <= test_settings.BCRYPT_ROUNDS <= 15


# ============================================
# DATABASE SETTINGS
# ============================================

class TestDatabaseSettings:
    """Test database configuration."""
    
    def test_database_url_present(self, test_settings):
        """Test that DATABASE_URL is configured."""
        assert test_settings.DATABASE_URL is not None
        assert len(test_settings.DATABASE_URL) > 0
    
    def test_database_url_format(self, test_settings):
        """Test that DATABASE_URL has valid format."""
        # Should contain protocol://
        assert "://" in test_settings.DATABASE_URL
    
    def test_database_url_is_test_db(self, test_settings):
        """Test that DATABASE_URL is pointing to test database."""
        # In testing, should be SQLite in-memory
        assert "sqlite" in test_settings.DATABASE_URL.lower() or "memory" in test_settings.DATABASE_URL


# ============================================
# REDIS SETTINGS
# ============================================

class TestRedisSettings:
    """Test Redis configuration."""
    
    def test_redis_host_present(self, test_settings):
        """Test that REDIS_HOST is configured."""
        assert test_settings.REDIS_HOST is not None
        assert len(test_settings.REDIS_HOST) > 0
    
    def test_redis_host_is_string(self, test_settings):
        """Test that REDIS_HOST is a string."""
        assert isinstance(test_settings.REDIS_HOST, str)
    
    def test_redis_port_is_integer(self, test_settings):
        """Test that REDIS_PORT is an integer."""
        assert isinstance(test_settings.REDIS_PORT, int)
    
    def test_redis_port_in_valid_range(self, test_settings):
        """Test that REDIS_PORT is in valid range."""
        assert 1 <= test_settings.REDIS_PORT <= 65535
    
    def test_redis_socket_timeout_positive(self, test_settings):
        """Test that REDIS_SOCKET_CONNECT_TIMEOUT is positive."""
        assert test_settings.REDIS_SOCKET_CONNECT_TIMEOUT > 0
    
    def test_rate_limit_requests_positive(self, test_settings):
        """Test that RATE_LIMIT_REQUESTS is positive."""
        assert test_settings.RATE_LIMIT_REQUESTS > 0
    
    def test_rate_limit_window_positive(self, test_settings):
        """Test that RATE_LIMIT_WINDOW_SECONDS is positive."""
        assert test_settings.RATE_LIMIT_WINDOW_SECONDS > 0


# ============================================
# GLPI SETTINGS
# ============================================

class TestGLPISettings:
    """Test GLPI configuration."""
    
    def test_glpi_base_url_present(self, test_settings):
        """Test that GLPI_BASE_URL is configured."""
        assert test_settings.GLPI_BASE_URL is not None
        assert len(test_settings.GLPI_BASE_URL) > 0
    
    def test_glpi_base_url_format(self, test_settings):
        """Test that GLPI_BASE_URL is a valid URL."""
        assert "http" in test_settings.GLPI_BASE_URL.lower()
        assert "://" in test_settings.GLPI_BASE_URL
    
    def test_glpi_app_token_present(self, test_settings):
        """Test that GLPI_APP_TOKEN is configured."""
        assert test_settings.GLPI_APP_TOKEN is not None
        assert len(test_settings.GLPI_APP_TOKEN) > 0
    
    def test_glpi_app_token_not_default(self, test_settings):
        """Test that GLPI_APP_TOKEN is not a default value."""
        default_tokens = [
            "default-token",
            "change-me",
            "test-token",
        ]
        # Should not be obvious default
        assert test_settings.GLPI_APP_TOKEN not in default_tokens
    
    def test_glpi_user_present(self, test_settings):
        """Test that GLPI_USER is configured."""
        assert test_settings.GLPI_USER is not None
        assert len(test_settings.GLPI_USER) > 0
    
    def test_glpi_password_present(self, test_settings):
        """Test that GLPI_PASSWORD is configured."""
        assert test_settings.GLPI_PASSWORD is not None
        assert len(test_settings.GLPI_PASSWORD) > 0
    
    def test_glpi_timeout_positive(self, test_settings):
        """Test that GLPI_TIMEOUT is positive."""
        assert test_settings.GLPI_TIMEOUT > 0


# ============================================
# OLLAMA SETTINGS
# ============================================

class TestOllamaSettings:
    """Test Ollama LLM configuration."""
    
    def test_ollama_base_url_present(self, test_settings):
        """Test that OLLAMA_BASE_URL is configured."""
        assert test_settings.OLLAMA_BASE_URL is not None
        assert len(test_settings.OLLAMA_BASE_URL) > 0
    
    def test_ollama_base_url_format(self, test_settings):
        """Test that OLLAMA_BASE_URL is a valid URL."""
        assert "http" in test_settings.OLLAMA_BASE_URL.lower()
        assert "://" in test_settings.OLLAMA_BASE_URL
    
    def test_ollama_model_present(self, test_settings):
        """Test that OLLAMA_MODEL is configured."""
        assert test_settings.OLLAMA_MODEL is not None
        assert len(test_settings.OLLAMA_MODEL) > 0
    
    def test_ollama_model_is_known(self, test_settings):
        """Test that OLLAMA_MODEL is a known model."""
        known_models = [
            "mistral",
            "llama2",
            "neural-chat",
            "dolphin-mixtral",
        ]
        assert test_settings.OLLAMA_MODEL.lower() in known_models
    
    def test_ollama_timeout_positive(self, test_settings):
        """Test that OLLAMA_TIMEOUT is positive."""
        assert test_settings.OLLAMA_TIMEOUT > 0
    
    def test_ollama_timeout_long_enough(self, test_settings):
        """Test that OLLAMA_TIMEOUT is sufficient for LLM."""
        # LLM generation can take time
        assert test_settings.OLLAMA_TIMEOUT >= 30
    
    def test_ollama_temperature_valid_range(self, test_settings):
        """Test that OLLAMA_TEMPERATURE is in valid range."""
        # Temperature should be between 0.0 and 1.0
        assert 0.0 <= test_settings.OLLAMA_TEMPERATURE <= 1.0


# ============================================
# LOGGING SETTINGS
# ============================================

class TestLoggingSettings:
    """Test logging configuration."""
    
    def test_log_level_present(self, test_settings):
        """Test that LOG_LEVEL is configured."""
        assert test_settings.LOG_LEVEL is not None
        assert len(test_settings.LOG_LEVEL) > 0
    
    def test_log_level_valid(self, test_settings):
        """Test that LOG_LEVEL is valid."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        assert test_settings.LOG_LEVEL in valid_levels
    
    def test_log_format_present(self, test_settings):
        """Test that LOG_FORMAT is configured."""
        assert test_settings.LOG_FORMAT is not None
        assert len(test_settings.LOG_FORMAT) > 0
    
    def test_log_format_valid(self, test_settings):
        """Test that LOG_FORMAT is valid."""
        valid_formats = ["json", "text"]
        assert test_settings.LOG_FORMAT in valid_formats
    
    def test_log_file_present(self, test_settings):
        """Test that LOG_FILE is configured."""
        assert test_settings.LOG_FILE is not None
        assert len(test_settings.LOG_FILE) > 0
    
    def test_log_max_bytes_positive(self, test_settings):
        """Test that LOG_MAX_BYTES is positive."""
        assert test_settings.LOG_MAX_BYTES > 0
    
    def test_log_backup_count_positive(self, test_settings):
        """Test that LOG_BACKUP_COUNT is positive."""
        assert test_settings.LOG_BACKUP_COUNT > 0


# ============================================
# CORS SETTINGS
# ============================================

class TestCORSSettings:
    """Test CORS configuration."""
    
    def test_cors_origins_is_list(self, test_settings):
        """Test that CORS_ORIGINS is a list."""
        assert isinstance(test_settings.CORS_ORIGINS, list)
    
    def test_cors_origins_not_empty(self, test_settings):
        """Test that CORS_ORIGINS is not empty."""
        assert len(test_settings.CORS_ORIGINS) > 0
    
    def test_cors_origins_contains_localhost(self, test_settings):
        """Test that CORS_ORIGINS includes localhost."""
        origins_str = " ".join(test_settings.CORS_ORIGINS)
        assert "localhost" in origins_str
    
    def test_cors_allow_credentials_is_bool(self, test_settings):
        """Test that CORS_ALLOW_CREDENTIALS is a boolean."""
        assert isinstance(test_settings.CORS_ALLOW_CREDENTIALS, bool)
    
    def test_cors_allow_methods_is_list(self, test_settings):
        """Test that CORS_ALLOW_METHODS is a list."""
        assert isinstance(test_settings.CORS_ALLOW_METHODS, list)
    
    def test_cors_allow_methods_not_empty(self, test_settings):
        """Test that CORS_ALLOW_METHODS is not empty."""
        assert len(test_settings.CORS_ALLOW_METHODS) > 0
    
    def test_cors_allow_methods_includes_common(self, test_settings):
        """Test that CORS_ALLOW_METHODS includes common methods."""
        assert "GET" in test_settings.CORS_ALLOW_METHODS
        assert "POST" in test_settings.CORS_ALLOW_METHODS
    
    def test_cors_allow_headers_is_list(self, test_settings):
        """Test that CORS_ALLOW_HEADERS is a list."""
        assert isinstance(test_settings.CORS_ALLOW_HEADERS, list)


# ============================================
# SECURITY HEADERS SETTINGS
# ============================================

class TestSecurityHeadersSettings:
    """Test security headers configuration."""
    
    def test_enable_hsts_is_bool(self, test_settings):
        """Test that ENABLE_HSTS is a boolean."""
        assert isinstance(test_settings.ENABLE_HSTS, bool)
    
    def test_hsts_max_age_positive(self, test_settings):
        """Test that HSTS_MAX_AGE is positive."""
        assert test_settings.HSTS_MAX_AGE > 0
    
    def test_enable_csp_is_bool(self, test_settings):
        """Test that ENABLE_CSP is a boolean."""
        assert isinstance(test_settings.ENABLE_CSP, bool)
    
    def test_enable_nosniff_is_bool(self, test_settings):
        """Test that ENABLE_NOSNIFF is a boolean."""
        assert isinstance(test_settings.ENABLE_NOSNIFF, bool)
    
    def test_enable_xframe_options_is_bool(self, test_settings):
        """Test that ENABLE_XFRAME_OPTIONS is a boolean."""
        assert isinstance(test_settings.ENABLE_XFRAME_OPTIONS, bool)


# ============================================
# ENVIRONMENT VARIABLE LOADING
# ============================================

class TestEnvironmentVariableLoading:
    """Test loading settings from environment variables."""
    
    def test_settings_loads_from_env(self, monkeypatch):
        """Test that Settings loads values from environment."""
        monkeypatch.setenv("APP_NAME", "Custom App Name")
        monkeypatch.setenv("PORT", "9999")
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        
        custom_settings = Settings()
        
        assert custom_settings.APP_NAME == "Custom App Name"
        assert custom_settings.PORT == 9999
        assert custom_settings.LOG_LEVEL == "DEBUG"
    
    def test_settings_uses_defaults(self, monkeypatch):
        """Test that Settings uses default values when env not set."""
        # Clear specific env vars
        monkeypatch.delenv("APP_NAME", raising=False)
        monkeypatch.delenv("PORT", raising=False)
        
        settings_with_defaults = Settings()
        
        # Should have some default values
        assert settings_with_defaults.APP_NAME is not None
        assert settings_with_defaults.PORT > 0


# ============================================
# TYPE VALIDATION
# ============================================

class TestTypeValidation:
    """Test that Settings validates types correctly."""
    
    def test_all_string_settings_are_strings(self, test_settings):
        """Test that string settings are strings."""
        string_settings = [
            test_settings.APP_NAME,
            test_settings.ENVIRONMENT,
            test_settings.HOST,
            test_settings.JWT_SECRET,
            test_settings.GLPI_BASE_URL,
            test_settings.OLLAMA_BASE_URL,
        ]
        
        for setting in string_settings:
            assert isinstance(setting, str)
    
    def test_all_integer_settings_are_integers(self, test_settings):
        """Test that integer settings are integers."""
        integer_settings = [
            test_settings.PORT,
            test_settings.WORKERS,
            test_settings.REDIS_PORT,
            test_settings.RATE_LIMIT_REQUESTS,
            test_settings.LOG_MAX_BYTES,
        ]
        
        for setting in integer_settings:
            assert isinstance(setting, int)
    
    def test_all_boolean_settings_are_booleans(self, test_settings):
        """Test that boolean settings are booleans."""
        boolean_settings = [
            test_settings.DEBUG,
            test_settings.CORS_ALLOW_CREDENTIALS,
            test_settings.ENABLE_HSTS,
            test_settings.ENABLE_CSP,
        ]
        
        for setting in boolean_settings:
            assert isinstance(setting, bool)
    
    def test_all_list_settings_are_lists(self, test_settings):
        """Test that list settings are lists."""
        list_settings = [
            test_settings.CORS_ORIGINS,
            test_settings.CORS_ALLOW_METHODS,
            test_settings.CORS_ALLOW_HEADERS,
        ]
        
        for setting in list_settings:
            assert isinstance(setting, list)
