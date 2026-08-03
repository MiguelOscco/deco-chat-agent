"""Unit tests for input validators - OWASP compliance."""

import pytest
from validators.input_validators import (
    validate_email,
    validate_password,
    validate_username,
    validate_search_query,
    validate_chat_message,
    sanitize_string,
    validate_ip_address,
    is_sql_injection_attempt,
    is_xss_attempt,
)


# ============================================
# EMAIL VALIDATION TESTS
# ============================================

class TestEmailValidation:
    """Test email validation function."""
    
    def test_valid_emails(self, sample_emails):
        """Test that valid emails are accepted."""
        for email in sample_emails["valid"]:
            assert validate_email(email) is True, f"Valid email rejected: {email}"
    
    def test_invalid_emails(self, sample_emails):
        """Test that invalid emails are rejected."""
        for email in sample_emails["invalid"]:
            assert validate_email(email) is False, f"Invalid email accepted: {email}"
    
    def test_email_none(self):
        """Test that None is rejected."""
        assert validate_email(None) is False
    
    def test_email_empty_string(self):
        """Test that empty string is rejected."""
        assert validate_email("") is False
    
    def test_email_not_string(self):
        """Test that non-string types are rejected."""
        assert validate_email(123) is False
        assert validate_email([]) is False
        assert validate_email({}) is False
    
    def test_email_without_at(self):
        """Test email without @ symbol."""
        assert validate_email("invalidemail.com") is False
    
    def test_email_without_domain(self):
        """Test email without domain."""
        assert validate_email("user@") is False
    
    def test_email_multiple_at(self):
        """Test email with multiple @ symbols."""
        assert validate_email("user@@example.com") is False
    
    def test_email_very_long(self):
        """Test email exceeding 255 characters."""
        long_email = "a" * 250 + "@example.com"
        assert validate_email(long_email) is False


# ============================================
# PASSWORD VALIDATION TESTS
# ============================================

class TestPasswordValidation:
    """Test password validation function."""
    
    def test_strong_password(self, sample_strong_password):
        """Test that strong password is accepted."""
        assert validate_password(sample_strong_password) is True
    
    def test_weak_passwords(self, sample_weak_passwords):
        """Test that weak passwords are rejected."""
        for password in sample_weak_passwords:
            assert validate_password(password) is False, f"Weak password accepted: {password}"
    
    def test_password_none(self):
        """Test that None is rejected."""
        assert validate_password(None) is False
    
    def test_password_empty_string(self):
        """Test that empty string is rejected."""
        assert validate_password("") is False
    
    def test_password_not_string(self):
        """Test that non-string types are rejected."""
        assert validate_password(123) is False
        assert validate_password([]) is False
    
    def test_password_no_uppercase(self):
        """Test password without uppercase letters."""
        assert validate_password("lowercase123!") is False
    
    def test_password_no_lowercase(self):
        """Test password without lowercase letters."""
        assert validate_password("UPPERCASE123!") is False
    
    def test_password_no_digits(self):
        """Test password without digits."""
        assert validate_password("NoNumbers!") is False
    
    def test_password_no_special_chars(self):
        """Test password without special characters."""
        assert validate_password("NoSpecial123") is False
    
    def test_password_too_short(self):
        """Test password shorter than 8 characters."""
        assert validate_password("Pass12!") is False
    
    def test_password_too_long(self):
        """Test password longer than 255 characters."""
        long_password = "Aa1!" * 70
        assert validate_password(long_password) is False
    
    def test_password_valid_special_chars(self):
        """Test password with valid special characters."""
        valid_passwords = [
            "Password123!",
            "Secure@Pass456",
            "Test$Password789",
            "Check%Pass000",
            "Valid&Pass111",
        ]
        for pwd in valid_passwords:
            assert validate_password(pwd) is True, f"Valid password rejected: {pwd}"


# ============================================
# USERNAME VALIDATION TESTS
# ============================================

class TestUsernameValidation:
    """Test username validation function."""
    
    def test_valid_usernames(self, sample_usernames):
        """Test that valid usernames are accepted."""
        for username in sample_usernames["valid"]:
            assert validate_username(username) is True, f"Valid username rejected: {username}"
    
    def test_invalid_usernames(self, sample_usernames):
        """Test that invalid usernames are rejected."""
        for username in sample_usernames["invalid"]:
            assert validate_username(username) is False, f"Invalid username accepted: {username}"
    
    def test_username_none(self):
        """Test that None is rejected."""
        assert validate_username(None) is False
    
    def test_username_empty_string(self):
        """Test that empty string is rejected."""
        assert validate_username("") is False
    
    def test_username_not_string(self):
        """Test that non-string types are rejected."""
        assert validate_username(123) is False
    
    def test_username_too_short(self):
        """Test username shorter than 3 characters."""
        assert validate_username("ab") is False
    
    def test_username_too_long(self):
        """Test username longer than 100 characters."""
        long_username = "a" * 101
        assert validate_username(long_username) is False
    
    def test_username_with_spaces(self):
        """Test username with spaces."""
        assert validate_username("user name") is False
    
    def test_username_with_special_chars(self):
        """Test username with special characters."""
        assert validate_username("user@email") is False
        assert validate_username("user$special") is False
        assert validate_username("user!bang") is False
    
    def test_username_with_hyphen_underscore(self):
        """Test username with hyphen and underscore (allowed)."""
        assert validate_username("user-name") is True
        assert validate_username("user_name") is True
        assert validate_username("user_name-123") is True


