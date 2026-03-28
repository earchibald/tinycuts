# Batch 1 Shortcut Analysis

Analysis of 15 shortcuts downloaded from the Shortcuts app gallery, March 2026.

Download method: `curl -s "https://www.icloud.com/shortcuts/api/records/{ID}"` returns JSON with `fields.shortcut.value.downloadURL`. Then download the binary, convert with `plutil -convert xml1`.

---

## Top-level plist keys observed

All shortcuts share these keys:
- `WFWorkflowClientVersion` — build number (e.g. `3514.0.4.200`, `900`, `692`)
- `WFWorkflowClientRelease` — human version string, only present in older shortcuts (e.g. `2.2.1`, `2.0`, `1.7.6`)
- `WFWorkflowMinimumClientVersion` — integer (e.g. `900`, `1113`)
- `WFWorkflowMinimumClientVersionString` — string form, not always present
- `WFWorkflowTypes` — array of strings declaring where the shortcut can run
- `WFWorkflowInputContentItemClasses` — array of `WF*ContentItem` class strings (empty = no input)
- `WFWorkflowActions` — array of action dicts
- `WFWorkflowIcon` — icon configuration dict
- `WFWorkflowImportQuestions` — import-time configuration questions

### WFWorkflowTypes values observed

| Value | Meaning |
|---|---|
| `Watch` | Runs on Apple Watch |
| `NCWidget` | Today / Notification Center widget |
| `WatchKit` | Older Watch extension type |
| `ActionExtension` | Share Sheet extension |
| `QuickActions` | Finder / Files quick action |
| `MenuBar` | macOS menu bar item |
| `ReceivesOnScreenContent` | Can receive content from screen |

---

## Shortcuts

### 1. QR Your Shortcuts
- **Client version:** 3514.0.4.200 | **Min version:** 900
- **Types:** Watch, NCWidget
- **Input:** all content item classes (generic)
- **Actions (10 total, 9 unique):**
  - `is.workflow.actions.comment`
  - `is.workflow.actions.getmyworkflows`
  - `is.workflow.actions.choosefromlist`
  - `is.workflow.actions.repeat.each`
  - `is.workflow.actions.text.replace`
  - `is.workflow.actions.gettext`
  - `is.workflow.actions.generatebarcode`
  - `is.workflow.actions.makepdf`
  - `is.workflow.actions.previewdocument`

**Notable patterns:**
- `getmyworkflows` produces a list of all shortcuts; piped into `choosefromlist` with `WFChooseFromListActionSelectMultiple: true`
- `repeat.each` loops over chosen shortcuts, generates a QR per shortcut URL (`shortcuts://run-shortcut?name=<name>`)
- `text.replace` URL-encodes spaces: `WFReplaceTextFind: " "`, `WFReplaceTextReplace: "%20"`
- `makepdf` collects all Repeat Results into one PDF: `WFPDFIncludedPages: "All Pages"`
- `previewdocument` shows the final PDF

---

### 2. QR Your Wi-Fi
- **Client version:** 1092 | **Min version:** 900
- **Types:** Watch, NCWidget
- **Input:** all content item classes
- **Actions (7 total, 6 unique):**
  - `is.workflow.actions.comment`
  - `is.workflow.actions.getwifi`
  - `is.workflow.actions.ask`
  - `is.workflow.actions.gettext`
  - `is.workflow.actions.generatebarcode`
  - `is.workflow.actions.showresult`

**Notable patterns:**

`getwifi` detail selection:
```
WFWiFiDetail: "Network Name"
CustomOutputName: "Wi-Fi Name"
```

Variable wiring in `ask` default answer — output token referencing previous action by UUID:
```json
"WFAskActionDefaultAnswer": {
  "Value": {
    "attachmentsByRange": {
      "{0, 1}": {
        "OutputName": "Wi-Fi Name",
        "OutputUUID": "74B94EAB-...",
        "Type": "ActionOutput"
      }
    },
    "string": "\uFFFC"
  },
  "WFSerializationType": "WFTextTokenString"
}
```

