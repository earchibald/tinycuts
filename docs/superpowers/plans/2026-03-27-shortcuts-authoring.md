# Shortcuts Authoring Skill — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a skill that teaches agents to author macOS Shortcuts as binary plists, sign them, and package them as Claude Code plugins for a marketplace of macOS automation capabilities.

**Architecture:** The skill is a `SKILL.md` document with resource files. The builder template (`builder_template.py`) provides Python helpers for plist assembly, variable wiring, control flow, and signing. Action examples are complete, runnable Python scripts that produce real `.shortcut` files. A plugin template provides the skeleton for distribution packaging.

**Tech Stack:** Python 3 stdlib (`plistlib`, `uuid`, `subprocess`), macOS `shortcuts` CLI, macOS `plutil` CLI

**Spec:** `docs/superpowers/specs/2026-03-27-shortcuts-authoring-design.md`

---

## File Structure

```
shortcuts-authoring/
├── SKILL.md                              # Main skill document (format ref, action catalog, workflow, packaging)
├── resources/
│   ├── builder_template.py               # Python builder with scaffold + helpers
│   ├── plugin_template/
│   │   ├── SKILL.md.template             # Published plugin SKILL.md template
│   │   └── install.sh.template           # Install hook template
│   └── action_examples/
│       ├── clipboard_summarize.py        # Get Clipboard → Summarize → Notification
│       ├── file_processor.py             # File input → Transform → Save
│       ├── app_bridge.py                 # JXA → App automation → Output
│       └── ai_pipeline.py               # Use Model → Writing Tools chain
└── tests/
    ├── test_builder_template.py          # Unit tests for builder helpers
    └── test_plist_output.py              # Integration tests: build → plutil -lint
```

---

### Task 1: Initialize Project and Git

**Files:**
- Create: `shortcuts-authoring/` directory structure
- Create: `.gitignore`

- [ ] **Step 1: Initialize git repo**

```bash
cd /Users/earchibald/work/github/earchibald/tinycuts
git init
```

- [ ] **Step 2: Create .gitignore**

Create `/Users/earchibald/work/github/earchibald/tinycuts/.gitignore`:

```
# Build artifacts
*.shortcut
unsigned.shortcut
signed.shortcut
debug.xml

# Python
__pycache__/
*.pyc
.pytest_cache/

# macOS
.DS_Store
```

- [ ] **Step 3: Create directory structure**

```bash
mkdir -p shortcuts-authoring/resources/plugin_template
mkdir -p shortcuts-authoring/resources/action_examples
mkdir -p shortcuts-authoring/tests
```

- [ ] **Step 4: Commit**

```bash
git add .gitignore docs/ shortcuts-authoring/
git commit -m "chore: initialize project with spec and directory structure"
```

---

### Task 2: Builder Template — Scaffold and Serialization

**Files:**
- Create: `shortcuts-authoring/resources/builder_template.py`
- Create: `shortcuts-authoring/tests/test_builder_template.py`

This task covers the `make_shortcut()` scaffold function and the build/validate/sign pipeline. No helpers yet — just the skeleton.

- [ ] **Step 1: Write failing test for make_shortcut**

Create `shortcuts-authoring/tests/test_builder_template.py`:

```python
"""Tests for builder_template.py scaffold and helpers."""
import plistlib
import sys
import os

# Add resources to path so we can import the template as a module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "resources"))

from builder_template import make_shortcut


def test_make_shortcut_returns_valid_plist_structure():
    """make_shortcut produces a dict with all required top-level keys."""
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
    """make_shortcut accepts custom input types."""
    result = make_shortcut("Test", [], input_types=["WFImageContentItem"])
    assert result["WFWorkflowInputContentItemClasses"] == ["WFImageContentItem"]


def test_make_shortcut_custom_workflow_types():
    """make_shortcut accepts custom workflow types."""
    result = make_shortcut("Test", [], workflow_types=["ActionExtension"])
    assert result["WFWorkflowTypes"] == ["ActionExtension"]


def test_make_shortcut_serializes_to_binary_plist():
    """make_shortcut output can be serialized to binary plist."""
    import tempfile
    result = make_shortcut("Test", [])
    with tempfile.NamedTemporaryFile(suffix=".plist", delete=False) as f:
        plistlib.dump(result, f, fmt=plistlib.FMT_BINARY)
        path = f.name

    # Read it back
    with open(path, "rb") as f:
        loaded = plistlib.load(f)
    os.unlink(path)

    assert loaded["WFWorkflowActions"] == []
    assert loaded["WFWorkflowMinimumClientVersion"] == 1700
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/earchibald/work/github/earchibald/tinycuts && python3 -m pytest shortcuts-authoring/tests/test_builder_template.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'builder_template'`

- [ ] **Step 3: Write builder_template.py with make_shortcut and pipeline**

Create `shortcuts-authoring/resources/builder_template.py`:

