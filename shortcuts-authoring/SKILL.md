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
| `WFWorkflowClientVersion` | String | Client version string (e.g., `"1700"` for macOS 26). Must be a string — WorkflowKit's migration code calls string methods on this value. |
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

## Action Catalog

### Tier 1: App Automation

#### Open App

**Identifier:** `is.workflow.actions.openapp`

**Requires:** macOS 12+

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `WFAppIdentifier` | String | No | Bundle ID of the app to open (e.g., `"com.apple.Safari"`) |
| `WFSelectedApp` | Dict | No | Dict with `BundleIdentifier` and `Name` keys |

```python
{
    "WFWorkflowActionIdentifier": "is.workflow.actions.openapp",
    "WFWorkflowActionParameters": {
        "WFAppIdentifier": "com.apple.Safari",
        "WFSelectedApp": {
            "BundleIdentifier": "com.apple.Safari",
            "Name": "Safari",
        },
    },
}
```

**Variable wiring example:** Open App does not produce output; no chaining needed.

> **Note on app-specific actions:** Mail, Calendar, Reminders, Notes, Finder, Safari, and Maps have their own action identifiers that follow the pattern `is.workflow.actions.<verb><appname>` (e.g., `is.workflow.actions.mail.send`). Exact identifiers for app-specific actions should be extracted at runtime from the Shortcuts.app action library or from Apple gallery shortcuts.

---

### Tier 2: File System

#### Get File

**Identifier:** `is.workflow.actions.documentpicker.open`

**Requires:** macOS 12+

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `WFFile` | Variable ref | No | Variable reference to the file to open |
| `WFGetFilePath` | String | No | Path to the file to open |
| `UUID` | String | Yes | UUID for referencing this action's output |

```python
get_file_uuid = new_uuid()

{
    "WFWorkflowActionIdentifier": "is.workflow.actions.documentpicker.open",
    "WFWorkflowActionParameters": {
        "WFGetFilePath": "/Users/me/Documents/notes.txt",
        "UUID": get_file_uuid,
    },
}
```

**Variable wiring example:**

```python
get_file_uuid = new_uuid()
notify_uuid = new_uuid()

actions = [
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.documentpicker.open",
        "WFWorkflowActionParameters": {
            "WFGetFilePath": "/Users/me/Documents/notes.txt",
            "UUID": get_file_uuid,
        },
    },
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.notification",
        "WFWorkflowActionParameters": {
            "WFNotificationActionBody": make_attachment(get_file_uuid, "Get File"),
            "WFNotificationActionTitle": "File Contents",
        },
    },
]
```

---

#### Save File

**Identifier:** `is.workflow.actions.documentpicker.save`

**Requires:** macOS 12+

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `WFInput` | Variable ref | Yes | Variable reference to the content to save |
| `WFFileDestinationPath` | String/Variable | No | Destination path for the file |

```python
{
    "WFWorkflowActionIdentifier": "is.workflow.actions.documentpicker.save",
    "WFWorkflowActionParameters": {
        "WFInput": make_attachment(source_uuid, "Previous Action"),
        "WFFileDestinationPath": "/Users/me/Documents/output.txt",
    },
}
```

**Variable wiring example:**

```python
# Chain: Get Clipboard → Save File
clipboard_uuid = new_uuid()

actions = [
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.getclipboard",
        "WFWorkflowActionParameters": {"UUID": clipboard_uuid},
    },
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.documentpicker.save",
        "WFWorkflowActionParameters": {
            "WFInput": make_attachment(clipboard_uuid, "Clipboard"),
            "WFFileDestinationPath": "/Users/me/Desktop/clipboard.txt",
        },
    },
]
```

---

#### Get Folder Contents

**Identifier:** `is.workflow.actions.file.getfoldercontents`

**Requires:** macOS 12+

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `WFFolder` | Variable ref | Yes | Variable reference to the folder |
| `UUID` | String | Yes | UUID for referencing this action's output |

```python
folder_uuid = new_uuid()

{
    "WFWorkflowActionIdentifier": "is.workflow.actions.file.getfoldercontents",
    "WFWorkflowActionParameters": {
        "WFFolder": make_attachment(source_uuid, "Folder"),
        "UUID": folder_uuid,
    },
}
```

---

#### Rename File

**Identifier:** `is.workflow.actions.file.rename`

**Requires:** macOS 12+

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `WFFile` | Variable ref | Yes | Variable reference to the file to rename |
| `WFNewFilename` | String | Yes | New filename (without path) |

