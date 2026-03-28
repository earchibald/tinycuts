"""Tests for builder_template.py scaffold and helpers."""
import plistlib
import sys
import os
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "resources"))

from builder_template import make_shortcut


def test_make_shortcut_returns_valid_plist_structure():
    actions = []
    result = make_shortcut("Test", actions)
    assert result["WFWorkflowActions"] == []
    assert result["WFWorkflowMinimumClientVersionString"] == "1700"
    assert result["WFWorkflowMinimumClientVersion"] == 1700
    assert result["WFWorkflowClientVersion"] == 1700
    assert result["WFWorkflowClientRelease"] == "26.0"
    assert "WFWorkflowIcon" in result
    assert result["WFWorkflowIcon"]["WFWorkflowIconStartColor"] == 0x4B0082
    assert result["WFWorkflowIcon"]["WFWorkflowIconGlyphNumber"] == 0xE032
    assert "WFWorkflowInputContentItemClasses" in result
    assert "WFWorkflowTypes" in result
    assert result["WFWorkflowHasShortcutInputVariables"] is True
    assert result["WFWorkflowImportQuestions"] == []


def test_make_shortcut_custom_input_types():
    result = make_shortcut("Test", [], input_types=["WFImageContentItem"])
    assert result["WFWorkflowInputContentItemClasses"] == ["WFImageContentItem"]


def test_make_shortcut_custom_workflow_types():
    result = make_shortcut("Test", [], workflow_types=["ActionExtension"])
    assert result["WFWorkflowTypes"] == ["ActionExtension"]


def test_make_shortcut_serializes_to_binary_plist():
    result = make_shortcut("Test", [])
    with tempfile.NamedTemporaryFile(suffix=".plist", delete=False) as f:
        plistlib.dump(result, f, fmt=plistlib.FMT_BINARY)
        path = f.name
    with open(path, "rb") as f:
        loaded = plistlib.load(f)
    os.unlink(path)
    assert loaded["WFWorkflowActions"] == []
    assert loaded["WFWorkflowMinimumClientVersion"] == 1700