`generatebarcode` with error correction:
```json
"WFQRErrorCorrectionLevel": "High",
"WFText": { ... WFTextTokenString referencing Text output ... }
```

Wi-Fi QR string format: `"WIFI:S:\uFFFC;T:WPA;P:\uFFFC;;"` (SSID at offset 7, password at offset 17)

---

### 3. Batch Add Reminders
- **Client version:** 3218.0.9 | **Min version:** 900
- **Types:** ActionExtension, Watch, QuickActions
- **Input:** WFStringContentItem only
- **Actions (15 total, 7 unique):**
  - `is.workflow.actions.comment`
  - `is.workflow.actions.ask`
  - `is.workflow.actions.addnewreminder`
  - `is.workflow.actions.conditional`
  - `is.workflow.actions.setvariable`
  - `is.workflow.actions.text.split`
  - `is.workflow.actions.repeat.each`

**Notable patterns:**

`addnewreminder` with a parent task (sub-reminders):
```json
"WFParentTask": {
  "Value": {
    "OutputName": "New Reminder",
    "OutputUUID": "871C1213-...",
    "Type": "ActionOutput"
  },
  "WFSerializationType": "WFTextTokenAttachment"
}
```

`addnewreminder` parameters: `WFCalendarItemTitle`, `WFCalendarItemCalendar`, `WFCalendarItemNotes`, `WFCalendarDescriptor` (with `Identifier`, `IsAllCalendar`, `Title`), `WFFlag`, `WFAlertCondition`, `WFAlertEnabled` ("No Alert"), `WFURL`, `WFParentTask`

`conditional` checking if extension input has a value (WFCondition: 100 = "has any value"):
```json
"WFInput": {
  "Type": "Variable",
  "Variable": {
    "Value": { "Type": "ExtensionInput" },
    "WFSerializationType": "WFTextTokenAttachment"
  }
},
"WFCondition": 100,
"WFControlFlowMode": 0
```

`setvariable` with named variable:
```json
"WFVariableName": "Reminders to Add",
"WFInput": { ... WFTextTokenAttachment ... }
```

`text.split` referencing a named variable:
```json
"text": {
  "Value": { "Type": "Variable", "VariableName": "Reminders to Add" },
  "WFSerializationType": "WFTextTokenAttachment"
}
```

---

### 4. Hold That Thought
- **Client version:** 3303.0.4 | **Min version:** 900
- **Types:** MenuBar, Watch
- **Input:** all content item classes
- **Actions (34 total, 16 unique):**
  - `is.workflow.actions.comment`
  - `is.workflow.actions.choosefrommenu`
  - `is.workflow.actions.alert`
  - `is.workflow.actions.delay`
  - `is.workflow.actions.takescreenshot`
  - `is.workflow.actions.image.convert`
  - `is.workflow.actions.ask`
  - `is.workflow.actions.gettext`
  - `is.workflow.actions.getdevicedetails`
  - `is.workflow.actions.conditional`
  - `is.workflow.actions.safari.geturl`
  - `is.workflow.actions.filter.calendarevents`
  - `is.workflow.actions.filter.notes`
  - `is.workflow.actions.appendnote`
  - `com.apple.mobilenotes.SharingExtension`
  - `is.workflow.actions.shownote`

**Notable patterns:**

`choosefrommenu` menu definition (GroupingIdentifier ties menu open/items/close together):
```json
"GroupingIdentifier": "7BBE256F-...",
"WFControlFlowMode": 0,
"WFMenuItems": ["📸 Capture", "🔁 Recall"],
"WFMenuPrompt": "Capture or recall last stopping point?"
```
Menu branch: `WFControlFlowMode: 1` + `WFMenuItemTitle: "📸 Capture"`, end: `WFControlFlowMode: 2`

`getdevicedetails` with property:
```json
"WFDeviceDetail": "Device Model"
```

`conditional` contains-string check (WFCondition: 99 = "contains"):
```json
"WFCondition": 99,
"WFConditionalActionString": "Mac"
```