```python
"""Shortcut Builder Template.

Copy this file and fill in the `actions` list to create a macOS Shortcut.
Uses Python stdlib only (plistlib, uuid, subprocess).

Ref: Spec at docs/superpowers/specs/2026-03-27-shortcuts-authoring-design.md
Ref: Zachary7829's format docs — https://zachary7829.github.io/blog/shortcuts/fileformat
Ref: Python plistlib — https://docs.python.org/3/library/plistlib.html
"""
import plistlib
import uuid
import subprocess
import sys


# ---------------------------------------------------------------------------
# Scaffold
# ---------------------------------------------------------------------------

def make_shortcut(name, actions,
                  icon_color=0x4B0082, icon_glyph=0xE032,
                  input_types=None, workflow_types=None):
    """Build a complete shortcut plist structure.

    Args:
        name: Shortcut display name (used for file naming, not embedded in plist).
        actions: List of action dicts.
        icon_color: Integer color value for the shortcut icon.
        icon_glyph: Integer glyph number for the shortcut icon.
        input_types: List of accepted WFContentItemClass strings.
            Defaults to ["WFStringContentItem", "WFURLContentItem"].
        workflow_types: List of workflow type strings.
            Defaults to ["MenuBar", "QuickActions"].
    """
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
# (Helpers are added in subsequent tasks)

actions = [
    # Agent fills this in from the action catalog
]


# ---------------------------------------------------------------------------
# Build / Validate / Sign pipeline
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    shortcut = make_shortcut("My Shortcut", actions)

    with open("unsigned.shortcut", "wb") as f:
        plistlib.dump(shortcut, f, fmt=plistlib.FMT_BINARY)

    # Validate
    result = subprocess.run(
        ["plutil", "-lint", "unsigned.shortcut"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"Plist validation failed: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    print("Plist validation passed")

    # Sign
    result = subprocess.run(
        ["shortcuts", "sign", "-m", "anyone",
         "-i", "unsigned.shortcut", "-o", "signed.shortcut"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"Signing failed: {result.stderr}", file=sys.stderr)
        print("Common causes: malformed plist, missing Apple ID, "
              "no network for iCloud notarization")
        sys.exit(1)

    print("Signed shortcut written to signed.shortcut")
    print("Import with: open signed.shortcut")
    print("Debug with: plutil -convert xml1 -o debug.xml unsigned.shortcut")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/earchibald/work/github/earchibald/tinycuts && python3 -m pytest shortcuts-authoring/tests/test_builder_template.py -v`
Expected: All 4 tests PASS

- [ ] **Step 5: Commit**

```bash
git add shortcuts-authoring/resources/builder_template.py shortcuts-authoring/tests/test_builder_template.py
git commit -m "feat: add builder template scaffold with make_shortcut and build pipeline"
```

---

### Task 3: Builder Template — Variable Helpers

**Files:**
- Modify: `shortcuts-authoring/resources/builder_template.py`
- Modify: `shortcuts-authoring/tests/test_builder_template.py`

Add `new_uuid`, `make_attachment`, `make_magic_variable`, `make_text_with_variable`.

> Ref: Spec Section 3 (Variable System) — WFTextTokenAttachment and WFTextTokenString structures extracted from Apple gallery shortcuts in `WorkflowKit.framework/Resources/Gallery.bundle/`.

- [ ] **Step 1: Write failing tests for variable helpers**

Append to `shortcuts-authoring/tests/test_builder_template.py`:

```python
from builder_template import (
    new_uuid, make_attachment, make_magic_variable, make_text_with_variable,
)
import re


def test_new_uuid_format():
    """new_uuid returns uppercase UUID string."""
    uid = new_uuid()
    assert re.match(r"^[A-F0-9]{8}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{12}$", uid)


def test_new_uuid_unique():
    """new_uuid returns unique values."""
    assert new_uuid() != new_uuid()


def test_make_attachment():
    """make_attachment creates WFTextTokenAttachment dict."""
    result = make_attachment("ABCD-1234", "Clipboard")
    assert result["WFSerializationType"] == "WFTextTokenAttachment"
    assert result["Value"]["Type"] == "ActionOutput"
    assert result["Value"]["OutputUUID"] == "ABCD-1234"
    assert result["Value"]["OutputName"] == "Clipboard"


def test_make_magic_variable():
    """make_magic_variable creates WFTextTokenAttachment with Variable type."""
    result = make_magic_variable("Repeat Item")
    assert result["WFSerializationType"] == "WFTextTokenAttachment"
    assert result["Value"]["Type"] == "Variable"
    assert result["Value"]["VariableName"] == "Repeat Item"


def test_make_text_with_variable():
    """make_text_with_variable creates WFTextTokenString with embedded var."""
    result = make_text_with_variable("Hello ", "UUID-1", "Name", " world")
    assert result["WFSerializationType"] == "WFTextTokenString"
    assert result["Value"]["string"] == "Hello \ufffc world"
    assert "{6, 1}" in result["Value"]["attachmentsByRange"]
    attachment = result["Value"]["attachmentsByRange"]["{6, 1}"]
    assert attachment["OutputUUID"] == "UUID-1"
    assert attachment["OutputName"] == "Name"
    assert attachment["Type"] == "ActionOutput"


def test_make_text_with_variable_at_start():
    """make_text_with_variable works when variable is at position 0."""
    result = make_text_with_variable("", "UUID-1", "Name", " suffix")
    assert result["Value"]["string"] == "\ufffc suffix"
    assert "{0, 1}" in result["Value"]["attachmentsByRange"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest shortcuts-authoring/tests/test_builder_template.py -v -k "uuid or attachment or magic or text_with"`
Expected: FAIL — `ImportError: cannot import name 'new_uuid'`

- [ ] **Step 3: Add variable helpers to builder_template.py**

Add after `make_shortcut()`, before `# === ACTIONS GO HERE ===`:

