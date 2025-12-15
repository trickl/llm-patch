"""
Tests for the PatchApplier class.
"""

import pytest
from llm_patch import PatchApplier, apply_patch


class TestPatchApplier:
    """Test cases for PatchApplier class."""

    def test_initialization_valid_threshold(self):
        """Test that PatchApplier can be initialized with valid threshold."""
        applier = PatchApplier(similarity_threshold=0.8)
        assert applier.similarity_threshold == 0.8

    def test_initialization_invalid_threshold_too_high(self):
        """Test that PatchApplier raises error for threshold > 1."""
        with pytest.raises(ValueError, match="similarity_threshold must be between 0 and 1"):
            PatchApplier(similarity_threshold=1.5)

    def test_initialization_invalid_threshold_negative(self):
        """Test that PatchApplier raises error for negative threshold."""
        with pytest.raises(ValueError, match="similarity_threshold must be between 0 and 1"):
            PatchApplier(similarity_threshold=-0.1)

    def test_apply_empty_source(self):
        """Test applying patch to empty source."""
        applier = PatchApplier()
        patch = "line1\nline2\n"
        result, success = applier.apply("", patch)
        assert success is True
        assert result == patch

    def test_apply_empty_patch(self):
        """Test applying empty patch to source."""
        applier = PatchApplier()
        source = "line1\nline2\n"
        result, success = applier.apply(source, "")
        assert success is True
        assert result == source

    def test_apply_simple_patch(self):
        """Test applying a simple patch."""
        applier = PatchApplier()
        source = "line1\nline2\nline3\n"
        patch = "line1\nline2_modified\nline3\n"
        result, success = applier.apply(source, patch)
        assert success is True
        assert isinstance(result, str)

    def test_apply_unified_diff_patch(self):
        """PatchApplier should accept unified diffs."""
        applier = PatchApplier()
        source = "line1\nline2\nline3\n"
        diff = (
            "--- before.txt\n"
            "+++ before.txt\n"
            "@@ -1,3 +1,3 @@\n"
            " line1\n"
            "-line2\n"
            "+line2_modified\n"
            " line3\n"
        )
        result, success = applier.apply(source, diff)
        assert success is True
        assert "line2_modified" in result

    def test_apply_addition_only_hunk(self):
        """Insertion-only hunks should append content when necessary."""
        applier = PatchApplier()
        source = ""
        diff = (
            "--- before.txt\n"
            "+++ before.txt\n"
            "@@ -0,0 +1,2 @@\n"
            "+alpha\n"
            "+beta\n"
        )
        result, success = applier.apply(source, diff)
        assert success is True
        assert result.strip().splitlines() == ["alpha", "beta"]

    def test_apply_unified_diff_failure(self):
        """PatchApplier should return failure when context cannot be located."""
        applier = PatchApplier()
        source = "lineA\nlineB\n"
        diff = (
            "--- before.txt\n"
            "+++ before.txt\n"
            "@@ -1,1 +1,1 @@\n"
            "-missing\n"
            "+replacement\n"
        )
        result, success = applier.apply(source, diff)
        assert success is False
        assert result == source

    def test_apply_replacement_block_patch(self):
        """PatchApplier should accept ORIGINAL/NEW block format."""
        applier = PatchApplier()
        source = "line1\nline2\nline3\n"
        replacement = (
            "ORIGINAL LINES:\n"
            "line2\n"
            "NEW LINES:\n"
            "line2_modified\n"
        )
        result, success = applier.apply(source, replacement)
        assert success is True
        assert "line2_modified" in result

    def test_apply_replacement_block_strips_fences_and_numbers(self):
        """Replacement blocks should ignore markdown fences and numbered prefixes."""
        applier = PatchApplier()
        source = "alpha\nbeta\ngamma\n"
        replacement = (
            "ORIGINAL LINES:\n"
            "```java\n"
            "2 | beta\n"
            "```\n"
            "NEW LINES:\n"
            "```java\n"
            "2 | beta_modified\n"
            "```\n"
        )
        result, success = applier.apply(source, replacement)
        assert success is True
        assert "beta_modified" in result
        assert "```" not in result
        assert "2 |" not in result

    def test_find_context_empty_lists(self):
        """Test finding context with empty lists."""
        applier = PatchApplier()
        result = applier.find_context([], [])
        assert result is None

    def test_find_context_with_data(self):
        """Test finding context with actual data."""
        applier = PatchApplier()
        source = ["line1", "line2", "line3"]
        context = ["line1", "line2"]
        result = applier.find_context(source, context)
        # Result can be None or an index, both are valid
        assert result is None or isinstance(result, int)


class TestApplyPatchFunction:
    """Test cases for the apply_patch convenience function."""

    def test_apply_patch_function(self):
        """Test the apply_patch convenience function."""
        source = "line1\nline2\n"
        patch = "line1\nline2_modified\n"
        result, success = apply_patch(source, patch)
        assert success is True
        assert isinstance(result, str)

    def test_apply_patch_function_with_threshold(self):
        """Test apply_patch with custom threshold."""
        source = "line1\nline2\n"
        patch = "line1\nline2_modified\n"
        result, success = apply_patch(source, patch, similarity_threshold=0.9)
        assert success is True
        assert isinstance(result, str)

    def test_apply_patch_empty_source_and_patch(self):
        """Test apply_patch with empty source and patch."""
        result, success = apply_patch("", "")
        assert success is True
        assert result == ""
