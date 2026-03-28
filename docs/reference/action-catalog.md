# Shortcuts Action Catalog

Complete catalog of action identifiers with parameter schemas, organized by category. Sourced from 41 gallery/iCloud shortcuts, Apple frameworks, Cherri, and shortcuts-js.

---

## Quick Lookup — Identifier by Friendly Name

| Friendly Name | Identifier |
|---------------|-----------|
| Add New Reminder | `is.workflow.actions.addnewreminder` |
| Add to Calendar | `is.workflow.actions.addnewcalendar` |
| Adjust Date | `is.workflow.actions.adjustdate` |
| Adjust Tone | `com.apple.WritingTools.WritingToolsAppIntentsExtension.AdjustToneIntent` |
| Alert / Show Alert | `is.workflow.actions.alert` |
| Append Note | `is.workflow.actions.appendnote` |
| Append to Variable | `is.workflow.actions.appendvariable` |
| Ask for Input | `is.workflow.actions.ask` |
| Choose from List | `is.workflow.actions.choosefromlist` |
| Choose from Menu | `is.workflow.actions.choosefrommenu` |
| Combine Images | `is.workflow.actions.image.combine` |
| Comment | `is.workflow.actions.comment` |
| Convert Image | `is.workflow.actions.image.convert` |
| Copy to Clipboard | `is.workflow.actions.setclipboard` |
| Count | `is.workflow.actions.count` |
| Create Note | `com.apple.mobilenotes.SharingExtension` |
| Date | `is.workflow.actions.date` |
| Delay | `is.workflow.actions.delay` |
| Delete Photos | `is.workflow.actions.deletephotos` |
| Dictionary | `is.workflow.actions.dictionary` |
| Download URL | `is.workflow.actions.downloadurl` |
| Exit Shortcut | `is.workflow.actions.exit` |
| File | `is.workflow.actions.file` |
| Filter Calendar Events | `is.workflow.actions.filter.calendarevents` |
| Filter Files | `is.workflow.actions.filter.files` |
| Filter Music | `is.workflow.actions.filter.music` |
| Filter Notes | `is.workflow.actions.filter.notes` |
| Filter Photos | `is.workflow.actions.filter.photos` |
| Filter Reminders | `is.workflow.actions.filter.reminders` |
| Format as List | `com.apple.WritingTools.WritingToolsAppIntentsExtension.FormatListIntent` |
| Format as Table | `com.apple.WritingTools.WritingToolsAppIntentsExtension.FormatTableIntent` |
| Format Date | `is.workflow.actions.format.date` |
| Generate Barcode/QR | `is.workflow.actions.generatebarcode` |
| Get Clipboard | `is.workflow.actions.getclipboard` |
| Get Current Song | `is.workflow.actions.getcurrentsong` |
| Get Current URL | `is.workflow.actions.safari.geturl` |
| Get Device Details | `is.workflow.actions.getdevicedetails` |
| Get My Shortcuts | `is.workflow.actions.getmyworkflows` |
| Get Text | `is.workflow.actions.gettext` |
| Get Text from PDF | `is.workflow.actions.gettextfrompdf` |
| Get Value for Key | `is.workflow.actions.getvalueforkey` |
| Get Variable | `is.workflow.actions.getvariable` |
| Get Wi-Fi Details | `is.workflow.actions.getwifi` |
| If / Conditional | `is.workflow.actions.conditional` |
| List | `is.workflow.actions.list` |
| Make GIF | `is.workflow.actions.makegif` |
| Make PDF | `is.workflow.actions.makepdf` |
| Make ZIP | `is.workflow.actions.makezip` |
| Markup | `is.workflow.actions.avairyeditphoto` |
| Nothing | `is.workflow.actions.nothing` |
| Notification | `is.workflow.actions.notification` |
| Number | `is.workflow.actions.number` |
| Open App | `is.workflow.actions.openapp` |
| Open File | `is.workflow.actions.documentpicker.open` |
| Open Note | `is.workflow.actions.shownote` |
| Open URL | `is.workflow.actions.openurl` |
| Play Music | `is.workflow.actions.playmusic` |
| Preview Document | `is.workflow.actions.previewdocument` |
| Proofread | `com.apple.WritingTools.WritingToolsAppIntentsExtension.ProofreadIntent` |
| Repeat Count | `is.workflow.actions.repeat.count` |
| Repeat with Each | `is.workflow.actions.repeat.each` |
| Replace Text | `is.workflow.actions.text.replace` |
| Rewrite Text | `com.apple.WritingTools.WritingToolsAppIntentsExtension.RewriteTextIntent` |
| Round Number | `is.workflow.actions.round` |
| Run JavaScript on Web Page | `is.workflow.actions.runjavascriptonwebpage` |
| Run JXA Script | `is.workflow.actions.runjavascript` |
| Run Shell Script | `is.workflow.actions.runshellscript` |
| Run Shortcut | `is.workflow.actions.runworkflow` |
| Save File | `is.workflow.actions.documentpicker.save` |
| Save to Camera Roll | `is.workflow.actions.savetocameraroll` |
| Select Photos | `is.workflow.actions.selectphoto` |
| Send Message | `is.workflow.actions.sendmessage` |
| Set Focus/DND | `is.workflow.actions.dnd.set` |
| Set Variable | `is.workflow.actions.setvariable` |
| Share | `is.workflow.actions.share` |
| Show Content / Show Result | `is.workflow.actions.showresult` |
| Speak Text | `is.workflow.actions.speaktext` |
| Split Text | `is.workflow.actions.text.split` |
| Start Timer | `is.workflow.actions.timer.start` |
| Summarize Text | `com.apple.WritingTools.WritingToolsAppIntentsExtension.SummarizeTextIntent` |
| Take Screenshot | `is.workflow.actions.takescreenshot` |
| Text | `is.workflow.actions.gettext` |
| URL | `is.workflow.actions.url` |
| Use Model (AI) | `is.workflow.actions.askllm` |
| Weather Conditions | `is.workflow.actions.weather.currentconditions` |

