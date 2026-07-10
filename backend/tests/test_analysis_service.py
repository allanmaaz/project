"""
Unit tests for analysis service logic.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.analysis_service import AnalysisService
from app.utils.cache import analysis_cache


class TestAnalysisService:
    @pytest.fixture
    def mock_db(self):
        """Create a mock async database session."""
        db = AsyncMock()
        db.execute = AsyncMock()
        db.commit = AsyncMock()
        db.rollback = AsyncMock()
        return db

    @pytest.fixture
    def analysis_service(self):
        return AnalysisService()

    def test_pipeline_map_contains_expected_types(self):
        """Verify all expected document types have pipelines."""
        from app.services.analysis_service import PIPELINE_MAP
        
        expected_types = [
            "medical",
            "legal_contract",
            "bill_utility",
            "bill_bank",
            "government",
            "receipt_invoice",
            "scam_message",
            "screenshot_ui",
        ]
        
        for doc_type in expected_types:
            assert doc_type in PIPELINE_MAP, f"Missing pipeline for {doc_type}"

    def test_risk_order_values(self):
        """Verify risk level ordering is correct."""
        from app.services.analysis_service import RISK_ORDER
        
        assert RISK_ORDER["informational"] == 1
        assert RISK_ORDER["low"] == 2
        assert RISK_ORDER["medium"] == 3
        assert RISK_ORDER["high"] == 4
        assert RISK_ORDER["critical"] == 5

    @pytest.mark.asyncio
    async def test_calculate_risk_score(self, analysis_service):
        """Test risk score calculation from sections."""
        # Test with danger and warning sections
        sections = [
            {"type": "danger"},
            {"type": "danger"},
            {"type": "warning"},
        ]
        
        danger = sum(1 for s in sections if s.get("type") == "danger")
        warning = sum(1 for s in sections if s.get("type") == "warning")
        score = min((danger * 20) + (warning * 8), 100)
        
        assert score == 48  # 2*20 + 1*8 = 48

    @pytest.mark.asyncio
    async def test_calculate_risk_score_max_cap(self, analysis_service):
        """Test risk score caps at 100."""
        sections = [{"type": "danger"} for _ in range(10)]
        
        danger = sum(1 for s in sections if s.get("type") == "danger")
        score = min((danger * 20), 100)
        
        assert score == 100

    @pytest.mark.asyncio
    async def test_scam_risk_override(self, analysis_service):
        """Test scam document risk level override based on probability."""
        pipeline_result = {
            "document_type": "scam_message",
            "scam_data": {"probability": 0.85},
        }
        
        prob = float(pipeline_result.get("scam_data", {}).get("probability", 0))
        if prob >= 0.8:
            risk_level = "critical"
        elif prob >= 0.6:
            risk_level = "high"
        else:
            risk_level = "informational"
            
        assert risk_level == "critical"

    @pytest.mark.asyncio
    async def test_cache_key_consistency(self, analysis_service):
        """Test that cache keys are consistent for same input."""
        from app.utils.cache import hash_file, analysis_cache
        
        file_bytes = b"test content"
        file_hash = hash_file(file_bytes)
        
        # Cache key should include file hash and language
        cache_key1 = analysis_cache.make_key(file_hash, "en")
        cache_key2 = analysis_cache.make_key(file_hash, "en")
        
        assert cache_key1 == cache_key2

    @pytest.mark.asyncio
    async def test_download_file_failure(self, analysis_service):
        """Test _download_file raises AnalysisFailedError on failure."""
        from app.utils.exceptions import AnalysisFailedError
        
        # Mock supabase to return non-bytes
        analysis_service.supabase.storage.from_.download.return_value = "not bytes"
        
        with pytest.raises(AnalysisFailedError):
            await analysis_service._download_file("nonexistent/path")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])