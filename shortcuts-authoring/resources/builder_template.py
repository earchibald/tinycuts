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
