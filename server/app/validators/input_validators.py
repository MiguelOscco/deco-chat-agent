"""Input validation functions - OWASP compliance."""

import re
import logging
from typing import Tuple

logger = logging.getLogger(__name__)


def validate_email(email: str) -> bool:
    """Validate email format."""
    if not email or not isinstance(email, str):
        return False
    
    # RFC 5322 simplified regex
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if len(email) > 255:
        return False
    
    return bool(re.match(pattern, email))


def validate_password(password: str) -> bool:
    """Validate password strength."""
    if not password or not isinstance(password, str):
        return False
    
    # Requirements:
    # - At least 8 characters
    # - At least 1 uppercase letter
    # - At least 1 lowercase letter
    # - At least 1 digit
    # - At least 1 special character
    
    if len(password) < 8 or len(password) > 255:
        return False
    
    has_upper = bool(re.search(r'[A-Z]', password))
    has_lower = bool(re.search(r'[a-z]', password))
    has_digit = bool(re.search(r'\d', password))
    has_special = bool(re.search(r'[@$!%*?&_\-\.\,\;:\+\=]', password))
    
    return has_upper and has_lower and has_digit and has_special


def validate_username(username: str) -> bool:
    """Validate username format."""
    if not username or not isinstance(username, str):
        return False
    
    if len(username) < 3 or len(username) > 100:
        return False
    
    # Alphanumeric + underscore + hyphen only
    pattern = r'^[a-zA-Z0-9_-]+$'
    
    return bool(re.match(pattern, username))


def validate_search_query(query: str) -> bool:
    """Validate search query - prevent SQL injection and XSS."""
    if not query or not isinstance(query, str):
        return False
    
    if len(query) < 2 or len(query) > 500:
        return False
    
    # Check for SQL injection patterns
    sql_keywords = [
        "DROP", "DELETE", "INSERT", "UPDATE", "ALTER", "EXEC",
        "UNION", "SELECT", ";", "--", "/*", "*/", "xp_", "sp_"
    ]
    
    upper_query = query.upper()
    for keyword in sql_keywords:
        if keyword in upper_query:
            logger.warning(f"⚠️ Potential SQL injection detected: {keyword}")
            return False
    
    # Check for XSS patterns
    xss_patterns = [
        r'<script',
        r'javascript:',
        r'onerror=',
        r'onload=',
        r'onclick=',
        r'<iframe',
        r'<embed',
        r'<object'
    ]
    
    for pattern in xss_patterns:
        if re.search(pattern, query, re.IGNORECASE):
            logger.warning(f"⚠️ Potential XSS detected: {pattern}")
            return False
    
    return True


def validate_chat_message(message: str) -> bool:
    """Validate chat message - prevent injection and abuse."""
    if not message or not isinstance(message, str):
        return False
    
    if len(message) < 1 or len(message) > 5000:
        return False
    
    # Check for SQL injection patterns (same as search)
    sql_keywords = [
        "DROP", "DELETE", "INSERT", "UPDATE", "ALTER", "EXEC",
        "UNION", "SELECT", ";", "--", "/*", "*/", "xp_", "sp_"
    ]
    
    upper_message = message.upper()
    for keyword in sql_keywords:
        if keyword in upper_message:
            # Be less strict for chat - allow SQL keywords in normal conversation
            # but flag excessive use
            count = upper_message.count(keyword)
            if count > 3:  # More than 3 SQL keywords is suspicious
                logger.warning(f"⚠️ Potential SQL injection in chat: {keyword} (count={count})")
                return False
    
    # Check for XSS patterns (same as search)
    xss_patterns = [
        r'<script',
        r'javascript:',
        r'onerror=',
        r'onload=',
        r'onclick=',
        r'<iframe',
        r'<embed',
        r'<object'
    ]
    
    for pattern in xss_patterns:
        if re.search(pattern, message, re.IGNORECASE):
            logger.warning(f"⚠️ Potential XSS in chat: {pattern}")
            return False
    
    return True


def sanitize_string(text: str, max_length: int = 255) -> str:
    """Sanitize string input - remove dangerous characters."""
    if not text or not isinstance(text, str):
        return ""
    
    # Remove null bytes
    text = text.replace('\x00', '')
    
    # Remove control characters except newline and tab
    text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\t')
    
    # Truncate to max length
    text = text[:max_length]
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    return text


def validate_ip_address(ip: str) -> bool:
    """Validate IPv4 or IPv6 address."""
    if not ip or not isinstance(ip, str):
        return False
    
    # IPv4 pattern
    ipv4_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
    if re.match(ipv4_pattern, ip):
        parts = ip.split('.')
        return all(0 <= int(part) <= 255 for part in parts)
    
    # Simple IPv6 check (not perfect but good enough)
    ipv6_pattern = r'^([\da-fA-F]{0,4}:){2,7}[\da-fA-F]{0,4}$'
    return bool(re.match(ipv6_pattern, ip))


def is_sql_injection_attempt(query: str) -> bool:
    """Check if query looks like SQL injection attempt."""
    if not query:
        return False
    
    dangerous_patterns = [
        r"'\s*(OR|AND)\s*'",  # ' OR '
        r"1\s*=\s*1",           # 1=1
        r";\s*(DROP|DELETE|INSERT|UPDATE)",
        r"UNION.*SELECT",
        r"--\s*$",
        r"/\*.*\*/",
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, query, re.IGNORECASE):
            return True
    
    return False


def is_xss_attempt(text: str) -> bool:
    """Check if text looks like XSS attempt."""
    if not text:
        return False
    
    dangerous_patterns = [
        r'<\s*script',
        r'javascript\s*:',
        r'on\w+\s*=',
        r'<\s*(iframe|embed|object|applet)',
        r'<\s*img[^>]*on',
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    
    return False

