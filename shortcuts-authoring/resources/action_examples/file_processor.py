"""Example: File Input → Get Text → Proofread → Save to File.

Produces a shortcut that:
1. Receives a file path via stdin
2. Gets the file contents
3. Proofreads the text with Apple Intelligence
4. Saves the proofread version alongside the original

Requirements: macOS 26+, Apple Intelligence enabled, file system access
I/O Contract: input=stdin/text (file path), output=file-path

Ref: Spec Section 5, Tier 2 — File System actions
Ref: com.apple.WritingTools.WritingToolsAppIntentsExtension.ProofreadIntent
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
input_uuid = new_uuid()
file_uuid = new_uuid()
text_uuid = new_uuid()
proofread_uuid = new_uuid()

# --- Actions ---
actions = [
    make_comment(
        "File Proofreader — Requires Apple Intelligence.\n"
        "Reads a text file, proofreads it, saves the result.\n"
        "Input: file path via stdin | Output: proofread file path"
    ),

    # Step 1: Get file path from input
    make_comment("Step 1: Receive file path from shortcut input."),
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.gettext",
        "WFWorkflowActionParameters": {
            "WFTextActionText": {
                "Value": {"Type": "ExtensionInput"},
                "WFSerializationType": "WFTextTokenAttachment",
            },
            "UUID": input_uuid,
        },
    },

    # Step 2: Get file contents
    make_comment("Step 2: Read the file at the given path."),
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.documentpicker.open",
        "WFWorkflowActionParameters": {
            "WFFile": make_attachment(input_uuid, "Text"),
            "UUID": file_uuid,
        },
    },

    # Step 3: Extract text
    make_comment("Step 3: Extract text content from the file."),
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.gettext",
        "WFWorkflowActionParameters": {
            "WFTextActionText": make_attachment(file_uuid, "File"),
            "UUID": text_uuid,
        },
    },

    # Step 4: Proofread with Apple Intelligence
    make_comment(
        "Step 4: Proofread the text using Apple Intelligence Writing Tools.\n"
        "Requires: Apple Intelligence enabled in System Settings."
    ),
    {
        "WFWorkflowActionIdentifier":
            "com.apple.WritingTools.WritingToolsAppIntentsExtension.ProofreadIntent",
        "WFWorkflowActionParameters": {
            "text": make_attachment(text_uuid, "Text"),
            "UUID": proofread_uuid,
        },
    },

    # Step 5: Save proofread file
    make_comment("Step 5: Save the proofread text to a new file."),
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.documentpicker.save",
        "WFWorkflowActionParameters": {
            "WFInput": make_attachment(proofread_uuid, "Proofread Text"),
            "WFFileDestinationPath": make_text_with_variable(
                "", input_uuid, "Text", ".proofread.txt"
            ),
        },
    },
]

# --- Build ---
shortcut = make_shortcut(
    "File Proofreader",
    actions,
    input_types=["WFStringContentItem", "WFFileContentItem"],
    workflow_types=["MenuBar", "QuickActions"],
)

output_dir = os.path.dirname(os.path.abspath(__file__))
unsigned_path = os.path.join(output_dir, "file_processor_unsigned.shortcut")

with open(unsigned_path, "wb") as f:
    plistlib.dump(shortcut, f, fmt=plistlib.FMT_BINARY)

result = subprocess.run(["plutil", "-lint", unsigned_path], capture_output=True, text=True)
if result.returncode != 0:
    print(f"Validation failed: {result.stderr}", file=sys.stderr)
    sys.exit(1)
print(f"Validated: {unsigned_path}")
