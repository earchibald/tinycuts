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
from builder_template import (
    make_comment, make_if_block, make_repeat_count,
    make_repeat_each, make_menu,
)
import re


def test_make_shortcut_returns_valid_plist_structure():
    actions = []
    result = make_shortcut("Test", actions)
    assert result["WFWorkflowActions"] == []
    assert result["WFWorkflowMinimumClientVersionString"] == "1700"
    assert result["WFWorkflowMinimumClientVersion"] == 1700
    assert result["WFWorkflowClientVersion"] == "1700"
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


def test_make_comment():
    result = make_comment("This is a comment")
    assert result["WFWorkflowActionIdentifier"] == "is.workflow.actions.comment"
    assert result["WFWorkflowActionParameters"]["WFCommentActionText"] == "This is a comment"


def test_make_if_block_structure():
    then_action = {"WFWorkflowActionIdentifier": "test.then", "WFWorkflowActionParameters": {}}
    result = make_if_block("Equals", "hello", [then_action])
    assert len(result) == 3
    assert result[0]["WFWorkflowActionIdentifier"] == "is.workflow.actions.conditional"
    assert result[0]["WFWorkflowActionParameters"]["WFControlFlowMode"] == 0
    assert result[0]["WFWorkflowActionParameters"]["WFCondition"] == "Equals"
    assert result[0]["WFWorkflowActionParameters"]["WFConditionalActionString"] == "hello"
    assert result[1]["WFWorkflowActionIdentifier"] == "test.then"
    assert result[2]["WFWorkflowActionParameters"]["WFControlFlowMode"] == 2
    gid = result[0]["WFWorkflowActionParameters"]["GroupingIdentifier"]
    assert result[2]["WFWorkflowActionParameters"]["GroupingIdentifier"] == gid


def test_make_if_block_with_else():
    then_action = {"WFWorkflowActionIdentifier": "test.then", "WFWorkflowActionParameters": {}}
    else_action = {"WFWorkflowActionIdentifier": "test.else", "WFWorkflowActionParameters": {}}
    result = make_if_block("Has Any Value", None, [then_action], [else_action])
    assert len(result) == 5
    assert result[0]["WFWorkflowActionParameters"]["WFControlFlowMode"] == 0
    assert "WFConditionalActionString" not in result[0]["WFWorkflowActionParameters"]
    assert result[2]["WFWorkflowActionParameters"]["WFControlFlowMode"] == 1
    assert result[4]["WFWorkflowActionParameters"]["WFControlFlowMode"] == 2


def test_make_repeat_count_structure():
    body = [{"WFWorkflowActionIdentifier": "test.body", "WFWorkflowActionParameters": {}}]
    result = make_repeat_count(5, body)
    assert len(result) == 3
    assert result[0]["WFWorkflowActionIdentifier"] == "is.workflow.actions.repeat.count"
    assert result[0]["WFWorkflowActionParameters"]["WFRepeatCount"] == 5
    assert result[0]["WFWorkflowActionParameters"]["WFControlFlowMode"] == 0
    assert result[2]["WFWorkflowActionParameters"]["WFControlFlowMode"] == 2
    gid = result[0]["WFWorkflowActionParameters"]["GroupingIdentifier"]
    assert result[2]["WFWorkflowActionParameters"]["GroupingIdentifier"] == gid


def test_make_repeat_each_structure():
    input_ref = make_attachment("UUID-1", "Items")
    body = [{"WFWorkflowActionIdentifier": "test.body", "WFWorkflowActionParameters": {}}]
    result = make_repeat_each(input_ref, body)
    assert len(result) == 3
    assert result[0]["WFWorkflowActionIdentifier"] == "is.workflow.actions.repeat.each"
    assert result[0]["WFWorkflowActionParameters"]["WFInput"] == input_ref
    assert result[0]["WFWorkflowActionParameters"]["WFControlFlowMode"] == 0
    assert result[2]["WFWorkflowActionParameters"]["WFControlFlowMode"] == 2


def test_make_menu_structure():
    case_actions = {
        "Option A": [{"WFWorkflowActionIdentifier": "test.a", "WFWorkflowActionParameters": {}}],
        "Option B": [{"WFWorkflowActionIdentifier": "test.b", "WFWorkflowActionParameters": {}}],
    }
    result = make_menu("Pick one", ["Option A", "Option B"], case_actions)
    assert len(result) == 6
    assert result[0]["WFWorkflowActionParameters"]["WFControlFlowMode"] == 0
    assert result[0]["WFWorkflowActionParameters"]["WFMenuItems"] == ["Option A", "Option B"]
    assert result[0]["WFWorkflowActionParameters"]["WFMenuPrompt"] == "Pick one"
    assert result[1]["WFWorkflowActionParameters"]["WFMenuItemTitle"] == "Option A"
    assert result[3]["WFWorkflowActionParameters"]["WFMenuItemTitle"] == "Option B"
    assert result[5]["WFWorkflowActionParameters"]["WFControlFlowMode"] == 2