`safari.geturl` — no parameters, returns current Safari page.

`filter.calendarevents` with date-bounded filter:
```json
"WFContentItemFilter": {
  "Value": {
    "WFActionParameterFilterPrefix": 1,
    "WFActionParameterFilterTemplates": [{
      "Bounded": true,
      "Operator": 1000,
      "Property": "Start Date",
      "Values": { "Number": "1", "Unit": 32 }
    }]
  },
  "WFSerializationType": "WFContentPredicateTableTemplate"
},
"WFContentItemLimitEnabled": true,
"WFContentItemLimitNumber": 1.0,
"WFContentItemSortOrder": "Oldest First",
"WFContentItemSortProperty": "Start Date"
```

`filter.notes` with name-contains filter:
```json
"WFActionParameterFilterTemplates": [{
  "Operator": 99,
  "Property": "Name",
  "Values": { "String": "⏸️ Hold that thought", "Unit": 4 }
}],
"WFContentItemLimitEnabled": true,
"WFContentItemLimitNumber": 1.0,
"WFContentItemSortOrder": "Latest First",
"WFContentItemSortProperty": "Creation Date"
```
Note: requires `AppIntentDescriptor` with `BundleIdentifier: "com.apple.Notes"`, `AppIntentIdentifier: "NoteEntity"`.

`conditional` checking if a property of a variable has a value (WFCondition: 1002 = "is not empty"):
```json
"WFInput": {
  "Type": "Variable",
  "Variable": {
    "Value": {
      "Aggrandizements": [{
        "PropertyName": "Creation Date",
        "PropertyUserInfo": { "WFLinkEntityContentPropertyUserInfoPropertyIdentifier": "creationDate" },
        "Type": "WFPropertyVariableAggrandizement"
      }],
      "OutputName": "Note",
      "OutputUUID": "CD062FA5-...",
      "Type": "ActionOutput"
    },
    "WFSerializationType": "WFTextTokenAttachment"
  }
}
```

`appendnote` parameters:
```json
"WFInput": { ... WFTextTokenString with content ... },
"WFNote": { ... WFTextTokenAttachment pointing to a note output ... }
```
Requires `AppIntentDescriptor` with `AppIntentIdentifier: "AppendToNoteLinkAction"`.

`com.apple.mobilenotes.SharingExtension` (create note):
```json
"WFCreateNoteInput": { ... WFTextTokenString ... },
"OpenWhenRun": false
```
Requires `AppIntentDescriptor` with `AppIntentIdentifier: "CreateNoteLinkAction"`.

`shownote` (open note):
```json
"WFInput": { ... WFTextTokenAttachment pointing to note ... }
```
Requires `AppIntentDescriptor` with `AppIntentIdentifier: "OpenNoteLinkAction"`.

Current date inline reference in text tokens:
```json
"{36, 1}": {
  "Type": "CurrentDate",
  "Aggrandizements": [{
    "Type": "WFDateFormatVariableAggrandizement",
    "WFDateFormatStyle": "Short",
    "WFTimeFormatStyle": "Short"
  }]
}
```

Clipboard inline reference in text tokens:
```json
"{68, 1}": { "Type": "Clipboard" }
```

`image.convert` to PNG:
```json
"WFImageFormat": "PNG",
"WFInput": { ... WFTextTokenAttachment ... }
```

---

### 5. Speak Brush Teeth Routine
- **Client version:** 782 (release 2.2.1) | **Min version:** none
- **Types:** NCWidget, WatchKit, ActionExtension
- **Input:** all content item classes
- **Actions (23 total, 3 unique):**
  - `is.workflow.actions.gettext`
  - `is.workflow.actions.speaktext`
  - `is.workflow.actions.delay`

**Notable patterns:**
- Entirely linear: gettext → speaktext (no params, uses output of gettext) → delay → repeat
- `speaktext` takes no explicit parameters; it operates on the implicit output from the previous action
- `delay` parameter: `WFDelayTime: 10.0` (float, seconds)
- `gettext` with static string: `WFTextActionText: "Get your toothbrush, toothpaste and cup."`

