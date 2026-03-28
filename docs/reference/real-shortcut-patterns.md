# Real Shortcut Patterns

Patterns extracted from 41 production shortcuts in the Apple gallery and iCloud library. Use these as templates for building new shortcuts.

---

## Pattern: Input Validation Loop (Self-Recursive)

**Used in:** Start Pomodoro, Accessibility Assistant

Shortcut calls itself when input is invalid, creating a retry loop.

```
ask (number, default 25) → round up → conditional (≤ 1?)
  then: runworkflow (isSelf: true) → exit
  otherwise: proceed with valid number
```

Key parameters:
```json
"WFWorkflow": { "isSelf": true, "workflowIdentifier": "...", "workflowName": "..." },
"WFShowWorkflow": true
```

---

## Pattern: Extension Input Detection

**Used in:** Batch Add Reminders

Detect whether shortcut was invoked from Share Sheet or standalone.

```
conditional (ExtensionInput has any value?)
  then: use extension input
  otherwise: ask for input
→ setvariable → proceed
```

```json
"WFInput": {
    "Type": "Variable",
    "Variable": {
        "Value": { "Type": "ExtensionInput" },
        "WFSerializationType": "WFTextTokenAttachment"
    }
},
"WFCondition": 100
```

---

## Pattern: Multi-Item Collection via Loop

**Used in:** Document Review

Collect N items from user using a repeat loop with menu choices.

```
repeat.count(2) {
  choosefrommenu("File or URL?") {
    "File": file (Ask) → pipeline
    "URL": url (Ask) → downloadurl → pipeline
  }
}
→ Repeat Results contains both items
→ askllm (compare the items)
```

---

## Pattern: Accumulate + De-duplicate

**Used in:** Accessibility Assistants (155+ actions)

Build a list across menu branches, then de-duplicate before output.

```
appendvariable("Collection") in each menu branch
→ repeat.each over Collection
  → filter.files (Name equals Repeat Item in existing De-duped list)
  → conditional (no match → appendvariable "De-duped List")
→ filter.files (sort De-duped List A-Z)
→ output
```

---

## Pattern: QR Code Generation

**Used in:** QR Your Shortcuts, QR Your Wi-Fi

```
gettext (build content string with variables)
→ generatebarcode (WFQRErrorCorrectionLevel: "High")
→ show/share result
```

Wi-Fi QR format string: `WIFI:S:{SSID};T:WPA;P:{PASSWORD};;`

---

## Pattern: Photo Workflow (Select → Preview → Confirm → Act)

**Used in:** Clear Out Photos, Clean Up Screenshots

```
filter.photos / selectphoto
→ setvariable("Photos")
→ count (Items)
→ image.combine (In a Grid, spacing 5) or previewdocument
→ choosefrommenu("Delete N photos?", ["Yes", "No"])
  "Yes": deletephotos
  "No": nothing
→ alert (confirmation, no cancel button)
```

---

## Pattern: Screenshot to Archive

**Used in:** Clean Up Screenshots

```
filter.photos (Is a Screenshot = true, Latest First)
→ choosefromlist (multi-select)
→ setvariable
→ date → format.date (ISO 8601)
→ makezip (name = "Screenshots {date}")
→ documentpicker.save (WFAskWhereToSave: true)
→ deletephotos
```

---

## Pattern: AI Pipeline — Summarize Content

**Used in:** Summarize PDF

```
gettextfrompdf (ExtensionInput)
→ SummarizeTextIntent (summaryType: "createKeyPoints")
→ showresult
→ share
```

---

## Pattern: AI Pipeline — Morning Report

**Used in:** Morning Summary

```
weather.currentconditions
→ filter.calendarevents (today, 7-day range)
→ filter.reminders (incomplete, due today/overdue)
→ askllm (FollowUp: true, 3 variables injected into prompt)
```

No showresult needed — `FollowUp: true` displays inline.

---

## Pattern: AI Pipeline — List Extraction + Actions

**Used in:** Action Items from Meeting Notes