```python
# ---------------------------------------------------------------------------
# Variable Helpers
# Ref: Spec Section 3 — Variable System
# Ref: Structures from Apple gallery .wflow files (MorningReport, ActionItems)
# ---------------------------------------------------------------------------

def new_uuid():
    """Generate an uppercase UUID for action output linking."""
    return str(uuid.uuid4()).upper()


def make_attachment(output_uuid, output_name):
    """Create a WFTextTokenAttachment referencing a previous action's output.

    Use when a parameter is purely a variable reference (no surrounding text).

    Ref: WFTextTokenAttachment in Spec Section 3
    """
    return {
        "Value": {
            "OutputName": output_name,
            "OutputUUID": output_uuid,
            "Type": "ActionOutput",
        },
        "WFSerializationType": "WFTextTokenAttachment",
    }


def make_magic_variable(variable_name):
    """Create a WFTextTokenAttachment for a magic variable (e.g., 'Repeat Item').

    Ref: Magic Variables in Spec Section 3
    """
    return {
        "Value": {
            "Type": "Variable",
            "VariableName": variable_name,
        },
        "WFSerializationType": "WFTextTokenAttachment",
    }


def make_text_with_variable(text_before, output_uuid, output_name, text_after=""):
    """Create a WFTextTokenString with a variable embedded in text.

    Inserts U+FFFC at the variable position and builds attachmentsByRange.
    For multiple variables in one string, build the dict manually.

    Note: position uses NSString character indices (UTF-16 code units).
    len() works for ASCII/BMP text. For strings with emoji or non-BMP chars,
    use: position = len(text_before.encode('utf-16-le')) // 2

    Ref: WFTextTokenString in Spec Section 3
    """
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest shortcuts-authoring/tests/test_builder_template.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add shortcuts-authoring/resources/builder_template.py shortcuts-authoring/tests/test_builder_template.py
git commit -m "feat: add variable helpers (attachment, magic variable, text with variable)"
```

---

### Task 4: Builder Template — Control Flow Helpers

**Files:**
- Modify: `shortcuts-authoring/resources/builder_template.py`
- Modify: `shortcuts-authoring/tests/test_builder_template.py`

Add `make_comment`, `make_if_block`, `make_repeat_count`, `make_repeat_each`, `make_menu`.

> Ref: Spec Section 3 (Control Flow) — GroupingIdentifier and WFControlFlowMode patterns from Apple's DocumentReview.wflow and ActionItems.wflow.

- [ ] **Step 1: Write failing tests for control flow helpers**

Append to `shortcuts-authoring/tests/test_builder_template.py`:

```python
from builder_template import (
    make_comment, make_if_block, make_repeat_count,
    make_repeat_each, make_menu,
)


def test_make_comment():
    """make_comment creates a comment action."""
    result = make_comment("This is a comment")
    assert result["WFWorkflowActionIdentifier"] == "is.workflow.actions.comment"
    assert result["WFWorkflowActionParameters"]["WFCommentActionText"] == "This is a comment"


def test_make_if_block_structure():
    """make_if_block produces If/End If with shared GroupingIdentifier."""
    then_action = {"WFWorkflowActionIdentifier": "test.then", "WFWorkflowActionParameters": {}}
    result = make_if_block("Equals", "hello", [then_action])

    assert len(result) == 3  # If + then_action + End If
    # First: If (mode 0)
    assert result[0]["WFWorkflowActionIdentifier"] == "is.workflow.actions.conditional"
    assert result[0]["WFWorkflowActionParameters"]["WFControlFlowMode"] == 0
    assert result[0]["WFWorkflowActionParameters"]["WFCondition"] == "Equals"
    assert result[0]["WFWorkflowActionParameters"]["WFConditionalActionString"] == "hello"
    # Middle: then action
    assert result[1]["WFWorkflowActionIdentifier"] == "test.then"
    # Last: End If (mode 2)
    assert result[2]["WFWorkflowActionParameters"]["WFControlFlowMode"] == 2
    # Shared GroupingIdentifier
    gid = result[0]["WFWorkflowActionParameters"]["GroupingIdentifier"]
    assert result[2]["WFWorkflowActionParameters"]["GroupingIdentifier"] == gid


def test_make_if_block_with_else():
    """make_if_block with else_actions adds Otherwise (mode 1)."""
    then_action = {"WFWorkflowActionIdentifier": "test.then", "WFWorkflowActionParameters": {}}
    else_action = {"WFWorkflowActionIdentifier": "test.else", "WFWorkflowActionParameters": {}}
    result = make_if_block("Has Any Value", None, [then_action], [else_action])

    assert len(result) == 5  # If + then + Otherwise + else + End If
    assert result[0]["WFWorkflowActionParameters"]["WFControlFlowMode"] == 0
    assert "WFConditionalActionString" not in result[0]["WFWorkflowActionParameters"]
    assert result[2]["WFWorkflowActionParameters"]["WFControlFlowMode"] == 1
    assert result[4]["WFWorkflowActionParameters"]["WFControlFlowMode"] == 2


def test_make_repeat_count_structure():
    """make_repeat_count produces Repeat/End Repeat with count."""
    body = [{"WFWorkflowActionIdentifier": "test.body", "WFWorkflowActionParameters": {}}]
    result = make_repeat_count(5, body)

    assert len(result) == 3  # Repeat + body + End Repeat
    assert result[0]["WFWorkflowActionIdentifier"] == "is.workflow.actions.repeat.count"
    assert result[0]["WFWorkflowActionParameters"]["WFRepeatCount"] == 5
    assert result[0]["WFWorkflowActionParameters"]["WFControlFlowMode"] == 0
    assert result[2]["WFWorkflowActionParameters"]["WFControlFlowMode"] == 2
    gid = result[0]["WFWorkflowActionParameters"]["GroupingIdentifier"]
    assert result[2]["WFWorkflowActionParameters"]["GroupingIdentifier"] == gid


def test_make_repeat_each_structure():
    """make_repeat_each produces Repeat Each/End Repeat."""
    input_ref = make_attachment("UUID-1", "Items")
    body = [{"WFWorkflowActionIdentifier": "test.body", "WFWorkflowActionParameters": {}}]
    result = make_repeat_each(input_ref, body)

    assert len(result) == 3
    assert result[0]["WFWorkflowActionIdentifier"] == "is.workflow.actions.repeat.each"
    assert result[0]["WFWorkflowActionParameters"]["WFInput"] == input_ref
    assert result[0]["WFWorkflowActionParameters"]["WFControlFlowMode"] == 0
    assert result[2]["WFWorkflowActionParameters"]["WFControlFlowMode"] == 2


def test_make_menu_structure():
    """make_menu produces Menu start + cases + End Menu."""
    case_actions = {
        "Option A": [{"WFWorkflowActionIdentifier": "test.a", "WFWorkflowActionParameters": {}}],
        "Option B": [{"WFWorkflowActionIdentifier": "test.b", "WFWorkflowActionParameters": {}}],
    }
    result = make_menu("Pick one", ["Option A", "Option B"], case_actions)

    # Start (mode 0) + Case A (mode 1) + action_a + Case B (mode 1) + action_b + End (mode 2)
    assert len(result) == 6
    assert result[0]["WFWorkflowActionParameters"]["WFControlFlowMode"] == 0
    assert result[0]["WFWorkflowActionParameters"]["WFMenuItems"] == ["Option A", "Option B"]
    assert result[0]["WFWorkflowActionParameters"]["WFMenuPrompt"] == "Pick one"
    assert result[1]["WFWorkflowActionParameters"]["WFMenuItemTitle"] == "Option A"
    assert result[3]["WFWorkflowActionParameters"]["WFMenuItemTitle"] == "Option B"
    assert result[5]["WFWorkflowActionParameters"]["WFControlFlowMode"] == 2
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest shortcuts-authoring/tests/test_builder_template.py -v -k "comment or if_block or repeat or menu"`
Expected: FAIL — `ImportError`