---

### 6. iPhone and iPad Accessibility Assistant
- **Client version:** 3514.0.4.200 | **Min version:** 900
- **Types:** Watch, NCWidget
- **Input:** none (empty array)
- **Actions (155 total, 13 unique):**
  - `is.workflow.actions.comment`
  - `is.workflow.actions.appendvariable`
  - `is.workflow.actions.choosefrommenu`
  - `is.workflow.actions.gettext`
  - `is.workflow.actions.nothing`
  - `is.workflow.actions.text.split`
  - `is.workflow.actions.runworkflow`
  - `is.workflow.actions.setvariable`
  - `is.workflow.actions.repeat.each`
  - `is.workflow.actions.conditional`
  - `is.workflow.actions.filter.files`
  - `com.apple.mobilenotes.SharingExtension`
  - `is.workflow.actions.shownote`

**Notable patterns:**

Deeply nested `choosefrommenu` (category → sub-category → condition) drives content generation.

`appendvariable` for accumulating results across branches:
```json
"WFVariableName": "Accessibility Features",
"WFInput": { ... ActionOutput or Variable ... }
```

`runworkflow` calling itself (recursive/self-referential):
```json
"WFWorkflow": {
  "isSelf": true,
  "workflowIdentifier": "264A4D8E-...",
  "workflowName": "Accessibility Matrix Test - ALT BUILD"
},
"WFInput": {
  "Value": { "Type": "Variable", "VariableName": "Accessibility Features" },
  "WFSerializationType": "WFTextTokenAttachment"
},
"WFShowWorkflow": true
```

`filter.files` for de-duplication (filter by name equals a variable):
```json
"WFContentItemFilter": {
  "Value": {
    "WFActionParameterFilterTemplates": [{
      "Operator": 8,
      "Property": "Name",
      "Values": {
        "String": { "Value": { "attachmentsByRange": { "{0,1}": { "Type": "Variable", "VariableName": "Repeat Item" } } }, ... }
      }
    }]
  }
}
```

`filter.files` for sorting A-Z:
```json
"WFContentItemInputParameter": { "Value": { "Type": "Variable", "VariableName": "De-duped List" }, ... },
"WFContentItemSortOrder": "A to Z",
"WFContentItemSortProperty": "Name"
```

`com.apple.mobilenotes.SharingExtension` with folder:
```json
"WFNoteGroup": { "DisplayString": "Notes [iCloud]", "Identifier": "x-c..." },
"OpenWhenRun": false,
"ShowWhenRun": false
```

---

### 7. Mac Accessibility Assistant
- **Client version:** 3514.0.4.200 | **Min version:** 900
- **Types:** Watch, NCWidget
- **Input:** none
- **Actions (156 total, 14 unique):** same as iPhone Accessibility plus:
  - `is.workflow.actions.openapp`

`openapp` parameters:
```json
"WFAppIdentifier": "com.apple.Notes",
"WFSelectedApp": {
  "BundleIdentifier": "com.apple.Notes",
  "Name": "Notes",
  "TeamIdentifier": "0000000000"
}
```

---

### 8. Apple Watch Accessibility Assistant
- **Client version:** 3514.0.4.101 | **Min version:** 900
- **Types:** Watch (only)
- **Input:** none
- **Actions (155 total, 13 unique):** identical identifier set to iPhone Accessibility

---

### 9. Time Tracking
- **Client version:** 900 | **Min version:** 900
- **Types:** Watch
- **Input:** all content item classes
- **Actions (12 total, 9 unique):**
  - `is.workflow.actions.comment`
  - `is.workflow.actions.list`
  - `is.workflow.actions.choosefromlist`
  - `is.workflow.actions.ask`
  - `is.workflow.actions.filter.notes`
  - `is.workflow.actions.conditional`
  - `com.apple.mobilenotes.SharingExtension`
  - `is.workflow.actions.gettext`
  - `is.workflow.actions.appendnote`