# ============================================
# SEARCH QUERY VALIDATION TESTS
# ============================================

class TestSearchQueryValidation:
    """Test search query validation function."""
    
    def test_valid_search_query(self):
        """Test that valid search queries are accepted."""
        valid_queries = [
            "acceso",
            "sistema de acceso",
            "ticket 123",
            "error en base de datos",
        ]
        for query in valid_queries:
            assert validate_search_query(query) is True, f"Valid query rejected: {query}"
    
    def test_search_query_none(self):
        """Test that None is rejected."""
        assert validate_search_query(None) is False
    
    def test_search_query_empty_string(self):
        """Test that empty string is rejected."""
        assert validate_search_query("") is False
    
    def test_search_query_too_short(self):
        """Test query shorter than 2 characters."""
        assert validate_search_query("a") is False
    
    def test_search_query_too_long(self):
        """Test query longer than 500 characters."""
        long_query = "a" * 501
        assert validate_search_query(long_query) is False
    
    def test_search_query_sql_injection(self, sql_injection_payloads):
        """Test that SQL injection payloads are rejected."""
        for payload in sql_injection_payloads:
            assert validate_search_query(payload) is False, f"SQL injection accepted: {payload}"
    
    def test_search_query_xss_injection(self, xss_payloads):
        """Test that XSS payloads are rejected."""
        for payload in xss_payloads:
            assert validate_search_query(payload) is False, f"XSS injection accepted: {payload}"
    
    def test_search_query_drop_keyword(self):
        """Test that DROP keyword is rejected."""
        assert validate_search_query("DROP TABLE users") is False
    
    def test_search_query_delete_keyword(self):
        """Test that DELETE keyword is rejected."""
        assert validate_search_query("DELETE FROM tickets") is False
    
    def test_search_query_union_keyword(self):
        """Test that UNION keyword is rejected."""
        assert validate_search_query("UNION SELECT * FROM") is False


# ============================================
# CHAT MESSAGE VALIDATION TESTS
# ============================================

class TestChatMessageValidation:
    """Test chat message validation function."""
    
    def test_valid_chat_message(self):
        """Test that valid chat messages are accepted."""
        valid_messages = [
            "¿Cuál es el estado del ticket?",
            "Necesito ayuda con acceso GLPI",
            "El sistema está lento",
        ]
        for msg in valid_messages:
            assert validate_chat_message(msg) is True, f"Valid message rejected: {msg}"
    
    def test_chat_message_none(self):
        """Test that None is rejected."""
        assert validate_chat_message(None) is False
    
    def test_chat_message_empty_string(self):
        """Test that empty string is rejected."""
        assert validate_chat_message("") is False
    
    def test_chat_message_too_long(self):
        """Test message longer than 5000 characters."""
        long_message = "a" * 5001
        assert validate_chat_message(long_message) is False
    
    def test_chat_message_xss_injection(self, xss_payloads):
        """Test that XSS payloads are rejected."""
        for payload in xss_payloads:
            assert validate_chat_message(payload) is False, f"XSS injection accepted: {payload}"
    
    def test_chat_message_script_tag(self):
        """Test that script tags are rejected."""
        assert validate_chat_message("<script>alert('XSS')</script>") is False
    
    def test_chat_message_javascript_protocol(self):
        """Test that javascript: protocol is rejected."""
        assert validate_chat_message("javascript:alert('XSS')") is False
    
    def test_chat_message_event_handler(self):
        """Test that event handlers are rejected."""
        assert validate_chat_message("<img onerror=alert('XSS')>") is False
        assert validate_chat_message("onclick=alert('XSS')") is False
    
    def test_chat_message_sql_keywords_allowed_once(self):
        """Test that SQL keywords are allowed in normal chat (less strict)."""
        # Single mention should be OK
        assert validate_chat_message("¿Qué es SELECT?") is True
        assert validate_chat_message("El usuario hizo un UPDATE") is True
    
    def test_chat_message_sql_keywords_excessive(self):
        """Test that excessive SQL keywords are rejected."""
        suspicious = "DROP DROP DROP DELETE DELETE DELETE INSERT INSERT INSERT"
        assert validate_chat_message(suspicious) is False


# ============================================
# IP ADDRESS VALIDATION TESTS
# ============================================