- [ ] **Step 3: Add control flow and comment helpers to builder_template.py**

Add after the variable helpers, before `# === ACTIONS GO HERE ===`:

```python
# ---------------------------------------------------------------------------
# Comment Helper
# Ref: Spec Section 13 — Commenting & Readability
# ---------------------------------------------------------------------------

def make_comment(text):
    """Create a comment action visible in the Shortcuts editor.

    Use liberally: shortcuts must be self-explicating for users who inspect them.
    """
    return {
        "WFWorkflowActionIdentifier": "is.workflow.actions.comment",
        "WFWorkflowActionParameters": {
            "WFCommentActionText": text,
        },
    }


# ---------------------------------------------------------------------------
# Control Flow Helpers
# Ref: Spec Section 3 — Control Flow
# Ref: Patterns from Apple's DocumentReview.wflow and ActionItems.wflow
# WFControlFlowMode: 0=start, 1=middle (Otherwise/case), 2=end
# ---------------------------------------------------------------------------

def make_if_block(condition, condition_value, then_actions, else_actions=None):
    """Create If/Otherwise/End If with shared GroupingIdentifier.

    Args:
        condition: e.g., "Equals", "Has Any Value", "Is Greater Than"
        condition_value: comparison value, or None for "Has Any Value"
        then_actions: list of action dicts for the If branch
        else_actions: optional list for the Otherwise branch

    Returns: flat list of action dicts
    """
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
    """Create Repeat with Each / End Repeat with shared GroupingIdentifier.

    Args:
        input_ref: WFTextTokenAttachment dict (from make_attachment)
        body_actions: list of action dicts (can use make_magic_variable("Repeat Item"))
    """
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
    """Create Choose from Menu with cases.

    Args:
        prompt: menu prompt string
        items: list of menu item strings
        case_actions_map: dict mapping item string -> list of action dicts
    """
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest shortcuts-authoring/tests/test_builder_template.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add shortcuts-authoring/resources/builder_template.py shortcuts-authoring/tests/test_builder_template.py
git commit -m "feat: add control flow helpers (if, repeat, menu) and comment helper"
```

---

### Task 5: Integration Test — Build and Validate a Real Shortcut

**Files:**
- Create: `shortcuts-authoring/tests/test_plist_output.py`

This test builds a shortcut using the helpers and validates the binary plist output with `plutil -lint`. It does NOT sign or import (that requires user interaction).

- [ ] **Step 1: Write integration test**

Create `shortcuts-authoring/tests/test_plist_output.py`:

```python
"""Integration tests: build shortcuts and validate with plutil."""
import os
import sys
import plistlib
import subprocess
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "resources"))

from builder_template import (
    make_shortcut, new_uuid, make_attachment, make_comment,
    make_text_with_variable, make_if_block, make_repeat_count,
)


def _build_and_validate(actions):
    """Build a shortcut plist and validate with plutil -lint. Returns loaded plist."""
    shortcut = make_shortcut("Test Shortcut", actions)
    with tempfile.NamedTemporaryFile(suffix=".shortcut", delete=False) as f:
        plistlib.dump(shortcut, f, fmt=plistlib.FMT_BINARY)
        path = f.name
    try:
        result = subprocess.run(
            ["plutil", "-lint", path],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, f"plutil -lint failed: {result.stderr}"

        with open(path, "rb") as f:
            return plistlib.load(f)
    finally:
        os.unlink(path)


def test_empty_shortcut_validates():
    """An empty shortcut passes plutil validation."""
    loaded = _build_and_validate([])
    assert loaded["WFWorkflowActions"] == []


def test_notification_shortcut_validates():
    """A shortcut with a comment and notification validates."""
    actions = [
        make_comment("This shortcut shows a notification."),
        {
            "WFWorkflowActionIdentifier": "is.workflow.actions.notification",
            "WFWorkflowActionParameters": {
                "WFNotificationActionBody": "Hello from test!",
                "WFNotificationActionTitle": "Test",
            },
        },
    ]
    loaded = _build_and_validate(actions)
    assert len(loaded["WFWorkflowActions"]) == 2


def test_variable_wiring_shortcut_validates():
    """A shortcut with variable references validates."""
    clip_uuid = new_uuid()
    actions = [
        make_comment("Get clipboard and show in notification."),
        {
            "WFWorkflowActionIdentifier": "is.workflow.actions.getclipboard",
            "WFWorkflowActionParameters": {"UUID": clip_uuid},
        },
        {
            "WFWorkflowActionIdentifier": "is.workflow.actions.notification",
            "WFWorkflowActionParameters": {
                "WFNotificationActionBody": make_attachment(clip_uuid, "Clipboard"),
                "WFNotificationActionTitle": "Clipboard Contents",
            },
        },
    ]
    loaded = _build_and_validate(actions)
    assert len(loaded["WFWorkflowActions"]) == 3


def test_control_flow_shortcut_validates():
    """A shortcut with if/repeat validates."""
    notify = {
        "WFWorkflowActionIdentifier": "is.workflow.actions.notification",
        "WFWorkflowActionParameters": {
            "WFNotificationActionBody": "Inside block",
        },
    }
    if_actions = make_if_block("Has Any Value", None, [notify])
    repeat_actions = make_repeat_count(3, [notify])
    all_actions = [make_comment("Control flow test.")] + if_actions + repeat_actions
    _build_and_validate(all_actions)


def test_text_with_variable_shortcut_validates():
    """A shortcut with WFTextTokenString validates."""
    clip_uuid = new_uuid()
    actions = [
        {
            "WFWorkflowActionIdentifier": "is.workflow.actions.getclipboard",
            "WFWorkflowActionParameters": {"UUID": clip_uuid},
        },
        {
            "WFWorkflowActionIdentifier": "is.workflow.actions.notification",
            "WFWorkflowActionParameters": {
                "WFNotificationActionBody": make_text_with_variable(
                    "You copied: ", clip_uuid, "Clipboard"
                ),
            },
        },
    ]
    _build_and_validate(actions)
```

- [ ] **Step 2: Run integration tests**

Run: `python3 -m pytest shortcuts-authoring/tests/test_plist_output.py -v`
Expected: All 5 tests PASS (plutil -lint validates every output)

- [ ] **Step 3: Commit**

```bash
git add shortcuts-authoring/tests/test_plist_output.py
git commit -m "test: add integration tests validating shortcut plist output with plutil"
```

---

### Task 6: Action Example — clipboard_summarize.py

**Files:**
- Create: `shortcuts-authoring/resources/action_examples/clipboard_summarize.py`

First complete action example: Get Clipboard → Summarize (Apple Intelligence) → Show Notification. This is the concrete example from Spec Section 5.

> Ref: Apple Intelligence identifiers from Spec Section 5 Tier 5. Writing Tools intents extracted from WritingToolsAppIntentsExtension on macOS 26.

- [ ] **Step 1: Create clipboard_summarize.py**

Create `shortcuts-authoring/resources/action_examples/clipboard_summarize.py`:

```python
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
```

- [ ] **Step 2: Validate it produces a valid plist**

Run: `cd /Users/earchibald/work/github/earchibald/tinycuts && python3 shortcuts-authoring/resources/action_examples/clipboard_summarize.py`
Expected: "Validated:" message. Signing may succeed or fail depending on Apple ID.

- [ ] **Step 3: Commit**

```bash
git add shortcuts-authoring/resources/action_examples/clipboard_summarize.py
git commit -m "feat: add clipboard_summarize example (Apple Intelligence Writing Tools)"
```

---

### Task 7: Action Example — ai_pipeline.py

**Files:**
- Create: `shortcuts-authoring/resources/action_examples/ai_pipeline.py`

Use Model → Adjust Tone → Show Result. Demonstrates chaining Apple Intelligence actions and using `is.workflow.actions.askllm`.

- [ ] **Step 1: Create ai_pipeline.py**

Create `shortcuts-authoring/resources/action_examples/ai_pipeline.py`:

```python
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
```

- [ ] **Step 2: Validate**

Run: `python3 shortcuts-authoring/resources/action_examples/ai_pipeline.py`
Expected: "Validated:" message

- [ ] **Step 3: Commit**

```bash
git add shortcuts-authoring/resources/action_examples/ai_pipeline.py
git commit -m "feat: add ai_pipeline example (Use Model + Adjust Tone chain)"
```

---