**Notable patterns:**

`list` with no items (empty — user is meant to add items at import/edit time):
```json
"UUID": "29780CD5-..."
```
(WFItems not present = empty list)

`choosefromlist` with explicit WFInput (rather than using implicit pipeline output):
```json
"WFInput": {
  "Value": {
    "OutputName": "List",
    "OutputUUID": "29780CD5-...",
    "Type": "ActionOutput"
  },
  "WFSerializationType": "WFTextTokenAttachment"
}
```

`ask` for Date and Time with CurrentDate default:
```json
"WFInputType": "Date and Time",
"WFAskActionDefaultAnswerDateAndTime": {
  "Value": {
    "attachmentsByRange": { "{0, 1}": { "Type": "CurrentDate" } },
    "string": "\uFFFC"
  },
  "WFSerializationType": "WFTextTokenString"
}
```

`ask` for Number with defaults:
```json
"WFInputType": "Number",
"WFAskActionAllowsDecimalNumbers": false,
"WFAskActionAllowsNegativeNumbers": false,
"WFAskActionDefaultAnswerNumber": "10"
```

`conditional` checking count > 0 (WFCondition: 101 = "is greater than"):
```json
"WFCondition": 101,
"WFNumberValue": "0"
```

`com.apple.mobilenotes.SharingExtension` with static string title:
```json
"WFCreateNoteInput": "Time Logging Shortcut Data",
"ShowWhenRun": false
```

`gettext` with multiple named variable references in one string — using date formatting aggrandizements:
```json
"attachmentsByRange": {
  "{7, 1}": {
    "OutputName": "Start Date", "OutputUUID": "...",
    "Aggrandizements": [{
      "Type": "WFDateFormatVariableAggrandizement",
      "WFDateFormatStyle": "Medium",
      "WFTimeFormatStyle": "None"
    }]
  },
  "{35, 1}": {
    "OutputName": "Start Date", "OutputUUID": "...",
    "Aggrandizements": [{
      "Type": "WFDateFormatVariableAggrandizement",
      "WFDateFormatStyle": "None",
      "WFTimeFormatStyle": "Short"
    }]
  }
}
```
Note: same OutputUUID referenced twice with different aggrandizements to get date-only vs. time-only.

---

### 10. Start Pomodoro
- **Client version:** 1202 | **Min version:** 900
- **Types:** MenuBar, Watch, NCWidget
- **Input:** none
- **Actions (11 total, 9 unique):**
  - `is.workflow.actions.comment`
  - `is.workflow.actions.ask`
  - `is.workflow.actions.round`
  - `is.workflow.actions.conditional`
  - `is.workflow.actions.runworkflow`
  - `is.workflow.actions.adjustdate`
  - `is.workflow.actions.timer.start`
  - `is.workflow.actions.dnd.set`
  - `is.workflow.actions.showresult`

**Notable patterns:**

`ask` for number with decimal/negative controls:
```json
"WFInputType": "Number",
"WFAskActionAllowsDecimalNumbers": false,
"WFAskActionAllowsNegativeNumbers": false,
"WFAskActionDefaultAnswerNumber": "25"
```

`round` with mode:
```json
"WFInput": { ... ActionOutput ... },
"WFRoundMode": "Always Round Up"
```

`conditional` less-than-or-equal (WFCondition: 0):
```json
"WFCondition": 0,
"WFNumberValue": "1"
```

`runworkflow` calling self with input (self-recursion for input validation loop):
```json
"WFWorkflow": {
  "isSelf": true,
  "workflowIdentifier": "58AFDCC6-...",
  "workflowName": "Start Pomodoro"
},
"WFShowWorkflow": true
```

