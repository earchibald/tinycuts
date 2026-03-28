# Batch 3 Shortcut Analysis

Analysis of shortcuts (3 gallery downloads + 7 Apple Intelligence built-in shortcuts), March 2026.

**Source discovery:** The vanity URLs (`icloud.com/shortcuts/getstartedwithmodels`, etc.) are not resolvable via the web API — they are iOS deep links that open the Shortcuts app directly. The actual shortcut files are bundled inside `WorkflowKit.framework` on macOS:

```
/System/Library/PrivateFrameworks/WorkflowKit.framework/Versions/A/Resources/Gallery.bundle/Contents/Resources/
```

Files: `ActionItems.wflow`, `DocumentReview.wflow`, `GetStartedWithModels.wflow`, `Haiku.wflow`, `LeftoverRecipes.wflow`, `MorningReport.wflow`, `SummarizePDF.wflow`

The gallery index is at `Gallery.bundle/Contents/Resources/gallery.plist`:
```xml
<key>collections</key>
<array>
  <dict>
    <key>id</key>
    <string>UseModel</string>
    <key>shortcuts</key>
    <array>
      <string>GetStartedWithModels</string>
      <string>MorningReport</string>
      <string>Haiku</string>
      <string>ActionItems</string>
      <string>LeftoverRecipes</string>
      <string>SummarizePDF</string>
      <string>DocumentReview</string>
    </array>
  </dict>
</array>
```

Collection display name (from `gallery.loctable`): `"Apple Intelligence"`.

---

## Apple Intelligence Action Identifiers

### `is.workflow.actions.askllm`

The primary Apple Intelligence action. Action name in the UI: **"Use Model"** (from `'Use Model (Action Name)'` in WorkflowKit `Localizable.loctable`). Description: `"Use a model to handle complex requests in your shortcuts."`

**Parameter summary string:** `"Use ${WFLLMModel}"` and `"Use ${WFLLMModel} model"` (from loctable).

#### Parameters

| Parameter key | Type | Values / Notes |
|---|---|---|
| `WFLLMPrompt` | WFTextTokenString or plain String | The prompt/request text. Supports variable token attachments. |
| `WFLLMModel` | String (enum raw value) | Model selection — see values below. Optional; omitting uses a default (automatic). |
| `WFGenerativeResultType` | String (enum raw value) | Output type — see values below. Optional; omitting = Automatic. |
| `FollowUp` | Boolean | When `true`, shows model response before passing to next action, allowing follow-up queries. Described as: "Show the model's response and make additional requests before the final response is passed to the next action." |
| `UUID` | String | Action UUID for output reference. |

#### `WFLLMModel` values

The model parameter key is internally labeled `"Model (WFAskLLM)"` → display: `"Model"`.

Sourced from `ContentKit.WFGenerativeModelName` enum (Swift enum with String raw values, in `ContentKit.framework`):

| Plist string value | WFGenerativeModelName case | Model class | Display name |
|---|---|---|---|
| `"Apple Intelligence"` | `.afm` | `WFAFMInstructServerV1Model` | Private Cloud Compute |
| *(not yet confirmed string)* | `.afmOnDevice` | `WFAFMDevice3BModel` | On-Device |
| *(not yet confirmed string)* | `.chatgpt` | `WFChatGPTModel` | ChatGPT (Extension) |

Observed in gallery shortcuts: `WFLLMModel: "Apple Intelligence"`. When `WFLLMModel` is absent (e.g., in DocumentReview), the runtime selects a model automatically.

From WorkflowKit loctable help text:
> **Private Cloud Compute Model** — Use a large server-based model on Private Cloud Compute to handle complex requests while protecting your privacy.
>
> **On-Device Model** — Use the on-device model to handle simple requests without the need for a network connection.

#### `WFGenerativeResultType` values

The output-type parameter is internally labeled `"Output (WFGenerativeResultType)"` → display: `"Output"`.

Sourced from `ContentKit.WFGeneratedOutputType` enum:

