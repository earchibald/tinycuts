"""Example: Use Model (Apple Intelligence) → Adjust Tone → Show Result.

Produces a shortcut that:
1. Takes stdin text input
2. Sends it to Apple Intelligence with a prompt
3. Adjusts the tone of the response to professional
4. Outputs the result to stdout

Requirements: macOS 26+, Apple Intelligence enabled
I/O Contract: input=stdin/text, output=stdout/text

Ref: Spec Section 5, Tier 5 — is.workflow.actions.askllm
Ref: com.apple.WritingTools.WritingToolsAppIntentsExtension.AdjustToneIntent
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
model_uuid = new_uuid()
tone_uuid = new_uuid()

# --- Actions ---
actions = [
    make_comment(
        "AI Pipeline — Requires Apple Intelligence.\n"
        "Takes text input, processes with AI model, adjusts tone.\n"
        "Input: stdin/text | Output: stdout/text"
    ),

    # Step 1: Get Shortcut Input
    make_comment("Step 1: Receive text input from stdin or share sheet."),
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.gettext",
        "WFWorkflowActionParameters": {
            "WFTextActionText": {
                "Value": {
                    "Type": "ExtensionInput",
                },
                "WFSerializationType": "WFTextTokenAttachment",
            },
            "UUID": input_uuid,
        },
    },

    # Step 2: Use Model (Apple Intelligence)
    make_comment(
        "Step 2: Send text to Apple Intelligence with instructions.\n"
        "Uses the on-device or Private Cloud Compute model."
    ),
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.askllm",
        "WFWorkflowActionParameters": {
            "WFLLMPrompt": make_text_with_variable(
                "Rewrite the following text as a concise executive summary:\n\n",
                input_uuid, "Text",
            ),
            "WFGenerativeResultType": "Text",
            "UUID": model_uuid,
        },
    },

    # Step 3: Adjust Tone to Professional
    make_comment(
        "Step 3: Adjust tone to professional using Writing Tools.\n"
        "Requires: Apple Intelligence enabled."
    ),
    {
        "WFWorkflowActionIdentifier":
            "com.apple.WritingTools.WritingToolsAppIntentsExtension.AdjustToneIntent",
        "WFWorkflowActionParameters": {
            "text": make_attachment(model_uuid, "Response"),
            "tone": "professional",
            "UUID": tone_uuid,
        },
    },

    # Step 4: Output result
    make_comment("Step 4: Output the final text to stdout."),
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.output",
        "WFWorkflowActionParameters": {
            "WFOutput": make_attachment(tone_uuid, "Adjust Tone of Text"),
        },
    },
]

# --- Build ---
shortcut = make_shortcut(
    "AI Pipeline",
    actions,
    input_types=["WFStringContentItem"],
    workflow_types=["MenuBar", "QuickActions"],
)

output_dir = os.path.dirname(os.path.abspath(__file__))
unsigned_path = os.path.join(output_dir, "ai_pipeline_unsigned.shortcut")
signed_path = os.path.join(output_dir, "ai_pipeline.shortcut")

with open(unsigned_path, "wb") as f:
    plistlib.dump(shortcut, f, fmt=plistlib.FMT_BINARY)

result = subprocess.run(["plutil", "-lint", unsigned_path], capture_output=True, text=True)
if result.returncode != 0:
    print(f"Validation failed: {result.stderr}", file=sys.stderr)
    sys.exit(1)
print(f"Validated: {unsigned_path}")

result = subprocess.run(
    ["shortcuts", "sign", "-m", "anyone", "-i", unsigned_path, "-o", signed_path],
    capture_output=True, text=True,
)
if result.returncode != 0:
    print(f"Signing skipped: {result.stderr}")
else:
    print(f"Signed: {signed_path}")