`adjustdate` with dynamic magnitude from action output:
```json
"WFDuration": {
  "Value": {
    "Magnitude": {
      "OutputName": "Rounded Number",
      "OutputUUID": "5DFB8DC2-...",
      "Type": "ActionOutput"
    },
    "Unit": "min"
  },
  "WFSerializationType": "WFQuantityFieldValue"
},
"WFDate": {
  "Value": {
    "attachmentsByRange": { "{0,1}": { "Type": "CurrentDate" } },
    "string": "\uFFFC"
  },
  "WFSerializationType": "WFTextTokenString"
}
```

`timer.start` with dynamic duration:
```json
"WFDuration": {
  "Value": {
    "Magnitude": { "OutputName": "Rounded Number", "OutputUUID": "...", "Type": "ActionOutput" },
    "Unit": "min"
  },
  "WFSerializationType": "WFQuantityFieldValue"
}
```

`dnd.set` (Focus mode) until a specific time:
```json
"AssertionType": "Time",
"Enabled": 1,
"FocusModes": { "DisplayString": "Work", "Identifier": "com.apple.focus.work" },
"Event": { ... WFTextTokenAttachment pointing to Break End Time ... },
"Time": { ... WFTextTokenString with Break End Time token ... }
```

---

### 11. Markup and Send
- **Client version:** 9999 | **Min version:** 1113
- **Types:** ActionExtension, QuickActions, MenuBar, ReceivesOnScreenContent
- **Input:** WFImageContentItem
- **Actions (2 total, 2 unique):**
  - `is.workflow.actions.avairyeditphoto`
  - `is.workflow.actions.sendmessage`

**Notable patterns:**

`avairyeditphoto` (Markup editor):
```json
"WFDocument": {
  "Value": { "Type": "ExtensionInput" },
  "WFSerializationType": "WFTextTokenAttachment"
}
```

`sendmessage` (iMessage/SMS):
```json
"IntentAppDefinition": {
  "BundleIdentifier": "com.apple.MobileSMS",
  "Name": "Messages",
  "TeamIdentifier": "0000000000"
},
"WFSendMessageContent": { ... WFTextTokenString with Markup Result token ... }
```
Note: no recipient specified — prompts at runtime.

---

### 12. Play Entire Current Album
- **Client version:** 484 (release 1.7.6) | **Min version:** none
- **Types:** NCWidget, WatchKit
- **Input:** all content item classes
- **Actions (3 total, 3 unique):**
  - `is.workflow.actions.getcurrentsong`
  - `is.workflow.actions.filter.music`
  - `is.workflow.actions.playmusic`

**Notable patterns:**

`getcurrentsong` — no parameters, produces current track.

`filter.music` with property aggrandizement on a variable (get Album property of current song, use as filter value):
```json
"WFContentItemFilter": {
  "Value": {
    "WFActionParameterFilterPrefix": 1,
    "WFActionParameterFilterTemplates": [{
      "Operator": 4,
      "Property": "Album",
      "VariableOverrides": {
        "stringValue": {
          "Value": {
            "attachmentsByRange": {
              "{0, 1}": {
                "Aggrandizements": [{
                  "PropertyName": "Album",
                  "PropertyUserInfo": "albumTitle",
                  "Type": "WFPropertyVariableAggrandizement"
                }],
                "OutputName": "Current Song",
                "OutputUUID": "2AAF1EE2-...",
                "Type": "ActionOutput"
              }
            },
            "string": "\uFFFC"
          },
          "WFSerializationType": "WFTextTokenString"
        }
      }
    }]
  },
  "WFSerializationType": "WFContentPredicateTableTemplate"
},
"WFContentItemSortOrder": "Smallest First",
"WFContentItemSortProperty": "Album Track #"
```

`playmusic` with shuffle/repeat options:
```json
"WFPlayMusicActionRepeat": "None",
"WFPlayMusicActionShuffle": "Off"
```
Note: no explicit input — uses implicit pipeline (filtered songs).

---

### 13. Change Video Speed
- **Client version:** 692 (release 2.0) | **Min version:** none
- **Types:** ActionExtension
- **Input:** WFSafariWebPageContentItem
- **Actions (8 total, 6 unique):**
  - `is.workflow.actions.list`
  - `is.workflow.actions.choosefromlist`
  - `is.workflow.actions.getvariable`
  - `is.workflow.actions.runjavascriptonwebpage`
  - `is.workflow.actions.conditional`
  - `is.workflow.actions.alert`