---

## Detailed Action Parameters

### Text & Data

#### is.workflow.actions.gettext

```json
"WFTextActionText": "static string" | { WFTextTokenString }
```

#### is.workflow.actions.text.replace

```json
"WFInput": { WFTextTokenAttachment },
"WFReplaceTextFind": " ",
"WFReplaceTextReplace": "%20",
"WFReplaceTextRegularExpression": false
```

#### is.workflow.actions.text.split

```json
"text": { WFTextTokenAttachment },
"WFTextSeparator": "New Lines" | "Custom",
"WFTextCustomSeparator": ","
```

#### is.workflow.actions.count

```json
"WFCountType": "Items" | "Characters" | "Words" | "Sentences" | "Lines",
"Input": { WFTextTokenAttachment }
```

#### is.workflow.actions.number

```json
"WFNumberActionNumber": 42
```

#### is.workflow.actions.round

```json
"WFInput": { WFTextTokenAttachment },
"WFRoundMode": "Normal" | "Always Round Up" | "Always Round Down"
```

#### is.workflow.actions.list

```json
"WFItems": ["item1", "item2"],
"UUID": "..."
```

Empty list: omit `WFItems` entirely.

#### is.workflow.actions.dictionary

```json
"WFItems": { WFDictionaryFieldValue }
```

See format-reference.md for `WFDictionaryFieldValue` encoding.

#### is.workflow.actions.getvalueforkey

```json
"WFDictionaryKey": "Earth",
"WFInput": { WFTextTokenAttachment }
```

### User Interaction

#### is.workflow.actions.ask

```json
"WFAskActionPrompt": "What's your name?",
"WFInputType": "Text" | "Number" | "URL" | "Date and Time",
"WFAskActionDefaultAnswer": "default text",
"WFAskActionAllowsDecimalNumbers": false,
"WFAskActionAllowsNegativeNumbers": false,
"WFAskActionDefaultAnswerNumber": "25",
"WFAskActionDefaultAnswerDateAndTime": { WFTextTokenString with CurrentDate }
```

#### is.workflow.actions.alert

```json
"WFAlertActionTitle": "Title",
"WFAlertActionMessage": "Message text",
"WFAlertActionCancelButtonShown": true
```

