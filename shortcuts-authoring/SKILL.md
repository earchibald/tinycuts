---
name: shortcuts-authoring
description: Author, sign, and package macOS Shortcuts as binary plists for distribution as Claude Code plugins. Teaches agents to build production-quality .shortcut files using the full Shortcuts action library.
tags:
  - macos
  - shortcuts
  - automation
  - apple-intelligence
---

# Shortcuts Authoring

Author macOS Shortcuts as binary property lists (`.shortcut` files), sign them for distribution, and package them as Claude Code plugins. This skill enables a marketplace of macOS automation capabilities delivered as Shortcuts — bridging macOS's walled garden for agentic use without MCP servers.

Use this skill when building a shortcut plugin that automates macOS: app control, file operations, clipboard/notifications, scripting (JXA), or Apple Intelligence. The skill provides a Python builder template, a complete action catalog, and a plugin packaging template.

> **Ref:** [Shortcuts User Guide](https://support.apple.com/guide/shortcuts-mac/welcome/mac), [Run shortcuts from the command line](https://support.apple.com/guide/shortcuts-mac/run-shortcuts-from-the-command-line-apd455c82f02/mac)

## Quick Start

1. **Copy the builder template:**
   ```bash
   cp resources/builder_template.py my_shortcut.py
   ```

2. **Fill in the `actions` list** using the Action Catalog below. Each action is a Python dict with `WFWorkflowActionIdentifier` and `WFWorkflowActionParameters`.

3. **Build the shortcut:**
   ```bash
   python3 my_shortcut.py
   ```
   This writes `unsigned.shortcut` and validates it with `plutil -lint`.

4. **Sign for distribution:**
   ```bash
   shortcuts sign -m anyone -i unsigned.shortcut -o signed.shortcut
   ```
   Requires Apple ID and network for iCloud notarization.

5. **Import into Shortcuts.app:**
   ```bash
   open signed.shortcut
   ```
   Confirm in the import dialog.

6. **Test from CLI:**
   ```bash
   shortcuts run "My Shortcut"
   echo "input text" | shortcuts run "My Shortcut"
   ```

7. **Package as a plugin** using `resources/plugin_template/` — see Plugin Packaging section.

> **Ref:** See `resources/action_examples/` for complete, runnable examples.

## Format Reference

### Binary Plist Structure

`.shortcut` files are binary property lists (bplist). The format is not officially documented by Apple — all knowledge comes from community reverse-engineering.

> **Ref:** [Zachary7829's Shortcuts File Format](https://zachary7829.github.io/blog/shortcuts/fileformat), [Cherri File Format](https://cherrilang.org/compiler/file-format.html)

#### Top-Level Schema

| Key | Type | Description |
|-----|------|-------------|
| `WFWorkflowActions` | Array | The action sequence (core of the shortcut) |
| `WFWorkflowClientVersion` | Integer | Client version number (e.g., `1700` for macOS 26) |
| `WFWorkflowClientRelease` | String | Semantic version string (e.g., `"26.0"`) |
| `WFWorkflowMinimumClientVersion` | Integer | Minimum version required to run |
| `WFWorkflowMinimumClientVersionString` | String | Minimum version as string (e.g., `"1700"`) |
| `WFWorkflowIcon` | Dict | `WFWorkflowIconStartColor` (int) + `WFWorkflowIconGlyphNumber` (int) |
| `WFWorkflowInputContentItemClasses` | Array | Accepted input types (e.g., `WFStringContentItem`, `WFURLContentItem`) |
| `WFWorkflowTypes` | Array | Where it appears: `MenuBar`, `QuickActions`, `ActionExtension`, etc. |
| `WFWorkflowImportQuestions` | Array | Prompts shown during import (usually `[]`) |
| `WFWorkflowHasShortcutInputVariables` | Bool | Whether the shortcut accepts input variables |

The builder template's `make_shortcut()` sets all these with sensible defaults.

### Action Structure

Each entry in `WFWorkflowActions` is a dict with two keys:

```python
{
    "WFWorkflowActionIdentifier": "is.workflow.actions.notification",
    "WFWorkflowActionParameters": {
        "WFNotificationActionBody": "Hello!",
        "WFNotificationActionTitle": "Alert",
    },
}
```

- **`WFWorkflowActionIdentifier`** — reverse-domain string (e.g., `is.workflow.actions.*` for built-in actions)
- **`WFWorkflowActionParameters`** — dict of action-specific configuration

Actions that produce output include a `"UUID"` key in their parameters. Downstream actions reference it via `OutputUUID`.

> **Ref:** [iOS-Shortcuts-Reference (GitHub)](https://github.com/sebj/iOS-Shortcuts-Reference)

### Variable System

#### Single Variable Reference (`WFTextTokenAttachment`)

When a parameter is purely a variable reference (no surrounding text):

```python
# Use make_attachment() helper:
make_attachment(output_uuid, "Clipboard")

# Produces:
{
    "Value": {
        "OutputName": "Clipboard",
        "OutputUUID": "09B5964F-CBB7-429E-B6D3-3BE92C08E3FF",
        "Type": "ActionOutput",
    },
    "WFSerializationType": "WFTextTokenAttachment",
}
```

The `Type` field can be: `ActionOutput` (references another action's UUID), `Variable` (named/magic variable), `ExtensionInput`, `Ask`, or `CurrentDate`.

#### Variable Embedded in Text (`WFTextTokenString`)

When a variable is interpolated within a string, the string contains U+FFFC (Object Replacement Character) as a placeholder:

```python
# Use make_text_with_variable() helper:
make_text_with_variable("Summary: ", summary_uuid, "Summarize Text")

# Produces:
{
    "Value": {
        "string": "Summary: \ufffc",
        "attachmentsByRange": {
            "{9, 1}": {
                "OutputName": "Summarize Text",
                "OutputUUID": "...",
                "Type": "ActionOutput",
            }
        },
    },
    "WFSerializationType": "WFTextTokenString",
}
```

The `{position, 1}` key uses NSString character indices (UTF-16 code units). `len()` works for ASCII/BMP text. For emoji/non-BMP: `position = len(text.encode('utf-16-le')) // 2`.

#### Magic Variables

Built-in variables like `Repeat Item` use `Type: Variable` with `VariableName`:

```python
# Use make_magic_variable() helper:
make_magic_variable("Repeat Item")

# Produces:
{
    "Value": {
        "Type": "Variable",
        "VariableName": "Repeat Item",
    },
    "WFSerializationType": "WFTextTokenAttachment",
}
```

> **Ref:** Variable structures extracted from Apple gallery shortcuts at `WorkflowKit.framework/Resources/Gallery.bundle/` (MorningReport.wflow, ActionItems.wflow, DocumentReview.wflow). See also [0xdevalias decompilation notes](https://gist.github.com/0xdevalias/27d9aea9529be7b6ce59055332a94477).

### Control Flow

Control flow actions (If, Repeat, Menu) use a shared `GroupingIdentifier` UUID and `WFControlFlowMode` integer:

| Mode | Meaning |
|------|---------|
| `0` | Start of block (If / Repeat / Choose from Menu) |
| `1` | Middle of block (Otherwise / menu case) |
| `2` | End of block (End If / End Repeat / End Menu) |

All actions in a block share the same `GroupingIdentifier`. The end action also has a `UUID` key for output referencing.

**Helpers:** `make_if_block()`, `make_repeat_count()`, `make_repeat_each()`, `make_menu()` — all handle GroupingIdentifier and mode values automatically.

### Signing

Exported `.shortcut` files must be cryptographically signed before import (since macOS 12):

```bash
shortcuts sign -m anyone -i unsigned.shortcut -o signed.shortcut
```

Modes:
- `anyone` — notarized via iCloud, suitable for public sharing
- `people-who-know-me` — local signing, contacts-only

Import via `open signed.shortcut` (triggers Shortcuts.app import dialog — user must confirm).

> **Ref:** [Run shortcuts from the command line — Apple Support](https://support.apple.com/guide/shortcuts-mac/run-shortcuts-from-the-command-line-apd455c82f02/mac)
