"""Shortcut Builder Template.

Copy this file and fill in the `actions` list to create a macOS Shortcut.
Uses Python stdlib only (plistlib, uuid, subprocess).

Ref: Zachary7829's format docs — https://zachary7829.github.io/blog/shortcuts/fileformat
Ref: Python plistlib — https://docs.python.org/3/library/plistlib.html
"""
import plistlib
import uuid
import subprocess
import sys


def make_shortcut(name, actions,
                  icon_color=0x4B0082, icon_glyph=0xE032,
                  input_types=None, workflow_types=None):
    """Build a complete shortcut plist structure."""
    return {
        "WFWorkflowMinimumClientVersionString": "1700",
        "WFWorkflowMinimumClientVersion": 1700,
        "WFWorkflowClientVersion": 1700,
        "WFWorkflowClientRelease": "26.0",
        "WFWorkflowIcon": {
            "WFWorkflowIconStartColor": icon_color,
            "WFWorkflowIconGlyphNumber": icon_glyph,
        },
        "WFWorkflowInputContentItemClasses": input_types or [
            "WFStringContentItem",
            "WFURLContentItem",
        ],
        "WFWorkflowTypes": workflow_types or [
            "MenuBar",
            "QuickActions",
        ],
        "WFWorkflowHasShortcutInputVariables": True,
        "WFWorkflowActions": actions,
        "WFWorkflowImportQuestions": [],
    }


def new_uuid():
    """Generate an uppercase UUID for action output linking."""
    return str(uuid.uuid4()).upper()


def make_attachment(output_uuid, output_name):
    """Create a WFTextTokenAttachment referencing a previous action's output."""
    return {
        "Value": {
            "OutputName": output_name,
            "OutputUUID": output_uuid,
            "Type": "ActionOutput",
        },
        "WFSerializationType": "WFTextTokenAttachment",
    }


def make_magic_variable(variable_name):
    """Create a WFTextTokenAttachment for a magic variable (e.g., 'Repeat Item')."""
    return {
        "Value": {
            "Type": "Variable",
            "VariableName": variable_name,
        },
        "WFSerializationType": "WFTextTokenAttachment",
    }


def make_text_with_variable(text_before, output_uuid, output_name, text_after=""):
    """Create a WFTextTokenString with a variable embedded in text."""
    # Note: position uses NSString character indices (UTF-16 code units).
    # len() works for ASCII/BMP text. For emoji/non-BMP chars,
    # use: position = len(text_before.encode('utf-16-le')) // 2
    position = len(text_before)
    full_string = text_before + "\ufffc" + text_after
    return {
        "Value": {
            "string": full_string,
            "attachmentsByRange": {
                f"{{{position}, 1}}": {
                    "OutputName": output_name,
                    "OutputUUID": output_uuid,
                    "Type": "ActionOutput",
                }
            },
        },
        "WFSerializationType": "WFTextTokenString",
    }


def make_comment(text):
    """Create a comment action visible in the Shortcuts editor."""
    return {
        "WFWorkflowActionIdentifier": "is.workflow.actions.comment",
        "WFWorkflowActionParameters": {
            "WFCommentActionText": text,
        },
    }


def make_if_block(condition, condition_value, then_actions, else_actions=None):
    """Create If/Otherwise/End If with shared GroupingIdentifier."""
    gid = new_uuid()
    end_uuid = new_uuid()
    actions = []
    if_params = {
        "GroupingIdentifier": gid,
        "WFControlFlowMode": 0,
        "WFCondition": condition,
    }
    if condition_value is not None:
        if_params["WFConditionalActionString"] = condition_value
    actions.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": if_params,
    })
    actions.extend(then_actions)
    if else_actions:
        actions.append({
            "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
            "WFWorkflowActionParameters": {
                "GroupingIdentifier": gid,
                "WFControlFlowMode": 1,
            },
        })
        actions.extend(else_actions)
    actions.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {
            "GroupingIdentifier": gid,
            "UUID": end_uuid,
            "WFControlFlowMode": 2,
        },
    })
    return actions


def make_repeat_count(count, body_actions):
    """Create Repeat N Times / End Repeat with shared GroupingIdentifier."""
    gid = new_uuid()
    end_uuid = new_uuid()
    actions = [{
        "WFWorkflowActionIdentifier": "is.workflow.actions.repeat.count",
        "WFWorkflowActionParameters": {
            "GroupingIdentifier": gid,
            "WFControlFlowMode": 0,
            "WFRepeatCount": count,
        },
    }]
    actions.extend(body_actions)
    actions.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.repeat.count",
        "WFWorkflowActionParameters": {
            "GroupingIdentifier": gid,
            "UUID": end_uuid,
            "WFControlFlowMode": 2,
        },
    })
    return actions


def make_repeat_each(input_ref, body_actions):
    """Create Repeat with Each / End Repeat with shared GroupingIdentifier."""
    gid = new_uuid()
    end_uuid = new_uuid()
    actions = [{
        "WFWorkflowActionIdentifier": "is.workflow.actions.repeat.each",
        "WFWorkflowActionParameters": {
            "GroupingIdentifier": gid,
            "WFControlFlowMode": 0,
            "WFInput": input_ref,
        },
    }]
    actions.extend(body_actions)
    actions.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.repeat.each",
        "WFWorkflowActionParameters": {
            "GroupingIdentifier": gid,
            "UUID": end_uuid,
            "WFControlFlowMode": 2,
        },
    })
    return actions


def make_menu(prompt, items, case_actions_map):
    """Create Choose from Menu with cases."""
    gid = new_uuid()
    end_uuid = new_uuid()
    actions = [{
        "WFWorkflowActionIdentifier": "is.workflow.actions.choosefrommenu",
        "WFWorkflowActionParameters": {
            "GroupingIdentifier": gid,
            "WFControlFlowMode": 0,
            "WFMenuItems": items,
            "WFMenuPrompt": prompt,
        },
    }]
    for item in items:
        actions.append({
            "WFWorkflowActionIdentifier": "is.workflow.actions.choosefrommenu",
            "WFWorkflowActionParameters": {
                "GroupingIdentifier": gid,
                "WFControlFlowMode": 1,
                "WFMenuItemTitle": item,
            },
        })
        actions.extend(case_actions_map.get(item, []))
    actions.append({
        "WFWorkflowActionIdentifier": "is.workflow.actions.choosefrommenu",
        "WFWorkflowActionParameters": {
            "GroupingIdentifier": gid,
            "UUID": end_uuid,
            "WFControlFlowMode": 2,
        },
    })
    return actions


# === ACTIONS GO HERE ===
actions = []


if __name__ == "__main__":
    shortcut = make_shortcut("My Shortcut", actions)
    with open("unsigned.shortcut", "wb") as f:
        plistlib.dump(shortcut, f, fmt=plistlib.FMT_BINARY)
    result = subprocess.run(["plutil", "-lint", "unsigned.shortcut"], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Plist validation failed: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    print("Plist validation passed")
    result = subprocess.run(
        ["shortcuts", "sign", "-m", "anyone", "-i", "unsigned.shortcut", "-o", "signed.shortcut"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"Signing failed: {result.stderr}", file=sys.stderr)
        print("Common causes: malformed plist, missing Apple ID, no network for iCloud notarization")
        sys.exit(1)
    print("Signed shortcut written to signed.shortcut")
    print("Import with: open signed.shortcut")
    print("Debug with: plutil -convert xml1 -o debug.xml unsigned.shortcut")