#### is.workflow.actions.notification

```json
"WFNotificationActionBody": { WFTextTokenString },
"WFNotificationActionTitle": "Title",
"WFNotificationActionSound": true
```

#### is.workflow.actions.showresult

```json
"WFText": { WFTextTokenString }
```

Note: renamed to "Show Content" in macOS 26+.

#### is.workflow.actions.choosefromlist

```json
"WFInput": { WFTextTokenAttachment },
"WFChooseFromListActionPrompt": "Pick one",
"WFChooseFromListActionSelectMultiple": false,
"WFChooseFromListActionSelectAll": false
```

### Control Flow

#### is.workflow.actions.conditional (If/Otherwise/End If)

Start block (mode 0):
```json
"GroupingIdentifier": "<shared-uuid>",
"WFControlFlowMode": 0,
"WFCondition": "Equals" | 0 | 4 | 99 | 100 | 101 | 1002,
"WFConditionalActionString": "value",
"WFNumberValue": "0",
"WFInput": { WFTextTokenAttachment }
```

WFCondition values: see format-reference.md.

#### is.workflow.actions.repeat.count

Start block:
```json
"GroupingIdentifier": "<shared-uuid>",
"WFControlFlowMode": 0,
"WFRepeatCount": 5
```

#### is.workflow.actions.repeat.each

Start block:
```json
"GroupingIdentifier": "<shared-uuid>",
"WFControlFlowMode": 0,
"WFInput": { WFTextTokenAttachment }
```

#### is.workflow.actions.choosefrommenu

Start block:
```json
"GroupingIdentifier": "<shared-uuid>",
"WFControlFlowMode": 0,
"WFMenuItems": ["Option A", "Option B"],
"WFMenuPrompt": "Pick one" | { WFTextTokenString }
```

Menu item (mode 1):
```json
"GroupingIdentifier": "<shared-uuid>",
"WFControlFlowMode": 1,
"WFMenuItemTitle": "Option A"
```

### Variables

#### is.workflow.actions.setvariable

```json
"WFVariableName": "My Variable",
"WFInput": { WFTextTokenAttachment }
```

#### is.workflow.actions.appendvariable

```json
"WFVariableName": "Collection",
"WFInput": { WFTextTokenAttachment }
```

#### is.workflow.actions.getvariable

```json
"WFVariable": { WFTextTokenAttachment with Type: "Variable" }
```

### Date & Time

#### is.workflow.actions.date

```json
"WFDateActionMode": "Specified Date" | "Current Date",
"WFDateActionDate": "March 27, 2026"
```

#### is.workflow.actions.adjustdate

```json
"WFDate": { WFTextTokenString with CurrentDate },
"WFDuration": { WFQuantityFieldValue with Magnitude + Unit }
```

Units: `"min"`, `"hr"`, `"day"`, `"wk"`, `"mon"`, `"yr"`

#### is.workflow.actions.format.date

```json
"WFDateFormatStyle": "Short" | "Medium" | "Long" | "ISO 8601" | "RFC 2822" | "Custom",
"WFDate": { WFTextTokenString }
```

### Files & Documents

#### is.workflow.actions.file

```json
"WFFile": { WFTextTokenAttachment with Type: "Ask" }
```

#### is.workflow.actions.documentpicker.open

```json
"WFFile": { WFTextTokenAttachment }
```

#### is.workflow.actions.documentpicker.save

```json
"WFAskWhereToSave": true,
"WFInput": { WFTextTokenAttachment }
```

#### is.workflow.actions.makepdf

```json
"WFPDFIncludedPages": "All Pages" | "Single Page",
"WFInput": { WFTextTokenAttachment }
```

#### is.workflow.actions.gettextfrompdf

```json
"WFInput": { WFTextTokenAttachment }
```

#### is.workflow.actions.makezip

```json
"WFZIPName": "archive" | { WFTextTokenString },
"WFInput": { WFTextTokenAttachment }
```

### Web & Network

#### is.workflow.actions.url

```json
"WFURLActionURL": "https://example.com" | { WFTextTokenString }
```

#### is.workflow.actions.downloadurl

