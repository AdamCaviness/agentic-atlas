"""Agentic Workflow Atlas engine.

Reads a versioned rubric, gathers evidence from a target, resolves indicators,
computes signed axis positions with a fixed formula, and renders a profile.

The public surface is intentionally small:

    from atlas.spec import load_rubric
    from atlas.scoring import score_axis, score_profile
"""

__version__ = "0.1.0"
