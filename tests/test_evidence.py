"""Tests for evidence collection helpers."""

import pytest

from atlas.evidence import _matches


@pytest.mark.parametrize(
    "path,pattern,expected",
    [
        ("skills/foo.md", "**/skills/**", True),      # top-level dir, no parent segment
        ("a/b/skills/foo.md", "**/skills/**", True),  # nested
        ("skills/foo.md", "skills/**", True),
        ("src/agent.md", "**/*agent*.md", True),
        ("agents/pm/agent.md", "**/agents/**", True),
        ("readme.md", "**/skills/**", False),
        ("skillset/foo.md", "**/skills/**", False),   # must be a real path segment
        ("BROWNFIELD.md", "**/brownfield*", False),   # case-sensitive by design
        ("brownfield-guide.md", "**/brownfield*", True),
    ],
)
def test_matches(path, pattern, expected):
    assert _matches(path, pattern) is expected