**Notable patterns:**

`list` with explicit items:
```json
"WFItems": ["0.8", "1.0", "1.1", "1.2", "1.5", "2.0"]
```

`getvariable` to retrieve extension input (web page):
```json
"WFVariable": {
  "Value": { "Type": "ExtensionInput" },
  "WFSerializationType": "WFTextTokenAttachment"
}
```

`runjavascriptonwebpage` with variable interpolated into JS:
```json
"WFJavaScript": {
  "Value": {
    "attachmentsByRange": {
      "{102, 1}": {
        "OutputName": "Speed",
        "OutputUUID": "83496B13-...",
        "Type": "ActionOutput"
      }
    },
    "string": "var videos = document.querySelectorAll(\"video\");\nfor (var video of videos) {\n    video.playbackRate = \uFFFC;\n}\n\ncompletion(videos.length);"
  },
  "WFSerializationType": "WFTextTokenString"
},
"WFRunJavaScriptCompletion": "Synchronous"
```
`completion(value)` returns data back to Shortcuts; `completion()` signals done with no return value.

`conditional` string equals "0":
```json
"WFCondition": "Equals",
"WFConditionalActionString": "0"
```

`alert` without cancel button:
```json
"WFAlertActionCancelButtonShown": false,
"WFAlertActionMessage": "There aren't any videos on this page.",
"WFAlertActionTitle": "No videos found"
```

---

### 14. Change Font
- **Client version:** 700 (release 2.0) | **Min version:** none
- **Types:** WatchKit, ActionExtension
- **Input:** WFSafariWebPageContentItem
- **Actions (4 total, 4 unique):**
  - `is.workflow.actions.dictionary`
  - `is.workflow.actions.choosefromlist`
  - `is.workflow.actions.getvariable`
  - `is.workflow.actions.runjavascriptonwebpage`

**Notable patterns:**

`dictionary` with WFDictionaryFieldValue (display-name → PostScript-name mapping):
```json
"WFItems": {
  "Value": {
    "WFDictionaryFieldValueItems": [
      {
        "WFItemType": 0,
        "WFKey": { "Value": { "attachmentsByRange": {}, "string": "Bradley Hand" }, "WFSerializationType": "WFTextTokenString" },
        "WFValue": { "Value": { "attachmentsByRange": {}, "string": "BradleyHandITCTT-Bold" }, "WFSerializationType": "WFTextTokenString" }
      },
      ...
    ]
  },
  "WFSerializationType": "WFDictionaryFieldValue"
}
```
`WFItemType: 0` = text value.

`choosefromlist` uses implicit pipeline (dictionary) — no explicit `WFInput`.

`runjavascriptonwebpage` injecting CSS with chosen font:
```js
var style = document.createElement("style");
style.type = "text/css";
var head = document.head;
head.appendChild(style);
style.sheet.insertRule("* { font-family: '<FONT>', cursive !important; }");
completion(true);
```

---

### 15. Edit Webpage
- **Client version:** 692 (release 2.0) | **Min version:** none
- **Types:** NCWidget, WatchKit, ActionExtension
- **Input:** all content item classes
- **Actions (1 total, 1 unique):**
  - `is.workflow.actions.runjavascriptonwebpage`

**Notable patterns:**

Simplest possible `runjavascriptonwebpage` — static JS, no return value needed (void `completion()`):
```js
document.body.contentEditable = "true"; document.designMode = "on"
completion();
```
No UUID, no custom parameters — shows minimum required structure.

---

## Variable Wiring Patterns Summary

### WFSerializationType values observed

