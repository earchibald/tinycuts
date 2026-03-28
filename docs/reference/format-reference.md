# Shortcuts File Format Reference

Binary plist (`.shortcut` / `.wflow`) format for macOS Shortcuts.

**Sources:** Zachary7829 format docs, Apple WorkflowKit framework, 41 gallery/iCloud shortcuts analysis.

---

## Top-Level Plist Keys

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `WFWorkflowActions` | Array | Yes | Ordered list of action dictionaries |
| `WFWorkflowClientVersion` | **String** | Yes | Build number, e.g. `"1700"`. **Must be String, not Integer** — Apple's `WFCompareBundleVersions` calls string methods on it. Integer causes `NSInvalidArgumentException` crash during signing. |
| `WFWorkflowClientRelease` | String | Yes | Human version, e.g. `"26.0"` |
| `WFWorkflowMinimumClientVersion` | Integer | Yes | Minimum build number as integer, e.g. `1700` |
| `WFWorkflowMinimumClientVersionString` | String | Yes | Same as above but string form, e.g. `"1700"` |
| `WFWorkflowIcon` | Dict | Yes | Icon configuration (see below) |
| `WFWorkflowInputContentItemClasses` | Array | Yes | Content types accepted as input |
| `WFWorkflowTypes` | Array | Yes | Where the shortcut can appear |
| `WFWorkflowHasShortcutInputVariables` | Boolean | Yes | Whether shortcut accepts input variables |
| `WFWorkflowImportQuestions` | Array | Yes | Import-time configuration prompts (usually `[]`) |
| `WFQuickActionSurfaces` | Array | No | Apple Intelligence gallery shortcuts use `[]` |
| `WFWorkflowHiddenInComplication` | Boolean | No | Hide from Watch complications |

## WFWorkflowIcon

```json
{
    "WFWorkflowIconStartColor": 4915330,
    "WFWorkflowIconGlyphNumber": 57394
}
```

### Common Icon Colors (hex → decimal)

| Color | Hex | Decimal |
|-------|-----|---------|
| Red | `0xEF4439` | 15680569 |
| Orange | `0xEF7D3B` | 15695163 |
| Yellow | `0xEFBF39` | 15712057 |
| Green | `0x3EDC64` | 4120676 |
| Teal | `0x2CCCBF` | 2935999 |
| Blue | `0x3478F6` | 3438838 |
| Purple | `0x5856D6` | 5789398 |
| Indigo | `0x4B0082` | 4915330 |
| Pink | `0xED4694` | 15550100 |
| Gray | `0x8E8E93` | 9342611 |

### Common Glyph Numbers

| Glyph | Number (hex) | Number (decimal) |
|-------|-------------|-----------------|
| Magic wand | `0xE032` | 57394 |
| Gear | `0xE032` | 57394 |
| Document | `0xE10B` | 57611 |
| Rocket | `0xE145` | 57669 |

## WFWorkflowTypes Values

| Value | Meaning |
|-------|---------|
| `MenuBar` | macOS menu bar item |
| `QuickActions` | Finder / Files quick action |
| `Watch` | Runs on Apple Watch |
| `NCWidget` | Notification Center / Today widget |
| `WatchKit` | Older Watch extension type |
| `ActionExtension` | Share Sheet extension |
| `ReceivesOnScreenContent` | Can receive content from screen |
| `Sleep` | Bedtime automation |
| `Automation` | Personal Automation |

## WFWorkflowInputContentItemClasses

Common content type strings:

| Class | Accepts |
|-------|---------|
| `WFStringContentItem` | Plain text |
| `WFURLContentItem` | URLs |
| `WFImageContentItem` | Images |
| `WFPDFContentItem` | PDF documents |
| `WFAppContentItem` | App content |
| `WFGenericFileContentItem` | Generic files |
| `WFSafariWebPageContentItem` | Safari web pages |
| `WFPhoneNumberContentItem` | Phone numbers |
| `WFEmailAddressContentItem` | Email addresses |
| `WFLocationContentItem` | Locations |
| `WFDateContentItem` | Dates |
| `WFRichTextContentItem` | Rich text |
| `WFMKMapItemContentItem` | Map items |
| `WFContactContentItem` | Contacts |

Empty array (`[]`) = no input accepted.

---

## Action Structure

Every action is a dictionary with two keys:

```json
{
    "WFWorkflowActionIdentifier": "is.workflow.actions.gettext",
    "WFWorkflowActionParameters": {
        "UUID": "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX",
        "CustomOutputName": "My Text",
        "WFTextActionText": "Hello world"
    }
}
```

### Standard Parameter Keys

| Key | Type | Purpose |
|-----|------|---------|
| `UUID` | String | Unique identifier for referencing this action's output |
| `CustomOutputName` | String | Rename the action's output variable |
| `ShowWhenRun` | Boolean | Show result in UI when running |
| `OpenWhenRun` | Boolean | Open the result when running |

---

## WFSerializationType Values

| Type | Purpose | Structure |
|------|---------|-----------|
| `WFTextTokenString` | Rich text with embedded variable tokens | `{Value: {string, attachmentsByRange}, WFSerializationType}` |
| `WFTextTokenAttachment` | Single variable/output reference | `{Value: {Type, OutputUUID, OutputName, ...}, WFSerializationType}` |
| `WFContentPredicateTableTemplate` | Filter predicates for filter.* actions | `{Value: {WFActionParameterFilterPrefix, WFActionParameterFilterTemplates}, WFSerializationType}` |
| `WFDictionaryFieldValue` | Dictionary action key-value items | `{Value: {WFDictionaryFieldValueItems: [...]}, WFSerializationType}` |
| `WFQuantityFieldValue` | Numeric value with unit | `{Value: {Magnitude, Unit}, WFSerializationType}` |
| `WFTimeOffsetValue` | Time offset for date adjustment | See adjustdate action |

