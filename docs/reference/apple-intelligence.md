# Apple Intelligence Actions Reference

Complete reference for Apple Intelligence and Writing Tools actions in macOS Shortcuts.

**Source frameworks:**
- `WorkflowKit` — hosts `is.workflow.actions.askllm`
- `ContentKit` — `WFGenerativeModelName` enum, `WFGeneratedOutputType` enum, model classes
- `WritingToolsAppIntentsExtension` — all 6 Writing Tools actions

---

## is.workflow.actions.askllm (Use Model)

The primary Apple Intelligence action. UI name: "Use Model".

### Parameters

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `WFLLMPrompt` | String or WFTextTokenString | Yes | The prompt text. Plain string for static, WFTextTokenString for dynamic with variables. |
| `WFLLMModel` | String | No | Model selection. Omit for automatic. |
| `WFGenerativeResultType` | String | No | Output type. Omit for automatic. |
| `FollowUp` | Boolean | No | When `true`, shows response inline and allows follow-up queries before passing to next action. Eliminates need for `showresult`. |
| `UUID` | String | Yes | Action UUID for output referencing. |

Output name in subsequent references: `"Response"`.

### WFLLMModel Values

| Plist Value | Model Class | Description |
|-------------|-------------|-------------|
| `"Apple Intelligence"` | `WFAFMInstructServerV1Model` | Private Cloud Compute — large server model, privacy-preserving |
| *(absent)* | (automatic) | Runtime selects appropriate model |
| *(suspected: on-device string)* | `WFAFMDevice3BModel` | On-device model — no network required, simpler tasks |
| *(suspected: chatgpt string)* | `WFChatGPTModel` | ChatGPT extension — requires ChatGPT integration |

### WFGenerativeResultType Values

| Plist Value | Enum Case | Description |
|-------------|-----------|-------------|
| `"Automatic"` | `.automatic` | Default. Runtime infers type from context. |
| `"Text"` | `.text` | Plain text string |
| `"List"` | `.list` | Ordered list of items |
| `"Dictionary"` | `.dictionary` | Key-value dictionary |
| `"Number"` | `.number` | Numeric value |
| `"Boolean"` | `.boolean` | True/False |
| `"Date"` | `.date` | Date value |
| `"textOrEntities"` | `.textOrEntities` | Text or structured entities |

### Minimal Example — Static Prompt

```json
{
    "WFWorkflowActionIdentifier": "is.workflow.actions.askllm",
    "WFWorkflowActionParameters": {
        "UUID": "B068AF27-3FD8-4FAF-85BB-9FB8E792D4A5",
        "WFGenerativeResultType": "Dictionary",
        "WFLLMModel": "Apple Intelligence",
        "WFLLMPrompt": "List every planet and its diameter. Keys = planet name, values = diameter in km."
    }
}
```

### Dynamic Prompt with Variables

```json
{
    "WFWorkflowActionIdentifier": "is.workflow.actions.askllm",
    "WFWorkflowActionParameters": {
        "UUID": "7FCB58C0-...",
        "WFLLMModel": "Apple Intelligence",
        "WFLLMPrompt": {
            "Value": {
                "string": "Summarize today's weather: \uFFFC",
                "attachmentsByRange": {
                    "{30, 1}": {
                        "OutputName": "Weather Conditions",
                        "OutputUUID": "70BFB126-...",
                        "Type": "ActionOutput"
                    }
                }
            },
            "WFSerializationType": "WFTextTokenString"
        }
    }
}
```

### FollowUp Mode (Interactive)

When `FollowUp: true`, the shortcut shows the model's response and lets the user ask follow-up questions. No `showresult` action needed.

```json
{
    "WFWorkflowActionIdentifier": "is.workflow.actions.askllm",
    "WFWorkflowActionParameters": {
        "UUID": "B54B3DDD-...",
        "FollowUp": true,
        "WFGenerativeResultType": "Automatic",
        "WFLLMModel": "Apple Intelligence",
        "WFLLMPrompt": { "...WFTextTokenString..." }
    }
}
```

### List Output → Repeat with Each

Common pattern: askllm with `"List"` output → `repeat.each` over the results.

```
askllm (List) → repeat.each (input = Response) → per-item action using "Repeat Item"
```

### Dictionary Output → Get Value for Key

```
askllm (Dictionary) → getvalueforkey (WFDictionaryKey = "Earth") → showresult
```

---

## Writing Tools Actions

All 6 Writing Tools are App Intents in `WritingToolsAppIntentsExtension.appex`.

### Action Identifiers

| Identifier | UI Name | Description |
|------------|---------|-------------|
| `com.apple.WritingTools.WritingToolsAppIntentsExtension.SummarizeTextIntent` | Summarize Text | Generate summary or key points |
| `com.apple.WritingTools.WritingToolsAppIntentsExtension.ProofreadIntent` | Proofread | Fix grammar and spelling |
| `com.apple.WritingTools.WritingToolsAppIntentsExtension.RewriteTextIntent` | Rewrite Text | Rewrite the text |
| `com.apple.WritingTools.WritingToolsAppIntentsExtension.AdjustToneIntent` | Adjust Tone | Change tone (friendly/professional/concise) |
| `com.apple.WritingTools.WritingToolsAppIntentsExtension.FormatListIntent` | Format as List | Organize text as a list |
| `com.apple.WritingTools.WritingToolsAppIntentsExtension.FormatTableIntent` | Format as Table | Organize text as a table |

### SummarizeTextIntent Parameters

| Parameter | Type | Values |
|-----------|------|--------|
| `text` | WFTextTokenString | Input text |
| `summaryType` | String | `"summarize"` or `"createKeyPoints"` |

Output name: `"Summarize Text"`

### AdjustToneIntent Parameters

| Parameter | Type | Values |
|-----------|------|--------|
| `text` | WFTextTokenString | Input text |
| `tone` | String | `"friendly"`, `"professional"`, `"concise"` |

### ProofreadIntent, RewriteTextIntent, FormatListIntent, FormatTableIntent

Single parameter: `text` (WFTextTokenString).

### Writing Tools Example — Summarize PDF

```json
{
    "WFWorkflowActionIdentifier": "com.apple.WritingTools.WritingToolsAppIntentsExtension.SummarizeTextIntent",
    "WFWorkflowActionParameters": {
        "UUID": "09B5964F-...",
        "summaryType": "createKeyPoints",
        "text": {
            "Value": {
                "string": "\uFFFC",
                "attachmentsByRange": {
                    "{0, 1}": {
                        "OutputName": "Text",
                        "OutputUUID": "A42AE8FE-...",
                        "Type": "ActionOutput"
                    }
                }
            },
            "WFSerializationType": "WFTextTokenString"
        }
    }
}
```

---

## Common AI Pipelines

### Clipboard → Summarize → Notify

```
getclipboard → SummarizeTextIntent → notification
```

### Extension Input → Proofread → Output

```
ExtensionInput → ProofreadIntent → showresult
```

### Weather + Calendar + Reminders → Morning Report

```
weather.currentconditions → filter.calendarevents → filter.reminders → askllm (FollowUp: true)
```

### Meeting Notes → Action Items → Reminders

```
ask → filter.notes → askllm (List) → repeat.each → addnewreminder
```

### Document Comparison

```
repeat.count(2) { choosefrommenu → file/url } → askllm (compare)
```
