"""Tests for builder_template.py scaffold and helpers."""
import plistlib
import sys
import os
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "resources"))

from builder_template import make_shortcut
from builder_template import (
    new_uuid, make_attachment, make_magic_variable, make_text_with_variable,
)
import re


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


def test_new_uuid_format():
    uid = new_uuid()
    assert re.match(r"^[A-F0-9]{8}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{12}$", uid)


def test_new_uuid_unique():
    assert new_uuid() != new_uuid()


def test_make_attachment():
    result = make_attachment("ABCD-1234", "Clipboard")
    assert result["WFSerializationType"] == "WFTextTokenAttachment"
    assert result["Value"]["Type"] == "ActionOutput"
    assert result["Value"]["OutputUUID"] == "ABCD-1234"
    assert result["Value"]["OutputName"] == "Clipboard"


def test_make_magic_variable():
    result = make_magic_variable("Repeat Item")
    assert result["WFSerializationType"] == "WFTextTokenAttachment"
    assert result["Value"]["Type"] == "Variable"
    assert result["Value"]["VariableName"] == "Repeat Item"


def test_make_text_with_variable():
    result = make_text_with_variable("Hello ", "UUID-1", "Name", " world")
    assert result["WFSerializationType"] == "WFTextTokenString"
    assert result["Value"]["string"] == "Hello \ufffc world"
    assert "{6, 1}" in result["Value"]["attachmentsByRange"]
    attachment = result["Value"]["attachmentsByRange"]["{6, 1}"]
    assert attachment["OutputUUID"] == "UUID-1"
    assert attachment["OutputName"] == "Name"
    assert attachment["Type"] == "ActionOutput"


def test_make_text_with_variable_at_start():
    result = make_text_with_variable("", "UUID-1", "Name", " suffix")
    assert result["Value"]["string"] == "\ufffc suffix"
    assert "{0, 1}" in result["Value"]["attachmentsByRange"]
