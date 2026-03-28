"""Example: Get Clipboard → Summarize with Apple Intelligence → Show Notification.

Produces a signed shortcut that:
1. Gets the clipboard contents
2. Summarizes them using Apple Intelligence (Writing Tools)
3. Shows the summary as a notification

Requirements: macOS 26+, Apple Intelligence enabled
I/O Contract: input=clipboard, output=notification

Ref: Spec Section 5, Tier 5 — Apple Intelligence action identifiers
Ref: com.apple.WritingTools.WritingToolsAppIntentsExtension.SummarizeTextIntent
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from builder_template import (
    make_shortcut, new_uuid, make_attachment, make_comment,
)
import plistlib
import subprocess

# --- UUIDs for action output linking ---
clipboard_uuid = new_uuid()
summary_uuid = new_uuid()

# --- Actions ---
actions = [
    make_comment(
        "Clipboard Summarizer — Requires Apple Intelligence.\n"
        "Gets clipboard text, summarizes it, and shows a notification.\n"
        "Input: clipboard | Output: notification"
    ),

    # Step 1: Get Clipboard
    make_comment("Step 1: Read the current clipboard contents."),
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.getclipboard",
        "WFWorkflowActionParameters": {
            "UUID": clipboard_uuid,
        },
    },

    # Step 2: Summarize with Apple Intelligence
    make_comment(
        "Step 2: Summarize the clipboard text using Apple Intelligence.\n"
        "Requires: Apple Intelligence enabled in System Settings."
    ),
    {
        "WFWorkflowActionIdentifier":
            "com.apple.WritingTools.WritingToolsAppIntentsExtension.SummarizeTextIntent",
        "WFWorkflowActionParameters": {
            "text": make_attachment(clipboard_uuid, "Clipboard"),
            "summaryType": "summarize",
            "UUID": summary_uuid,
        },
    },

    # Step 3: Show Notification
    make_comment("Step 3: Display the summary as a macOS notification."),
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.notification",
        "WFWorkflowActionParameters": {
            "WFNotificationActionBody": make_attachment(summary_uuid, "Summarize Text"),
            "WFNotificationActionTitle": "Clipboard Summary",
        },
    },
]

# --- Build ---
shortcut = make_shortcut(
    "Clipboard Summarizer",
    actions,
    icon_color=0x4B0082,
    icon_glyph=0xE032,
    input_types=["WFStringContentItem"],
)

output_dir = os.path.dirname(os.path.abspath(__file__))
unsigned_path = os.path.join(output_dir, "clipboard_summarize_unsigned.shortcut")
signed_path = os.path.join(output_dir, "clipboard_summarize.shortcut")

with open(unsigned_path, "wb") as f:
    plistlib.dump(shortcut, f, fmt=plistlib.FMT_BINARY)

# Validate
result = subprocess.run(["plutil", "-lint", unsigned_path], capture_output=True, text=True)
if result.returncode != 0:
    print(f"Validation failed: {result.stderr}", file=sys.stderr)
    sys.exit(1)
print(f"Validated: {unsigned_path}")

# Sign (will fail without Apple ID / network — that's expected in CI)
result = subprocess.run(
    ["shortcuts", "sign", "-m", "anyone", "-i", unsigned_path, "-o", signed_path],
    capture_output=True, text=True,
)
if result.returncode != 0:
    print(f"Signing skipped (expected in CI): {result.stderr}")
    print(f"Unsigned shortcut at: {unsigned_path}")
else:
    print(f"Signed shortcut at: {signed_path}")
    print(f"Import with: open '{signed_path}'")