| Type | Used For |
|---|---|
| `WFTextTokenString` | Rich text with embedded token attachments (`attachmentsByRange`) |
| `WFTextTokenAttachment` | Single variable/output reference |
| `WFContentPredicateTableTemplate` | Filter predicates (filter.* actions) |
| `WFDictionaryFieldValue` | Dictionary action items |
| `WFQuantityFieldValue` | Numeric values with units (e.g. duration) |
| `WFTimeOffsetValue` | Time offset for adjustdate |

### Token attachment "Type" values

| Type | Meaning |
|---|---|
| `ActionOutput` | Output of a specific previous action (requires `OutputUUID` + `OutputName`) |
| `Variable` | Named variable (set via setvariable/appendvariable; requires `VariableName`) |
| `ExtensionInput` | Share Sheet / Action Extension input |
| `CurrentDate` | Current date/time at runtime |
| `Clipboard` | Current clipboard contents |

### Aggrandizement types

| Type | Purpose |
|---|---|
| `WFPropertyVariableAggrandizement` | Extract a property from an object (`PropertyName`, `PropertyUserInfo`) |
| `WFDateFormatVariableAggrandizement` | Format a date (`WFDateFormatStyle`, `WFTimeFormatStyle`) |
| `WFCoercionVariableAggrandizement` | Type-coerce to a content item class (`CoercionItemClass`) |

### WFCondition values observed

| Value | Meaning |
|---|---|
| `0` | Less than or equal |
| `4` | Equals (string/filter operator) |
| `8` | Does not equal |
| `99` | Contains |
| `100` | Has any value |
| `101` | Is greater than |
| `1000` | Within next N (date filter) |
| `1002` | Is not empty |
| `"Equals"` | String equality (older format) |

### WFControlFlowMode values

| Value | Meaning |
|---|---|
| `0` | Start of block (if/loop/menu) |
| `1` | Middle of block (else/menu-item) |
| `2` | End of block |

### AppIntentDescriptor usage (Notes actions)

All modern Notes actions require an `AppIntentDescriptor` dict:
```json
{
  "AppIntentIdentifier": "CreateNoteLinkAction" | "AppendToNoteLinkAction" | "OpenNoteLinkAction" | "NoteEntity",
  "BundleIdentifier": "com.apple.Notes",
  "Name": "Notes",
  "TeamIdentifier": "0000000000"
}
```

---

## Action Identifier Master List (batch 1)

```
com.apple.mobilenotes.SharingExtension
is.workflow.actions.addnewreminder
is.workflow.actions.adjustdate
is.workflow.actions.alert
is.workflow.actions.appendnote
is.workflow.actions.appendvariable
is.workflow.actions.ask
is.workflow.actions.avairyeditphoto
is.workflow.actions.choosefrommenu
is.workflow.actions.choosefromlist
is.workflow.actions.comment
is.workflow.actions.conditional
is.workflow.actions.delay
is.workflow.actions.dictionary
is.workflow.actions.dnd.set
is.workflow.actions.filter.calendarevents
is.workflow.actions.filter.files
is.workflow.actions.filter.music
is.workflow.actions.filter.notes
is.workflow.actions.generatebarcode
is.workflow.actions.getcurrentsong
is.workflow.actions.getdevicedetails
is.workflow.actions.getmyworkflows
is.workflow.actions.gettext
is.workflow.actions.getvariable
is.workflow.actions.image.convert
is.workflow.actions.list
is.workflow.actions.makepdf
is.workflow.actions.nothing
is.workflow.actions.openapp
is.workflow.actions.playmusic
is.workflow.actions.previewdocument
is.workflow.actions.repeat.each
is.workflow.actions.round
is.workflow.actions.runjavascriptonwebpage
is.workflow.actions.runworkflow
is.workflow.actions.safari.geturl
is.workflow.actions.sendmessage
is.workflow.actions.setvariable
is.workflow.actions.shownote
is.workflow.actions.showresult
is.workflow.actions.speaktext
is.workflow.actions.takescreenshot
is.workflow.actions.text.replace
is.workflow.actions.text.split
is.workflow.actions.timer.start
```
Total: 46 unique identifiers across 15 shortcuts.
