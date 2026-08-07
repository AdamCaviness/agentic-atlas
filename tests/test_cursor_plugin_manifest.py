"""Cursor plugin manifest is a peer of the Claude Code plugin manifest."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CLAUDE = REPO_ROOT / ".claude-plugin" / "plugin.json"
CURSOR = REPO_ROOT / ".cursor-plugin" / "plugin.json"

PEER_KEYS = (
    "name",
    "description",
    "version",
    "homepage",
    "repository",
    "license",
    "keywords",
)


def test_cursor_plugin_json_exists() -> None:
    assert CURSOR.is_file(), f"missing {CURSOR}"


def test_cursor_peers_claude_identity_fields() -> None:
    claude = json.loads(CLAUDE.read_text())
    cursor = json.loads(CURSOR.read_text())
    for key in PEER_KEYS:
        assert key in cursor, f"cursor missing {key}"
        assert cursor[key] == claude[key], f"mismatch on {key}"
    assert cursor["author"]["name"] == claude["author"]["name"]


def test_release_please_bumps_cursor_plugin_version() -> None:
    config = json.loads((REPO_ROOT / "release-please-config.json").read_text())
    extra = config["packages"]["."]["extra-files"]
    cursor_entries = [
        e
        for e in extra
        if e.get("path") == ".cursor-plugin/plugin.json" and e.get("jsonpath") == "$.version"
    ]
    assert len(cursor_entries) == 1, "release-please must bump .cursor-plugin/plugin.json $.version"
