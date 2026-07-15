"""Finnish enterprise identifier validations and localization helpers.

This module provides utilities to validate and parse specific formats
required by Finnish enterprise APIs, such as Business IDs (Y-tunnus),
Personal Identity Codes (HETU), and national bank reference numbers (Viitenumero).
"""

import re


def validate_y_tunnus(y_tunnus: str) -> bool:
    """Validate a Finnish Business ID (Y-tunnus) using Modulo 11.

    Format: 7 digits, hyphen, 1 check digit (e.g. 1234567-8).
    Weights: 7, 9, 10, 5, 8, 4, 2.
    """
    clean = str(y_tunnus).replace(" ", "").strip()
    if not re.match(r"^\d{7}-\d$", clean):
        return False

    parts = clean.split("-")
    digits = [int(d) for d in parts[0]]
    check_digit = int(parts[1])

    weights = [7, 9, 10, 5, 8, 4, 2]
    total_sum = sum(d * w for d, w in zip(digits, weights, strict=False))

    remainder = total_sum % 11
    if remainder == 0:
        expected = 0
    elif remainder == 1:
        # A remainder of 1 means the generated Y-tunnus would be invalid
        return False
    else:
        expected = 11 - remainder

    return check_digit == expected


def validate_hetu(hetu: str) -> bool:
    """Validate a Finnish Personal Identity Code (HETU).

    Format: DDMMYYCZZZQ
    Where C is the century marker (+, -, A, B, C, D, E, F, Y, X, W, V, U)
    and Q is the check character.
    """
    clean = str(hetu).strip().upper()
    if not re.match(r"^\d{6}[+\-ABCDEFYXWVU]\d{3}[0-9A-FHJ-NP-Z]$", clean):
        return False

    date_part = clean[:6]
    individual_number = clean[7:10]
    check_char = clean[10]

    # Check character string mapping
    check_chars = "0123456789ABCDEFHJKLMNPRSTUVWXY"

    # The number formed by the date and the individual number
    number_to_divide = int(f"{date_part}{individual_number}")
    remainder = number_to_divide % 31

    return check_char == check_chars[remainder]


def validate_finnish_reference(ref: str) -> bool:
    """Verify Finnish national invoice reference number (viitenumero) check digit.

    Validates using the 7-3-1 weight pattern from right to left.
    """
    clean = str(ref).replace(" ", "").strip()
    if not clean.isdigit() or len(clean) < 4 or len(clean) > 20:
        return False

    digits = [int(char) for char in clean[:-1]]
    check_digit = int(clean[-1])

    weights = [7, 3, 1]
    total_sum = 0

    # Iterate in reverse over the base digits
    for idx, d in enumerate(reversed(digits)):
        total_sum += d * weights[idx % 3]

    # Find the next ten
    next_ten = ((total_sum + 9) // 10) * 10
    expected = next_ten - total_sum

    # If expected is 10, check digit is 0
    if expected == 10:
        expected = 0

    return check_digit == expected


def answer_contains_number_fi(answer: str, value: str) -> bool:
    """Check if a number appears in the answer, handling Finnish locale formatting.

    Finnish format uses comma as decimal separator and space as thousand separator.
    """
    normalized_answer = answer.replace(" ", "").replace(",", ".")
    normalized_needle = value.replace(" ", "").replace(",", ".")

    pattern = rf"(?<![\d.]){re.escape(normalized_needle)}(?!\d)"
    return bool(re.search(pattern, normalized_answer))
