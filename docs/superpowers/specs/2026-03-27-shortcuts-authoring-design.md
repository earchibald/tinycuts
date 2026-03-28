# Shortcuts Authoring Skill — Design Specification

**Date:** 2026-03-27
**Status:** Draft
**Skill name:** `shortcuts-authoring`

## 1. Vision

Shortcuts is the universal bridge into macOS's walled garden for agents. No MCP server needed — just `shortcuts run` with well-crafted shortcuts that reach into apps, system services, Apple Intelligence, accessibility, AppleScript, and everything else macOS exposes through its Shortcuts action catalog.

This skill enables a **marketplace of macOS automation capabilities delivered as Shortcuts**. Agents use this skill to author production-quality `.shortcut` files, sign them, and package them as Claude Code plugins for distribution.

## 2. Product Scope

### Two Skills

| Skill | Purpose | Target User | This Arc |
|-------|---------|-------------|----------|
| `shortcuts-authoring` | Author, sign, and package macOS Shortcuts as Claude Code plugins | Skill/plugin developers | **Yes** |
| `shortcuts-usage` | Discover, invoke, and orchestrate installed shortcuts via `shortcuts run` | End-user agents | Future |

`shortcuts-usage` must support both running published shortcuts from plugins AND running shortcuts under development during the authoring workflow (the dev-loop: write → sign → import → run → validate → iterate).

### What `shortcuts-authoring` Is NOT

- Not a runtime — it creates shortcuts, it does not run them
- Not a Cherri/ScPL wrapper — it works directly with the binary plist format
- Not limited to a fixed action set — it teaches the *pattern* for any action, with deep templates for priority categories

## 3. Technical Foundation

### File Format

`.shortcut` files are binary property lists (bplist). The format is not officially documented by Apple; all knowledge comes from community reverse-engineering.

**Top-level plist schema:**

| Key | Type | Description |
|-----|------|-------------|
| `WFWorkflowActions` | Array | The action sequence (core of the shortcut) |
| `WFWorkflowClientVersion` | Integer | Client version number |
| `WFWorkflowClientRelease` | String | Semantic version string |
| `WFWorkflowMinimumClientVersion` | Integer | Minimum version required to run |
| `WFWorkflowMinimumClientVersionString` | String | Minimum version as string (e.g., "1700" for macOS 26) |
| `WFWorkflowIcon` | Dict | `WFWorkflowIconStartColor` (int) + `WFWorkflowIconGlyphNumber` (int) |
| `WFWorkflowInputContentItemClasses` | Array | Accepted input types (e.g., `WFStringContentItem`, `WFURLContentItem`) |
| `WFWorkflowTypes` | Array | Where it appears: `MenuBar`, `QuickActions`, `ActionExtension`, etc. |
| `WFWorkflowImportQuestions` | Array | Prompts shown during import |