| Plist string value | Enum case | Notes |
|---|---|---|
| `"Automatic"` | `.automatic` | Default when parameter is absent. Response type inferred from context (e.g. if piped into Repeat with Each → list). |
| `"Text"` | `.text` | Plain text string. |
| `"List"` | `.list` | Ordered list of items. |
| `"Dictionary"` | `.dictionary` | Key-value dictionary. |
| `"Number"` | `.number` | Numeric value. |
| `"Boolean"` | `.boolean` | True/False. |
| `"Date"` | `.date` | Date value. |
| `"textOrEntities"` | `.textOrEntities` | Text or structured entities. |
| (entity list) | `.entityList(String)` | Entity list parameterized by type name — not yet observed in gallery shortcuts. |

### `com.apple.WritingTools.WritingToolsAppIntentsExtension.SummarizeTextIntent`

A Writing Tools action. Implemented in:
```
/System/Library/ExtensionKit/Extensions/WritingToolsAppIntentsExtension.appex
```

#### All 6 Writing Tools AppIntents

| Full identifier | Description |
|---|---|
| `com.apple.WritingTools.WritingToolsAppIntentsExtension.SummarizeTextIntent` | Generates a summary of the provided text using Apple Intelligence. |
| `com.apple.WritingTools.WritingToolsAppIntentsExtension.ProofreadIntent` | Corrects grammatical and spelling errors. |
| `com.apple.WritingTools.WritingToolsAppIntentsExtension.RewriteTextIntent` | Rewrites the provided text. |
| `com.apple.WritingTools.WritingToolsAppIntentsExtension.AdjustToneIntent` | Adjusts the tone of the provided text. |
| `com.apple.WritingTools.WritingToolsAppIntentsExtension.FormatListIntent` | Organizes the provided text in a list. |
| `com.apple.WritingTools.WritingToolsAppIntentsExtension.FormatTableIntent` | Organizes the provided text in a table. |

#### SummarizeTextIntent parameters

| Parameter | Type | Values |
|---|---|---|
| `text` | WFTextTokenString | Input text to summarize. |
| `summaryType` | String (enum raw value) | `"summarize"` (Summarize) or `"createKeyPoints"` (Create Key Points) — from `WritingToolsAppIntentsExtension.SummaryIntentMode` enum. |

Output name: `"Summarize Text"`.

#### AdjustToneIntent parameters

| Parameter | Type | Values |
|---|---|---|
| `text` | WFTextTokenString | Input text. |
| `tone` | String (enum raw value) | `"friendly"` / `"professional"` / `"concise"` — from `WritingToolsAppIntentsExtension.IntentTone` enum. |

#### ProofreadIntent, RewriteTextIntent, FormatListIntent, FormatTableIntent

Single parameter: `text` (WFTextTokenString).

---

## Shortcuts

### 1. Clear Out Photos

- **Source:** `https://www.icloud.com/shortcuts/514b39e7ddb949e89145ca0df224924a`
- **Client version:** 1142 | **Min version:** 900 (string: `"900"`)
- **Types:** (not set)
- **Input:** all content item classes
- **Actions (15 total, 9 unique):**

```
is.workflow.actions.selectphoto
is.workflow.actions.setvariable
is.workflow.actions.count
is.workflow.actions.getvariable
is.workflow.actions.choosefrommenu
is.workflow.actions.image.combine
is.workflow.actions.previewdocument
is.workflow.actions.alert
is.workflow.actions.deletephotos
```

**Notable patterns:**

`selectphoto` with multi-select:
```json
"WFSelectMultiplePhotos": true
```

`count` on an item list:
```json
"WFCountType": "Items",
"Input": { "Value": { "Type": "Variable", "VariableName": "Photos" }, "WFSerializationType": "WFTextTokenAttachment" }
```

`image.combine` in grid mode:
```json
"WFImageCombineMode": "In a Grid",
"WFImageCombineSpacing": 5,
"WFInput": { ... Variable "Photos" ... }
```

`choosefrommenu` prompt referencing a count variable:
```json
"WFMenuPrompt": {
  "Value": {
    "attachmentsByRange": {
      "{27, 1}": { "Type": "Variable", "VariableName": "Count", ... }
    },
    "string": "Do you want to delete \uFFFC photo(s)?"
  },
  "WFSerializationType": "WFTextTokenString"
},
"WFMenuItems": ["Yes", "No"]
```