```python
{
    "WFWorkflowActionIdentifier": "is.workflow.actions.file.rename",
    "WFWorkflowActionParameters": {
        "WFFile": make_attachment(file_uuid, "Get File"),
        "WFNewFilename": "renamed_file.txt",
    },
}
```

---

### Tier 3: System Services

#### Get Clipboard

**Identifier:** `is.workflow.actions.getclipboard`

**Requires:** macOS 12+

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `UUID` | String | Yes | UUID for referencing this action's output |

```python
clipboard_uuid = new_uuid()

{
    "WFWorkflowActionIdentifier": "is.workflow.actions.getclipboard",
    "WFWorkflowActionParameters": {"UUID": clipboard_uuid},
}
```

---

#### Set Clipboard

**Identifier:** `is.workflow.actions.setclipboard`

**Requires:** macOS 12+

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `WFInput` | Variable ref | Yes | Variable reference to the content to copy to clipboard |

```python
{
    "WFWorkflowActionIdentifier": "is.workflow.actions.setclipboard",
    "WFWorkflowActionParameters": {
        "WFInput": make_attachment(source_uuid, "Previous Action"),
    },
}
```

---

#### Take Screenshot

**Identifier:** `is.workflow.actions.takescreenshot`

**Requires:** macOS 12+

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `WFScreenshotType` | String | No | `"Full Screen"`, `"Window"`, or `"Interactive"` (default: `"Full Screen"`) |
| `UUID` | String | Yes | UUID for referencing this action's output |

```python
screenshot_uuid = new_uuid()

{
    "WFWorkflowActionIdentifier": "is.workflow.actions.takescreenshot",
    "WFWorkflowActionParameters": {
        "WFScreenshotType": "Full Screen",
        "UUID": screenshot_uuid,
    },
}
```

---

#### Show Notification

**Identifier:** `is.workflow.actions.notification`

**Requires:** macOS 12+

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `WFNotificationActionBody` | String/Variable | Yes | Body text of the notification |
| `WFNotificationActionTitle` | String | No | Title of the notification |
| `WFNotificationActionSound` | Bool | No | Whether to play a sound (default: `True`) |

```python
{
    "WFWorkflowActionIdentifier": "is.workflow.actions.notification",
    "WFWorkflowActionParameters": {
        "WFNotificationActionBody": make_attachment(source_uuid, "Previous Action"),
        "WFNotificationActionTitle": "Alert",
        "WFNotificationActionSound": True,
    },
}
```

**Common pattern: Get Clipboard → Summarize → Notify**

```python
# Common Pattern: Get Clipboard → Summarize → Notify
clipboard_uuid = new_uuid()
summary_uuid = new_uuid()

actions = [
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.getclipboard",
        "WFWorkflowActionParameters": {"UUID": clipboard_uuid},
    },
    {
        "WFWorkflowActionIdentifier":
            "com.apple.WritingTools.WritingToolsAppIntentsExtension.SummarizeTextIntent",
        "WFWorkflowActionParameters": {
            "text": make_attachment(clipboard_uuid, "Clipboard"),
            "summaryType": "summarize",
            "UUID": summary_uuid,
        },
    },
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.notification",
        "WFWorkflowActionParameters": {
            "WFNotificationActionBody": make_attachment(summary_uuid, "Summarize Text"),
            "WFNotificationActionTitle": "Clipboard Summary",
        },
    },
]
```

---

### Tier 4: Scripting

#### Run JavaScript for Automation (JXA)

**Identifier:** `is.workflow.actions.runjavascript`

**Requires:** macOS 12+

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `WFJavaScript` | String | Yes | JavaScript for Automation (JXA) source code to run |
| `UUID` | String | Yes | UUID for referencing this action's output |

```python
jxa_uuid = new_uuid()

{
    "WFWorkflowActionIdentifier": "is.workflow.actions.runjavascript",
    "WFWorkflowActionParameters": {
        "WFJavaScript": "Application('Finder').home().name()",
        "UUID": jxa_uuid,
    },
}
```

**Variable wiring example:**

```python
jxa_uuid = new_uuid()

actions = [
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.runjavascript",
        "WFWorkflowActionParameters": {
            "WFJavaScript": "Application('System Events').frontmost().name()",
            "UUID": jxa_uuid,
        },
    },
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.notification",
        "WFWorkflowActionParameters": {
            "WFNotificationActionBody": make_attachment(jxa_uuid, "Run JavaScript for Automation"),
            "WFNotificationActionTitle": "Front App",
        },
    },
]
```

