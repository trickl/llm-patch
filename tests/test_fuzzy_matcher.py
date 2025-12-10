"""
Tests for the FuzzyMatcher class.
"""

import pytest
from llm_patch import FuzzyMatcher


class TestFuzzyMatcher:
    """Test cases for FuzzyMatcher class."""

    def test_initialization_valid_threshold(self):
        """Test FuzzyMatcher initialization with valid threshold."""
        matcher = FuzzyMatcher(threshold=0.7)
        assert matcher.threshold == 0.7

    def test_initialization_default_threshold(self):
        """Test FuzzyMatcher initialization with default threshold."""
        matcher = FuzzyMatcher()
        assert matcher.threshold == 0.8

    def test_initialization_invalid_threshold_too_high(self):
        """Test that FuzzyMatcher raises error for threshold > 1."""
        with pytest.raises(ValueError, match="threshold must be between 0 and 1"):
            FuzzyMatcher(threshold=1.5)

    def test_initialization_invalid_threshold_negative(self):
        """Test that FuzzyMatcher raises error for negative threshold."""
        with pytest.raises(ValueError, match="threshold must be between 0 and 1"):
            FuzzyMatcher(threshold=-0.2)

    def test_find_best_match_empty_pattern(self):
        """Test finding match with empty pattern."""
        matcher = FuzzyMatcher()
        source = ["line1", "line2", "line3"]
        result = matcher.find_best_match(source, [])
        assert result is None

    def test_find_best_match_empty_source(self):
        """Test finding match with empty source."""
        matcher = FuzzyMatcher()
        pattern = ["line1", "line2"]
        result = matcher.find_best_match([], pattern)
        assert result is None

    def test_find_best_match_exact_match(self):
        """Test finding exact match at start."""
        matcher = FuzzyMatcher(threshold=0.8)
        source = ["line1", "line2", "line3", "line4"]
        pattern = ["line1", "line2"]
        result = matcher.find_best_match(source, pattern)
        assert result == 0

    def test_find_best_match_at_middle(self):
        """Test finding match in middle of source."""
        matcher = FuzzyMatcher(threshold=0.8)
        source = ["line1", "line2", "line3", "line4"]
        pattern = ["line2", "line3"]
        result = matcher.find_best_match(source, pattern)
        assert result == 1

    def test_find_best_match_no_match(self):
        """Test finding match when similarity is too low."""
        matcher = FuzzyMatcher(threshold=0.99)
        source = ["line1", "line2", "line3"]
        pattern = ["completely", "different"]
        result = matcher.find_best_match(source, pattern)
        assert result is None

    def test_calculate_similarity_identical(self):
        """Test similarity calculation for identical lines."""
        matcher = FuzzyMatcher()
        lines1 = ["line1", "line2"]
        lines2 = ["line1", "line2"]
        similarity = matcher._calculate_similarity(lines1, lines2)
        assert similarity == 1.0

    def test_calculate_similarity_empty(self):
        """Test similarity calculation with empty lists."""
        matcher = FuzzyMatcher()
        similarity = matcher._calculate_similarity([], [])
        assert similarity == 0.0

    def test_calculate_similarity_one_empty(self):
        """Test similarity calculation with one empty list."""
        matcher = FuzzyMatcher()
        lines1 = ["line1", "line2"]
        similarity = matcher._calculate_similarity(lines1, [])
        assert similarity == 0.0

    def test_get_similarity_identical_strings(self):
        """Test get_similarity with identical strings."""
        matcher = FuzzyMatcher()
        text1 = "Hello, world!"
        text2 = "Hello, world!"
        similarity = matcher.get_similarity(text1, text2)
        assert similarity == 1.0

    def test_get_similarity_different_strings(self):
        """Test get_similarity with different strings."""
        matcher = FuzzyMatcher()
        text1 = "Hello, world!"
        text2 = "Goodbye, world!"
        similarity = matcher.get_similarity(text1, text2)
        assert 0 < similarity < 1.0

    def test_get_similarity_empty_strings(self):
        """Test get_similarity with empty strings."""
        matcher = FuzzyMatcher()
        similarity = matcher.get_similarity("", "")
        assert similarity == 0.0

    def test_get_similarity_one_empty_string(self):
        """Test get_similarity with one empty string."""
        matcher = FuzzyMatcher()
        similarity = matcher.get_similarity("Hello", "")
        assert similarity == 0.0

    def test_find_best_match_pattern_longer_than_source(self):
        """Test when pattern is longer than source."""
        matcher = FuzzyMatcher()
        source = ["line1"]
        pattern = ["line1", "line2", "line3"]
        result = matcher.find_best_match(source, pattern)
        assert result is None
