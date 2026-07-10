"""
Unit tests for utility functions.
"""
import pytest
from app.utils.text_utils import (
    clean_text,
    truncate_for_llm,
    extract_dates,
    extract_amounts,
    extract_urls,
    extract_phone_numbers,
    extract_all_entities,
    estimate_token_count,
)


class TestCleanText:
    def test_normal_text(self):
        text = "Hello world\n\nThis is a test."
        assert clean_text(text) == text

    def test_removes_null_bytes(self):
        text = "Hello\x00world"
        assert clean_text(text) == "Helloworld"

    def test_removes_control_chars(self):
        text = "Hello\x01\x02world"
        assert clean_text(text) == "Helloworld"

    def test_collapses_multiple_newlines(self):
        text = "Line 1\n\n\n\nLine 2"
        assert clean_text(text) == "Line 1\n\nLine 2"

    def test_collapses_multiple_spaces(self):
        text = "Hello    world"
        assert clean_text(text) == "Hello world"

    def test_strips_whitespace(self):
        text = "  Hello world  "
        assert clean_text(text) == "Hello world"

    def test_empty_string(self):
        assert clean_text("") == ""

    def test_none_input(self):
        assert clean_text(None) == ""


class TestTruncateForLLM:
    def test_short_text(self):
        text = "Short text"
        assert truncate_for_llm(text, max_chars=100) == text

    def test_long_text_truncated(self):
        text = "a" * 1000
        result = truncate_for_llm(text, max_chars=100)
        assert len(result) <= 100 + 50  # Allow for truncation message

    def test_truncation_message(self):
        text = "a" * 1000
        result = truncate_for_llm(text, max_chars=100)
        assert "[Document truncated" in result


class TestExtractDates:
    def test_slash_format(self):
        text = "Date: 12/31/2024"
        dates = extract_dates(text)
        assert "12/31/2024" in dates

    def test_dash_format(self):
        text = "Date: 12-31-2024"
        dates = extract_dates(text)
        assert "12-31-2024" in dates

    def test_dot_format(self):
        text = "Date: 12.31.2024"
        dates = extract_dates(text)
        assert "12.31.2024" in dates

    def test_month_name_format(self):
        text = "Date: January 15, 2024"
        dates = extract_dates(text)
        assert "January 15, 2024" in dates

    def test_iso_format(self):
        text = "Date: 2024-12-31"
        dates = extract_dates(text)
        assert "2024-12-31" in dates

    def test_multiple_dates(self):
        text = "Start: 01/01/2024, End: 12/31/2024"
        dates = extract_dates(text)
        assert len(dates) == 2

    def test_deduplication(self):
        text = "Date: 01/01/2024 and 01/01/2024"
        dates = extract_dates(text)
        assert len(dates) == 1


class TestExtractAmounts:
    def test_dollar_amount(self):
        text = "Total: $1,234.56"
        amounts = extract_amounts(text)
        assert "$1,234.56" in amounts

    def test_euro_amount(self):
        text = "Total: €1,234.56"
        amounts = extract_amounts(text)
        assert "€1,234.56" in amounts

    def test_rupee_amount(self):
        text = "Total: ₹1,234.56"
        amounts = extract_amounts(text)
        assert "₹1,234.56" in amounts

    def test_usd_suffix(self):
        text = "Total: 1234.56 USD"
        amounts = extract_amounts(text)
        assert "1234.56 USD" in amounts

    def test_rs_prefix(self):
        text = "Total: Rs. 1,234"
        amounts = extract_amounts(text)
        assert "Rs. 1,234" in amounts


class TestExtractUrls:
    def test_http_url(self):
        text = "Visit https://example.com"
        urls = extract_urls(text)
        assert "https://example.com" in urls

    def test_www_url(self):
        text = "Visit www.example.com"
        urls = extract_urls(text)
        assert "www.example.com" in urls

    def test_multiple_urls(self):
        text = "Check https://a.com and https://b.com"
        urls = extract_urls(text)
        assert len(urls) == 2


class TestExtractPhoneNumbers:
    def test_us_format(self):
        text = "Call 123-456-7890"
        phones = extract_phone_numbers(text)
        assert "123-456-7890" in phones

    def test_parentheses_format(self):
        text = "Call (123) 456-7890"
        phones = extract_phone_numbers(text)
        assert "(123) 456-7890" in phones

    def test_international_format(self):
        text = "Call +1 123 456 7890"
        phones = extract_phone_numbers(text)
        assert "+1 123 456 7890" in phones


class TestExtractAllEntities:
    def test_all_types(self):
        text = "Date: 01/01/2024, Amount: $100, URL: https://test.com, Phone: 123-456-7890"
        entities = extract_all_entities(text)
        assert "01/01/2024" in entities["dates"]
        assert "$100" in entities["amounts"]
        assert "https://test.com" in entities["urls"]
        assert "123-456-7890" in entities["phones"]


class TestEstimateTokenCount:
    def test_english_text(self):
        text = "This is a test sentence."
        tokens = estimate_token_count(text)
        # ~4 chars per token
        assert tokens == len(text) // 4

    def test_empty_string(self):
        assert estimate_token_count("") == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])