"""
Unit tests for the PDFProcessor service.

This module tests the PDFProcessor class in isolation,
focusing on its core text processing capabilities.
"""

import pytest
from app.services.pdf_processor import PDFProcessor


@pytest.mark.unit
class TestPDFProcessor:
    """Unit tests for the PDFProcessor service."""

    def test_extract_thermal_conductivity_variations(self, pdf_processor):
        """Test extraction of thermal conductivity with various formats."""
        test_cases = [
            ("Hővezetési tényező: 0,036 W/mK", "0,036"),
            ("λD = 0.040 W/mK", "0.040"),
            ("Thermal conductivity ≤ 0,032 W/mK", "0,032"),
            ("λ: 0,045 W/(m·K)", "0,045"),
        ]
        
        for content, expected in test_cases:
            specs = pdf_processor.extract_specs_from_pdf_content(content)
            assert "Hővezetési tényező" in specs
            assert expected in specs["Hővezetési tényező"]

    def test_extract_fire_classification(self, pdf_processor):
        """Test extraction of fire classification."""
        test_cases = [
            ("Tűzvédelmi osztály: A1", "A1"),
            ("Fire classification = A2", "A2"),
            ("Tűzvédelmi osztály: B", "B"),
        ]
        
        for content, expected in test_cases:
            specs = pdf_processor.extract_specs_from_pdf_content(content)
            assert "Tűzvédelmi osztály" in specs
            assert expected in specs["Tűzvédelmi osztály"]

    def test_extract_density(self, pdf_processor):
        """Test extraction of density values."""
        test_cases = [
            ("Testsűrűség: 140 kg/m³", "140"),
            ("Density = 120 kg/m³", "120"),
            ("Testsűrűség: 160 kg/m³", "160"),
        ]
        
        for content, expected in test_cases:
            specs = pdf_processor.extract_specs_from_pdf_content(content)
            assert "Testsűrűség" in specs
            assert expected in specs["Testsűrűség"]

    def test_extract_compressive_strength(self, pdf_processor):
        """Test extraction of compressive strength."""
        test_cases = [
            ("Nyomószilárdság ≥ 40 kPa", "40"),
            ("Compressive strength: 60 kPa", "60"),
            ("Nyomószilárdság = 80 MPa", "80"),
        ]
        
        for content, expected in test_cases:
            specs = pdf_processor.extract_specs_from_pdf_content(content)
            assert "Nyomószilárdság" in specs
            assert expected in specs["Nyomószilárdság"]

    def test_extract_rockwool_specific_values(self, pdf_processor):
        """Test extraction of ROCKWOOL-specific standard values."""
        content_with_a1 = "Nem éghető termék, A1 osztály"
        specs = pdf_processor.extract_specs_from_pdf_content(content_with_a1)
        assert "Tűzvédelmi osztály" in specs
        assert "A1" in specs["Tűzvédelmi osztály"]
        
        content_with_melting = "Olvadáspont > 1000°C"
        specs = pdf_processor.extract_specs_from_pdf_content(content_with_melting)
        assert "Olvadáspont" in specs
        assert "> 1000°C" in specs["Olvadáspont"]

    def test_format_content_headers(self, pdf_processor):
        """Test that headers are properly formatted."""
        content = """
ROCKWOOL FRONTROCK S
Műszaki adatok
Alkalmazási területek
        """
        
        formatted = pdf_processor.format_pdf_content_simple(content)
        
        # Headers should be wrapped in h3 tags
        assert "<h3>ROCKWOOL FRONTROCK S</h3>" in formatted
        assert "<h3>Műszaki adatok</h3>" in formatted
        assert "<h3>Alkalmazási területek</h3>" in formatted

    def test_format_content_specifications(self, pdf_processor):
        """Test that specification lines are properly formatted."""
        content = """
Hővezetési tényező: 0,036 W/mK
Testsűrűség: 140 kg/m³
Tűzvédelmi osztály: A1
        """
        
        formatted = pdf_processor.format_pdf_content_simple(content)
        
        # Spec lines should be wrapped in spec-line divs
        assert "<div class='spec-line'>" in formatted
        assert "Hővezetési tényező: 0,036 W/mK" in formatted
        assert "Testsűrűség: 140 kg/m³" in formatted

    def test_format_content_paragraphs(self, pdf_processor):
        """Test that regular paragraphs are properly formatted."""
        content = """
A ROCKWOOL FRONTROCK S egy kiváló minőségű homlokzati hőszigetelő lemez.
Alkalmas homlokzati hőszigetelő kompozit rendszerekhez.
        """
        
        formatted = pdf_processor.format_pdf_content_simple(content)
        
        # Paragraphs should be wrapped in p tags
        assert "<p>" in formatted
        assert "homlokzati hőszigetelő lemez" in formatted

    def test_format_content_indented_text(self, pdf_processor):
        """Test that indented content is formatted as table rows."""
        content = """
        - Homlokzati HISZ rendszerek
        - Kétféle falazat közötti hőszigetelés
            - Belsőfalak
            - Külsőfalak
        """
        
        formatted = pdf_processor.format_pdf_content_simple(content)
        
        # Indented content should be formatted as table rows
        assert "<div class='table-row'>" in formatted

    def test_format_content_html_escaping(self, pdf_processor):
        """Test that HTML special characters are properly escaped."""
        content = """
Temperature range: < 80°C & > -40°C
Formula: H₂O + CO₂ → products
        """
        
        formatted = pdf_processor.format_pdf_content_simple(content)
        
        # HTML characters should be escaped
        assert "&lt;" in formatted
        assert "&gt;" in formatted
        assert "&#8322;" in formatted or "₂" in formatted  # Subscript 2

    def test_format_empty_content(self, pdf_processor):
        """Test handling of empty or None content."""
        # Test None
        result = pdf_processor.format_pdf_content_simple(None)
        assert "Nincs elérhető tartalom" in result
        
        # Test empty string
        result = pdf_processor.format_pdf_content_simple("")
        assert "Nincs elérhető tartalom" in result
        
        # Test whitespace only
        result = pdf_processor.format_pdf_content_simple("   \n  \t  ")
        assert "Nincs elérhető tartalom" in result

    def test_format_content_page_markers_removed(self, pdf_processor):
        """Test that page markers are removed from formatted content."""
        content = """
ROCKWOOL FRONTROCK S
--- Page 1 ---
Műszaki adatok
--- Page 2 ---
Alkalmazási területek
        """
        
        formatted = pdf_processor.format_pdf_content_simple(content)
        
        # Page markers should be removed
        assert "--- Page" not in formatted
        assert "<h3>ROCKWOOL FRONTROCK S</h3>" in formatted
        assert "<h3>Műszaki adatok</h3>" in formatted

    def test_extract_specs_edge_cases(self, pdf_processor):
        """Test specification extraction with edge cases."""
        # Test with multiple values for same spec
        content = """
        Hővezetési tényező: 0,036 W/mK
        Hővezetési tényező: 0,040 W/mK
        """
        specs = pdf_processor.extract_specs_from_pdf_content(content)
        # Should take the first match
        assert "0,036" in specs["Hővezetési tényező"]
        
        # Test with very long value (should be ignored)
        content_long = """
        Hővezetési tényező: this is a very long value that exceeds the 50 character limit and should be ignored
        """
        specs = pdf_processor.extract_specs_from_pdf_content(content_long)
        assert "Hővezetési tényező" not in specs
        
        # Test with empty matches
        content_empty = "Hővezetési tényező:"
        specs = pdf_processor.extract_specs_from_pdf_content(content_empty)
        assert "Hővezetési tényező" not in specs

    def test_extract_specs_case_insensitive(self, pdf_processor):
        """Test that specification extraction is case insensitive."""
        content = """
        HŐVEZETÉSI TÉNYEZŐ: 0,036 W/mK
        tűzvédelmi osztály: a1
        TESTSŰRŰSÉG: 140 KG/M³
        """
        
        specs = pdf_processor.extract_specs_from_pdf_content(content)
        
        assert "Hővezetési tényező" in specs
        assert "Tűzvédelmi osztály" in specs
        assert "Testsűrűség" in specs

    @pytest.mark.parametrize("content,expected_specs", [
        (
            "Hővezetési tényező: 0,035 W/mK\nTűzvédelmi osztály: A1",
            {"Hővezetési tényező": "0,035 W/mK", "Tűzvédelmi osztály": "A1"}
        ),
        (
            "Density = 150 kg/m³\nCompressive strength ≥ 50 kPa",
            {"Testsűrűség": "150 kg/m³", "Nyomószilárdság": "50 kPa"}
        ),
        (
            "No specifications here, just regular text.",
            {}
        ),
    ])
    def test_extract_specs_parametrized(self, pdf_processor, content, expected_specs):
        """Parametrized test for specification extraction."""
        specs = pdf_processor.extract_specs_from_pdf_content(content)
        
        for key, expected_value in expected_specs.items():
            assert key in specs
            assert expected_value in specs[key]
        
        # Verify no unexpected specs are extracted
        unexpected_specs = set(specs.keys()) - set(expected_specs.keys())
        assert len(unexpected_specs) == 0 or all(
            # Allow W/mK and kPa fallback patterns
            any(pattern in key for pattern in ["W/mK", "kPa"]) 
            for key in unexpected_specs
        )