---

#### URL

**Identifier:** `is.workflow.actions.url`

**Requires:** macOS 12+

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `WFURLActionURL` | String/Variable | Yes | The URL string or variable |
| `UUID` | String | Yes | UUID for referencing this action's output |

```python
url_uuid = new_uuid()

{
    "WFWorkflowActionIdentifier": "is.workflow.actions.url",
    "WFWorkflowActionParameters": {
        "WFURLActionURL": "https://example.com",
        "UUID": url_uuid,
    },
}
```

---

#### Open URL

**Identifier:** `is.workflow.actions.openurl`

**Requires:** macOS 12+

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `WFInput` | Variable ref | Yes | Variable reference to the URL to open |

```python
{
    "WFWorkflowActionIdentifier": "is.workflow.actions.openurl",
    "WFWorkflowActionParameters": {
        "WFInput": make_attachment(url_uuid, "URL"),
    },
}
```

**Variable wiring example:**

```python
url_uuid = new_uuid()

actions = [
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.url",
        "WFWorkflowActionParameters": {
            "WFURLActionURL": "https://apple.com",
            "UUID": url_uuid,
        },
    },
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.openurl",
        "WFWorkflowActionParameters": {
            "WFInput": make_attachment(url_uuid, "URL"),
        },
    },
]
```

---

### Tier 5: Apple Intelligence

> **Requires:** macOS 15.1+ (Sequoia) with Apple Intelligence enabled. All identifiers below are verified from the macOS 26 system.