class TestIPAddressValidation:
    """Test IP address validation function."""
    
    def test_valid_ipv4(self):
        """Test that valid IPv4 addresses are accepted."""
        valid_ips = [
            "192.168.1.1",
            "10.0.0.1",
            "172.16.0.1",
            "127.0.0.1",
            "255.255.255.255",
            "0.0.0.0",
        ]
        for ip in valid_ips:
            assert validate_ip_address(ip) is True, f"Valid IPv4 rejected: {ip}"
    
    def test_valid_ipv6(self):
        """Test that valid IPv6 addresses are accepted."""
        valid_ips = [
            "2001:db8::1",
            "::1",
            "fe80::1",
        ]
        for ip in valid_ips:
            assert validate_ip_address(ip) is True, f"Valid IPv6 rejected: {ip}"
    
    def test_invalid_ipv4(self):
        """Test that invalid IPv4 addresses are rejected."""
        invalid_ips = [
            "256.256.256.256",      # Out of range
            "192.168.1",            # Incomplete
            "192.168.1.1.1",        # Too many octets
            "192.168.a.1",          # Non-numeric
            "192.168.-1.1",         # Negative
        ]
        for ip in invalid_ips:
            assert validate_ip_address(ip) is False, f"Invalid IPv4 accepted: {ip}"
    
    def test_ip_none(self):
        """Test that None is rejected."""
        assert validate_ip_address(None) is False
    
    def test_ip_empty_string(self):
        """Test that empty string is rejected."""
        assert validate_ip_address("") is False


# ============================================
# STRING SANITIZATION TESTS
# ============================================

class TestStringSanitization:
    """Test string sanitization function."""
    
    def test_sanitize_normal_string(self):
        """Test that normal strings are unchanged."""
        text = "Normal text"
        assert sanitize_string(text) == text
    
    def test_sanitize_removes_null_bytes(self):
        """Test that null bytes are removed."""
        text = "Text with\x00null"
        result = sanitize_string(text)
        assert "\x00" not in result
    
    def test_sanitize_removes_control_chars(self):
        """Test that control characters are removed."""
        text = "Text with\x01control\x02chars"
        result = sanitize_string(text)
        assert len(result) < len(text)
    
    def test_sanitize_keeps_newline_tab(self):
        """Test that newline and tab are kept."""
        text = "Line1\nLine2\tTabbed"
        result = sanitize_string(text)
        assert "\n" in result
        assert "\t" in result
    
    def test_sanitize_truncates_long_text(self):
        """Test that text is truncated to max_length."""
        text = "a" * 300
        result = sanitize_string(text, max_length=255)
        assert len(result) <= 255
    
    def test_sanitize_strips_whitespace(self):
        """Test that leading/trailing whitespace is removed."""
        text = "  Text with spaces  "
        result = sanitize_string(text)
        assert result == "Text with spaces"
    
    def test_sanitize_none(self):
        """Test that None returns empty string."""
        assert sanitize_string(None) == ""
    
    def test_sanitize_empty_string(self):
        """Test that empty string returns empty string."""
        assert sanitize_string("") == ""


# ============================================
# SQL INJECTION DETECTION TESTS
# ============================================

class TestSQLInjectionDetection:
    """Test SQL injection detection function."""
    
    def test_sql_injection_payloads(self, sql_injection_payloads):
        """Test that SQL injection payloads are detected."""
        for payload in sql_injection_payloads:
            assert is_sql_injection_attempt(payload) is True, f"SQL injection not detected: {payload}"
    
    def test_normal_text_not_sql_injection(self):
        """Test that normal text is not detected as SQL injection."""
        normal_text = [
            "Hello world",
            "¿Cuál es el estado?",
            "Sistema de acceso",
        ]
        for text in normal_text:
            assert is_sql_injection_attempt(text) is False, f"False positive: {text}"
    
    def test_sql_injection_none(self):
        """Test that None returns False."""
        assert is_sql_injection_attempt(None) is False
    
    def test_sql_injection_empty_string(self):
        """Test that empty string returns False."""
        assert is_sql_injection_attempt("") is False


# ============================================
# XSS DETECTION TESTS
# ============================================

class TestXSSDetection:
    """Test XSS detection function."""
    
    def test_xss_payloads(self, xss_payloads):
        """Test that XSS payloads are detected."""
        for payload in xss_payloads:
            assert is_xss_attempt(payload) is True, f"XSS not detected: {payload}"
    
    def test_normal_text_not_xss(self):
        """Test that normal text is not detected as XSS."""
        normal_text = [
            "Hello world",
            "¿Cuál es el estado?",
            "Script para tareas",
            "Evento importante",
        ]
        for text in normal_text:
            assert is_xss_attempt(text) is False, f"False positive: {text}"
    
    def test_xss_none(self):
        """Test that None returns False."""
        assert is_xss_attempt(None) is False
    
    def test_xss_empty_string(self):
        """Test that empty string returns False."""
        assert is_xss_attempt("") is False