---

## Control Flow

All control flow blocks use a shared `GroupingIdentifier` UUID and `WFControlFlowMode`:

| Mode | Meaning |
|------|---------|
| `0` | Start of block (if / loop start / menu open) |
| `1` | Middle of block (else / menu item) |
| `2` | End of block (end if / end loop / end menu) |

The end block action also gets a `UUID` for output referencing.

---

## Filter Predicates (WFContentPredicateTableTemplate)

Used by `filter.photos`, `filter.notes`, `filter.calendarevents`, `filter.reminders`, `filter.music`, `filter.files`.

```json
{
    "Value": {
        "WFActionParameterFilterPrefix": 1,
        "WFActionParameterFilterTemplates": [
            {
                "Operator": 4,
                "Property": "Album",
                "Values": { "String": "Vacation" }
            }
        ],
        "WFContentPredicateBoundedDate": false
    },
    "WFSerializationType": "WFContentPredicateTableTemplate"
}
```

### Filter Operators

| Operator | Meaning |
|----------|---------|
| `4` | Equals |
| `5` | Does not equal |
| `8` | Does not equal (alt) |
| `99` | Contains |
| `100` | Has any value |
| `101` | Is greater than |
| `1000` | Within next N (date bounded) |
| `1002` | Is not empty |

### Filter Value Types

| Key in `Values` | Used For |
|-----------------|----------|
| `String` | Text matching (can be WFTextTokenString for dynamic) |
| `Number` | Numeric comparison |
| `Bool` | Boolean matching (true/false) |
| `Unit` | Time unit for date filters (32 = days) |
| `Enumeration` | Enum matching (e.g., `"Burst"` for Media Type) |

### Filter Sorting

```json
"WFContentItemSortOrder": "Latest First",
"WFContentItemSortProperty": "Creation Date",
"WFContentItemLimitEnabled": true,
"WFContentItemLimitNumber": 1.0
```

Sort orders: `"Latest First"`, `"Oldest First"`, `"A to Z"`, `"Z to A"`, `"Smallest First"`, `"Largest First"`

---

## Dictionary Encoding (WFDictionaryFieldValue)

```json
{
    "Value": {
        "WFDictionaryFieldValueItems": [
            {
                "WFItemType": 0,
                "WFKey": {
                    "Value": { "attachmentsByRange": {}, "string": "key_name" },
                    "WFSerializationType": "WFTextTokenString"
                },
                "WFValue": {
                    "Value": { "attachmentsByRange": {}, "string": "value" },
                    "WFSerializationType": "WFTextTokenString"
                }
            }
        ]
    },
    "WFSerializationType": "WFDictionaryFieldValue"
}
```

`WFItemType`: `0` = text, `1` = number, `2` = boolean, `3` = array, `4` = dictionary.

---

## Build & Sign Pipeline

```bash
# 1. Write plist
python3 build_shortcut.py

# 2. Validate
plutil -lint unsigned.shortcut

# 3. Sign (requires iCloud/network)
shortcuts sign -m anyone -i unsigned.shortcut -o signed.shortcut

# 4. Import
open signed.shortcut

# 5. Debug (convert to XML for inspection)
plutil -convert xml1 -o debug.xml unsigned.shortcut
```

### Common Signing Failures

| Error | Cause | Fix |
|-------|-------|-----|
| `NSInvalidArgumentException: -[__NSCFNumber length]` | `WFWorkflowClientVersion` is integer | Change to string: `"1700"` |
| `errSecInternalComponent` / network error | No iCloud / no network | Sign requires iCloud auth + network |
| Exit code 1, no stderr | Malformed plist structure | Check with `plutil -lint`, convert to XML to inspect |

---

## URL Schemes

| Scheme | Purpose |
|--------|---------|
| `shortcuts://run-shortcut?name=<name>` | Run a shortcut by name |
| `shortcuts://run-shortcut?name=<name>&input=text&text=<text>` | Run with text input |
| `shortcuts://run-shortcut?name=<name>&input=clipboard` | Run with clipboard |
| `shortcuts://open-shortcut?name=<name>` | Open shortcut in editor |
| `shortcuts://create-shortcut` | Create new shortcut |
| `shortcuts://gallery` | Open gallery |
| `x-apple-reminderkit://REMCDList/<UUID>` | Reference a Reminders list |

---

## Python plistlib Notes

```python
import plistlib

# Write binary plist (REQUIRED format for .shortcut files)
with open("unsigned.shortcut", "wb") as f:
    plistlib.dump(shortcut_dict, f, fmt=plistlib.FMT_BINARY)

# Read binary plist
with open("shortcut.shortcut", "rb") as f:
    data = plistlib.load(f)
```

**Gotchas:**
- File must be opened in binary mode (`"wb"` / `"rb"`)
- Must specify `fmt=plistlib.FMT_BINARY` for writing
- `bytes` objects are written as `<data>` elements — don't accidentally pass bytes where strings are expected
- Python `True`/`False` map to plist `<true/>`/`<false/>`
- Python `int` maps to `<integer>`, `float` to `<real>` — `WFWorkflowClientVersion` must be string
