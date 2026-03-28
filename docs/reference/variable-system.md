# Shortcuts Variable System Reference

How variables, outputs, and data flow work in the Shortcuts plist format.

---

## Variable Token Types

Every variable reference uses `WFSerializationType` to declare its encoding.

### WFTextTokenAttachment (Single Reference)

References a single variable or action output. Used when a parameter takes exactly one value.

```json
{
    "Value": {
        "Type": "ActionOutput",
        "OutputUUID": "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX",
        "OutputName": "Clipboard"
    },
    "WFSerializationType": "WFTextTokenAttachment"
}
```

### WFTextTokenString (Text with Embedded Variables)

Embeds one or more variable tokens inside a text string. Each variable occupies a single `\uFFFC` (U+FFFC Object Replacement Character) in the string, with position tracked in `attachmentsByRange`.

```json
{
    "Value": {
        "string": "Hello \uFFFC, today is \uFFFC",
        "attachmentsByRange": {
            "{6, 1}": {
                "Type": "ActionOutput",
                "OutputUUID": "AAA-...",
                "OutputName": "Name"
            },
            "{18, 1}": {
                "Type": "CurrentDate"
            }
        }
    },
    "WFSerializationType": "WFTextTokenString"
}
```

**Position calculation:** `{offset, 1}` where offset = number of UTF-16 code units before the `\uFFFC`. For ASCII/BMP text, `len(text_before)` works. For emoji/non-BMP characters, use `len(text.encode('utf-16-le')) // 2`.

---

## Token Type Values

The `Type` field in a token attachment:

| Type | Description | Required Fields |
|------|-------------|-----------------|
| `ActionOutput` | Output of a specific previous action | `OutputUUID`, `OutputName` |
| `Variable` | Named variable (from setvariable/appendvariable) | `VariableName` |
| `ExtensionInput` | Share Sheet / Action Extension input | (none) |
| `CurrentDate` | Current date/time at runtime | (none) |
| `Clipboard` | Current clipboard contents | (none) |
| `Ask` | Prompt user for input at runtime | (none) |

### ActionOutput Example

```json
{
    "Type": "ActionOutput",
    "OutputUUID": "74B94EAB-1234-5678-9ABC-DEF012345678",
    "OutputName": "Wi-Fi Name"
}
```

### Named Variable Example

```json
{
    "Type": "Variable",
    "VariableName": "Repeat Item"
}
```

### ExtensionInput Example

```json
{
    "Type": "ExtensionInput"
}
```

### Ask (Runtime Prompt) Example

Used in `is.workflow.actions.file` and `is.workflow.actions.url`:

```json
{
    "Value": { "Type": "Ask" },
    "WFSerializationType": "WFTextTokenAttachment"
}
```

---

## Aggrandizements

Aggrandizements transform a variable's value — extract a property, format a date, or coerce to a type. They appear as an `Aggrandizements` array on the token.

### WFPropertyVariableAggrandizement

Extract a property from an object.

```json
{
    "Type": "ActionOutput",
    "OutputUUID": "...",
    "OutputName": "Current Song",
    "Aggrandizements": [{
        "Type": "WFPropertyVariableAggrandizement",
        "PropertyName": "Album",
        "PropertyUserInfo": "albumTitle"
    }]
}
```

`PropertyUserInfo` can be a string (e.g., `"albumTitle"`) or a dict with `WFLinkEntityContentPropertyUserInfoPropertyIdentifier` (e.g., `"creationDate"` for Notes).

### WFDateFormatVariableAggrandizement

Format a date value.

```json
{
    "Type": "ActionOutput",
    "OutputUUID": "...",
    "OutputName": "Start Date",
    "Aggrandizements": [{
        "Type": "WFDateFormatVariableAggrandizement",
        "WFDateFormatStyle": "Medium",
        "WFTimeFormatStyle": "None"
    }]
}
```

**Style values:** `"None"`, `"Short"`, `"Medium"`, `"Long"`, `"Full"`, `"ISO 8601"`, `"RFC 2822"`

**Pattern:** Same `OutputUUID` can be referenced multiple times with different aggrandizements — e.g., once for date-only, once for time-only.

### WFCoercionVariableAggrandizement

Type-coerce a value to a specific content item class.

```json
{
    "Aggrandizements": [{
        "Type": "WFCoercionVariableAggrandizement",
        "CoercionItemClass": "WFDictionaryContentItem"
    }]
}
```

