"""
Simple validation utilities for patient registration.

Provides basic format validation for:
- Phone numbers (US format)
- Email addresses
- Patient names
"""

import re
from typing import Tuple


def validate_phone(phone: str) -> Tuple[bool, str]:
    """
    Validate and normalize phone number to US format.

    Accepts various formats:
    - 4155550199
    - 415-555-0199
    - (415) 555-0199
    - +1-415-555-0199
    - 1-415-555-0199

    Args:
        phone: Raw phone input string

    Returns:
        Tuple of (is_valid, normalized_phone_or_error_message)
        - If valid: (True, "+1-415-555-0199")
        - If invalid: (False, "error message")
    """
    if not phone:
        return False, "Phone number is required"

    # Remove all non-digit characters
    digits = re.sub(r'[^\d]', '', phone)

    # Check for valid US phone (10 or 11 digits)
    if len(digits) == 10:
        # Format as +1-NNN-NNN-NNNN
        normalized = f"+1-{digits[0:3]}-{digits[3:6]}-{digits[6:10]}"
        return True, normalized
    elif len(digits) == 11 and digits[0] == '1':
        # Format as +1-NNN-NNN-NNNN (strip leading 1)
        normalized = f"+1-{digits[1:4]}-{digits[4:7]}-{digits[7:11]}"
        return True, normalized
    else:
        return False, "Please provide a 10-digit phone number"


def validate_email(email: str) -> Tuple[bool, str]:
    """
    Validate email address format.

    Performs basic format validation using regex.
    Does not verify email deliverability or check for disposable domains.

    Args:
        email: Raw email input string

    Returns:
        Tuple of (is_valid, normalized_email_or_error_message)
        - If valid: (True, "user@example.com")
        - If invalid: (False, "error message")
    """
    if not email:
        return False, "Email address is required"

    # Basic email regex: user@domain.tld
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    email_cleaned = email.strip()

    if re.match(pattern, email_cleaned):
        # Normalize to lowercase
        return True, email_cleaned.lower()
    else:
        return False, "Please provide a valid email address"


def validate_name(name: str) -> Tuple[bool, str]:
    """
    Validate patient name.

    Requires at least first and last name (contains at least one space).
    Minimum length of 2 characters.

    Args:
        name: Raw name input string

    Returns:
        Tuple of (is_valid, name_or_error_message)
        - If valid: (True, "John Doe")
        - If invalid: (False, "error message")
    """
    if not name:
        return False, "Name is required"

    name_cleaned = name.strip()

    # Check minimum length
    if len(name_cleaned) < 2:
        return False, "Please provide your full name"

    # Check for at least one space (first and last name)
    if ' ' not in name_cleaned:
        return False, "Please provide both first and last name"

    return True, name_cleaned