`deletephotos` — takes action output (from menu result, which contains the selected photos):
```json
"photos": { "Value": { "OutputName": "Menu Result", "OutputUUID": "CAE572DE-...", "Type": "ActionOutput" }, "WFSerializationType": "WFTextTokenAttachment" }
```

Alert without cancel button, confirming success:
```json
"WFAlertActionCancelButtonShown": false,
"WFAlertActionMessage": "Your image(s) were successfully deleted!"
```

---

### 2. Clean Up Screenshots

- **Source:** `https://www.icloud.com/shortcuts/c4cb5cce55eb4873a5d1dfb861ddf4aa`
- **Client version:** 1142 | **Min version:** 1106 (string: `"1106"`)
- **Types:** (not set)
- **Input:** all content item classes
- **Actions (14 total, 11 unique):**

```
is.workflow.actions.filter.photos
is.workflow.actions.choosefromlist
is.workflow.actions.setvariable
is.workflow.actions.choosefrommenu
is.workflow.actions.date
is.workflow.actions.format.date
is.workflow.actions.makezip
is.workflow.actions.documentpicker.save
is.workflow.actions.deletephotos
is.workflow.actions.count
is.workflow.actions.alert
```

**Notable patterns:**

`filter.photos` filtering for screenshots:
```json
"WFContentItemFilter": {
  "Value": {
    "WFActionParameterFilterPrefix": 1,
    "WFActionParameterFilterTemplates": [{
      "Operator": 4,
      "Property": "Is a Screenshot",
      "Values": { "Bool": true }
    }],
    "WFContentPredicateBoundedDate": false
  },
  "WFSerializationType": "WFContentPredicateTableTemplate"
},
"WFContentItemSortOrder": "Latest First",
"WFContentItemSortProperty": "Creation Date"
```

`choosefromlist` with multi-select prompt:
```json
"WFChooseFromListActionPrompt": "Choose the screenshots",
"WFChooseFromListActionSelectMultiple": true
```

`format.date` with ISO 8601:
```json
"WFDateFormatStyle": "ISO 8601",
"WFDate": { ... WFTextTokenString with Date action output ... }
```

`makezip` with tokenized filename:
```json
"WFZIPName": {
  "Value": {
    "attachmentsByRange": {
      "{12, 1}": { "OutputName": "Formatted Date", "OutputUUID": "B6B1D022-...", "Type": "ActionOutput" }
    },
    "string": "Screenshots \uFFFC"
  },
  "WFSerializationType": "WFTextTokenString"
}
```

`documentpicker.save` with ask-where-to-save:
```json
"WFAskWhereToSave": true
```

`count` with a variable as both input and count type (unusual pattern — type appears to be the variable itself):
```json
"Input": { "Value": { "Type": "Variable", "VariableName": "Screenshots", "VariableUUID": "..." }, ... },
"WFCountType": { "Value": { "Type": "Variable", "VariableName": "Screenshots", "VariableUUID": "..." }, ... }
```
(This is likely a UI artifact — `WFCountType` should normally be `"Items"` but here references a variable, possibly a display-only quirk.)

---

### 3. Convert Burst to GIF

- **Source:** `https://www.icloud.com/shortcuts/60a3411b37204842baf5ca0696fb3aed`
- **Client version:** 485 (release not specified) | **Min version:** (not set)
- **Extra top-level key:** `WFWorkflowHiddenInComplication: false`
- **Types:** (not set, `WFWorkflowTypes` absent)
- **Input:** all content item classes
- **Actions (10 total, 7 unique):**

```
is.workflow.actions.filter.photos
is.workflow.actions.choosefromlist
is.workflow.actions.makegif
is.workflow.actions.previewdocument
is.workflow.actions.choosefrommenu
is.workflow.actions.share
is.workflow.actions.savetocameraroll
```

**Notable patterns:**

`filter.photos` filtering for burst photos:
```json
"WFContentItemFilter": {
  "Value": {
    "WFActionParameterFilterPrefix": 1,
    "WFActionParameterFilterTemplates": [{
      "Enumeration": "Burst",
      "Operator": 4,
      "Property": "Media Type"
    }]
  }
},
"WFContentItemSortOrder": "Latest First",
"WFContentItemSortProperty": "Time Taken"
```