> **Ref:** [Zachary7829's Shortcuts File Format Documentation](https://zachary7829.github.io/blog/shortcuts/fileformat), [Cherri File Format page](https://cherrilang.org/compiler/file-format.html)

### Action Structure

Each entry in `WFWorkflowActions` is a dictionary with two keys:

- **`WFWorkflowActionIdentifier`** — Reverse-domain-notation string, e.g., `is.workflow.actions.setvariable`
- **`WFWorkflowActionParameters`** — Dictionary of action-specific configuration

The `is.workflow.actions` prefix denotes built-in Shortcuts actions. Third-party app actions use their own bundle identifiers.

> **Ref:** [iOS-Shortcuts-Reference (GitHub)](https://github.com/sebj/iOS-Shortcuts-Reference)

### Variable System

There are two serialization types for variable references:

#### `WFTextTokenAttachment` — Single variable reference (no surrounding text)

Used when a parameter is purely a variable reference:

```xml
<key>WFInput</key>
<dict>
    <key>Value</key>
    <dict>
        <key>OutputName</key>
        <string>Summarize Text</string>
        <key>OutputUUID</key>
        <string>09B5964F-CBB7-429E-B6D3-3BE92C08E3FF</string>
        <key>Type</key>
        <string>ActionOutput</string>
    </dict>
    <key>WFSerializationType</key>
    <string>WFTextTokenAttachment</string>
</dict>
```

The `Type` field can be: `ActionOutput` (references another action's UUID), `Variable` (named variable with `VariableName` key), `ExtensionInput`, `Ask`, or `CurrentDate`.

#### `WFTextTokenString` — Variable embedded in text

Used when a variable is interpolated within a string. The string contains U+FFFC (Object Replacement Character) as a placeholder, and `attachmentsByRange` maps each placeholder's `{position, length}` to a variable reference:

```xml
<key>WFLLMPrompt</key>
<dict>
    <key>Value</key>
    <dict>
        <key>attachmentsByRange</key>
        <dict>
            <key>{52, 1}</key>
            <dict>
                <key>OutputName</key>
                <string>Weather Conditions</string>
                <key>OutputUUID</key>
                <string>70BFB126-1E9B-409B-BB29-10258A03E6AE</string>
                <key>Type</key>
                <string>ActionOutput</string>
            </dict>
        </dict>
        <key>string</key>
        <string>Write me a concise, fun summary of today's weather: &#xFFFC;</string>
    </dict>
    <key>WFSerializationType</key>
    <string>WFTextTokenString</string>
</dict>
```

Multiple variables use multiple `{position, 1}` entries in `attachmentsByRange`, each with its own U+FFFC in the string.

#### Magic Variables (Repeat Item, etc.)

Built-in variables like `Repeat Item` use `Type: Variable` with a `VariableName` key instead of `OutputUUID`:

```xml
<key>{0, 1}</key>
<dict>
    <key>Type</key>
    <string>Variable</string>
    <key>VariableName</key>
    <string>Repeat Item</string>
</dict>
```

#### UUID Linking

Each action that produces output has a `UUID` key in its parameters. Downstream actions reference it via `OutputUUID`. The `OutputName` is a display label (e.g., `"Weather Conditions"`, `"Response"`).

> **Ref:** [0xdevalias decompilation notes](https://gist.github.com/0xdevalias/27d9aea9529be7b6ce59055332a94477), [TheAppleWiki: WorkflowKit.framework](https://theapplewiki.com/wiki/Dev:WorkflowKit.framework). Variable structures extracted from Apple's gallery shortcuts at `/System/Library/PrivateFrameworks/WorkflowKit.framework/Resources/Gallery.bundle/` (MorningReport.wflow, ActionItems.wflow, DocumentReview.wflow).

### Control Flow

Control flow actions (If, Repeat, Menu) use a shared `GroupingIdentifier` UUID and `WFControlFlowMode` integer:

| Mode | Meaning |
|------|---------|
| `0` | Start of block (If / Repeat / Choose from Menu) |
| `1` | Middle of block (Otherwise / menu case) |
| `2` | End of block (End If / End Repeat / End Menu) |

All actions in a control flow block share the same `GroupingIdentifier`. The end action (`WFControlFlowMode: 2`) also has a `UUID` key for output referencing.

**Example: Choose from Menu** (from Apple's DocumentReview.wflow):

```xml
<!-- Start: Choose from Menu (mode 0) -->
<dict>
    <key>WFWorkflowActionIdentifier</key>
    <string>is.workflow.actions.choosefrommenu</string>
    <key>WFWorkflowActionParameters</key>
    <dict>
        <key>GroupingIdentifier</key>
        <string>4D9D4BA4-F00A-4BD7-8AD5-4E558704E03A</string>
        <key>WFControlFlowMode</key>
        <integer>0</integer>
        <key>WFMenuItems</key>
        <array>
            <string>File</string>
            <string>URL</string>
        </array>
        <key>WFMenuPrompt</key>
        <string>Select a file, or input a URL to a document</string>
    </dict>
</dict>
<!-- Case: "File" (mode 1) -->
<dict>
    <key>WFWorkflowActionIdentifier</key>
    <string>is.workflow.actions.choosefrommenu</string>
    <key>WFWorkflowActionParameters</key>
    <dict>
        <key>GroupingIdentifier</key>
        <string>4D9D4BA4-F00A-4BD7-8AD5-4E558704E03A</string>
        <key>WFControlFlowMode</key>
        <integer>1</integer>
        <key>WFMenuItemTitle</key>
        <string>File</string>
    </dict>
</dict>
<!-- ... actions inside File case ... -->
<!-- End Menu (mode 2) -->
<dict>
    <key>WFWorkflowActionIdentifier</key>
    <string>is.workflow.actions.choosefrommenu</string>
    <key>WFWorkflowActionParameters</key>
    <dict>
        <key>GroupingIdentifier</key>
        <string>4D9D4BA4-F00A-4BD7-8AD5-4E558704E03A</string>
        <key>UUID</key>
        <string>9A00A0CE-75D2-4341-B478-506A244340D2</string>
        <key>WFControlFlowMode</key>
        <integer>2</integer>
    </dict>
</dict>
```

**Repeat with Count** uses `is.workflow.actions.repeat.count`; **Repeat with Each** uses `is.workflow.actions.repeat.each` (input via `WFInput` variable reference). **If/Otherwise** uses `is.workflow.actions.conditional` with `WFCondition` (e.g., `"Has Any Value"`, `"Equals"`) and `WFConditionalActionString` for the comparison value.

### Signing

Starting with macOS 12, exported `.shortcut` files must be cryptographically signed before import. The `shortcuts` CLI provides signing:

```bash
shortcuts sign -m anyone -i unsigned.shortcut -o signed.shortcut
```

Modes: `anyone` (notarized via iCloud, public sharing) or `people-who-know-me` (local signing, contacts-only).

> **Ref:** [Run shortcuts from the command line — Apple Support](https://support.apple.com/guide/shortcuts-mac/run-shortcuts-from-the-command-line-apd455c82f02/mac)

### Import

There is no `import` CLI subcommand. Import is done via:

```bash
open signed.shortcut
```

This opens Shortcuts.app and triggers the import dialog. The user must confirm.

## 4. Approach: Direct Plist Assembly

The skill teaches agents to emit the `WFWorkflow*` plist structure directly as Python dictionaries, then serialize with `plistlib`. No intermediate language, no external dependencies.

### Why This Approach

- **Zero dependencies beyond Python** — ships with macOS
- **Full access to every action** — nothing is abstracted away
- **No abstraction tax** — when Apple adds new actions, document the identifier and parameters, done
- **Debuggable** — `plutil -convert xml1` on any output for inspection
- **The skill IS the value** — the hard part is knowing the action catalog, parameter shapes, and variable wiring patterns

> **Ref:** Python `plistlib` — [stdlib docs](https://docs.python.org/3/library/plistlib.html)

### Alternatives Considered

| Approach | Why Not |
|----------|---------|
| Cherri compiler | External Go dependency; limited to what Cherri supports; Apple Intelligence actions may lag |
| JSON schema + builder | Adds an abstraction layer that can fall behind Apple's format; two things to debug |

## 5. Action Catalog

### Priority Categories

Organized by priority for agentic macOS automation:

#### Tier 1: App Automation (Primary — the walled garden bridge)
- Open App
- App-specific actions: Mail, Calendar, Reminders, Notes, Finder, Safari, Maps
- Find/Filter actions for app data

#### Tier 2: File System (Essential I/O)
- Get File, Save File
- Get Folder Contents
- File metadata, Rename, Move, Delete

#### Tier 3: System Services (Agent observability)
- Get Clipboard, Set Clipboard
- Take Screenshot
- Show Notification

#### Tier 4: Scripting (Escape hatch)
- Run JavaScript for Automation (JXA)
- Open URL, URL construction

#### Tier 5: Apple Intelligence (Unique differentiator)

Available on macOS 26+ with Apple Intelligence enabled.

**Use Model (general LLM action):**

| Action | Identifier | Parameters |
|--------|-----------|------------|
| Use Model | `is.workflow.actions.askllm` | `WFLLMPrompt` (text/variable), `WFLLMModel` (defaults to `"Apple Intelligence"`), `WFGenerativeResultType` (`"Text"`, `"List"`, `"Dictionary"`, `"Automatic"`), `FollowUp` (bool) |

Also available as direct model aliases:
- `com.apple.Shortcuts.AskAFMAction3B` — on-device 3B parameter model
- `com.apple.Shortcuts.AskMontaraAction` — server-side model (Private Cloud Compute)

**Writing Tools (via WritingToolsAppIntentsExtension):**

| Action | Identifier | Parameters |
|--------|-----------|------------|
| Summarize Text | `com.apple.WritingTools.WritingToolsAppIntentsExtension.SummarizeTextIntent` | `text`, `summaryType` (`"summarize"`, `"createKeyPoints"`) |
| Rewrite Text | `com.apple.WritingTools.WritingToolsAppIntentsExtension.RewriteTextIntent` | `text` |
| Proofread Text | `com.apple.WritingTools.WritingToolsAppIntentsExtension.ProofreadIntent` | `text` |
| Adjust Tone of Text | `com.apple.WritingTools.WritingToolsAppIntentsExtension.AdjustToneIntent` | `text`, `tone` (`"friendly"`, `"professional"`, `"concise"`) |
| Make List from Text | `com.apple.WritingTools.WritingToolsAppIntentsExtension.FormatListIntent` | `text` |
| Make Table from Text | `com.apple.WritingTools.WritingToolsAppIntentsExtension.FormatTableIntent` | `text` |

**Image Playground:**

| Action | Identifier | Parameters |
|--------|-----------|------------|
| Create Image | TBD — needs extraction from macOS 26 with Image Playground | Prompt text, style options |

> **Ref:** [Use Apple Intelligence in Shortcuts — Apple Support](https://support.apple.com/guide/mac-help/use-apple-intelligence-in-shortcuts-mchl91750563/mac), [What's new in Shortcuts for macOS 26](https://support.apple.com/en-us/125148), [9to5Mac: 25+ new actions in iOS 26](https://9to5mac.com/2025/12/09/ios-26s-shortcuts-app-adds-25-new-actions-heres-everything-new/), [MacObserver: All 25+ new actions](https://www.macobserver.com/news/all-25-new-shortcuts-actions-introduced-in-ios-26-heres-everything-you-can-do/). Identifiers extracted from Apple gallery shortcuts in `WorkflowKit.framework/Resources/Gallery.bundle/` and WritingTools intents plist on macOS 26.

#### Tier 6: Control Flow (Structural glue)
- If / Otherwise / End If
- Repeat / Repeat with Each
- Choose from Menu
- Set Variable / Get Variable
- Dictionary / Get Dictionary Value
- List / Get Item from List

> **Ref:** [Shortcuts User Guide — How shortcuts work](https://support.apple.com/guide/shortcuts-mac/welcome/mac)

### Action Template Format

Every action in the catalog follows this structure:

```
### Action: <Name>
- **Identifier:** `is.workflow.actions.<name>`
- **Requires:** <macOS version, Apple Intelligence, specific app, etc.>
- **Input:** <type>
- **Output:** <type>

**Parameters:**
| Key | Type | Required | Values | Description |
|-----|------|----------|--------|-------------|

**Plist Example:**
(isolated action dict)

**With Variable Reference:**
(shows UUID + WFTextTokenAttachment wiring)

**Common Pattern: <descriptive name>**
(complete multi-action snippet that does something useful)
```

Key template principles:
- Every action has a **runnable multi-action pattern**, not just the isolated action
- **Variable wiring shown explicitly** every time (the hardest part to get right)
- **System requirements called out** so the agent sets correct minimum version metadata

### Concrete Example: Show Notification

```
### Action: Show Notification
- **Identifier:** `is.workflow.actions.notification`
- **Requires:** macOS 26+
- **Input:** None (uses parameters)
- **Output:** None

**Parameters:**
| Key | Type | Required | Values | Description |
|-----|------|----------|--------|-------------|
| `WFNotificationActionBody` | String/WFTextTokenString | Yes | — | Notification body text |
| `WFNotificationActionTitle` | String | No | — | Notification title |
| `WFNotificationActionSound` | Bool | No | true/false | Play sound (default true) |

**Plist Example:**
{
    "WFWorkflowActionIdentifier": "is.workflow.actions.notification",
    "WFWorkflowActionParameters": {
        "WFNotificationActionBody": "Hello from Shortcuts!",
        "WFNotificationActionTitle": "Agent Alert"
    }
}

**With Variable Reference:**
# notification_uuid = new_uuid()
{
    "WFWorkflowActionIdentifier": "is.workflow.actions.notification",
    "WFWorkflowActionParameters": {
        "WFNotificationActionBody": make_text_with_variable(
            "Summary: ", summary_uuid, "Summarize Text"
        ),
        "WFNotificationActionTitle": "AI Summary Complete"
    }
}

**Common Pattern: Get Clipboard → Summarize → Notify**
clipboard_uuid = new_uuid()
summary_uuid = new_uuid()

actions = [
    # Step 1: Get Clipboard
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.getclipboard",
        "WFWorkflowActionParameters": {
            "UUID": clipboard_uuid,
        },
    },
    # Step 2: Summarize (Apple Intelligence)
    {
        "WFWorkflowActionIdentifier":
            "com.apple.WritingTools.WritingToolsAppIntentsExtension.SummarizeTextIntent",
        "WFWorkflowActionParameters": {
            "text": make_attachment(clipboard_uuid, "Clipboard"),
            "summaryType": "summarize",
            "UUID": summary_uuid,
        },
    },
    # Step 3: Show Notification with result
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.notification",
        "WFWorkflowActionParameters": {
            "WFNotificationActionBody": make_attachment(summary_uuid, "Summarize Text"),
            "WFNotificationActionTitle": "Clipboard Summary",
        },
    },
]
```

## 6. Build & Sign Pipeline

### Builder Template (`resources/builder_template.py`)

A reusable Python script template the agent copies and fills in:

```python
import plistlib
import uuid
import subprocess
import sys

# --- Scaffold ---

def make_shortcut(name, actions,
                  icon_color=0x4B0082, icon_glyph=0xE032,
                  input_types=None, workflow_types=None):
    """Build a complete shortcut plist structure.

    Args:
        name: Shortcut display name (used for file naming, not embedded in plist)
        actions: List of action dicts
        icon_color: Integer color value for the shortcut icon
        icon_glyph: Integer glyph number for the shortcut icon
        input_types: List of accepted input content item classes.
            Defaults to ["WFStringContentItem", "WFURLContentItem"].
            Common values: WFStringContentItem, WFURLContentItem,
            WFImageContentItem, WFPDFContentItem, WFFileContentItem
        workflow_types: List of workflow type strings.
            Common values: "MenuBar", "QuickActions", "ActionExtension", "NCWidget"
            Defaults to ["MenuBar", "QuickActions"] for general-purpose shortcuts.
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

# --- Variable Helpers ---

def new_uuid():
    """Generate an uppercase UUID for action output linking."""
    return str(uuid.uuid4()).upper()

def make_attachment(output_uuid, output_name):
    """Create a WFTextTokenAttachment referencing a previous action's output.

    Use when a parameter is purely a variable reference (no surrounding text).
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
    """Create a WFTextTokenAttachment for a magic variable (e.g., 'Repeat Item')."""
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
    """
    # Note: position uses NSString character indices (UTF-16 code units).
    # len() works for ASCII/BMP text. For strings with emoji or non-BMP chars,
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

# --- Control Flow Helpers ---

def make_if_block(condition, condition_value, then_actions, else_actions=None):
    """Create If/Otherwise/End If with shared GroupingIdentifier.

    Args:
        condition: e.g., "Equals", "Has Any Value", "Is Greater Than"
        condition_value: comparison value (string or number), or None for "Has Any Value"
        then_actions: list of action dicts for the If branch
        else_actions: optional list of action dicts for the Otherwise branch

    Returns: flat list of action dicts (If + then + Otherwise + else + End If)
    """
    gid = new_uuid()
    end_uuid = new_uuid()

    actions = []

    # If (mode 0)
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

    # Then branch actions
    actions.extend(then_actions)

    # Otherwise (mode 1) — only if else_actions provided
    if else_actions:
        actions.append({
            "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
            "WFWorkflowActionParameters": {
                "GroupingIdentifier": gid,
                "WFControlFlowMode": 1,
            },
        })
        actions.extend(else_actions)

    # End If (mode 2)
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
    """Create Repeat N Times / End Repeat with shared GroupingIdentifier.

    Returns: flat list of action dicts
    """
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

# --- Comment Helper ---

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

# === ACTIONS GO HERE ===
actions = [
    # Agent fills this in from the action catalog
]

# --- Build ---
shortcut = make_shortcut("My Shortcut", actions)

with open("unsigned.shortcut", "wb") as f:
    plistlib.dump(shortcut, f, fmt=plistlib.FMT_BINARY)

# --- Validate ---
# Check the plist is well-formed before signing
result = subprocess.run(["plutil", "-lint", "unsigned.shortcut"], capture_output=True, text=True)
if result.returncode != 0:
    print(f"Plist validation failed: {result.stderr}", file=sys.stderr)
    sys.exit(1)
print("Plist validation passed")

# --- Sign ---
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
```

The template provides the scaffold and helpers. The agent's job is filling in the `actions` list using patterns from the action catalog.

## 7. Debugging & Troubleshooting

### Validation Steps (integrated into dev workflow)

1. **Validate plist structure:** `plutil -lint unsigned.shortcut` — catches malformed plists before signing
2. **Inspect plist contents:** `plutil -convert xml1 -o debug.xml unsigned.shortcut` — human-readable XML for debugging
3. **Check signing:** If `shortcuts sign` fails, stderr typically reports the cause. Common failures:
   - Malformed plist (missing required keys, wrong types) → fix plist structure
   - No Apple ID signed in → sign in via System Settings
   - No network → `shortcuts sign -m anyone` requires iCloud connectivity for notarization
4. **Test import:** `open signed.shortcut` → if the import dialog doesn't appear, the file may not be properly signed
5. **Test execution:** `echo "test" | shortcuts run "Name" --input-path - --output-path - 2>&1` — check both stdout and stderr

### Common Failure Modes

| Symptom | Cause | Fix |
|---------|-------|-----|
| `shortcuts sign` exits non-zero | Malformed plist | Run `plutil -lint` and fix structure |
| Import dialog shows but shortcut is empty | `WFWorkflowActions` is empty or malformed | Inspect XML, check action dicts have both `WFWorkflowActionIdentifier` and `WFWorkflowActionParameters` |
| Shortcut runs but produces no output | Missing `UUID` on output-producing actions | Add `UUID` key to actions whose output you reference |
| Variable shows as blank | `OutputUUID` doesn't match producing action's `UUID` | Verify UUID strings match exactly (case-sensitive) |
| Control flow (If/Repeat) doesn't group correctly | Mismatched `GroupingIdentifier` | All actions in a block must share the same `GroupingIdentifier` UUID |
| Apple Intelligence action fails | Apple Intelligence not enabled, or wrong identifier | Verify Apple Intelligence is enabled in System Settings; check identifier string |

### Limitations

- **No automated import:** `open signed.shortcut` always shows a confirmation dialog. Fully automated testing of the import-and-run cycle is not possible without user interaction. Automated testing can validate: plist structure (`plutil -lint`), signing success, and post-import execution (if the shortcut is already imported).
- **No programmatic uninstall:** There is no CLI to remove an installed shortcut. Best-effort via AppleScript or user guidance.
- **Signing requires network:** `shortcuts sign -m anyone` contacts Apple's servers. Offline signing is only possible with `-m people-who-know-me` (but limits who can import).

## 8. Plugin Packaging

### Published Plugin Structure

```
my-shortcut-plugin/
├── SKILL.md                    # What the shortcut does, I/O contract, usage
├── shortcuts/
│   └── my-shortcut.shortcut    # Signed .shortcut file
├── scripts/
│   ├── install.sh              # Imports shortcut via `open`
│   └── uninstall.sh            # Best-effort removal guidance
└── src/
    └── build.py                # Builder script (kept for transparency)
```

### Design Decisions

- **`src/build.py` ships with the plugin** — consumers and future agents can inspect how the shortcut was built, rebuild it, or fork it
- **Install hook uses `open`** — triggers the Shortcuts import dialog; user must confirm (no silent install)
- **Uninstall is best-effort** — no CLI to remove a shortcut; script guides the user or attempts AppleScript

### I/O Contract Schema (in SKILL.md)

Standardized format that bridges `shortcuts-authoring` → `shortcuts-usage`. All plugin SKILL.md files must include this block:

```yaml
shortcut:
  name: "My Shortcut"               # Required. Exact name as installed in Shortcuts.app
  input: stdin/text                  # Required. See allowed values below
  output: stdout/text                # Required. See allowed values below
  requires:                          # Required. Minimum system requirements
    macos: "26"                      # Required. Minimum macOS version
    apple-intelligence: true         # Optional. Default false
  permissions:                       # Optional. List of system capabilities used
    - clipboard-read
    - notifications
```

**Allowed `input` values:**

| Value | Meaning | CLI invocation |
|-------|---------|----------------|
| `stdin/text` | Accepts text via stdin | `echo "..." \| shortcuts run "Name" --input-path -` |
| `stdin/file` | Accepts file data via stdin | `cat file.pdf \| shortcuts run "Name" --input-path -` |
| `file-path` | Accepts a file path as text input | `echo "/path/to/file" \| shortcuts run "Name" --input-path -` |
| `clipboard` | Reads from system clipboard (no CLI input needed) | `shortcuts run "Name"` |
| `none` | No input required | `shortcuts run "Name"` |

**Allowed `output` values:**

| Value | Meaning | CLI invocation |
|-------|---------|----------------|
| `stdout/text` | Outputs text to stdout | `shortcuts run "Name" --output-path -` |
| `stdout/file` | Outputs file data to stdout | `shortcuts run "Name" --output-path - --output-type public.png` |
| `file-path` | Writes to a file, outputs path to stdout | `shortcuts run "Name" --output-path -` |
| `clipboard` | Sets system clipboard (no CLI output) | `shortcuts run "Name"` |
| `notification` | Shows a notification (no CLI output) | `shortcuts run "Name"` |
| `none` | No output (side-effect only) | `shortcuts run "Name"` |

**Allowed `permissions` values:** `clipboard-read`, `clipboard-write`, `notifications`, `screenshots`, `file-read`, `file-write`, `calendar-read`, `calendar-write`, `reminders-read`, `reminders-write`, `mail-send`, `location`, `network`

This contract is what `shortcuts-usage` reads to know how to invoke the shortcut.

### Plugin Template

The skill ships a `resources/plugin_template/` skeleton:
- `SKILL.md.template` — with placeholders for name, description, I/O contract
- `install.sh.template` — parameterized install hook
- Directory structure ready to fill

## 9. Skill File Layout

```
shortcuts-authoring/
├── SKILL.md                          # Main skill document
│                                     # - Format reference
│                                     # - Action catalog (all tiers)
│                                     # - Build & sign workflow
│                                     # - Plugin packaging guide
├── resources/
│   ├── builder_template.py           # Python script template
│   ├── plugin_template/              # Skeleton plugin structure
│   │   ├── SKILL.md.template         # Published plugin SKILL.md template
│   │   └── install.sh.template       # Install hook template
│   └── action_examples/              # Complete working examples
│       ├── clipboard_summarize.py    # Get Clipboard → Summarize → Notification
│       ├── file_processor.py         # File input → Transform → Save
│       ├── app_bridge.py             # JXA → App automation → Output
│       └── ai_pipeline.py            # Use Model → Writing Tools chain
```

### File Roles

- **`SKILL.md`** — The main skill. Contains everything an agent needs: format reference, action catalog, workflow guidance, packaging instructions. Heavily annotated with external references.
- **`resources/builder_template.py`** — Reusable scaffold with helpers for UUID generation, variable wiring, control flow grouping, and the serialize → sign → verify pipeline. Marked with `# ACTIONS GO HERE` insertion point.
- **`resources/action_examples/`** — Complete, runnable Python scripts. Each produces a signed, importable shortcut. Serve as documentation AND integration tests.
- **`resources/plugin_template/`** — Skeleton the agent copies when packaging a finished shortcut for distribution.

## 10. Development Workflow

The authoring workflow the skill teaches:

```
1.  Define the shortcut's purpose and I/O contract
2.  Copy builder_template.py
3.  Assemble actions from the catalog into the actions list
4.  Run the script to produce unsigned.shortcut
5.  Validate with `plutil -lint unsigned.shortcut`
6.  Debug with `plutil -convert xml1 -o debug.xml unsigned.shortcut` (if needed)
7.  Sign with `shortcuts sign -m anyone -i unsigned.shortcut -o signed.shortcut`
8.  Import with `open signed.shortcut` (user confirms import dialog)
9.  Test with `shortcuts run <name> --input-path - --output-path -`
    (this is where shortcuts-usage skill comes in during dev)
10. Iterate on steps 3-9 until correct
11. Copy plugin_template/, fill in SKILL.md with I/O contract, move signed shortcut
12. Publish
```

## 11. Baseline Requirements

- **macOS 26 / iOS 26** — baseline OS version
- **Python 3** — only stdlib (`plistlib`, `uuid`, `subprocess`). **Note:** Apple removed system Python in macOS 12.3. Python 3 is available if Xcode Command Line Tools are installed (`xcode-select --install`) or via Homebrew. The `install.sh` template (not the Python script itself) should check for Python availability and print a helpful error if missing.
- **`shortcuts` CLI** — ships with macOS
- **Apple Intelligence** — required for Tier 5 actions; skill documents this requirement clearly
- **Apple ID** — required for `shortcuts sign -m anyone` (iCloud notarization)

## 12. External References

### Apple Official Documentation
- [Shortcuts User Guide for Mac](https://support.apple.com/guide/shortcuts-mac/welcome/mac)
- [Use Apple Intelligence in Shortcuts](https://support.apple.com/guide/mac-help/use-apple-intelligence-in-shortcuts-mchl91750563/mac)
- [What's new in Shortcuts for macOS 26](https://support.apple.com/en-us/125148)
- [Run shortcuts from the command line](https://support.apple.com/guide/shortcuts-mac/run-shortcuts-from-the-command-line-apd455c82f02/mac)
- [Writing Tools with Apple Intelligence](https://support.apple.com/guide/mac-help/use-writing-tools-mchldcd6c260/15.0/mac/15.0)

### Community Format Documentation
- [Zachary7829's Shortcuts File Format Docs](https://zachary7829.github.io/blog/shortcuts/fileformat) — most comprehensive reverse-engineered format reference
- [Cherri File Format page](https://cherrilang.org/compiler/file-format.html) — plist structure walkthrough
- [iOS-Shortcuts-Reference (GitHub)](https://github.com/sebj/iOS-Shortcuts-Reference) — community action schema docs
- [0xdevalias decompilation notes](https://gist.github.com/0xdevalias/27d9aea9529be7b6ce59055332a94477) — WorkflowKit internals
- [TheAppleWiki: WorkflowKit.framework](https://theapplewiki.com/wiki/Dev:WorkflowKit.framework)

### Tools & Projects (Reference Only)
- [Cherri](https://github.com/electrikmilk/cherri) — Go-based shortcuts compiler (reference for action identifiers and parameter shapes)
- [shortcuts-js](https://github.com/joshfarrant/shortcuts-js) — Node.js shortcuts builder (reference for plist patterns)
- Python `plistlib` — [stdlib docs](https://docs.python.org/3/library/plistlib.html)

### Coverage of Apple Intelligence Actions
- [9to5Mac: 25+ new Shortcuts actions in iOS 26](https://9to5mac.com/2025/12/09/ios-26s-shortcuts-app-adds-25-new-actions-heres-everything-new/)
- [MacObserver: All 25+ new actions in iOS 26](https://www.macobserver.com/news/all-25-new-shortcuts-actions-introduced-in-ios-26-heres-everything-you-can-do/)
- [Cult of Mac: 13 mind-blowing iOS 26 shortcuts with Apple Intelligence](https://www.cultofmac.com/guide/13-mind-blowing-ios-26-shortcuts-with-apple-intelligence)
- [TechBuzz: Apple Makes Shortcuts a Powerful AI Automation Tool](https://www.techbuzz.ai/articles/apple-quietly-makes-shortcuts-app-a-powerful-ai-automation-tool)

## 13. Commenting & Readability

Shortcuts must be **thoroughly commented**. Users can inspect shortcuts in the Shortcuts app when choosing whether to install them. Every published shortcut must be as clear and self-explicating as possible.

### Comment Action

The Shortcuts comment action (`is.workflow.actions.comment`) adds visible annotations in the Shortcuts editor:

```python
{
    "WFWorkflowActionIdentifier": "is.workflow.actions.comment",
    "WFWorkflowActionParameters": {
        "WFCommentActionText": "Step 1: Get the clipboard contents and pass to Apple Intelligence for summarization."
    }
}
```

### Commenting Requirements for Published Shortcuts

1. **Header comment** — First action must be a comment explaining what the shortcut does, its expected input/output, and any requirements (e.g., "Requires Apple Intelligence")
2. **Section comments** — Before each logical group of actions, add a comment explaining the intent (e.g., "Step 2: Filter results to only include today's events")
3. **Control flow comments** — Before If/Repeat/Menu blocks, explain the branching logic and what each branch handles
4. **Variable comments** — When setting or referencing non-obvious variables, explain what they hold and why
5. **Integration comments** — When calling app-specific actions or Apple Intelligence, note any permissions or capabilities required

The skill's action catalog templates include comment actions in their "Common Pattern" examples. The builder template includes a `make_comment(text)` helper.

## 14. Open Questions

### Resolved

- ~~Apple Intelligence action identifiers~~ — Extracted from macOS 26 system: `is.workflow.actions.askllm` for Use Model, `com.apple.WritingTools.WritingToolsAppIntentsExtension.*` for Writing Tools. See Section 5, Tier 5.
- ~~Variable wiring details~~ — Fully documented from Apple gallery shortcuts. Two serialization types: `WFTextTokenAttachment` (single ref) and `WFTextTokenString` (embedded in text). See Section 3.
- ~~Signing requires network~~ — Confirmed: `shortcuts sign -m anyone` requires iCloud connectivity. Offline signing available via `-m people-who-know-me` but limits importability.

### Remaining

1. **App-specific action identifiers** — Mail, Calendar, Reminders, Notes, Finder, Safari all expose actions through Shortcuts. The exact identifiers and parameter schemas for Tier 1 actions need extraction during implementation. Strategy: create representative shortcuts in the GUI, export via `shortcuts sign`, and inspect with `plutil`.

2. **Import behavior with name conflicts** — When `open signed.shortcut` triggers the import dialog for a shortcut with the same name as an existing one, does it overwrite, create a duplicate, or prompt? Needs testing during implementation.

3. **Image Playground action identifier** — The Create Image action identifier has not been extracted. Needs a macOS 26 system with Image Playground enabled.

4. **WritingTools intent parameter format** — The Writing Tools actions use App Intents identifiers rather than `is.workflow.actions.*`. The exact parameter serialization format (do `text` and `tone` use the same `WFTextTokenAttachment` pattern?) needs verification from real shortcuts using these actions.

## 15. Future Plans

Beyond the initial `shortcuts-authoring` and `shortcuts-usage` skills, the following are planned for future arcs:

1. **AppleScript / osascript integration** — A dedicated skill (or skill extension) for authoring shortcuts that leverage `Run AppleScript` actions (`is.workflow.actions.runscript`). AppleScript unlocks deep app automation that Shortcuts actions alone cannot reach — scripting Finder, System Events, accessibility APIs, GUI scripting, inter-app communication via `tell` blocks, and more. This includes:
   - AppleScript action templates with common patterns (Finder operations, app scripting, UI automation via System Events)
   - `osascript` CLI integration for testing AppleScript snippets outside of Shortcuts
   - JXA (JavaScript for Automation) as an alternative scripting bridge for developers who prefer JavaScript
   - Hybrid patterns: Shortcuts for orchestration + AppleScript for deep app control

2. **`shortcuts-usage` skill** — Teaching agents to discover, invoke, and orchestrate installed shortcuts. Includes dev-loop testing support for the authoring workflow.

3. **Marketplace infrastructure** — Discovery, versioning, dependency management, and update mechanisms for published shortcut plugins.

4. **iOS / iPadOS targeting** — Extending the authoring skill to produce shortcuts that work across Apple platforms, handling platform-specific action availability and capabilities.
