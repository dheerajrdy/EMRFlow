"""
Unit tests for validation utilities.

Tests validation functions for phone, email, and name inputs.
"""

import pytest
from src.utils.validation import validate_phone, validate_email, validate_name


class TestValidatePhone:
    """Test phone number validation."""

    def test_valid_10_digit_phone(self):
        """Test 10-digit phone number."""
        is_valid, result = validate_phone("4155550199")
        assert is_valid is True
        assert result == "+1-415-555-0199"

    def test_valid_phone_with_dashes(self):
        """Test phone with dashes."""
        is_valid, result = validate_phone("415-555-0199")
        assert is_valid is True
        assert result == "+1-415-555-0199"

    def test_valid_phone_with_parentheses(self):
        """Test phone with parentheses."""
        is_valid, result = validate_phone("(415) 555-0199")
        assert is_valid is True
        assert result == "+1-415-555-0199"

    def test_valid_phone_with_plus_one(self):
        """Test phone with +1 prefix."""
        is_valid, result = validate_phone("+1-415-555-0199")
        assert is_valid is True
        assert result == "+1-415-555-0199"

    def test_valid_phone_with_leading_one(self):
        """Test 11-digit phone starting with 1."""
        is_valid, result = validate_phone("14155550199")
        assert is_valid is True
        assert result == "+1-415-555-0199"

    def test_invalid_phone_too_short(self):
        """Test phone number too short."""
        is_valid, result = validate_phone("12345")
        assert is_valid is False
        assert "10-digit" in result

    def test_invalid_phone_too_long(self):
        """Test phone number too long."""
        is_valid, result = validate_phone("123456789012")
        assert is_valid is False
        assert "10-digit" in result

    def test_invalid_phone_empty(self):
        """Test empty phone number."""
        is_valid, result = validate_phone("")
        assert is_valid is False
        assert "required" in result

    def test_invalid_phone_letters(self):
        """Test phone with letters (should extract digits)."""
        is_valid, result = validate_phone("abc")
        assert is_valid is False


class TestValidateEmail:
    """Test email validation."""

    def test_valid_email_simple(self):
        """Test simple valid email."""
        is_valid, result = validate_email("user@example.com")
        assert is_valid is True
        assert result == "user@example.com"

    def test_valid_email_with_dots(self):
        """Test email with dots in username."""
        is_valid, result = validate_email("first.last@example.com")
        assert is_valid is True
        assert result == "first.last@example.com"

    def test_valid_email_with_plus(self):
        """Test email with plus sign."""
        is_valid, result = validate_email("user+tag@example.com")
        assert is_valid is True
        assert result == "user+tag@example.com"

    def test_valid_email_subdomain(self):
        """Test email with subdomain."""
        is_valid, result = validate_email("user@mail.example.com")
        assert is_valid is True
        assert result == "user@mail.example.com"

    def test_email_normalized_to_lowercase(self):
        """Test email is normalized to lowercase."""
        is_valid, result = validate_email("User@Example.COM")
        assert is_valid is True
        assert result == "user@example.com"

    def test_email_with_whitespace_stripped(self):
        """Test email with surrounding whitespace."""
        is_valid, result = validate_email("  user@example.com  ")
        assert is_valid is True
        assert result == "user@example.com"

    def test_invalid_email_no_at(self):
        """Test email without @ symbol."""
        is_valid, result = validate_email("userexample.com")
        assert is_valid is False
        assert "valid email" in result

    def test_invalid_email_no_domain(self):
        """Test email without domain."""
        is_valid, result = validate_email("user@")
        assert is_valid is False
        assert "valid email" in result

    def test_invalid_email_no_tld(self):
        """Test email without TLD."""
        is_valid, result = validate_email("user@example")
        assert is_valid is False
        assert "valid email" in result

    def test_invalid_email_empty(self):
        """Test empty email."""
        is_valid, result = validate_email("")
        assert is_valid is False
        assert "required" in result


class TestValidateName:
    """Test name validation."""

    def test_valid_name_first_last(self):
        """Test valid first and last name."""
        is_valid, result = validate_name("John Doe")
        assert is_valid is True
        assert result == "John Doe"

    def test_valid_name_with_middle(self):
        """Test valid name with middle name."""
        is_valid, result = validate_name("John Michael Doe")
        assert is_valid is True
        assert result == "John Michael Doe"

    def test_valid_name_with_suffix(self):
        """Test valid name with suffix."""
        is_valid, result = validate_name("John Doe Jr.")
        assert is_valid is True
        assert result == "John Doe Jr."

    def test_name_with_whitespace_stripped(self):
        """Test name with surrounding whitespace."""
        is_valid, result = validate_name("  John Doe  ")
        assert is_valid is True
        assert result == "John Doe"

    def test_invalid_name_single_word(self):
        """Test name with only one word."""
        is_valid, result = validate_name("John")
        assert is_valid is False
        assert "first and last" in result

    def test_invalid_name_too_short(self):
        """Test name too short."""
        is_valid, result = validate_name("J")
        assert is_valid is False
        assert "full name" in result

    def test_invalid_name_empty(self):
        """Test empty name."""
        is_valid, result = validate_name("")
        assert is_valid is False
        assert "required" in result

    def test_invalid_name_only_whitespace(self):
        """Test name with only whitespace."""
        is_valid, result = validate_name("   ")
        assert is_valid is False
        assert "required" in result or "full name" in result