`makegif` with delay time:
```json
"WFMakeGIFActionDelayTime": 0.1
```

`share` — no parameters, shares the implicit pipeline output (the GIF).

`savetocameraroll` — no parameters, saves to Camera Roll.

---

### 4. Get Started with Models *(Apple Intelligence gallery)*

- **Source:** `WorkflowKit Gallery.bundle/GetStartedWithModels.wflow`
- **Vanity URL:** `https://www.icloud.com/shortcuts/getstartedwithmodels`
- **Client version:** 9999 | **Min version:** 900
- **Extra top-level key:** `WFQuickActionSurfaces: []`
- **Types:** (not set)
- **Description:** "Learn how you can use models to power up your shortcuts."
- **Actions (13 total, 6 unique):**

```
is.workflow.actions.comment
is.workflow.actions.weather.currentconditions
is.workflow.actions.askllm
is.workflow.actions.showresult
is.workflow.actions.list
is.workflow.actions.getvalueforkey
```

**Three demonstration blocks (separated by comment actions):**

#### Block 1: Weather summary (text output)
```json
{
  "WFWorkflowActionIdentifier": "is.workflow.actions.askllm",
  "WFWorkflowActionParameters": {
    "UUID": "7FCB58C0-40A0-4226-8E80-C28D2C85A664",
    "WFLLMModel": "Apple Intelligence",
    "WFLLMPrompt": {
      "Value": {
        "attachmentsByRange": {
          "{52, 1}": {
            "OutputName": "Weather Conditions",
            "OutputUUID": "70BFB126-1E9B-409B-BB29-10258A03E6AE",
            "Type": "ActionOutput"
          }
        },
        "string": "Write me a concise, fun summary of today's weather: \uFFFC"
      },
      "WFSerializationType": "WFTextTokenString"
    }
  }
}
```
No `WFGenerativeResultType` → defaults to Automatic.

Output referenced as `"Response"` in subsequent `showresult`.

#### Block 2: List filtering/sorting
```json
{
  "WFWorkflowActionIdentifier": "is.workflow.actions.askllm",
  "WFWorkflowActionParameters": {
    "UUID": "2A985A84-EDBE-4129-8B9A-0E025C7356ED",
    "WFGenerativeResultType": "List",
    "WFLLMPrompt": {
      "Value": {
        "attachmentsByRange": {
          "{87, 1}": {
            "OutputName": "Fruits",
            "OutputUUID": "E7D3F4DE-1DDF-4382-B883-B72D3EFC81C7",
            "Type": "ActionOutput"
          }
        },
        "string": "Sort these fruits from largest to smallest, and remove any items that are not fruits.\n\n\uFFFC"
      },
      "WFSerializationType": "WFTextTokenString"
    }
  }
}
```
Note: no `WFLLMModel` — uses runtime default.

#### Block 3: Dictionary output with key extraction
```json
{
  "WFWorkflowActionIdentifier": "is.workflow.actions.askllm",
  "WFWorkflowActionParameters": {
    "UUID": "B068AF27-3FD8-4FAF-85BB-9FB8E792D4A5",
    "WFGenerativeResultType": "Dictionary",
    "WFLLMModel": "Apple Intelligence",
    "WFLLMPrompt": "List every planet in the solar system and its diameter. The keys should be the planet name and the values should be the corresponding diameter in kilometers."
  }
}
```
Followed by `getvalueforkey` with `WFDictionaryKey: "Earth"`, and `showresult` displaying `"The diameter of Earth is \uFFFC km"`.

**Variable wiring note:** `WFLLMPrompt` can be either a plain `String` value (static prompt, no attachments) or a `WFTextTokenString` dict (dynamic prompt with variable tokens).

---

### 5. Morning Summary *(Apple Intelligence gallery)*

- **Source:** `WorkflowKit Gallery.bundle/MorningReport.wflow`
- **Vanity URL:** `https://www.icloud.com/shortcuts/morningreport`
- **Client version:** 9999 | **Min version:** 900
- **Extra top-level key:** `WFQuickActionSurfaces: []`
- **Description:** "Summarize the weather, reminders, and events for the day."
- **Actions (5 total, 4 unique):**