### Task 8: Action Example — file_processor.py

**Files:**
- Create: `shortcuts-authoring/resources/action_examples/file_processor.py`

Demonstrates file I/O: receive file path → read file → process → save output.

- [ ] **Step 1: Create file_processor.py**

Create `shortcuts-authoring/resources/action_examples/file_processor.py`:

```python
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
```

- [ ] **Step 2: Validate**

Run: `python3 shortcuts-authoring/resources/action_examples/file_processor.py`
Expected: "Validated:" message

- [ ] **Step 3: Commit**

```bash
git add shortcuts-authoring/resources/action_examples/file_processor.py
git commit -m "feat: add file_processor example (file I/O + Proofread)"
```

---

### Task 9: Action Example — app_bridge.py

**Files:**
- Create: `shortcuts-authoring/resources/action_examples/app_bridge.py`

Demonstrates JXA scripting escape hatch and URL actions.

- [ ] **Step 1: Create app_bridge.py**

Create `shortcuts-authoring/resources/action_examples/app_bridge.py`:

```python
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
```

- [ ] **Step 2: Validate**

Run: `python3 shortcuts-authoring/resources/action_examples/app_bridge.py`
Expected: "Validated:" message

- [ ] **Step 3: Commit**

```bash
git add shortcuts-authoring/resources/action_examples/app_bridge.py
git commit -m "feat: add app_bridge example (JXA + URL actions)"
```

---

### Task 10: Plugin Template

**Files:**
- Create: `shortcuts-authoring/resources/plugin_template/SKILL.md.template`
- Create: `shortcuts-authoring/resources/plugin_template/install.sh.template`
- Create: `shortcuts-authoring/resources/plugin_template/uninstall.sh.template`

> Ref: Spec Section 8 — Plugin Packaging, I/O Contract Schema

- [ ] **Step 1: Create SKILL.md.template**

Create `shortcuts-authoring/resources/plugin_template/SKILL.md.template`:

```markdown
---
name: {{SHORTCUT_NAME}}
description: {{DESCRIPTION}}
version: 1.0.0
author: {{AUTHOR}}
tags:
  - macos
  - shortcuts
  - automation
---

# {{SHORTCUT_NAME}}

{{DESCRIPTION}}

## I/O Contract

```yaml
shortcut:
  name: "{{SHORTCUT_NAME}}"
  input: {{INPUT_TYPE}}
  output: {{OUTPUT_TYPE}}
  requires:
    macos: "26"
    apple-intelligence: {{REQUIRES_AI}}
  permissions:
{{PERMISSIONS}}
```

## Usage

### From CLI

```bash
{{CLI_EXAMPLE}}
```

### From an agent

This shortcut is designed to be invoked via `shortcuts run`. See the I/O contract above for input/output format.

## Installation

Run the install script to import the shortcut:

```bash
bash scripts/install.sh
```

You will be prompted to confirm the import in Shortcuts.app.

## How It Works

{{HOW_IT_WORKS}}

## Requirements

- macOS 26 or later
{{ADDITIONAL_REQUIREMENTS}}
```

- [ ] **Step 2: Create install.sh.template**

Create `shortcuts-authoring/resources/plugin_template/install.sh.template`:

```bash
#!/bin/bash
# Install script for {{SHORTCUT_NAME}}
# Opens the signed shortcut file, triggering the Shortcuts.app import dialog.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SHORTCUT_FILE="$SCRIPT_DIR/../shortcuts/{{SHORTCUT_FILENAME}}"

# Check Python availability (needed if rebuilding from source)
if ! command -v python3 &> /dev/null; then
    echo "Warning: python3 not found. Install via: xcode-select --install"
    echo "Python is only needed to rebuild shortcuts from source (src/build.py)."
fi

# Check shortcut file exists
if [ ! -f "$SHORTCUT_FILE" ]; then
    echo "Error: Shortcut file not found at $SHORTCUT_FILE"
    echo "You may need to rebuild it: cd $SCRIPT_DIR/../src && python3 build.py"
    exit 1
fi

echo "Importing {{SHORTCUT_NAME}}..."
echo "You will be prompted to confirm in Shortcuts.app."
open "$SHORTCUT_FILE"
```

- [ ] **Step 3: Create uninstall.sh.template**

Create `shortcuts-authoring/resources/plugin_template/uninstall.sh.template`:

```bash
#!/bin/bash
# Uninstall script for {{SHORTCUT_NAME}}
# Note: macOS does not provide a CLI to remove shortcuts.
# This script provides guidance for manual removal.

set -e

echo "To uninstall {{SHORTCUT_NAME}}:"
echo ""
echo "1. Open the Shortcuts app"
echo "2. Find '{{SHORTCUT_NAME}}' in your shortcuts list"
echo "3. Right-click (or Control-click) the shortcut"
echo "4. Select 'Delete'"
echo "5. Confirm deletion"
echo ""
echo "Note: There is no programmatic way to remove a shortcut on macOS."
echo "This is a known limitation of the Shortcuts platform."
```

- [ ] **Step 4: Verify templates**

Run:
```bash
# Check install.sh.template is valid bash syntax
bash -n shortcuts-authoring/resources/plugin_template/install.sh.template 2>&1 || echo "Note: template placeholders expected to cause syntax issues — manual review OK"

# Check all required placeholders exist in SKILL.md.template
for placeholder in SHORTCUT_NAME DESCRIPTION INPUT_TYPE OUTPUT_TYPE REQUIRES_AI PERMISSIONS CLI_EXAMPLE HOW_IT_WORKS; do
    grep -q "{{$placeholder}}" shortcuts-authoring/resources/plugin_template/SKILL.md.template && echo "OK: {{$placeholder}}" || echo "MISSING: {{$placeholder}}"
done
```
Expected: All placeholders show "OK"

