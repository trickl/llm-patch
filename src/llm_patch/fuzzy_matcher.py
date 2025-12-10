"""
Fuzzy matching functionality for finding code contexts.
"""

from typing import List, Optional
import difflib


class FuzzyMatcher:
    """
    Performs fuzzy matching to find similar code contexts.

    Uses similarity ratios to match code patterns even when they don't
    exactly match, allowing for minor variations in whitespace, comments, etc.
    """

    def __init__(self, threshold: float = 0.8):
        """
        Initialize the FuzzyMatcher.

        Args:
            threshold: Minimum similarity ratio (0-1) for considering a match.
        """
        if not 0 <= threshold <= 1:
            raise ValueError("threshold must be between 0 and 1")
        self.threshold = threshold

    def find_best_match(self, source_lines: List[str], pattern_lines: List[str]) -> Optional[int]:
        """
        Find the best matching location for pattern_lines within source_lines.

        Args:
            source_lines: List of lines to search within.
            pattern_lines: List of lines to search for.

        Returns:
            The starting line index of the best match, or None if no match
            exceeds the threshold.
        """
        if not pattern_lines or not source_lines:
            return None

        pattern_len = len(pattern_lines)
        best_ratio = 0.0
        best_index = None

        # Slide the pattern across the source
        for i in range(len(source_lines) - pattern_len + 1):
            candidate = source_lines[i : i + pattern_len]
            ratio = self._calculate_similarity(pattern_lines, candidate)

            if ratio > best_ratio and ratio >= self.threshold:
                best_ratio = ratio
                best_index = i

        return best_index

    def _calculate_similarity(self, lines1: List[str], lines2: List[str]) -> float:
        """
        Calculate similarity ratio between two lists of lines.

        Args:
            lines1: First list of lines.
            lines2: Second list of lines.

        Returns:
            Similarity ratio between 0 and 1.
        """
        if not lines1 or not lines2:
            return 0.0

        # Join lines and use SequenceMatcher
        text1 = "\n".join(lines1)
        text2 = "\n".join(lines2)

        matcher = difflib.SequenceMatcher(None, text1, text2)
        return matcher.ratio()

    def get_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity ratio between two text strings.

        Args:
            text1: First text string.
            text2: Second text string.

        Returns:
            Similarity ratio between 0 and 1.
        """
        if not text1 or not text2:
            return 0.0

        matcher = difflib.SequenceMatcher(None, text1, text2)
        return matcher.ratio()