```
is.workflow.actions.weather.currentconditions
is.workflow.actions.filter.calendarevents
is.workflow.actions.filter.reminders
is.workflow.actions.askllm
```

**Full askllm action:**
```json
{
  "WFWorkflowActionIdentifier": "is.workflow.actions.askllm",
  "WFWorkflowActionParameters": {
    "UUID": "B54B3DDD-D631-4AA9-A9E0-3395F0FD9E55",
    "FollowUp": true,
    "WFGenerativeResultType": "Automatic",
    "WFLLMModel": "Apple Intelligence",
    "WFLLMPrompt": {
      "Value": {
        "attachmentsByRange": {
          "{354, 1}": {
            "OutputName": "Weather Conditions",
            "OutputUUID": "AFF8EA42-490A-472E-AC87-C9A75700B877",
            "Type": "ActionOutput"
          },
          "{356, 1}": {
            "OutputName": "Calendar Events",
            "OutputUUID": "3F085D4E-18AE-48E6-A3AD-52BF26315CC6",
            "Type": "ActionOutput"
          },
          "{358, 1}": {
            "OutputName": "Reminders",
            "OutputUUID": "916AD24C-64D5-448A-B59F-F0E46BA3AA7F",
            "Type": "ActionOutput"
          }
        },
        "string": "Give me a morning report summarizing my day based on this info -- format it nicely with bold text, headers, separators, bullet points, and emoji if needed, and start with the weather (with the high and low)! Be very concise about the calendar events! If you don't see any calendar events or reminders, just tell me there is nothing planned for the day.\n\n\uFFFC\n\uFFFC\n\uFFFC"
      },
      "WFSerializationType": "WFTextTokenString"
    }
  }
}
```

**Key observations:**
- Three separate variable tokens at consecutive positions (354, 356, 358) — each `\uFFFC` in the string maps to a distinct action output.
- `FollowUp: true` — shows the morning report and lets user ask follow-up questions.
- `WFGenerativeResultType: "Automatic"` — runtime selects appropriate output type.
- The shortcut has NO `showresult` action — the `FollowUp: true` flag causes the runtime to display the response inline.