> **Ref:** [Use Apple Intelligence in Shortcuts](https://support.apple.com/guide/mac-help/use-apple-intelligence-in-shortcuts-mchl91750563/mac). Identifiers extracted from Apple gallery shortcuts in `WorkflowKit.framework/Resources/Gallery.bundle/`.

#### Use Model

**Identifier:** `is.workflow.actions.askllm`

**Requires:** macOS 15.1+, Apple Intelligence

**Direct model aliases:**
- `com.apple.Shortcuts.AskAFMAction3B` — on-device model
- `com.apple.Shortcuts.AskMontaraAction` — server/PCC model

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `WFLLMPrompt` | Text/Variable | Yes | The prompt to send to the model |
| `WFLLMModel` | String | No | Model to use (default: `"Apple Intelligence"`) |
| `WFGenerativeResultType` | String | No | Output format: `"Text"`, `"List"`, `"Dictionary"`, `"Automatic"` |
| `FollowUp` | Bool | No | Whether this is a follow-up in a conversation |
| `UUID` | String | Yes | UUID for referencing this action's output |

```python
llm_uuid = new_uuid()

{
    "WFWorkflowActionIdentifier": "is.workflow.actions.askllm",
    "WFWorkflowActionParameters": {
        "WFLLMPrompt": make_attachment(input_uuid, "Input"),
        "WFLLMModel": "Apple Intelligence",
        "WFGenerativeResultType": "Text",
        "FollowUp": False,
        "UUID": llm_uuid,
    },
}
```

**Variable wiring example:**

```python
clipboard_uuid = new_uuid()
llm_uuid = new_uuid()

actions = [
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.getclipboard",
        "WFWorkflowActionParameters": {"UUID": clipboard_uuid},
    },
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.askllm",
        "WFWorkflowActionParameters": {
            "WFLLMPrompt": make_text_with_variable("Improve this text: ", clipboard_uuid, "Clipboard"),
            "WFGenerativeResultType": "Text",
            "UUID": llm_uuid,
        },
    },
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.notification",
        "WFWorkflowActionParameters": {
            "WFNotificationActionBody": make_attachment(llm_uuid, "Use Model"),
            "WFNotificationActionTitle": "Improved Text",
        },
    },
]
```

---

#### Summarize Text

**Identifier:** `com.apple.WritingTools.WritingToolsAppIntentsExtension.SummarizeTextIntent`

**Requires:** macOS 15.1+, Apple Intelligence

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `text` | Variable | Yes | Variable reference to the text to summarize |
| `summaryType` | String | No | `"summarize"` (default) or `"createKeyPoints"` |
| `UUID` | String | Yes | UUID for referencing this action's output |

```python
summary_uuid = new_uuid()

{
    "WFWorkflowActionIdentifier":
        "com.apple.WritingTools.WritingToolsAppIntentsExtension.SummarizeTextIntent",
    "WFWorkflowActionParameters": {
        "text": make_attachment(input_uuid, "Input"),
        "summaryType": "summarize",
        "UUID": summary_uuid,
    },
}
```

---

#### Rewrite Text

**Identifier:** `com.apple.WritingTools.WritingToolsAppIntentsExtension.RewriteTextIntent`

**Requires:** macOS 15.1+, Apple Intelligence

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `text` | Variable | Yes | Variable reference to the text to rewrite |
| `UUID` | String | Yes | UUID for referencing this action's output |

```python
rewrite_uuid = new_uuid()

{
    "WFWorkflowActionIdentifier":
        "com.apple.WritingTools.WritingToolsAppIntentsExtension.RewriteTextIntent",
    "WFWorkflowActionParameters": {
        "text": make_attachment(input_uuid, "Input"),
        "UUID": rewrite_uuid,
    },
}
```

---

#### Proofread Text

**Identifier:** `com.apple.WritingTools.WritingToolsAppIntentsExtension.ProofreadIntent`

**Requires:** macOS 15.1+, Apple Intelligence

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `text` | Variable | Yes | Variable reference to the text to proofread |
| `UUID` | String | Yes | UUID for referencing this action's output |

```python
proofread_uuid = new_uuid()

{
    "WFWorkflowActionIdentifier":
        "com.apple.WritingTools.WritingToolsAppIntentsExtension.ProofreadIntent",
    "WFWorkflowActionParameters": {
        "text": make_attachment(input_uuid, "Input"),
        "UUID": proofread_uuid,
    },
}
```

---

#### Adjust Tone

**Identifier:** `com.apple.WritingTools.WritingToolsAppIntentsExtension.AdjustToneIntent`

**Requires:** macOS 15.1+, Apple Intelligence

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `text` | Variable | Yes | Variable reference to the text |
| `tone` | String | Yes | `"friendly"`, `"professional"`, or `"concise"` |
| `UUID` | String | Yes | UUID for referencing this action's output |

```python
tone_uuid = new_uuid()

{
    "WFWorkflowActionIdentifier":
        "com.apple.WritingTools.WritingToolsAppIntentsExtension.AdjustToneIntent",
    "WFWorkflowActionParameters": {
        "text": make_attachment(input_uuid, "Input"),
        "tone": "professional",
        "UUID": tone_uuid,
    },
}
```

---

#### Make List

**Identifier:** `com.apple.WritingTools.WritingToolsAppIntentsExtension.FormatListIntent`

**Requires:** macOS 15.1+, Apple Intelligence

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `text` | Variable | Yes | Variable reference to the text to format as a list |
| `UUID` | String | Yes | UUID for referencing this action's output |

```python
list_uuid = new_uuid()

{
    "WFWorkflowActionIdentifier":
        "com.apple.WritingTools.WritingToolsAppIntentsExtension.FormatListIntent",
    "WFWorkflowActionParameters": {
        "text": make_attachment(input_uuid, "Input"),
        "UUID": list_uuid,
    },
}
```

---

#### Make Table

**Identifier:** `com.apple.WritingTools.WritingToolsAppIntentsExtension.FormatTableIntent`

**Requires:** macOS 15.1+, Apple Intelligence

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `text` | Variable | Yes | Variable reference to the text to format as a table |
| `UUID` | String | Yes | UUID for referencing this action's output |

```python
table_uuid = new_uuid()

{
    "WFWorkflowActionIdentifier":
        "com.apple.WritingTools.WritingToolsAppIntentsExtension.FormatTableIntent",
    "WFWorkflowActionParameters": {
        "text": make_attachment(input_uuid, "Input"),
        "UUID": table_uuid,
    },
}
```

> **Note on Image Playground:** The Image Playground action identifier is TBD — it needs extraction from macOS 26 with Image Playground enabled.

---

### Tier 6: Control Flow

> **Note:** Prefer using the builder template helpers (`make_if_block`, `make_repeat_count`, `make_repeat_each`, `make_menu`) over manual construction of control flow actions. The helpers handle `GroupingIdentifier` and `WFControlFlowMode` values automatically and are less error-prone.

#### Comment

**Identifier:** `is.workflow.actions.comment`

**Requires:** macOS 12+

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `WFCommentActionText` | String | Yes | Comment text (displayed in Shortcuts editor, not executed) |

```python
{
    "WFWorkflowActionIdentifier": "is.workflow.actions.comment",
    "WFWorkflowActionParameters": {
        "WFCommentActionText": "This section handles the file processing",
    },
}
```

---

#### If / Otherwise / End If

**Identifier:** `is.workflow.actions.conditional`

**Requires:** macOS 12+

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `WFCondition` | Int/String | Yes | Condition type (e.g., `100` for "is", `101` for "is not") |
| `WFConditionalActionString` | String | No | Value to compare against |
| `GroupingIdentifier` | String | Yes | Shared UUID linking If/Otherwise/End If |
| `WFControlFlowMode` | Int | Yes | `0` = If, `1` = Otherwise, `2` = End If |
| `WFInput` | Variable ref | No | The variable to evaluate |

```python
# Prefer make_if_block() helper from builder_template.py
group_id = new_uuid()

actions = [
    # If block (mode 0)
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {
            "WFCondition": 100,
            "WFConditionalActionString": "hello",
            "GroupingIdentifier": group_id,
            "WFControlFlowMode": 0,
            "WFInput": make_attachment(input_uuid, "Input"),
        },
    },
    # ... actions inside If ...
    # Otherwise block (mode 1)
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {
            "GroupingIdentifier": group_id,
            "WFControlFlowMode": 1,
        },
    },
    # ... actions inside Otherwise ...
    # End If block (mode 2)
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
        "WFWorkflowActionParameters": {
            "GroupingIdentifier": group_id,
            "WFControlFlowMode": 2,
        },
    },
]
```

---

#### Repeat (Count)

**Identifier:** `is.workflow.actions.repeat.count`

**Requires:** macOS 12+

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `WFRepeatCount` | Int | Yes | Number of times to repeat |
| `GroupingIdentifier` | String | Yes | Shared UUID linking Start/End Repeat |
| `WFControlFlowMode` | Int | Yes | `0` = Start Repeat, `2` = End Repeat |

```python
# Prefer make_repeat_count() helper from builder_template.py
group_id = new_uuid()

actions = [
    # Start Repeat (mode 0)
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.repeat.count",
        "WFWorkflowActionParameters": {
            "WFRepeatCount": 3,
            "GroupingIdentifier": group_id,
            "WFControlFlowMode": 0,
        },
    },
    # ... repeated actions ...
    # End Repeat (mode 2)
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.repeat.count",
        "WFWorkflowActionParameters": {
            "GroupingIdentifier": group_id,
            "WFControlFlowMode": 2,
        },
    },
]
```

---

#### Repeat with Each

**Identifier:** `is.workflow.actions.repeat.each`

**Requires:** macOS 12+

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `WFInput` | Variable | Yes | Variable reference to the list to iterate over |
| `GroupingIdentifier` | String | Yes | Shared UUID linking Start/End Repeat |
| `WFControlFlowMode` | Int | Yes | `0` = Start Repeat, `2` = End Repeat |

```python
# Prefer make_repeat_each() helper from builder_template.py
group_id = new_uuid()

actions = [
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.repeat.each",
        "WFWorkflowActionParameters": {
            "WFInput": make_attachment(list_uuid, "List"),
            "GroupingIdentifier": group_id,
            "WFControlFlowMode": 0,
        },
    },
    # Use make_magic_variable("Repeat Item") inside the loop
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.repeat.each",
        "WFWorkflowActionParameters": {
            "GroupingIdentifier": group_id,
            "WFControlFlowMode": 2,
        },
    },
]
```

---

#### Choose from Menu

**Identifier:** `is.workflow.actions.choosefrommenu`

**Requires:** macOS 12+

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `WFMenuPrompt` | String | No | Prompt shown to the user |
| `WFMenuItems` | Array | Yes | Array of menu item dicts with `WFItemType` and `WFMenuItemTitle` |
| `WFMenuItemTitle` | String | Yes (in cases) | Title of this menu item branch |
| `GroupingIdentifier` | String | Yes | Shared UUID linking all menu actions |
| `WFControlFlowMode` | Int | Yes | `0` = Menu start, `1` = menu case, `2` = End Menu |

```python
# Prefer make_menu() helper from builder_template.py
group_id = new_uuid()

actions = [
    # Menu start (mode 0)
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.choosefrommenu",
        "WFWorkflowActionParameters": {
            "WFMenuPrompt": "Choose an option",
            "WFMenuItems": [
                {"WFItemType": 0, "WFMenuItemTitle": "Option A"},
                {"WFItemType": 0, "WFMenuItemTitle": "Option B"},
            ],
            "GroupingIdentifier": group_id,
            "WFControlFlowMode": 0,
        },
    },
    # Option A case (mode 1)
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.choosefrommenu",
        "WFWorkflowActionParameters": {
            "WFMenuItemTitle": "Option A",
            "GroupingIdentifier": group_id,
            "WFControlFlowMode": 1,
        },
    },
    # ... actions for Option A ...
    # Option B case (mode 1)
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.choosefrommenu",
        "WFWorkflowActionParameters": {
            "WFMenuItemTitle": "Option B",
            "GroupingIdentifier": group_id,
            "WFControlFlowMode": 1,
        },
    },
    # ... actions for Option B ...
    # End Menu (mode 2)
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.choosefrommenu",
        "WFWorkflowActionParameters": {
            "GroupingIdentifier": group_id,
            "WFControlFlowMode": 2,
        },
    },
]
```

---

#### Set Variable

**Identifier:** `is.workflow.actions.setvariable`

**Requires:** macOS 12+

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `WFVariableName` | String | Yes | Name to assign to the variable |
| `WFInput` | Variable | Yes | Variable reference to store |

```python
{
    "WFWorkflowActionIdentifier": "is.workflow.actions.setvariable",
    "WFWorkflowActionParameters": {
        "WFVariableName": "MyResult",
        "WFInput": make_attachment(source_uuid, "Previous Action"),
    },
}
```

---

#### Get Variable

**Identifier:** `is.workflow.actions.getvariable`

**Requires:** macOS 12+

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `WFVariable` | Variable ref | Yes | Reference to the named variable to retrieve |
| `UUID` | String | Yes | UUID for referencing this action's output |

```python
get_var_uuid = new_uuid()

{
    "WFWorkflowActionIdentifier": "is.workflow.actions.getvariable",
    "WFWorkflowActionParameters": {
        "WFVariable": {
            "Value": {"Type": "Variable", "VariableName": "MyResult"},
            "WFSerializationType": "WFTextTokenAttachment",
        },
        "UUID": get_var_uuid,
    },
}
```

---

#### Dictionary

**Identifier:** `is.workflow.actions.dictionary`

**Requires:** macOS 12+

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `WFItems` | Dict | Yes | The dictionary data structure |
| `UUID` | String | Yes | UUID for referencing this action's output |

```python
dict_uuid = new_uuid()

{
    "WFWorkflowActionIdentifier": "is.workflow.actions.dictionary",
    "WFWorkflowActionParameters": {
        "WFItems": {
            "Value": {
                "WFDictionaryFieldValueItems": [
                    {
                        "WFItemType": 0,
                        "WFKey": {"Value": {"string": "name"}, "WFSerializationType": "WFTextTokenString"},
                        "WFValue": {"Value": {"string": "Alice"}, "WFSerializationType": "WFTextTokenString"},
                    }
                ]
            },
            "WFSerializationType": "WFDictionaryFieldValue",
        },
        "UUID": dict_uuid,
    },
}
```

---

#### Get Dictionary Value

**Identifier:** `is.workflow.actions.getvalueforkey`

**Requires:** macOS 12+

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `WFDictionaryKey` | String | Yes | Key to retrieve from the dictionary |
| `WFInput` | Variable | Yes | Variable reference to the dictionary |
| `UUID` | String | Yes | UUID for referencing this action's output |

```python
value_uuid = new_uuid()

{
    "WFWorkflowActionIdentifier": "is.workflow.actions.getvalueforkey",
    "WFWorkflowActionParameters": {
        "WFDictionaryKey": "name",
        "WFInput": make_attachment(dict_uuid, "Dictionary"),
        "UUID": value_uuid,
    },
}
```

---

#### List

**Identifier:** `is.workflow.actions.list`

**Requires:** macOS 12+

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `WFItems` | Array | Yes | Array of items (strings, variables, or mixed) |
| `UUID` | String | Yes | UUID for referencing this action's output |

```python
list_uuid = new_uuid()

{
    "WFWorkflowActionIdentifier": "is.workflow.actions.list",
    "WFWorkflowActionParameters": {
        "WFItems": [
            {"WFItemType": 0, "WFValue": {"Value": {"string": "apple"}, "WFSerializationType": "WFTextTokenString"}},
            {"WFItemType": 0, "WFValue": {"Value": {"string": "banana"}, "WFSerializationType": "WFTextTokenString"}},
        ],
        "UUID": list_uuid,
    },
}
```

---

#### Get Item from List

**Identifier:** `is.workflow.actions.getitemfromlist`

**Requires:** macOS 12+

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `WFItemSpecifier` | String | Yes | `"First Item"`, `"Last Item"`, `"Random Item"`, or `"Item At Index"` |
| `WFItemIndex` | Int | No | Zero-based index (only when `WFItemSpecifier` is `"Item At Index"`) |
| `WFInput` | Variable | Yes | Variable reference to the list |
| `UUID` | String | Yes | UUID for referencing this action's output |

```python
item_uuid = new_uuid()

{
    "WFWorkflowActionIdentifier": "is.workflow.actions.getitemfromlist",
    "WFWorkflowActionParameters": {
        "WFItemSpecifier": "First Item",
        "WFInput": make_attachment(list_uuid, "List"),
        "UUID": item_uuid,
    },
}
```

---

#### Output

**Identifier:** `is.workflow.actions.output`

**Requires:** macOS 12+

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `WFOutput` | Variable ref | Yes | Variable reference to the value to output |

> **Note:** This action provides stdout output when running via `shortcuts run` from the command line. Use it as the final action in shortcuts intended for CLI use.

```python
{
    "WFWorkflowActionIdentifier": "is.workflow.actions.output",
    "WFWorkflowActionParameters": {
        "WFOutput": make_attachment(result_uuid, "Previous Action"),
    },
}
```

**Variable wiring example:**

```python
# Full pipeline: clipboard → summarize → output to stdout
clipboard_uuid = new_uuid()
summary_uuid = new_uuid()

actions = [
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.getclipboard",
        "WFWorkflowActionParameters": {"UUID": clipboard_uuid},
    },
    {
        "WFWorkflowActionIdentifier":
            "com.apple.WritingTools.WritingToolsAppIntentsExtension.SummarizeTextIntent",
        "WFWorkflowActionParameters": {
            "text": make_attachment(clipboard_uuid, "Clipboard"),
            "summaryType": "summarize",
            "UUID": summary_uuid,
        },
    },
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.output",
        "WFWorkflowActionParameters": {
            "WFOutput": make_attachment(summary_uuid, "Summarize Text"),
        },
    },
]
```

---

## Build & Sign Workflow

Follow these steps for every shortcut:

1. Define the shortcut's purpose and I/O contract
2. Copy `resources/builder_template.py`
3. Assemble actions from the catalog into the `actions` list
4. Run the script to produce `unsigned.shortcut`
5. Validate with `plutil -lint unsigned.shortcut`
6. Debug with `plutil -convert xml1 -o debug.xml unsigned.shortcut` (if needed)
7. Sign with `shortcuts sign -m anyone -i unsigned.shortcut -o signed.shortcut`
8. Import with `open signed.shortcut` (user confirms import dialog)
9. Test with `shortcuts run <name> --input-path - --output-path -`
10. Iterate on steps 3–9 until correct
11. Copy `resources/plugin_template/`, fill in SKILL.md with I/O contract
12. Publish

---

## Debugging & Troubleshooting

### Validation Steps

1. `plutil -lint unsigned.shortcut` — catches malformed plists
2. `plutil -convert xml1 -o debug.xml unsigned.shortcut` — human-readable XML
3. If `shortcuts sign` fails — check stderr for cause
4. `open signed.shortcut` — test import dialog appears
5. `echo "test" | shortcuts run "Name" --input-path - --output-path - 2>&1` — test execution

### Common Failure Modes

| Symptom | Cause | Fix |
|---------|-------|-----|
| `shortcuts sign` exits non-zero | Malformed plist | Run `plutil -lint` and fix structure |
| Import dialog shows but shortcut is empty | `WFWorkflowActions` is empty/malformed | Inspect XML, check action dicts |
| Shortcut runs but produces no output | Missing `UUID` on output-producing actions | Add `UUID` key |
| Variable shows as blank | `OutputUUID` doesn't match producing action's `UUID` | Verify UUID strings match exactly |
| Control flow doesn't group correctly | Mismatched `GroupingIdentifier` | All actions in a block must share the same GID |
| Apple Intelligence action fails | AI not enabled or wrong identifier | Check System Settings and identifier |
| `shortcuts sign` prints ObjC warnings/crash trace to stderr | macOS 26 beta runtime warnings | Check exit code, not stderr — signing succeeds if exit code is 0 |

### Limitations

- No automated import (confirmation dialog required)
- No programmatic uninstall
- Signing requires network for `-m anyone`

---

## Plugin Packaging

### Directory Structure

Published plugin directories follow this layout:

```
my-shortcut-plugin/
├── SKILL.md                    # I/O contract, usage docs
├── shortcuts/
│   └── my-shortcut.shortcut    # Signed .shortcut file
├── scripts/
│   ├── install.sh              # Imports via `open`
│   └── uninstall.sh            # Best-effort removal guidance
└── src/
    └── build.py                # Builder script (for transparency)
```

See `resources/plugin_template/` for skeleton templates.

### I/O Contract Schema

Each plugin's SKILL.md must include a contract block:

```yaml
shortcut:
  name: "My Shortcut"
  input: stdin/text
  output: stdout/text
  requires:
    macos: "26"
    apple-intelligence: true
  permissions:
    - clipboard-read
    - notifications
```

### Allowed `input` Values

| Value | Meaning | CLI invocation |
|-------|---------|----------------|
| `stdin/text` | Accepts text via stdin | `echo "..." \| shortcuts run "Name" --input-path -` |
| `stdin/file` | Accepts file data via stdin | `cat file.pdf \| shortcuts run "Name" --input-path -` |
| `file-path` | Accepts a file path as text input | `echo "/path/to/file" \| shortcuts run "Name" --input-path -` |
| `clipboard` | Reads from system clipboard | `shortcuts run "Name"` |
| `none` | No input required | `shortcuts run "Name"` |

### Allowed `output` Values

| Value | Meaning | CLI invocation |
|-------|---------|----------------|
| `stdout/text` | Outputs text to stdout | `shortcuts run "Name" --output-path -` |
| `stdout/file` | Outputs file data to stdout | `shortcuts run "Name" --output-path - --output-type public.png` |
| `file-path` | Writes to a file, outputs path | `shortcuts run "Name" --output-path -` |
| `clipboard` | Sets system clipboard | `shortcuts run "Name"` |
| `notification` | Shows a notification | `shortcuts run "Name"` |
| `none` | No output (side-effect only) | `shortcuts run "Name"` |

### Allowed `permissions` Values

`clipboard-read`, `clipboard-write`, `notifications`, `screenshots`, `file-read`, `file-write`, `calendar-read`, `calendar-write`, `reminders-read`, `reminders-write`, `mail-send`, `location`, `network`

---

## Commenting Requirements

Shortcuts must be **thoroughly commented**. Users can inspect shortcuts when choosing whether to install them.

Requirements:

1. **Header comment** — First action: what it does, I/O, requirements
2. **Section comments** — Before each logical group
3. **Control flow comments** — Explain branching logic
4. **Variable comments** — Explain non-obvious variables
5. **Integration comments** — Note permissions for app-specific/AI actions

Use the `make_comment()` helper (defined in `resources/builder_template.py`) to insert comment actions.

---

## External References

### Apple Official

- [Shortcuts User Guide for Mac](https://support.apple.com/guide/shortcuts-mac/welcome/mac)
- [Use Apple Intelligence in Shortcuts](https://support.apple.com/guide/mac-help/use-apple-intelligence-in-shortcuts-mchl91750563/mac)
- [What's new in Shortcuts for macOS 26](https://support.apple.com/en-us/125148)
- [Run shortcuts from the command line](https://support.apple.com/guide/shortcuts-mac/run-shortcuts-from-the-command-line-apd455c82f02/mac)

### Community Format Documentation

- [Zachary7829's Shortcuts File Format](https://zachary7829.github.io/blog/shortcuts/fileformat)
- [Cherri File Format](https://cherrilang.org/compiler/file-format.html)
- [iOS-Shortcuts-Reference (GitHub)](https://github.com/sebj/iOS-Shortcuts-Reference)
- [0xdevalias decompilation notes](https://gist.github.com/0xdevalias/27d9aea9529be7b6ce59055332a94477)

### Tools & Projects (Reference Only)

- [Cherri](https://github.com/electrikmilk/cherri) — Go-based shortcuts compiler
- [shortcuts-js](https://github.com/joshfarrant/shortcuts-js) — Node.js shortcuts builder
- Python `plistlib` — [stdlib docs](https://docs.python.org/3/library/plistlib.html)

### Apple Intelligence Coverage

- [9to5Mac: 25+ new Shortcuts actions in iOS 26](https://9to5mac.com/2025/12/09/ios-26s-shortcuts-app-adds-25-new-actions-heres-everything-new/)
- [MacObserver: All 25+ new actions](https://www.macobserver.com/news/all-25-new-shortcuts-actions-introduced-in-ios-26-heres-everything-you-can-do/)
