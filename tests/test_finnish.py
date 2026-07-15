
from tool_eval_bench.utils.finnish import (
    answer_contains_number_fi,
    validate_finnish_reference,
    validate_hetu,
    validate_y_tunnus,
)


def test_validate_y_tunnus() -> None:
    assert validate_y_tunnus("1234567-8") is False  # Just making sure dummy fails
    assert validate_y_tunnus("1572860-0") is True  # Real valid Business ID
    assert validate_y_tunnus("2953258-8") is True  # Valid Business ID
    assert validate_y_tunnus("0123456-2") is True  # Valid Business ID
    assert validate_y_tunnus("invalid-str") is False
    assert validate_y_tunnus("12345678-1") is False


def test_validate_hetu() -> None:
    assert validate_hetu("230181-2376") is True
    assert validate_hetu("131052-308T") is True
    assert validate_hetu("010101+123N") is True  # 1800s
    assert validate_hetu("230181-237A") is False # Invalid check char
    assert validate_hetu("invalid_hetu") is False


def test_validate_finnish_reference() -> None:
    assert validate_finnish_reference("1232") is True
    assert validate_finnish_reference("123 2") is True
    assert validate_finnish_reference("1234567") is False # Invalid check
    # Reference number with 10 as expected check digit -> 0
    assert validate_finnish_reference("0110") is True


def test_answer_contains_number_fi() -> None:
    assert answer_contains_number_fi("Saldo on 1 500,50 euroa.", "1 500,50") is True
    assert answer_contains_number_fi("Saldo on 1500,50 euroa.", "1500,50") is True
    assert answer_contains_number_fi("Saldo on 1.500,50 euroa.", "1.500,50") is True
    assert answer_contains_number_fi("Maksu on 50,00", "50,00") is True
    assert answer_contains_number_fi("Maksu on 50,000", "50,00") is False
