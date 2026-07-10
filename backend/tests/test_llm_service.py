import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.llm_service import LLMService


class TestLLMService:
    @pytest.fixture
    def mock_genai(self):
        with patch("app.services.llm_service.genai") as mock:
            yield mock

    def test_parse_json_direct(self, mock_genai):
        service = LLMService.__new__(LLMService)
        result = service._parse_json('{"key": "value"}')
        assert result == {"key": "value"}

    def test_parse_json_with_code_fence(self, mock_genai):
        service = LLMService.__new__(LLMService)
        text = '''```json
{"key": "value"}
```'''
        result = service._parse_json(text)
        assert result == {"key": "value"}

    def test_parse_json_with_code_fence_no_language(self, mock_genai):
        service = LLMService.__new__(LLMService)
        text = '''```
{"key": "value"}
```'''
        result = service._parse_json(text)
        assert result == {"key": "value"}

    def test_parse_json_nested_in_text(self, mock_genai):
        service = LLMService.__new__(LLMService)
        text = 'Here is the result: {"key": "value"} end of text.'
        result = service._parse_json(text)
        assert result == {"key": "value"}

    def test_parse_json_fixed_quotes(self, mock_genai):
        service = LLMService.__new__(LLMService)
        text = "{'key': 'value'}"  # Single quotes
        result = service._parse_json(text)
        assert result == {"key": "value"}

    def test_parse_json_fixed_trailing_comma(self, mock_genai):
        service = LLMService.__new__(LLMService)
        text = '{"key": "value",}'  # Trailing comma
        result = service._parse_json(text)
        assert result == {"key": "value"}

    def test_parse_json_invalid_returns_empty(self, mock_genai):
        service = LLMService.__new__(LLMService)
        text = "not json at all"
        result = service._parse_json(text)
        assert result == {}

    def test_parse_json_brace_matching(self, mock_genai):
        service = LLMService.__new__(LLMService)
        # Test brace counting logic
        text = '{"outer": {"inner": "value"}}'
        result = service._parse_json(text)
        assert result == {"outer": {"inner": "value"}}

    def test_parse_json_empty_string(self, mock_genai):
        service = LLMService.__new__(LLMService)
        result = service._parse_json("")
        assert result == {}

    def test_parse_json_whitespace_only(self, mock_genai):
        service = LLMService.__new__(LLMService)
        result = service._parse_json("   \n\t  ")
        assert result == {}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])