```
ask ("Which note?")
→ filter.notes (Name contains user input)
→ askllm (WFGenerativeResultType: "List", extract action items)
→ repeat.each (Response)
  → addnewreminder (title = Repeat Item)
```

---

## Pattern: AI Pipeline — Dictionary + Key Extraction

**Used in:** Get Started with Models

```
askllm (WFGenerativeResultType: "Dictionary", "List planets and diameters")
→ getvalueforkey (WFDictionaryKey: "Earth")
→ showresult ("The diameter of Earth is {value} km")
```

---

## Pattern: Web Page Manipulation

**Used in:** Change Video Speed, Change Font, Edit Webpage

```
getvariable (ExtensionInput — the web page)
→ runjavascriptonwebpage (inject variable into JS, completion() returns data)
→ conditional (check return value)
```

JavaScript must call `completion(value)` to return data, or `completion()` to signal done.

---

## Pattern: Notes CRUD

**Used in:** Hold That Thought, Time Tracking, Accessibility Assistants

**Create:**
```
com.apple.mobilenotes.SharingExtension
  AppIntentDescriptor: CreateNoteLinkAction
  WFCreateNoteInput: { content }
```

**Find:**
```
filter.notes (Name contains "keyword")
  AppIntentDescriptor: NoteEntity
```

**Append:**
```
appendnote
  AppIntentDescriptor: AppendToNoteLinkAction
  WFNote: { reference to found note }
  WFInput: { new content }
```

**Open:**
```
shownote
  AppIntentDescriptor: OpenNoteLinkAction
  WFInput: { reference to note }
```

---

## Pattern: Dynamic Duration with WFQuantityFieldValue

**Used in:** Start Pomodoro

```
ask (number) → round → adjustdate (CurrentDate + N minutes) → timer.start (N minutes)
```

```json
"WFDuration": {
    "Value": {
        "Magnitude": { "OutputName": "Rounded Number", "OutputUUID": "...", "Type": "ActionOutput" },
        "Unit": "min"
    },
    "WFSerializationType": "WFQuantityFieldValue"
}
```

---

## Pattern: Music Filtering by Property

**Used in:** Play Entire Current Album

```
getcurrentsong
→ filter.music (Album equals current song's Album property)
  sort by Album Track #, Smallest First
→ playmusic (shuffle Off, repeat None)
```

Key: using `VariableOverrides` in the filter template with a `WFPropertyVariableAggrandizement` to extract the Album property from the current song.

---

## Pattern: Focus Mode Until Time

**Used in:** Start Pomodoro

```
adjustdate (now + N minutes) → dnd.set (Enabled: 1, until adjusted time)
```

```json
"AssertionType": "Time",
"Enabled": 1,
"FocusModes": { "DisplayString": "Work", "Identifier": "com.apple.focus.work" }
```

---

## Pattern: Date-Bounded Calendar Filter

**Used in:** Hold That Thought, Morning Summary

```json
"WFContentItemFilter": {
    "Value": {
        "WFActionParameterFilterTemplates": [{
            "Bounded": true,
            "Operator": 1000,
            "Property": "Start Date",
            "Values": { "Number": "7", "Unit": 32 }
        }]
    }
},
"WFContentItemLimitEnabled": true,
"WFContentItemLimitNumber": 1.0,
"WFContentItemSortOrder": "Oldest First",
"WFContentItemSortProperty": "Start Date"
```

Unit 32 = days. Operator 1000 = "within next N".

---

## Complexity Distribution

From the 41 analyzed shortcuts:

| Actions | Count | Example |
|---------|-------|---------|
| 1-5 | 12 | Edit Webpage (1), Haiku (3), Summarize PDF (4) |
| 6-15 | 18 | QR Wi-Fi (7), Pomodoro (11), Clean Up Screenshots (14) |
| 16-35 | 5 | Hold That Thought (34), Batch Add Reminders (15) |
| 100+ | 6 | Accessibility Assistants (155+) |

Most useful shortcuts are 5-15 actions.