Common coercion targets: `WFDictionaryContentItem`, `WFStringContentItem`, `WFNumberContentItem`, `WFBooleanContentItem`, `WFImageContentItem`, `WFURLContentItem`

---

## Named Variables

### Set Variable

```json
{
    "WFWorkflowActionIdentifier": "is.workflow.actions.setvariable",
    "WFWorkflowActionParameters": {
        "WFVariableName": "My Data",
        "WFInput": { "...WFTextTokenAttachment..." }
    }
}
```

### Append to Variable

Accumulates values into a list variable.

```json
{
    "WFWorkflowActionIdentifier": "is.workflow.actions.appendvariable",
    "WFWorkflowActionParameters": {
        "WFVariableName": "Collected Items",
        "WFInput": { "...WFTextTokenAttachment..." }
    }
}
```

### Get Variable

```json
{
    "WFWorkflowActionIdentifier": "is.workflow.actions.getvariable",
    "WFWorkflowActionParameters": {
        "WFVariable": {
            "Value": { "Type": "Variable", "VariableName": "My Data" },
            "WFSerializationType": "WFTextTokenAttachment"
        }
    }
}
```

---

## Magic Variables

These are special variable names that reference loop/control flow state:

| Variable Name | Available In | Contains |
|---------------|-------------|----------|
| `Repeat Item` | Repeat with Each body | Current iteration item |
| `Repeat Index` | Repeat Count body | Current iteration number (1-based) |
| `Repeat Results` | After Repeat block | Collected outputs from loop |
| `Menu Result` | After Choose from Menu | Selected menu item value |
| `ShortcutInput` | Top-level | Input passed to the shortcut |

---

## Implicit Pipeline

Actions that don't specify explicit input automatically receive the output of the previous action. This is the "pipeline" model.

**Example:** `speaktext` with no parameters speaks the output of the preceding `gettext`:

```json
[
    {"WFWorkflowActionIdentifier": "is.workflow.actions.gettext", "WFWorkflowActionParameters": {"WFTextActionText": "Hello"}},
    {"WFWorkflowActionIdentifier": "is.workflow.actions.speaktext", "WFWorkflowActionParameters": {}}
]
```

To explicitly reference a specific action's output (breaking the pipeline), use `WFInput` or the action's specific input parameter with a `WFTextTokenAttachment`.

---

## Multi-Token Strings — Real Examples

### Wi-Fi QR Code String

```json
"string": "WIFI:S:\uFFFC;T:WPA;P:\uFFFC;;",
"attachmentsByRange": {
    "{7, 1}": { "OutputName": "SSID", "OutputUUID": "...", "Type": "ActionOutput" },
    "{17, 1}": { "OutputName": "Password", "OutputUUID": "...", "Type": "ActionOutput" }
}
```

### Morning Report Prompt (3 variables at end)

```json
"string": "...summarize my day based on this info...\n\n\uFFFC\n\uFFFC\n\uFFFC",
"attachmentsByRange": {
    "{354, 1}": { "OutputName": "Weather Conditions", ... },
    "{356, 1}": { "OutputName": "Calendar Events", ... },
    "{358, 1}": { "OutputName": "Reminders", ... }
}
```

### JavaScript with Injected Variable

```json
"string": "var videos = document.querySelectorAll(\"video\");\nfor (var video of videos) {\n    video.playbackRate = \uFFFC;\n}\ncompletion(videos.length);",
"attachmentsByRange": {
    "{102, 1}": { "OutputName": "Speed", "OutputUUID": "...", "Type": "ActionOutput" }
}
```

### Date Formatting — Same UUID, Different Aggrandizements

```json
"attachmentsByRange": {
    "{7, 1}": {
        "OutputName": "Start Date", "OutputUUID": "SAME-UUID",
        "Aggrandizements": [{"Type": "WFDateFormatVariableAggrandizement", "WFDateFormatStyle": "Medium", "WFTimeFormatStyle": "None"}]
    },
    "{35, 1}": {
        "OutputName": "Start Date", "OutputUUID": "SAME-UUID",
        "Aggrandizements": [{"Type": "WFDateFormatVariableAggrandizement", "WFDateFormatStyle": "None", "WFTimeFormatStyle": "Short"}]
    }
}
```