```json
"WFURL": { WFTextTokenAttachment },
"WFHTTPMethod": "GET" | "POST" | "PUT" | "PATCH" | "DELETE",
"WFHTTPHeaders": { WFDictionaryFieldValue },
"WFHTTPBodyType": "JSON" | "Form" | "File",
"WFRequestVariable": { WFTextTokenAttachment }
```

#### is.workflow.actions.openurl

```json
"WFInput": { WFTextTokenAttachment }
```

#### is.workflow.actions.safari.geturl

No parameters. Returns current Safari page URL.

### Scripting

#### is.workflow.actions.runshellscript

```json
"WFShellScript": "echo hello",
"Shell": "/bin/bash" | "/bin/zsh" | "/usr/bin/python3",
"WFInput": { WFTextTokenAttachment },
"WFInputEncoding": "UTF-8"
```

#### is.workflow.actions.runjavascript (JXA)

```json
"WFJavaScriptText": "ObjC.import('AppKit');\n..."
```

#### is.workflow.actions.runjavascriptonwebpage

```json
"WFJavaScript": { WFTextTokenString with JS code },
"WFRunJavaScriptCompletion": "Synchronous"
```

`completion(value)` returns data to Shortcuts. `completion()` signals done.

### Shortcut Management

#### is.workflow.actions.runworkflow

```json
"WFWorkflow": {
    "isSelf": true,
    "workflowIdentifier": "UUID",
    "workflowName": "Shortcut Name"
},
"WFInput": { WFTextTokenAttachment },
"WFShowWorkflow": true
```

Self-recursive pattern: `isSelf: true` calls the current shortcut again.

#### is.workflow.actions.getmyworkflows

No parameters. Returns list of all user shortcuts.

### Photos & Media

#### is.workflow.actions.selectphoto

```json
"WFSelectMultiplePhotos": true
```

#### is.workflow.actions.image.convert

```json
"WFImageFormat": "PNG" | "JPEG" | "TIFF" | "GIF" | "BMP" | "PDF" | "HEIF",
"WFInput": { WFTextTokenAttachment }
```

#### is.workflow.actions.image.combine

```json
"WFImageCombineMode": "In a Grid" | "Horizontally" | "Vertically",
"WFImageCombineSpacing": 5,
"WFInput": { WFTextTokenAttachment }
```

#### is.workflow.actions.makegif

```json
"WFMakeGIFActionDelayTime": 0.1,
"WFInput": { WFTextTokenAttachment }
```

#### is.workflow.actions.savetocameraroll

No parameters. Saves pipeline input.

#### is.workflow.actions.deletephotos

```json
"photos": { WFTextTokenAttachment }
```

### Music

#### is.workflow.actions.getcurrentsong

No parameters.

#### is.workflow.actions.playmusic

```json
"WFPlayMusicActionShuffle": "Off" | "Songs",
"WFPlayMusicActionRepeat": "None" | "One" | "All"
```

### Communication

#### is.workflow.actions.sendmessage

```json
"IntentAppDefinition": {
    "BundleIdentifier": "com.apple.MobileSMS",
    "Name": "Messages",
    "TeamIdentifier": "0000000000"
},
"WFSendMessageContent": { WFTextTokenString }
```

### Notes (Require AppIntentDescriptor)

All Notes actions require:
```json
"AppIntentDescriptor": {
    "BundleIdentifier": "com.apple.Notes",
    "Name": "Notes",
    "TeamIdentifier": "0000000000",
    "AppIntentIdentifier": "<see table>"
}
```

| Action | AppIntentIdentifier |
|--------|-------------------|
| Create Note | `CreateNoteLinkAction` |
| Append Note | `AppendToNoteLinkAction` |
| Open Note | `OpenNoteLinkAction` |
| Filter Notes (entity) | `NoteEntity` |

#### com.apple.mobilenotes.SharingExtension (Create Note)

```json
"WFCreateNoteInput": { WFTextTokenString },
"WFNoteGroup": { "DisplayString": "Notes [iCloud]", "Identifier": "x-c..." },
"OpenWhenRun": false,
"ShowWhenRun": false
```