- [ ] **Step 5: Commit**

```bash
git add shortcuts-authoring/resources/plugin_template/
git commit -m "feat: add plugin template (SKILL.md, install.sh, uninstall.sh templates)"
```

---

### Task 11: SKILL.md — Frontmatter, Overview, Quick Start, Format Reference

**Files:**
- Create: `shortcuts-authoring/SKILL.md`

First part of the main skill document: the sections an agent reads to understand the format and get started.

> Ref: Spec Sections 3, 10

- [ ] **Step 1: Write SKILL.md with frontmatter, overview, quick start, and format reference**

Create `shortcuts-authoring/SKILL.md` with these sections:

1. **Frontmatter** — skill metadata (name: `shortcuts-authoring`, description, tags: macos/shortcuts/automation/apple-intelligence)
2. **Overview** — 1 paragraph: what this skill does, when to use it, what it produces
3. **Quick Start** — numbered steps: copy `resources/builder_template.py`, fill in actions from the catalog, run script to build, sign with `shortcuts sign`, import with `open`, test with `shortcuts run`, package with `resources/plugin_template/`
4. **Format Reference** — condensed from Spec Section 3:
   - Top-level plist schema table (all keys from spec)
   - Action structure (`WFWorkflowActionIdentifier` + `WFWorkflowActionParameters`)
   - Variable system: `WFTextTokenAttachment` (single ref), `WFTextTokenString` (embedded in text with U+FFFC), magic variables. Include XML examples from spec.
   - Control flow: `GroupingIdentifier`, `WFControlFlowMode` (0/1/2), patterns for If/Repeat/Menu
   - Signing: `shortcuts sign -m anyone`, import via `open`
   - Include inline refs to external docs (Zachary7829, Cherri, Apple Support)

Do NOT include the action catalog yet — that's the next task.

- [ ] **Step 2: Verify the file is well-structured**

Run: `head -5 shortcuts-authoring/SKILL.md && grep '^#' shortcuts-authoring/SKILL.md`
Expected: Frontmatter present, section headings for Overview, Quick Start, Format Reference

- [ ] **Step 3: Commit**

```bash
git add shortcuts-authoring/SKILL.md
git commit -m "feat: add SKILL.md — frontmatter, overview, quick start, format reference"
```

---

### Task 12: SKILL.md — Action Catalog (Tiers 1-3)

**Files:**
- Modify: `shortcuts-authoring/SKILL.md`

Add the action catalog for Tiers 1-3: App Automation, File System, System Services.

