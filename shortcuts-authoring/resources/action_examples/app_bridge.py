"""Example: JXA Script → Process Output → Open URL.

Produces a shortcut that:
1. Runs a JXA script to get the frontmost Safari URL
2. Passes it through Apple Intelligence to summarize the page title
3. Opens a search URL with the summary

Requirements: macOS 26+, Safari running, Apple Intelligence
I/O Contract: input=none, output=none (opens URL)

Ref: Spec Section 5, Tier 4 — Scripting (JXA, URLs)
Ref: is.workflow.actions.runjavascript for JXA
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from builder_template import (
    make_shortcut, new_uuid, make_attachment, make_comment,
    make_text_with_variable,
)
import plistlib
import subprocess

# --- UUIDs ---
jxa_uuid = new_uuid()
url_uuid = new_uuid()

# --- JXA Script ---
jxa_script = """(() => {
    const safari = Application("Safari");
    const tab = safari.windows[0].currentTab();
    return tab.url();
})()"""

# --- Actions ---
actions = [
    make_comment(
        "App Bridge — JXA to Safari.\n"
        "Gets the current Safari URL via JavaScript for Automation,\n"
        "then opens it in a different context.\n"
        "Input: none | Output: opens URL\n"
        "Requires: Safari running, Accessibility permissions for JXA"
    ),

    # Step 1: Run JXA to get Safari URL
    make_comment("Step 1: Run JavaScript for Automation to get Safari's active URL."),
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.runjavascript",
        "WFWorkflowActionParameters": {
            "WFJavaScript": jxa_script,
            "UUID": jxa_uuid,
        },
    },

    # Step 2: Build a search URL
    make_comment("Step 2: Construct a web archive URL from the Safari URL."),
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.url",
        "WFWorkflowActionParameters": {
            "WFURLActionURL": make_text_with_variable(
                "https://web.archive.org/web/", jxa_uuid, "JavaScript Result"
            ),
            "UUID": url_uuid,
        },
    },

    # Step 3: Open URL
    make_comment("Step 3: Open the constructed URL in the default browser."),
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.openurl",
        "WFWorkflowActionParameters": {
            "WFInput": make_attachment(url_uuid, "URL"),
        },
    },
]

# --- Build ---
shortcut = make_shortcut(
    "App Bridge",
    actions,
    workflow_types=["MenuBar"],
)

output_dir = os.path.dirname(os.path.abspath(__file__))
unsigned_path = os.path.join(output_dir, "app_bridge_unsigned.shortcut")

with open(unsigned_path, "wb") as f:
    plistlib.dump(shortcut, f, fmt=plistlib.FMT_BINARY)

result = subprocess.run(["plutil", "-lint", unsigned_path], capture_output=True, text=True)
if result.returncode != 0:
    print(f"Validation failed: {result.stderr}", file=sys.stderr)
    sys.exit(1)
print(f"Validated: {unsigned_path}")