#### is.workflow.actions.appendnote

```json
"WFInput": { WFTextTokenString },
"WFNote": { WFTextTokenAttachment }
```

### System

#### is.workflow.actions.openapp

```json
"WFAppIdentifier": "com.apple.Notes",
"WFSelectedApp": {
    "BundleIdentifier": "com.apple.Notes",
    "Name": "Notes",
    "TeamIdentifier": "0000000000"
}
```

#### is.workflow.actions.getdevicedetails

```json
"WFDeviceDetail": "Device Model" | "Device Name" | "System Version" | "Screen Width" | "Screen Height" | "Current Volume" | "Current Brightness"
```

#### is.workflow.actions.dnd.set (Focus Mode)

```json
"Enabled": 1,
"AssertionType": "Time" | "Event",
"FocusModes": { "DisplayString": "Work", "Identifier": "com.apple.focus.work" },
"Time": { WFTextTokenString }
```

#### is.workflow.actions.delay

```json
"WFDelayTime": 10.0
```

#### is.workflow.actions.speaktext

No parameters (uses pipeline input), or:
```json
"WFText": { WFTextTokenString }
```

#### is.workflow.actions.timer.start

```json
"WFDuration": { WFQuantityFieldValue }
```

#### is.workflow.actions.generatebarcode

```json
"WFText": { WFTextTokenString },
"WFQRErrorCorrectionLevel": "Low" | "Medium" | "Quartile" | "High"
```

### Miscellaneous

#### is.workflow.actions.comment

```json
"WFCommentActionText": "This is a comment"
```

#### is.workflow.actions.nothing

No parameters. Produces no output. Useful as a placeholder.

#### is.workflow.actions.exit

```json
"WFResult": { WFTextTokenString }
```

#### is.workflow.actions.share

No parameters. Shares pipeline input via system share sheet.

#### is.workflow.actions.setclipboard

```json
"WFInput": { WFTextTokenAttachment }
```

#### is.workflow.actions.getclipboard

No parameters.

---

## Third-Party Action Pattern

Third-party apps register actions with their bundle identifier:

```json
"WFWorkflowActionIdentifier": "com.flexibits.fantastical2.ipad.addevent"
```

Common third-party patterns:
- `com.flexibits.fantastical2.ipad.addevent` — Fantastical calendar
- App-specific parameters vary by developer

---

## Additional Identifiers (from shortcuts-js / Cherri)

These identifiers are known but not detailed above:

```
is.workflow.actions.base64encode
is.workflow.actions.detect.address
is.workflow.actions.detect.date
is.workflow.actions.detect.emailaddress
is.workflow.actions.detect.link
is.workflow.actions.detect.phonenumber
is.workflow.actions.format.number
is.workflow.actions.getitemfromlist
is.workflow.actions.getmarkdownrichtext
is.workflow.actions.getrichtextfromhtml
is.workflow.actions.getrichtextfrommarkdown
is.workflow.actions.hash
is.workflow.actions.math
is.workflow.actions.properties.files
is.workflow.actions.random
is.workflow.actions.setbrightness
is.workflow.actions.setvolume
is.workflow.actions.statistics
is.workflow.actions.text.changecase
is.workflow.actions.text.combine
is.workflow.actions.text.match
is.workflow.actions.urlencode
is.workflow.actions.viewresult
is.workflow.actions.waittoreturn
```

### Math Operations (is.workflow.actions.math)

```json
"WFMathOperation": "+" | "-" | "×" | "÷" | "Modulus",
"WFMathOperand": 5,
"WFInput": { WFTextTokenAttachment }
```

### Statistics (is.workflow.actions.statistics)

```json
"WFStatisticsOperation": "Average" | "Minimum" | "Maximum" | "Sum" | "Median" | "Mode" | "Range" | "Standard Deviation"
```

### Conditional String Values (from shortcuts-js)

When `WFCondition` is a string (older format):
`"Equals"`, `"Contains"`, `"Is Greater Than"`, `"Is Less Than"`, `"Begins With"`, `"Ends With"`, `"Has Any Value"`, `"Does Not Contain"`, `"Is Not"`