> Ref: Spec Section 5 (Tiers 1-3). Action template format from Spec Section 5.
> Note: Tier 1 app-specific action identifiers are partially unverified (Spec Open Question #1). Document the known identifiers (Open App, Find/Filter patterns) and note that app-specific identifiers need extraction for Mail, Calendar, etc.

- [ ] **Step 1: Add Action Catalog section header and Tiers 1-3**

Append to `shortcuts-authoring/SKILL.md`:

Each action follows the template format:
- Identifier, Requires, Input, Output
- Parameters table
- Plist example dict
- Variable reference example
- Common multi-action pattern

**Tier 1 actions to cover:** `is.workflow.actions.openapp`, Find/Filter patterns, and a note about app-specific identifiers being implementation-time extracted.

**Tier 2 actions to cover:** `is.workflow.actions.documentpicker.open`, `is.workflow.actions.documentpicker.save`, `is.workflow.actions.file.getfoldercontents`, `is.workflow.actions.file.getlink`, `is.workflow.actions.file.rename`, `is.workflow.actions.file.move`, `is.workflow.actions.file.delete`

**Tier 3 actions to cover:** `is.workflow.actions.getclipboard`, `is.workflow.actions.setclipboard`, `is.workflow.actions.takescreenshot`, `is.workflow.actions.notification`

Include the concrete Show Notification example from the spec verbatim.

- [ ] **Step 2: Verify action count**

Run: `grep -c 'WFWorkflowActionIdentifier' shortcuts-authoring/SKILL.md`
Expected: At least 10 distinct action templates

- [ ] **Step 3: Commit**

```bash
git add shortcuts-authoring/SKILL.md
git commit -m "feat: add action catalog Tiers 1-3 (App Automation, File System, System Services)"
```

---

### Task 13: SKILL.md — Action Catalog (Tiers 4-6)

**Files:**
- Modify: `shortcuts-authoring/SKILL.md`

Add the action catalog for Tiers 4-6: Scripting, Apple Intelligence, Control Flow.

> Ref: Spec Section 5 (Tiers 4-6). Apple Intelligence identifiers verified from macOS 26 system.

- [ ] **Step 1: Add Tiers 4-6 to the Action Catalog**

**Tier 4 actions to cover:** `is.workflow.actions.runjavascript` (JXA), `is.workflow.actions.url`, `is.workflow.actions.openurl`

**Tier 5 actions to cover (with verified identifiers):**
- `is.workflow.actions.askllm` (Use Model) — with `WFLLMPrompt`, `WFLLMModel`, `WFGenerativeResultType`, `FollowUp` parameters
- `com.apple.WritingTools.WritingToolsAppIntentsExtension.SummarizeTextIntent`
- `com.apple.WritingTools.WritingToolsAppIntentsExtension.RewriteTextIntent`
- `com.apple.WritingTools.WritingToolsAppIntentsExtension.ProofreadIntent`
- `com.apple.WritingTools.WritingToolsAppIntentsExtension.AdjustToneIntent`
- `com.apple.WritingTools.WritingToolsAppIntentsExtension.FormatListIntent`
- `com.apple.WritingTools.WritingToolsAppIntentsExtension.FormatTableIntent`
- Note Image Playground as TBD (Spec Open Question #3)

**Tier 6 actions to cover:** `is.workflow.actions.conditional` (If), `is.workflow.actions.repeat.count`, `is.workflow.actions.repeat.each`, `is.workflow.actions.choosefrommenu`, `is.workflow.actions.setvariable`, `is.workflow.actions.getvariable`, `is.workflow.actions.dictionary`, `is.workflow.actions.getvalueforkey`, `is.workflow.actions.list`, `is.workflow.actions.getitemfromlist`, `is.workflow.actions.comment`, `is.workflow.actions.output`

Note: `is.workflow.actions.output` is used in examples for stdout output. Document with a note that the exact parameter format needs runtime verification.

- [ ] **Step 2: Verify all Apple Intelligence identifiers present**

Run: `grep -c 'WritingToolsAppIntentsExtension' shortcuts-authoring/SKILL.md`
Expected: At least 6 (one per Writing Tools action)

- [ ] **Step 3: Commit**

```bash
git add shortcuts-authoring/SKILL.md
git commit -m "feat: add action catalog Tiers 4-6 (Scripting, Apple Intelligence, Control Flow)"
```

---

### Task 14: SKILL.md — Build Workflow, Debugging, Packaging, References

**Files:**
- Modify: `shortcuts-authoring/SKILL.md`

Final sections of SKILL.md.

> Ref: Spec Sections 7, 8, 10, 12, 13

- [ ] **Step 1: Add remaining sections**

Append to `shortcuts-authoring/SKILL.md`:

1. **Build & Sign Workflow** — the 12-step workflow from Spec Section 10, with exact commands
2. **Debugging & Troubleshooting** — from Spec Section 7: validation steps, failure modes table, limitations
3. **Plugin Packaging** — from Spec Section 8: published plugin directory structure, I/O contract schema (full YAML with allowed `input`/`output`/`permissions` values tables), install hook, reference to `resources/plugin_template/`
4. **Commenting Requirements** — from Spec Section 13: header comment, section comments, control flow comments, variable comments, integration comments
5. **External References** — from Spec Section 12, organized: Apple Official, Community Format, Tools & Projects, Apple Intelligence coverage

- [ ] **Step 2: Verify all resource paths referenced**

Run:
```bash
grep -oP 'resources/[^ )\n`]+' shortcuts-authoring/SKILL.md | sort -u | while read f; do
    [ -e "shortcuts-authoring/$f" ] && echo "OK: $f" || echo "MISSING: $f"
done
```
Expected: All paths show "OK"

- [ ] **Step 3: Commit**

```bash
git add shortcuts-authoring/SKILL.md
git commit -m "feat: add build workflow, debugging, packaging, and references to SKILL.md"
```

---

### Task 15: End-to-End Validation

**Files:**
- No new files. Validates everything built so far.

- [ ] **Step 1: Run all unit tests**

Run: `python3 -m pytest shortcuts-authoring/tests/ -v`
Expected: All tests PASS

- [ ] **Step 2: Run all action examples (plist validation)**

Run:
```bash
for f in shortcuts-authoring/resources/action_examples/*.py; do
    echo "=== $f ==="
    python3 "$f"
    echo
done
```
Expected: Each prints "Validated:" (signing may be skipped)

- [ ] **Step 3: Verify skill file structure matches spec**

Run:
```bash
find shortcuts-authoring -type f | sort
```

Expected output should match the file structure from Spec Section 9 (plus uninstall template and tests):
```
shortcuts-authoring/SKILL.md
shortcuts-authoring/resources/action_examples/ai_pipeline.py
shortcuts-authoring/resources/action_examples/app_bridge.py
shortcuts-authoring/resources/action_examples/clipboard_summarize.py
shortcuts-authoring/resources/action_examples/file_processor.py
shortcuts-authoring/resources/builder_template.py
shortcuts-authoring/resources/plugin_template/SKILL.md.template
shortcuts-authoring/resources/plugin_template/install.sh.template
shortcuts-authoring/resources/plugin_template/uninstall.sh.template
shortcuts-authoring/tests/test_builder_template.py
shortcuts-authoring/tests/test_plist_output.py
```

- [ ] **Step 4: Verify SKILL.md covers all spec sections**

Run:
```bash
echo "Checking SKILL.md section coverage..."
for section in "Format Reference" "Action Catalog" "App Automation" "File System" "System Services" "Scripting" "Apple Intelligence" "Control Flow" "Build" "Debugging" "Plugin Packaging" "I/O Contract" "Commenting" "External References"; do
    grep -qi "$section" shortcuts-authoring/SKILL.md && echo "OK: $section" || echo "MISSING: $section"
done
```
Expected: All sections show "OK"

- [ ] **Step 5: Commit final state**

```bash
git add -A
git commit -m "chore: end-to-end validation complete — all tests pass, all examples validate"
```