**Calendar filter (today's events, 7-day range):**
```json
"WFContentItemFilter": {
  "Value": {
    "WFActionParameterFilterTemplates": [{
      "Bounded": true,
      "Operator": 1002,
      "Property": "Start Date",
      "Values": { "Number": "7", "Unit": 32 }
    }]
  }
}
```

**Reminders filter (two-stage):**
First filter: incomplete reminders only (`Operator: 4, Property: "Is Completed", Values: {Bool: false}`).
Second filter: reminders due today or overdue, applied to the first filter's output via `WFContentItemInputParameter`.

---

### 6. Action Items from Meeting Notes *(Apple Intelligence gallery)*

- **Source:** `WorkflowKit Gallery.bundle/ActionItems.wflow`
- **Vanity URL:** `https://www.icloud.com/shortcuts/actionitems`
- **Client version:** 4018.0.4 | **Min version:** 900
- **Extra top-level key:** `WFQuickActionSurfaces: []`
- **Description:** "Find action items in your meeting notes and add them to Reminders."
- **Actions (6 total, 5 unique):**

```
is.workflow.actions.ask
is.workflow.actions.filter.notes
is.workflow.actions.askllm
is.workflow.actions.repeat.each
is.workflow.actions.addnewreminder
```

**Full askllm action:**
```json
{
  "WFWorkflowActionIdentifier": "is.workflow.actions.askllm",
  "WFWorkflowActionParameters": {
    "UUID": "80A98864-CE75-4B2F-B23F-A13B10472037",
    "WFGenerativeResultType": "List",
    "WFLLMPrompt": {
      "Value": {
        "attachmentsByRange": {
          "{127, 1}": {
            "OutputName": "Note",
            "OutputUUID": "7309E37E-D49F-4F67-81FF-A5197D84A547",
            "Type": "ActionOutput"
          }
        },
        "string": "Here's the contents of a meeting note. Can you help me identify any outstanding action items that haven't been addressed yet?\n\n\uFFFC"
      },
      "WFSerializationType": "WFTextTokenString"
    }
  }
}
```

No `WFLLMModel` and no `FollowUp`. Output type: `"List"`.

**Loop wiring:** `repeat.each` input = askllm Response output → each `Repeat Item` becomes a reminder title.

**`addnewreminder` with Repeat Item:**
```json
"WFCalendarItemTitle": {
  "Value": {
    "attachmentsByRange": {
      "{0, 1}": { "Type": "Variable", "VariableName": "Repeat Item" }
    },
    "string": "\uFFFC"
  },
  "WFSerializationType": "WFTextTokenString"
},
"WFCalendarItemCalendar": "Personal",
"WFCalendarDescriptor": {
  "Identifier": "<x-apple-reminderkit://REMCDList/038A6209-7581-4A55-8697-D5FCFE36BB5B>",
  "IsAllCalendar": false,
  "Title": "Personal"
}
```

**`filter.notes` with dynamic name filter:**
```json
"WFContentItemFilter": {
  "Value": {
    "WFActionParameterFilterTemplates": [{
      "Operator": 99,
      "Property": "Name",
      "Values": {
        "String": {
          "Value": {
            "attachmentsByRange": {
              "{0, 1}": {
                "OutputName": "Ask for Input",
                "OutputUUID": "BA9CB3E7-...",
                "Type": "ActionOutput"
              }
            },
            "string": "\uFFFC"
          },
          "WFSerializationType": "WFTextTokenString"
        }
      }
    }]
  }
}
```
Requires `AppIntentDescriptor` with `AppIntentIdentifier: "NoteEntity"`, `BundleIdentifier: "com.apple.mobilenotes"`.

---

### 7. Summarize PDF *(Apple Intelligence gallery)*

- **Source:** `WorkflowKit Gallery.bundle/SummarizePDF.wflow`
- **Vanity URL:** `https://www.icloud.com/shortcuts/summarizepdf`
- **Client version:** 4018.0.4 | **Min version:** 900
- **Extra top-level keys:** `WFQuickActionSurfaces: []`, `WFWorkflowTypes: ["ActionExtension"]`
- **Input:** `WFAppContentItem`, `WFGenericFileContentItem`, `WFPDFContentItem`
- **Description:** "Summarize a PDF that you provide."
- **Actions (4 total, 4 unique):**

```
is.workflow.actions.gettextfrompdf
com.apple.WritingTools.WritingToolsAppIntentsExtension.SummarizeTextIntent
is.workflow.actions.showresult
is.workflow.actions.share
```

**Full SummarizeTextIntent action:**
```json
{
  "WFWorkflowActionIdentifier": "com.apple.WritingTools.WritingToolsAppIntentsExtension.SummarizeTextIntent",
  "WFWorkflowActionParameters": {
    "UUID": "09B5964F-CBB7-429E-B6D3-3BE92C08E3FF",
    "summaryType": "createKeyPoints",
    "text": {
      "Value": {
        "attachmentsByRange": {
          "{0, 1}": {
            "OutputName": "Text",
            "OutputUUID": "A42AE8FE-1733-478B-B139-F78839E7BBCD",
            "Type": "ActionOutput"
          }
        },
        "string": "\uFFFC"
      },
      "WFSerializationType": "WFTextTokenString"
    }
  }
}
```

Output name: `"Summarize Text"`.

`gettextfrompdf` uses ExtensionInput:
```json
"WFInput": { "Value": { "Type": "ExtensionInput" }, "WFSerializationType": "WFTextTokenAttachment" }
```

---

### 8. Document Review *(Apple Intelligence gallery)*

- **Source:** `WorkflowKit Gallery.bundle/DocumentReview.wflow`
- **Vanity URL:** `https://www.icloud.com/shortcuts/documentreview`
- **Client version:** 9999 | **Min version:** 900
- **Extra top-level key:** `WFQuickActionSurfaces: []`
- **Description:** "Use a model to compare and contrast two documents."
- **Actions (11 total, 7 unique):**

```
is.workflow.actions.repeat.count
is.workflow.actions.choosefrommenu
is.workflow.actions.file
is.workflow.actions.url
is.workflow.actions.downloadurl
is.workflow.actions.askllm
is.workflow.actions.showresult
```

**Full askllm action:**
```json
{
  "WFWorkflowActionIdentifier": "is.workflow.actions.askllm",
  "WFWorkflowActionParameters": {
    "UUID": "84D2B952-A403-4AB1-A27E-5E87DF5FFA2D",
    "WFLLMPrompt": {
      "Value": {
        "attachmentsByRange": {
          "{123, 1}": {
            "OutputName": "Repeat Results",
            "OutputUUID": "7AB014AA-A9E7-43C8-B0B7-66037FBB9000",
            "Type": "ActionOutput"
          }
        },
        "string": "Compare and contrast these two documents with a high-level summary of each and any key differences between the documents.\n\n\uFFFC"
      },
      "WFSerializationType": "WFTextTokenString"
    }
  }
}
```

No `WFLLMModel`, no `WFGenerativeResultType`, no `FollowUp` — fully automatic/default model.

**Loop pattern for collecting 2 documents:**

```json
{
  "WFWorkflowActionIdentifier": "is.workflow.actions.repeat.count",
  "WFWorkflowActionParameters": {
    "GroupingIdentifier": "C53DD091-5266-4AA9-A1D0-ACFDE9081EAC",
    "WFControlFlowMode": 0,
    "WFRepeatCount": 2.0
  }
}
```

Inside the loop, a `choosefrommenu` lets user select "File" or "URL":
- File branch: `is.workflow.actions.file` with `WFFile: { "Value": { "Type": "Ask" }, ... }` — prompts user to select a file.
- URL branch: `is.workflow.actions.url` → `is.workflow.actions.downloadurl` — fetches the document from a URL.

After loop: `Repeat Results` contains the two documents, passed directly to askllm.

**`is.workflow.actions.file` with Ask prompt:**
```json
"WFFile": { "Value": { "Type": "Ask" }, "WFSerializationType": "WFTextTokenAttachment" }
```

**`is.workflow.actions.url` with Ask prompt:**
```json
"WFURLActionURL": { "Value": { "Type": "Ask" }, "WFSerializationType": "WFTextTokenAttachment" }
```

---

### 9. Haiku *(Apple Intelligence gallery — bonus)*

- **Source:** `WorkflowKit Gallery.bundle/Haiku.wflow`
- **Client version:** 4018.0.4 | **Min version:** 900
- **Description:** "Use a model to write a fun haiku!"
- **Actions (3 total, 3 unique):**

```
is.workflow.actions.ask
is.workflow.actions.askllm
is.workflow.actions.showresult
```

Minimal example — ask for topic → askllm with `WFGenerativeResultType: "Text"` and `WFLLMModel: "Apple Intelligence"`.

Prompt: `"Create a funny haiku for this topic: \uFFFC"`

---

### 10. Leftover Recipes *(Apple Intelligence gallery — bonus)*

- **Source:** `WorkflowKit Gallery.bundle/LeftoverRecipes.wflow`
- **Client version:** 4018.0.4 | **Min version:** 900
- **Description:** "Use a model to whip up a quick recipe with the leftovers you have in the fridge."
- **Actions (2 total, 2 unique):**

```
is.workflow.actions.ask
is.workflow.actions.askllm
```

Minimal example with `FollowUp: true` and no `WFLLMModel` (uses default model). No `showresult` — FollowUp displays inline.

Prompt: `"Help me with a recipe based on what I have left in my fridge: \uFFFC"`

---

## Apple Intelligence Action Parameter Summary

### `is.workflow.actions.askllm` — complete parameter shape

```json
{
  "WFWorkflowActionIdentifier": "is.workflow.actions.askllm",
  "WFWorkflowActionParameters": {
    "UUID": "<action-uuid>",
    "WFLLMPrompt": "<string or WFTextTokenString>",
    "WFLLMModel": "<model-name>",
    "WFGenerativeResultType": "<output-type>",
    "FollowUp": true
  }
}
```

All parameters except `WFLLMPrompt` and `UUID` are optional.

Output name from subsequent references: `"Response"`.

### `WFLLMModel` plist values confirmed in gallery

| Value | Model |
|---|---|
| `"Apple Intelligence"` | Private Cloud Compute (WFAFMInstructServerV1Model / `.afm`) |
| *(absent)* | Automatic — runtime selects model |

Additional values suspected but not yet observed in plist files: `"On-Device"` (for `.afmOnDevice` / WFAFMDevice3BModel) and a ChatGPT value (for `.chatgpt` / WFChatGPTModel).

### `WFGenerativeResultType` plist values confirmed in gallery

| Value | Example shortcut |
|---|---|
| `"List"` | ActionItems, GetStartedWithModels |
| `"Dictionary"` | GetStartedWithModels |
| `"Text"` | Haiku |
| `"Automatic"` | MorningReport |
| *(absent)* | Default = Automatic |

Additional values known from `ContentKit.WFGeneratedOutputType` enum: `"Number"`, `"Boolean"`, `"Date"`, `"textOrEntities"`, `.entityList(String)`.

### `FollowUp` parameter

| Value | Behavior |
|---|---|
| `true` | Shows model response; user can ask follow-up questions before response passes to next action. No need for `showresult` action. |
| `false` / absent | Response passes silently to next action. Use `showresult` to display. |

### Variable wiring: multi-token prompt

Multiple variables can be injected into a single prompt string. Each `\uFFFC` character in the string occupies one position; the `attachmentsByRange` dict maps `"{offset, 1}"` to the corresponding variable/action-output descriptor.

```json
"WFLLMPrompt": {
  "Value": {
    "string": "Summarize this:\n\n\uFFFC\n\n\uFFFC",
    "attachmentsByRange": {
      "{16, 1}": { "OutputName": "Doc 1", "OutputUUID": "AAA...", "Type": "ActionOutput" },
      "{18, 1}": { "OutputName": "Doc 2", "OutputUUID": "BBB...", "Type": "ActionOutput" }
    }
  },
  "WFSerializationType": "WFTextTokenString"
}
```

---

## Framework Sources for Apple Intelligence Actions

| Framework | Path | Role |
|---|---|---|
| `WorkflowKit` | `/System/Library/PrivateFrameworks/WorkflowKit.framework` | Hosts `is.workflow.actions.askllm` action class (`WFAskLLMModelParameter`), serialization, availability checks |
| `ContentKit` | `/System/Library/PrivateFrameworks/ContentKit.framework` | `WFGenerativeModelName` enum, `WFGeneratedOutputType` enum, model classes (`WFAFMDevice3BModel`, `WFAFMInstructServerV1Model`, `WFChatGPTModel`), error types |
| `WritingToolsAppIntentsExtension` | `/System/Library/ExtensionKit/Extensions/WritingToolsAppIntentsExtension.appex` | All Writing Tools AppIntents (Summarize, Proofread, Rewrite, AdjustTone, FormatList, FormatTable) |

---

## New Action Identifiers (batch 3)

```
com.apple.WritingTools.WritingToolsAppIntentsExtension.AdjustToneIntent
com.apple.WritingTools.WritingToolsAppIntentsExtension.FormatListIntent
com.apple.WritingTools.WritingToolsAppIntentsExtension.FormatTableIntent
com.apple.WritingTools.WritingToolsAppIntentsExtension.ProofreadIntent
com.apple.WritingTools.WritingToolsAppIntentsExtension.RewriteTextIntent
com.apple.WritingTools.WritingToolsAppIntentsExtension.SummarizeTextIntent
is.workflow.actions.askllm
is.workflow.actions.count
is.workflow.actions.deletephotos
is.workflow.actions.documentpicker.save
is.workflow.actions.file
is.workflow.actions.filter.photos
is.workflow.actions.filter.reminders
is.workflow.actions.format.date
is.workflow.actions.gettextfrompdf
is.workflow.actions.getvalueforkey
is.workflow.actions.image.combine
is.workflow.actions.makegif
is.workflow.actions.makezip
is.workflow.actions.repeat.count
is.workflow.actions.savetocameraroll
is.workflow.actions.selectphoto
is.workflow.actions.share
is.workflow.actions.url
is.workflow.actions.weather.currentconditions
```
Total: 25 new unique identifiers in batch 3.
